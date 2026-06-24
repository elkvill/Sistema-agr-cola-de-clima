"""
Principio SRP (Single Responsibility Principle) - Responsabilidad Única.

Este módulo contiene tres clases de dominio, cada una con una única razón
para cambiar:

- AnalizadorCondiciones: cambia solo si cambian los umbrales o las reglas
  de detección de alertas climáticas.

- GeneradorRecomendacion: cambia solo si cambia la lógica de selección de
  qué estrategia aplicar (qué condición tiene prioridad).

- ClasificadorPronostico: cambia solo si cambia cómo se clasifica
  la peligrosidad de cada día del pronóstico.
"""
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
    """
    SRP: Única responsabilidad → detectar qué alertas climáticas están activas.

    Si los umbrales cambian o se añaden nuevas alertas (ej: VIENTO_FUERTE),
    solo esta clase se modifica.
    """

    def analizar(self, temperatura: float, humedad: float,
                 precipitacion: float) -> List[str]:
        """
        Evalúa los valores climáticos y retorna una lista de códigos de alerta.

        Returns:
            Lista de strings con las condiciones activas
            (ej: ['CALOR_EXTREMO', 'HUMEDAD_BAJA']).
        """
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
    """
    SRP: Única responsabilidad → seleccionar y aplicar la estrategia correcta.

    Aplica OCP mediante composición: delega la generación del AnalisisLocal
    a la EstrategiaRecomendacion correspondiente. Para añadir un nuevo tipo
    de zona o prioridad, solo se añade una nueva condición en _seleccionar()
    o una nueva EstrategiaRecomendacion, sin tocar las existentes.

    Principio LSP: cualquier implementación de EstrategiaRecomendacion
    puede sustituirse aquí sin romper el comportamiento del generador.
    """

    def generar(self, es_agricola: bool,
                condiciones: List[str]) -> AnalisisLocal:
        """
        Selecciona la estrategia adecuada y genera la recomendación.

        Args:
            es_agricola: Indica si la ciudad es zona agrícola.
            condiciones: Lista de códigos de alerta activos.

        Returns:
            AnalisisLocal con el resultado de la recomendación.
        """
        estrategia: EstrategiaRecomendacion = self._seleccionar(
            es_agricola, condiciones
        )
        return estrategia.aplicar(condiciones)

    def _seleccionar(self, es_agricola: bool,
                     condiciones: List[str]) -> EstrategiaRecomendacion:
        """Determina qué estrategia usar según el contexto."""
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
    """
    SRP: Única responsabilidad → clasificar la peligrosidad de cada día
    del pronóstico de 5 días.

    Si el criterio de puntuación cambia (ej: añadir viento como factor),
    solo esta clase se modifica, sin afectar AnalizadorCondiciones ni
    GeneradorRecomendacion.
    """

    def clasificar(self, pronostico: List[dict]) -> List[dict]:
        """
        Asigna una etiqueta (Favorable/Normal/Riesgoso) a cada día.

        Args:
            pronostico: Lista de diccionarios con datos diarios del clima.

        Returns:
            Lista de diccionarios con 'fecha' y 'etiqueta'.
        """
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
