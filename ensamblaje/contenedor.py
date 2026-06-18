import os

from configuracion.ajustes import (
    CLAVE_API_OPENWEATHER, CLAVE_API_GROQ, CIUDADES
)
from dominio.consultar_y_analizar_clima import ObtenerClimaYAnalizar
from adaptadores.secundarios.api.openweather_adaptador import OpenWeatherAdapter
from adaptadores.secundarios.api.groq_adaptador import GroqAdapter
from adaptadores.secundarios.persistencia.adaptadores_sqlite import (
    AdaptadorSqliteClima, AdaptadorSqliteAnalisis,
    AdaptadorSqliteHistorial, AdaptadorSqliteCiudades
)
from adaptadores.primarios.interfaz_streamlit import StreamlitUI


def crear_aplicacion():
    _BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db_path = os.path.join(_BASE_DIR, 'data_backup.db')

    servicio_clima = OpenWeatherAdapter(CLAVE_API_OPENWEATHER)
    servicio_ia = GroqAdapter(CLAVE_API_GROQ)

    repo_clima = AdaptadorSqliteClima(db_path)
    repo_analisis = AdaptadorSqliteAnalisis(db_path)
    repo_historial = AdaptadorSqliteHistorial(db_path)

    caso_uso = ObtenerClimaYAnalizar(
        servicio_clima, servicio_ia, repo_clima, repo_analisis, repo_historial
    )

    ui = StreamlitUI(caso_uso, servicio_ia, repo_analisis, repo_historial, CIUDADES)
    return ui
