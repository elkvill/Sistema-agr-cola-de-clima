from dominio.entidades import (
    MedicionActual, PronosticoDia, ConsultaHistorial
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
