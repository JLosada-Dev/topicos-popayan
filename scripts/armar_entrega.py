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

NOTEBOOK_PRINCIPAL = "proyecto_final.ipynb"
POR_ETAPA = ("00_preparacion", "01_caracterizacion", "02_topicos", "03_evaluacion")

README = f"""# Entrega · Temas emergentes en las reseñas gastronómicas de Popayán

Trabajo final de Text & Web Analytics · Especialización en Data Analytics para Marketing
Digital, FUP.

**El informe se entrega por separado**, no está en este paquete.

## Qué hay en cada carpeta

- **`1_notebook/`** — `proyecto_final.ipynb`, el estudio completo: problema, objetivo,
  pregunta analítica, datos, técnicas, resultados, insights y recomendaciones. Ya viene
  ejecutado, con todas sus salidas y figuras.
  - **`html/`** — los cuatro notebooks por etapa, que son el anexo metodológico.
- **`2_dataset/`** — los cinco archivos de datos, el diccionario que describe cada
  columna y el manifiesto con los hashes SHA-256 para verificar su integridad.
- **`3_presentacion/capturas/`** — capturas del dashboard de resultados.

## Los HTML no necesitan nada

Los archivos de `1_notebook/html/` se abren **con doble clic en cualquier navegador**:
no hace falta instalar Python, ni Jupyter, ni tener conexión a internet. Las figuras van
incrustadas dentro del propio archivo.

El `.ipynb` sí requiere Jupyter o Google Colab para abrirse.

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
    if DESTINO.exists():
        shutil.rmtree(DESTINO)
    DESTINO.mkdir(parents=True)

    (DESTINO / "README.md").write_text(README, encoding="utf-8")

    copiar(RAIZ / "notebooks" / NOTEBOOK_PRINCIPAL,
           DESTINO / "1_notebook" / NOTEBOOK_PRINCIPAL)
    for nombre in POR_ETAPA:
        copiar(RAIZ / "docs" / "notebooks_html" / f"{nombre}.html",
               DESTINO / "1_notebook" / "html" / f"{nombre}.html")

    for archivo in sorted((RAIZ / "dataset").iterdir()):
        if archivo.is_file():
            copiar(archivo, DESTINO / "2_dataset" / archivo.name)

    capturas = DESTINO / "3_presentacion" / "capturas"
    capturas.mkdir(parents=True)
    (capturas / "LEEME.txt").write_text(
        "Aquí van las capturas del dashboard.\n", encoding="utf-8"
    )

    for carpeta in sorted(p for p in DESTINO.rglob("*") if p.is_dir()):
        archivos = [f for f in carpeta.iterdir() if f.is_file()]
        print(f"  {carpeta.relative_to(DESTINO)}/".ljust(34)
              + f"{len(archivos):>2} archivos  {peso(carpeta) / 1024 / 1024:>6.2f} MB")
    print(f"\n  TOTAL".ljust(36) + f"{peso(DESTINO) / 1024 / 1024:>6.2f} MB")


if __name__ == "__main__":
    main()
