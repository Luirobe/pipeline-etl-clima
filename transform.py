"""
transform.py - Paso 2 del pipeline ETL: limpiar y transformar los datos.

Toma el JSON crudo más reciente de data/raw/, lo convierte en una tabla
(DataFrame de pandas), lo limpia y lo guarda en data/processed/.

Uso:
    pip install pandas
    python transform.py
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from extract import CIUDAD  # reutilizamos el nombre de la ciudad

# --- Configuración -----------------------------------------------------------
CARPETA_RAW = Path("data/raw")
CARPETA_PROCESSED = Path("data/processed")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


# --- Funciones ---------------------------------------------------------------
def encontrar_ultimo_json() -> Path:
    """Busca el archivo JSON más reciente en data/raw/."""
    archivos = sorted(CARPETA_RAW.glob("clima_*.json"))
    if not archivos:
        raise FileNotFoundError(
            "No hay archivos en data/raw/. Corre primero: python extract.py"
        )
    # Los nombres llevan fecha y hora, así que el último en orden es el más nuevo
    return archivos[-1]


def cargar_json(ruta: Path) -> dict:
    """Lee un archivo JSON y lo regresa como diccionario."""
    logger.info("Leyendo %s", ruta)
    with open(ruta, "r", encoding="utf-8") as f:
        return json.load(f)


def a_dataframe(datos: dict) -> pd.DataFrame:
    """Convierte la sección 'hourly' del JSON en una tabla con una fila por hora."""
    df = pd.DataFrame(datos["hourly"])
    logger.info("Tabla creada: %d filas, %d columnas", *df.shape)
    return df


def limpiar(df: pd.DataFrame) -> pd.DataFrame:
    """Renombra columnas, ajusta tipos, quita duplicados y nulos."""
    # 1. Nombres de columnas claros
    df = df.rename(
        columns={
            "time": "fecha_hora",
            "temperature_2m": "temperatura_c",
            "relative_humidity_2m": "humedad_pct",
            "wind_speed_10m": "viento_kmh",
        }
    )

    # 2. Tipos de datos correctos (el texto de fecha pasa a fecha real)
    df["fecha_hora"] = pd.to_datetime(df["fecha_hora"])

    # 3. Quitar duplicados y filas con datos faltantes
    antes = len(df)
    df = df.drop_duplicates(subset="fecha_hora")
    df = df.dropna()
    logger.info("Filas eliminadas por duplicados/nulos: %d", antes - len(df))

    # 4. Columnas nuevas
    df["ciudad"] = CIUDAD
    df["fecha_extraccion"] = datetime.now(timezone.utc)

    # 5. Ordenar por fecha y reiniciar el índice
    df = df.sort_values("fecha_hora").reset_index(drop=True)
    return df


def guardar(df: pd.DataFrame) -> Path:
    """Guarda la tabla limpia como CSV en data/processed/."""
    CARPETA_PROCESSED.mkdir(parents=True, exist_ok=True)
    ruta = CARPETA_PROCESSED / "clima_limpio.csv"
    df.to_csv(ruta, index=False)
    logger.info("Datos limpios guardados en %s", ruta)
    return ruta


def main() -> None:
    ruta_json = encontrar_ultimo_json()
    datos = cargar_json(ruta_json)
    df = a_dataframe(datos)
    df = limpiar(df)
    guardar(df)

    print("\nPrimeras 5 filas:")
    print(df.head())
    print("\nTipos de datos:")
    print(df.dtypes)


if __name__ == "__main__":
    main()
