import streamlit as st
from .components import well_selector, wavelet_selector
def cwt_view():

    st.title('Análisis de transformada de ondícula continua')


    cube = st.session_state.cube

    if cube is not None:
        if cube.well_locations_df is not None:
            well_selector(cube, st.session_state.view)
            if 'TWT' in cube.las[st.session_state.current_well].columns:
                st.selectbox(
                    'Selecciona un registro',
                    options=['Sísmica Original'] + cube.las[st.session_state.current_well].columns,
                    key=f'{st.session_state.current_well}_las',
                )
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

        wavelet_selector(cube)
        wavelet = st.session_state.wavelet
        bandwidth = st.session_state.bandwidth if 'bandwidth' in st.session_state else None
        center_freq = st.session_state.center_freq if 'center_freq' in st.session_state else None

        col3, col4 = st.columns(2)
        with col3:
            fig = cube.plot_trace(
                inline=inline_value,
                crossline=crossline_value,
                well_name=st.session_state.current_well if 'current_well' in st.session_state else None,
                log = st.session_state[f'{st.session_state.current_well}_las'] if f'{st.session_state.current_well}_las' in st.session_state else None
            )


            if 'current_well' in st.session_state and st.session_state.current_well != 'Custom' and cube.fm_df is not None:
                fig = cube.add_tops_to_fig(
                    fig=fig,
                    well_name=st.session_state.current_well,
                    x=[
                        cube.las[st.session_state.current_well][st.session_state[f'{st.session_state.current_well}_las']].min(),
                        cube.las[st.session_state.current_well][st.session_state[f'{st.session_state.current_well}_las']].max()
                        ]
                        if f'{st.session_state.current_well}_las' in st.session_state
                        and st.session_state[f'{st.session_state.current_well}_las'] != 'Sísmica Original'
                        else [-100, 150]
                )
            st.plotly_chart(
                fig,
            )

        with col4:
            if  wavelet == 'cmor' and center_freq and bandwidth:
                wavelet = f'{wavelet}-{center_freq}-{bandwidth}'

            cwt_fig, phase_fig = cube.plot_cwt(
                    inline=inline_value,
                    crossline=crossline_value,
                    wavelet=wavelet,
                )
            if 'current_well' in st.session_state and st.session_state.current_well != 'Custom' and cube.fm_df is not None:
                cwt_fig = cube.add_tops_to_fig(
                    fig=cwt_fig,
                    well_name=st.session_state.current_well,
                    x=[cube.freqs.min(), cube.freqs.max()],
                )
                if phase_fig is not None:
                    phase_fig = cube.add_tops_to_fig(
                        fig=phase_fig,
                        well_name=st.session_state.current_well,
                        x=[cube.freqs.min(), cube.freqs.max()],
                    )

            st.plotly_chart(
                cwt_fig
            )

        if phase_fig is not None and st.session_state.return_phase:
            st.plotly_chart(
                phase_fig,
            )