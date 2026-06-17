import os

# Configuración del Sistema Agrícola Nicaragua

# Selección de API
# Opciones: "openmeteo", "openweather"

USAR_API = "openweather"

# API Keys (desde variables de entorno - nunca hardcodear)
CLAVE_API_OPENWEATHER = os.getenv("CLAVE_API_OPENWEATHER", "")
CLAVE_API_GROQ = os.getenv("CLAVE_API_GROQ", "")

# Configuración de Ciudades en Nicaragua
# Contiene: latitud, longitud, es_agricola
CIUDADES = {
    "Boaco": {"lat": 12.4722, "lon": -85.6586, "es_agricola": True},
    "Jinotepe (Carazo)": {"lat": 11.8500, "lon": -86.2000, "es_agricola": True},
    "Chinandega": {"lat": 12.6289, "lon": -87.1317, "es_agricola": True},
    "Juigalpa (Chontales)": {"lat": 12.1064, "lon": -85.3645, "es_agricola": True},
    "Estelí": {"lat": 13.0918, "lon": -86.3538, "es_agricola": True},
    "Granada": {"lat": 11.9299, "lon": -85.9560, "es_agricola": True},
    "Jinotega": {"lat": 13.0900, "lon": -86.0000, "es_agricola": True},
    "León": {"lat": 12.4378, "lon": -86.8780, "es_agricola": True},
    "Somoto (Madriz)": {"lat": 13.4808, "lon": -86.5821, "es_agricola": True},

    "Managua": {"lat": 12.1328, "lon": -86.2504, "es_agricola": False},
    "Masaya": {"lat": 11.9744, "lon": -86.0942, "es_agricola": True},
    "Matagalpa": {"lat": 12.9256, "lon": -85.9175, "es_agricola": True},
    "Ocotal (Nueva Segovia)": {"lat": 13.6333, "lon": -86.4833, "es_agricola": True},
    "Rivas": {"lat": 11.4372, "lon": -85.8263, "es_agricola": True},
    "San Carlos (Río San Juan)": {"lat": 11.1236, "lon": -84.7772, "es_agricola": True},
    "Puerto Cabezas (RACCN)": {"lat": 14.0333, "lon": -83.3833, "es_agricola": True},
    "Bluefields (RACCS)": {"lat": 12.0131, "lon": -83.7635, "es_agricola": True},
}

# Límites Agrícolas (Umbrales)
UMBRALES = {
    "temp_max": 35.0,        # Calor extremo
    "temp_min": 15.0,        # Frío inusual
    "rain_heavy": 15.0,      # Lluvia intensa (mm)
    "humidity_low": 40.0,    # Humedad baja (%)
    "humidity_high": 90.0,   # Humedad muy alta (%)
    "viento_max": 20.0,      # Viento fuerte (km/h)
}
