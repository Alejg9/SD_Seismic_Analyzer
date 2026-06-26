FROM pytorch/pytorch:2.10.0-cuda13.0-cudnn9-runtime

WORKDIR /app

LABEL authors="aleja"

RUN pip install --break-system-packages --no-cache-dir numpy polars xarray opencv-python-headless PyWavelets ptwt pyzgy plotly streamlit