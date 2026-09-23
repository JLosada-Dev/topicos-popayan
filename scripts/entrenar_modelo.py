"""Entrena y persiste el modelo definitivo con la configuración congelada."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd  # noqa: E402

from src.config import DATOS_PROCESADOS  # noqa: E402
from src.embeddings import MODELO_EMBEDDINGS, obtener  # noqa: E402
from src.experimentos import metricas  # noqa: E402
from src.topicos import (  # noqa: E402
    ATIPICO,
    MIN_SAMPLES,
    MIN_TOPIC_SIZE,
    UMBRAL_REDUCCION,
    ajustar_definitivo,
    guardar_modelo,
    resumen_topicos,
)

SALIDA_ASIGNACIONES = DATOS_PROCESADOS / "fragmentos_topicos.csv"
SALIDA_RESUMEN = DATOS_PROCESADOS / "topicos_resumen.csv"


def main() -> None:
    fragmentos = pd.read_csv(DATOS_PROCESADOS / "fragmentos.csv")
    embeddings, info = obtener(fragmentos, MODELO_EMBEDDINGS)
    print(f"embeddings: {info['modelo']} {embeddings.shape} ({info['origen']})")
    print(f"config: min_cluster_size={MIN_TOPIC_SIZE} min_samples={MIN_SAMPLES} "
          f"umbral_reduccion={UMBRAL_REDUCCION}")

    modelo, asignado = ajustar_definitivo(fragmentos, embeddings)
    m = metricas(modelo, asignado, embeddings, "definitivo")
    print(f"\ntópicos={m['n_topicos']}  atípicos={m['pct_atipicos']}%  "
          f"mayor={m['pct_topico_mayor']}%  eta2={m['eta2_rating']}  "
          f"duplicados={m['n_topicos_duplicados']}")

    asignado[["fragmento_id", "review_id", "topico", "topico_sin_reduccion"]].to_csv(
        SALIDA_ASIGNACIONES, index=False
    )
    resumen_topicos(modelo, asignado).to_csv(SALIDA_RESUMEN, index=False)
    guardar_modelo(modelo)
    print(f"\nmodelo guardado en {DATOS_PROCESADOS / 'modelo_bertopic'}")


if __name__ == "__main__":
    main()
