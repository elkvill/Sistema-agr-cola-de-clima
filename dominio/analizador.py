
from typing import List

from dominio.entidades import AnalisisLocal
from dominio.estrategias_recomendacion import (
    EstrategiaRecomendacion,
    RecomendacionUrbana,
    RecomendacionFavorable,
    RecomendacionRiesgoLluvia,
    RecomendacionRiesgoCalor,
    RecomendacionNormal,
)


# Umbrales climáticos centralizados para este módulo
_UMBRALES = {
    "temp_max": 35.0,
    "temp_min": 15.0,
    "rain_heavy": 15.0,
    "humidity_low": 40.0,
    "humidity_high": 90.0,
}


class AnalizadorCondiciones:

    def analizar(self, temperatura: float, humedad: float,
                 precipitacion: float) -> List[str]:
        condiciones = []
        if temperatura >= _UMBRALES['temp_max']:
            condiciones.append("CALOR_EXTREMO")
        elif temperatura <= _UMBRALES['temp_min']:
            condiciones.append("FRIO_BAJO")
        if precipitacion >= _UMBRALES['rain_heavy']:
            condiciones.append("LLUVIA_INTENSA")
        if humedad <= _UMBRALES['humidity_low']:
            condiciones.append("HUMEDAD_BAJA")
        elif humedad >= _UMBRALES['humidity_high']:
            condiciones.append("HUMEDAD_ALTA")
        return condiciones


class GeneradorRecomendacion:

    def generar(self, es_agricola: bool,
                condiciones: List[str]) -> AnalisisLocal:
        estrategia: EstrategiaRecomendacion = self._seleccionar(
            es_agricola, condiciones
        )
        return estrategia.aplicar(condiciones)

    def _seleccionar(self, es_agricola: bool,
                     condiciones: List[str]) -> EstrategiaRecomendacion:
        if not es_agricola:
            return RecomendacionUrbana()
        if not condiciones:
            return RecomendacionFavorable()
        if "LLUVIA_INTENSA" in condiciones:
            return RecomendacionRiesgoLluvia()
        if "CALOR_EXTREMO" in condiciones or "HUMEDAD_BAJA" in condiciones:
            return RecomendacionRiesgoCalor()
        return RecomendacionNormal()


class ClasificadorPronostico:

    def clasificar(self, pronostico: List[dict]) -> List[dict]:
        clasificacion = []
        for dia in pronostico:
            score = 0
            if dia['temperatura_max'] >= _UMBRALES['temp_max']:
                score += 2
            if dia['precipitacion'] >= _UMBRALES['rain_heavy']:
                score += 2
            if dia['humedad'] <= _UMBRALES['humidity_low']:
                score += 1

            if score == 0:
                etiqueta = "Favorable"
            elif score <= 2:
                etiqueta = "Normal"
            else:
                etiqueta = "Riesgoso"

            clasificacion.append({"fecha": dia['fecha'], "etiqueta": etiqueta})
        return clasificacion
