import pandas as pd
import numpy as np

def calcular_estadisticas(forecast_data):
    """
    Calcula estadísticas para el pronóstico de temperatura.
    forecast_data: lista de diccionarios con 'temp_max' y 'temp_min'.
    """
    if not forecast_data:
        return None
        
    df = pd.DataFrame(forecast_data)
    
    # Trabajamos con el promedio diario
    df['temp_avg'] = (df['temp_max'] + df['temp_min']) / 2
    
    stats = {
        "media": df['temp_avg'].mean(),
        "mediana": df['temp_avg'].median(),
        "std": df['temp_avg'].std(),
        "max": df['temp_max'].max(),
        "min": df['temp_min'].min(),
        "lluvia_total": df['precipitation'].sum(),
        "tendencia": "Estable"
    }
    
    # Calcular tendencia (pendiente simple)
    if len(df) > 1:
        diff = df['temp_avg'].iloc[-1] - df['temp_avg'].iloc[0]
        if diff > 0.5:
            stats["tendencia"] = "En aumento"
        elif diff < -0.5:
            stats["tendencia"] = "En descenso"
            
    return stats
