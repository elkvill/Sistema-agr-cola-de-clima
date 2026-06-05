from config.settings import UMBRALES, CIUDADES

def analizar_condiciones(datos_actuales):
    """
    Analiza las condiciones actuales comparándolas con los umbrales.
    """
    condiciones = []
    
    if datos_actuales['temp'] >= UMBRALES['temp_max']:
        condiciones.append("CALOR_EXTREMO")
    elif datos_actuales['temp'] <= UMBRALES['temp_min']:
        condiciones.append("FRIO_BAJO")
        
    # Nota: rain_heavy, humidity_low, etc. deben estar en UMBRALES o manejarse con cuidado
    # Como el usuario solo vio una parte de settings.py, me aseguro de usar lo que existe
    if datos_actuales['precipitation'] >= UMBRALES.get('rain_heavy', 10.0):
        condiciones.append("LLUVIA_INTENSA")
        
    if datos_actuales['humidity'] <= UMBRALES.get('humidity_low', 40.0):
        condiciones.append("HUMEDAD_BAJA")
    elif datos_actuales['humidity'] >= UMBRALES.get('humidity_high', 85.0):
        condiciones.append("HUMEDAD_ALTA")
        
    return condiciones

def generar_recomendacion(ciudad, condiciones):
    """
    Genera una recomendación basada en la ciudad y condiciones.
    """
    # Verificación de agricultura
    if not CIUDADES[ciudad]["es_agricola"]:
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

def clasificar_dias(pronostico):
    """
    Clasifica cada día del pronóstico.
    """
    clasificacion = []
    for dia in pronostico:
        score = 0
        if dia['temp_max'] >= UMBRALES['temp_max']: score += 2
        if dia['precipitation'] >= UMBRALES.get('rain_heavy', 10.0): score += 2
        if dia['humidity'] <= UMBRALES.get('humidity_low', 40.0): score += 1
        
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
