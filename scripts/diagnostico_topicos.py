"""Primera corrida diagnóstica de BERTopic. Guarda asignaciones y resumen."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd  # noqa: E402

from src.config import DATOS_PROCESADOS  # noqa: E402
from src.embeddings import obtener  # noqa: E402
from src.topicos import (  # noqa: E402
    ATIPICO,
    MIN_TOPIC_SIZE,
    ajustar,
    representativos,
    resumen_topicos,
)

FRAGMENTOS = DATOS_PROCESADOS / "fragmentos.csv"
SALIDA_ASIGNACIONES = DATOS_PROCESADOS / "fragmentos_topicos.csv"
SALIDA_RESUMEN = DATOS_PROCESADOS / "topicos_resumen.csv"
SALIDA_EJEMPLOS = DATOS_PROCESADOS / "topicos_ejemplos.csv"


def main() -> None:
    fragmentos = pd.read_csv(FRAGMENTOS)
    embeddings, info = obtener(fragmentos)
    print(f"fragmentos {len(fragmentos)} | embeddings {embeddings.shape} | {info['origen']}")

    modelo, asignaciones = ajustar(fragmentos, embeddings, MIN_TOPIC_SIZE)
    fragmentos["topico"] = asignaciones

    n_topicos = int((fragmentos["topico"] != ATIPICO).sum() and fragmentos["topico"].max() + 1)
    atipicos = int((fragmentos["topico"] == ATIPICO).sum())
    print(f"\nmin_topic_size = {MIN_TOPIC_SIZE}")
    print(f"tópicos encontrados: {n_topicos}")
    print(f"sin asignar (-1):    {atipicos}  ({100 * atipicos / len(fragmentos):.1f}%)")

    resumen = resumen_topicos(modelo, fragmentos)
    print("\n=== TAMAÑO Y TERMINOS ===")
    with pd.option_context("display.width", 200, "display.max_colwidth", 88):
        print(resumen[["topico", "n", "porcentaje", "terminos"]].to_string(index=False))

    print("\n=== TONO, LOCAL Y LONGITUD ===")
    with pd.option_context("display.width", 200, "display.max_colwidth", 30):
        print(
            resumen[[
                "topico", "n", "rating_medio", "pct_1_2_estrellas", "largo_mediano",
                "n_locales", "pct_local_top", "local_top", "dimension_dominante",
            ]].to_string(index=False)
        )

    print("\n=== FRAGMENTOS REPRESENTATIVOS (10 tópicos más grandes) ===")
    filas_ejemplo = []
    mayores = resumen[resumen["topico"] != ATIPICO].nlargest(10, "n")
    for fila in mayores.itertuples(index=False):
        print(f"\n--- Tópico {fila.topico}  (n={fila.n}, rating {fila.rating_medio}) ---")
        print(f"    {fila.terminos}")
        for ejemplo in representativos(modelo, fragmentos, fila.topico, 3):
            print(f"  · {ejemplo[:160]}")
            filas_ejemplo.append({"topico": fila.topico, "ejemplo": ejemplo})

    fragmentos[["fragmento_id", "review_id", "topico"]].to_csv(SALIDA_ASIGNACIONES, index=False)
    resumen.to_csv(SALIDA_RESUMEN, index=False)
    pd.DataFrame(filas_ejemplo).to_csv(SALIDA_EJEMPLOS, index=False)
    print(f"\nGuardado: {SALIDA_ASIGNACIONES.name}, {SALIDA_RESUMEN.name}, {SALIDA_EJEMPLOS.name}")


if __name__ == "__main__":
    main()
