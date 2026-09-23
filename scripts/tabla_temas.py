"""Tabla consolidada de temas para el informe: una fila por tema, no por tópico."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd  # noqa: E402

from src.config import DATOS_PROCESADOS  # noqa: E402
from src.topicos import ATIPICO  # noqa: E402

SALIDA = DATOS_PROCESADOS / "temas_consolidado.csv"


def polaridad_dominante(grupo: pd.DataFrame) -> str:
    """Polaridad de la mayoría de los fragmentos del tema; 'mixta' si ninguna manda."""
    peso = grupo.groupby("polaridad")["n"].sum()
    mayor = peso.idxmax()
    if peso[mayor] / peso.sum() < 0.6:
        return "mixta"
    return mayor


def main() -> None:
    etiquetas = pd.read_csv(DATOS_PROCESADOS / "topicos_etiquetados.csv")
    fragmentos = pd.read_csv(DATOS_PROCESADOS / "fragmentos.csv").merge(
        pd.read_csv(DATOS_PROCESADOS / "fragmentos_topicos.csv"),
        on=["fragmento_id", "review_id"],
    )
    asignados = int((fragmentos["topico"] != ATIPICO).sum())

    filas = []
    for tema, grupo in etiquetas.groupby("tema"):
        n = int(grupo["n"].sum())
        subtemas = sorted(s for s in grupo["subtema"].fillna("") if s)
        filas.append(
            {
                "tema": tema,
                "tipo": grupo["tipo"].iloc[0],
                "topicos": ", ".join(f"T{t}" for t in sorted(grupo["topico_id"])),
                "n_topicos": len(grupo),
                "fragmentos": n,
                "pct_asignado": round(100 * n / asignados, 1),
                "rating": round(float((grupo["rating"] * grupo["n"]).sum() / n), 2),
                "pct_1_2_estrellas": round(
                    float((grupo["pct_1_2_estrellas"] * grupo["n"]).sum() / n), 1
                ),
                "polaridad_dominante": polaridad_dominante(grupo),
                "subtemas": ", ".join(subtemas),
            }
        )

    tabla = pd.DataFrame(filas).sort_values("fragmentos", ascending=False)
    tabla.to_csv(SALIDA, index=False)

    atipicos = fragmentos[fragmentos["topico"] == ATIPICO]
    print(f"corpus asignado: {asignados} fragmentos "
          f"({100 * asignados / len(fragmentos):.1f} % de {len(fragmentos)})")
    print(f"atípicos: {len(atipicos)} (rating {atipicos['rating'].mean():.2f}, "
          f"{100 * (atipicos['rating'] <= 2).mean():.1f} % de 1-2★)\n")
    with pd.option_context("display.width", 240, "display.max_colwidth", 46):
        print(tabla.drop(columns="subtemas").to_string(index=False))
    print("\nSubtemas:")
    for fila in tabla[tabla["subtemas"] != ""].itertuples(index=False):
        print(f"  {fila.tema}: {fila.subtemas}")
    print(f"\nescrito {SALIDA}")


if __name__ == "__main__":
    main()
