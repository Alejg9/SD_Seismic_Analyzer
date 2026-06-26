import streamlit as st
from py_seismic_reader.spectral_decomposition import Cube
import tempfile

from py_seismic_reader.zgy_reader import ZGYCube
from visualizer.seismic import seismic_visualizer
from visualizer.cwt import cwt_view
from visualizer.spectral_decomposition import spectral_decomposicion_view
from visualizer.wells import well_view
from visualizer.init import start_window
import json
import os
import polars as pl
st.set_page_config(
    page_title="Dashboard",
    layout="wide"
)

# ===== TOP BAR (simulada) =====

if 'project' in st.session_state:
    row = st.columns(2)

    with row[0]:
        st.title(st.session_state.project)
    with row[1]:
        if st.button('Guardar', key=f'save_{st.session_state.project if "project" in st.session_state else ""}'):
            if 'cube' in st.session_state:
                cube = st.session_state.cube
                project_dir = st.session_state.project_path
                initial_dict = {
                    'name': st.session_state.project,
                    'paths': {
                        'main_zgy': os.path.join(project_dir, 'main.zgy'),
                        'fm_df': os.path.join(project_dir, 'fm_df.csv') if cube.fm_df is not None else None,
                        'well_locations_df': os.path.join(project_dir, 'well_locations_df.csv') if cube.well_locations_df is not None else None,
                    }
                }

                if initial_dict['paths']['main_zgy'] is not None:
                    cube.write_zgy_raw(initial_dict['paths']['main_zgy'])

                if cube.fm_df is not None:
                    fm_df: pl.DataFrame = cube.fm_df
                    fm_df.write_csv(os.path.join(project_dir, 'fm_df.csv'))

                if cube.well_locations_df is not None:
                    well_locations_df: pl.DataFrame = cube.well_locations_df
                    well_locations_df.write_csv(os.path.join(project_dir, 'well_locations_df.csv'))
                with open("/app/projects/" + st.session_state.project + '/config.json', 'w') as fp:
                    json.dump(initial_dict, fp)

else:
    st.title('Seismic Analyzer')
row = st.columns(2, vertical_alignment="center")

# ===== SIDEBAR MENU =====
menu = st.sidebar.selectbox(
    "Menú",
    ["Inicio","Carga de archivos", "Visualizador", "Escalogramas", "Descomposición espectral"]
)

# ===== CONTENIDO PRINCIPAL =====
if menu == 'Inicio':
    start_window()

elif menu == "Carga de archivos":
    well_view()
elif menu == "Visualizador":
    st.title("Modulo Sismico")

    seismic_visualizer()

elif menu == "Escalogramas":
    cwt_view()



elif menu == "Descomposición espectral":
    spectral_decomposicion_view()