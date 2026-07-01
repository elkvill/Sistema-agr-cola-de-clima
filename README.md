# Sistema Inteligente de Apoyo Agrícola - SIA Nicaragua

El Sistema Inteligente de Apoyo Agrícola (SIA) es una solución tecnológica avanzada diseñada para la gestión y soporte de decisiones en el sector agropecuario de Nicaragua. Este sistema integra el análisis de datos meteorológicos en tiempo real con capacidades de Inteligencia Artificial para ofrecer recomendaciones precisas sobre ciclos de siembra, gestión de riesgos y monitoreo climático.

## Descripción del Proyecto

El SIA Nicaragua ha sido desarrollado como una herramienta modular que permite a los productores y técnicos agrícolas visualizar el estado actual y futuro del clima en diversos municipios del país. La plataforma no solo muestra datos crudos, sino que los procesa a través de un motor de lógica agronómica para determinar si las condiciones son favorables para cultivos específicos, como granos básicos (maíz y frijol).

El proyecto está diseñado bajo estrictos principios de diseño **SOLID** y una **Arquitectura Hexagonal**, lo que garantiza su mantenibilidad, extensibilidad y testabilidad.

## Estructura de Directorios

```text
ProyectoExamenSismos/
├── dominio/                     # Núcleo de la aplicación (Hexágono)
│   ├── entidades.py             # Modelos de negocio (MedicionActual, AnalisisLocal, etc.)
│   ├── puertos.py               # Interfaces abstractas/puertos (ServicioClima, RepositorioClima, etc.)
│   ├── estadisticas.py          # Cálculo de métricas climáticas (promedio, tendencia)
│   ├── excepciones.py           # Excepciones personalizadas de dominio
│   ├── analizador_condiciones.py# Analizador de condiciones climáticas (OCP via Evaluadores)
│   ├── generador_recomendacion.py# Generador de recomendaciones agrícolas (Strategy Pattern)
│   ├── clasificador_pronostico.py# Clasificador de riesgo diario (Strategy Pattern)
│   └── consultar_y_analizar_clima.py   # Lógica de negocio/Caso de uso (ObtenerClimaYAnalizar)
├── adaptadores/
│   ├── primarios/
│   │   ├── interfaz_streamlit.py # UI principal (coordinador del layout)
│   │   ├── componente_graficos.py# Componente para gráficos y calendario de riesgo
│   │   ├── componente_chat.py    # Componente para el chat con IA
│   │   ├── componente_reportes.py# Componente para exportar reportes en PDF
│   │   └── utils_ui.py           # Inyección de CSS y VerificadorConectividadSocket
│   └── secundarios/
│       ├── api/
│       │   ├── openweather_adaptador.py  # Conexión con OpenWeatherMap API
│       │   └── groq_adaptador.py         # Integración con IA Groq (Llama 3)
│       └── persistencia/
│           ├── mapeadores.py             # Mappers (traducción BD <-> dominio)
│           ├── migrador_sqlite.py        # Migrador e inicializador del esquema físico (SRP)
│           └── adaptadores_sqlite.py     # Adaptador SQLite enfocado solo en CRUD (SRP)
├── ensamblaje/
│   └── contenedor.py           # Composition Root (Inyección de dependencias)
├── configuracion/
│   └── ajustes.py              # Ajustes generales (API keys, ciudades, UMBRALES centrales)
├── app.py                      # Entry point delgado (< 10 líneas)
├── estilos/                    # Hojas de estilo CSS
│   └── estilos.css
└── data_backup.db              # Base de datos física de SQLite
```

## Arquitectura del Sistema - Hexagonal (Puertos y Adaptadores)

El proyecto sigue la **Arquitectura Hexagonal** (también llamada de Puertos y Adaptadores) propuesta por Alistair Cockburn, que aísla la lógica de negocio de la infraestructura exterior para que pueda evolucionar sin acoplamiento tecnológico.

### Diagrama de la Arquitectura y Flujos (Normal vs Fallback)

