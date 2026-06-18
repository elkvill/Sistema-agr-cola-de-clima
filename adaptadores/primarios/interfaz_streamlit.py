import datetime
import os
import streamlit as st
import socket
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from dominio.entidades import ResultadoConsulta, ConsultaHistorial
from dominio.puertos import ConsultarClima, ServicioIA, PuertoAnalisis, PuertoHistorial
from dominio.excepciones import ApiCaidaError, DatosNoEncontradosError


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


def _graficar_tendencia_temperatura(pronostico):
    df = pd.DataFrame([vars(d) for d in pronostico])
    df['etiq_fecha'] = pd.to_datetime(df['fecha']).dt.strftime('%d %b')
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df['etiq_fecha'], y=df['temperatura_max'],
                             name='Max', mode='lines+markers',
                             line=dict(color='#d32f2f')))
    fig.add_trace(go.Scatter(x=df['etiq_fecha'], y=df['temperatura_min'],
                             name='Min', mode='lines+markers',
                             line=dict(color='#1976d2')))
    fig.update_layout(title='Tendencia de Temperatura',
                      plot_bgcolor='rgba(0,0,0,0)',
                      paper_bgcolor='rgba(0,0,0,0)',
                      hovermode='x unified')
    st.plotly_chart(fig, use_container_width=True)


