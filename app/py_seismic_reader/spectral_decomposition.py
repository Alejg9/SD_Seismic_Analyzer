from .zgy_reader import ZGYCube
import ptwt
import pywt
import numpy as np
import polars as pl
import torch
import xarray as xr
from typing import Union
import cv2
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st
class Cube(ZGYCube):

    def __init__(self, path: str):
        super().__init__(path)


    def load_well_location(self, path: str):

        try:
            df = pl.read_csv(path)
        except Exception as e:
            return None


        self.well_locations_df = df

    def get_image(self,dim_index: int, var:str='raw_data', dim:str = 'iline'):

        raw_img = self.ds[var].sel({dim: dim_index}).values
        img = cv2.normalize(raw_img, None, 0, 255, cv2.NORM_MINMAX, dtype=cv2.CV_8UC3)
        img = cv2.applyColorMap(img, cv2.COLORMAP_JET)

        return img.T.transpose(1, 2, 0), raw_img

    def plot_trace(self, inline: int, crossline: int):

        trace = self.ds['raw_data'].sel(iline=inline, xline=crossline)
        time = self.time_cuda.cpu().numpy()
        fig = px.line(
            y=time,
            x=trace.values,
            height=1024
        )

        fig.update_yaxes(autorange="reversed", title='Tiempo (ms)')
        fig.update_xaxes(title='Amplitud')
        return fig
    def apply_cwt_to_image(
            self,
            dim: str,
            dim_index: int,
            wavelet: str,
            mode: str,
            min_freq: float | None = None,
            max_freq: float | None = None,
            agg: str | None = None,
            output_freq: float | None = None,
            return_phase: bool | None = None,
    ):
        trace = self.ds['raw_data'].sel({dim: dim_index}).values
        trace = torch.as_tensor(trace, dtype=torch.float32).cuda()

        cwtmatr, freqs = self._calculate_cwt_cached(
            wavelet= wavelet,
            trace=trace,
            time=self.time_cuda
        )

        abscwtmatr = torch.abs(cwtmatr)

        if mode == 'rango':
            if not min_freq or not max_freq or not agg:
                raise

            abscwtmatr = abscwtmatr[(freqs >= min_freq) & (freqs <= max_freq)]

            func = getattr(torch, agg)
            abscwtmatr = func(abscwtmatr, dim=0)
        elif mode == 'puntual':

            if not output_freq:
                raise Exception(f'Not output_freq given.\n {output_freq}')
            idx = torch.argmin(torch.abs(freqs - output_freq))
            abscwtmatr = abscwtmatr[idx]
            print(abscwtmatr)
        fig = make_subplots(
            rows=2 if return_phase else 1,
            cols=1,
        )

        fig.update_layout(
            title=f"Descomposición espectral: CWT({wavelet}) - "
                  f"{f'{output_freq} Hz' if output_freq is not None else f'{agg} de {min_freq} Hz - {max_freq} Hz'}\n"
                  f"{dim}: {dim_index}",
            height=1024 if return_phase else 512,
        )

        fig.add_trace(
            go.Heatmap(
                z=abscwtmatr.cpu().numpy().T,
                x=freqs.cpu(),
                y=self.time_cuda.cpu().numpy(),
                colorscale=[[0, 'rgb(255,255,255)'], [1, 'rgb(255,0,0)']],
                colorbar=dict(
                    title="|CWT|",
                    x=1.02,  # Barra del primer heatmap
                    y=0.78,
                    len=0.42
                )
            )
        )
        if return_phase:
            phase = torch.angle(cwtmatr)
            phase = torch.cos(phase)

            if mode == 'rango':
                if not min_freq or not max_freq or not agg:
                    raise

                phase = phase[(freqs >= min_freq) & (freqs <= max_freq)]
                func = getattr(torch, agg)
                phase = func(phase, dim=0)

            elif mode == 'puntual':
                if not output_freq:
                    raise Exception(f'Not output_freq given.\n {output_freq}')

                idx = torch.argmin(torch.abs(freqs - output_freq))
                phase = phase[idx]

            fig.add_trace(
                go.Heatmap(
                    z=phase.cpu().numpy().T,
                    x=self.ds['iline'].values if dim == 'xline' else self.ds['xline'].values,
                    y=self.ds['time'].values if dim in ['iline', 'xline'] else self.ds['iline'].values,
                    colorscale=[[0, 'rgb(255,255,255)'], [1, 'rgb(0,0,0)']],
                    colorbar=dict(
                        title="Cos-Phase",
                        x=1.02,  # Misma columna, pero más abajo
                        y=0.22,
                        len=0.42
                    )
                ),
                row=2,
                col=1
            )

        if dim == "iline":
            x_title = "Crossline"
            y_title = "Time (ms)"
        elif dim == "xline":
            x_title = "Inline"
            y_title = "Time (ms)"
        else:  # dim == "time"
            x_title = "Crossline"
            y_title = "Inline"

        fig.update_xaxes(title_text=x_title)
        fig.update_yaxes(
            title_text=y_title,
            autorange="reversed"
        )

        return fig
    def plot_cwt(self, inline: int, crossline: int, wavelet: str):
        trace = self.ds['raw_data'].sel(iline=inline, xline=crossline).values
        cwtmatr, freqs = self._calculate_cwt_cached(
            wavelet,
            torch.from_numpy(trace),
            self.time_cuda
        )

        fig = make_subplots(
            rows=2,
            cols=1,
            shared_xaxes=True,
            vertical_spacing=0.05
        )

        fig.add_trace(
            go.Heatmap(
                z=torch.abs(cwtmatr).T.cpu(),
                x=freqs.cpu(),
                y=self.time_cuda.cpu(),
                colorscale='Viridis',#[[0, 'rgb(0,0,255)'], [0.43, 'rgb(255,255,255)'], [1, 'rgb(255,0,0)']],
                name='Escalograma |CWT|',
                colorbar=dict(
                    title="|CWT|",
                    x=2.02,      # Barra del primer heatmap
                    y=0.78,
                    len=0.42
                )
            ),
            row=1,
            col=1
        )

        if cwtmatr.is_complex():
            fig.add_trace(
                go.Heatmap(
                    z=torch.cos(torch.angle(cwtmatr)).T.cpu(),
                    x=freqs.cpu(),
                    y=self.time_cuda.cpu(),
                    colorscale=[[0, 'rgb(255,255,255)'], [1, 'rgb(0,0,0)']],
                    name='Coseno de la fase de CWT compleja',
                    colorbar=dict(
                        title="Imag",
                        x=2.02,  # Misma columna, pero más abajo
                        y=0.22,
                        len=0.42
                    )
                ),
                row=2,
                col=1
            )

            fig.update_yaxes(autorange="reversed", row=2, col=1)
        fig.update_layout(
            height=2048,
        )
        fig.update_yaxes(autorange="reversed", row=1, col=1)


        return fig

    def add_tops_to_fig(self, fig, well_name, x, subplot_row=None, subplot_col=None):

        df = self.fm_df.filter(pl.col("WellName") == well_name)

        for fm in df.iter_rows(named=True):

            trace = go.Scatter(
                x=x,
                y=[fm["twt"], fm["twt"]],
                mode="lines",
                name=fm["FmName"]
            )

            if subplot_row is not None and subplot_col is not None:
                fig.add_trace(trace, row=subplot_row, col=subplot_col)
            else:
                fig.add_trace(trace)

        return fig

    @staticmethod
    def get_wavelets():
        return [wav for wav in pywt.wavelist() if wav.__contains__('morl') or wav.__contains__('cmor') or wav.__contains__('gaus') or wav.__contains__('mexh')]

    def apply_spectral_decomp_to_image(self, data,output_frequency, include_phase=True, wavelet='cmor1.5-1.0'):
        n_xl, n_t = data.shape
        print(n_xl, n_t)
        traces = data.reshape(-1, n_t)
        traces = torch.as_tensor(traces, dtype=torch.float32)

        if type(output_frequency) == int:
            _processed = self._calculate_cwt(
                wavelet,
                traces,
                output_frequency
            )  # (batch, time)
        elif type(output_frequency) == list:
            _processed = self._calculate_cwts_mean(
                wavelet,
                traces,
                output_frequency,
                include_phase=include_phase
            )
        else:
            raise TypeError(f'output_frequency must be int or list')

        if include_phase:
            _processed, phase = _processed

        return _processed, phase
    def load_fm_df(self, path: str, has_header: bool = False, separator: str = '\t'):
        df = pl.read_csv(path, has_header=has_header, separator=separator)
        header: list = ['WellName', 'FmName', 'depth', 'tvdss', 'twt']
        df.columns = header

        self.fm_df = df

    def calculate_cwt_over_wells(self, wavelet, return_phase=False):
        wl_df = self.well_locations_df
        cwtmatrs = []
        phases = []
        well_names = []
        for row in wl_df.iter_rows(named=True):
            iline = row['Inline']
            xline = row['Xline']
            well_names.append(row['WellName'])

            cwtmatr, phase, freqs = self.calculate_cwt(wavelet, iline, xline, return_phase)
            cwtmatrs.append(cwtmatr)
            if type(phase) == torch.Tensor: phases.append(phase.cpu())
        time = np.linspace(
            float(self.time_cuda.min()),
            float(self.time_cuda.max()),
            cwtmatrs[0].shape[1]
        )

        phases = np.array(phases)
        cwtmatrs = np.array(cwtmatrs)
        print(phases.shape)
        print(cwtmatrs.shape)

        if phases.size > 0:
            ds = xr.Dataset(
                data_vars={
                    wavelet: (['well_name', 'frequency', 'time'], cwtmatrs),
                    f'phase_{wavelet}': (['well_name', 'frequency', 'time'], phases),
                },
                coords=dict(
                    time=time,
                    frequency=freqs.cpu(),
                    well_name=well_names
                ),
            )
        else:
            ds = xr.Dataset(
                data_vars={
                    wavelet: (['well_name', 'frequency', 'time'], cwtmatrs),
                },
                coords=dict(
                    time=time,
                    frequency=freqs.cpu(),
                    well_name=well_names
                ),
            )
        if wavelet not in self.cwt_results:
            self.cwt_results[wavelet] = ds

    def calculate_cwt(self, wavelet, iline: int, xline: int, return_phase=False):

        trace = torch.from_numpy(
            self.ds['raw_data'].sel(iline=iline, xline=xline).values
        ).cuda()

        cwtmatr, freqs = self._calculate_cwt_cached(
            wavelet,
            trace,
            self.time_cuda,
            return_phase=return_phase
        )

        phase = None
        if return_phase:
            phase = torch.angle(cwtmatr)
            phase = torch.cos(phase)

        cwtmatr = torch.abs(cwtmatr)

        return cwtmatr.cpu(), phase.cpu(), freqs.cpu()

    def spectral_decomposition(self, wavelet, output_frequency: Union[int, list], status_callback, batch_size=50_000,
                               include_phase=False):

        data = self.ds["raw_data"].values
        if status_callback:
            status_callback("Iniciando...")
        n_il, n_xl, n_t = data.shape

        traces = data.reshape(-1, n_t)
        traces = torch.as_tensor(traces, dtype=torch.float32)

        result = torch.empty(
            (traces.shape[0], n_t),
            dtype=torch.float32
        )

        if include_phase:
            r_phase = torch.empty(
                (traces.shape[0], n_t),
                dtype=torch.float32
            )
        for i in range(0, traces.shape[0], batch_size):
            if status_callback:
                status_callback(f"Processando: {(i / traces.shape[0]) * 100} %")
            batch = traces[i:i + batch_size].cuda()

            if type(output_frequency) == int:
                _processed = self._calculate_cwt(
                    wavelet,
                    batch,
                    output_frequency
                )  # (batch, time)
            elif type(output_frequency) == list:
                _processed = self._calculate_cwts_mean(
                    wavelet,
                    batch,
                    output_frequency,
                    include_phase=include_phase
                )
            else:
                raise TypeError(f'output_frequency must be int or list')

            if include_phase:
                _processed, phase = _processed
                r_phase[i:i + batch_size] = phase
            result[i:i + batch_size] = _processed.cpu()

            del batch, _processed
            torch.cuda.empty_cache()

        # reconstruir cubo
        cube = result.reshape(n_il, n_xl, n_t)
        data_vars = {
            'data': (['iline', 'xline', 'time'], cube),
        }
        if include_phase:
            r_phase = r_phase.reshape(n_il, n_xl, n_t)

            data_vars = {
                'data': (['iline', 'xline', 'time'], cube),
                'phase': (['iline', 'xline', 'time'], r_phase),
            }
        if str(output_frequency) not in self.processed:
            self.processed[str(output_frequency)] = xr.Dataset(
                data_vars,
                coords=dict(
                    xline=self.ds['xline'].values,
                    iline=self.ds['iline'].values,
                    time=self.ds['time'].values,
                ),
            )
        st.session_state.processing_status = 100
    def correlate_by_cwt(self, wavelet, batch_size, target_z, well_name, threshold, window_size=12):
        data = self.ds["raw_data"].values

        n_il, n_xl, n_t = data.shape

        traces = data.reshape(-1, n_t)
        traces = torch.as_tensor(traces, dtype=torch.float32)

        result = torch.empty(
            (traces.shape[0]),
            dtype=torch.float32
        )
        result_valid = torch.zeros_like(result, dtype=torch.bool)
        target_z = torch.as_tensor(target_z, dtype=torch.float32)
        window_sample = round((window_size / 4) * 2)
        window_size = torch.as_tensor(window_size, dtype=torch.float32)
        kernel_cwt = self.cwt_results[wavelet][wavelet].sel(well_name=well_name).values.T
        kernel_cwt = torch.as_tensor(kernel_cwt, dtype=torch.float32).cuda()
        kernel_cwt = kernel_cwt[torch.where(
            (self.time_cuda >= target_z - window_size) &
            (self.time_cuda <= target_z + window_size)
        )]

        kernel_n = (
                           kernel_cwt - kernel_cwt.mean()
                   ) / (
                           kernel_cwt.std() + 1e-12
                   )
        kernel_n = kernel_n.T

        for i in range(0, traces.shape[0], batch_size):
            print(f"Processing {i} → {i + batch_size}")

            batch = traces[i:i + batch_size].cuda()

            cwtmatr, phase, freqs = self._calculate_cwt_cached(
                wavelet,
                batch,
                self.time_cuda
            )  # (batch, time)
            cwtmatr = cwtmatr.permute(1, 0, 2).contiguous()

            windows = cwtmatr.unfold(
                2,
                kernel_cwt.shape[0],
                1
            )
            mu = windows.mean(dim=(3, 1), keepdim=True)
            sigma = windows.std(dim=(3, 1), keepdim=True)
            windows_n = (windows - mu) / (sigma + 1e-12)
            corr = (windows_n * kernel_n[None, :, None, :]).mean(dim=(1, 3))
            corr_masked = corr.clone()

            corr_masked = torch.where(
                corr_masked < threshold,
                torch.tensor(float('-inf'), device=corr_masked.device),
                corr_masked
            )
            valid = (corr_masked.max(dim=1).values != float('-inf'))
            idx = torch.argmax(corr_masked, dim=1)
            idx = (idx * 4) + 2500 + window_size
            result_valid[i:i + batch_size] = valid.cpu()
            result[i:i + batch_size] = idx.cpu()
            del batch, cwtmatr, freqs

            torch.cuda.empty_cache()

        _map = result.reshape(n_il, n_xl)
        _mask = result_valid.reshape(n_il, n_xl)

        _map[~_mask] = torch.nan
        return _map

    def _calculate_cwts_mean(self, wavelet, trace, ranges_frequencies: list, include_phase=False):
        cwtmatr, freqs = self._calculate_cwt_cached(
            wavelet,
            trace,
            self.time_cuda
        )
        mask = torch.zeros(cwtmatr.shape[0], dtype=torch.bool).cuda()

        for fmin, fmax in ranges_frequencies:
            mask |= (freqs >= fmin) & (freqs <= fmax)

        cwtmatr = cwtmatr[mask]

        if include_phase:
            phase = torch.angle(
                torch.mean(cwtmatr, dim=0)
            )

            phase = torch.cos(phase)

        cwtmatr = torch.sum(
            torch.abs(cwtmatr) ** 2,
            dim=0
        )

        if include_phase:
            return cwtmatr, phase
        else:
            return cwtmatr

    def _calculate_cwt(self, wavelet, trace, output_frequency):
        cwtmatr, freqs = self._calculate_cwt_cached(
            wavelet,
            trace,
            self.time_cuda
        )

        idx = torch.argmin(torch.abs(freqs - output_frequency))
        cwtmatr = cwtmatr[idx, :, :]
        return cwtmatr

    def _calculate_cwt_cached(self, wavelet, trace, time):

        # ----------------------------
        # 1. sampling period (ligero)
        # ----------------------------
        sampling_period = float(torch.diff(time).mean().detach().cpu() / 1000)

        # ----------------------------
        # 2. cache de widths por wavelet
        # ----------------------------
        if wavelet not in self._cwt_cache:
            freqs = self.freqs  # numpy
            # fc = pywt.central_frequency(wavelet)
            # widths_np = fc / (freqs * sampling_period)
            widths_np = pywt.frequency2scale(
                wavelet,
                freqs * sampling_period
            )
            # widths_np = pywt.scale2frequency(wavelet, freqs) / sampling_period
            self._cwt_cache[wavelet] = torch.tensor(widths_np, dtype=torch.float32)

        widths = self._cwt_cache[wavelet]

        # ----------------------------
        # 4. CWT real
        # ----------------------------
        cwtmatr = ptwt.cwt(
            trace,
            widths,
            wavelet,
            sampling_period=sampling_period,
            precision=14,
        )

        if len(cwtmatr) == 2:
            cwtmatr, freqs = cwtmatr
        else: raise NotImplementedError
        # ----------------------------
        # 5. asegurar compatibilidad torch
        # ----------------------------
        freqs = torch.as_tensor(freqs, device=trace.device)

        return cwtmatr, freqs



    def write_netcdf(self, frequency: str, path: str):
        cube: xr.Dataset = self.processed[frequency]

        cube.to_netcdf(path)
