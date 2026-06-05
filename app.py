import streamlit as st
import json
import datetime
import os
from config.settings import USAR_API, CLAVE_API_OPENWEATHER, CLAVE_API_GEMINI, CIUDADES
from api.openmeteo_api import obtener_datos_openmeteo
from api.openweather_api import obtener_datos_openweather
from api.gemini_api import generar_recomendacion_ia, chat_agricola
from utils.statistics import calcular_estadisticas
from services.analysis import analizar_condiciones, generar_recomendacion, clasificar_dias
from components.ui import renderizar_tarjeta_clima, renderizar_recomendacion, renderizar_indicadores_estadisticas, inyectar_css_personalizado
from components.charts import graficar_tendencia_temperatura, graficar_pronostico_humedad
from utils.pdf_generator import generar_pdf_diagnostico, generar_pdf_estadistico
from services.database import init_db, save_to_local, load_from_local, load_history

# Configuración de página
st.set_page_config(page_title="SIA Nicaragua", layout="wide", page_icon="None")

# Inyectar CSS
inyectar_css_personalizado("styles/styles.css")

# --- Funciones de Persistencia ---
def guardar_datos(datos):
    """El historial ahora es gestionado automáticamente por un Trigger de auditoría en SQLite."""
    pass

# --- Funciones de Lógica de App ---
import socket

def hay_internet():
    try:
        # Intenta abrir una conexión rápida a Cloudflare vía IP directa (evita la espera de resolución de DNS en Windows)
        socket.setdefaulttimeout(1.0)
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(("1.1.1.1", 80))
        s.close()
        return True
    except Exception:
        return False

@st.cache_data(ttl=3600)
def obtener_clima_consolidado_v3(ciudad_nombre):
    """
    Obtiene el clima según la API seleccionada en configuración.
    """
    if not hay_internet():
        raise ConnectionError("Sin conexión a internet detectada (rápido)")
        
    ciudad_coord = CIUDADES[ciudad_nombre]
    if USAR_API == "openmeteo":
        data = obtener_datos_openmeteo(ciudad_coord["lat"], ciudad_coord["lon"])
    else:
        data = obtener_datos_openweather(ciudad_coord["lat"], ciudad_coord["lon"], CLAVE_API_OPENWEATHER)
        
    if data is None:
        raise ConnectionError("Fallo API, forzando error para no guardar en caché")
    return data

