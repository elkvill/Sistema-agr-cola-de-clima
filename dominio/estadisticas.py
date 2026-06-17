import statistics
from typing import List, Dict, Any


def calcular_estadisticas(pronostico: List[Dict[str, Any]]) -> Dict[str, Any]:
    temps_max = [d['temperatura_max'] for d in pronostico]
    temps_min = [d['temperatura_min'] for d in pronostico]
    humedades = [d.get('humedad', 0) for d in pronostico]
    lluvias = [d.get('precipitacion', 0) for d in pronostico]

    return {
        "media": round(statistics.mean(temps_max), 1),
        "mediana": round(statistics.median(temps_max), 1),
        "desviacion": round(statistics.stdev(temps_max), 2) if len(temps_max) > 1 else 0.0,
        "varianza": round(statistics.variance(temps_max), 2) if len(temps_max) > 1 else 0.0,
        "max": max(temps_max),
        "min": min(temps_min),
        "rango": round(max(temps_max) - min(temps_min), 1),
        "media_humedad": round(statistics.mean(humedades), 1),
        "lluvia_total": round(sum(lluvias), 1),
        "tendencia": _calcular_tendencia(temps_max),
    }


def _calcular_tendencia(temps: List[float]) -> str:
    if len(temps) < 2:
        return "Estable"
    pendiente = (temps[-1] - temps[0]) / len(temps)
    if pendiente > 0.3:
        return "En aumento"
    if pendiente < -0.3:
        return "En descenso"
    return "Estable"
