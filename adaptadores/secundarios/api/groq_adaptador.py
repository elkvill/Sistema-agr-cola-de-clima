import json
import urllib.request
import urllib.error

from dominio.puertos import ServicioIA


class GroqAdapter(ServicioIA):
    def __init__(self, api_key: str):
        self._api_key = api_key
        self._url = "https://api.groq.com/openai/v1/chat/completions"
        self._model = "llama-3.1-8b-instant"

    def generar_recomendacion(self, temperatura: float, humedad: float,
                               precipitacion: float) -> str:
        prompt = (
            "Actua como experto agricola en Nicaragua. "
            f"Datos: Temp {temperatura}C, Humedad {humedad}%, "
            f"Lluvia {precipitacion}mm. "
            "Genera una recomendacion breve y clara para el agricultor."
        )
        return self._llamar_groq(prompt)

    def chat(self, pregunta: str, temperatura: float, humedad: float,
             precipitacion: float) -> str:
        contexto = f"Clima: {temperatura}C, {humedad}%, {precipitacion}mm."
        prompt = f"{contexto}\n\nPregunta: {pregunta}"
        return self._llamar_groq(prompt)

    def _llamar_groq(self, prompt: str) -> str:
        try:
            body = json.dumps({
                "model": self._model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.7, "max_tokens": 300
            }).encode()
            req = urllib.request.Request(
                self._url, data=body,
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "Content-Type": "application/json",
                    "User-Agent": "Python/3.0"
                }
            )
            with urllib.request.urlopen(req, timeout=15) as r:
                resp = json.loads(r.read().decode())
                return resp["choices"][0]["message"]["content"]
        except urllib.error.HTTPError as e:
            if e.code == 429:
                return "Error: Cuota de API agotada."
            return f"Error de IA: HTTP {e.code}"
        except Exception as e:
            return f"Error al conectar con Groq: {str(e)[:80]}"