def _graficar_humedad(pronostico):
    if all(getattr(d, 'humedad', 0) == 0 for d in pronostico):
        st.info(
            "Pronostico de humedad no disponible. `configuracion/ajustes.py` para ver estos datos.")
        return
    df = pd.DataFrame([vars(d) for d in pronostico])
    df['etiq_fecha'] = pd.to_datetime(df['fecha']).dt.strftime('%d %b')
    fig = px.bar(df, x='etiq_fecha', y='humedad',
                 title='Pronostico de Humedad',
                 color='humedad', color_continuous_scale='Blues')
    fig.update_layout(plot_bgcolor='rgba(0,0,0,0)',
                      paper_bgcolor='rgba(0,0,0,0)',
                      coloraxis_showscale=False)
    st.plotly_chart(fig, use_container_width=True)


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
                 repositorio_analisis: PuertoAnalisis,
                 repositorio_historial: PuertoHistorial,
                 ciudades: dict):
        self._caso_uso = caso_uso
        self._servicio_ia = servicio_ia
        self._repositorio_analisis = repositorio_analisis
        self._repositorio_historial = repositorio_historial
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
            btn_analizar = st.button(
                "Analizar Clima", use_container_width=True)

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
                    raise ConnectionError("Sin conexión a internet")

                resultado = self._caso_uso.ejecutar(
                    ciudad_sel, coord["lat"], coord["lon"],
                    coord["es_agricola"]
                )
                st.session_state.modo_offline = False
            except (ConnectionError, ApiCaidaError, Exception) as e:
                try:
                    resultado = self._caso_uso.ejecutar(
                        ciudad_sel, 0, 0, coord["es_agricola"]
                    )
                    st.session_state.modo_offline = True
                    st.warning(
                        "Modo offline - mostrando datos locales guardados.")
                except DatosNoEncontradosError as dne:
                    st.error(f"Error de Datos: {dne}")
                    return
                except ApiCaidaError as ace:
                    st.error(f"Error de API: {ace}")
                    return
                except Exception as ex:
                    st.error(
                        f"Error al obtener datos y no hay respaldo local: {ex}")
                    return

            if resultado.modo_offline:
                analisis_guardado = self._repositorio_analisis.cargar_analisis(
                    ciudad_sel)
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
        estadisticas = r.estadisticas if r.estadisticas else {}
        dias_fav = sum(
            1 for d in r.clasificacion_dias if d['etiqueta'] == "Favorable"
        )

        col_main, col_side = st.columns([2, 1], gap="medium")

        with col_main:
            with st.container(border=True):
                st.markdown("## Dashboard Climatico")
                st.divider()
                st.subheader("Resumen Semanal")
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Promedio Temp",
                          f"{estadisticas.get('media', 'N/A')}C")
                m2.metric("Lluvia Total",
                          f"{estadisticas.get('lluvia_total', 0):.1f}mm")
                m3.metric("Dias Favorables", f"{dias_fav}/7")
                m4.metric("Tendencia", estadisticas.get('tendencia', 'N/A'))

            with st.container(border=True):
                st.subheader("Graficos de Pronostico")
                _graficar_tendencia_temperatura(r.datos.pronostico)
                _graficar_humedad(r.datos.pronostico)

            with st.container(border=True):
                st.subheader("Calendario de Riesgo")
                cols = st.columns(7)
                for i, c in enumerate(r.clasificacion_dias):
                    with cols[i]:
                        fecha = c['fecha'][-5:]
                        if c['etiqueta'] == 'Favorable':
                            st.success(f"{fecha}\n\n**{c['etiqueta']}**")
                        elif c['etiqueta'] == 'Normal':
                            st.warning(f"{fecha}\n\n**{c['etiqueta']}**")
                        else:
                            st.error(f"{fecha}\n\n**{c['etiqueta']}**")

        with col_side:
            with st.container(border=True):
                st.markdown("### Situacion Actual")
                st.info(f"**Ciudad:** {ciudad_sel}")
                c1, c2 = st.columns(2)
                c1.metric("Temperatura",
                          f"{r.datos.actual.temperatura}C")
                c2.metric("Humedad",
                          f"{r.datos.actual.humedad}%")

            with st.container(border=True):
                st.markdown("### Recomendacion")
                a = r.analisis
                if a.estado == "FAVORABLE":
                    st.success(a.mensaje)
                elif a.estado == "NORMAL":
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
            
            self._mostrar_descargas_pdf(ciudad_sel, r)

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
                        prompt, r.datos.actual.temperatura,
                        r.datos.actual.humedad, r.datos.actual.precipitacion
                    )
                    st.write(resp)
                    st.session_state.chat_historial.append(
                        {"role": "assistant", "content": resp}
                    )
            except Exception as e:
                st.error(f"Error: {e}")

    def _mostrar_historial(self):
        historico = self._repositorio_historial.obtener_historial(limite=5)
        if not historico:
            st.write("No hay historial en SQLite.")
        else:
            for h in historico:
                with st.container(border=True):
                    st.markdown(f"**{h.fecha}**")
                    st.markdown(f"**Ciudad:** {h.ciudad}")
                    st.markdown(f"**Temp:** {h.temperatura}C | **Estado:** {h.estado}")

    def _mostrar_descargas_pdf(self, ciudad_sel, r):
        st.divider()
        st.markdown("### Descargar Reportes PDF")
        col1, col2 = st.columns(2)

        try:
            from utilidades.generador_pdf import generar_pdf_diagnostico, generar_pdf_estadistico

            with col1:
                datos_actuales = {
                    'temperatura': r.datos.actual.temperatura,
                    'humedad': r.datos.actual.humedad,
                    'precipitacion': r.datos.actual.precipitacion,
                }
                pdf_diag = generar_pdf_diagnostico(
                    ciudad_sel, datos_actuales,
                    r.recomendacion_ia,
                    st.session_state.chat_historial
                )
                st.download_button(
                    label="Reporte de Diagnostico",
                    data=pdf_diag,
                    file_name=f"diagnostico_{ciudad_sel.replace(' ', '_')}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )

            with col2:
                pronostico_lista = [
                    {"fecha": d.fecha, "temperatura_max": d.temperatura_max,
                     "temperatura_min": d.temperatura_min, "precipitacion": d.precipitacion,
                     "humedad": d.humedad}
                    for d in r.datos.pronostico
                ]
                alertas = [
                    f"{c['etiqueta']}: {c['fecha']}" for c in r.clasificacion_dias
                    if c['etiqueta'] == 'Riesgoso'
                ]
                pdf_est = generar_pdf_estadistico(
                    ciudad_sel, pronostico_lista,
                    r.estadisticas or {}, alertas
                )
                st.download_button(
                    label="Reporte Estadistico",
                    data=pdf_est,
                    file_name=f"estadistico_{ciudad_sel.replace(' ', '_')}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
        except ImportError:
            st.warning("Instala fpdf2 para habilitar la descarga de PDFs: pip install fpdf2")
        except Exception as e:
            st.error(f"Error al generar PDF: {e}")
