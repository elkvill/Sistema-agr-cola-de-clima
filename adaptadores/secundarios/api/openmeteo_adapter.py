import json
import urllib.request
from typing import Optional

from dominio.entidades import DatosClima, MedicionActual, PronosticoDia
from dominio.puertos import ServicioClima


class OpenMeteoAdapter(ServicioClima):
    def obtener_actual(self, lat: float, lon: float) -> Optional[DatosClima]:
        url = (
            "https://api.open-meteo.com/v1/forecast?"
            f"latitude={lat}&longitude={lon}"
            "&current=temperature_2m,relative_humidity_2m,precipitation"
            "&daily=temperature_2m_max,temperature_2m_min,precipitation_sum"
            "&timezone=auto"
        )
        with urllib.request.urlopen(url, timeout=10) as r:
            data = json.loads(r.read().decode())

        actual = MedicionActual(
            temp=data["current"]["temperature_2m"],
            humidity=data["current"]["relative_humidity_2m"],
            precipitation=data["current"].get("precipitation", 0)
        )

        forecast = []
        for i in range(len(data["daily"]["time"])):
            forecast.append(PronosticoDia(
                date=data["daily"]["time"][i],
                temp_max=data["daily"]["temperature_2m_max"][i],
                temp_min=data["daily"]["temperature_2m_min"][i],
                precipitation=data["daily"]["precipitation_sum"][i],
                humidity=0
            ))

        return DatosClima(actual=actual, forecast=forecast)
