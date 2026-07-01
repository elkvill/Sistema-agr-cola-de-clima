
from abc import ABC, abstractmethod
from typing import List, Optional

from dominio.entidades import DatosClima, AnalisisLocal, ConsultaHistorial, ResultadoConsulta


class ServicioClima(ABC):

    @abstractmethod
    def obtener_actual(self, lat: float, lon: float) -> DatosClima:
        raise NotImplementedError


class ServicioRecomendacionIA(ABC):

    @abstractmethod
    def generar_recomendacion(self, temperatura: float, humedad: float,
                              precipitacion: float) -> str:
        raise NotImplementedError


class ServicioChatIA(ABC):

    @abstractmethod
    def chat(self, pregunta: str, temperatura: float, humedad: float,
             precipitacion: float) -> str:
        raise NotImplementedError


class ServicioIA(ServicioRecomendacionIA, ServicioChatIA):
    pass


class AnalizadorCondicionesPort(ABC):

    @abstractmethod
    def analizar(self, temperatura: float, humedad: float,
                 precipitacion: float) -> List[str]:
        raise NotImplementedError


class GeneradorRecomendacionPort(ABC):

    @abstractmethod
    def generar(self, es_agricola: bool,
                condiciones: List[str]) -> AnalisisLocal:
        raise NotImplementedError


class ClasificadorPronosticoPort(ABC):

    @abstractmethod
    def clasificar(self, pronostico: List[dict]) -> List[dict]:
        raise NotImplementedError


class VerificadorConectividad(ABC):

    @abstractmethod
    def hay_conexion(self) -> bool:
        raise NotImplementedError



class RepositorioClima(ABC):

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
    def guardar_consulta(self, ciudad: str, temperatura: float,
                         estado: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def obtener_historial(self, limite: int = 5) -> List[ConsultaHistorial]:
        raise NotImplementedError


class ConsultarClima(ABC):

    @abstractmethod
    def ejecutar(self, ciudad_nombre: str, lat: float, lon: float,
                 es_agricola: bool) -> ResultadoConsulta:
        raise NotImplementedError
