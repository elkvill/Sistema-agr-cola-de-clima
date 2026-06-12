import os

from config.settings import (
    USAR_API, CLAVE_API_OPENWEATHER, CLAVE_API_GROQ, CIUDADES
)
from dominio.casos_de_uso import ObtenerClimaYAnalizar
from adaptadores.secundarios.api.openmeteo_adapter import OpenMeteoAdapter
from adaptadores.secundarios.api.openweather_adapter import OpenWeatherAdapter
from adaptadores.secundarios.api.groq_adapter import GroqAdapter
from adaptadores.secundarios.persistencia.sqlite_repositorio import SQLiteRepositorio
from adaptadores.primarios.streamlit_ui import StreamlitUI


def crear_aplicacion():
    _BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db_path = os.path.join(_BASE_DIR, 'data_backup.db')

    if USAR_API == "openmeteo":
        servicio_clima = OpenMeteoAdapter()
    else:
        servicio_clima = OpenWeatherAdapter(CLAVE_API_OPENWEATHER)

    servicio_ia = GroqAdapter(CLAVE_API_GROQ)
    repositorio = SQLiteRepositorio(db_path)

    caso_uso = ObtenerClimaYAnalizar(servicio_clima, servicio_ia, repositorio)

    ui = StreamlitUI(caso_uso, servicio_ia, repositorio, CIUDADES)
    return ui
