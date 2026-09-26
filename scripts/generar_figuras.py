"""Genera las cuatro figuras del informe en PNG y PDF a 300 dpi."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from src.config import DATOS_PROCESADOS, DIMENSIONES  # noqa: E402
from src.figuras import (  # noqa: E402
    PASOS_CATEGORIA,
    RAMPA,
    REJILLA,
    TINTA,
    TINTA_SECUNDARIA,
    TINTA_TENUE,
    TRAMAS,
    guardar,
    preparar,
    titular,
)
from src.etiquetas import legible as bonito  # noqa: E402
from src.topicos import ATIPICO  # noqa: E402

NOMBRE_TIPO = {
    "atributo_esquema": "Atributo del esquema\na priori",
    "valoracion_global": "Valoración global\n(sin atributo)",
    "atributo_nuevo": "Atributo emergente",
}


def datos():
    fragmentos = pd.read_csv(DATOS_PROCESADOS / "fragmentos.csv").merge(
        pd.read_csv(DATOS_PROCESADOS / "fragmentos_topicos.csv"),
        on=["fragmento_id", "review_id"],
    )
    return (
        fragmentos,
        pd.read_csv(DATOS_PROCESADOS / "topicos_etiquetados.csv"),
        pd.read_csv(DATOS_PROCESADOS / "temas_consolidado.csv"),
    )


def figura_tipos(temas, asignados):
    """Parte-de-un-todo con tres clases: una sola barra apilada horizontal."""
    orden = ["atributo_esquema", "valoracion_global", "atributo_nuevo"]
    grupo = temas.groupby("tipo")["fragmentos"].sum().reindex(orden)

    figura, eje = plt.subplots(figsize=(7.2, 2.5))
    izquierda = 0
    for i, (tipo, valor) in enumerate(grupo.items()):
        porcentaje = 100 * valor / asignados
        eje.barh(
            0, porcentaje, left=izquierda, height=0.42,
            color=PASOS_CATEGORIA[i], hatch=TRAMAS[i], edgecolor="#fcfcfb", linewidth=2,
        )
        centro = izquierda + porcentaje / 2
        tinta = "#ffffff" if i == 0 else TINTA
        eje.text(centro, 0, f"{porcentaje:.1f} %", ha="center", va="center",
                 fontsize=11, fontweight="bold", color=tinta)
        eje.text(centro, -0.33, f"{NOMBRE_TIPO[tipo]}\n{valor:,} fragmentos".replace(",", "."),
                 ha="center", va="top", fontsize=8, color=TINTA_SECUNDARIA)
        izquierda += porcentaje

    eje.set_xlim(0, 100)
    eje.set_ylim(-1.15, 0.45)
    eje.axis("off")
    titular(eje, "Un quinto del corpus asignado no describe ningún atributo",
            f"Fragmentos por tipo de tema · n = {asignados:,} fragmentos asignados".replace(",", "."))
    return guardar(figura, "01_distribucion_por_tipo")


def figura_rating(temas, fragmentos):
    """Magnitud ordenada con una referencia: puntos, tamaño proporcional a n."""
    tabla = temas.sort_values("rating")
    media = fragmentos["rating"].mean()

    figura, eje = plt.subplots(figsize=(7.6, 5.2))
    posicion = np.arange(len(tabla))
    eje.axvline(media, color=TINTA_TENUE, linewidth=1.2, linestyle=(0, (4, 3)), zorder=1)
    eje.text(media, len(tabla) - 0.35, f"  media del corpus {media:.2f}",
             fontsize=8, color=TINTA_SECUNDARIA, va="center")

    for y, fila in zip(posicion, tabla.itertuples(index=False)):
        eje.plot([media, fila.rating], [y, y], color=REJILLA, linewidth=1.4, zorder=2)
    tamanos = 28 + 340 * (tabla["fragmentos"] / tabla["fragmentos"].max())
    colores = [PASOS_CATEGORIA[["atributo_esquema", "valoracion_global",
                                "atributo_nuevo"].index(t)] for t in tabla["tipo"]]
    eje.scatter(tabla["rating"], posicion, s=tamanos, c=colores,
                edgecolor="#fcfcfb", linewidth=1.5, zorder=3)

    # El desplazamiento crece con el radio del punto: si no, la etiqueta del tema
    # mayor queda encima de su propia marca
    radios = 0.045 + 0.055 * np.sqrt(tamanos / tamanos.max())
    for y, fila, radio in zip(posicion, tabla.itertuples(index=False), radios):
        hacia_derecha = fila.rating >= media
        signo = 1 if hacia_derecha else -1
        eje.text(fila.rating + signo * radio, y, f"{fila.rating:.2f}  (n={fila.fragmentos})",
                 va="center", ha="left" if hacia_derecha else "right",
                 fontsize=7.5, color=TINTA_SECUNDARIA)

    eje.set_yticks(posicion, [bonito(t) for t in tabla["tema"]], fontsize=8.5)
    eje.set_xlim(1.4, 5.35)
    eje.set_xlabel("Calificación media de la reseña de origen (estrellas)")
    eje.grid(axis="x", zorder=0)
    eje.set_axisbelow(True)
    eje.spines["left"].set_visible(False)
    eje.tick_params(axis="y", length=0)

    manijas = [plt.Line2D([], [], marker="o", linestyle="", markersize=7,
                          markerfacecolor=PASOS_CATEGORIA[i], markeredgecolor="#fcfcfb",
                          label=NOMBRE_TIPO[t].replace("\n", " "))
               for i, t in enumerate(["atributo_esquema", "valoracion_global", "atributo_nuevo"])]
    # Arriba a la izquierda es el único cuadrante libre: los temas altos están a la
    # derecha de la media y la barra de espera ocupa el inferior izquierdo
    eje.legend(handles=manijas, loc="upper left", labelcolor=TINTA_SECUNDARIA,
               bbox_to_anchor=(0.01, 0.99))
    titular(eje, "La espera es el único tema que cae por debajo de tres estrellas",
            "Área del punto proporcional al número de fragmentos")
    return guardar(figura, "02_temas_por_rating")


def figura_mapa_calor(fragmentos, etiquetas):
    """Magnitud en una rejilla: rampa secuencial de un solo tono."""
    asignados = fragmentos[fragmentos["topico"] != ATIPICO]
    mayores = asignados["topico"].value_counts().head(15).index
    nombres = etiquetas.set_index("topico_id")
    matriz, filas = [], []
    for topico in mayores:
        sub = asignados[asignados["topico"] == topico]
        matriz.append([100 * sub[d].mean() for d in DIMENSIONES])
        subtema = nombres.loc[topico, "subtema"]
        sufijo = f" / {bonito(subtema)}" if isinstance(subtema, str) and subtema else ""
        filas.append(f"T{topico}  {bonito(nombres.loc[topico, 'tema'])}{sufijo}  (n={len(sub)})")
    matriz = np.array(matriz)

    mapa = mpl_rampa()
    figura, eje = plt.subplots(figsize=(7.4, 6.0))
    imagen = eje.imshow(matriz, cmap=mapa, vmin=0, vmax=100, aspect="auto")
    eje.set_xticks(range(len(DIMENSIONES)), [d.capitalize() for d in DIMENSIONES])
    eje.set_yticks(range(len(filas)), filas, fontsize=8)
    eje.tick_params(length=0)
    for spine in eje.spines.values():
        spine.set_visible(False)
    eje.set_xticks(np.arange(-0.5, len(DIMENSIONES)), minor=True)
    eje.set_yticks(np.arange(-0.5, len(filas)), minor=True)
    eje.grid(which="minor", color="#fcfcfb", linewidth=2)
    eje.tick_params(which="minor", length=0)

    for i in range(matriz.shape[0]):
        for j in range(matriz.shape[1]):
            valor = matriz[i, j]
            eje.text(j, i, f"{valor:.0f}", ha="center", va="center", fontsize=7.5,
                     color="#ffffff" if valor >= 55 else TINTA)

    barra = figura.colorbar(imagen, ax=eje, fraction=0.03, pad=0.02)
    barra.set_label("% de los fragmentos del tópico que activan la dimensión", fontsize=8)
    barra.outline.set_visible(False)
    barra.ax.tick_params(length=0, labelsize=8)
    titular(eje, "Ninguna dimensión se concentra en un solo tópico",
            "Quince tópicos mayores · el valor de la celda es el porcentaje")
    return guardar(figura, "03_mapa_topico_dimension")


def mpl_rampa():
    from matplotlib.colors import LinearSegmentedColormap

    pasos = [RAMPA[p] for p in (100, 200, 300, 400, 500, 600, 700)]
    return LinearSegmentedColormap.from_list("azul_secuencial", ["#fcfcfb", *pasos])


def figura_embudo(fragmentos, asignados):
    """Dos paneles porque la unidad cambia: primero reseñas, después fragmentos."""
    resenas = [
        ("Reseñas del corpus heredado", 8451),
        ("Con texto y ≥ 50 caracteres", 2645),
        ("En español", 2432),
        ("Sin duplicado real", 2430),
    ]
    trozos = [
        ("Fragmentos por cláusula", 5913),
        ("Asignados a un tópico", asignados),
    ]

    figura, ejes = plt.subplots(2, 1, figsize=(7.4, 4.6),
                                gridspec_kw={"height_ratios": [4, 2.2]})
    for eje, datos_panel, unidad, base in (
        (ejes[0], resenas, "reseñas", 8451),
        (ejes[1], trozos, "fragmentos", 5913),
    ):
        etiquetas = [e for e, _ in datos_panel]
        valores = [v for _, v in datos_panel]
        pasos = [RAMPA[p] for p in (650, 500, 400, 250)][: len(valores)]
        posicion = np.arange(len(valores))
        eje.barh(posicion, valores, height=0.58, color=pasos, edgecolor="#fcfcfb", linewidth=1.5)
        for y, valor in zip(posicion, valores):
            eje.text(valor + base * 0.012, y,
                     f"{valor:,}".replace(",", ".") + f"   ({100 * valor / base:.0f} %)",
                     va="center", fontsize=8.5, color=TINTA_SECUNDARIA)
        eje.set_yticks(posicion, etiquetas, fontsize=8.5)
        eje.invert_yaxis()
        eje.set_xlim(0, base * 1.28)
        eje.set_xticks([])
        eje.tick_params(axis="y", length=0)
        for lado in ("left", "bottom"):
            eje.spines[lado].set_visible(False)
        eje.text(1.0, 1.06, f"unidad: {unidad}", transform=eje.transAxes, ha="right",
                 fontsize=8, color=TINTA_TENUE, style="italic")

    titular(ejes[0], "Del corpus heredado al corpus de fragmentos asignados",
            "Los porcentajes son sobre la primera fila de cada panel")
    ejes[1].set_title("La segmentación cambia la unidad: 2.430 reseñas dan 5.913 fragmentos",
                      loc="left", fontsize=9, color=TINTA, pad=16)
    return guardar(figura, "04_embudo_corpus")


def main() -> None:
    preparar()
    fragmentos, etiquetas, temas = datos()
    asignados = int((fragmentos["topico"] != ATIPICO).sum())
    for rutas in (
        figura_tipos(temas, asignados),
        figura_rating(temas, fragmentos),
        figura_mapa_calor(fragmentos, etiquetas),
        figura_embudo(fragmentos, asignados),
    ):
        print("  " + ", ".join(r.name for r in rutas))


if __name__ == "__main__":
    main()
