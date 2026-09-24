"""Exporta los notebooks a HTML con sus salidas ya ejecutadas.

El destino es `docs/notebooks_html/`, para anexarlos al informe sin que el lector tenga
que instalar nada ni ejecutar código. Los HTML son autocontenidos: las figuras van
incrustadas en base64.

Se ejecutan de nuevo antes de exportar, en vez de reutilizar salidas guardadas, para
que lo que se anexa corresponda al estado actual de `data/processed/`.
"""

import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import RAIZ  # noqa: E402

ORIGEN = RAIZ / "notebooks"
DESTINO = RAIZ / "docs" / "notebooks_html"

NOTEBOOKS = ("00_preparacion", "01_caracterizacion", "02_topicos", "03_evaluacion")

# nbconvert enlaza MathJax y require.js desde un CDN. Estos notebooks no tienen
# fórmulas ni widgets, así que el enlace solo impide leerlos sin internet.
GUIONES_EXTERNOS = re.compile(
    r"<script[^>]+src=\"https?://cdnjs\.cloudflare\.com/[^\"]+\"[^>]*>\s*</script>",
    re.IGNORECASE,
)


def hacer_autocontenido(ruta: Path) -> int:
    """Quita los enlaces a CDN y devuelve cuántos quitó."""
    html = ruta.read_text(encoding="utf-8")
    limpio, cuantos = GUIONES_EXTERNOS.subn("", html)
    if cuantos:
        ruta.write_text(limpio, encoding="utf-8")
    return cuantos


def exportar(nombre: str) -> Path:
    salida = DESTINO / f"{nombre}.html"
    orden = [
        sys.executable, "-m", "jupyter", "nbconvert",
        "--to", "html",
        "--execute",
        "--embed-images",
        "--ExecutePreprocessor.timeout=600",
        "--output-dir", str(DESTINO),
        "--output", f"{nombre}.html",
        str(ORIGEN / f"{nombre}.ipynb"),
    ]
    resultado = subprocess.run(orden, capture_output=True, text=True)
    if resultado.returncode != 0:
        raise RuntimeError(f"{nombre}: {resultado.stderr[-800:]}")
    return salida


def main() -> None:
    DESTINO.mkdir(parents=True, exist_ok=True)
    for nombre in NOTEBOOKS:
        ruta = exportar(nombre)
        quitados = hacer_autocontenido(ruta)
        print(f"  {ruta.name:<26} {ruta.stat().st_size / 1024:>7.0f} KB"
              f"  ({quitados} enlaces a CDN eliminados)")


if __name__ == "__main__":
    main()
