import os
from fpdf import FPDF
import datetime
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from io import BytesIO

class PDF(FPDF):
    def header(self):
        self.set_font('Helvetica', 'B', 15)
        self.cell(0, 10, 'SIA Nicaragua - Reporte Meteorológico', 0, 1, 'C')
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 8)
        self.cell(0, 10, f'Página {self.page_no()} | Generado el {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}', 0, 0, 'C')

def generar_pdf_diagnostico(ciudad, datos_actuales, recomendacion_ia, historial_chat):
    pdf = PDF()
    pdf.add_page()
    
    # Título del Informe
    pdf.set_font('Helvetica', 'B', 14)
    pdf.cell(0, 10, f'Informe de Diagnóstico Meteorológico: {ciudad}', 0, 1, 'L')
    pdf.ln(5)

    # Resumen Ejecutivo
    pdf.set_font('Helvetica', 'B', 12)
    pdf.cell(0, 10, '1. Resumen Ejecutivo (Estado Actual)', 0, 1, 'L')
    pdf.set_font('Helvetica', '', 11)
    
    # Crear una tabla simple para datos actuales
    data = [
        ['Variable', 'Valor'],
        ['Temperatura', f"{datos_actuales.get('temp')} °C"],
        ['Humedad', f"{datos_actuales.get('humidity')} %"],
        ['Precipitación', f"{datos_actuales.get('precipitation')} mm"],
        ['Viento', f"{datos_actuales.get('windspeed', 'N/A')} km/h"]
    ]
    
    for row in data:
        pdf.cell(40, 8, row[0], 1)
        pdf.cell(40, 8, row[1], 1)
        pdf.ln()
    
    pdf.ln(10)

    # Análisis Predictivo de IA
    pdf.set_font('Helvetica', 'B', 12)
    pdf.cell(0, 10, '2. Análisis Predictivo y Recomendación IA', 0, 1, 'L')
    pdf.set_font('Helvetica', '', 11)
    pdf.multi_cell(0, 8, recomendacion_ia)
    pdf.ln(10)

    # Sección de Chat (Últimas 3 interacciones)
    if historial_chat:
        pdf.set_font('Helvetica', 'B', 12)
        pdf.cell(0, 10, '3. Consultas Relevantes del Chat', 0, 1, 'L')
        pdf.set_font('Helvetica', '', 10)
        
        relevantes = historial_chat[-6:] # 3 pares de pregunta/respuesta
        for msg in relevantes:
            rol = "Usuario" if msg['role'] == "user" else "Experto"
            pdf.set_font('Helvetica', 'B', 10)
            pdf.write(5, f"{rol}: ")
            pdf.set_font('Helvetica', '', 10)
            pdf.write(5, f"{msg['content']}\n")
            pdf.ln(2)

    return bytes(pdf.output())

def generar_pdf_estadistico(ciudad, forecast_data, stats, alertas):
    pdf = PDF()
    pdf.add_page()
    
    # Título del Informe
    pdf.set_font('Helvetica', 'B', 14)
    pdf.cell(0, 10, f'Reporte de Análisis Estadístico: {ciudad}', 0, 1, 'L')
    pdf.ln(5)

    # Estadísticas Descriptivas
    pdf.set_font('Helvetica', 'B', 12)
    pdf.cell(0, 10, '1. Estadísticas Descriptivas de la Semana', 0, 1, 'L')
    pdf.set_font('Helvetica', '', 11)
    
    data_stats = [
        ['Métrica', 'Valor'],
        ['Temperatura Media', f"{stats['media']:.1f} °C"],
        ['Temperatura Máxima', f"{stats['max']:.1f} °C"],
        ['Temperatura Mínima', f"{stats['min']:.1f} °C"],
        ['Lluvia Total Semanal', f"{stats['lluvia_total']:.1f} mm"],
        ['Tendencia Térmica', stats['tendencia']]
    ]
    
    for row in data_stats:
        pdf.cell(60, 8, row[0], 1)
        pdf.cell(60, 8, row[1], 1)
        pdf.ln()
    
    pdf.ln(10)

    # Gráfico de Tendencia
    pdf.set_font('Helvetica', 'B', 12)
    pdf.cell(0, 10, '2. Visualización de Tendencias', 0, 1, 'L')
    
    # Crear gráfico con Matplotlib
    df = pd.DataFrame(forecast_data)
    plt.figure(figsize=(8, 4))
    sns.lineplot(x='date', y='temp_max', data=df, label='Temp Máx', marker='o', color='red')
    sns.lineplot(x='date', y='temp_min', data=df, label='Temp Mín', marker='o', color='blue')
    plt.title(f'Tendencia de Temperatura en {ciudad}')
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    img_buf = BytesIO()
    plt.savefig(img_buf, format='png')
    plt.close()
    
    pdf.image(img_buf, x=10, w=180)
    pdf.ln(5)

    # Alertas de Umbrales
    if alertas:
        pdf.set_font('Helvetica', 'B', 12)
        pdf.cell(0, 10, '3. Alertas de Umbrales Críticos', 0, 1, 'L')
        pdf.set_font('Helvetica', '', 10)
        for alerta in alertas:
            pdf.multi_cell(0, 6, f"- {alerta}")
            
    return bytes(pdf.output())
