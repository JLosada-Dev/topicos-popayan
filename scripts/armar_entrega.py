"""Arma `entrega/`, el paquete que se sube a Classroom.

Todo se **copia**, nunca se mueve: el proyecto sigue funcionando igual. La carpeta se
regenera entera en cada ejecución, así que nunca queda desincronizada con el repositorio.

El informe no va aquí: se entrega por separado.
"""

import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import RAIZ, URL_DASHBOARD  # noqa: E402

DESTINO = RAIZ / "entrega"
REPOSITORIO = "https://github.com/JLosada-Dev/topicos-popayan"

NOTEBOOK_PRINCIPAL = "proyecto_final"
POR_ETAPA = ("00_preparacion", "01_caracterizacion", "02_topicos", "03_evaluacion")
EN_HTML = (NOTEBOOK_PRINCIPAL, *POR_ETAPA)

README = f"""# Entrega · Temas emergentes en las reseñas gastronómicas de Popayán

Trabajo final de Text & Web Analytics · Especialización en Data Analytics para Marketing
Digital, FUP.

**Estudiante:** José David Losada Legarda · 76261004

**El informe se entrega por separado**, no está en este paquete.

## De qué trata

Se analizaron **5.913 fragmentos de 2.430 reseñas** de Google Maps de establecimientos
gastronómicos de Popayán, para ver si los temas que emergen del texto coinciden con las
seis dimensiones con las que tradicionalmente se evalúa la experiencia gastronómica
—comida, servicio, precio, ambiente, tiempo de espera y patrimonio—.

El acuerdo resultó **parcial, no total**: un 13 % del corpus habla de atributos que el
esquema no contempla, y lo que el método no logra agrupar es sistemáticamente lo más
crítico.

## Por dónde empezar

1. **{URL_DASHBOARD}** — el dashboard, si prefieres
   recorrer los resultados de forma interactiva en vez de leerlos. No hay que instalar
   nada: se abre en el navegador. Lleva la misma presentación, más las tablas
   explorables y un buscador sobre el corpus.
2. **`3_presentacion/presentacion.pdf`** — el recorrido completo en once pantallas, de
   diez minutos de lectura.
3. **`1_notebook/html/proyecto_final.html`** — el estudio con su desarrollo, sus cifras
   y sus figuras.
4. **`2_dataset/diccionario_datos.md`** — qué hay en cada archivo de datos, columna por
   columna, antes de abrir ningún CSV.

## Qué hay en cada carpeta

- **`1_notebook/`** — `proyecto_final.ipynb`, el estudio completo: problema, objetivo,
  pregunta analítica, datos, técnicas, resultados, insights y recomendaciones. Ya viene
  ejecutado, con todas sus salidas y figuras. Si quieres volver a ejecutarlo, las
  instrucciones para Colab están en la primera celda del propio notebook.
  - **`html/`** — el mismo estudio más los cuatro notebooks por etapa, que son el anexo
    metodológico, en formato HTML.
- **`2_dataset/`** — cinco archivos de datos, el diccionario que describe cada columna y
  su procedencia, y un manifiesto con los hashes SHA-256 para verificar su integridad.
- **`3_presentacion/`** — `presentacion.pdf`, las once pantallas de la sustentación en
  formato 16:9, una por página, listas para proyectar o imprimir.

## Los HTML no necesitan nada

Los archivos de `1_notebook/html/` se abren **con doble clic en cualquier navegador**: no
hace falta instalar Python, ni Jupyter, ni tener conexión a internet. Las figuras van
incrustadas dentro del propio archivo.

El `.ipynb` es la versión ejecutable. En **Google Colab** funciona sin preparativos: la
primera celda clona el repositorio con el código y los datos, y el resto son lecturas de
resultados ya calculados, así que corre en segundos. También funciona en un Jupyter
local si tienes el proyecto.

## Sobre el corpus

Son **reseñas públicas de Google Maps**, reutilizadas con fines exclusivamente
académicos. **Las personas que las escribieron no son identificables**: el corpus no
contiene nombre, identificador ni foto de autor. El único dato de autoría es cuántas
reseñas ha escrito cada persona, que no permite reidentificarla.

Dentro del análisis, los nombres de establecimiento se reemplazan por el marcador
`[LOCAL]`, para que el modelo agrupe por lo que se dice y no por de quién se habla.

## El dashboard en línea

{URL_DASHBOARD}

Las mismas once pantallas de la presentación, más cuatro secciones para explorar por tu
cuenta: los catorce temas con sus tópicos y ejemplos, el mapa de calor del contraste con
el diccionario, y un buscador que recupera fragmentos del corpus por lo que escribas.

Se abre en el navegador, sin instalar nada. Solo lee los resultados ya calculados, así
que responde en segundos. Si lleva días sin visitas puede tardar un minuto en despertar
la primera vez.

En el buscador, la opción de búsqueda **por significado** solo aparece al ejecutarlo en
local: necesita el modelo de embeddings, que excede la memoria del despliegue gratuito.
En línea queda la búsqueda por coincidencia de palabras.

## Repositorio

Código, notebooks ejecutables y documentación completa, incluida la bitácora con cada
decisión y sus cifras:

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

    # Va la versión de Colab, no la local: es la única que sirve a quien recibe el
    # paquete sin tener el proyecto. En Colab clona el repositorio; en local detecta la
    # carpeta. La versión local solo funciona si ya tienes el proyecto, en cuyo caso
    # usarías la copia del repositorio.
    copiar(RAIZ / "notebooks" / "colab" / f"{NOTEBOOK_PRINCIPAL}_colab.ipynb",
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
