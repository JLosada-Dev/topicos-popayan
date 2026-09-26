"""Arma `entrega/`, el paquete que se sube a Classroom.

Todo se **copia**, nunca se mueve: el proyecto sigue funcionando igual. La carpeta se
regenera entera en cada ejecución, así que nunca queda desincronizada con el repositorio.

El informe no va aquí: se entrega por separado.
"""

import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import RAIZ  # noqa: E402

DESTINO = RAIZ / "entrega"
REPOSITORIO = "https://github.com/JLosada-Dev/topicos-popayan"

NOTEBOOK_PRINCIPAL = "proyecto_final"
POR_ETAPA = ("00_preparacion", "01_caracterizacion", "02_topicos", "03_evaluacion")
EN_HTML = (NOTEBOOK_PRINCIPAL, *POR_ETAPA)

README = f"""# Entrega · Temas emergentes en las reseñas gastronómicas de Popayán

Trabajo final de Text & Web Analytics · Especialización en Data Analytics para Marketing
Digital, FUP.

**El informe se entrega por separado**, no está en este paquete.

## Qué hay en cada carpeta

- **`1_notebook/`** — `proyecto_final.ipynb`, el estudio completo: problema, objetivo,
  pregunta analítica, datos, técnicas, resultados, insights y recomendaciones. Ya viene
  ejecutado, con todas sus salidas y figuras.
  - **`html/`** — el mismo estudio y los cuatro notebooks por etapa, que son el anexo
    metodológico, en formato HTML.
- **`2_dataset/`** — los cinco archivos de datos, el diccionario que describe cada
  columna y el manifiesto con los hashes SHA-256 para verificar su integridad.
- **`3_presentacion/`** — `presentacion.pdf`, las once pantallas de la sustentación en
  formato 16:9, una por página, listas para proyectar o imprimir.

## Los HTML no necesitan nada

Los archivos de `1_notebook/html/` se abren **con doble clic en cualquier navegador**:
no hace falta instalar Python, ni Jupyter, ni tener conexión a internet. Las figuras van
incrustadas dentro del propio archivo. Para leer el estudio sin instalar nada, el archivo
es `html/proyecto_final.html`.

El `.ipynb` es la versión ejecutable y requiere Jupyter o Google Colab.

## Repositorio

Código, notebooks ejecutables y documentación completa:

{REPOSITORIO}
"""


def copiar(origen: Path, destino: Path) -> int:
    destino.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(origen, destino)
    return destino.stat().st_size


def peso(carpeta: Path) -> int:
    return sum(f.stat().st_size for f in carpeta.rglob("*") if f.is_file())


def main() -> None:
    # Se rehacen solo las carpetas que produce este script. `3_presentacion/` la genera
    # `exportar_presentacion.py` y se versiona, así que borrarla aquí haría perder las
    # capturas y el PDF sin avisar.
    for carpeta in (DESTINO / "1_notebook", DESTINO / "2_dataset"):
        if carpeta.exists():
            shutil.rmtree(carpeta)
    DESTINO.mkdir(parents=True, exist_ok=True)

    (DESTINO / "README.md").write_text(README, encoding="utf-8")

    copiar(RAIZ / "notebooks" / f"{NOTEBOOK_PRINCIPAL}.ipynb",
           DESTINO / "1_notebook" / f"{NOTEBOOK_PRINCIPAL}.ipynb")
    for nombre in EN_HTML:
        copiar(RAIZ / "docs" / "notebooks_html" / f"{nombre}.html",
               DESTINO / "1_notebook" / "html" / f"{nombre}.html")

    for archivo in sorted((RAIZ / "dataset").iterdir()):
        if archivo.is_file():
            copiar(archivo, DESTINO / "2_dataset" / archivo.name)

    (DESTINO / "3_presentacion").mkdir(parents=True, exist_ok=True)

    for carpeta in sorted(p for p in DESTINO.rglob("*") if p.is_dir()):
        archivos = [f for f in carpeta.iterdir() if f.is_file()]
        print(f"  {carpeta.relative_to(DESTINO)}/".ljust(34)
              + f"{len(archivos):>2} archivos  {peso(carpeta) / 1024 / 1024:>6.2f} MB")
    print(f"\n  TOTAL".ljust(36) + f"{peso(DESTINO) / 1024 / 1024:>6.2f} MB")


if __name__ == "__main__":
    main()
