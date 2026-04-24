# Sistema Inteligente de Apoyo Agricola - SIA Nicaragua

El Sistema Inteligente de Apoyo Agricola (SIA) es una solucion tecnologica avanzada diseñada para la gestion y soporte de decisiones en el sector agropecuario de Nicaragua. Este sistema integra analisis de datos meteorologicos en tiempo real con capacidades de Inteligencia Artificial para ofrecer recomendaciones precisas sobre ciclos de siembra, gestion de riesgos y monitoreo climatico.

## Descripcion del Proyecto

El SIA Nicaragua ha sido desarrollado como una herramienta modular que permite a los productores y tecnicos agricolas visualizar el estado actual y futuro del clima en diversos municipios del pais. La plataforma no solo muestra datos crudos, sino que los procesa a traves de un motor de logica agronomica para determinar si las condiciones son favorables para cultivos especificos, como granos basicos (maiz y frijol).



## Estructura de Directorios

```text
ProyectoExamenSismos/
├── api/                # Conectores de servicios externos
├── components/         # Elementos de UI y graficos
├── config/             # Configuracion y umbrales
├── data/               # Historial de consultas
├── services/           # Logica de negocio
├── styles/             # Estilos visuales
├── utils/              # Herramientas auxiliares
├── app.py              # Aplicacion principal
└── README.md           # Documentacion
```

## Arquitectura del Sistema

El proyecto sigue una estructura modular para facilitar su mantenimiento y escalabilidad:

- **Capa de Aplicacion (app.py)**: Orquesta la interfaz de usuario con Streamlit, gestionando el flujo de datos entre los servicios y los componentes visuales.
- **Capa de APIs (api/)**: Contiene la logica de conexion con servicios externos:
    - **Open-Meteo**: Utilizado para pronosticos gratuitos y de alta precision sin necesidad de llave de API.
    - **OpenWeather**: Alternativa para datos actuales mas granulares.
    - **Google Gemini**: Implementa el cerebro de IA para analisis predictivo y recomendaciones personalizadas.
- **Capa de Servicios (services/)**: Ejecuta el motor de analisis agronomico y clasificacion de riesgos.
- **Capa de Componentes (components/)**: Define la visualizacion, incluyendo graficos de Plotly y tarjetas de diseño personalizado.
- **Capa de Configuracion (config/)**: Centraliza los umbrales climaticos y las coordenadas geograficas de los municipios.

## Funcionalidades Detalladas

### 1. Analisis Climatico Predictivo
El sistema evalua variables criticas para el sector agricola:
- **Temperatura**: Monitoreo de estres termico (umbral > 35 grados Celsius).
- **Precipitacion**: Deteccion de riesgos de inundacion o erosion (> 20mm).
- **Humedad Relativa**: Analisis de riesgos fitosanitarios (hongos o plagas) en rangos extremos (< 40% o > 80%).

### 2. Integracion Resiliente con IA
El modulo de IA (Gemini) cuenta con un sistema de redundancia:
- Intenta primero el modelo **Gemini 2.0 Flash** para maxima velocidad.
- Si hay errores de cuota o disponibilidad, escala automaticamente a **Gemini 1.5 Flash**.
- Como ultimo recurso, utiliza el modelo **Flash Latest**.

### 3. Visualizacion de Datos
- **Tendencias**: Graficos interactivos que comparan temperaturas maximas y minimas previstas para los proximos 7 dias.
- **Distribucion de Humedad**: Graficos de barras que permiten identificar periodos de sequia o saturacion hidrica.
- **Calendario de Riesgo**: Una matriz visual que clasifica los dias futuros segun el indice de favorabilidad agricola.

### 4. Persistencia de Consultas
El sistema almacena automaticamente cada analisis realizado en un archivo historico (`data/data.json`). Esto permite llevar un registro de las condiciones consultadas y las recomendaciones emitidas por la IA para su posterior auditoria o analisis estadistico.

## Configuracion de Seguridad y APIs

Para mantener la integridad del sistema en entornos publicos (como GitHub), se han implementado las siguientes medidas:
- **Archivo api_keys.txt**: Un respaldo local que contiene las llaves de acceso reales.
- **Exclusion via .gitignore**: Archivos sensibles como historicos de datos y llaves de acceso estan excluidos del repositorio.
- **Placeholders**: En `config/settings.py`, las llaves estan reemplazadas por etiquetas descriptivas para evitar fugas de informacion.

## Instrucciones de Instalacion

1. Asegurese de tener instalado Python 3.10 o superior.
2. Clone este repositorio en su maquina local.
3. Instale las bibliotecas necesarias:
   ```bash
   pip install streamlit pandas plotly requests google-generativeai
   ```
4. Configure sus credenciales en `config/settings.py` consultando su archivo de respaldo `api_keys.txt`.
5. Ejecute el comando:
   ```bash
   streamlit run app.py
   ```

## Municipios Soportados
El sistema cuenta con coordenadas preconfiguradas para los 15 departamentos y las 2 regiones autonomas de Nicaragua, incluyendo logica especifica para diferenciar zonas predominantemente urbanas (como Managua) de zonas con alto potencial agricola.

---
Proyecto desarrollado para el area de Administracion de Sistemas Informaticos - SIA Nicaragua.
