"""Ejecuta los notebooks y deja sus salidas guardadas, en `.ipynb` y en HTML.

Dos destinos:

- Los propios `notebooks/*.ipynb` quedan **con sus salidas**, para que se puedan leer
  en GitHub o en Jupyter sin ejecutarlos.
- `docs/notebooks_html/` tiene la versión HTML autocontenida, para anexar al informe.

Se ejecuta **una sola vez** por notebook: primero se guardan las salidas en el `.ipynb`
y después el HTML se genera a partir de ese archivo ya ejecutado. Así los dos formatos
muestran exactamente las mismas cifras, que es lo que no garantizaba ejecutar dos veces.

Ojo: `scripts/generar_notebooks.py` reescribe los notebooks sin salidas. Si se cambia
el contenido hay que generar primero y ejecutar después, en ese orden.
"""

import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import RAIZ  # noqa: E402

ORIGEN = RAIZ / "notebooks"
DESTINO_HTML = RAIZ / "docs" / "notebooks_html"

NOTEBOOKS = ("00_preparacion", "01_caracterizacion", "02_topicos", "03_evaluacion")

TIEMPO_MAXIMO = 600

# nbconvert enlaza MathJax y require.js desde un CDN. Estos notebooks no tienen
# fórmulas ni widgets, así que el enlace solo impide leerlos sin internet.
GUIONES_EXTERNOS = re.compile(
    r'<script[^>]+src="https?://cdnjs\.cloudflare\.com/[^"]+"[^>]*>\s*</script>',
    re.IGNORECASE,
)


def _nbconvert(*argumentos: str) -> None:
    orden = [sys.executable, "-m", "jupyter", "nbconvert", *argumentos]
    resultado = subprocess.run(orden, capture_output=True, text=True)
    if resultado.returncode != 0:
        raise RuntimeError(resultado.stderr[-900:])


def ejecutar_en_sitio(nombre: str) -> Path:
    """Ejecuta el notebook y guarda sus salidas en el mismo archivo."""
    ruta = ORIGEN / f"{nombre}.ipynb"
    _nbconvert(
        "--to", "notebook", "--execute", "--inplace",
        f"--ExecutePreprocessor.timeout={TIEMPO_MAXIMO}",
        str(ruta),
    )
    return ruta


def exportar_html(nombre: str) -> Path:
    """HTML a partir del notebook ya ejecutado; no vuelve a ejecutarlo."""
    _nbconvert(
        "--to", "html", "--embed-images",
        "--output-dir", str(DESTINO_HTML),
        "--output", f"{nombre}.html",
        str(ORIGEN / f"{nombre}.ipynb"),
    )
    return DESTINO_HTML / f"{nombre}.html"


def limpiar_stderr(ruta: Path) -> int:
    """Quita las salidas de stderr, que son ruido del entorno y no resultados.

    Son avisos de tqdm, del hub de modelos y barras de progreso; además delatan la
    ruta local de quien ejecutó el notebook. Los errores reales no se tocan: van como
    `output_type: "error"`, y de todas formas harían fallar la ejecución antes.
    """
    cuaderno = json.loads(ruta.read_text(encoding="utf-8"))
    quitadas = 0
    for celda in cuaderno["cells"]:
        salidas = celda.get("outputs")
        if not salidas:
            continue
        limpias = [s for s in salidas if s.get("name") != "stderr"]
        quitadas += len(salidas) - len(limpias)
        celda["outputs"] = limpias
    if quitadas:
        ruta.write_text(json.dumps(cuaderno, ensure_ascii=False, indent=1), encoding="utf-8")
    return quitadas


def hacer_autocontenido(ruta: Path) -> int:
    """Quita los enlaces a CDN y devuelve cuántos quitó."""
    html = ruta.read_text(encoding="utf-8")
    limpio, cuantos = GUIONES_EXTERNOS.subn("", html)
    if cuantos:
        ruta.write_text(limpio, encoding="utf-8")
    return cuantos


def contar_salidas(ruta: Path) -> int:
    cuaderno = json.loads(ruta.read_text(encoding="utf-8"))
    return sum(len(c.get("outputs", [])) for c in cuaderno["cells"])


def main() -> None:
    DESTINO_HTML.mkdir(parents=True, exist_ok=True)
    for nombre in NOTEBOOKS:
        cuaderno = ejecutar_en_sitio(nombre)
        ruido = limpiar_stderr(cuaderno)
        html = exportar_html(nombre)
        hacer_autocontenido(html)
        print(
            f"  {nombre:<20} ipynb {cuaderno.stat().st_size / 1024:>6.0f} KB "
            f"({contar_salidas(cuaderno)} salidas, {ruido} de ruido quitadas)  ·  "
            f"html {html.stat().st_size / 1024:>6.0f} KB"
        )


if __name__ == "__main__":
    main()
