
from typing import List

from dominio.entidades import (
    DatosClima, AnalisisLocal, ResultadoConsulta
)
from dominio.puertos import (
    ServicioClima, ServicioIA, RepositorioClima, ConsultarClima
)
from dominio.estadisticas import calcular_estadisticas
from dominio.excepciones import ApiCaidaError, DatosNoEncontradosError
from dominio.analizador import (
    AnalizadorCondiciones, GeneradorRecomendacion, ClasificadorPronostico
)


class ObtenerClimaYAnalizar(ConsultarClima):

    def __init__(self, servicio_clima: ServicioClima,
                 servicio_ia: ServicioIA,
                 repositorio: RepositorioClima):
        # dependencias inyectadas como abstracciones, no como concretos
        self._servicio_clima = servicio_clima
        self._servicio_ia = servicio_ia
        self._repositorio = repositorio

        self._analizador = AnalizadorCondiciones()
        self._generador = GeneradorRecomendacion()
        self._clasificador = ClasificadorPronostico()

    def ejecutar(self, ciudad_nombre: str, lat: float, lon: float,
                 es_agricola: bool) -> ResultadoConsulta:

        datos, modo_offline = self._obtener_datos(ciudad_nombre, lat, lon)

        condiciones = self._analizador.analizar(
            datos.actual.temperatura,
            datos.actual.humedad,
            datos.actual.precipitacion
        )
        analisis = self._generador.generar(es_agricola, condiciones)
        rec_ia = self._obtener_recomendacion_ia(
            ciudad_nombre, datos, modo_offline, analisis
        )

        pronostico_dicts = self._normalizar_pronostico(datos)
        clasificacion = self._clasificador.clasificar(pronostico_dicts)
        estadisticas = calcular_estadisticas(
            pronostico_dicts) if pronostico_dicts else {}

        return ResultadoConsulta(
            ciudad=ciudad_nombre,
            datos=datos,
            analisis=analisis,
            recomendacion_ia=rec_ia,
            clasificacion_dias=clasificacion,
            modo_offline=modo_offline,
            estadisticas=estadisticas
        )

    def _obtener_datos(self, ciudad_nombre: str,
                       lat: float, lon: float) -> tuple:
        """Obtiene datos del clima (en línea o desde caché local)."""
        if lat == 0 and lon == 0:
            datos = self._repositorio.cargar_clima(ciudad_nombre)
            if not datos:
                raise DatosNoEncontradosError(
                    f"No hay datos locales para {ciudad_nombre}"
                )
            return datos, True

        try:
            datos = self._servicio_clima.obtener_actual(lat, lon)
            self._repositorio.guardar_clima(ciudad_nombre, datos)
            return datos, False
        except Exception as e:
            datos_cargados = self._repositorio.cargar_clima(ciudad_nombre)
            if datos_cargados:
                return datos_cargados, True
            raise ApiCaidaError(
                f"No hay conexión y no hay datos de respaldo para "
                f"{ciudad_nombre}. Detalle: {e}"
            )

    def _obtener_recomendacion_ia(self, ciudad_nombre: str,
                                  datos: DatosClima, modo_offline: bool,
                                  analisis: AnalisisLocal) -> str:
        if not modo_offline:
            try:
                rec_ia = self._servicio_ia.generar_recomendacion(
                    datos.actual.temperatura,
                    datos.actual.humedad,
                    datos.actual.precipitacion
                )
                self._repositorio.guardar_analisis(
                    ciudad_nombre, analisis, rec_ia)
                self._repositorio.guardar_consulta(
                    ciudad_nombre, datos.actual.temperatura, analisis.estado
                )
                return rec_ia
            except Exception:
                pass

        analisis_guardado = self._repositorio.cargar_analisis(ciudad_nombre)
        rec_ia = analisis_guardado.get(
            'recomendacion_ia', '') if analisis_guardado else ''
        self._repositorio.guardar_analisis(ciudad_nombre, analisis, rec_ia)
        self._repositorio.guardar_consulta(
            ciudad_nombre, datos.actual.temperatura, analisis.estado
        )
        return rec_ia

    def _normalizar_pronostico(self, datos: DatosClima) -> list:

        return [
            {
                "fecha": d.fecha,
                "temperatura_max": d.temperatura_max,
                "temperatura_min": d.temperatura_min,
                "precipitacion": d.precipitacion,
                "humedad": d.humedad,
            }
            for d in datos.pronostico
        ]
