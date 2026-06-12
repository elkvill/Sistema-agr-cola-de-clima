import streamlit as st

from ensamblaje.contenedor import crear_aplicacion
from adaptadores.primarios.streamlit_ui import inyectar_css_personalizado

st.set_page_config(page_title="SIA Nicaragua", layout="wide", page_icon="None")
inyectar_css_personalizado("styles/styles.css")

app = crear_aplicacion()
app.ejecutar()
