import streamlit as st

from py_seismic_reader.spectral_decomposition import Cube
from .seismic import seismic_visualizer
import polars as pl
import os
def spectral_decomposicion_view():
    cube = st.session_state.cube
    st.title("Módulo de descomposición espectral")

    if cube is not None:
        status_box = st.empty()
        batch_size = st.number_input(
            'Tamaño de batch',
            min_value=1,
            max_value=10_000,
            value=2000,
            key='batch_size'
        )

        def update(msg):
            st.session_state.job_status = msg
            status_box.text(msg)
        if st.button('Ejecutar descomposición espectral en cubo completo'):

            cube.spectral_decomposition(
                wavelet=st.session_state.wavelet,
                output_frequency=st.session_state.freq
                if 'freq' in st.session_state
                else [(st.session_state.min_freq, st.session_state.max_freq)],
                batch_size=batch_size,
                include_phase=st.session_state.return_phase if 'return_phase' in st.session_state else False,
                status_callback=update
            )

            temp_path = f'/app/{st.session_state.project}/temp_files/{hash(st.session_state.wavelet)}_sd.zgy'

            if not os.path.exists(temp_path):
                update(
                    'Escribiendo arrchivo ZGY...'
                )

                if not os.path.exists(f"/app/{st.session_state.project}/temp_files/"): os.makedirs(f"/app/{st.session_state.project}/temp_files/")
                cube.write_zgy(
                    str(st.session_state.freq)
                    if 'freq' in st.session_state
                    else str([(st.session_state.min_freq, st.session_state.max_freq)]),
                    path=temp_path,
                    var='data'
                )

            st.session_state.sd_path = temp_path

            if 'return_phase' in st.session_state and st.session_state.return_phase:
                phase_temp_path = temp_path.replace('_sd', '_sd_phase')
                if not os.path.exists(f"/app/{st.session_state.project}/temp_files/"): os.makedirs(
                    f"/app/{st.session_state.project}/temp_files/")
                if not os.path.exists(phase_temp_path):
                    cube.write_zgy(
                        str(st.session_state.freq)
                        if 'freq' in st.session_state
                        else str([(st.session_state.min_freq, st.session_state.max_freq)]),
                        path=phase_temp_path,
                        var='phase'
                    )
                st.session_state.phase_path = phase_temp_path
            update("✅ Listo para descarga")
            st.session_state.job_status = "ready"

        if "sd_path" in st.session_state:
            with open(st.session_state.sd_path, "rb") as f:
                st.download_button(
                    label="Descargar descomposición espectral",
                    data=f,
                    file_name="spectral_decomposition.zgy",
                    mime="application/octet-stream",
                    on_click=update,
                    args=("Procesando descarga de descomposición espectral...",)
                )

        if 'return_phase' in st.session_state and st.session_state.return_phase and 'phase_path' in st.session_state:
            with open(st.session_state.phase_path, "rb") as f:
                st.download_button(
                    label="Descargar coseno phase",
                    data=f,
                    file_name="spectral_decomposition_cos_phase.zgy",
                    mime="application/octet-stream",
                    on_click=update,
                    args=('Procesando descarga de coseno fase...',)
                )


        update(
            "Listo"
        )


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
