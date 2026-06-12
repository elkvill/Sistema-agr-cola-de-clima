import datetime
import os
import streamlit as st
import socket

from dominio.entidades import ResultadoConsulta, ConsultaHistorial
from dominio.puertos import ConsultarClima, ServicioIA, RepositorioClima


def inyectar_css_personalizado(ruta):
    posibles = [ruta, os.path.join(os.getcwd(), ruta),
                os.path.join(os.path.dirname(__file__), "..", "..", "styles", "styles.css"),
                "styles/styles.css"]
    for p in posibles:
        if os.path.exists(p):
            with open(p, encoding='utf-8') as f:
                st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
            return
    st.markdown("""
        <style>
        .stApp { background-color: #F5F5DC !important; }
        [data-testid="stSidebar"] { background-color: #1b5e20 !important; }
        </style>
    """, unsafe_allow_html=True)


def _hay_internet():
    try:
        socket.setdefaulttimeout(1.0)
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(("1.1.1.1", 80))
        s.close()
        return True
    except Exception:
        return False


class StreamlitUI:
    def __init__(self, caso_uso: ConsultarClima,
                 servicio_ia: ServicioIA,
                 repositorio: RepositorioClima,
                 ciudades: dict):
        self._caso_uso = caso_uso
        self._servicio_ia = servicio_ia
        self._repositorio = repositorio
        self._ciudades = ciudades
        self._inicializar_sesion()

    def _inicializar_sesion(self):
        if "data_clima" not in st.session_state:
            st.session_state.data_clima = None
        if "analisis_hecho" not in st.session_state:
            st.session_state.analisis_hecho = False
        if "chat_historial" not in st.session_state:
            st.session_state.chat_historial = []
        if "modo_offline" not in st.session_state:
            st.session_state.modo_offline = False
        if "ver_historial" not in st.session_state:
            st.session_state.ver_historial = False

    def ejecutar(self):
        st.title("Sistema Inteligente de Apoyo Agricola")
        st.subheader("Monitoreo Climatico y Decisiones de Cultivo - Nicaragua")

        with st.sidebar:
            st.header("Configuracion")
            ciudad_sel = st.selectbox(
                "Seleccione la Ciudad", list(self._ciudades.keys())
            )
            btn_analizar = st.button("Analizar Clima", use_container_width=True)

            if btn_analizar:
                self._analizar_ciudad(ciudad_sel)

            if st.button("Historial de Consultas", use_container_width=True):
                st.session_state.ver_historial = not st.session_state.ver_historial

            if st.session_state.ver_historial:
                self._mostrar_historial()

        if st.session_state.analisis_hecho and st.session_state.data_clima:
            self._mostrar_dashboard(ciudad_sel)
        else:
            st.info("Seleccione una ciudad y pulse 'Analizar Clima'.")
            st.image(
                "https://images.unsplash.com/photo-1500382017468-9049fed747ef"
                "?auto=format&fit=crop&q=80&w=1000",
                use_container_width=True
            )

    def _analizar_ciudad(self, ciudad_sel):
        with st.spinner("Obteniendo datos y analizando..."):
            try:
                coord = self._ciudades[ciudad_sel]
                if not _hay_internet():
                    raise ConnectionError("Sin internet")

                resultado = self._caso_uso.ejecutar(
                    ciudad_sel, coord["lat"], coord["lon"],
                    coord["es_agricola"]
                )
                st.session_state.modo_offline = False
            except Exception:
                try:
                    resultado = self._caso_uso.ejecutar(
                        ciudad_sel, 0, 0, coord["es_agricola"]
                    )
                    st.session_state.modo_offline = True
                    st.warning("Modo offline - mostrando datos locales guardados.")
                except Exception:
                    st.error("Error al obtener datos y no hay respaldo local.")
                    return

            if resultado.modo_offline:
                analisis_guardado = self._repositorio.cargar_analisis(ciudad_sel)
                if analisis_guardado:
                    resultado.recomendacion_ia = analisis_guardado.get(
                        'recomendacion_ia', ''
                    )

            st.session_state.data_clima = resultado
            st.session_state.analisis_hecho = True
            st.session_state.chat_historial = []
            st.rerun()

    def _mostrar_dashboard(self, ciudad_sel):
        r: ResultadoConsulta = st.session_state.data_clima
        stats = r.stats if r.stats else {}
        dias_fav = sum(
            1 for d in r.clasificacion_dias if d['label'] == "Favorable"
        )

        col_main, col_side = st.columns([2, 1], gap="medium")

        with col_main:
            with st.container(border=True):
                st.markdown("## Dashboard Climatico")
                st.divider()
                st.subheader("Resumen Semanal")
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Promedio Temp",
                          f"{stats.get('media', 'N/A')}C")
                m2.metric("Lluvia Total",
                          f"{stats.get('lluvia_total', 0):.1f}mm")
                m3.metric("Dias Favorables", f"{dias_fav}/7")
                m4.metric("Tendencia", stats.get('tendencia', 'N/A'))

            with st.container(border=True):
                st.subheader("Calendario de Riesgo")
                cols = st.columns(7)
                for i, c in enumerate(r.clasificacion_dias):
                    with cols[i]:
                        fecha = c['date'][-5:]
                        if c['label'] == 'Favorable':
                            st.success(f"{fecha}\n\n**{c['label']}**")
                        elif c['label'] == 'Normal':
                            st.warning(f"{fecha}\n\n**{c['label']}**")
                        else:
                            st.error(f"{fecha}\n\n**{c['label']}**")

        with col_side:
            with st.container(border=True):
                st.markdown("### Situacion Actual")
                st.info(f"**Ciudad:** {ciudad_sel}")
                c1, c2 = st.columns(2)
                c1.metric("Temperatura",
                          f"{r.datos.actual.temp}C")
                c2.metric("Humedad",
                          f"{r.datos.actual.humidity}%")

            with st.container(border=True):
                st.markdown("### Recomendacion")
                a = r.analisis
                if a.status == "FAVORABLE":
                    st.success(a.mensaje)
                elif a.status == "NORMAL":
                    st.warning(a.mensaje)
                else:
                    st.error(a.mensaje)

                st.divider()
                st.markdown("#### Analisis IA")
                st.info(r.recomendacion_ia if r.recomendacion_ia
                        else "No disponible.")

            with st.container(border=True):
                st.markdown("### Asesoria Inteligente")
                with st.expander("Abrir Chat Experto"):
                    for msg in st.session_state.chat_historial:
                        with st.chat_message(msg["role"]):
                            st.write(msg["content"])
                    if prompt := st.chat_input(
                        "Dudas sobre tu cultivo o el clima?"
                    ):
                        self._procesar_chat(prompt, r)

    def _procesar_chat(self, prompt, r):
        with st.chat_message("user"):
            st.write(prompt)
        st.session_state.chat_historial.append(
            {"role": "user", "content": prompt}
        )
        with st.chat_message("assistant"):
            try:
                if st.session_state.modo_offline:
                    st.error("Chat no disponible en modo offline.")
                else:
                    resp = self._servicio_ia.chat(
                        prompt, r.datos.actual.temp,
                        r.datos.actual.humidity, r.datos.actual.precipitation
                    )
                    st.write(resp)
                    st.session_state.chat_historial.append(
                        {"role": "assistant", "content": resp}
                    )
            except Exception as e:
                st.error(f"Error: {e}")

    def _mostrar_historial(self):
        historico = self._repositorio.historial(limit=5)
        if not historico:
            st.write("No hay historial en SQLite.")
        else:
            for h in historico:
                with st.container(border=True):
                    st.markdown(f"**{h.fecha}**")
                    st.markdown(f"**Ciudad:** {h.ciudad}")
                    st.markdown(f"**Temp:** {h.temp}C | **Estado:** {h.status}")
