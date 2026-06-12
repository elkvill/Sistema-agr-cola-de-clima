from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime


@dataclass
class MedicionActual:
    temp: float
    humidity: float
    precipitation: float


@dataclass
class PronosticoDia:
    date: str
    temp_max: float
    temp_min: float
    precipitation: float
    humidity: float


@dataclass
class DatosClima:
    actual: MedicionActual
    forecast: List[PronosticoDia]


@dataclass
class AnalisisLocal:
    status: str
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
    stats: Optional[dict] = None


@dataclass
class ConsultaHistorial:
    fecha: str
    ciudad: str
    temp: float
    status: str
