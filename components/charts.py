import plotly.express as px
import pandas as pd
import streamlit as st

def graficar_tendencia_temperatura(datos_pronostico):
    """
    Grafica la tendencia de temperatura usando Plotly.
    """
    df = pd.DataFrame(datos_pronostico)
    df['fecha_formateada'] = pd.to_datetime(df['date']).dt.strftime('%d %b')
    
    fig = px.line(df, x='fecha_formateada', y=['temp_max', 'temp_min'],
                  labels={'value': 'Temperatura (°C)', 'fecha_formateada': 'Fecha'},
                  title='Tendencia de Temperatura Próximos Días',
                  markers=True,
                  color_discrete_sequence=['#d32f2f', '#1976d2'])
    
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        legend_title_text='Variable',
        hovermode="x unified"
    )
    
    st.plotly_chart(fig)

def graficar_pronostico_humedad(datos_pronostico):
    """
    Grafica el pronóstico de humedad usando Plotly.
    """
    df = pd.DataFrame(datos_pronostico)
    df['fecha_formateada'] = pd.to_datetime(df['date']).dt.strftime('%d %b')
    
    fig = px.bar(df, x='fecha_formateada', y='humidity',
                 labels={'humidity': 'Humedad (%)', 'fecha_formateada': 'Fecha'},
                 title='Pronóstico de Humedad Relativa',
                 color='humidity',
                 color_continuous_scale='Blues')
    
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        coloraxis_showscale=False
    )
    
    st.plotly_chart(fig)
