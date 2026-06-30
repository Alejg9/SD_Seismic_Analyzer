import tempfile

from py_seismic_reader.zgy_reader import ZGYCube
from .components import well_selector
from py_seismic_reader.spectral_decomposition import Cube
import streamlit as st
import os
import polars as pl


@st.dialog("Relation")
def relation_dialog(files, kinda='checkshots'):
    for file in files:
        col1, col2 = st.columns(2)
        with col1:
            st.text(file.name)

        with col2:
            st.selectbox(
                'Pozos',
                st.session_state.cube.wells,
                key=f'{file.name}_wellname'
            )

    if st.button("Aceptar"):
        upload_files(files, kinda=kinda)
        st.success("Salir")
        st.rerun()

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
def upload_files(uploaded_files: list, kinda: str):
    for uploaded_file in uploaded_files:
        upload_file(uploaded_file, kinda)
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

    elif kinda == 'checkshots':
        cube.load_check_shot(path=tmp_path, well_name=st.session_state[f'{uploaded_file.name}_wellname'])
    elif kinda == 'logs':
        cube.load_well_log(path=tmp_path, well_name=st.session_state[f'{uploaded_file.name}_wellname'])
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

    row = st.columns(4, vertical_alignment="center", border=True)

    with row[0]:

        _row = st.columns([4,1], vertical_alignment="center")
        with _row[0]:
            uploaded_file = st.file_uploader(
                "Encabezado",
                type='csv'
            )

        with _row[1]:
            if st.button("Cargar", key='well_location_load'):
                upload_file(uploaded_file, kinda='location')
                dialog()

    with row[1]:
        _row = st.columns([4,1], vertical_alignment="center")

        with _row[0]:
            uploaded_file_tops = st.file_uploader(
                "Cimas",
                type='csv'
            )

        with _row[1]:
            if st.button("Cargar", key='well_tops'):
                upload_file(uploaded_file_tops, kinda='tops')

                dialog()

    with row[2]:
        _row = st.columns([4,1], vertical_alignment="center")

        with _row[0]:
            uploaded_file_checkshots = st.file_uploader(
                'Checkshots',
                accept_multiple_files=True,
                type=['csv', 'txt']
            )

        with _row[1]:
            if st.button("Cargar", key='checkshots'):
                relation_dialog(uploaded_file_checkshots, kinda='checkshots')

    with row[3]:
        _row = st.columns([4,1], vertical_alignment="center")

        with _row[0]:
            uploaded_file_logs = st.file_uploader(
                'Registros',
                accept_multiple_files=True,
                type='LAS'
            )

        with _row[1]:
            if st.button("Cargar", key='registros'):
                relation_dialog(uploaded_file_logs, kinda='logs')

    if cube is not None:
        options = []

        if cube.well_locations_df is not None:
            options.append('Localización de Pozos')
            # well_selector(cube, st.session_state.view)

        if cube.fm_df is not None:
            options.append('Cimas de formación')

        if len(cube.check_shots) > 0:
            options.append('Checkshots')

        if len(cube.las) > 0:
            options.append('Registros')

        st.selectbox(
            'Tablas',
            options=options,
            key='table_to_show'
        )
        if st.session_state.table_to_show == 'Localización de Pozos':
            st.subheader('Tabla de localización')
            st.table(
                data=cube.well_locations_df,
            )

        elif st.session_state.table_to_show == 'Cimas de formación':
            st.subheader('Tabla de formación')
            well_selector(cube, st.session_state.view)
            st.table(data=cube.fm_df.filter(pl.col('WellName') == st.session_state.current_well) if st.session_state.current_well != 'Custom' else cube.fm_df)

        elif st.session_state.table_to_show == 'Checkshots':
            st.subheader('Checkshots')
            well_selector(cube, st.session_state.view)

            if st.button('Calcular TWT de cimas'):
                cube.calculate_tops(st.session_state.current_well)

            st.table(
                data=cube.check_shots[st.session_state.current_well] if st.session_state.current_well != 'Custom' else None,
            )
        elif st.session_state.table_to_show == 'Registros':
            st.subheader('Registros')
            well_selector(cube, st.session_state.view)

            if st.button('Calcular TWT para los registros'):
                cube.calculate_twt(st.session_state.current_well)
            st.table(
                data=cube.las[st.session_state.current_well] if st.session_state.current_well != 'Custom' else None,
            )