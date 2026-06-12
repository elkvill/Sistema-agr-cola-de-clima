# Sistema Inteligente de Apoyo Agricola - SIA Nicaragua

El Sistema Inteligente de Apoyo Agricola (SIA) es una solucion tecnologica avanzada diseñada para la gestion y soporte de decisiones en el sector agropecuario de Nicaragua. Este sistema integra analisis de datos meteorologicos en tiempo real con capacidades de Inteligencia Artificial para ofrecer recomendaciones precisas sobre ciclos de siembra, gestion de riesgos y monitoreo climatico.

## Descripcion del Proyecto

El SIA Nicaragua ha sido desarrollado como una herramienta modular que permite a los productores y tecnicos agricolas visualizar el estado actual y futuro del clima en diversos municipios del pais. La plataforma no solo muestra datos crudos, sino que los procesa a traves de un motor de logica agronomica para determinar si las condiciones son favorables para cultivos especificos, como granos basicos (maiz y frijol).

## Estructura de Directorios

```text
ProyectoExamenSismos/
├── dominio/                     # Nucleo de la aplicacion (Hexagono)
│   ├── entidades.py             # Modelos del negocio (MedicionClima, AnalisisLocal, etc.)
│   ├── puertos.py               # Interfaces abstractas (ServicioClima, RepositorioClima, ServicioIA)
│   └── casos_de_uso.py          # Logica de negocio orquestada (ObtenerClimaYAnalizar)
├── adaptadores/
│   ├── primarios/
│   │   └── streamlit_ui.py      # Interfaz de usuario (Streamlit) - punto de entrada
│   └── secundarios/
│       ├── api/
│       │   ├── openmeteo_adapter.py    # API Open-Meteo (gratuita, sin llave)
│       │   ├── openweather_adapter.py  # API OpenWeatherMap
│       │   └── groq_adapter.py         # IA Groq (Llama 3.1) para recomendaciones
│       └── persistencia/
│           └── sqlite_repositorio.py   # SQLite con triggers, vistas, UDFs, transacciones
├── ensamblaje/
│   └── contenedor.py           # Composition Root (unico lugar que crea instancias)
├── config/
│   └── settings.py             # Configuracion (API keys, umbrales, ciudades)
├── app.py                      # Entry point delgado (< 10 lineas)
├── styles/                     # Estilos visuales CSS
├── Arquitectura Hexagonal/     # PDF de referencia + ejercicios
│   ├── Arquitecctura hexagonal.pdf
│   └── ejercicios/             # 5 ejercicios resueltos
└── data/                       # Datos locales
    └── data_backup.db          # Base de datos SQLite
```

## Arquitectura del Sistema - Hexagonal (Puertos y Adaptadores)

El proyecto sigue la **Arquitectura Hexagonal** (tambien llamada de Puertos y Adaptadores) propuesta por Alistair Cockburn, que aísla la logica de negocio del mundo exterior para que pueda evolucionar sin romperse ante cambios tecnologicos.

### Capas:

- **Dominio (el Hexagono)**: Contiene las entidades del negocio, los puertos (interfaces abstractas) y los casos de uso. No importa nada de infraestructura (ni `requests`, ni `sqlite3`, ni Streamlit). Solo lenguaje de negocio puro.
  - `entidades.py`: `MedicionActual`, `PronosticoDia`, `DatosClima`, `AnalisisLocal`, `ResultadoConsulta`
  - `puertos.py`: `ServicioClima`, `ServicioIA`, `RepositorioClima`, `ConsultarClima` (todos ABC)
  - `casos_de_uso.py`: `ObtenerClimaYAnalizar` - orquesta: obtener clima → guardar → analizar → recomendar

- **Adaptadores Secundarios (lado derecho)**: Implementan los puertos con tecnologias concretas.
  - `openmeteo_adapter.py` / `openweather_adapter.py`: Conectan con APIs meteorologicas.
  - `groq_adapter.py`: Conecta con Groq API (modelo `llama-3.1-8b-instant`) para recomendaciones IA.
  - `sqlite_repositorio.py`: Persistencia en SQLite con 7 tablas, indices, vistas, triggers, UDFs y transacciones.

- **Adaptadores Primarios (lado izquierdo)**: Puntos de entrada que el usuario usa.
  - `streamlit_ui.py`: Interfaz grafica con Streamlit. Depende del puerto `ConsultarClima`, nunca de la implementacion concreta.

- **Composition Root (`ensamblaje/contenedor.py`)**: Unico lugar donde se crean instancias concretas y se conectan adaptadores a casos de uso. Cambiar de Open-Meteo a OpenWeather o de SQLite a MongoDB implica modificar solo este archivo.

### Principio de Inversion de Dependencias (DIP):
Las dependencias apuntan hacia adentro: el dominio define puertos (interfaces) y los adaptadores los implementan. Ningun archivo del dominio importa nada de infraestructura.

### Flujo completo:
1. Usuario selecciona ciudad en Streamlit y hace clic en "Analizar Clima"
2. `StreamlitUI` llama al caso de uso `ObtenerClimaYAnalizar` a traves del puerto `ConsultarClima`
3. El caso de uso intenta `ServicioClima.obtener_actual(lat, lon)` (Open-Meteo u OpenWeather)
4. Si funciona: guarda en SQLite via `RepositorioClima.guardar_clima()`
5. Si falla: carga desde SQLite via `RepositorioClima.cargar_clima()` (modo offline)
6. Ejecuta analisis local (condiciones, umbrales, clasificacion de dias)
7. Si hay internet: obtiene recomendacion IA via `ServicioIA.generar_recomendacion()` (Groq)
8. Si no hay internet: carga la ultima recomendacion guardada en SQLite
9. Guarda todo el analisis en SQLite y devuelve `ResultadoConsulta` a la UI

