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
            temp=curr["main"]["temp"],
            humidity=curr["main"]["humidity"],
            precipitation=curr.get("rain", {}).get("1h", 0)
        )

        daily = {}
        for item in fore["list"]:
            d = item["dt_txt"].split()[0]
            if d not in daily:
                daily[d] = {"tmax": -999, "tmin": 999, "precip": 0, "hum": []}
            daily[d]["tmax"] = max(daily[d]["tmax"], item["main"]["temp_max"])
            daily[d]["tmin"] = min(daily[d]["tmin"], item["main"]["temp_min"])
            daily[d]["precip"] += item.get("rain", {}).get("3h", 0)
            daily[d]["hum"].append(item["main"]["humidity"])

        forecast = []
        for d, s in daily.items():
            forecast.append(PronosticoDia(
                date=d,
                temp_max=s["tmax"],
                temp_min=s["tmin"],
                precipitation=s["precip"],
                humidity=round(sum(s["hum"]) / len(s["hum"]), 1)
            ))

        return DatosClima(actual=actual, forecast=forecast)
