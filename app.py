import streamlit as st

from ensamblaje.contenedor import crear_aplicacion
from adaptadores.primarios.interfaz_streamlit import inyectar_css_personalizado

st.set_page_config(page_title="SIA Nicaragua", layout="wide", page_icon="None")
inyectar_css_personalizado("estilos/estilos.css")

app = crear_aplicacion()
app.ejecutar()
