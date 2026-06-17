import json
import urllib.request
from typing import Optional

from dominio.entidades import DatosClima, MedicionActual, PronosticoDia
from dominio.puertos import ServicioClima


class OpenWeatherAdapter(ServicioClima):
    def __init__(self, api_key: str):
        self._api_key = api_key

    def obtener_actual(self, lat: float, lon: float) -> Optional[DatosClima]:
        url = (
            "https://api.openweathermap.org/data/2.5/"
            f"weather?lat={lat}&lon={lon}&appid={self._api_key}&units=metric"
        )
        with urllib.request.urlopen(url, timeout=10) as r:
            curr = json.loads(r.read().decode())

        url = (
            "https://api.openweathermap.org/data/2.5/"
            f"forecast?lat={lat}&lon={lon}&appid={self._api_key}&units=metric"
        )
        with urllib.request.urlopen(url, timeout=10) as r:
            fore = json.loads(r.read().decode())

        actual = MedicionActual(
            temperatura=curr["main"]["temp"],
            humedad=curr["main"]["humidity"],
            precipitacion=curr.get("rain", {}).get("1h", 0)
        )

        diario = {}
        for item in fore["list"]:
            d = item["dt_txt"].split()[0]
            if d not in diario:
                diario[d] = {"tmax": -999, "tmin": 999, "precip": 0, "hum": []}
            diario[d]["tmax"] = max(diario[d]["tmax"], item["main"]["temp_max"])
            diario[d]["tmin"] = min(diario[d]["tmin"], item["main"]["temp_min"])
            diario[d]["precip"] += item.get("rain", {}).get("3h", 0)
            diario[d]["hum"].append(item["main"]["humidity"])

        pronostico = []
        for d, s in diario.items():
            pronostico.append(PronosticoDia(
                fecha=d,
                temperatura_max=s["tmax"],
                temperatura_min=s["tmin"],
                precipitacion=s["precip"],
                humedad=round(sum(s["hum"]) / len(s["hum"]), 1)
            ))

        return DatosClima(actual=actual, pronostico=pronostico)
