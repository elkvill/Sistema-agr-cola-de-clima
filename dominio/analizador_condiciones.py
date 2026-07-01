from abc import ABC, abstractmethod
from typing import List, Optional

from dominio.puertos import AnalizadorCondicionesPort


class EvaluadorCondicion(ABC):

    @abstractmethod
    def evaluar(self, temperatura: float, humedad: float,
                precipitacion: float) -> Optional[str]:
        raise NotImplementedError


class EvaluadorCalorExtremo(EvaluadorCondicion):

    def __init__(self, umbral: float):
        self.umbral = umbral

    def evaluar(self, temperatura: float, humedad: float,
                precipitacion: float) -> Optional[str]:
        if temperatura >= self.umbral:
            return "CALOR_EXTREMO"
        return None


class EvaluadorFrioBajo(EvaluadorCondicion):

    def __init__(self, umbral: float):
        self.umbral = umbral

    def evaluar(self, temperatura: float, humedad: float,
                precipitacion: float) -> Optional[str]:
        if temperatura <= self.umbral:
            return "FRIO_BAJO"
        return None


class EvaluadorLluviaIntensa(EvaluadorCondicion):

    def __init__(self, umbral: float):
        self.umbral = umbral

    def evaluar(self, temperatura: float, humedad: float,
                precipitacion: float) -> Optional[str]:
        if precipitacion >= self.umbral:
            return "LLUVIA_INTENSA"
        return None


class EvaluadorHumedadBaja(EvaluadorCondicion):

    def __init__(self, umbral: float):
        self.umbral = umbral

    def evaluar(self, temperatura: float, humedad: float,
                precipitacion: float) -> Optional[str]:
        if humedad <= self.umbral:
            return "HUMEDAD_BAJA"
        return None


class EvaluadorHumedadAlta(EvaluadorCondicion):

    def __init__(self, umbral: float):
        self.umbral = umbral

    def evaluar(self, temperatura: float, humedad: float,
                precipitacion: float) -> Optional[str]:
        if humedad >= self.umbral:
            return "HUMEDAD_ALTA"
        return None


class AnalizadorCondiciones(AnalizadorCondicionesPort):

    def __init__(self, evaluadores: List[EvaluadorCondicion]):
        self._evaluadores = evaluadores

    def analizar(self, temperatura: float, humedad: float,
                 precipitacion: float) -> List[str]:
        condiciones = []
        for ev in self._evaluadores:
            condicion = ev.evaluar(temperatura, humedad, precipitacion)
            if condicion:
                condiciones.append(condicion)
        return condiciones
