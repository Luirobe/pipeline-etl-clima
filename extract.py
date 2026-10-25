"""
extract.py - Paso 1 del pipeline ETL: extraer datos de una API pública.

API usada: Open-Meteo (clima). No requiere API key.
Docs: https://open-meteo.com/en/docs

Uso:
    python extract.py
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

import requests

# --- Configuración -----------------------------------------------------------
API_URL = "https://api.open-meteo.com/v1/forecast"

# Hermosillo, Sonora. Cambia las coordenadas para otra ciudad.
CIUDAD = "Hermosillo"
LATITUD = 29.0729
LONGITUD = -110.9559

TIMEOUT_SEGUNDOS = 15
CARPETA_RAW = Path("data/raw")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


# --- Funciones ---------------------------------------------------------------
def extraer_clima() -> dict:
    """Llama a la API y regresa la respuesta como diccionario."""
    params = {
        "latitude": LATITUD,
        "longitude": LONGITUD,
        "hourly": "temperature_2m,relative_humidity_2m,wind_speed_10m",
        "timezone": "America/Hermosillo",
        "forecast_days": 3,
    }

    logger.info("Consultando Open-Meteo para %s...", CIUDAD)

    try:
        respuesta = requests.get(API_URL, params=params, timeout=TIMEOUT_SEGUNDOS)
        respuesta.raise_for_status()  # lanza error si el status no es 2xx
    except requests.exceptions.Timeout:
        logger.error("La API tardó más de %s segundos.", TIMEOUT_SEGUNDOS)
        raise
    except requests.exceptions.HTTPError as e:
        logger.error("Error HTTP de la API: %s", e)
        raise
    except requests.exceptions.RequestException as e:
        logger.error("Error de conexión: %s", e)
        raise

    datos = respuesta.json()
    logger.info("Datos recibidos correctamente.")
    return datos


def guardar_raw(datos: dict) -> Path:
    """Guarda el JSON crudo con marca de tiempo (útil para auditar y depurar)."""
    CARPETA_RAW.mkdir(parents=True, exist_ok=True)
    marca = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    ruta = CARPETA_RAW / f"clima_{CIUDAD.lower()}_{marca}.json"

    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=2)

    logger.info("JSON crudo guardado en %s", ruta)
    return ruta


def main() -> None:
    datos = extraer_clima()
    guardar_raw(datos)

    # Vistazo rápido para verificar que todo llegó bien
    horario = datos["hourly"]
    print("\nPrimeras 5 lecturas:")
    for i in range(5):
        print(
            f"  {horario['time'][i]} | "
            f"{horario['temperature_2m'][i]} °C | "
            f"{horario['relative_humidity_2m'][i]} % | "
            f"{horario['wind_speed_10m'][i]} km/h"
        )


if __name__ == "__main__":
    main()
