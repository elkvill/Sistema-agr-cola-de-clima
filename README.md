# Sistema Inteligente de Apoyo Agrícola (Nicaragua) 🌾

Un sistema profesional basado en **Streamlit** diseñado para proporcionar recomendaciones agronómicas precisas a los agricultores de Nicaragua mediante el análisis de condiciones climáticas en tiempo real.

## 🚀 Características

- **Análisis Multi-Ciudad:** Soporte para las 17 cabeceras departamentales y regionales de Nicaragua.
- **Motor de Recomendación Agrícola:** Lógica personalizada para detectar riesgos de calor extremo, lluvias intensas y sequía.
- **Detección de Zonas Urbanas:** Mensaje inteligente si la ciudad seleccionada no es apta para análisis agrícola.
- **Dashboard Estadístico:** Gráficas interactivas de tendencia térmica y humedad usando Plotly.
- **Abstracción de API:** Listo para funcionar con **Open-Meteo** (sin key) o **OpenWeatherMap** (con key) mediante configuración.
- **Diseño Premium:** Interfaz moderna con *glassmorphism* y CSS personalizado.
- **Persistencia:** Historial de análisis guardado en formato JSON.

## 📂 Estructura del Proyecto

```text
├── app.py                # Punto de entrada principal
├── config/
│   └── settings.py       # Configuración global y ciudades
├── api/
│   ├── openmeteo_api.py  # Integración Open-Meteo
│   └── openweather_api.py # Integración OpenWeather
├── utils/
│   └── statistics.py     # Cálculos con Pandas
├── services/
│   └── analysis.py       # Motor de recomendaciones
├── components/
│   ├── charts.py         # Visualizaciones Plotly
│   └── ui.py            # Componentes de interfaz
├── styles/
│   └── styles.css        # Estilos personalizados
└── data/
    └── data.json         # Historial de consultas
```

## 🛠️ Instalación

1. Asegúrate de tener Python 3.8+ instalado.
2. Instala las dependencias:
   ```bash
   pip install streamlit pandas plotly requests
   ```
3. Ejecuta la aplicación:
   ```bash
   streamlit run app.py
   ```

## ⚙️ Configuración

Para cambiar el proveedor de datos o agregar una API Key, modifica `config/settings.py`:
- `USE_API = "openmeteo"` o `"openweather"`
- `OPENWEATHER_API_KEY = "tu_key_aqui"`

---
**Desarrollado para el Fortalecimiento del Sector Agropecuario Nicaragüense.**
