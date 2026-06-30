# import streamlit as st
# from py_seismic_reader.spectral_decomposition import Cube
# import tempfile
# import plotly.graph_objects as go
#
# if 'cube' is not None:
#
#     row = st.columns(4)
#
#     with row[0]:
#         st.number_input(
#             'Min Frequency',
#             value=1,
#             min_value=1,
#             max_value=125,
#         )
#
#     with row[1]:
#         st.number_input(
#             'Max Frequency',
#             value=125,
#             min_value=1,
#             max_value=125,
#         )
#     with row[2]:
#         st.selectbox(
#             'Wavelet',
#             ['morl', 'mexh', 'cmor1.5-1.0'],
#             key="wavelet",
#         )
#     with row[3]:
#         st.checkbox(
#             'Include Phase',
#             disabled=True if not st.session_state.wavelet.startswith('cmor') else False,
#         )
#
#
#     st.button(
#         'Execute Spectral Decomposition',
#     )