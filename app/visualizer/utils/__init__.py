import streamlit as st
import polars as pl

import os
import json

from py_seismic_reader.spectral_decomposition import Cube
def syncronize_well(view):
    cube = st.session_state.cube

    if st.session_state.current_well == "Custom":
        return None

    df = cube.well_locations_df.filter(
        pl.col("WellName") == st.session_state.current_well
    )

    if df.is_empty():
        return None

    row = df.row(0, named=True)


    if view == st.session_state.dims[0]:
        return row["Inline"]

    if view == st.session_state.dims[1]:
        return row["Xline"]

    return None

def update_slice():
    value = st.session_state[f'{st.session_state.view}_slider']
    value = syncronize_well(st.session_state.view) or value
    view = f'{st.session_state.view}_value'

    if st.session_state.get(view) != value:

        st.session_state[view] = value
        st.session_state[f'{st.session_state.view}_slider'] = value



def update_well():
    update_slice()


def open_project(project: str):
    st.session_state.project = project
    st.session_state.project_path = os.path.join("/app/projects", project)

    config = json.load(open("/app/projects/" + project + '/config.json'))['paths']

    if config['main_zgy']:
        cube = Cube(config['main_zgy'])

        if config['well_locations_df']:
            cube.load_well_location(config['well_locations_df'])
        if config['fm_df']:
            cube.load_fm_df(config['fm_df'], has_header=True, separator=',')
        st.session_state.dims = list(
            cube.ds.dims.keys()
        )

        if config['check_shots_dfs']:
            for shot, well_name in config['check_shots_dfs']:
                cube.load_check_shot(shot,well_name, separator=',')

        if config['las_dfs']:
            for las, well_name in config['las_dfs']:
                cube.load_well_log_csv(las,well_name)
        st.session_state.view = st.session_state.dims[0]
        st.session_state.cube = cube
        st.session_state.view_section = True
        st.rerun()


