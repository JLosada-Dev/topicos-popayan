"""Sensibilidad al tamaño mínimo de tópico.

No toca el modelo congelado. Corre la misma configuración con `min_cluster_size` más
bajo para comprobar si los temas negativos de baja masa forman tópico propio cuando el
umbral se lo permite. Sirve para sustentar que su ausencia en el modelo principal es un
efecto del umbral y no del corpus.

Un tema «forma tópico propio» si existe un tópico donde al menos el 25 % de sus
fragmentos pertenecen al tema y que concentra al menos el 20 % del tema. Las dos
condiciones son necesarias: la primera evita contar un tópico grande que apenas lo roza,
la segunda evita contar un tópico minúsculo que casualmente es puro.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd  # noqa: E402

from src.config import DATOS_PROCESADOS  # noqa: E402
from src.embeddings import MODELO_EMBEDDINGS, obtener  # noqa: E402
from src.experimentos import metricas  # noqa: E402
from src.texto import plegar  # noqa: E402
from src.topicos import (  # noqa: E402
    ATIPICO,
    MIN_SAMPLES,
    MIN_TOPIC_SIZE,
    UMBRAL_REDUCCION,
    actualizar_representacion,
    ajustar,
    reducir_atipicos,
)

from scripts.temas_baja_masa import REGLAS  # noqa: E402

PUREZA_MINIMA = 0.25
CONCENTRACION_MINIMA = 0.20
TEMAS_VIGILADOS = ("inocuidad", "honestidad en el cobro", "horarios e informacion digital")


def corrida(fragmentos, embeddings, min_cluster_size, min_samples):
    modelo, asignaciones = ajustar(fragmentos, embeddings, min_cluster_size, min_samples)
    copia = fragmentos.copy()
    copia["topico"] = asignaciones
    copia["topico"] = reducir_atipicos(modelo, copia, embeddings, UMBRAL_REDUCCION)
    actualizar_representacion(modelo, copia)
    return modelo, copia


def revisar_tema(asignado, marca, modelo):
    """Si el tema forma tópico propio, cuál y con qué pureza y concentración."""
    sub = asignado[marca & (asignado["topico"] != ATIPICO)]
    if sub.empty:
        return None
    candidatos = []
    for topico, cuantos in sub["topico"].value_counts().items():
        tamano = int((asignado["topico"] == topico).sum())
        pureza = cuantos / tamano
        concentracion = cuantos / int(marca.sum())
        if pureza >= PUREZA_MINIMA and concentracion >= CONCENTRACION_MINIMA:
            terminos = [t for t, _ in (modelo.get_topic(topico) or [])][:7]
            candidatos.append((topico, tamano, cuantos, pureza, concentracion, terminos))
    return max(candidatos, key=lambda c: c[3]) if candidatos else None


def main() -> None:
    fragmentos = pd.read_csv(DATOS_PROCESADOS / "fragmentos.csv")
    embeddings, _ = obtener(fragmentos, MODELO_EMBEDDINGS)
    plegado = fragmentos["texto"].map(plegar)
    marcas = {
        tema: plegado.str.contains(REGLAS[tema], regex=True, na=False)
        for tema in TEMAS_VIGILADOS
    }
    print("tamaño de cada tema (regla de piso): " + ", ".join(
        f"{t}={int(m.sum())}" for t, m in marcas.items()
    ))

    configuraciones = [(MIN_TOPIC_SIZE, MIN_SAMPLES), (20, 10), (15, 7)]
    for min_cluster_size, min_samples in configuraciones:
        modelo, asignado = corrida(fragmentos, embeddings, min_cluster_size, min_samples)
        m = metricas(modelo, asignado, embeddings, f"mcs={min_cluster_size}")
        marca_principal = " (CONGELADA)" if min_cluster_size == MIN_TOPIC_SIZE else ""
        print(f"\n{'=' * 78}")
        print(f"min_cluster_size={min_cluster_size}  min_samples={min_samples}{marca_principal}")
        print(f"{'=' * 78}")
        print(f"  tópicos={m['n_topicos']}  atípicos={m['pct_atipicos']}%  "
              f"mayor={m['pct_topico_mayor']}% (r={m['rating_topico_mayor']})  "
              f"c_v pendiente  duplicados={m['n_topicos_duplicados']}")
        for tema, marca in marcas.items():
            hallazgo = revisar_tema(asignado, marca, modelo)
            if hallazgo is None:
                sub = asignado[marca]
                mayor = sub[sub["topico"] != ATIPICO]["topico"].value_counts()
                detalle = (f"mayor concentración {100 * mayor.iloc[0] / int(marca.sum()):.0f} % en T{mayor.index[0]}"
                           if len(mayor) else "sin asignar")
                print(f"  {tema:<32} NO  ({detalle})")
                continue
            topico, tamano, cuantos, pureza, concentracion, terminos = hallazgo
            print(f"  {tema:<32} SÍ  T{topico} (n={tamano}): "
                  f"pureza {100 * pureza:.0f} %, concentra {100 * concentracion:.0f} % del tema")
            print(f"  {'':<32}     {', '.join(terminos)}")


if __name__ == "__main__":
    main()
