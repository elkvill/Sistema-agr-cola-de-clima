# Clase base para todas las excepciones del dominio.
class ErrorDominio(Exception):
    pass


#   Se lanza cuando la API externa falla y no hay conexión a internet.

class ApiCaidaError(ErrorDominio):
    pass

# Se lanza cuando se solicitan datos de una ciudad que no existen en local ni en remoto.


class DatosNoEncontradosError(ErrorDominio):
    pass
