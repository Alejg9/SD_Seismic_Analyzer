from .components import slice_selector, well_selector, wavelet_selector, output_params
import streamlit as st
import cv2
import numpy as np

def blend_view():

    cube = st.session_state.cube
    slice_selector()
    well_selector(cube, st.session_state.view)
    wavelet_selector(cube)
    wavelet = st.session_state.wavelet
    bandwidth = st.session_state.bandwidth if 'bandwidth' in st.session_state else None
    center_freq = st.session_state.center_freq if 'center_freq' in st.session_state else None

    if wavelet == 'cmor' and center_freq and bandwidth:
        wavelet = f'{wavelet}-{center_freq}-{bandwidth}'

    output_params(cube, kind='R')
    output_params(cube, kind='G')
    output_params(cube, kind='B')

    r_cwtmatr = cube.apply_cwt_to_image(
        dim=st.session_state.view,
        dim_index=st.session_state[f'{st.session_state.view}_value'],
        wavelet=wavelet,
        mode=st.session_state.mode_R,
        min_freq=st.session_state.min_freq_R if 'min_freq_R' in st.session_state else None,
        max_freq=st.session_state.max_freq_R if 'max_freq_R' in st.session_state else None,
        agg=st.session_state.aggregator_R if 'aggregator_R' in st.session_state else None,
        output_freq=st.session_state.freq_R if 'freq_R' in st.session_state else None,
        return_phase=st.session_state.return_phase_R if 'return_phase_R' in st.session_state else None,
        time_slider=st.session_state.time_slider_R if 'time_slider_R' in st.session_state else None,
        return_matr=True
    )

    g_cwtmatr = cube.apply_cwt_to_image(
        dim=st.session_state.view,
        dim_index=st.session_state[f'{st.session_state.view}_value'],
        wavelet=wavelet,
        mode=st.session_state.mode_G,
        min_freq=st.session_state.min_freq_G if 'min_freq_G' in st.session_state else None,
        max_freq=st.session_state.max_freq_G if 'max_freq_G' in st.session_state else None,
        agg=st.session_state.aggregator_G if 'aggregator_G' in st.session_state else None,
        output_freq=st.session_state.freq_G if 'freq_G' in st.session_state else None,
        return_phase=st.session_state.return_phase_G if 'return_phase_G' in st.session_state else None,
        time_slider=st.session_state.time_slider_G if 'time_slider_G' in st.session_state else None,
        return_matr=True
    )


    b_cwtmatr = cube.apply_cwt_to_image(
        dim=st.session_state.view,
        dim_index=st.session_state[f'{st.session_state.view}_value'],
        wavelet=wavelet,
        mode=st.session_state.mode_B,
        min_freq=st.session_state.min_freq_B if 'min_freq_B' in st.session_state else None,
        max_freq=st.session_state.max_freq_B if 'max_freq_B' in st.session_state else None,
        agg=st.session_state.aggregator_B if 'aggregator_B' in st.session_state else None,
        output_freq=st.session_state.freq_B if 'freq_B' in st.session_state else None,
        return_phase=st.session_state.return_phase_B if 'return_phase_B' in st.session_state else None,
        time_slider=st.session_state.time_slider_B if 'time_slider_B' in st.session_state else None,
        return_matr=True
    )

    global_min = min(
        r_cwtmatr.min(),
        g_cwtmatr.min(),
        b_cwtmatr.min(),
    )

    global_max = max(
        r_cwtmatr.max(),
        g_cwtmatr.max(),
        b_cwtmatr.max(),
    )

    def normalize(x):
        return ((x - global_min) / (global_max - global_min) * 255).clip(0, 255).astype(np.uint8)

    img_R = normalize(r_cwtmatr)
    img_G = normalize(g_cwtmatr)
    img_B = normalize(b_cwtmatr)

    img = cv2.merge([
        img_R.astype(np.uint8),
        img_B.astype(np.uint8),
        img_G.astype(np.uint8),
    ])

    st.image(img, caption='RGB Image', channels='RGB', output_format='PNG', clamp=True)