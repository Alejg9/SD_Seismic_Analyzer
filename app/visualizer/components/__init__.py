import streamlit as st
import polars as pl
import plotly.graph_objects as go
from visualizer.utils import update_slice
from py_seismic_reader.spectral_decomposition import Cube


def well_selector(cube:Cube, view: str):
    st.subheader('Selecciona un pozo')

    wells = cube.wells

    st.selectbox(
        label='Pozo',
        options=wells + ['Custom'],
        index=0,
        key='current_well'
    )

    if st.session_state.current_well != 'Custom':
        data = cube.well_locations_df.filter(
            pl.col('WellName') == st.session_state.current_well,
        )

        data = data.to_dict(as_series=False)

        st.session_state.xline_value = data['Xline'][0]
        st.session_state.iline_value = data['Inline'][0]
        st.session_state[f"{view}_slider"] = st.session_state[f"{view}_value"]


def wavelet_selector(cube:Cube):
    st.subheader('Parámetros de CWT')
    st.selectbox(
        label='Wavelet',
        options=cube.get_wavelets(),
        index=0,
        key='wavelet'
    )

    wavelet = st.session_state.wavelet

    if wavelet == 'cmor':
        col5, col6, col7 = st.columns(3)

        with col5:
            st.selectbox(
                label='Frecuencia central',
                options=['0.5', '1.5', '2.5'],
                index=0,
                key='center_freq',
            )

        with col6:
            st.selectbox(
                label='Ancho de banda',
                options=['0.5', '1.0', '1.5'],
                index=0,
                key='bandwidth',
            )

        with col7:
            st.selectbox(
                label='Retornar coseno fase',
                options=[False, True],
                index=0,
                key='return_phase',
            )

def section_view(cube:Cube, view: str):
    view_value = f'{view}_value'
    val_ranges = cube.ds[view].values

    st.slider(
        view,
        min_value=int(val_ranges.min()),
        max_value=int(val_ranges.max()),
        value=st.session_state[view_value] if view_value in st.session_state else int(val_ranges.min()),
        key=f'{view}_slider',
        on_change=update_slice
    )

    idx = st.session_state.get(view_value, int(val_ranges.min()))

    img, raw_image = cube.get_image(dim_index=idx, dim=view)

    fig = go.Figure(
        data=go.Heatmap(
            z=raw_image.T,
            x=cube.ds['iline'].values if view == 'xline' else cube.ds['xline'].values,
            y=cube.ds['time'].values if view in ['iline', 'xline'] else cube.ds['iline'].values,
            colorscale=[
                [0, 'rgb(0,247,255)'],
                [0.345959396, 'rgb(0,0,204)'],
                [0.407575638, 'rgb(100,100,100)'],
                [0.44, 'rgb(222,222,222)'],
                [0.55, 'rgb(102,51,0)'],
                [0.7, 'rgb(255,0,0)'],
                [1, 'rgb(255,255,0)']
            ]
        ),
        layout=go.Layout(
            title=f'{view} - {idx}'
        )
    )

    if view == "iline":
        x_title = "Crossline"
        y_title = "Time (ms)"
    elif view == "xline":
        x_title = "Inline"
        y_title = "Time (ms)"
    else:  # view == "time"
        x_title = "Crossline"
        y_title = "Inline"

    fig.update_xaxes(title_text=x_title)
    fig.update_yaxes(
        title_text=y_title,
        autorange="reversed"
    )

    def change_view_section_state():
        st.session_state.view_section = not st.session_state.view_section

    st.button(
        f'Ver sección sísmica',
        key='view_section_button',
        on_click=change_view_section_state
    )

    if st.session_state.view_section:
        st.plotly_chart(
            fig
        )


def slice_selector():
    dims = st.session_state.dims
    st.selectbox(
        'Slice Selector',
        dims,
        key="view",
    )


def output_params(cube, kind:str | None = None):
    if kind:
        st.subheader(f'Parámetros de salida {kind}')
    else:
        st.subheader('Parámetros de salida')
    rows = st.columns(3)
    with rows[0]:
        mode = st.selectbox(
            label='Modo',
            options=['rango', 'puntual'],
            index=1,
            key=f'mode_{kind}' if kind else 'mode'
        )

    with rows[1]:
        if mode == 'rango':
            row = st.columns(3)

            with row[0]:
                st.number_input(
                    'Frecuencia Minima',
                    min_value=cube.freqs.min(),
                    max_value=cube.freqs.max(),
                    value=cube.freqs.min(),
                    key=f'min_freq_{kind}' if kind else 'min_freq'
                )

            with row[1]:
                st.number_input(
                    'Frecuencia Maxima',
                    min_value=cube.freqs.min(),
                    max_value=cube.freqs.max(),
                    value=cube.freqs.max(),
                    key=f'max_freq_{kind}' if kind else 'max_freq'
                )

            with row[2]:
                st.selectbox(
                    'Función de agregación',
                    options=['mean', 'sum', 'median'],
                    index=0,
                    key=f'aggregator_{kind}' if kind else 'aggregator',
                )
        elif mode == 'puntual':

            st.number_input(
                'Frecuencia',
                min_value=cube.freqs.min(),
                max_value=cube.freqs.max(),
                value=cube.freqs.min(),
                key=f'freq_{kind}' if kind else 'freq'
            )