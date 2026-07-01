import sqlite3


class MigradorSqlite:

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

    def ejecutar_migraciones(self):
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
                CREATE TRIGGER IF NOT EXISTS trg_log_analisis AFTER INSERT ON analisis_clima FOR EACH ROW BEGIN
                    INSERT INTO log_auditoria (tabla, operacion, registro_id, detalle)
                    VALUES ('analisis_clima', 'INSERT', NEW.id,
                        'Ciudad: ' || (SELECT ciudad FROM clima_actual WHERE id = NEW.clima_actual_id) || ', Estado: ' || NEW.estado ||
                        ', Condiciones: ' || NEW.condiciones);
                END;
            """)

            if necesita_migrar:
                cursor.execute(
                    "INSERT INTO ciudades "
                    "SELECT nombre, latitud, longitud, es_agricola FROM old_ciudades"
                )
                cursor.execute(
                    "INSERT INTO clima_actual (ciudad, temperatura, humedad, precipitacion, fecha_guardado) "
                    "SELECT ciudad, temp, humidity, precipitation, fecha_guardado FROM old_clima_actual"
                )
                cursor.execute(
                    "INSERT OR IGNORE INTO clima_pronostico "
                    "(ciudad, fecha, temperatura_maxima, temperatura_minima, precipitacion, humedad, fecha_guardado) "
                    "SELECT ciudad, substr(date,1,10), temp_max, temp_min, precipitation, humidity, fecha_guardado "
                    "FROM old_clima_pronostico"
                )
                cursor.execute(
                    "INSERT INTO historial_consultas (fecha_consulta, ciudad, temperatura, estado) "
                    "SELECT fecha_consulta, ciudad, temp, status FROM old_historial_consultas"
                )
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
