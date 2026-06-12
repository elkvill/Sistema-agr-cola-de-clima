import sqlite3
import os
from typing import List, Optional

from dominio.entidades import (
    DatosClima, MedicionActual, PronosticoDia,
    AnalisisLocal, ConsultaHistorial
)
from dominio.puertos import RepositorioClima


def _clasificar_clima_udf(temp, humidity, es_agricola):
    if not es_agricola:
        return "URBAN"
    if temp >= 35.0 or humidity <= 40.0 or humidity >= 90.0:
        return "RIESGOSO"
    return "FAVORABLE"


def _celsius_a_fahrenheit(celsius):
    if celsius is None:
        return None
    return round((celsius * 9 / 5) + 32, 1)


class SQLiteRepositorio(RepositorioClima):
    def __init__(self, db_path: str):
        self._db_path = db_path
        self._inicializar()

    def _conectar(self):
        conn = sqlite3.connect(self._db_path)
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.create_function("clasificar_clima", 3, _clasificar_clima_udf)
        conn.create_function("celsius_a_fahrenheit", 1, _celsius_a_fahrenheit)
        return conn

    def _inicializar(self):
        conn = self._conectar()
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ciudades (
                nombre TEXT PRIMARY KEY, latitud REAL NOT NULL,
                longitud REAL NOT NULL, es_agricola INTEGER DEFAULT 1)
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS clima_actual (
                ciudad TEXT PRIMARY KEY, temp REAL NOT NULL,
                humidity REAL NOT NULL, precipitation REAL NOT NULL,
                fecha_guardado TEXT DEFAULT (datetime('now','localtime')),
                FOREIGN KEY (ciudad) REFERENCES ciudades(nombre) ON DELETE CASCADE)
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS clima_pronostico (
                id INTEGER PRIMARY KEY AUTOINCREMENT, ciudad TEXT NOT NULL,
                date TEXT NOT NULL, temp_max REAL NOT NULL, temp_min REAL NOT NULL,
                precipitation REAL NOT NULL, humidity REAL NOT NULL,
                fecha_guardado TEXT DEFAULT (datetime('now','localtime')),
                FOREIGN KEY (ciudad) REFERENCES ciudades(nombre) ON DELETE CASCADE)
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS historial_consultas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fecha_consulta TEXT DEFAULT (datetime('now','localtime')),
                ciudad TEXT NOT NULL, temp REAL NOT NULL, status TEXT NOT NULL,
                FOREIGN KEY (ciudad) REFERENCES ciudades(nombre) ON DELETE CASCADE)
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS recomendaciones_ia (
                id INTEGER PRIMARY KEY AUTOINCREMENT, ciudad TEXT NOT NULL,
                temp REAL NOT NULL, humidity REAL NOT NULL,
                precipitation REAL NOT NULL, recomendacion TEXT NOT NULL,
                fecha_consulta TEXT DEFAULT (datetime('now','localtime')),
                FOREIGN KEY (ciudad) REFERENCES ciudades(nombre) ON DELETE CASCADE)
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS analisis_clima (
                id INTEGER PRIMARY KEY AUTOINCREMENT, ciudad TEXT NOT NULL,
                status TEXT NOT NULL, mensaje TEXT NOT NULL,
                condiciones TEXT NOT NULL, recomendacion_ia TEXT DEFAULT '',
                temp REAL NOT NULL, humidity REAL NOT NULL,
                precipitation REAL NOT NULL,
                fecha_consulta TEXT DEFAULT (datetime('now','localtime')),
                FOREIGN KEY (ciudad) REFERENCES ciudades(nombre) ON DELETE CASCADE)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_clima_pronostico_ciudad
            ON clima_pronostico (ciudad)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_historial_fecha
            ON historial_consultas (fecha_consulta DESC)
        """)

        cursor.execute("DROP TRIGGER IF EXISTS trg_validar_humedad")
        cursor.execute("""
            CREATE TRIGGER trg_validar_humedad
            BEFORE INSERT ON clima_actual FOR EACH ROW BEGIN
                SELECT CASE WHEN NEW.humidity < 0 OR NEW.humidity > 100
                THEN RAISE(ABORT, 'Humedad fuera de rango') END;
            END;
        """)

        cursor.execute("DROP TRIGGER IF EXISTS trg_auditar_consulta")
        cursor.execute("""
            CREATE TRIGGER trg_auditar_consulta
            AFTER INSERT ON clima_actual FOR EACH ROW BEGIN
                INSERT INTO historial_consultas (ciudad, temp, status)
                VALUES (NEW.ciudad, NEW.temp,
                (SELECT clasificar_clima(NEW.temp, NEW.humidity, c.es_agricola)
                 FROM ciudades c WHERE c.nombre = NEW.ciudad));
            END;
        """)

        cursor.execute("DROP TRIGGER IF EXISTS trg_log_analisis")
        cursor.execute("""
            CREATE TRIGGER trg_log_analisis
            AFTER INSERT ON analisis_clima FOR EACH ROW BEGIN
                INSERT INTO log_auditoria (tabla, operacion, registro_id, detalle)
                VALUES ('analisis_clima', 'INSERT', NEW.id,
                'Ciudad: ' || NEW.ciudad || ', Status: ' || NEW.status ||
                ', Condiciones: ' || NEW.condiciones);
            END;
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS log_auditoria (
                id INTEGER PRIMARY KEY AUTOINCREMENT, tabla TEXT NOT NULL,
                operacion TEXT NOT NULL, registro_id INTEGER, detalle TEXT,
                fecha TEXT DEFAULT (datetime('now','localtime')))
        """)

        conn.commit()
        conn.close()

    def guardar_clima(self, ciudad: str, datos: DatosClima) -> None:
        conn = self._conectar()
        cursor = conn.cursor()
        try:
            cursor.execute("BEGIN TRANSACTION;")
            cursor.execute("""
                INSERT OR REPLACE INTO clima_actual
                (ciudad, temp, humidity, precipitation)
                VALUES (?,?,?,?)
            """, (ciudad, datos.actual.temp, datos.actual.humidity,
                  datos.actual.precipitation))
            cursor.execute("DELETE FROM clima_pronostico WHERE ciudad = ?", (ciudad,))
            for f in datos.forecast:
                cursor.execute("""
                    INSERT INTO clima_pronostico
                    (ciudad, date, temp_max, temp_min, precipitation, humidity)
                    VALUES (?,?,?,?,?,?)
                """, (ciudad, f.date, f.temp_max, f.temp_min,
                      f.precipitation, f.humidity))
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def cargar_clima(self, ciudad: str) -> Optional[DatosClima]:
        conn = self._conectar()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "SELECT temp, humidity, precipitation FROM clima_actual WHERE ciudad = ?",
                (ciudad,)
            )
            row = cursor.fetchone()
            if not row:
                return None
            actual = MedicionActual(temp=row[0], humidity=row[1], precipitation=row[2])
            cursor.execute(
                "SELECT date, temp_max, temp_min, precipitation, humidity "
                "FROM clima_pronostico WHERE ciudad = ? ORDER BY date", (ciudad,)
            )
            forecast = [PronosticoDia(date=r[0], temp_max=r[1], temp_min=r[2],
                                      precipitation=r[3], humidity=r[4])
                        for r in cursor.fetchall()]
            return DatosClima(actual=actual, forecast=forecast)
        finally:
            conn.close()

    def guardar_analisis(self, ciudad: str, analisis: AnalisisLocal,
                         rec_ia: str) -> None:
        conn = self._conectar()
        cursor = conn.cursor()
        try:
            cursor.execute("BEGIN TRANSACTION;")
            if rec_ia:
                cursor.execute("""
                    INSERT INTO recomendaciones_ia
                    (ciudad, temp, humidity, precipitation, recomendacion)
                    VALUES (?,?,?,?,?)
                """, (ciudad, 0, 0, 0, rec_ia))
            cursor.execute("""
                INSERT INTO analisis_clima
                (ciudad, status, mensaje, condiciones, recomendacion_ia,
                 temp, humidity, precipitation)
                VALUES (?,?,?,?,?,?,?,?)
            """, (ciudad, analisis.status, analisis.mensaje,
                  ",".join(analisis.condiciones) if analisis.condiciones else "NINGUNA",
                  rec_ia, 0, 0, 0))
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def cargar_analisis(self, ciudad: str) -> Optional[dict]:
        conn = self._conectar()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT status, mensaje, condiciones, recomendacion_ia
                FROM analisis_clima WHERE ciudad = ?
                ORDER BY fecha_consulta DESC LIMIT 1
            """, (ciudad,))
            row = cursor.fetchone()
            if not row:
                return None
            result = {
                'status': row[0], 'mensaje': row[1],
                'condiciones': row[2],
                'recomendacion_ia': row[3] if row[3] else ""
            }
            cursor.execute("""
                SELECT recomendacion FROM recomendaciones_ia
                WHERE ciudad = ? ORDER BY fecha_consulta DESC LIMIT 1
            """, (ciudad,))
            row_ia = cursor.fetchone()
            if row_ia:
                result['recomendacion_gemini'] = row_ia[0]
            return result
        finally:
            conn.close()

    def historial(self, limite: int = 5) -> List[ConsultaHistorial]:
        conn = self._conectar()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT fecha_consulta, ciudad, temp, status
                FROM historial_consultas
                ORDER BY fecha_consulta DESC LIMIT ?
            """, (limite,))
            return [
                ConsultaHistorial(fecha=r[0], ciudad=r[1], temp=r[2], status=r[3])
                for r in cursor.fetchall()
            ]
        finally:
            conn.close()
