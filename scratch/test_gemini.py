import google.generativeai as genai
import sys

API_KEY = "TU_API_KEY_AQUI"

try:
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
    response = model.generate_content("Hola, ¿puedes leerme?")
    print(f"RESPONSE 1.5: {response.text}")
except Exception as e:
    print(f"ERROR 1.5: {e}")

try:
    model2 = genai.GenerativeModel('gemini-2.0-flash')
    response2 = model2.generate_content("Hola, ¿puedes leerme?")
    print(f"RESPONSE 2.0: {response2.text}")
except Exception as e:
    print(f"ERROR 2.0: {e}")
