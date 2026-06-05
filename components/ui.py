import streamlit as st
import os

def renderizar_tarjeta_clima(titulo, valor, unidad, icono=""):
    """
    Renderiza una tarjeta de métrica con estilo glassmorphism.
    """
    st.markdown(f"""
        <div class="weather-card">
            <div class="metric-title">{icono} {titulo}</div>
            <div class="metric-value">{valor}{unidad}</div>
        </div>
    """, unsafe_allow_html=True)

def renderizar_recomendacion(datos_rec):
    """
    Renderiza el banner de recomendación agrícola.
    """
    st.markdown(f"""
        <div class="recommendation-banner banner-{datos_rec['color']}">
            <div>{datos_rec['mensaje']}</div>
        </div>
    """, unsafe_allow_html=True)

def renderizar_indicadores_estadisticas(stats):
    """
    Renderiza una fila de indicadores para el dashboard.
    """
    if not stats: return
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Promedio Semanal", f"{stats['media']:.1f}°C")
    with col2:
        st.metric("Máxima Prevista", f"{stats['max']:.1f}°C")
    with col3:
        st.metric("Mínima Prevista", f"{stats['min']:.1f}°C")
    with col4:
        st.metric("Tendencia", stats['tendencia'])

def inyectar_css_personalizado(ruta_archivo):
    """
    Inyecta el CSS personalizado en la aplicación de Streamlit.
    """
    posibles_rutas = [
        ruta_archivo,
        os.path.join(os.getcwd(), ruta_archivo),
        os.path.join(os.path.dirname(__file__), "..", "styles", "styles.css"),
        "styles/styles.css"
    ]
    
    contenido_css = None
    for ruta in posibles_rutas:
        if os.path.exists(ruta):
            with open(ruta, encoding='utf-8') as f:
                contenido_css = f.read()
                break
    
    if contenido_css:
        st.markdown(f'<style>{contenido_css}</style>', unsafe_allow_html=True)
    else:
        # Estilos de emergencia mínimos
        st.markdown("""
            <style>
            .stApp { background-color: #F5F5DC !important; }
            [data-testid="stSidebar"] { background-color: #1b5e20 !important; }
            </style>
        """, unsafe_allow_html=True)
