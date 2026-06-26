import streamlit as st
from py_seismic_reader.spectral_decomposition import Cube
import tempfile
from visualizer.seismic import seismic_visualizer
from visualizer.cwt import cwt_view
from visualizer.spectral_decomposition import spectral_decomposicion_view
from visualizer.wells import well_view
import os
st.set_page_config(
    page_title="Dashboard",
    layout="wide"
)

@st.cache_data
def upload_file(uploaded_file):
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

# ===== TOP BAR (simulada) =====

row = st.columns(2, vertical_alignment="center")

with row[0]:
    uploaded_file = st.file_uploader(
        "Carga tu archivo",
        max_upload_size=10 * 1024,
        type='zgy'
    )

# Inicializar estado
if "cube" not in st.session_state:
    st.session_state.cube = None

with row[1]:
    if st.button("Cargar"):
        cube = upload_file(uploaded_file)
        @st.dialog("Confirmación")
        def dialog():
            st.write("Archivo cargado exitosamente")
            if st.button("Salir"):
                st.success("Salir")
                st.rerun()
        dialog()

# ===== SIDEBAR MENU =====
menu = st.sidebar.selectbox(
    "Menú",
    ["Visualizador", "Pozos", "Escalogramas", "Descomposición espectral"]
)

# ===== CONTENIDO PRINCIPAL =====
if menu == "Visualizador":
    st.title("Modulo Sismico")

    seismic_visualizer()

elif menu == "Escalogramas":
    cwt_view()

elif menu == "Pozos":
    well_view()

elif menu == "Descomposición espectral":
    spectral_decomposicion_view()