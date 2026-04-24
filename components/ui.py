import streamlit as st

def render_weather_card(title, value, unit, icon=""):
    """
    Renders a glassmorphism metric card.
    """
    st.markdown(f"""
        <div class="weather-card">
            <div class="metric-title">{icon} {title}</div>
            <div class="metric-value">{value}{unit}</div>
        </div>
    """, unsafe_allow_html=True)

def render_recommendation(rec_data):
    """
    Renders the agricultural recommendation banner.
    """
    st.markdown(f"""
        <div class="recommendation-banner banner-{rec_data['color']}">
            <div>{rec_data['mensaje']}</div>
        </div>
    """, unsafe_allow_html=True)

def render_stats_indicators(stats):
    """
    Renders a row of indicators for the dashboard.
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

def inject_custom_css(file_path):
    """
    Injects the custom CSS into the Streamlit app.
    """
    if os.path.exists(file_path):
        with open(file_path, encoding='utf-8') as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

import os # Missing import check
