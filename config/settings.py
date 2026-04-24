# Configuración del Sistema Agrícola Nicaragua

# API Selection
# Opciones: "openmeteo", "openweather"
USE_API = "openmeteo"

# API Keys
OPENWEATHER_API_KEY = "TU_API_KEY_AQUI"
GEMINI_API_KEY = "TU_API_KEY_AQUI"

# Configuración de Ciudades en Nicaragua
# contains: latitude, longitude, is_agricultural
CITIES = {
    "Boaco": {"lat": 12.4722, "lon": -85.6586, "is_agricultural": True},
    "Jinotepe (Carazo)": {"lat": 11.8500, "lon": -86.2000, "is_agricultural": True},
    "Chinandega": {"lat": 12.6289, "lon": -87.1317, "is_agricultural": True},
    "Juigalpa (Chontales)": {"lat": 12.1064, "lon": -85.3645, "is_agricultural": True},
    "Estelí": {"lat": 13.0918, "lon": -86.3538, "is_agricultural": True},
    "Granada": {"lat": 11.9299, "lon": -85.9560, "is_agricultural": True},
    "Jinotega": {"lat": 13.0900, "lon": -86.0000, "is_agricultural": True},
    "León": {"lat": 12.4378, "lon": -86.8780, "is_agricultural": True},
    "Somoto (Madriz)": {"lat": 13.4808, "lon": -86.5821, "is_agricultural": True},
    "Managua": {"lat": 12.1328, "lon": -86.2504, "is_agricultural": False},  # Zona urbana
    "Masaya": {"lat": 11.9744, "lon": -86.0942, "is_agricultural": True},
    "Matagalpa": {"lat": 12.9256, "lon": -85.9175, "is_agricultural": True},
    "Ocotal (Nueva Segovia)": {"lat": 13.6333, "lon": -86.4833, "is_agricultural": True},
    "Rivas": {"lat": 11.4372, "lon": -85.8263, "is_agricultural": True},
    "San Carlos (Río San Juan)": {"lat": 11.1236, "lon": -84.7772, "is_agricultural": True},
    "Puerto Cabezas (RACCN)": {"lat": 14.0333, "lon": -83.3833, "is_agricultural": True},
    "Bluefields (RACCS)": {"lat": 12.0131, "lon": -83.7635, "is_agricultural": True},
}

# Límites Agrícolas (Umbrales)
THRESHOLDS = {
    "temp_max": 35.0,  # Calor extremo
    "temp_min": 15.0,  # Frío inusual
    "rain_heavy": 20.0, # Lluvia intensa (mm)
    "humidity_low": 40.0, # Humedad crítica baja
    "humidity_high": 80.0  # Humedad alta (riesgo hongos)
}
