from typing import List

from dominio.entidades import AnalisisLocal
from dominio.puertos import GeneradorRecomendacionPort
from dominio.estrategias_recomendacion import (
    EstrategiaRecomendacion,
    RecomendacionUrbana,
    RecomendacionFavorable,
    RecomendacionRiesgoLluvia,
    RecomendacionRiesgoCalor,
    RecomendacionNormal,
)


class GeneradorRecomendacion(GeneradorRecomendacionPort):

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
