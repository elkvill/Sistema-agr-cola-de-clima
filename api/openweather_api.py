import requests
import streamlit as st

def fetch_openweather_data(lat, lon, api_key):
    """
    Fetches current and 5-day forecast data from OpenWeatherMap.
    Requires a valid API Key.
    """
    if not api_key:
        st.warning("API Key de OpenWeatherMap no configurada.")
        return None

    try:
        # Current Weather
        curr_url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}&units=metric"
        curr_resp = requests.get(curr_url, timeout=10)
        curr_resp.raise_for_status()
        curr_data = curr_resp.json()
        
        # Forecast (5 days / 3 hours)
        fore_url = f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={api_key}&units=metric"
        fore_resp = requests.get(fore_url, timeout=10)
        fore_resp.raise_for_status()
        fore_data = fore_resp.json()
        
        # Mapeo a formato estándar
        result = {
            "current": {
                "temp": curr_data["main"]["temp"],
                "humidity": curr_data["main"]["humidity"],
                "precipitation": curr_data.get("rain", {}).get("1h", 0)
            },
            "forecast": []
        }
        
        # Procesar pronóstico (agrupando por día y calculando max/min real)
        daily_stats = {}
        for item in fore_data["list"]:
            date_str = item["dt_txt"].split(" ")[0]
            if date_str not in daily_stats:
                daily_stats[date_str] = {
                    "temp_max": -999,
                    "temp_min": 999,
                    "precipitation": 0,
                    "humidity": []
                }
            
            stats = daily_stats[date_str]
            stats["temp_max"] = max(stats["temp_max"], item["main"]["temp_max"])
            stats["temp_min"] = min(stats["temp_min"], item["main"]["temp_min"])
            stats["precipitation"] += item.get("rain", {}).get("3h", 0)
            stats["humidity"].append(item["main"]["humidity"])
        
        for date, stats in daily_stats.items():
            result["forecast"].append({
                "date": date,
                "temp_max": stats["temp_max"],
                "temp_min": stats["temp_min"],
                "precipitation": stats["precipitation"],
                "humidity": sum(stats["humidity"]) / len(stats["humidity"])
            })
            
        return result
    except Exception as e:
        st.error(f"Error al conectar con OpenWeatherMap: {e}")
        return None