```mermaid
graph TD
    %% Estilos de Nodos
    classDef domain fill:#c8e6c9,stroke:#388e3c,stroke-width:2px;
    classDef port fill:#bbdefb,stroke:#1976d2,stroke-width:2px;
    classDef infra fill:#ffe0b2,stroke:#f57c00,stroke-width:2px;

    subgraph Capa_Adaptadores_Primarios["Adaptadores Primarios (UI y Utils)"]
        UI["interfaz_streamlit.py (Interfaz Principal)"]:::infra
        COMP_GRAF["componente_graficos.py (Gráficos/Calendario)"]:::infra
        COMP_CHAT["componente_chat.py (Chat UI)"]:::infra
        COMP_REP["componente_reportes.py (Exportación PDF)"]:::infra
        CONN_SOCK["VerificadorConectividadSocket"]:::infra
    end

    subgraph Hexagono_Dominio["Dominio (Núcleo)"]
        PUERTO_PRIMARIO["ConsultarClima (Puerto)"]:::port
        UC["ObtenerClimaYAnalizar (Caso de Uso)"]:::domain
        ENTIDADES["Entidades de Dominio (MedicionActual, AnalisisLocal, etc.)"]:::domain
        
        P_COND["AnalizadorCondicionesPort"]:::port
        P_REC["GeneradorRecomendacionPort"]:::port
        P_CLAS["ClasificadorPronosticoPort"]:::port
        P_CONN["VerificadorConectividad (Puerto)"]:::port
    end

    subgraph Puertos_Secundarios["Puertos Secundarios"]
        P_CLIMA["ServicioClima (Puerto)"]:::port
        P_REC_IA["ServicioRecomendacionIA (Puerto)"]:::port
        P_CHAT_IA["ServicioChatIA (Puerto)"]:::port
        P_REPO["RepositorioClima (Puerto)"]:::port
    end

    subgraph Capa_Adaptadores_Secundarios["Adaptadores Secundarios (Infraestructura)"]
        API_CLIMA["OpenWeatherAdapter"]:::infra
        API_IA["GroqAdapter (IA)"]:::infra
        SQLITE_CRUD["AdaptadorSqlite (CRUD)"]:::infra
        SQLITE_MIG["MigradorSqlite (Esquema/Migración)"]:::infra
    end

    %% Relaciones de Dependencia y Flujo
    UI -->|Usa| COMP_GRAF
    UI -->|Usa| COMP_CHAT
    UI -->|Usa| COMP_REP
    UI -->|Llama| PUERTO_PRIMARIO
    PUERTO_PRIMARIO -->|Implementado por| UC
    UC -.->|Usa| ENTIDADES
    
    UC -->|Usa| P_COND
    UC -->|Usa| P_REC
    UC -->|Usa| P_CLAS

    UC -->|Consulta| P_CLIMA
    UC -->|Consulta| P_REC_IA
    UC -->|Persiste / Carga| P_REPO

    UI -->|Usa| P_CONN

    P_CLIMA -->|Implementado por| API_CLIMA
    API_IA -->|Implementa| P_REC_IA
    API_IA -->|Implementa| P_CHAT_IA
    P_REPO -->|Implementado por| SQLITE_CRUD
    P_CONN -->|Implementado por| CONN_SOCK

    %% Subdiagrama de Flujos (Normal vs Fallback)
    subgraph Flujo_Normal_vs_Fallback["Flujo de Operación (Normal vs Fallback)"]
        A[Inicio Consulta Ciudad] --> B{¿Hay Internet?}
        
        %% Flujo Normal
        B -->|SÍ: Flujo Normal| C[Consultar Clima vía API]
        C --> D[Guardar datos en SQLite]
        D --> E[Obtener Recomendación IA vía Groq]
        E --> F[Guardar Análisis en SQLite]
        F --> G[Registrar Consulta en Historial]
        
        %% Flujo Fallback
        B -->|NO: Flujo Fallback| H[Cargar último clima desde SQLite]
        H --> I[Cargar última recomendación IA desde SQLite]
        I --> G
        
        G --> J[Mostrar en UI Streamlit]
    end

    %% Enlaces visuales
    API_CLIMA -.-> C
    SQLITE_CRUD -.-> D
    API_IA -.-> E
    SQLITE_CRUD -.-> F
    SQLITE_CRUD -.-> H
    SQLITE_CRUD -.-> I
    UI -.-> J
```

### Capas:

- **Dominio (el Hexágono)**: Contiene las entidades del negocio, los puertos (interfaces abstractas) y los casos de uso. Está completamente aislado de la infraestructura (no importa `requests`, `sqlite3` ni Streamlit).
  - `entidades.py`: `MedicionActual`, `PronosticoDia`, `DatosClima`, `AnalisisLocal`, `ResultadoConsulta`, `ConsultaHistorial`
  - `puertos.py`: Define los puertos abstractos (e.g., `ServicioClima`, `ServicioRecomendacionIA`, `ServicioChatIA`, `RepositorioClima`, `AnalizadorCondicionesPort`, `GeneradorRecomendacionPort`, `ClasificadorPronosticoPort`, `VerificadorConectividad`)
  - `consultar_y_analizar_clima.py`: `ObtenerClimaYAnalizar` - orquesta el flujo de negocio sin depender de librerías externas o clases concretas, cumpliendo con el **DIP** al inyectarle todos sus sub-procesadores de dominio.
  - `analizador_condiciones.py`: Implementa la evaluación de alertas climáticas mediante evaluadores configurables (`EvaluadorCondicion`) que heredan de una base común para cumplir con **OCP**.
  - `generador_recomendacion.py`: Selecciona la estrategia adecuada (`EstrategiaRecomendacion`) basándose en el tipo de suelo y alertas.
  - `clasificador_pronostico.py`: Clasifica el riesgo del pronóstico diario delegando en estrategias (`EstrategiaClasificacion`) cumpliendo con **OCP**.

