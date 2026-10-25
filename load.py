"""
load.py - Paso 3 del pipeline ETL: cargar los datos limpios a PostgreSQL.

Lee data/processed/clima_limpio.csv y lo inserta en la tabla clima_horario.
Si corres el script varias veces NO se duplican filas: si la hora ya existe
para esa ciudad, se actualiza en lugar de insertarla de nuevo.

Antes de correrlo:
    docker compose up -d
    pip install sqlalchemy psycopg2-binary pandas

Uso:
    python load.py
"""

import logging
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text

# --- Configuración -----------------------------------------------------------
RUTA_CSV = Path("data/processed/clima_limpio.csv")

# Formato: postgresql+psycopg2://usuario:contraseña@servidor:puerto/base_de_datos
# Estos valores coinciden con los de docker-compose.yml (solo para práctica local)
DB_URL = "postgresql+psycopg2://clima_user:clima_pass@localhost:5432/clima_db"

CREAR_TABLA = """
CREATE TABLE IF NOT EXISTS clima_horario (
    ciudad            VARCHAR(100) NOT NULL,
    fecha_hora        TIMESTAMP    NOT NULL,
    temperatura_c     REAL,
    humedad_pct       REAL,
    viento_kmh        REAL,
    fecha_extraccion  TIMESTAMPTZ,
    PRIMARY KEY (ciudad, fecha_hora)
);
"""

# ON CONFLICT: si ya existe esa ciudad+hora, actualiza los valores
INSERTAR = """
INSERT INTO clima_horario
    (ciudad, fecha_hora, temperatura_c, humedad_pct, viento_kmh, fecha_extraccion)
VALUES
    (:ciudad, :fecha_hora, :temperatura_c, :humedad_pct, :viento_kmh, :fecha_extraccion)
ON CONFLICT (ciudad, fecha_hora) DO UPDATE SET
    temperatura_c    = EXCLUDED.temperatura_c,
    humedad_pct      = EXCLUDED.humedad_pct,
    viento_kmh       = EXCLUDED.viento_kmh,
    fecha_extraccion = EXCLUDED.fecha_extraccion;
"""

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


# --- Funciones ---------------------------------------------------------------
def leer_csv() -> pd.DataFrame:
    """Lee el CSV limpio generado por transform.py."""
    if not RUTA_CSV.exists():
        raise FileNotFoundError(
            f"No existe {RUTA_CSV}. Corre primero: python transform.py"
        )
    df = pd.read_csv(RUTA_CSV, parse_dates=["fecha_hora", "fecha_extraccion"])
    logger.info("CSV leído: %d filas", len(df))
    return df


def cargar(df: pd.DataFrame) -> None:
    """Crea la tabla (si no existe) e inserta/actualiza las filas."""
    engine = create_engine(DB_URL)

    # engine.begin() abre una transacción: si algo falla, no se guarda nada a medias
    with engine.begin() as conexion:
        conexion.execute(text(CREAR_TABLA))
        conexion.execute(text(INSERTAR), df.to_dict("records"))

    logger.info("Carga completada: %d filas procesadas", len(df))


def verificar() -> None:
    """Consulta la tabla para comprobar que los datos llegaron."""
    engine = create_engine(DB_URL)

    total = pd.read_sql("SELECT COUNT(*) AS total FROM clima_horario", engine)
    print(f"\nFilas en la tabla clima_horario: {total['total'][0]}")

    muestra = pd.read_sql(
        "SELECT ciudad, fecha_hora, temperatura_c, humedad_pct, viento_kmh "
        "FROM clima_horario ORDER BY fecha_hora LIMIT 5",
        engine,
    )
    print("\nPrimeras 5 filas en la base de datos:")
    print(muestra)


def main() -> None:
    df = leer_csv()
    cargar(df)
    verificar()


if __name__ == "__main__":
    main()
