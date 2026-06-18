from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime


@dataclass
class Ciudad:
    nombre: str
    latitud: float
    longitud: float
    es_agricola: bool


@dataclass
class MedicionActual:
    temperatura: float
    humedad: float
    precipitacion: float


@dataclass
class PronosticoDia:
    fecha: str
    temperatura_max: float
    temperatura_min: float
    precipitacion: float
    humedad: float


@dataclass
class DatosClima:
    actual: MedicionActual
    pronostico: List[PronosticoDia]


@dataclass
class AnalisisLocal:
    estado: str
    mensaje: str
    condiciones: List[str]


@dataclass
class ResultadoConsulta:
    ciudad: str
    datos: DatosClima
    analisis: AnalisisLocal
    recomendacion_ia: str
    clasificacion_dias: List[dict]
    modo_offline: bool
    estadisticas: Optional[dict] = None


@dataclass
class ConsultaHistorial:
    fecha: str
    ciudad: str
    temperatura: float
    estado: str
