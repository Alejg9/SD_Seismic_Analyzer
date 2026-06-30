import streamlit as st
import json
import os

from .utils import open_project

def start_window():
    st.header("Proyectos")
    projects = os.listdir("/app/projects")
    if projects:
        for project in projects:
            st.text(project)

            if st.button('Abrir proyecto', key=f'open_{project}'):
               open_project(project)
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
        st.rerun()