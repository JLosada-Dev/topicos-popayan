"""Arma `dataset/`, el paquete de datos que acompaña al informe.

Reúne en una sola carpeta los archivos que hacen falta para entender y reproducir el
estudio: las tres entradas heredadas y las dos salidas propias. Cada uno se copia con
su hash SHA-256, de modo que el lector pueda verificar que es el mismo archivo que se
usó y no una versión posterior.
"""

import hashlib
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd  # noqa: E402

from src.config import (  # noqa: E402
    CORPUS,
    DATOS_PROCESADOS,
    DICCIONARIO_DIMENSIONES,
    MARCO_MUESTRAL,
    RAIZ,
)

DESTINO = RAIZ / "dataset"

# archivo de destino -> (origen, unidad de analisis, procedencia)
ARCHIVOS = {
    "corpus_final.csv": (
        CORPUS, "una reseña",
        "Proyecto previo `reputacion-popayan`, captura de Google Maps vía Apify",
    ),
    "marco_muestral_final.csv": (
        MARCO_MUESTRAL, "un establecimiento",
        "Proyecto previo `reputacion-popayan`, marco muestral del estudio",
    ),
    "dimensiones.csv": (
        DICCIONARIO_DIMENSIONES, "un término del diccionario",
        "Proyecto previo `reputacion-popayan`, diccionario construido y validado allí",
    ),
    "fragmentos_topicos.csv": (
        DATOS_PROCESADOS / "fragmentos.csv", "un fragmento (cláusula)",
        "Producido por este proyecto con `scripts/construir_fragmentos.py`",
    ),
    "temas_consolidado.csv": (
        DATOS_PROCESADOS / "temas_consolidado.csv", "un tema",
        "Producido por este proyecto con `scripts/tabla_temas.py`",
    ),
}

# `fragmentos_topicos.csv` del dataset une el corpus de fragmentos con su topico
# asignado, que en data/processed/ viven separados
UNIR_TOPICOS = "fragmentos_topicos.csv"


def hash_sha256(ruta: Path) -> str:
    resumen = hashlib.sha256()
    with ruta.open("rb") as archivo:
        for bloque in iter(lambda: archivo.read(1 << 20), b""):
            resumen.update(bloque)
    return resumen.hexdigest()


def main() -> None:
    DESTINO.mkdir(parents=True, exist_ok=True)
    filas = []
    for nombre, (origen, unidad, procedencia) in ARCHIVOS.items():
        destino = DESTINO / nombre
        if nombre == UNIR_TOPICOS:
            unido = pd.read_csv(origen).merge(
                pd.read_csv(DATOS_PROCESADOS / "fragmentos_topicos.csv"),
                on=["fragmento_id", "review_id"],
            )
            unido.to_csv(destino, index=False)
        else:
            shutil.copyfile(origen, destino)

        tabla = pd.read_csv(destino)
        filas.append({
            "archivo": nombre,
            "unidad_de_analisis": unidad,
            "filas": len(tabla),
            "columnas": len(tabla.columns),
            "bytes": destino.stat().st_size,
            "sha256": hash_sha256(destino),
            "procedencia": procedencia,
        })
        print(f"  {nombre:<28} {len(tabla):>6} filas × {len(tabla.columns):>2}  "
              f"{hash_sha256(destino)[:12]}")

    manifiesto = pd.DataFrame(filas)
    manifiesto.to_csv(DESTINO / "manifiesto.csv", index=False)
    print(f"\n  manifiesto.csv con {len(manifiesto)} entradas")


if __name__ == "__main__":
    main()
