import requests
import streamlit as st

def fetch_openmeteo_data(lat, lon):
    """
    Fetches current and 7-day forecast data from Open-Meteo.
    """
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": "temperature_2m,relative_humidity_2m,precipitation",
        "hourly": "temperature_2m,relative_humidity_2m",
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum",
        "timezone": "auto"
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # Mapeo a formato estándar
        result = {
            "current": {
                "temp": data["current"]["temperature_2m"],
                "humidity": data["current"]["relative_humidity_2m"],
                "precipitation": data["current"]["precipitation"]
            },
            "forecast": []
        }
        
        # Procesar pronóstico diario
        for i in range(len(data["daily"]["time"])):
            result["forecast"].append({
                "date": data["daily"]["time"][i],
                "temp_max": data["daily"]["temperature_2m_max"][i],
                "temp_min": data["daily"]["temperature_2m_min"][i],
                "precipitation": data["daily"]["precipitation_sum"][i],
                # Promediamos la humedad horaria para el día (aprox)
                "humidity": sum(data["hourly"]["relative_humidity_2m"][i*24 : (i+1)*24]) / 24 
                if "hourly" in data else 0
            })
            
        return result
    except Exception as e:
        st.error(f"Error al conectar con Open-Meteo: {e}")
        return None
