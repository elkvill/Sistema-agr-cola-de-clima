import google.generativeai as genai

API_KEY = "TU_API_KEY_AQUI"

try:
    genai.configure(api_key=API_KEY)
    print("Available models:")
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(m.name)
except Exception as e:
    print(f"ERROR: {e}")
