"""Construye `data/processed/fragmentos.csv` y reporta las cifras de cada etapa."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd  # noqa: E402

from src.config import DATOS_PROCESADOS, DIMENSIONES, DIMENSIONES_APTAS_ES  # noqa: E402
from src.preparacion import (  # noqa: E402
    cargar_resenas,
    patron_nombres_completos,
    construir_fragmentos,
    contar_descartes_por_largo,
    eliminar_duplicados,
    nombres_establecimientos,
)

SALIDA = DATOS_PROCESADOS / "fragmentos.csv"

COLUMNAS_SALIDA = [
    "fragmento_id", "review_id", "place_id", "establecimiento", "zona", "rating",
    "fragmento_num", "n_fragmentos_resena", "texto", "texto_limpio",
    "largo_caracteres", "largo_palabras", "tiene_local",
    *DIMENSIONES, "n_dim",
]


def percentiles(serie: pd.Series) -> str:
    q = serie.quantile([0.25, 0.5, 0.75, 0.90])
    return (
        f"min {serie.min()}, p25 {q[0.25]:.0f}, mediana {q[0.5]:.0f}, "
        f"p75 {q[0.75]:.0f}, p90 {q[0.90]:.0f}, max {serie.max()}, media {serie.mean():.1f}"
    )


def main() -> None:
    resenas = cargar_resenas()
    print(f"Reseñas aptas en español            {len(resenas):>6}")

    resenas, eliminadas = eliminar_duplicados(resenas)
    print(f"Duplicados reales eliminados        {len(eliminadas):>6}")
    for fila in eliminadas.itertuples(index=False):
        print(f"    {fila.review_id}  autor_n={fila.autor_n_resenas}  {fila.texto[:60]!r}")
    print(f"Reseñas de trabajo                  {len(resenas):>6}")

    nombres = nombres_establecimientos()
    patron_completos = patron_nombres_completos(nombres)
    print(f"\nNombres de establecimiento          {len(nombres):>6}")

    descartes = contar_descartes_por_largo(resenas, patron_completos)
    print(f"\nCláusulas antes del largo mínimo    {descartes['clausulas_totales']:>6}")
    print(f"  descartadas por < 10 caracteres   {descartes['descartadas_por_largo']:>6}")

    fragmentos = construir_fragmentos(resenas)
    print(f"Fragmentos finales                  {len(fragmentos):>6}")

    afectados = int(fragmentos["tiene_local"].sum())
    resenas_marcadas = int((fragmentos.groupby("review_id")["marcas_local_resena"].first() > 0).sum())
    print(f"\nFragmentos con [LOCAL]              {afectados:>6}  ({100*afectados/len(fragmentos):.1f}%)")
    print(f"Reseñas con al menos un enmascarado {resenas_marcadas:>6}  ({100*resenas_marcadas/len(resenas):.1f}%)")

    por_resena = fragmentos.groupby("review_id").size()
    print(f"\nReseñas representadas               {por_resena.size:>6}")
    print(f"Fragmentos por reseña: {percentiles(por_resena)}")
    print(f"Longitud en caracteres: {percentiles(fragmentos['largo_caracteres'])}")
    print(f"Longitud en palabras:   {percentiles(fragmentos['largo_palabras'])}")
    vacios = int((fragmentos['texto_limpio'].str.len() == 0).sum())
    print(f"texto_limpio vacío tras stopwords:  {vacios} ({100*vacios/len(fragmentos):.1f}%)")

    aptas = pd.read_csv(DIMENSIONES_APTAS_ES)
    aptas = aptas[aptas["review_id"].isin(fragmentos["review_id"])]
    print("\n--- Prevalencia: fragmento contra reseña ---")
    print(f"{'dimension':<12}{'frag':>7}{'% frag':>9}{'resenas hered.':>16}{'% res':>8}"
          f"{'resenas recalc.':>17}{'% res':>8}")
    for dimension in DIMENSIONES:
        n_frag = int(fragmentos[dimension].sum())
        heredada = int(aptas[dimension].sum())
        recalc = int(fragmentos.groupby("review_id")[dimension].any().sum())
        print(
            f"{dimension:<12}{n_frag:>7}{100*n_frag/len(fragmentos):>8.1f}%"
            f"{heredada:>16}{100*heredada/len(aptas):>7.1f}%"
            f"{recalc:>17}{100*recalc/len(aptas):>7.1f}%"
        )

    print("\n--- Dimensiones por fragmento ---")
    reparto = fragmentos["n_dim"].value_counts().sort_index()
    for n_dim, cuenta in reparto.items():
        print(f"  n_dim = {n_dim}: {cuenta:>5}  ({100*cuenta/len(fragmentos):.1f}%)")
    cero = int((fragmentos["n_dim"] == 0).sum())
    una = int((fragmentos["n_dim"] == 1).sum())
    dos_o_mas = int((fragmentos["n_dim"] >= 2).sum())
    print(f"\n  0 dimensiones     {cero:>5}  ({100*cero/len(fragmentos):.1f}%)")
    print(f"  1 dimensión       {una:>5}  ({100*una/len(fragmentos):.1f}%)  <- disponible para AMI")
    print(f"  2 o más           {dos_o_mas:>5}  ({100*dos_o_mas/len(fragmentos):.1f}%)")

    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    fragmentos[COLUMNAS_SALIDA].to_csv(SALIDA, index=False)
    print(f"\nGuardado en {SALIDA}  ({len(fragmentos)} filas, {len(COLUMNAS_SALIDA)} columnas)")


if __name__ == "__main__":
    main()
