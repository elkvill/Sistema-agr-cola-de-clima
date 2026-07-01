import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


def graficar_tendencia_temperatura(pronostico):
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


def graficar_humedad(pronostico):
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


def mostrar_calendario_riesgo(clasificacion_dias):
    st.markdown("#### Calendario de Riesgo")
    cols_cal = st.columns(7)
    for i, c in enumerate(clasificacion_dias):
        with cols_cal[i]:
            fecha = c['fecha'][-5:]
            color = "#d4edda" if c['etiqueta'] == 'Favorable' else "#fff3cd" if c['etiqueta'] == 'Normal' else "#f8d7da"
            text_color = "#155724" if c['etiqueta'] == 'Favorable' else "#856404" if c['etiqueta'] == 'Normal' else "#721c24"
            with st.container():
                estilo_caja = (
                    f"background-color: {color}; color: {text_color}; "
                    "padding: 10px; border-radius: 5px; text-align: center; "
                    "font-weight: bold; font-size: 13px; min-height: 70px; "
                    "display: flex; flex-direction: column; "
                    "justify-content: center; align-items: center; "
                    "border: 1px solid rgba(0,0,0,0.05);"
                )
                st.markdown(
                    f'<div style="{estilo_caja}">'
                    f'<div>{fecha}</div><div style="margin-top: 5px;">{c["etiqueta"]}</div>'
                    f'</div>',
                    unsafe_allow_html=True
                )
