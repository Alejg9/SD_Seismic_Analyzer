import streamlit as st
from .seismic import seismic_visualizer
from .components import wavelet_selector, well_selector, slice_selector, output_params

import os


def get_freqcuency():
    frequency = None

    if 'freq' in st.session_state:
        frequency = str(st.session_state.freq)
    elif 'min_freq' in st.session_state and 'max_freq' in st.session_state:
        frequency = str([(st.session_state.min_freq, st.session_state.max_freq)])

    return frequency
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

        frequency = get_freqcuency()
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
                    frequency,
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
                        frequency,
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
                    file_name=f"spectral_decomposition_{st.session_state.wavelet}_{frequency}.zgy",
                    mime="application/octet-stream",
                    on_click=update,
                    args=("Procesando descarga de descomposición espectral...",)
                )

        if 'return_phase' in st.session_state and st.session_state.return_phase and 'phase_path' in st.session_state:
            with open(st.session_state.phase_path, "rb") as f:
                st.download_button(
                    label="Descargar coseno phase",
                    data=f,
                    file_name=f"spectral_decomposition_cos_phase_{st.session_state.wavelet}_{frequency}.zgy",
                    mime="application/octet-stream",
                    on_click=update,
                    args=('Procesando descarga de coseno fase...',)
                )


        update(
            "Listo"
        )
        slice_selector()
        well_selector(cube, st.session_state.view)
        wavelet_selector(cube)
        wavelet = st.session_state.wavelet
        bandwidth = st.session_state.bandwidth if 'bandwidth' in st.session_state else None
        center_freq = st.session_state.center_freq if 'center_freq' in st.session_state else None

        if wavelet == 'cmor' and center_freq and bandwidth:
            wavelet = f'{wavelet}-{center_freq}-{bandwidth}'
        print(wavelet)
        output_params(cube)
        fig = cube.apply_cwt_to_image(
            dim=st.session_state.view,
            dim_index=st.session_state[f'{st.session_state.view}_value'],
            wavelet=wavelet,
            mode=st.session_state.mode,
            min_freq=st.session_state.min_freq if 'min_freq' in st.session_state else None,
            max_freq=st.session_state.max_freq if 'max_freq' in st.session_state else None,
            agg=st.session_state.aggregator if 'aggregator' in st.session_state else None,
            output_freq=st.session_state.freq if 'freq' in st.session_state else None,
            return_phase=st.session_state.return_phase if 'return_phase' in st.session_state else None,
            time_slider=st.session_state.time_slider if 'time_slider' in st.session_state else None,
        )

        st.plotly_chart(fig)
