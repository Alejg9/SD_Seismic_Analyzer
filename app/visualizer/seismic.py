import streamlit as st
from py_seismic_reader.spectral_decomposition import Cube
import tempfile
import plotly.graph_objects as go
from .utils import update_slice, update_well
import polars as pl

def seismic_visualizer():
    import xarray as xr
    cube: Cube = st.session_state.cube

    if cube is not None:


        dims = st.session_state.dims
        view = st.selectbox(
            'Slice Selector',
            dims,
            key="view",
        )

        view_value = f'{view}_value'
        if cube.well_locations_df is not None:
            st.subheader('Selecciona un pozo')

            wells = cube.well_locations_df['WellName'].unique().to_list()

            st.selectbox(
                label='Pozo',
                options=wells + ['Custom'],
                index=0,
                key='current_well',
                on_change=update_well
            )

            if st.session_state.current_well != 'Custom':
                data = cube.well_locations_df.filter(
                    pl.col('WellName') == st.session_state.current_well,
                )

                data = data.to_dict(as_series=False)

                st.session_state.crossline_value = data['Xline'][0]
                st.session_state.inline_value = data['Inline'][0]

        range = cube.ds[view].values
        st.slider(
            view,
            min_value=int(range.min()),
            max_value=int(range.max()),
            value=st.session_state[view_value] if view_value in st.session_state else int(range.min()),
            key=f'{view}_slider',
            on_change=update_slice
        )

        idx = st.session_state.get(view_value, int(range.min()))

        img, raw_image = cube.get_image(dim_index=idx, dim=view)

        fig = go.Figure(
            data=go.Heatmap(
                z=raw_image.T,
                x=cube.ds['iline'].values if view == 'xline' else cube.ds['xline'].values,
                y=cube.ds['time'].values if view in ['iline', 'xline'] else cube.ds['iline'].values,
                colorscale=[[0, 'rgb(0,0,255)'], [0.43, 'rgb(255,255,255)'], [1, 'rgb(255,0,0)']]
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

        st.plotly_chart(
            fig
        )