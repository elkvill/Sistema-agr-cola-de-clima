from dataclasses import dataclass
from typing import List, Optional

from dominio.entidades import (
    Ciudad, MedicionActual, PronosticoDia, DatosClima,
    AnalisisLocal, ConsultaHistorial
)


# --- Row Models (privados del adaptador) ---

@dataclass
class FilaCiudad:
    nombre: str
    latitud: float
    longitud: float
    es_agricola: int


@dataclass
class FilaClimaActual:
    id: int
    ciudad: str
    temperatura: float
    humedad: float
    precipitacion: float
    fecha_guardado: str


@dataclass
class FilaPronostico:
    id: int
    ciudad: str
    fecha: str
    temperatura_maxima: float
    temperatura_minima: float
    precipitacion: float
    humedad: float
    fecha_guardado: str


@dataclass
class FilaAnalisis:
    id: int
    clima_actual_id: int
    estado: str
    condiciones: str
    mensaje: str
    recomendacion: str
    fecha_analisis: str


@dataclass
class FilaHistorial:
    id: int
    fecha_consulta: str
    ciudad: str
    temperatura: float
    estado: str


# --- Mappers ---

class MapeadorCiudad:
    @staticmethod
    def a_dominio(fila: FilaCiudad) -> Ciudad:
        return Ciudad(
            nombre=fila.nombre,
            latitud=fila.latitud,
            longitud=fila.longitud,
            es_agricola=bool(fila.es_agricola)
        )

    @staticmethod
    def a_fila(entidad: Ciudad) -> FilaCiudad:
        return FilaCiudad(
            nombre=entidad.nombre,
            latitud=entidad.latitud,
            longitud=entidad.longitud,
            es_agricola=1 if entidad.es_agricola else 0
        )


class MapeadorClima:
    @staticmethod
    def fila_a_medicion(fila: tuple) -> MedicionActual:
        return MedicionActual(
            temperatura=fila[0],
            humedad=fila[1],
            precipitacion=fila[2]
        )

    @staticmethod
    def fila_a_pronostico(fila: tuple) -> PronosticoDia:
        return PronosticoDia(
            fecha=fila[0],
            temperatura_max=fila[1],
            temperatura_min=fila[2],
            precipitacion=fila[3],
            humedad=fila[4]
        )

    @staticmethod
    def pronostico_a_fila(ciudad: str, p: PronosticoDia) -> tuple:
        return (ciudad, p.fecha, p.temperatura_max,
                p.temperatura_min, p.precipitacion, p.humedad)


class MapeadorAnalisis:
    @staticmethod
    def fila_a_analisis(fila: tuple) -> dict:
        return {
            'estado': fila[0],
            'mensaje': fila[1],
            'condiciones': fila[2],
            'recomendacion_ia': fila[3] if fila[3] else ""
        }


class MapeadorHistorial:
    @staticmethod
    def fila_a_historial(fila: tuple) -> ConsultaHistorial:
        return ConsultaHistorial(
            fecha=fila[0],
            ciudad=fila[1],
            temperatura=fila[2],
            estado=fila[3]
        )
