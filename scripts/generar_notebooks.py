"""Genera los cuatro notebooks en su versión local y en su versión Colab.

El contenido vive en `notebooks_contenido.py` y es idéntico en ambas versiones. Lo
único que cambia es el preámbulo: en local basta con poner la raíz del repositorio en
`sys.path`; en Colab hay que instalar dependencias y resolver de dónde salen los datos.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import RAIZ  # noqa: E402

from scripts.notebook_final import PROYECTO_FINAL  # noqa: E402
from scripts.notebooks_contenido import NOTEBOOKS, code, md  # noqa: E402

TODOS = {"proyecto_final": PROYECTO_FINAL, **NOTEBOOKS}

CARPETA_LOCAL = RAIZ / "notebooks"
CARPETA_COLAB = RAIZ / "notebooks" / "colab"

KERNEL_LOCAL = {"display_name": "topicos-popayan (uv)", "language": "python",
                "name": "topicos-popayan"}
KERNEL_COLAB = {"display_name": "Python 3", "language": "python", "name": "python3"}

DEPENDENCIAS_COLAB = (
    "pandas numpy pyarrow scikit-learn matplotlib "
    "sentence-transformers bertopic gensim"
)

PREAMBULO_LOCAL = [
    code("""
# Configuración local. El kernel es el del entorno de uv:
#     uv run python -m ipykernel install --user --name topicos-popayan
import sys
from pathlib import Path

RAIZ = Path.cwd().parent if Path.cwd().name == "notebooks" else Path.cwd()
sys.path.insert(0, str(RAIZ))
print(f"raíz del proyecto: {RAIZ.name}/  ·  datos: {(RAIZ / 'data' / 'processed').exists()}")
"""),
]


def preambulo_colab(nombre: str) -> list:
    return [
        md(f"""
> ### Versión Colab de `{nombre}`
>
> Equivalente en contenido a la versión local `notebooks/{nombre}.ipynb`. Solo cambian
> las dos primeras celdas, que instalan dependencias y resuelven de dónde salen los
> datos. **Ejecuta las dos y sigue de largo**; el resto del notebook es idéntico.
>
> El notebook **no recalcula nada costoso**: lee de `data/processed/` los resultados ya
> producidos por los scripts de `scripts/`. Necesita, por tanto, que el proyecto viaje
> con su carpeta `data/processed/`.
"""),
        code(f"""
# 1/2 · Dependencias. En local no hace falta: el entorno de uv ya las tiene.
import sys


def en_colab() -> bool:
    # `find_spec` no sirve aquí: lanza ModuleNotFoundError si no existe `google`
    try:
        import google.colab  # noqa: F401
    except ImportError:
        return False
    return True


EN_COLAB = en_colab()

if EN_COLAB:
    %pip install -q {DEPENDENCIAS_COLAB}
    print("dependencias instaladas")
else:
    print("no se detectó Colab: se asume el entorno de uv, no se instala nada")
"""),
        code('''
# 2/2 · Acceso a los datos. Tres caminos, en orden de preferencia:
#   a) el proyecto ya está en Drive          -> se monta y se usa
#   b) se sube un .zip del proyecto          -> se descomprime
#   c) se está ejecutando en local           -> se usa la carpeta del repositorio
import sys
import zipfile
from pathlib import Path

CARPETA_EN_DRIVE = "MyDrive/topicos-popayan"   # ajusta si la guardaste en otra ruta


def _valida(raiz):
    return (Path(raiz) / "src" / "config.py").exists() and (
        Path(raiz) / "data" / "processed" / "fragmentos.csv"
    ).exists()


def resolver_raiz():
    if not EN_COLAB:
        aqui = Path.cwd()
        for candidata in (aqui, aqui.parent, aqui.parent.parent):
            if _valida(candidata):
                return candidata
        raise RuntimeError("No se encontró la raíz del proyecto desde el directorio actual")

    from google.colab import drive, files

    try:
        drive.mount("/content/drive", force_remount=False)
        candidata = Path("/content/drive") / CARPETA_EN_DRIVE
        if _valida(candidata):
            return candidata
        print(f"No se encontró el proyecto en {candidata}")
    except Exception as error:                      # Drive no disponible o rechazado
        print(f"No se pudo montar Drive ({error})")

    print("Sube un .zip con el proyecto completo (debe incluir src/ y data/processed/)")
    subidos = files.upload()
    nombre = next(iter(subidos))
    destino = Path("/content/proyecto")
    with zipfile.ZipFile(nombre) as archivo:
        archivo.extractall(destino)
    candidatas = [destino, *(p.parent for p in destino.rglob("src/config.py"))]
    for candidata in candidatas:
        if _valida(candidata):
            return candidata
    raise RuntimeError("El zip no contiene src/ y data/processed/ juntos")


RAIZ = resolver_raiz()
sys.path.insert(0, str(RAIZ))
print(f"raíz del proyecto: {RAIZ.name}/")
'''),
        code("""
# El módulo de rutas deduce la raíz de su propia ubicación, así que ya apunta bien
from src.config import DATOS_PROCESADOS, FIGURAS

faltan = [n for n in ("fragmentos.csv", "fragmentos_topicos.csv", "topicos_etiquetados.csv")
          if not (DATOS_PROCESADOS / n).exists()]
print("data/processed:", "completo" if not faltan else f"FALTAN {faltan}")
print("figuras:", "sí" if FIGURAS.exists() else "no encontradas")
"""),
    ]


def a_celda(tipo: str, fuente: str, identificador: str) -> dict:
    lineas = fuente.split("\n")
    contenido = [linea + "\n" for linea in lineas[:-1]] + [lineas[-1]]
    celda = {"cell_type": tipo, "metadata": {}, "source": contenido, "id": identificador}
    if tipo == "code":
        celda.update({"execution_count": None, "outputs": []})
    return celda


def construir(celdas: list, kernel: dict) -> dict:
    return {
        "cells": [a_celda(t, f, f"celda{i:02d}") for i, (t, f) in enumerate(celdas)],
        "metadata": {
            "kernelspec": kernel,
            "language_info": {
                "name": "python", "version": "3.12.12", "file_extension": ".py",
                "mimetype": "text/x-python", "nbconvert_exporter": "python",
                "pygments_lexer": "ipython3",
            },
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }


def escribir(ruta: Path, cuaderno: dict) -> None:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(json.dumps(cuaderno, ensure_ascii=False, indent=1), encoding="utf-8")


def main() -> None:
    for nombre, cuerpo in TODOS.items():
        titulo, resto = cuerpo[0], cuerpo[1:]

        local = construir([titulo, *PREAMBULO_LOCAL, *resto], KERNEL_LOCAL)
        escribir(CARPETA_LOCAL / f"{nombre}.ipynb", local)

        colab = construir([titulo, *preambulo_colab(nombre), *resto], KERNEL_COLAB)
        escribir(CARPETA_COLAB / f"{nombre}_colab.ipynb", colab)

        print(f"  {nombre}: {len(local['cells'])} celdas local · "
              f"{len(colab['cells'])} celdas Colab")


if __name__ == "__main__":
    main()
