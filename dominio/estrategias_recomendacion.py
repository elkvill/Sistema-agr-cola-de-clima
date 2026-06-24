
from abc import ABC, abstractmethod
from typing import List

from dominio.entidades import AnalisisLocal


class EstrategiaRecomendacion(ABC):

    @abstractmethod
    def aplicar(self, condiciones: List[str]) -> AnalisisLocal:
        # Genera una recomendación basada en las condiciones detectadas.
        raise NotImplementedError


class RecomendacionUrbana(EstrategiaRecomendacion):

    def aplicar(self, condiciones: List[str]) -> AnalisisLocal:
        return AnalisisLocal(
            estado="URBAN",
            mensaje="Zona urbana. Sin recomendaciones agricolas.",
            condiciones=[]
        )


class RecomendacionFavorable(EstrategiaRecomendacion):

    def aplicar(self, condiciones: List[str]) -> AnalisisLocal:
        return AnalisisLocal(
            estado="FAVORABLE",
            mensaje="Condiciones ideales para siembra y cultivo.",
            condiciones=[]
        )


class RecomendacionRiesgoLluvia(EstrategiaRecomendacion):

    def aplicar(self, condiciones: List[str]) -> AnalisisLocal:
        return AnalisisLocal(
            estado="RIESGOSO",
            mensaje="Riesgo de inundacion. No aplicar fertilizantes.",
            condiciones=condiciones
        )


class RecomendacionRiesgoCalor(EstrategiaRecomendacion):

    def aplicar(self, condiciones: List[str]) -> AnalisisLocal:
        return AnalisisLocal(
            estado="RIESGOSO",
            mensaje="Estres hidrico. Se recomienda riego temprano.",
            condiciones=condiciones
        )


class RecomendacionNormal(EstrategiaRecomendacion):

    def aplicar(self, condiciones: List[str]) -> AnalisisLocal:
        return AnalisisLocal(
            estado="NORMAL",
            mensaje="Condiciones aceptables. Monitorear el suelo.",
            condiciones=condiciones
        )
