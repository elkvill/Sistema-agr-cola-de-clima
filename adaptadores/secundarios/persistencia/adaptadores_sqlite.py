import sqlite3
import os
from typing import List, Optional

from dominio.entidades import DatosClima, AnalisisLocal, ConsultaHistorial
from dominio.puertos import RepositorioClima
from adaptadores.secundarios.persistencia.mapeadores import (
    MapeadorClima, MapeadorAnalisis, MapeadorHistorial
)


def _celsius_a_fahrenheit(celsius):
    if celsius is None:
        return None
    return round((celsius * 9 / 5) + 32, 1)


class _BaseSqlite:
    def __init__(self, db_path: str):
        self._db_path = db_path
        self._inicializar()

    def _conectar(self):
        conn = sqlite3.connect(self._db_path)
        conn.execute("PRAGMA foreign_keys = ON;")
        cursor = conn.cursor()
        cursor.execute("PRAGMA foreign_keys;")
        if cursor.fetchone()[0] != 1:
            raise RuntimeError("No se pudieron activar las claves foraneas")
        conn.create_function("celsius_a_fahrenheit", 1, _celsius_a_fahrenheit)
        return conn

    def _inicializar(self):
        conn = self._conectar()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS _migrations (
                    version INTEGER PRIMARY KEY,
                    description TEXT NOT NULL,
                    applied_at TEXT NOT NULL DEFAULT (datetime('now','localtime'))
                );
            """)
            conn.commit()

            cursor.execute(
                "SELECT COUNT(*) FROM _migrations WHERE version = 1")
            if cursor.fetchone()[0] > 0:
                return

            cursor.execute("BEGIN TRANSACTION;")

            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' "
                           "AND name IN ('ciudades','clima_actual','clima_pronostico','historial_consultas','analisis_clima','log_auditoria','recomendaciones_ia')")
            tablas_viejas = [r[0] for r in cursor.fetchall()]

            necesita_migrar = False
            if 'clima_actual' in tablas_viejas:
                cursor.execute("PRAGMA table_info(clima_actual);")
                columnas = [r[1] for r in cursor.fetchall()]
                if 'temp' in columnas:
                    necesita_migrar = True

            if necesita_migrar:
                for t in ('trg_validar_humedad', 'trg_auditar_consulta', 'trg_log_analisis'):
                    cursor.execute(f"DROP TRIGGER IF EXISTS {t};")
                for t in tablas_viejas:
                    cursor.execute(f"ALTER TABLE {t} RENAME TO old_{t};")

            cursor.execute("""
                CREATE TABLE ciudades (
                    nombre TEXT NOT NULL CONSTRAINT pk_ciudades PRIMARY KEY,
                    latitud REAL NOT NULL,
                    longitud REAL NOT NULL,
                    es_agricola INTEGER DEFAULT 1 CHECK(es_agricola IN (0,1))
                );
            """)

            cursor.execute("""
                CREATE TABLE clima_actual (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ciudad TEXT NOT NULL CONSTRAINT uq_clima_actual_ciudad UNIQUE,
                    temperatura REAL NOT NULL CHECK(temperatura BETWEEN -50 AND 60),
                    humedad REAL NOT NULL CHECK(humedad BETWEEN 0 AND 100),
                    precipitacion REAL NOT NULL CHECK(precipitacion >= 0),
                    fecha_guardado TEXT NOT NULL DEFAULT (datetime('now','localtime'))
                        CHECK(fecha_guardado GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9] [0-9][0-9]:[0-9][0-9]:[0-9][0-9]'),
                    CONSTRAINT fk_clima_actual_ciudad FOREIGN KEY (ciudad) REFERENCES ciudades(nombre) ON DELETE CASCADE
                );
            """)

            cursor.execute("""
                CREATE TABLE clima_pronostico (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ciudad TEXT NOT NULL,
                    fecha TEXT NOT NULL CHECK(fecha GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]'),
                    temperatura_maxima REAL NOT NULL CHECK(temperatura_maxima BETWEEN -50 AND 60),
                    temperatura_minima REAL NOT NULL CHECK(temperatura_minima BETWEEN -50 AND 60),
                    precipitacion REAL NOT NULL CHECK(precipitacion >= 0),
                    humedad REAL NOT NULL CHECK(humedad BETWEEN 0 AND 100),
                    fecha_guardado TEXT NOT NULL DEFAULT (datetime('now','localtime'))
                        CHECK(fecha_guardado GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9] [0-9][0-9]:[0-9][0-9]:[0-9][0-9]'),
                    CONSTRAINT fk_clima_pronostico_ciudad FOREIGN KEY (ciudad) REFERENCES ciudades(nombre) ON DELETE CASCADE,
                    CONSTRAINT uq_clima_pronostico_ciudad_fecha UNIQUE (ciudad, fecha)
                );
            """)

            cursor.execute("""
                CREATE TABLE historial_consultas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    fecha_consulta TEXT NOT NULL DEFAULT (datetime('now','localtime'))
                        CHECK(fecha_consulta GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9] [0-9][0-9]:[0-9][0-9]:[0-9][0-9]'),
                    ciudad TEXT NOT NULL,
                    temperatura REAL NOT NULL CHECK(temperatura BETWEEN -50 AND 60),
                    estado TEXT NOT NULL CHECK(estado IN ('URBAN','NORMAL','FAVORABLE','RIESGOSO')),
                    CONSTRAINT fk_historial_consultas_ciudad FOREIGN KEY (ciudad) REFERENCES ciudades(nombre) ON DELETE CASCADE
                );
            """)

            cursor.execute("""
                CREATE TABLE analisis_clima (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    clima_actual_id INTEGER NOT NULL CONSTRAINT uq_analisis_clima_clima_actual UNIQUE,
                    estado TEXT NOT NULL CHECK(estado IN ('URBAN','NORMAL','FAVORABLE','RIESGOSO')),
                    condiciones TEXT NOT NULL,
                    mensaje TEXT NOT NULL,
                    recomendacion TEXT NOT NULL,
                    fecha_analisis TEXT NOT NULL DEFAULT (datetime('now','localtime'))
                        CHECK(fecha_analisis GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9] [0-9][0-9]:[0-9][0-9]:[0-9][0-9]'),
                    CONSTRAINT fk_analisis_clima_clima_actual FOREIGN KEY (clima_actual_id) REFERENCES clima_actual(id) ON DELETE CASCADE
                );
            """)

            cursor.execute("""
                CREATE TABLE log_auditoria (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tabla TEXT NOT NULL,
                    operacion TEXT NOT NULL CHECK(operacion IN ('INSERT','UPDATE','DELETE')),
                    registro_id INTEGER,
                    detalle TEXT,
                    fecha TEXT NOT NULL DEFAULT (datetime('now','localtime'))
                        CHECK(fecha GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9] [0-9][0-9]:[0-9][0-9]:[0-9][0-9]'),
                    usuario TEXT NOT NULL DEFAULT 'sistema',
                    direccion_ip TEXT NOT NULL DEFAULT '127.0.0.1'
                );
            """)

            cursor.execute("CREATE INDEX IF NOT EXISTS idx_clima_pronostico_ciudad ON clima_pronostico (ciudad)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_historial_fecha ON historial_consultas (fecha_consulta DESC)")

            cursor.execute("""
                CREATE TRIGGER trg_log_analisis AFTER INSERT ON analisis_clima FOR EACH ROW BEGIN
                    INSERT INTO log_auditoria (tabla, operacion, registro_id, detalle)
                    VALUES ('analisis_clima', 'INSERT', NEW.id,
                        'Ciudad: ' || (SELECT ciudad FROM clima_actual WHERE id = NEW.clima_actual_id) || ', Estado: ' || NEW.estado ||
                        ', Condiciones: ' || NEW.condiciones);
                END;
            """)

            if necesita_migrar:
                cursor.execute("INSERT INTO ciudades SELECT nombre, latitud, longitud, es_agricola FROM old_ciudades")
                cursor.execute("INSERT INTO clima_actual (ciudad, temperatura, humedad, precipitacion, fecha_guardado) SELECT ciudad, temp, humidity, precipitation, fecha_guardado FROM old_clima_actual")
                cursor.execute("INSERT OR IGNORE INTO clima_pronostico (ciudad, fecha, temperatura_maxima, temperatura_minima, precipitacion, humedad, fecha_guardado) SELECT ciudad, substr(date,1,10), temp_max, temp_min, precipitation, humidity, fecha_guardado FROM old_clima_pronostico")
                cursor.execute("INSERT INTO historial_consultas (fecha_consulta, ciudad, temperatura, estado) SELECT fecha_consulta, ciudad, temp, status FROM old_historial_consultas")
                cursor.execute("""
                    INSERT INTO analisis_clima (clima_actual_id, estado, condiciones, mensaje, recomendacion, fecha_analisis)
                    SELECT ca.id, ac.status, ac.condiciones, ac.mensaje, COALESCE(ac.recomendacion_ia,''), ac.fecha_consulta
                    FROM old_analisis_clima ac JOIN clima_actual ca ON ca.ciudad = ac.ciudad
                    WHERE ac.id = (SELECT MAX(ac2.id) FROM old_analisis_clima ac2 WHERE ac2.ciudad = ac.ciudad)
                """)
                cursor.execute("""
                    INSERT INTO log_auditoria (tabla, operacion, registro_id, detalle, fecha)
                    SELECT tabla, CASE WHEN operacion IN ('INSERT','UPDATE','DELETE') THEN operacion ELSE 'INSERT' END, registro_id, detalle, fecha FROM old_log_auditoria
                """)
                for t in tablas_viejas:
                    cursor.execute(f"DROP TABLE IF EXISTS old_{t};")

            cursor.execute("SELECT COUNT(*) FROM ciudades")
            if cursor.fetchone()[0] == 0:
                from configuracion.ajustes import CIUDADES
                for nombre, coord in CIUDADES.items():
                    cursor.execute("INSERT INTO ciudades (nombre, latitud, longitud, es_agricola) VALUES (?,?,?,?)",
                                   (nombre, coord["lat"], coord["lon"], 1 if coord["es_agricola"] else 0))

            cursor.execute("INSERT INTO _migrations (version, description) VALUES (1, 'Esquema unificado en espanol')")
            conn.commit()
        finally:
            conn.close()

    def _limpiar_antiguos(self, conn):
        cursor = conn.cursor()
        cursor.execute("DELETE FROM clima_pronostico WHERE date(fecha) < date('now', '-10 days')")
        cursor.execute("DELETE FROM historial_consultas WHERE date(fecha_consulta) < date('now', '-90 days')")
        cursor.execute("DELETE FROM log_auditoria WHERE date(fecha) < date('now', '-365 days')")


class AdaptadorSqlite(_BaseSqlite, RepositorioClima):
    def guardar_clima(self, ciudad: str, datos: DatosClima) -> None:
        conn = self._conectar()
        cursor = conn.cursor()
        try:
            cursor.execute("BEGIN TRANSACTION;")
            cursor.execute("""
                INSERT INTO clima_actual (ciudad, temperatura, humedad, precipitacion, fecha_guardado)
                VALUES (?, ?, ?, ?, datetime('now','localtime'))
                ON CONFLICT(ciudad) DO UPDATE SET
                    temperatura=excluded.temperatura, humedad=excluded.humedad,
                    precipitacion=excluded.precipitacion, fecha_guardado=excluded.fecha_guardado
            """, (ciudad, datos.actual.temperatura, datos.actual.humedad, datos.actual.precipitacion))
            cursor.execute("DELETE FROM clima_pronostico WHERE ciudad = ?", (ciudad,))
            for p in datos.pronostico:
                cursor.execute("""
                    INSERT INTO clima_pronostico (ciudad, fecha, temperatura_maxima, temperatura_minima, precipitacion, humedad, fecha_guardado)
                    VALUES (?,?,?,?,?,?, datetime('now','localtime'))
                """, MapeadorClima.pronostico_a_fila(ciudad, p))
            self._limpiar_antiguos(conn)
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
            cursor.execute("SELECT temperatura, humedad, precipitacion FROM clima_actual WHERE ciudad = ?", (ciudad,))
            row = cursor.fetchone()
            if not row:
                return None
            actual = MapeadorClima.fila_a_medicion(row)
            cursor.execute("SELECT fecha, temperatura_maxima, temperatura_minima, precipitacion, humedad FROM clima_pronostico WHERE ciudad = ? ORDER BY fecha", (ciudad,))
            pronostico = [MapeadorClima.fila_a_pronostico(r) for r in cursor.fetchall()]
            return DatosClima(actual=actual, pronostico=pronostico)
        finally:
            conn.close()

    def guardar_analisis(self, ciudad: str, analisis: AnalisisLocal, rec_ia: str) -> None:
        conn = self._conectar()
        cursor = conn.cursor()
        try:
            cursor.execute("BEGIN TRANSACTION;")
            cursor.execute("SELECT id FROM clima_actual WHERE ciudad = ?", (ciudad,))
            row = cursor.fetchone()
            if not row:
                raise ValueError(f"No existe clima actual para {ciudad}")
            cursor.execute("""
                INSERT INTO analisis_clima (clima_actual_id, estado, condiciones, mensaje, recomendacion, fecha_analisis)
                VALUES (?, ?, ?, ?, ?, datetime('now','localtime'))
                ON CONFLICT(clima_actual_id) DO UPDATE SET
                    estado=excluded.estado, condiciones=excluded.condiciones,
                    mensaje=excluded.mensaje, recomendacion=excluded.recomendacion,
                    fecha_analisis=excluded.fecha_analisis
            """, (row[0], analisis.estado,
                  ",".join(analisis.condiciones) if analisis.condiciones else "NINGUNA",
                  analisis.mensaje, rec_ia))
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
                SELECT ac.estado, ac.mensaje, ac.condiciones, ac.recomendacion
                FROM analisis_clima ac JOIN clima_actual ca ON ac.clima_actual_id = ca.id
                WHERE ca.ciudad = ? ORDER BY ac.fecha_analisis DESC LIMIT 1
            """, (ciudad,))
            row = cursor.fetchone()
            return MapeadorAnalisis.fila_a_analisis(row) if row else None
        finally:
            conn.close()

    def guardar_consulta(self, ciudad: str, temperatura: float, estado: str) -> None:
        conn = self._conectar()
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO historial_consultas (ciudad, temperatura, estado) VALUES (?, ?, ?)",
                           (ciudad, temperatura, estado))
            conn.commit()
        finally:
            conn.close()

    def obtener_historial(self, limite: int = 5) -> List[ConsultaHistorial]:
        conn = self._conectar()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT fecha_consulta, ciudad, temperatura, estado FROM historial_consultas ORDER BY fecha_consulta DESC LIMIT ?", (limite,))
            return [MapeadorHistorial.fila_a_historial(r) for r in cursor.fetchall()]
        finally:
            conn.close()
