"""
Principio OCP (Open/Closed Principle) - Abierto para extensión, cerrado para modificación.

Para añadir un nuevo tipo de recomendación (nueva zona, nueva condición climática),
solo se crea una nueva clase que implemente EstrategiaRecomendacion.
NO se modifica ninguna clase existente.

Principio LSP (Liskov Substitution Principle):
Cualquier EstrategiaRecomendacion concreta puede sustituir a la interfaz abstracta
sin alterar el comportamiento esperado. Todas devuelven un AnalisisLocal válido.
"""
from abc import ABC, abstractmethod
from typing import List

from dominio.entidades import AnalisisLocal


class EstrategiaRecomendacion(ABC):
    """
    Puerto de estrategia para generar recomendaciones agrícolas.

    Contrato LSP: toda subclase debe devolver un AnalisisLocal completo
    y nunca lanzar excepciones inesperadas. El cliente que reciba cualquier
    implementación de esta interfaz puede usarla sin conocer el tipo concreto.
    """

    @abstractmethod
    def aplicar(self, condiciones: List[str]) -> AnalisisLocal:
        """
        Genera una recomendación basada en las condiciones detectadas.

        Args:
            condiciones: Lista de códigos de alerta climática.

        Returns:
            AnalisisLocal con estado, mensaje y condiciones activas.
        """
        raise NotImplementedError


# ── Implementaciones concretas ────────────────────────────────────────────────
# Para añadir un nuevo caso (ej: SEQUIA_EXTREMA), crear una nueva clase aquí
# sin tocar ninguna de las existentes ni la clase GeneradorRecomendacion.

class RecomendacionUrbana(EstrategiaRecomendacion):
    """Zona urbana: sin recomendaciones agrícolas."""

    def aplicar(self, condiciones: List[str]) -> AnalisisLocal:
        return AnalisisLocal(
            estado="URBAN",
            mensaje="Zona urbana. Sin recomendaciones agricolas.",
            condiciones=[]
        )


class RecomendacionFavorable(EstrategiaRecomendacion):
    """Sin alertas activas: condiciones ideales para cultivo."""

    def aplicar(self, condiciones: List[str]) -> AnalisisLocal:
        return AnalisisLocal(
            estado="FAVORABLE",
            mensaje="Condiciones ideales para siembra y cultivo.",
            condiciones=[]
        )


class RecomendacionRiesgoLluvia(EstrategiaRecomendacion):
    """Lluvia intensa: riesgo de inundación."""

    def aplicar(self, condiciones: List[str]) -> AnalisisLocal:
        return AnalisisLocal(
            estado="RIESGOSO",
            mensaje="Riesgo de inundacion. No aplicar fertilizantes.",
            condiciones=condiciones
        )


class RecomendacionRiesgoCalor(EstrategiaRecomendacion):
    """Calor extremo o humedad baja: estrés hídrico."""

    def aplicar(self, condiciones: List[str]) -> AnalisisLocal:
        return AnalisisLocal(
            estado="RIESGOSO",
            mensaje="Estres hidrico. Se recomienda riego temprano.",
            condiciones=condiciones
        )


class RecomendacionNormal(EstrategiaRecomendacion):
    """Condiciones aceptables con algunas alertas menores."""

    def aplicar(self, condiciones: List[str]) -> AnalisisLocal:
        return AnalisisLocal(
            estado="NORMAL",
            mensaje="Condiciones aceptables. Monitorear el suelo.",
            condiciones=condiciones
        )
