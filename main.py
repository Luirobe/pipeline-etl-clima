"""
main.py - Orquestador del pipeline ETL de clima.

Ejecuta en orden: Extract -> Transform -> Load.
Los mensajes se muestran en pantalla y también se guardan en logs/pipeline.log

Uso:
    python main.py
"""

import logging
from pathlib import Path

# El logging se configura ANTES de importar los demás módulos, para que
# todos escriban en el mismo lugar (pantalla + archivo).
Path("logs").mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("logs/pipeline.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)

import extract  # noqa: E402
import load  # noqa: E402
import transform  # noqa: E402

logger = logging.getLogger("pipeline")


def ejecutar_pipeline() -> None:
    logger.info("===== INICIO DEL PIPELINE =====")

    # 1. EXTRACT: traer datos de la API y guardar el JSON crudo
    logger.info("Paso 1/3: Extract")
    datos = extract.extraer_clima()
    extract.guardar_raw(datos)

    # 2. TRANSFORM: limpiar y guardar el CSV
    logger.info("Paso 2/3: Transform")
    ruta_json = transform.encontrar_ultimo_json()
    datos_raw = transform.cargar_json(ruta_json)
    df = transform.a_dataframe(datos_raw)
    df = transform.limpiar(df)
    transform.guardar(df)

    # 3. LOAD: cargar a PostgreSQL
    logger.info("Paso 3/3: Load")
    df_limpio = load.leer_csv()
    load.cargar(df_limpio)

    logger.info("===== PIPELINE TERMINADO CON ÉXITO =====")


def main() -> None:
    try:
        ejecutar_pipeline()
    except Exception:
        # logger.exception guarda el error completo en el log
        logger.exception("El pipeline falló")
        raise SystemExit(1)  # código 1 = terminó con error


if __name__ == "__main__":
    main()