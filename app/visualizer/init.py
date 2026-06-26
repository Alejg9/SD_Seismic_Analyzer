import streamlit as st
import json
import os

from py_seismic_reader.spectral_decomposition import Cube


def start_window():
    st.header("Proyectos")
    projects = os.listdir("/app/projects")
    if projects:
        for project in projects:
            st.text(project)

            if st.button('Abrir proyecto', key=f'open_{project}'):
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
                    st.session_state.cube = cube
                    st.rerun()
    else:
        st.text("Aún no tienes proyectos")


    st.subheader("Crear nuevo proyecto")

    project_name  = st.text_input("Nombre de proyecto")

    if st.button("Crear nuevo proyecto") and project_name:
        project_path = os.path.join("/app/projects", project_name)
        if not os.path.exists(project_path):
            os.makedirs(project_path)

            initial_dict = {
                'name': project_name,
                'paths': {
                    'main_zgy': None,
                    'fm_df': None,
                    'well_locations_df': None,
                }
            }

            with open(project_path + "/config.json", "w") as fp:
                json.dump(initial_dict, fp)