## Base de Datos SQLite

El sistema utiliza **SQLite** como motor de persistencia con las siguientes caracteristicas:

### 7 Tablas:
| Tabla | Descripcion |
|-------|-------------|
| `ciudades` | Catalogo de 17 departamentos con coordenadas y tipo (agricola/urbano) |
| `clima_actual` | Clima actual de cada ciudad (1 registro por ciudad) |
| `clima_pronostico` | Pronostico de 5-7 dias por ciudad (1 registro por dia) |
| `historial_consultas` | Auditoria automatica de cada consulta realizada |
| `recomendaciones_ia` | Recomendaciones generadas por Groq IA |
| `analisis_clima` | Analisis local + recomendacion IA combinados |
| `log_auditoria` | Registro de eventos de auditoria |

### Temas del Manual SQLite aplicados:
- **Primary Keys y Foreign Keys** con `ON DELETE CASCADE`
- **Indices**: `idx_clima_pronostico_ciudad`, `idx_historial_fecha`
- **Vistas**: `vista_resumen_agricola`, `vista_estadisticas_clima`
- **Triggers**: `trg_validar_humedad` (BEFORE INSERT), `trg_auditar_consulta` (AFTER INSERT), `trg_log_analisis` (AFTER INSERT)
- **UDFs**: `clasificar_clima(temp, humidity, es_agricola)`, `celsius_a_fahrenheit(celsius)`
- **Transacciones**: `BEGIN TRANSACTION / COMMIT / ROLLBACK` en operaciones atomicas
- **NULLIF**: Para evitar division por cero en calculos de porcentajes
- **GROUP BY + CASE**: Para clasificacion de dias favorables
- **PRAGMA**: `PRAGMA foreign_keys = ON`

## Funcionalidades Detalladas

### 1. Analisis Climatico Predictivo
El sistema evalua variables criticas para el sector agricola:
- **Temperatura**: Monitoreo de estres termico (umbral > 35 grados Celsius).
- **Precipitacion**: Deteccion de riesgos de inundacion o erosion (> 15mm).
- **Humedad Relativa**: Analisis de riesgos fitosanitarios (hongos o plagas) en rangos extremos (< 40% o > 90%).

### 2. Integracion con IA - Groq
El modulo de IA utiliza **Groq API** con el modelo `llama-3.1-8b-instant` para:
- Generar recomendaciones agricolas personalizadas basadas en datos climaticos actuales.
- Chat interactivo para resolver dudas especificas de cultivo.
- Funcionamiento offline: las recomendaciones se guardan en SQLite y se recuperan cuando no hay internet.

### 3. Visualizacion de Datos
- **Tendencias**: Dashboard con metricas de temperatura promedio, lluvia total y tendencia semanal.
- **Calendario de Riesgo**: Clasifica los 7 dias del pronostico en Favorable / Normal / Riesgoso.
- **Historial de Consultas**: Acceso a las ultimas 5 consultas realizadas.

<<<<<<< HEAD
### 4. Persistencia con SQLite Profesional
El sistema cuenta con un motor de persistencia relacional basado en **SQLite**, estructurado según las mejores prácticas (triggers, vistas, índices, UDFs y transacciones):
- **Esquema Relacional**: Se implementan tablas estructuradas para `ciudades`, `clima_actual`, `clima_pronostico` y `historial_consultas` con integridad referencial activa (`PRAGMA foreign_keys = ON;`) y eliminación en cascada.
- **Auditoría Automatizada**: Mediante el trigger `trg_auditar_consulta` en la tabla `clima_actual`, el historial se registra de forma 100% autónoma en la base de datos sin depender de archivos planos JSON externos.
- **Caché Inteligente y Resiliencia**: El sistema está optimizado para funcionar sin internet de manera transparente. Si hay conexión, actualiza SQLite usando `INSERT OR REPLACE`; si no la hay, entra en modo fallback y carga el último estado disponible localmente.
- **Lógica en Base de Datos**: Se implementa una vista consolidada `vista_resumen_agricola` y funciones de Python registradas en el motor SQLite (UDFs) como `clasificar_clima` y `celsius_a_fahrenheit` para realizar operaciones complejas directamente en consultas SQL.

## Configuracion de Seguridad y APIs

Para mantener la integridad del sistema en entornos publicos (como GitHub), se han implementado las siguientes medidas:
- **Archivo api_keys.txt**: Un respaldo local que contiene las llaves de acceso reales.
- **Exclusion via .gitignore**: Archivos sensibles como historicos de datos y llaves de acceso estan excluidos del repositorio.
- **Placeholders**: En `config/settings.py`, las llaves estan reemplazadas por etiquetas descriptivas para evitar fugas de informacion.
=======
### 4. Modo Offline Transparente
El sistema detecta automaticamente si hay conexion a internet:
- **Online**: Descarga datos actuales de la API y genera recomendacion IA via Groq.
- **Offline**: Carga los ultimos datos guardados en SQLite y recupera la ultima recomendacion IA almacenada.
>>>>>>> 3eda9ca (Arquitectura Hexagonal)

## Instrucciones de Instalacion

1. Asegurese de tener instalado Python 3.10 o superior.
2. Clone este repositorio en su maquina local.
3. Las claves de API ya estan configuradas en `config/settings.py` para ejecucion inmediata.
4. Ejecute el comando:
   ```bash
   streamlit run app.py
   ```

## Municipios Soportados
El sistema cuenta con coordenadas preconfiguradas para los 15 departamentos y las 2 regiones autonomas de Nicaragua, incluyendo logica especifica para diferenciar zonas predominantemente urbanas (como Managua) de zonas con alto potencial agricola.

---
Proyecto desarrollado para el area de Administracion de Sistemas Informaticos - SIA Nicaragua.
