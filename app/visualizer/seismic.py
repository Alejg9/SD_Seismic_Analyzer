import streamlit as st
from py_seismic_reader.spectral_decomposition import Cube
from .utils import update_slice
import plotly.graph_objects as go
from visualizer.components import well_selector, section_view, slice_selector


def seismic_visualizer():
    cube: Cube = st.session_state.cube

    if cube is not None:

        view = st.session_state.view

        if cube.wells is not None:
            well_selector(cube, view)

        slice_selector()
        section_view(cube, view)