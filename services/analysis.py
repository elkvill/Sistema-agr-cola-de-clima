from config.settings import THRESHOLDS, CITIES

def analizar_condiciones(current_data):
    """
    Analiza las condiciones actuales comparándolas con los umbrales.
    """
    condiciones = []
    
    if current_data['temp'] >= THRESHOLDS['temp_max']:
        condiciones.append("CALOR_EXTREMO")
    elif current_data['temp'] <= THRESHOLDS['temp_min']:
        condiciones.append("FRIO_BAJO")
        
    if current_data['precipitation'] >= THRESHOLDS['rain_heavy']:
        condiciones.append("LLUVIA_INTENSA")
        
    if current_data['humidity'] <= THRESHOLDS['humidity_low']:
        condiciones.append("HUMEDAD_BAJA")
    elif current_data['humidity'] >= THRESHOLDS['humidity_high']:
        condiciones.append("HUMEDAD_ALTA")
        
    return condiciones

def generar_recomendacion(ciudad, condiciones):
    """
    Genera una recomendación basada en la ciudad y condiciones.
    """
    # Verificación de agricultura
    if not CITIES[ciudad]["is_agricultural"]:
        return {
            "status": "URBAN",
            "mensaje": "Esta zona es predominantemente urbana. No se dispone de datos de suelo o ciclos de cultivo para recomendaciones agrícolas.",
            "color": "urban"
        }
    
    if not condiciones:
        return {
            "status": "FAVORABLE",
            "mensaje": "Condiciones ideales. Apto para siesta de granos básicos (Maíz/Frijol). Mantener monitoreo.",
            "color": "favorable"
        }
        
    if "LLUVIA_INTENSA" in condiciones:
        return {
            "status": "RIESGOSO",
            "mensaje": "Riesgo de inundación o erosión. No se recomienda aplicar fertilizantes ni sembrar hoy.",
            "color": "riesgoso"
        }
        
    if "CALOR_EXTREMO" in condiciones or "HUMEDAD_BAJA" in condiciones:
        return {
            "status": "RIESGOSO",
            "mensaje": "Estrés hídrico detectado. Se recomienda riego temprano y evitar labores de campo pesadas.",
            "color": "riesgoso"
        }
        
    return {
        "status": "NORMAL",
        "mensaje": "Condiciones aceptables pero subóptimas. Monitorear humedad del suelo antes de proceder.",
        "color": "normal"
    }

def clasificar_dias(forecast):
    """
    Clasifica cada día del pronóstico.
    """
    clasificacion = []
    for dia in forecast:
        score = 0
        if dia['temp_max'] >= THRESHOLDS['temp_max']: score += 2
        if dia['precipitation'] >= THRESHOLDS['rain_heavy']: score += 2
        if dia['humidity'] <= THRESHOLDS['humidity_low']: score += 1
        
        if score == 0:
            label = "Favorable"
            color = "green"
        elif score <= 2:
            label = "Normal"
            color = "orange"
        else:
            label = "Riesgoso"
            color = "red"
            
        clasificacion.append({
            "date": dia['date'],
            "label": label,
            "color": color
        })
        
    return clasificacion
