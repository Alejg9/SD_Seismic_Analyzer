import streamlit as st
import polars as pl
from py_seismic_reader.spectral_decomposition import Cube


def cwt_view():

    st.title('Análisis de transformada de ondícula continua')


    cube = st.session_state.cube

    if cube is not None:
        if cube.well_locations_df is not None:
            st.subheader('Selecciona un pozo')

            wells = cube.well_locations_df['WellName'].unique().to_list()

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

                st.session_state.crossline_value = data['Xline'][0]
                st.session_state.inline_value = data['Inline'][0]

        col1, col2 = st.columns(2)

        with col1:
            inline = st.selectbox(
                label='Inline',
                options=st.session_state.dims,
                key='inline_dim'
            )

            inline_value = st.number_input(
                label='',
                key='inline_value',
                min_value=cube.ds[inline].values.min(),
                max_value=cube.ds[inline].values.max(),
            )

        with col2:
            crossline = st.selectbox(
                label='Xline',
                options=st.session_state.dims,
                index=1,
                key='xline_dim'
            )

            crossline_value = st.number_input(
                label='',
                key='crossline_value',
                min_value=cube.ds[crossline].values.min(),
                max_value=cube.ds[crossline].values.max(),
            )

        wavelet = st.selectbox(
            label='Wavelet',
            options=cube.get_wavelets(),
            index=0,
            key='wavelet'
        )

        if wavelet == 'cmor':
            col5, col6 = st.columns(2)

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
        col3, col4 = st.columns(2)
        with col3:
            fig = cube.plot_trace(inline=inline_value, crossline=crossline_value)
            if 'current_well' in st.session_state and st.session_state.current_well != 'Custom' and cube.fm_df is not None:
                fig = cube.add_tops_to_fig(
                    fig=fig,
                    well_name=st.session_state.current_well,
                    x=[-100, 150]
                )
            st.plotly_chart(
                fig,
            )

        with col4:
            if  wavelet == 'cmor' and center_freq and bandwidth:
                wavelet = f'{wavelet}-{center_freq}-{bandwidth}'

            fig = cube.plot_cwt(
                    inline=inline_value,
                    crossline=crossline_value,
                    wavelet=wavelet,
                )
            if 'current_well' in st.session_state and st.session_state.current_well != 'Custom' and cube.fm_df is not None:
                fig = cube.add_tops_to_fig(
                    fig=fig,
                    well_name=st.session_state.current_well,
                    x=[cube.freqs.min(), cube.freqs.max()],
                    subplot_col=1,
                    subplot_row=2,
                )
                fig = cube.add_tops_to_fig(
                    fig=fig,
                    well_name=st.session_state.current_well,
                    x=[cube.freqs.min(), cube.freqs.max()],
                    subplot_col=1,
                    subplot_row=1,
                )
            st.plotly_chart(
                fig
            )