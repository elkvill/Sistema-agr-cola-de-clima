import streamlit as st

from dominio.entidades import ResultadoConsulta
from dominio.puertos import ConsultarClima, ServicioIA, RepositorioClima, VerificadorConectividad
from dominio.excepciones import ApiCaidaError, DatosNoEncontradosError

from adaptadores.primarios.componente_graficos import (
    graficar_tendencia_temperatura, graficar_humedad, mostrar_calendario_riesgo
)
from adaptadores.primarios.componente_chat import renderizar_chat
from adaptadores.primarios.componente_reportes import renderizar_descargas_pdf


class StreamlitUI:

    def __init__(self, caso_uso: ConsultarClima,
                 servicio_ia: ServicioIA,
                 repositorio: RepositorioClima,
                 ciudades: dict,
                 verificador_conectividad: VerificadorConectividad):
        self._caso_uso = caso_uso
        self._servicio_ia = servicio_ia
        self._repositorio = repositorio
        self._ciudades = ciudades
        self._verificador_conectividad = verificador_conectividad
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
        if "ultima_ciudad" not in st.session_state:
            st.session_state.ultima_ciudad = None

    def ejecutar(self):
        st.title("Sistema Inteligente de Apoyo Agricola")
        st.subheader("Monitoreo Climatico y Decisiones de Cultivo - Nicaragua")

        with st.sidebar:
            st.header("Configuracion")
            ciudad_sel = st.selectbox(
                "Seleccione la Ciudad", list(self._ciudades.keys())
            )

            if st.session_state.ultima_ciudad != ciudad_sel:
                st.session_state.analisis_hecho = False
                st.session_state.data_clima = None
                st.session_state.ultima_ciudad = ciudad_sel
                st.rerun()

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
                if not self._verificador_conectividad.hay_conexion():
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
                analisis_guardado = self._repositorio.cargar_analisis(
                    ciudad_sel)
                if analisis_guardado:
                    resultado.recomendacion_ia = analisis_guardado.get(
                        'recomendacion_ia', ''
                    )

            st.session_state.data_clima = resultado
            st.session_state.analisis_hecho = True
            st.session_state.chat_historial = []

    def _mostrar_dashboard(self, ciudad_sel):
        r: ResultadoConsulta = st.session_state.data_clima
        estadisticas = r.estadisticas if r.estadisticas else {}
        dias_fav = sum(
            1 for d in r.clasificacion_dias if d['etiqueta'] == "Favorable"
        )
        st.markdown("## Dashboard Climático")
        st.markdown(f"### Ciudad: {ciudad_sel}")
        st.divider()

        # Sección 1: Situación Actual e Indicadores (Métricas en 1 sola fila plana)
        st.markdown("### Situación Actual e Indicadores")
        m1, m2, m3, m4, m5, m6 = st.columns(6)
        m1.metric("Temp. Actual", f"{r.datos.actual.temperatura}°C")
        m2.metric("Hum. Actual", f"{r.datos.actual.humedad}%")
        m3.metric("Promedio Temp.", f"{estadisticas.get('media', 'N/A')}°C")
        m4.metric("Lluvia Total", f"{estadisticas.get('lluvia_total', 0):.1f}mm")
        m5.metric("Días Favorables", f"{dias_fav}/7")
        m6.metric("Tendencia", estadisticas.get('tendencia', 'N/A'))
        st.divider()

        # Sección 2: Gráficos de Pronóstico y Calendario de Riesgo (Centro)
        st.markdown("### Pronóstico Semanal y Riesgo")
        with st.container():
            graficar_tendencia_temperatura(r.datos.pronostico)
        with st.container():
            graficar_humedad(r.datos.pronostico)

        mostrar_calendario_riesgo(r.clasificacion_dias)
        st.divider()

        # Sección 3: Recomendación Agrícola y Análisis de la IA (Abajo, a pantalla completa)
        st.markdown("### Recomendaciones de Cultivo")

        # Recomendación Local en contenedor aislado
        a = r.analisis
        color_local = "#d4edda" if a.estado == "FAVORABLE" else "#fff3cd" if a.estado == "NORMAL" else "#f8d7da"
        text_local = "#155724" if a.estado == "FAVORABLE" else "#856404" if a.estado == "NORMAL" else "#721c24"
        border_local = "#c3e6cb" if a.estado == "FAVORABLE" else "#ffeeba" if a.estado == "NORMAL" else "#f5c6cb"
        with st.container():
            st.markdown(
                f'<div style="background-color: {color_local}; color: {text_local}; border: 1px solid {border_local}; padding: 15px; border-radius: 6px; font-weight: bold; margin-bottom: 15px;">'
                f'Recomendación Local: {a.mensaje}'
                f'</div>',
                unsafe_allow_html=True
            )

        # Análisis IA en contenedor aislado (con el color azul informativo original)
        with st.container():
            contenido_ia = r.recomendacion_ia if r.recomendacion_ia else "Análisis de inteligencia artificial no disponible."
            st.info(contenido_ia)
        st.divider()

        # Sección 4: Chat de Asesoría y Descarga de Reportes (Pie de página)
        col_chat, col_rep = st.columns([2, 1], gap="medium")

        with col_chat:
            renderizar_chat(self._servicio_ia, r)

        with col_rep:
            renderizar_descargas_pdf(ciudad_sel, r)

    def _mostrar_historial(self):
        historico = self._repositorio.obtener_historial(limite=5)
        if not historico:
            st.write("No hay historial en SQLite.")
        else:
            for h in historico:
                with st.container(border=True):
                    st.markdown(f"**{h.fecha}**")
                    st.markdown(f"**Ciudad:** {h.ciudad}")
                    st.markdown(f"**Temp:** {h.temperatura}C | **Estado:** {h.estado}")
