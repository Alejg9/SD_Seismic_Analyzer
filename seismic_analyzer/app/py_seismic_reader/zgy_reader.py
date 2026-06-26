from typing import Tuple, Union

from pyzgy.accessors import SeismicReader, SeismicWriter
import xarray as xr
import numpy as np
import torch
import ptwt
import pywt
import polars as pl


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
        self.cwt_results = {}
        self.processed = {}
        self.time_cuda = torch.from_numpy(self.ds['time'].values).float().cuda()
        self._cwt_cache = {}
        self.freqs = np.arange(5, 126, 1)


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