# --- Interfaz Principal ---
def main():
    st.title("Sistema Inteligente de Apoyo Agrícola")
    st.subheader("Monitoreo Climático y Decisiones de Cultivo - Nicaragua")
    
    # Inicializar Base de Datos Local
    init_db()
    
    # Inicializar estado de la sesión
    if "data_clima" not in st.session_state:
        st.session_state.data_clima = None
    if "analisis_hecho" not in st.session_state:
        st.session_state.analisis_hecho = False
    if "chat_historial" not in st.session_state:
        st.session_state.chat_historial = []
    if "modo_offline" not in st.session_state:
        st.session_state.modo_offline = False

    # Barra lateral
    with st.sidebar:
        st.header("Configuración")
        ciudad_sel = st.selectbox("Seleccione la Ciudad", list(CIUDADES.keys()))
        btn_analizar = st.button("Analizar Clima", use_container_width=True)
        
        if btn_analizar:
            mostrar_warning_clima = False
            mostrar_error_clima = False
            
            # Indicador nativo para reemplazar el spinner usando st.empty
            indicador_carga = st.empty()
            indicador_carga.info("Obteniendo datos y analizando...")
            
            try:
                data = obtener_clima_consolidado_v3(ciudad_sel)
                save_to_local(ciudad_sel, data)
                st.session_state.modo_offline = False
            except Exception as e:
                data = load_from_local(ciudad_sel)
                if data:
                        mostrar_warning_clima = True
                        st.session_state.modo_offline = True
                else:
                        mostrar_error_clima = True
            
            # Limpiamos el indicador en esta misma ejecución
            indicador_carga.empty()
            
            if mostrar_warning_clima:
                st.warning("Sin conexión a la API. Mostrando datos locales de respaldo.")
            if mostrar_error_clima:
                st.error("Error al obtener datos y no hay respaldo local disponible.")
                
            # Procesar IA al mismo tiempo que el botón
            if data:
                try:
                    if st.session_state.modo_offline:
                        raise ConnectionError("Modo offline activo: omitiendo llamada a la API de IA")
                    respuesta = generar_recomendacion_ia(data['current'])
                    if "Error de IA" in respuesta or "No se pudo obtener" in respuesta or "no configurada" in respuesta:
                        raise Exception(respuesta)
                    
                    st.session_state.analisis_ia = respuesta
                    st.session_state.analisis_ia_ciudad = ciudad_sel
                    st.session_state.ia_usando_local = False
                except Exception as e:
                    st.session_state.analisis_ia = "Análisis IA no disponible (sin conexión o error de API)."
                    st.session_state.ia_usando_local = False
                        
                st.session_state.data_clima = data
                st.session_state.analisis_hecho = True
                st.session_state.ciudad_actual = ciudad_sel
                # Limpiar chat al cambiar de análisis
                st.session_state.chat_historial = []
                
                # Guardar en Historial (Silencioso)
                condiciones = analizar_condiciones(data['current'])
                rec = generar_recomendacion(ciudad_sel, condiciones)
                login_data = {
                    "fecha": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "ciudad": ciudad_sel,
                    "temp": data['current']['temp'],
                    "status": rec['status']
                }
                guardar_datos(login_data)

        # Estado del Historial
        if "ver_historial" not in st.session_state:
            st.session_state.ver_historial = False
            
        if st.button("Historial de Consultas", use_container_width=True):
            st.session_state.ver_historial = not st.session_state.ver_historial
            
        if st.session_state.ver_historial:
            historico = load_history(limit=5)
            if not historico:
                st.write("No hay historial aún en SQLite.")
            else:
                for h in historico:
                    with st.container(border=True):
                        st.markdown(f"**{h['fecha']}**")
                        st.markdown(f"**Ciudad:** {h['ciudad']}")
                        st.markdown(f"**Temp:** {h['temp']}°C | **Estado:** {h['status']}")
                
    if st.session_state.analisis_hecho and st.session_state.data_clima:
        data = st.session_state.data_clima
        ciudad_sel = st.session_state.ciudad_actual
        
        # Preparar datos adicionales
        stats = calcular_estadisticas(data['forecast'])
        clasificacion = clasificar_dias(data['forecast'])
        dias_favorables = sum(1 for d in clasificacion if d['label'] == "Favorable")
        
        # --- LAYOUT DE DOS COLUMNAS ---
        col_main, col_side = st.columns([2, 1], gap="medium")
        
        # --- COLUMNA IZQUIERDA: DASHBOARD ---
        with col_main:
            with st.container(border=True):
                st.markdown("## Dashboard Climático")
                st.divider()
                
                # Resumen Semanal
                st.subheader("Resumen Semanal")
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Promedio Temp", f"{stats['media']:.1f}°C")
                m2.metric("Lluvia Total", f"{stats['lluvia_total']:.1f}mm")
                m3.metric("Días Favorables", f"{dias_favorables}/7")
                m4.metric("Tendencia", stats['tendencia'])
            
            st.write("")
            
            # Gráficos
            with st.container(border=True):
                st.subheader("Tendencias y Pronóstico")
                graficar_tendencia_temperatura(data['forecast'])
                st.divider()
                graficar_pronostico_humedad(data['forecast'])
            
            st.write("")
            
            # Calendario
            with st.container(border=True):
                st.subheader("Calendario de Riesgo")
                cols_days = st.columns(7)
                for i, c in enumerate(clasificacion):
                    with cols_days[i]:
                        # Uso de componentes nativos de Streamlit para evitar fallos del DOM
                        texto_fecha = c['date'][-5:]
                        if c['label'] == 'Favorable':
                            st.success(f"{texto_fecha}\n\n**{c['label']}**")
                        elif c['label'] == 'Normal':
                            st.warning(f"{texto_fecha}\n\n**{c['label']}**")
                        else:
                            st.error(f"{texto_fecha}\n\n**{c['label']}**")

        # --- COLUMNA DERECHA: ALERTAS Y EXPERTO ---
        with col_side:
            # 1. Clima Actual
            with st.container(border=True):
                st.markdown("### Situación Actual")
                st.info(f"**Ciudad:** {ciudad_sel}")
                c_temp, c_hum = st.columns(2)
                c_temp.metric("Temperatura", f"{data['current']['temp']}°C")
                c_hum.metric("Humedad", f"{data['current']['humidity']}%")
            
            st.write("")
            
            # 2. Recomendaciones
            with st.container(border=True):
                st.markdown("### Recomendación")
                condiciones = analizar_condiciones(data['current'])
                rec = generar_recomendacion(ciudad_sel, condiciones)
                
                # Unificar alertas para mantener el DOM estático
                if rec['status'] == "FAVORABLE": 
                    st.success(rec['mensaje'])
                elif rec['status'] == "NORMAL": 
                    st.warning(rec['mensaje'])
                else: 
                    st.error(rec['mensaje'])
                
                st.divider()
                st.markdown("#### Análisis IA")
                
                texto_ia = st.session_state.get("analisis_ia", "Análisis no disponible.")
                if st.session_state.get("ia_usando_local", False):
                    texto_ia = " **Modo Offline (Respaldo Local)**\n\n" + texto_ia
                    
                st.info(texto_ia)

            st.write("")
            
            # 3. Chat Experto (Expander)
            with st.container(border=True):
                st.markdown("### Asesoría Inteligente")
                st.info("Resuelve dudas específicas de cultivo basadas en el clima actual.")
                
                with st.expander("Abrir Chat Experto"):
                    if "chat_historial" not in st.session_state:
                        st.session_state.chat_historial = []

                    for msg in st.session_state.chat_historial:
                        with st.chat_message(msg["role"]):
                            st.write(msg["content"])

                    if prompt := st.chat_input("Dudas específicas sobre tu cultivo o el clima?"):
                        with st.chat_message("user"):
                            st.write(prompt)
                        st.session_state.chat_historial.append({"role": "user", "content": prompt})
                        
                        with st.chat_message("assistant"):
                            try:
                                if st.session_state.get("modo_offline", False):
                                    st.error("El Asesor Inteligente no está disponible en modo offline (sin conexión a internet).")
                                else:
                                    resp = chat_agricola(prompt, data['current'])
                                    st.write(resp)
                                    st.session_state.chat_historial.append({"role": "assistant", "content": resp})
                            except Exception as e:
                                st.error(f"Error: {e}")

            st.write("")
            
            # 4. Exportar Informes
            with st.container(border=True):
                st.markdown("Generar Informes")
                
                # Generar Reporte 1: Diagnóstico IA
                try:
                    pdf_diag = generar_pdf_diagnostico(
                        ciudad_sel,
                        data['current'],
                        st.session_state.get('analisis_ia', "No disponible"),
                        st.session_state.chat_historial
                    )
                    st.download_button(
                        label="Generar Diagnóstico IA",
                        data=pdf_diag,
                        file_name=f"Diagnostico_IA_{ciudad_sel}.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )
                except Exception as e:
                    st.error(f"Error al generar PDF IA: {e}")

                # Generar Reporte 2: Análisis Estadístico
                try:
                    pdf_stats = generar_pdf_estadistico(
                        ciudad_sel,
                        data['forecast'],
                        stats,
                        condiciones
                    )
                    st.download_button(
                        label="Generar Reporte Estadístico",
                        data=pdf_stats,
                        file_name=f"Reporte_Estadistico_{ciudad_sel}.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )
                except Exception as e:
                    st.error(f"Error al generar PDF Estadístico: {e}")

    else:
        # Bienvenida
        st.info("Seleccione una ciudad en el panel lateral y pulse 'Analizar Clima'.")
        st.image("https://images.unsplash.com/photo-1500382017468-9049fed747ef?auto=format&fit=crop&q=80&w=1000", use_container_width=True)

if __name__ == "__main__":
    main()
