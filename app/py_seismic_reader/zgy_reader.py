from typing import Tuple, Union

from pyzgy.accessors import SeismicReader, SeismicWriter
import xarray as xr
import numpy as np
import torch
import ptwt
import pywt
import polars as pl
import lasio

def get_index_from_value(arr, value):
    return np.where(arr == value)[0][0]


class ZGYCube:
    def __init__(self, path: str):
        """
        :param path: Used to declare the cube path in ZGY Format.
        """

        with SeismicReader(path) as reader:
            cube = np.array(
                reader.read_volume()
            )

            # print(cube.shape, '\n',info, '\n', limits)
            cube = torch.from_numpy(cube)
            print(cube.shape)
            self.ds = xr.Dataset(
                data_vars=dict(
                    raw_data=(['iline', 'xline', 'time'], cube),
                ),
                coords=dict(
                    xline=reader.xlines,
                    iline=reader.ilines,
                    time=reader.samples
                ),
            )

            del cube
            self.corners = reader.corners
            self.zinc = reader.zinc
            self.annotstart = reader.annotstart
            self.annotinc = reader.annotinc
            self.zstart = reader.samples[0]
            reader.close()

        self.well_locations_df: pl.DataFrame | None = None
        self.fm_df: pl.DataFrame | None = None
        self.wells: list[str] = []
        self.check_shots: dict[str, pl.DataFrame] = {}
        self.las: dict[str, pl.DataFrame] = {}

        self.cwt_results = {}
        self.processed = {}
        self.time_cuda = torch.from_numpy(self.ds['time'].values).float().cuda()
        self._cwt_cache = {}
        self.freqs = np.arange(5, 126, 1)

    def write_zgy_raw(self, path: str):
        cube = self.ds['raw_data']
        with SeismicWriter(
                path,
                cube.values.shape,
                self.zstart,
                self.zinc,
                self.annotstart,
                self.annotinc,
                self.corners
        ) as writer:
            writer.write_volume(cube.values)

    def write_zgy(self, frequency: str, path: str, var: str = 'data'):
        cube = self.processed[frequency]
        print(cube[var].values.shape)
        with SeismicWriter(
                path,
                cube[var].values.shape,
                self.zstart,
                self.zinc,
                self.annotstart,
                self.annotinc,
                self.corners
        ) as writer:
            writer.write_volume(cube[var].values)

    def load_check_shot(self, path: str, well_name: str, separator:str='\t'):

        check_shot_df = pl.read_csv(
            path,
            skip_rows=1,
            has_header=True,
            separator=separator
        )

        if len(check_shot_df.columns) == 3:
            check_shot_df.columns = [
                'Depth',
                'TVDSS',
                'OWT'
            ]

            check_shot_df = check_shot_df.with_columns(
                (pl.col('OWT') * 2000).alias('TWT')
            )

        elif len(check_shot_df.columns) == 4:
            check_shot_df.columns = [
                'Depth',
                'TVDSS',
                'OWT',
                'TWT'
            ]
        self.check_shots[well_name] = check_shot_df

    def calculate_tops(self, well_name: str):
        _tops_df = self.fm_df

        _tops_df.columns = [
            'WellName',
            'FmName',
            'Depth',
            'TWT'
        ]


        check_shot_df = self.check_shots[well_name]

        check_shot_df.columns = [
            'Depth',
            'TVDSS',
            'OWT',
            'TWT'
        ]

        check_shot_depths = check_shot_df['Depth'].to_numpy()

        def find_top_bot_depths(depth: float, depths_arr: np.ndarray) -> tuple:
            try:
                bot_depth = depths_arr[depths_arr > depth].min()
                top_depth = depths_arr[depths_arr <= depth].max()
                print(bot_depth, top_depth, depth)
            except Exception as e:
                print(e)
                bot_depth, top_depth = None, None

            return bot_depth, top_depth

        tops_df = _tops_df.filter(
            pl.col('WellName') == well_name
        )

        tops_df = tops_df.with_columns(
            pl.col('Depth').map_elements(
                lambda x: find_top_bot_depths(x, check_shot_depths),
                return_dtype=pl.List(float)
            ).alias('tops_TWT')
        )

        tops_df = tops_df.with_columns(
            pl.col('tops_TWT').list.max().alias('Depth_max'),
            pl.col('tops_TWT').list.min().alias('Depth_min')
        )

        tops_df = tops_df.drop('TWT').join(
            check_shot_df.select(['Depth', 'TWT']),
            left_on='Depth_max',
            right_on='Depth',
            how='left',
        ).with_columns(
            pl.col('TWT').alias('TWT_max'),
        ).drop('TWT')

        tops_df = tops_df.join(
            check_shot_df.select(['Depth', 'TWT']),
            left_on='Depth_min',
            right_on='Depth',
            how='left',
        ).with_columns(
            pl.col('TWT').alias('TWT_min'),
        ).drop('TWT')

        tops_df = tops_df.with_columns(
            ((pl.col('TWT_max') - pl.col('TWT_min')) / (pl.col('Depth_max') - pl.col('Depth_min'))).alias('m'),
        )

        tops_df = tops_df.with_columns(
            (pl.col('TWT_max') - (pl.col('m') * pl.col('Depth_max'))).alias('b')
        )

        tops_df = tops_df.with_columns(
            (pl.col('Depth') * pl.col('m') + pl.col('b')).alias('TWT')
        )
        tops_df = tops_df.select([
            'WellName',
            'FmName',
            'Depth',
            'TWT'
        ])

        _tops_df = _tops_df.cast(tops_df.schema)
        _tops_df = _tops_df.filter(
            pl.col('WellName') != well_name
        ).vstack(tops_df)

        self.fm_df = _tops_df

    def load_well_log(self,path:str, well_name: str):

        las = lasio.read(path)
        df = las.df()

        pldf = pl.DataFrame(df)
        # pldf = pldf.with_columns(
        #     pl.Series(df.index).alias('Depth')
        # )
        self.las[well_name] = pldf

    def load_well_log_csv(self,path:str, well_name: str):
        df = pl.read_csv(path)

        self.las[well_name] = df

    def calculate_twt(self, well_name: str):


        check_shot_df = self.check_shots[well_name]

        check_shot_df.columns = [
            'Depth',
            'TVDSS',
            'OWT',
            'TWT'
        ]

        check_shot_depths = check_shot_df['Depth'].to_numpy()

        def find_top_bot_depths(depth: float, depths_arr: np.ndarray) -> tuple:
            try:
                bot_depth = depths_arr[depths_arr > depth].min()
                top_depth = depths_arr[depths_arr <= depth].max()
                print(bot_depth, top_depth, depth)
            except Exception as e:
                print(e)
                bot_depth, top_depth = None, None

            return bot_depth, top_depth

        log_df = self.las[well_name]

        log_df = log_df.with_columns(
            pl.col('DEPTH:2').map_elements(
                lambda x: find_top_bot_depths(x, check_shot_depths),
                return_dtype=pl.List(float)
            ).alias('tops_TWT')
        )

        log_df = log_df.with_columns(
            pl.col('tops_TWT').list.max().alias('Depth_max'),
            pl.col('tops_TWT').list.min().alias('Depth_min')
        )

        if 'TWT' in log_df.columns:
            log_df = log_df.drop('TWT')
        log_df = log_df.join(
            check_shot_df.select(['Depth', 'TWT']),
            left_on='Depth_max',
            right_on='Depth',
            how='left',
        ).with_columns(
            pl.col('TWT').alias('TWT_max'),
        ).drop('TWT')

        log_df = log_df.join(
            check_shot_df.select(['Depth', 'TWT']),
            left_on='Depth_min',
            right_on='Depth',
            how='left',
        ).with_columns(
            pl.col('TWT').alias('TWT_min'),
        ).drop('TWT')

        log_df = log_df.with_columns(
            ((pl.col('TWT_max') - pl.col('TWT_min')) / (pl.col('Depth_max') - pl.col('Depth_min'))).alias('m'),
        )

        log_df = log_df.with_columns(
            (pl.col('TWT_max') - (pl.col('m') * pl.col('Depth_max'))).alias('b')
        )

        log_df = log_df.with_columns(
            (pl.col('DEPTH:2') * pl.col('m') + pl.col('b')).alias('TWT')
        )
        log_df = log_df.select(self.las[well_name].columns + ['TWT'])

        self.las[well_name] = log_df