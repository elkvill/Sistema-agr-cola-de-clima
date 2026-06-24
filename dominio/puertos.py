"""
Puertos del dominio (interfaces abstractas).

Principio ISP (Interface Segregation Principle):
Cada puerto es una interfaz pequeña y específica. Ninguna clase
concreta se ve obligada a implementar métodos que no necesita.
Los adaptadores implementan solo el puerto que les corresponde.

Principio DIP (Dependency Inversion Principle):
Los módulos de alto nivel (casos de uso en dominio/) dependen
únicamente de estas abstracciones. Los adaptadores concretos
(openweather, groq, sqlite) dependen también de estas interfaces,
no al revés.

Principio LSP (Liskov Substitution Principle):
Contrato para todas las implementaciones concretas:
- Deben devolver exactamente el tipo declarado en la firma.
- No pueden lanzar excepciones distintas a las documentadas.
- No pueden imponer precondiciones más estrictas que las del puerto.
- Cualquier implementación concreta debe ser intercambiable sin
  que el código cliente necesite saber el tipo real.
"""
from abc import ABC, abstractmethod
from typing import List, Optional

from dominio.entidades import DatosClima, AnalisisLocal, ConsultaHistorial, ResultadoConsulta


class ServicioClima(ABC):
    """
    Puerto ISP: solo expone la obtención del clima actual.

    LSP: toda implementación concreta debe retornar un DatosClima válido
    o lanzar una excepción estándar (IOError / ConnectionError).
    No puede retornar None ni lanzar excepciones no documentadas.
    """

    @abstractmethod
    def obtener_actual(self, lat: float, lon: float) -> DatosClima:
        """
        Obtiene el clima actual para las coordenadas dadas.

        Args:
            lat: Latitud de la ciudad.
            lon: Longitud de la ciudad.

        Returns:
            DatosClima con la información actual y el pronóstico.

        Raises:
            Exception: Si el servicio externo no está disponible.
        """
        raise NotImplementedError


class ServicioIA(ABC):
    """
    Puerto ISP: solo expone las operaciones de inteligencia artificial.

    LSP: las implementaciones concretas siempre devuelven str.
    Nunca retornan None. En caso de error, retornan una cadena vacía.
    """

    @abstractmethod
    def generar_recomendacion(self, temperatura: float, humedad: float,
                              precipitacion: float) -> str:
        """
        Genera una recomendación agrícola usando IA.

        Returns:
            Texto con la recomendación. Nunca None.
        """
        raise NotImplementedError

    @abstractmethod
    def chat(self, pregunta: str, temperatura: float, humedad: float,
             precipitacion: float) -> str:
        """
        Responde una pregunta del usuario en contexto climático.

        Returns:
            Texto de respuesta. Nunca None.
        """
        raise NotImplementedError


class RepositorioClima(ABC):
    """
    Puerto ISP: agrupa las operaciones de persistencia climática.

    Este puerto podría segregarse en RepositorioLectura / RepositorioEscritura
    si surgiera una implementación de solo lectura (API externa de consulta).
    Por ahora, todas las implementaciones soportan ambas operaciones.

    LSP: las implementaciones concretas no pueden lanzar excepciones no
    relacionadas con la persistencia ni retornar tipos distintos a los
    declarados en cada firma.
    """

    @abstractmethod
    def guardar_clima(self, ciudad: str, datos: DatosClima) -> None:
        raise NotImplementedError

    @abstractmethod
    def cargar_clima(self, ciudad: str) -> Optional[DatosClima]:
        """Retorna None si no hay datos para la ciudad. Nunca lanza error."""
        raise NotImplementedError

    @abstractmethod
    def guardar_analisis(self, ciudad: str, analisis: AnalisisLocal,
                          rec_ia: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def cargar_analisis(self, ciudad: str) -> Optional[dict]:
        """Retorna None si no hay análisis previo. Nunca lanza error."""
        raise NotImplementedError

    @abstractmethod
    def guardar_consulta(self, ciudad: str, temperatura: float,
                          estado: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def obtener_historial(self, limite: int = 5) -> List[ConsultaHistorial]:
        """Retorna lista vacía si no hay historial. Nunca lanza error."""
        raise NotImplementedError


class ConsultarClima(ABC):
    """
    Puerto principal del caso de uso.

    ISP: interfaz de un solo método; el cliente solo necesita saber
    que puede ejecutar una consulta y obtener un ResultadoConsulta.

    LSP: ObtenerClimaYAnalizar implementa este puerto y puede sustituirlo
    en cualquier punto. El cliente (StreamlitUI) solo conoce este puerto,
    no la clase concreta.

    DIP: StreamlitUI (módulo de alto nivel) depende de este puerto,
    no de ObtenerClimaYAnalizar directamente.
    """

    @abstractmethod
    def ejecutar(self, ciudad_nombre: str, lat: float, lon: float,
                 es_agricola: bool) -> ResultadoConsulta:
        """
        Ejecuta la consulta de clima completa para una ciudad.

        Args:
            ciudad_nombre: Nombre legible de la ciudad.
            lat: Latitud (0 para modo offline).
            lon: Longitud (0 para modo offline).
            es_agricola: True si la zona tiene actividad agrícola.

        Returns:
            ResultadoConsulta con todos los datos del análisis.

        Raises:
            ApiCaidaError: Si la API no responde y no hay caché.
            DatosNoEncontradosError: Si no hay datos en modo offline.
        """
        raise NotImplementedError
