import streamlit as st

from py_seismic_reader.spectral_decomposition import Cube
from .seismic import seismic_visualizer
import polars as pl
def spectral_decomposicion_view():
    cube = st.session_state.cube
    st.title("Módulo de descomposición espectral")

    if cube is not None:

        st.subheader('Parámetros de salida')
        mode = st.selectbox(
            label='Modo',
            options=['rango', 'puntual']
        )

        if mode == 'rango':
            row = st.columns(2)

            with row[0]:
                st.number_input(
                    'Frecuencia Minima',
                    min_value=cube.freqs.min(),
                    max_value=cube.freqs.max(),
                    value=cube.freqs.min(),
                    key='min_freq'
                )

            with row[1]:
                st.number_input(
                    'Frecuencia Maxima',
                    min_value=cube.freqs.min(),
                    max_value=cube.freqs.max(),
                    value=cube.freqs.max(),
                    key='max_freq'
                )

            st.selectbox(
                'Función de agregación',
                options=['mean', 'sum', 'median'],
                index=0,
                key='aggregator',
            )
        elif mode == 'puntual':

            st.number_input(
                'Frecuencia',
                min_value=cube.freqs.min(),
                max_value=cube.freqs.max(),
                value=cube.freqs.min(),
                key='freq'
            )

        st.subheader('Parámetros de CWT')
        wavelet = st.selectbox(
            label='Wavelet',
            options=cube.get_wavelets(),
            index=0,
            key='wavelet'
        )
        if wavelet == 'cmor':
            col5, col6, col7 = st.columns(3)

            with col5:
                center_freq = st.selectbox(
                    label='Frecuencia central',
                    options=['0.5', '1.5', '2.5'],
                    index=0,
                    key='center_freq',
                )

            with col6:
                bandwidth = st.selectbox(
                    label='Ancho de banda',
                    options=['0.5', '1.0', '1.5'],
                    index=0,
                    key='bandwidth',
                )

            with col7:
                return_phase = st.selectbox(
                    label='Retornar coseno fase',
                    options=[False, True],
                    index=0,
                    key='return_phase',
                )

        seismic_visualizer()

        if wavelet == 'cmor' and center_freq and bandwidth:
            wavelet = f'{wavelet}-{center_freq}-{bandwidth}'

        if         st.button(
            'Ejecutar descomposición espectral',
        ):
            fig = cube.apply_cwt_to_image(
                dim=st.session_state.view,
                dim_index=st.session_state[f'{st.session_state.view}_value'],
                wavelet=wavelet,
                mode=mode,
                min_freq=st.session_state.min_freq if 'min_freq' in st.session_state else None,
                max_freq=st.session_state.max_freq if 'max_freq' in st.session_state else None,
                agg=st.session_state.aggregator if 'aggregator' in st.session_state else None,
                output_freq=st.session_state.freq if 'freq' in st.session_state else None,
                return_phase=st.session_state.return_phase if 'return_phase' in st.session_state else None,
            )

            st.plotly_chart(fig)