- **Adaptadores Secundarios (Infraestructura de salida)**: Implementan los puertos con tecnologías concretas.
  - `openweather_adaptador.py`: Conexión REST con la API de OpenWeatherMap.
  - `groq_adaptador.py`: Implementa `ServicioRecomendacionIA` y `ServicioChatIA` para conectarse con la API de Groq (Llama 3), cumpliendo con el **ISP**.
  - `migrador_sqlite.py`: Clase dedicada únicamente a inicializar la base de datos y correr migraciones (SRP).
  - `adaptadores_sqlite.py` + `mapeadores.py`: Repositorio SQLite que expone exclusivamente operaciones CRUD (SRP).

- **Adaptadores Primarios (Infraestructura de entrada)**: Interfaz de usuario o desencadenadores externos.
  - `interfaz_streamlit.py` + componentes gráficos, chat y reportes: Diseñado bajo el principio **SRP** para separar las tareas de visualización en archivos específicos.

- **Composition Root (`ensamblaje/contenedor.py`)**: El único lugar del código donde se configuran e instancian las implementaciones de los adaptadores, evaluadores y estrategias concretas y se inyectan a los casos de uso.

## Base de Datos SQLite

La base de datos relacional está optimizada en español para garantizar normalización, consistencia de datos y rendimiento, aplicando principios SOLID y de base de datos relacional.

### Estructura del Esquema (6 Tablas + Control de Versiones):

| Tabla | Propósito | Características Clave |
|-------|-----------|-----------------------|
| `_migrations` | Control de versiones de base de datos. | Registra la versión y la fecha de aplicación del esquema. |
| `ciudades` | Catálogo de municipios con coordenadas. | Clave primaria en `nombre`, CHECK para el booleano `es_agricola`. |
| `clima_actual` | Último clima medido por ciudad (relación 1:1 con ciudad). | `ciudad` UNIQUE, CHECK de rangos de temperatura (-50 a 60°C), humedad (0 a 100%), precipitación (>= 0), formato de fecha ISO 8601. |
| `analisis_clima` | Análisis generado (combinación de análisis local e IA). | Relación 1:1 con `clima_actual` mediante `clima_actual_id UNIQUE` con `ON DELETE CASCADE`. CHECK para estado (`URBAN`, `NORMAL`, `FAVORABLE`, `RIESGOSO`). |
| `clima_pronostico` | Pronóstico de 5 a 7 días por ciudad (relación 1:N). | Clave única combinada `UNIQUE(ciudad, fecha)`, CHECK de formatos e integridad referencial a ciudades. |
| `historial_consultas` | Registro histórico de consultas del usuario. | Poblado directamente desde la capa de aplicación/caso de uso para mantener las reglas de negocio en el dominio y evitar triggers complejos. |
| `log_auditoria` | Auditoría de eventos del sistema (log). | CHECK en operación (`INSERT`, `UPDATE`, `DELETE`), campos de `usuario` y `direccion_ip`. Se alimenta con el trigger `trg_log_analisis` al guardar nuevos análisis. |

### Características Técnicas de la Base de Datos:
1. **Integridad Referencial Estricta**: Activación explícita y verificación de `PRAGMA foreign_keys = ON;` en cada conexión.
2. **Restricciones CHECK**: Todo control de rango (temperatura, humedad, formatos ISO de fecha, estados válidos) se valida a nivel físico mediante CHECKs en SQLite.
3. **Triggers Desacoplados**: Se eliminaron los triggers que contenían lógica de negocio (`trg_validar_humedad` y `trg_auditar_consulta`), moviéndola al dominio. Se mantiene el trigger técnico `trg_log_analisis` para poblar el log de auditoría.
4. **Estrategia de Purga**: Limpieza automática al guardar nuevos climas para evitar el crecimiento descontrolado de la base de datos (se mantienen 10 días de pronóstico, 90 días de historial de consultas y 365 días de logs).
5. **Transacciones Atómicas**: Uso de `BEGIN TRANSACTION` / `COMMIT` / `ROLLBACK` para asegurar la atomicidad de las escrituras complejas.
6. **Migrador Aislado**: Las migraciones y actualizaciones del esquema físico son manejadas de forma exclusiva por [migrador_sqlite.py](file:///c:/clases/Administración de sistemas informaticos/ManualSQlite/ProyectoExamenSismos/adaptadores/secundarios/persistencia/migrador_sqlite.py) (SRP).

## Instrucciones de Instalación y Uso

1. Instalar dependencias requeridas (Streamlit, Pandas, Plotly, fpdf2).
2. Ejecutar la aplicación:
   ```bash
   streamlit run app.py
   ```
3. Seleccione una ciudad del panel lateral y presione **Analizar Clima**.
4. Use el botón **Historial de Consultas** para ver la auditoría de búsquedas anteriores.
5. Use el **Chat Experto** en el panel inferior para interactuar con la IA en modo online.
