import os
import socket
import streamlit as st
from dominio.puertos import VerificadorConectividad


def inyectar_css_personalizado(ruta):
    posibles = [ruta, os.path.join(os.getcwd(), ruta),
                os.path.join(os.path.dirname(__file__), "..",
                             "..", "estilos", "estilos.css"),
                "estilos/estilos.css"]
    for p in posibles:
        if os.path.exists(p):
            with open(p, encoding='utf-8') as f:
                st.markdown(f'<style>{f.read()}</style>',
                            unsafe_allow_html=True)
            return
    st.markdown("""
        <style>
        .stApp { background-color: #F5F5DC !important; }
        [data-testid="stSidebar"] { background-color: #1b5e20 !important; }
        </style>
    """, unsafe_allow_html=True)


class VerificadorConectividadSocket(VerificadorConectividad):

    def hay_conexion(self) -> bool:
        try:
            socket.setdefaulttimeout(1.0)
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect(("1.1.1.1", 80))
            s.close()
            return True
        except Exception:
            return False
