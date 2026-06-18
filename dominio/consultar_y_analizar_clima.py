from typing import List, Optional

from dominio.entidades import (
    DatosClima, MedicionActual, AnalisisLocal, ResultadoConsulta
)
from dominio.puertos import (
    ServicioClima, ServicioIA, PuertoClima, PuertoAnalisis,
    PuertoHistorial, ConsultarClima
)
from dominio.estadisticas import calcular_estadisticas
from dominio.excepciones import ApiCaidaError, DatosNoEncontradosError


UMBRALES = {
    "temp_max": 35.0, "temp_min": 15.0, "rain_heavy": 15.0,
    "humidity_low": 40.0, "humidity_high": 90.0,
}


def _analizar_condiciones(temperatura: float, humedad: float,
                          precipitacion: float) -> List[str]:
    condiciones = []
    if temperatura >= UMBRALES['temp_max']:
        condiciones.append("CALOR_EXTREMO")
    elif temperatura <= UMBRALES['temp_min']:
        condiciones.append("FRIO_BAJO")
    if precipitacion >= UMBRALES['rain_heavy']:
        condiciones.append("LLUVIA_INTENSA")
    if humedad <= UMBRALES['humidity_low']:
        condiciones.append("HUMEDAD_BAJA")
    elif humedad >= UMBRALES['humidity_high']:
        condiciones.append("HUMEDAD_ALTA")
    return condiciones


def _generar_recomendacion_local(es_agricola: bool,
                                  condiciones: List[str]) -> AnalisisLocal:
    if not es_agricola:
        return AnalisisLocal(
            estado="URBAN",
            mensaje="Zona urbana. Sin recomendaciones agricolas.",
            condiciones=[]
        )
    if not condiciones:
        return AnalisisLocal(
            estado="FAVORABLE",
            mensaje="Condiciones ideales para siembra y cultivo.",
            condiciones=[]
        )
    if "LLUVIA_INTENSA" in condiciones:
        return AnalisisLocal(
            estado="RIESGOSO",
            mensaje="Riesgo de inundacion. No aplicar fertilizantes.",
            condiciones=condiciones
        )
    if "CALOR_EXTREMO" in condiciones or "HUMEDAD_BAJA" in condiciones:
        return AnalisisLocal(
            estado="RIESGOSO",
            mensaje="Estres hidrico. Se recomienda riego temprano.",
            condiciones=condiciones
        )
    return AnalisisLocal(
        estado="NORMAL",
        mensaje="Condiciones aceptables. Monitorear el suelo.",
        condiciones=condiciones
    )


def _clasificar_dias(pronostico: List[dict]) -> List[dict]:
    clasificacion = []
    for dia in pronostico:
        score = 0
        if dia['temperatura_max'] >= UMBRALES['temp_max']:
            score += 2
        if dia['precipitacion'] >= UMBRALES['rain_heavy']:
            score += 2
        if dia['humedad'] <= UMBRALES['humidity_low']:
            score += 1
        if score == 0:
            etiqueta = "Favorable"
        elif score <= 2:
            etiqueta = "Normal"
        else:
            etiqueta = "Riesgoso"
        clasificacion.append({"fecha": dia['fecha'], "etiqueta": etiqueta})
    return clasificacion


def _calcular_stats(pronostico: List[dict]) -> dict:
    if not pronostico:
        return {}
    return calcular_estadisticas(pronostico)


class ObtenerClimaYAnalizar(ConsultarClima):
    def __init__(self, servicio_clima: ServicioClima,
                 servicio_ia: ServicioIA,
                 repositorio_clima: PuertoClima,
                 repositorio_analisis: PuertoAnalisis,
                 repositorio_historial: PuertoHistorial):
        self._servicio_clima = servicio_clima
        self._servicio_ia = servicio_ia
        self._repositorio_clima = repositorio_clima
        self._repositorio_analisis = repositorio_analisis
        self._repositorio_historial = repositorio_historial

    def ejecutar(self, ciudad_nombre: str, lat: float, lon: float,
                 es_agricola: bool) -> ResultadoConsulta:
        datos = None
        modo_offline = False

        if lat == 0 and lon == 0:
            modo_offline = True
            datos = self._repositorio_clima.cargar_clima(ciudad_nombre)
            if not datos:
                raise DatosNoEncontradosError(
                    f"No hay datos locales para {ciudad_nombre}"
                )
        else:
            try:
                datos = self._servicio_clima.obtener_actual(lat, lon)
                self._repositorio_clima.guardar_clima(ciudad_nombre, datos)
            except Exception as e:
                datos_cargados = self._repositorio_clima.cargar_clima(ciudad_nombre)
                if datos_cargados:
                    datos = datos_cargados
                    modo_offline = True
                else:
                    raise ApiCaidaError(
                        f"No hay conexión a internet y no se encontraron datos de respaldo locales para {ciudad_nombre}. Detalle: {e}"
                    )

        condiciones = _analizar_condiciones(
            datos.actual.temperatura, datos.actual.humedad, datos.actual.precipitacion
        )
        analisis = _generar_recomendacion_local(es_agricola, condiciones)

        rec_ia = ""
        if not modo_offline:
            try:
                rec_ia = self._servicio_ia.generar_recomendacion(
                    datos.actual.temperatura, datos.actual.humedad,
                    datos.actual.precipitacion
                )
            except Exception:
                rec_ia = ""

        analisis_guardado = self._repositorio_analisis.cargar_analisis(ciudad_nombre)
        if modo_offline and analisis_guardado:
            rec_ia = analisis_guardado.get('recomendacion_ia', '')

        self._repositorio_analisis.guardar_analisis(ciudad_nombre, analisis, rec_ia)
        self._repositorio_historial.guardar_consulta(
            ciudad_nombre, datos.actual.temperatura, analisis.estado
        )

        pronostico_dicts = [
            {"fecha": d.fecha, "temperatura_max": d.temperatura_max,
             "temperatura_min": d.temperatura_min, "precipitacion": d.precipitacion,
             "humedad": d.humedad}
            for d in datos.pronostico
        ]
        clasificacion = _clasificar_dias(pronostico_dicts)
        estadisticas = _calcular_stats(pronostico_dicts)

        return ResultadoConsulta(
            ciudad=ciudad_nombre,
            datos=datos,
            analisis=analisis,
            recomendacion_ia=rec_ia,
            clasificacion_dias=clasificacion,
            modo_offline=modo_offline,
            estadisticas=estadisticas
        )
