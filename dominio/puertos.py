from abc import ABC, abstractmethod
from typing import List, Optional

from dominio.entidades import DatosClima, AnalisisLocal, ConsultaHistorial


class ServicioClima(ABC):
    """Puerto secundario: obtener datos climaticos de una API externa."""

    @abstractmethod
    def obtener_actual(self, lat: float, lon: float) -> DatosClima:
        raise NotImplementedError


class ServicioIA(ABC):
    """Puerto secundario: generar recomendaciones con IA."""

    @abstractmethod
    def generar_recomendacion(self, temp: float, humidity: float,
                              precipitation: float) -> str:
        raise NotImplementedError

    @abstractmethod
    def chat(self, pregunta: str, temp: float, humidity: float,
             precipitation: float) -> str:
        raise NotImplementedError


class RepositorioClima(ABC):
    """Puerto secundario: persistir y recuperar datos climaticos."""

    @abstractmethod
    def guardar_clima(self, ciudad: str, datos: DatosClima) -> None:
        raise NotImplementedError

    @abstractmethod
    def cargar_clima(self, ciudad: str) -> Optional[DatosClima]:
        raise NotImplementedError

    @abstractmethod
    def guardar_analisis(self, ciudad: str, analisis: AnalisisLocal,
                         rec_ia: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def cargar_analisis(self, ciudad: str) -> Optional[dict]:
        raise NotImplementedError

    @abstractmethod
    def historial(self, limite: int = 5) -> List[ConsultaHistorial]:
        raise NotImplementedError


class ConsultarClima(ABC):
    """Puerto primario: caso de uso principal."""

    @abstractmethod
    def ejecutar(self, ciudad_nombre: str, lat: float, lon: float,
                 es_agricola: bool) -> object:
        raise NotImplementedError
