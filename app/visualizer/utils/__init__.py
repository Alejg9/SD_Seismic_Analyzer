import streamlit as st
import polars as pl

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