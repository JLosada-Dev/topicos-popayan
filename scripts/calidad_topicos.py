"""Coherencia y diversidad del modelo congelado."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd  # noqa: E402

from src.calidad import coherencia, diversidad  # noqa: E402
from src.config import DATOS_PROCESADOS  # noqa: E402
from src.topicos import cargar_modelo_guardado  # noqa: E402


def main() -> None:
    fragmentos = pd.read_csv(DATOS_PROCESADOS / "fragmentos.csv").merge(
        pd.read_csv(DATOS_PROCESADOS / "fragmentos_topicos.csv"),
        on=["fragmento_id", "review_id"],
    )
    etiquetas = pd.read_csv(DATOS_PROCESADOS / "topicos_etiquetados.csv").set_index("topico_id")
    modelo = cargar_modelo_guardado()

    resultado = coherencia(modelo, fragmentos)
    print(f"tópicos evaluados: {resultado['n_topicos_evaluados']}")
    print(f"c_v    = {resultado['c_v']}")
    print(f"c_npmi = {resultado['c_npmi']}")
    for n in (5, 10, 20):
        print(f"diversidad top-{n} = {diversidad(modelo, fragmentos, n)}")

    por_topico = pd.Series(resultado["c_v_por_topico"]).sort_values()
    etiquetas["c_v"] = por_topico
    etiquetas["subtema"] = etiquetas["subtema"].fillna("")

    def linea(topico, valor):
        fila = etiquetas.loc[topico]
        nombre = f"{fila['tema']}" + (f" / {fila['subtema']}" if fila["subtema"] else "")
        return f"  T{topico:<3} c_v={valor:.3f}  {nombre:<36} n={fila['n']}"

    print("\n6 tópicos menos coherentes:")
    for topico, valor in por_topico.head(6).items():
        print(linea(topico, valor))
    print("\n6 tópicos más coherentes:")
    for topico, valor in por_topico.tail(6).items():
        print(linea(topico, valor))

    print("\nc_v por tipo:")
    print(etiquetas.groupby("tipo")["c_v"].agg(["mean", "min", "max", "size"]).round(3).to_string())
    etiquetas.reset_index().to_csv(DATOS_PROCESADOS / "topicos_etiquetados.csv", index=False)


if __name__ == "__main__":
    main()
