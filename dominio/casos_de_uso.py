from typing import List, Optional

from dominio.entidades import (
    DatosClima, MedicionActual, AnalisisLocal, ResultadoConsulta
)
from dominio.puertos import (
    ServicioClima, ServicioIA, RepositorioClima, ConsultarClima
)


UMBRALES = {
    "temp_max": 35.0, "temp_min": 15.0, "rain_heavy": 15.0,
    "humidity_low": 40.0, "humidity_high": 90.0,
}


def _analizar_condiciones(temp: float, humidity: float,
                          precipitation: float) -> List[str]:
    condiciones = []
    if temp >= UMBRALES['temp_max']:
        condiciones.append("CALOR_EXTREMO")
    elif temp <= UMBRALES['temp_min']:
        condiciones.append("FRIO_BAJO")
    if precipitation >= UMBRALES['rain_heavy']:
        condiciones.append("LLUVIA_INTENSA")
    if humidity <= UMBRALES['humidity_low']:
        condiciones.append("HUMEDAD_BAJA")
    elif humidity >= UMBRALES['humidity_high']:
        condiciones.append("HUMEDAD_ALTA")
    return condiciones


def _generar_recomendacion_local(es_agricola: bool,
                                  condiciones: List[str]) -> AnalisisLocal:
    if not es_agricola:
        return AnalisisLocal(
            status="URBAN",
            mensaje="Zona urbana. Sin recomendaciones agricolas.",
            condiciones=[]
        )
    if not condiciones:
        return AnalisisLocal(
            status="FAVORABLE",
            mensaje="Condiciones ideales para siembra y cultivo.",
            condiciones=[]
        )
    if "LLUVIA_INTENSA" in condiciones:
        return AnalisisLocal(
            status="RIESGOSO",
            mensaje="Riesgo de inundacion. No aplicar fertilizantes.",
            condiciones=condiciones
        )
    if "CALOR_EXTREMO" in condiciones or "HUMEDAD_BAJA" in condiciones:
        return AnalisisLocal(
            status="RIESGOSO",
            mensaje="Estres hidrico. Se recomienda riego temprano.",
            condiciones=condiciones
        )
    return AnalisisLocal(
        status="NORMAL",
        mensaje="Condiciones aceptables. Monitorear el suelo.",
        condiciones=condiciones
    )


def _clasificar_dias(pronostico: List[dict]) -> List[dict]:
    clasificacion = []
    for dia in pronostico:
        score = 0
        if dia['temp_max'] >= UMBRALES['temp_max']:
            score += 2
        if dia['precipitation'] >= UMBRALES['rain_heavy']:
            score += 2
        if dia['humidity'] <= UMBRALES['humidity_low']:
            score += 1
        if score == 0:
            label = "Favorable"
        elif score <= 2:
            label = "Normal"
        else:
            label = "Riesgoso"
        clasificacion.append({"date": dia['date'], "label": label})
    return clasificacion


def _calcular_stats(pronostico: List[dict]) -> dict:
    if not pronostico:
        return {}
    temps = [(d['temp_max'] + d['temp_min']) / 2 for d in pronostico]
    media = sum(temps) / len(temps)
    lluvia_total = sum(d.get('precipitation', 0) for d in pronostico)
    max_temp = max(d['temp_max'] for d in pronostico)
    min_temp = min(d['temp_min'] for d in pronostico)
    tendencia = "Estable"
    if len(temps) > 1:
        diff = temps[-1] - temps[0]
        if diff > 0.5:
            tendencia = "En aumento"
        elif diff < -0.5:
            tendencia = "En descenso"
    return {
        "media": round(media, 1), "max": max_temp, "min": min_temp,
        "lluvia_total": round(lluvia_total, 1), "tendencia": tendencia
    }


class ObtenerClimaYAnalizar(ConsultarClima):
    def __init__(self, servicio_clima: ServicioClima,
                 servicio_ia: ServicioIA,
                 repositorio: RepositorioClima):
        self._servicio_clima = servicio_clima
        self._servicio_ia = servicio_ia
        self._repositorio = repositorio

    def ejecutar(self, ciudad_nombre: str, lat: float, lon: float,
                 es_agricola: bool) -> ResultadoConsulta:
        datos = None
        modo_offline = False

        if lat == 0 and lon == 0:
            modo_offline = True
            datos = self._repositorio.cargar_clima(ciudad_nombre)
            if not datos:
                raise RuntimeError(
                    f"No hay datos locales para {ciudad_nombre}"
                )
        else:
            try:
                datos = self._servicio_clima.obtener_actual(lat, lon)
                self._repositorio.guardar_clima(ciudad_nombre, datos)
            except Exception:
                datos_cargados = self._repositorio.cargar_clima(ciudad_nombre)
                if datos_cargados:
                    datos = datos_cargados
                    modo_offline = True
                else:
                    raise RuntimeError(
                        f"No hay datos disponibles para {ciudad_nombre}"
                    )

        condiciones = _analizar_condiciones(
            datos.actual.temp, datos.actual.humidity, datos.actual.precipitation
        )
        analisis = _generar_recomendacion_local(es_agricola, condiciones)

        rec_ia = ""
        if not modo_offline:
            try:
                rec_ia = self._servicio_ia.generar_recomendacion(
                    datos.actual.temp, datos.actual.humidity,
                    datos.actual.precipitation
                )
            except Exception:
                rec_ia = ""

        analisis_guardado = self._repositorio.cargar_analisis(ciudad_nombre)
        if modo_offline and analisis_guardado:
            rec_ia = analisis_guardado.get('recomendacion_ia', '')

        self._repositorio.guardar_analisis(ciudad_nombre, analisis, rec_ia)

        forecast_dicts = [
            {"date": d.date, "temp_max": d.temp_max,
             "temp_min": d.temp_min, "precipitation": d.precipitation,
             "humidity": d.humidity}
            for d in datos.forecast
        ]
        clasificacion = _clasificar_dias(forecast_dicts)
        stats = _calcular_stats(forecast_dicts)

        return ResultadoConsulta(
            ciudad=ciudad_nombre,
            datos=datos,
            analisis=analisis,
            recomendacion_ia=rec_ia,
            clasificacion_dias=clasificacion,
            modo_offline=modo_offline,
            stats=stats
        )
