"""Contraste entre los tópicos del modelo y las seis dimensiones a priori."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from src.config import DATOS_PROCESADOS, DIMENSIONES, SEMILLA  # noqa: E402
from src.etiquetas import ATRIBUTO_NUEVO  # noqa: E402
from src.topicos import ATIPICO  # noqa: E402

REPETICIONES_NULO = 200


def ami_nulo(topicos: np.ndarray, dimensiones: np.ndarray) -> tuple[float, float]:
    """Media y desviación del AMI con las etiquetas de dimensión permutadas."""
    from sklearn.metrics import adjusted_mutual_info_score

    generador = np.random.default_rng(SEMILLA)
    valores = [
        adjusted_mutual_info_score(topicos, generador.permutation(dimensiones))
        for _ in range(REPETICIONES_NULO)
    ]
    return float(np.mean(valores)), float(np.std(valores))


def main() -> None:
    from sklearn.metrics import adjusted_mutual_info_score, adjusted_rand_score

    fragmentos = pd.read_csv(DATOS_PROCESADOS / "fragmentos.csv").merge(
        pd.read_csv(DATOS_PROCESADOS / "fragmentos_topicos.csv"),
        on=["fragmento_id", "review_id"],
    )
    etiquetas = pd.read_csv(DATOS_PROCESADOS / "topicos_etiquetados.csv")
    tema = etiquetas.set_index("topico_id")["tema"]

    # --- Tabla cruzada -----------------------------------------------------------
    asignados = fragmentos[fragmentos["topico"] != ATIPICO]
    filas = []
    for topico in sorted(asignados["topico"].unique()):
        sub = asignados[asignados["topico"] == topico]
        fila = {"topico": topico, "tema": tema.get(topico, ""), "n": len(sub)}
        fila.update({d: round(100 * sub[d].mean(), 1) for d in DIMENSIONES})
        fila["sin_dim"] = round(100 * (sub["n_dim"] == 0).mean(), 1)
        filas.append(fila)
    cruzada = pd.DataFrame(filas)
    cruzada.to_csv(DATOS_PROCESADOS / "cruzada_topico_dimension.csv", index=False)
    print("=== TABLA CRUZADA: % de cada dimensión dentro de cada tópico ===")
    with pd.option_context("display.width", 200, "display.max_rows", 60):
        print(cruzada.to_string(index=False))

    # --- AMI ---------------------------------------------------------------------
    una = fragmentos[fragmentos["n_dim"] == 1].copy()
    una["dimension"] = una[list(DIMENSIONES)].idxmax(axis=1)
    con_topico = una[una["topico"] != ATIPICO]

    print(f"\n=== AMI: tópico contra dimensión ===")
    filas_ami = []
    for etiqueta, base in (
        ("solo fragmentos asignados", con_topico),
        ("incluyendo atípicos como una categoría más", una),
    ):
        ami = adjusted_mutual_info_score(base["topico"], base["dimension"])
        ari = adjusted_rand_score(base["topico"], base["dimension"])
        media, desviacion = ami_nulo(base["topico"].to_numpy(), base["dimension"].to_numpy())
        filas_ami.append({
            "base": etiqueta, "n": len(base), "ami": round(ami, 4), "ari": round(ari, 4),
            "nulo": round(media, 4), "sd_nulo": round(desviacion, 4),
            "exceso": round(ami - media, 4), "repeticiones": REPETICIONES_NULO,
        })
        print(f"\n  {etiqueta}  (n = {len(base)})")
        print(f"    AMI = {ami:.4f}   ARI = {ari:.4f}")
        print(f"    nulo por permutación ({REPETICIONES_NULO} repeticiones): "
              f"{media:.4f} ± {desviacion:.4f}")
        print(f"    exceso sobre el nulo: {ami - media:+.4f}")
    pd.DataFrame(filas_ami).to_csv(DATOS_PROCESADOS / "ami_resultados.csv", index=False)

    print(f"\n  cobertura: {len(una)} fragmentos tienen exactamente una dimensión "
          f"({100 * len(una) / len(fragmentos):.1f} % del corpus); "
          f"{len(con_topico)} de ellos están asignados a un tópico "
          f"({100 * len(con_topico) / len(una):.1f} %)")

    # --- Dispersión de cada dimensión --------------------------------------------
    print("\n=== En cuántos tópicos se reparte cada dimensión ===")
    filas_dispersion = []
    for dimension in DIMENSIONES:
        sub = asignados[asignados[dimension]]
        reparto = sub["topico"].value_counts()
        principal = int(reparto.index[0])
        filas_dispersion.append({
            "dimension": dimension, "fragmentos": len(sub), "topicos": len(reparto),
            "pct_en_el_mayor": round(100 * reparto.iloc[0] / len(sub), 1),
            "pct_en_los_3_mayores": round(100 * reparto.head(3).sum() / len(sub), 1),
            "topico_principal": principal, "tema_principal": tema.get(principal, ""),
        })
    dispersion = pd.DataFrame(filas_dispersion).sort_values("pct_en_el_mayor", ascending=False)
    dispersion.to_csv(DATOS_PROCESADOS / "dispersion_dimensiones.csv", index=False)
    print(dispersion.to_string(index=False))

    # --- Atributos nuevos sin dimensión ------------------------------------------
    nuevos = etiquetas.loc[etiquetas["tipo"] == ATRIBUTO_NUEVO, "topico_id"]
    sub = asignados[asignados["topico"].isin(nuevos)]
    print(f"\n=== Tópicos de tipo atributo_nuevo ===")
    print(f"  fragmentos: {len(sub)}")
    print(f"  con cero dimensiones del diccionario: {(sub['n_dim'] == 0).sum()} "
          f"({100 * (sub['n_dim'] == 0).mean():.1f} %)")
    print(f"  referencia, resto del corpus asignado: "
          f"{100 * (asignados[~asignados['topico'].isin(nuevos)]['n_dim'] == 0).mean():.1f} %")
    for topico in sorted(nuevos):
        s = sub[sub["topico"] == topico]
        print(f"    T{topico:<3} {tema.get(topico, ''):<26} sin dimensión "
              f"{100 * (s['n_dim'] == 0).mean():>5.1f} %  (n={len(s)})")


if __name__ == "__main__":
    main()
