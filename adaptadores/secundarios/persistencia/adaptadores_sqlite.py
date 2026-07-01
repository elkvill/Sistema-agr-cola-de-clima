import sqlite3
from typing import List, Optional

from dominio.entidades import DatosClima, AnalisisLocal, ConsultaHistorial
from dominio.puertos import RepositorioClima
from adaptadores.secundarios.persistencia.mapeadores import (
    MapeadorClima, MapeadorAnalisis, MapeadorHistorial
)


class _BaseSqlite:
    def __init__(self, db_path: str):
        self._db_path = db_path

    def _conectar(self):
        conn = sqlite3.connect(self._db_path)
        conn.execute("PRAGMA foreign_keys = ON;")
        cursor = conn.cursor()
        cursor.execute("PRAGMA foreign_keys;")
        if cursor.fetchone()[0] != 1:
            raise RuntimeError("No se pudieron activar las claves foraneas")
        return conn

    def _limpiar_antiguos(self, conn):
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM clima_pronostico "
            "WHERE date(fecha) < date('now', '-10 days')"
        )
        cursor.execute(
            "DELETE FROM historial_consultas "
            "WHERE date(fecha_consulta) < date('now', '-90 days')"
        )
        cursor.execute(
            "DELETE FROM log_auditoria "
            "WHERE date(fecha) < date('now', '-365 days')"
        )



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
            cursor.execute(
                "SELECT fecha, temperatura_maxima, temperatura_minima, precipitacion, humedad "
                "FROM clima_pronostico WHERE ciudad = ? ORDER BY fecha",
                (ciudad,)
            )
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
            cursor.execute(
                "SELECT fecha_consulta, ciudad, temperatura, estado "
                "FROM historial_consultas ORDER BY fecha_consulta DESC LIMIT ?",
                (limite,)
            )
            return [MapeadorHistorial.fila_a_historial(r) for r in cursor.fetchall()]
        finally:
            conn.close()
