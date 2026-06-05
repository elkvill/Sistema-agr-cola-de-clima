import sqlite3
import datetime
import os

DB_PATH = 'data_backup.db'

# UDF 1: Clasificador agrícola de clima en base a temperatura y humedad
def clasificar_clima_udf(temp, humidity, es_agricola):
    if not es_agricola:
        return "URBAN"
    # Lógica agrónoma (de services/analysis.py):
    # RIESGOSO si temp >= 35.0 (calor extremo) o humedad <= 40.0 (humedad baja)
    if temp >= 35.0 or humidity <= 40.0:
        return "RIESGOSO"
    if humidity >= 90.0: # humedad muy alta
        return "RIESGOSO"
    return "FAVORABLE"

# UDF 2: Conversión de Celsius a Fahrenheit en SQL
def celsius_a_fahrenheit(celsius):
    if celsius is None:
        return None
    return round((celsius * 9/5) + 32, 1)

def conectar_db():
    """Abre conexión con la base de datos, activa FKs y registra UDFs."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    # Registrar funciones definidas por el usuario (UDF)
    conn.create_function("clasificar_clima", 3, clasificar_clima_udf)
    conn.create_function("celsius_a_fahrenheit", 1, celsius_a_fahrenheit)
    return conn

def _esquema_necesita_recreacion(cursor):
    """Detecta si clima_actual tiene esquema incorrecto (ej. creado sin PK por versión anterior)."""
    cursor.execute("PRAGMA table_info(clima_actual)")
    columnas = cursor.fetchall()
    if not columnas:
        return False
    for col in columnas:
        if col[1] == 'ciudad' and col[5] == 1:
            return False
    return True

def _recrear_esquema_completo(cursor, conn):
    """Elimina tablas mal creadas, objetos dependientes y tablas leftover, conservando ciudades e historial."""
    cursor.execute("DROP TRIGGER IF EXISTS trg_auditar_consulta")
    cursor.execute("DROP TRIGGER IF EXISTS trg_validar_humedad")
    cursor.execute("DROP VIEW IF EXISTS vista_resumen_agricola")
    cursor.execute("DROP TABLE IF EXISTS clima_pronostico")
    cursor.execute("DROP TABLE IF EXISTS clima_actual")
    cursor.execute("DROP TABLE IF EXISTS historial_ia")
    conn.commit()

def init_db():
    """Crea la base de datos, tablas, índices, vistas y triggers si no existen."""
    conn = conectar_db()
    cursor = conn.cursor()
    
    # Verificar si el esquema existente es incorrecto (de versiones previas)
    if _esquema_necesita_recreacion(cursor):
        _recrear_esquema_completo(cursor, conn)
    
    # 1. Tabla de ciudades (padre)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ciudades (
            nombre TEXT PRIMARY KEY,
            latitud REAL NOT NULL,
            longitud REAL NOT NULL,
            es_agricola INTEGER DEFAULT 1
        )
    """)
    
    # Sembrar ciudades iniciales
    from config.settings import CIUDADES
    for nombre, coord in CIUDADES.items():
        cursor.execute("""
            INSERT OR IGNORE INTO ciudades (nombre, latitud, longitud, es_agricola)
            VALUES (?, ?, ?, ?)
        """, (nombre, coord['lat'], coord['lon'], 1 if coord['es_agricola'] else 0))
    
    # 2. Tabla clima_actual
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS clima_actual (
            ciudad TEXT PRIMARY KEY,
            temp REAL NOT NULL,
            humidity REAL NOT NULL,
            precipitation REAL NOT NULL,
            fecha_guardado TEXT DEFAULT (datetime('now', 'localtime')),
            FOREIGN KEY (ciudad) REFERENCES ciudades(nombre) ON DELETE CASCADE
        )
    """)
    
    # 3. Tabla clima_pronostico
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS clima_pronostico (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ciudad TEXT NOT NULL,
            date TEXT NOT NULL,
            temp_max REAL NOT NULL,
            temp_min REAL NOT NULL,
            precipitation REAL NOT NULL,
            humidity REAL NOT NULL,
            fecha_guardado TEXT DEFAULT (datetime('now', 'localtime')),
            FOREIGN KEY (ciudad) REFERENCES ciudades(nombre) ON DELETE CASCADE
        )
    """)
    
    # 4. Tabla de Auditoría / Historial de Consultas
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS historial_consultas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha_consulta TEXT DEFAULT (datetime('now', 'localtime')),
            ciudad TEXT NOT NULL,
            temp REAL NOT NULL,
            status TEXT NOT NULL,
            FOREIGN KEY (ciudad) REFERENCES ciudades(nombre) ON DELETE CASCADE
        )
    """)
    
    # 5. Índices para optimizar consultas
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_clima_pronostico_ciudad ON clima_pronostico (ciudad);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_historial_fecha ON historial_consultas (fecha_consulta DESC);")
    
    # 6. Vista simplificada para análisis agrícola rápido
    cursor.execute("""
        CREATE VIEW IF NOT EXISTS vista_resumen_agricola AS
        SELECT 
            ca.ciudad,
            ca.temp,
            ca.humidity,
            ca.precipitation,
            c.es_agricola,
            clasificar_clima(ca.temp, ca.humidity, c.es_agricola) AS status_sugerido,
            ca.fecha_guardado
        FROM clima_actual ca
        JOIN ciudades c ON ca.ciudad = c.nombre
    """)
    
    # 7. Trigger de Validación de Datos (Evita humedades erróneas de APIs o ingresos)
    cursor.execute("DROP TRIGGER IF EXISTS trg_validar_humedad")
    cursor.execute("""
        CREATE TRIGGER trg_validar_humedad
        BEFORE INSERT ON clima_actual
        FOR EACH ROW
        BEGIN
            SELECT
                CASE
                    WHEN NEW.humidity < 0 OR NEW.humidity > 100 THEN
                        RAISE(ABORT, 'Humedad fuera de rango físico: debe estar entre 0 y 100')
                END;
        END;
    """)
    
    # 8. Trigger de Auditoría Automático (AFTER INSERT / AFTER UPDATE en clima_actual)
    cursor.execute("DROP TRIGGER IF EXISTS trg_auditar_consulta")
    cursor.execute("""
        CREATE TRIGGER trg_auditar_consulta
        AFTER INSERT ON clima_actual
        FOR EACH ROW
        BEGIN
            INSERT INTO historial_consultas (ciudad, temp, status)
            VALUES (
                NEW.ciudad, 
                NEW.temp, 
                (SELECT status_sugerido FROM vista_resumen_agricola WHERE ciudad = NEW.ciudad)
            );
        END;
    """)
    
    conn.commit()
    conn.close()

def save_to_local(ciudad, data):
    """Guarda los datos del clima en SQLite de forma relacional y atómica."""
    conn = conectar_db()
    cursor = conn.cursor()
    
    try:
        # Iniciamos transacción explícita
        cursor.execute("BEGIN TRANSACTION;")
        
        # 1. Guardar Clima Actual (esto disparará el Trigger trg_auditar_consulta automáticamente!)
        current = data['current']
        
        # Primero validamos que la humedad esté dentro de rango en la inserción
        # Si viola la validación del trigger, lanzará sqlite3.IntegrityError
        cursor.execute("""
            INSERT OR REPLACE INTO clima_actual (ciudad, temp, humidity, precipitation, fecha_guardado)
            VALUES (?, ?, ?, ?, datetime('now', 'localtime'))
        """, (ciudad, current['temp'], current['humidity'], current['precipitation']))
        
        # 2. Borrar pronósticos anteriores de la ciudad
        cursor.execute("DELETE FROM clima_pronostico WHERE ciudad = ?", (ciudad,))
        
        # 3. Guardar Pronósticos Semanales (múltiples filas)
        pronosticos_tuples = [
            (
                ciudad,
                f['date'],
                f['temp_max'],
                f['temp_min'],
                f['precipitation'],
                f['humidity']
            )
            for f in data['forecast']
        ]
        
        cursor.executemany("""
            INSERT INTO clima_pronostico (ciudad, date, temp_max, temp_min, precipitation, humidity, fecha_guardado)
            VALUES (?, ?, ?, ?, ?, ?, datetime('now', 'localtime'))
        """, pronosticos_tuples)
        
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"Error al guardar clima local en SQLite: {e}")
        raise e
    finally:
        conn.close()

def load_from_local(ciudad):
    """Carga los datos del clima de SQLite de forma relacional."""
    conn = conectar_db()
    cursor = conn.cursor()
    
    try:
        # 1. Consultar Clima Actual
        cursor.execute("SELECT temp, humidity, precipitation FROM clima_actual WHERE ciudad = ?", (ciudad,))
        current_row = cursor.fetchone()
        if not current_row:
            return None
            
        current_data = {
            'temp': current_row[0],
            'humidity': current_row[1],
            'precipitation': current_row[2]
        }
        
        # 2. Consultar Pronóstico
        cursor.execute("""
            SELECT date, temp_max, temp_min, precipitation, humidity 
            FROM clima_pronostico 
            WHERE ciudad = ? 
            ORDER BY date ASC
        """, (ciudad,))
        forecast_rows = cursor.fetchall()
        
        forecast_data = []
        for r in forecast_rows:
            forecast_data.append({
                'date': r[0],
                'temp_max': r[1],
                'temp_min': r[2],
                'precipitation': r[3],
                'humidity': r[4]
            })
            
        return {
            'current': current_data,
            'forecast': forecast_data
        }
    except Exception as e:
        print(f"Error cargando de DB local: {e}")
        return None
    finally:
        conn.close()

def load_history(limit=5):
    """Carga el historial de consultas directamente desde SQLite."""
    conn = conectar_db()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT fecha_consulta, ciudad, temp, status 
            FROM historial_consultas 
            ORDER BY fecha_consulta DESC 
            LIMIT ?
        """, (limit,))
        rows = cursor.fetchall()
        history = []
        for r in rows:
            history.append({
                'fecha': r[0],
                'ciudad': r[1],
                'temp': r[2],
                'status': r[3]
            })
        return history
    except Exception as e:
        print(f"Error al cargar el historial de SQLite: {e}")
        return []
    finally:
        conn.close()
