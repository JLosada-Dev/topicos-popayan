"""Figuras del informe.

Todas se exportan en PNG y PDF a 300 dpi y deben ser legibles en escala de grises,
porque el informe se imprime. De ahí tres reglas que se aplican en todas:

- La identidad nunca depende del tono. Las series se separan por **luminosidad** —
  pasos distantes de una sola rampa azul— y, cuando comparten eje, además por trama.
- Toda magnitud lleva etiqueta directa, de modo que el valor se lee sin recurrir al
  color ni a la escala.
- Rejilla y ejes recesivos: la tinta se gasta en los datos.
"""

from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt

from src.config import FIGURAS

DPI = 300
FORMATOS = ("png", "pdf")

# La paleta vive en `src/paleta.py`, que no importa matplotlib, para que el dashboard
# pueda compartirla sin arrastrar esta dependencia
from src.paleta import (  # noqa: E402
    PASOS_CATEGORIA,
    RAMPA,
    REJILLA,
    SUPERFICIE,
    TINTA,
    TINTA_SECUNDARIA,
    TINTA_TENUE,
    TRAMAS,
)


def preparar() -> None:
    """Estilo común. Tipografía de tamaño de informe, no de pantalla."""
    mpl.rcParams.update({
        "figure.facecolor": SUPERFICIE,
        "axes.facecolor": SUPERFICIE,
        "savefig.facecolor": SUPERFICIE,
        "font.family": "sans-serif",
        "font.sans-serif": ["Helvetica Neue", "Helvetica", "Arial", "DejaVu Sans"],
        "font.size": 9,
        "axes.titlesize": 11,
        "axes.titleweight": "bold",
        "axes.labelsize": 9,
        "axes.edgecolor": REJILLA,
        "axes.labelcolor": TINTA_SECUNDARIA,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "xtick.color": TINTA_SECUNDARIA,
        "ytick.color": TINTA_SECUNDARIA,
        "xtick.labelsize": 8,
        "ytick.labelsize": 8,
        "grid.color": REJILLA,
        "grid.linewidth": 0.6,
        "legend.frameon": False,
        "legend.fontsize": 8,
        "figure.constrained_layout.use": True,
    })


def guardar(figura, nombre: str, carpeta: Path = FIGURAS) -> list[Path]:
    """Exporta la figura en todos los formatos y devuelve las rutas."""
    carpeta.mkdir(parents=True, exist_ok=True)
    rutas = []
    for formato in FORMATOS:
        ruta = carpeta / f"{nombre}.{formato}"
        figura.savefig(ruta, dpi=DPI, format=formato, bbox_inches="tight")
        rutas.append(ruta)
    plt.close(figura)
    return rutas


def titular(eje, titulo: str, subtitulo: str = "") -> None:
    """Título y, debajo, una línea que dice qué hay que leer en la figura."""
    eje.set_title(titulo, loc="left", color=TINTA, pad=18 if subtitulo else 8)
    if subtitulo:
        eje.text(
            0, 1.02, subtitulo, transform=eje.transAxes, fontsize=8,
            color=TINTA_SECUNDARIA, va="bottom",
        )
