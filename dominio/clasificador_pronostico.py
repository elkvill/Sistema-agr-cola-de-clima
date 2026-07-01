from abc import ABC, abstractmethod
from typing import List

from dominio.puertos import ClasificadorPronosticoPort


class EstrategiaClasificacion(ABC):

    @abstractmethod
    def clasificar_dia(self, dia: dict) -> str:
        raise NotImplementedError


class ClasificacionPuntuacionStrategy(EstrategiaClasificacion):

    def __init__(self, umbrales: dict):
        self.umbrales = umbrales

    def clasificar_dia(self, dia: dict) -> str:
        score = 0
        if dia['temperatura_max'] >= self.umbrales['temp_max']:
            score += 2
        if dia['precipitacion'] >= self.umbrales['rain_heavy']:
            score += 2
        if dia['humedad'] <= self.umbrales['humidity_low']:
            score += 1

        if score == 0:
            return "Favorable"
        elif score <= 2:
            return "Normal"
        else:
            return "Riesgoso"


class ClasificadorPronostico(ClasificadorPronosticoPort):

    def __init__(self, estrategia: EstrategiaClasificacion):
        self._estrategia = estrategia

    def clasificar(self, pronostico: List[dict]) -> List[dict]:
        clasificacion = []
        for dia in pronostico:
            etiqueta = self._estrategia.clasificar_dia(dia)
            clasificacion.append({"fecha": dia['fecha'], "etiqueta": etiqueta})
        return clasificacion
