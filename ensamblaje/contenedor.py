import os

from configuracion.ajustes import (
    CLAVE_API_OPENWEATHER, CLAVE_API_GROQ, CIUDADES, UMBRALES
)
from dominio.consultar_y_analizar_clima import ObtenerClimaYAnalizar
from adaptadores.secundarios.api.openweather_adaptador import OpenWeatherAdapter
from adaptadores.secundarios.api.groq_adaptador import GroqAdapter
from adaptadores.secundarios.persistencia.migrador_sqlite import MigradorSqlite
from adaptadores.secundarios.persistencia.adaptadores_sqlite import AdaptadorSqlite
from adaptadores.primarios.interfaz_streamlit import StreamlitUI
from adaptadores.primarios.utils_ui import VerificadorConectividadSocket

from dominio.analizador_condiciones import (
    AnalizadorCondiciones,
    EvaluadorCalorExtremo,
    EvaluadorFrioBajo,
    EvaluadorLluviaIntensa,
    EvaluadorHumedadBaja,
    EvaluadorHumedadAlta
)
from dominio.generador_recomendacion import GeneradorRecomendacion
from dominio.clasificador_pronostico import (
    ClasificadorPronostico, ClasificacionPuntuacionStrategy
)


def crear_aplicacion():
    _BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db_path = os.path.join(_BASE_DIR, 'data_backup.db')

    # Ejecutar migraciones e inicialización de BD de forma aislada
    migrador = MigradorSqlite(db_path)
    migrador.ejecutar_migraciones()

    servicio_clima = OpenWeatherAdapter(CLAVE_API_OPENWEATHER)
    servicio_ia = GroqAdapter(CLAVE_API_GROQ)

    # Repositorio dedicado solo a CRUD
    repositorio = AdaptadorSqlite(db_path)

    # Configuración de evaluadores de condiciones climáticas 
    evaluadores = [
        EvaluadorCalorExtremo(UMBRALES["temp_max"]),
        EvaluadorFrioBajo(UMBRALES["temp_min"]),
        EvaluadorLluviaIntensa(UMBRALES["rain_heavy"]),
        EvaluadorHumedadBaja(UMBRALES["humidity_low"]),
        EvaluadorHumedadAlta(UMBRALES["humidity_high"])
    ]
    analizador = AnalizadorCondiciones(evaluadores)

    # Generador y Clasificador configurados
    generador = GeneradorRecomendacion()
    estrategia_clasificacion = ClasificacionPuntuacionStrategy(UMBRALES)
    clasificador = ClasificadorPronostico(estrategia_clasificacion)

    # Inyección de dependencias en caso de uso
    caso_uso = ObtenerClimaYAnalizar(
        servicio_clima, servicio_ia, repositorio, analizador, generador, clasificador
    )

    verificador_conectividad = VerificadorConectividadSocket()

    ui = StreamlitUI(caso_uso, servicio_ia, repositorio, CIUDADES, verificador_conectividad)
    return ui
