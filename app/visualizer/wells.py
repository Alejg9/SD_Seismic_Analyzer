import tempfile
from py_seismic_reader.spectral_decomposition import Cube
import streamlit as st
import os

@st.dialog("Confirmación")
def dialog():
    st.write("Archivo cargado exitosamente")
    if st.button("Salir"):
        st.success("Salir")
        st.rerun()

@st.cache_data
def upload_cube(uploaded_file):
    if uploaded_file is None:
        return

    with tempfile.NamedTemporaryFile(delete=False, suffix=".zgy") as tmp:
        tmp.write(uploaded_file.getbuffer())
        tmp_path = tmp.name

    cube = Cube(tmp_path)  # ahora sí es un path válido
    os.remove(tmp_path)
    dims = list(
        cube.ds.dims.keys()
    )
    st.session_state.dims = dims
    st.session_state.cube = cube

@st.cache_data
def upload_file(uploaded_file, kinda):
    if "cube" not in st.session_state:
        return
    if uploaded_file is None:
        return
    with tempfile.NamedTemporaryFile(delete=False, suffix=".zgy") as tmp:
        tmp.write(uploaded_file.getbuffer())
        tmp_path = tmp.name

    cube = st.session_state.cube

    if kinda == 'location':
        cube.load_well_location(tmp_path)
    elif kinda == 'tops':
        cube.load_fm_df(
            tmp_path,
            has_header=True,
            separator=','
        )
    os.remove(tmp_path)

def well_view():
    st.header('Carga Archivos')
    st.subheader('Cubo sismico')
    row = st.columns(2)
    with row[0]:
        uploaded_file = st.file_uploader(
            "Carga tu archivo",
            max_upload_size=10 * 1024,
            type='zgy'
        )

    with row[1]:
        if st.button("Cargar"):
            cube = upload_cube(uploaded_file)

            dialog()
    st.subheader('Pozos')

    cube = st.session_state.cube if 'cube' in st.session_state else None

    row = st.columns(4, vertical_alignment="center")

    with row[0]:
        uploaded_file = st.file_uploader(
            "Encabezado",
            type='csv'
        )

    with row[1]:
        if st.button("Cargar", key='well_location_load'):
            upload_file(uploaded_file, kinda='location')
            dialog()

    with row[2]:
        uploaded_file_tops = st.file_uploader(
            "Cimas",
            type='csv'
        )


    with row[3]:
        if st.button("Cargar", key='well_tops'):
            upload_file(uploaded_file_tops, kinda='tops')

            dialog()

    if cube is not None:
        if cube.well_locations_df is not None:
            st.subheader('Tabla de localización')
            st.table(
                data=cube.well_locations_df,
            )

        if cube.fm_df is not None:
            st.subheader('Tabla de formación')
            st.table(data=cube.fm_df)
