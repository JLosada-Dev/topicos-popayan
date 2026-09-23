"""Persiste los resultados costosos para que los notebooks los lean.

La coherencia `c_v` tarda minutos y la rejilla de sensibilidad reajusta el modelo tres
veces. Ninguna de las dos puede correr dentro de un notebook que debe ejecutarse de
arriba abajo en un tiempo razonable, así que se calculan aquí una sola vez.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from src.calidad import coherencia, diversidad  # noqa: E402
from src.config import DATOS_PROCESADOS, SEMILLA  # noqa: E402
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
    cargar_modelo_guardado,
    reducir_atipicos,
)

from scripts.sensibilidad_umbral import (  # noqa: E402
    CONCENTRACION_MINIMA,
    PUREZA_MINIMA,
    TEMAS_VIGILADOS,
)
from scripts.temas_baja_masa import REGLAS  # noqa: E402

REPETICIONES_NULO = 200


def cargar():
    fragmentos = pd.read_csv(DATOS_PROCESADOS / "fragmentos.csv").merge(
        pd.read_csv(DATOS_PROCESADOS / "fragmentos_topicos.csv"),
        on=["fragmento_id", "review_id"],
    )
    return fragmentos, obtener(fragmentos, MODELO_EMBEDDINGS)[0]


def guardar_calidad(fragmentos):
    modelo = cargar_modelo_guardado()
    resultado = coherencia(modelo, fragmentos)
    filas = [
        {"indicador": "c_v", "valor": resultado["c_v"],
         "descripcion": "Coherencia c_v (Roder et al., 2015), media sobre los topicos"},
        {"indicador": "c_npmi", "valor": resultado["c_npmi"],
         "descripcion": "Coherencia NPMI, mas conservadora que c_v"},
        {"indicador": "diversidad_top10", "valor": diversidad(modelo, fragmentos, 10),
         "descripcion": "Proporcion de palabras unicas entre las 10 principales de cada topico"},
        {"indicador": "n_topicos", "valor": resultado["n_topicos_evaluados"],
         "descripcion": "Topicos evaluados"},
    ]
    pd.DataFrame(filas).to_csv(DATOS_PROCESADOS / "calidad_modelo.csv", index=False)
    return filas


def guardar_cohesion(fragmentos, embeddings):
    """Cohesión de cada grupo frente a grupos aleatorios del mismo tamaño."""
    normalizados = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)
    generador = np.random.default_rng(SEMILLA)

    def cohesion(indices):
        similitud = normalizados[indices] @ normalizados[indices].T
        return float(similitud[np.triu_indices_from(similitud, k=1)].mean())

    def nulo(n, repeticiones=REPETICIONES_NULO):
        return float(np.mean([
            cohesion(generador.choice(len(embeddings), n, replace=False))
            for _ in range(repeticiones)
        ]))

    plegado = fragmentos["texto"].map(plegar)
    etiquetas = pd.read_csv(DATOS_PROCESADOS / "topicos_etiquetados.csv").set_index("topico_id")
    filas = []
    for tema, patron in REGLAS.items():
        indices = np.where(plegado.str.contains(patron, regex=True, na=False))[0]
        if len(indices) < 3:
            continue
        valor = cohesion(indices)
        filas.append({"grupo": tema, "origen": "regla de recuperacion", "n": len(indices),
                      "cohesion": round(valor, 3), "nulo": round(nulo(len(indices)), 3)})
    for topico in (15, 40, 17, 0, 16):
        indices = np.where(fragmentos["topico"].to_numpy() == topico)[0]
        subtema = etiquetas.loc[topico, "subtema"]
        nombre = etiquetas.loc[topico, "tema"] + (
            f" / {subtema}" if isinstance(subtema, str) and subtema else ""
        )
        valor = cohesion(indices)
        filas.append({"grupo": f"T{topico} {nombre}", "origen": "topico del modelo",
                      "n": len(indices), "cohesion": round(valor, 3),
                      "nulo": round(nulo(len(indices)), 3)})
    tabla = pd.DataFrame(filas)
    tabla["exceso"] = (tabla["cohesion"] - tabla["nulo"]).round(3)
    tabla = tabla.sort_values("exceso", ascending=False)
    tabla.to_csv(DATOS_PROCESADOS / "cohesion_temas.csv", index=False)
    return tabla


def guardar_sensibilidad(fragmentos, embeddings):
    plegado = fragmentos["texto"].map(plegar)
    marcas = {t: plegado.str.contains(REGLAS[t], regex=True, na=False) for t in TEMAS_VIGILADOS}
    filas = []
    for min_cluster_size, min_samples in [(MIN_TOPIC_SIZE, MIN_SAMPLES), (20, 10), (15, 7)]:
        modelo, asignaciones = ajustar(fragmentos, embeddings, min_cluster_size, min_samples)
        copia = fragmentos.copy()
        copia["topico"] = asignaciones
        copia["topico"] = reducir_atipicos(modelo, copia, embeddings, UMBRAL_REDUCCION)
        actualizar_representacion(modelo, copia)
        m = metricas(modelo, copia, embeddings, f"{min_cluster_size}/{min_samples}")
        fila = {
            "min_cluster_size": min_cluster_size,
            "min_samples": min_samples,
            "congelada": min_cluster_size == MIN_TOPIC_SIZE,
            "n_topicos": m["n_topicos"],
            "pct_atipicos": m["pct_atipicos"],
            "pct_topico_mayor": m["pct_topico_mayor"],
        }
        for tema, marca in marcas.items():
            sub = copia[marca & (copia["topico"] != ATIPICO)]
            reparto = sub["topico"].value_counts()
            forma = False
            for topico, cuantos in reparto.items():
                tamano = int((copia["topico"] == topico).sum())
                if cuantos / tamano >= PUREZA_MINIMA and cuantos / int(marca.sum()) >= CONCENTRACION_MINIMA:
                    forma = True
                    break
            clave = tema.split()[0]
            fila[f"{clave}_forma_topico"] = forma
            fila[f"{clave}_max_concentracion"] = (
                round(100 * reparto.iloc[0] / int(marca.sum()), 1) if len(reparto) else 0.0
            )
        filas.append(fila)
    tabla = pd.DataFrame(filas)
    tabla.to_csv(DATOS_PROCESADOS / "sensibilidad_umbral.csv", index=False)
    return tabla


def main() -> None:
    fragmentos, embeddings = cargar()
    print("cohesión...")
    print(guardar_cohesion(fragmentos, embeddings).to_string(index=False))
    print("\nsensibilidad...")
    print(guardar_sensibilidad(fragmentos, embeddings).to_string(index=False))
    print("\ncoherencia (tarda unos minutos)...")
    for fila in guardar_calidad(fragmentos):
        print(f"  {fila['indicador']:<18} {fila['valor']}")


if __name__ == "__main__":
    main()
