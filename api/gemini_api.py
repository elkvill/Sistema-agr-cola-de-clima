import google.generativeai as genai
import streamlit as st
from config.settings import CLAVE_API_GEMINI


def configurar_gemini():
    """
    Configura la API de Gemini.
    """
    if not CLAVE_API_GEMINI:
        return False
    try:
        genai.configure(api_key=CLAVE_API_GEMINI)
        return True
    except Exception:
        return False


def generar_recomendacion_ia(datos_clima):
    """
    Genera recomendación agrícola intentando varios modelos por si hay problemas de cuota.
    """
    if not configurar_gemini():
        return "API Key de Gemini no configurada en settings.py"

    # Intentamos solo con los dos modelos más rápidos para no congelar la app si falla
    modelos = [
        'gemini-1.5-flash', 
        'gemini-flash-latest'
    ]

    ultimo_error = ""
    for model_name in modelos:
        try:
            model = genai.GenerativeModel(model_name)
            prompt = f"""
            Actúa como experto agrícola en Nicaragua.
            Datos: Temp {datos_clima.get('temp')}°C, Humedad {datos_clima.get('humidity')}%, Lluvia {datos_clima.get('precipitation')}mm.
            Genera una recomendación breve y clara.
            """
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            ultimo_error = str(e)
            if "429" in ultimo_error:
                continue  # Probar el siguiente si es error de cuota
            if "404" in ultimo_error:
                continue  # Probar el siguiente si no se encuentra
            return f"Error de IA ({model_name}): {ultimo_error}"

    return f"No se pudo obtener respuesta de la IA. Posible cuota agotada o modelo no disponible. Detalles: {ultimo_error}"


def chat_agricola(pregunta, datos_clima):
    """
    Chat inteligente con los mismos fallbacks.
    """
    if not configurar_gemini():
        return "Chat no disponible."

    # Lista de modelos optimizada
    modelos = [
        'gemini-1.5-flash', 
        'gemini-flash-latest'
    ]

    for model_name in modelos:
        try:
            model = genai.GenerativeModel(model_name)
            contexto = f"Clima: {datos_clima.get('temp')}°C, {datos_clima.get('humidity')}%, {datos_clima.get('precipitation')}mm."
            full_prompt = f"{contexto}\n\nPregunta: {pregunta}"
            response = model.generate_content(full_prompt)
            return response.text
        except Exception:
            continue

    return "Lo siento, el servicio de IA está saturado o no disponible en este momento."
