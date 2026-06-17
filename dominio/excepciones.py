class ErrorDominio(Exception):
    "Clase base para todas las excepciones del dominio."
    pass


class ApiCaidaError(ErrorDominio):
    "Se lanza cuando la API externa falla y no hay conexión a internet."
    pass


class DatosNoEncontradosError(ErrorDominio):
    "Se lanza cuando se solicitan datos de una ciudad que no existen en local ni en remoto."
    pass
