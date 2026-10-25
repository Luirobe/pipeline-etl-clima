# Pipeline ETL de clima con Python y PostgreSQL

Pipeline de datos que extrae el pronóstico del clima por hora desde una API pública, lo limpia con pandas y lo carga en una base de datos PostgreSQL. Se puede ejecutar de forma automática cada cierto tiempo con el Programador de tareas de Windows (o `cron` en Linux/Mac).

## Flujo del pipeline

```
Open-Meteo API  →  Extract  →  Transform  →  Load  →  PostgreSQL
                   (JSON)      (pandas/CSV)   (SQLAlchemy)
```

| Etapa | Archivo | Qué hace |
|-------|---------|----------|
| Extract | `extract.py` | Consulta la API de Open-Meteo y guarda la respuesta cruda en `data/raw/` |
| Transform | `transform.py` | Convierte el JSON en tabla, renombra columnas, ajusta tipos, elimina duplicados y nulos, y guarda un CSV en `data/processed/` |
| Load | `load.py` | Crea la tabla en PostgreSQL y carga los datos con *upsert* (no se duplican al correrlo varias veces) |
| Orquestación | `main.py` | Ejecuta las tres etapas en orden, con logging y manejo de errores |

## Tecnologías

- Python 3
- requests, pandas, SQLAlchemy, psycopg2
- PostgreSQL 16 (en Docker)
- Open-Meteo API (gratuita, sin API key)
- Programador de tareas de Windows / cron para la automatización

## Estructura del proyecto

```
.
├── extract.py
├── transform.py
├── load.py
├── main.py
├── ejecutar_pipeline.bat      # lo usa el Programador de tareas (Windows)
├── docker-compose.yml         # base de datos PostgreSQL
├── requirements.txt
└── README.md
```

Las carpetas `data/` y `logs/` se generan al ejecutar el pipeline.

## Cómo ejecutarlo

**1. Clonar e instalar dependencias**
```bash
git clone <URL-DEL-REPOSITORIO>
cd <NOMBRE-DE-LA-CARPETA>
pip install -r requirements.txt
```

**2. Levantar la base de datos** (requiere Docker Desktop abierto)
```bash
docker compose up -d
```

**3. Ejecutar el pipeline**
```bash
python main.py
```

También se puede correr cada etapa por separado: `python extract.py`, `python transform.py` y `python load.py`.

## Automatización

**Windows (Programador de tareas):**
```bash
schtasks /create /tn "PipelineClima" /tr "C:\ruta\al\proyecto\ejecutar_pipeline.bat" /sc hourly
```

**Linux / Mac (cron):**
```
0 * * * * cd /ruta/al/proyecto && python3 main.py >> logs/cron.log 2>&1
```

## Consultas de ejemplo

```sql
-- Temperatura promedio, máxima y mínima por día
SELECT
    DATE(fecha_hora)          AS dia,
    ROUND(AVG(temperatura_c)::numeric, 1) AS temp_promedio,
    MAX(temperatura_c)        AS temp_maxima,
    MIN(temperatura_c)        AS temp_minima
FROM clima_horario
GROUP BY DATE(fecha_hora)
ORDER BY dia;

-- Las 5 horas con más viento
SELECT fecha_hora, viento_kmh
FROM clima_horario
ORDER BY viento_kmh DESC
LIMIT 5;
```

## Decisiones de diseño

- **Se guarda el JSON crudo** con marca de tiempo, para poder auditar y reprocesar sin volver a llamar a la API.
- **Carga idempotente:** la tabla tiene llave primaria `(ciudad, fecha_hora)` y se usa `ON CONFLICT DO UPDATE`, así que ejecutar el pipeline varias veces no genera duplicados.
- **Transacciones:** la carga se hace dentro de una transacción; si falla, no queda nada a medias.
- **Logging:** cada ejecución deja registro en `logs/pipeline.log`, incluyendo el detalle de cualquier error.

## Posibles mejoras

- Soportar varias ciudades en una sola ejecución
- Migrar la orquestación a Apache Airflow
- Mover las credenciales a variables de entorno (`.env`)
- Agregar pruebas unitarias para la etapa de transformación
- Crear un dashboard con los datos (Power BI, Metabase o Streamlit)

## Autor

Luis Roberto Padilla Navarrete
