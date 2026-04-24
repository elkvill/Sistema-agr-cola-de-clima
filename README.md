# 🌾 Sistema Inteligente de Apoyo Agrícola (SIA Nicaragua)

El **Sistema Inteligente de Apoyo Agrícola (SIA)** es una plataforma avanzada diseñada para proporcionar soporte en la toma de decisiones agronómicas en Nicaragua. Utilizando datos meteorológicos en tiempo real e Inteligencia Artificial, el sistema ofrece recomendaciones personalizadas para optimizar los ciclos de cultivo y mitigar riesgos climáticos.

## 🚀 Características Principales

- **Monitoreo Climático en Tiempo Real**: Integración con las APIs de Open-Meteo y OpenWeather para obtener datos precisos de temperatura, humedad y precipitaciones.
- **Cobertura Nacional**: Análisis específico para los principales municipios de Nicaragua, distinguiendo entre zonas agrícolas y urbanas.
- **Recomendaciones Inteligentes (IA)**: Generación de consejos expertos utilizando modelos de lenguaje de última generación (Google Gemini).
- **Dashboard Estadístico**: Visualización interactiva de tendencias de temperatura y pronósticos de humedad mediante gráficos dinámicos.
- **Calendario de Riesgo**: Clasificación diaria de condiciones (Favorable, Normal, Riesgoso) para planificar actividades de siembra.
- **Chat Experto**: Interfaz de chat integrada para resolver dudas específicas sobre el manejo de cultivos.
- **Diseño Premium**: Interfaz moderna, responsiva y optimizada para una experiencia de usuario fluida.

## 🛠️ Tecnologías Utilizadas

- **Lenguaje**: Python 3.10+
- **Framework Web**: Streamlit
- **Visualización**: Plotly Express
- **Procesamiento de Datos**: Pandas
- **IA**: Google Generative AI (Gemini API)
- **Estilos**: CSS3 personalizado (Glassmorphism)

## 📁 Estructura del Proyecto

```text
ProyectoExamenSismos/
├── api/                # Módulos de conexión con servicios externos (Gemini, Clima)
├── components/         # Componentes visuales y gráficos interactivos
├── config/             # Parámetros de configuración y umbrales agrícolas
├── data/               # Persistencia de datos históricos (JSON)
├── services/           # Lógica de negocio y motores de análisis
├── styles/             # Hojas de estilo personalizadas
├── utils/              # Funciones matemáticas y estadísticas
├── app.py              # Punto de entrada principal de la aplicación
└── README.md           # Documentación del proyecto
```

## ⚙️ Configuración e Instalación

1. **Clonar el repositorio**:
   ```bash
   git clone https://github.com/elkvill/Sistema-agr-cola-de-clima.git
   ```

2. **Instalar dependencias**:
   ```bash
   pip install streamlit pandas plotly google-generativeai requests
   ```

3. **Configurar llaves de API**:
   - Localiza el archivo `config/settings.py`.
   - Reemplaza los placeholders `"TU_API_KEY_AQUI"` con tus llaves reales de OpenWeather y Google Gemini.
   - *Nota: Consulta el archivo local `api_keys.txt` si tienes un respaldo de las mismas.*

4. **Ejecutar la aplicación**:
   ```bash
   streamlit run app.py
   ```

## 📊 Lógica de Análisis

El sistema evalúa las condiciones climáticas basándose en umbrales científicos:
- **Calor Extremo**: > 35°C
- **Frío Crítico**: < 15°C
- **Lluvias Intensas**: > 20mm
- **Humedad Crítica**: < 40% o > 80%

Basado en estos datos, el motor de análisis clasifica los días y genera alertas automáticas para cultivos de granos básicos como maíz y frijol.

---
**Desarrollado por [Elkville]** - *Proyecto de Administración de Sistemas Informáticos*
