import streamlit as st
import json
import datetime
import os
from config.settings import USE_API, OPENWEATHER_API_KEY, CITIES
from api.openmeteo_api import fetch_openmeteo_data
from api.openweather_api import fetch_openweather_data
from api.gemini_api import generar_recomendacion_ia, chat_agricola
from utils.statistics import calcular_estadisticas
from services.analysis import analizar_condiciones, generar_recomendacion, clasificar_dias
from components.ui import render_weather_card, render_recommendation, render_stats_indicators, inject_custom_css
from components.charts import plot_temperature_trend, plot_humidity_forecast

# Configuración de página
st.set_page_config(page_title="SIA Nicaragua", layout="wide", page_icon="None")

# Inyectar CSS
inject_custom_css("styles/styles.css")

# Estilos específicos para el área principal usando data-testid
st.markdown("""
    <style>
    /* 1. Fondo del cuerpo de la página */
    div[data-testid="stAppViewContainer"] {
        background-color: #fdfdfd !important;
    }

    /* 2. Tarjetas de Métricas (Metrics) */
    div[data-testid="stMetric"] {
        background-color: #ffffff;
        border-radius: 12px;
        padding: 15px 20px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05), 0 1px 3px rgba(0, 0, 0, 0.1);
        border: 1px solid #f0f2f6;
    }

    /* 3. Contenedores Verticales y Espaciado (Resumen Semanal) */
    div[data-testid="stVerticalBlock"] {
        gap: 1.5rem !important;
    }

    /* 4. Bloque de Recomendación (Destaque Lateral) */
    div[data-testid="element-container"]:has(div.stAlert) {
        border-left: 5px solid #2e7d32;
        border-radius: 4px 12px 12px 4px;
    }

    /* Ajuste para evitar que los textos se corten */
    div[data-testid="stVerticalBlock"] > div {
        overflow: visible !important;
    }
    
    /* Mejorar visibilidad de títulos de métricas */
    div[data-testid="stMetricLabel"] > div {
        font-weight: 600;
        color: #4b5563;
    }
    </style>
    """, unsafe_allow_html=True)

# --- Funciones de Persistencia ---
def guardar_datos(datos):
    """Guarda el resultado del análisis en data/data.json"""
    file_path = "data/data.json"
    historico = []
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            try:
                historico = json.load(f)
            except:
                historico = []
    
    historico.append(datos)
    with open(file_path, "w") as f:
        json.dump(historico, f, indent=4)

# --- Funciones de Lógica de App ---
@st.cache_data(ttl=3600)
def obtener_clima_consolidado(ciudad_nombre):
    """
    Obtiene el clima según la API seleccionada en configuración.
    """
    ciudad_coord = CITIES[ciudad_nombre]
    if USE_API == "openmeteo":
        return fetch_openmeteo_data(ciudad_coord["lat"], ciudad_coord["lon"])
    else:
        return fetch_openweather_data(ciudad_coord["lat"], ciudad_coord["lon"], OPENWEATHER_API_KEY)

# --- Interfaz Principal ---
def main():
    st.title("Sistema Inteligente de Apoyo Agrícola")
    st.subheader("Monitoreo Climático y Decisiones de Cultivo - Nicaragua")
    
    # Barra lateral
    with st.sidebar:
        st.header("Configuración")
        ciudad_sel = st.selectbox("Seleccione la Ciudad", list(CITIES.keys()))
        btn_analizar = st.button("Analizar Clima", use_container_width=True)
        
        st.divider()
        st.info(f"API en uso: {USE_API.upper()}")
        if st.checkbox("Ver Historial de Consultas"):
            if os.path.exists("data/data.json"):
                with open("data/data.json", "r") as f:
                    st.write(json.load(f)[-5:]) # Últimas 5
            else:
                st.write("No hay historial aún.")

    # Cuerpo Principal
    if btn_analizar:
        data = obtener_clima_consolidado(ciudad_sel)
        
        if data:
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
                
                st.markdown("<br>", unsafe_allow_html=True)
                
                # Gráficos
                with st.container(border=True):
                    st.subheader("Tendencias y Pronóstico")
                    plot_temperature_trend(data['forecast'])
                    st.divider()
                    plot_humidity_forecast(data['forecast'])
                
                st.markdown("<br>", unsafe_allow_html=True)
                
                # Calendario
                with st.container(border=True):
                    st.subheader("Calendario de Riesgo")
                    cols_days = st.columns(7)
                    for i, c in enumerate(clasificacion):
                        with cols_days[i]:
                            st.markdown(f"""
                                <div style="background:{c['color']}; color:white; padding:10px; border-radius:10px; text-align:center; box-shadow: 0 2px 4px rgba(0,0,0,0.1); min-height: 80px;">
                                    <small>{c['date'][-5:]}</small><br><b>{c['label']}</b>
                                </div>
                            """, unsafe_allow_html=True)

            # --- COLUMNA DERECHA: ALERTAS Y EXPERTO ---
            with col_side:
                # 1. Clima Actual
                with st.container(border=True):
                    st.markdown("### Situación Actual")
                    st.info(f"**Ciudad:** {ciudad_sel}")
                    c_temp, c_hum = st.columns(2)
                    c_temp.metric("Temperatura", f"{data['current']['temp']}°C")
                    c_hum.metric("Humedad", f"{data['current']['humidity']}%")
                
                st.markdown("<br>", unsafe_allow_html=True)
                
                # 2. Recomendaciones
                with st.container(border=True):
                    st.markdown("### Recomendación")
                    condiciones = analizar_condiciones(data['current'])
                    rec = generar_recomendacion(ciudad_sel, condiciones)
                    
                    if rec['status'] == "FAVORABLE": st.success(rec['mensaje'])
                    elif rec['status'] == "NORMAL": st.warning(rec['mensaje'])
                    else: st.error(rec['mensaje'])
                    
                    st.divider()
                    st.markdown("#### Análisis IA")
                    with st.spinner("Consultando..."):
                        try:
                            rec_ia = generar_recomendacion_ia(data['current'])
                            st.info(rec_ia)
                        except:
                            st.warning("IA no disponible.")

                st.markdown("<br>", unsafe_allow_html=True)
                
                # 3. Chat
                with st.container(border=True):
                    st.markdown("### Chat Experto")
                    pregunta = st.text_input("¿Dudas específicas?", key="chat_v4")
                    if st.button("Consultar Chat"):
                        if pregunta:
                            resp = chat_agricola(pregunta, data['current'])
                            st.markdown(f"**Respuesta:** {resp}")

            # 5. Guardar en Historial (Silencioso)
            login_data = {
                "fecha": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "ciudad": ciudad_sel,
                "temp": data['current']['temp'],
                "status": rec['status']
            }
            guardar_datos(login_data)
            
        else:
            st.error("Error al obtener datos.")
    else:
        # Bienvenida
        st.info("Seleccione una ciudad en el panel lateral y pulse 'Analizar Clima'.")
        st.image("https://images.unsplash.com/photo-1500382017468-9049fed747ef?auto=format&fit=crop&q=80&w=1000")

if __name__ == "__main__":
    main()
