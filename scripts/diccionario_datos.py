"""Genera `dataset/diccionario_datos.md` desde los propios archivos.

Las tablas de columnas se leen de los CSV en vez de escribirse a mano, para que no
puedan desincronizarse. Las descripciones sí son manuales: dicen qué significa cada
columna, que es lo que un archivo no puede decir de sí mismo.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd  # noqa: E402

from src.config import RAIZ  # noqa: E402

DESTINO = RAIZ / "dataset"

TIPOS = {"object": "texto", "str": "texto", "bool": "booleano",
         "int64": "entero", "float64": "decimal"}


def miles(numero: int) -> str:
    """Separador de miles con punto, a la española. Solo toca el número."""
    return f"{numero:,}".replace(",", ".")


DESCRIPCIONES = {}  # se llena desde `descripciones_columnas.py`


def tabla_columnas(tabla: pd.DataFrame, descripciones: dict) -> list[str]:
    lineas = ["| Columna | Tipo | Vacíos | Descripción |", "|---|---|---:|---|"]
    for columna in tabla.columns:
        tipo = TIPOS.get(str(tabla[columna].dtype), str(tabla[columna].dtype))
        if str(tabla[columna].dtype).startswith("str"):
            tipo = "texto"
        lineas.append(
            f"| `{columna}` | {tipo} | {int(tabla[columna].isna().sum())} | "
            f"{descripciones.get(columna, '—')} |"
        )
    return lineas


def main() -> None:
    from scripts.descripciones_columnas import DESCRIPCIONES as desc

    manifiesto = pd.read_csv(DESTINO / "manifiesto.csv")
    lineas = [
        "# Diccionario de datos", "",
        "Este paquete reúne los cinco archivos necesarios para entender y reproducir el",
        "estudio: las tres entradas que se heredan del proyecto previo y las dos salidas",
        "propias.", "",
        "Todos son CSV con codificación UTF-8, separador coma y encabezado en la primera",
        "fila.", "",
        "## Resumen", "",
        "| Archivo | Unidad de análisis | Filas | Columnas | Procedencia |",
        "|---|---|---:|---:|---|",
    ]
    for fila in manifiesto.itertuples(index=False):
        lineas.append(
            f"| `{fila.archivo}` | {fila.unidad_de_analisis} | {miles(fila.filas)} | "
            f"{fila.columnas} | {fila.procedencia} |"
        )

    lineas += [
        "", "## Cómo se enlazan entre sí", "", "```",
        "marco_muestral_final.csv  --place_id-->   corpus_final.csv",
        "corpus_final.csv          --review_id-->  fragmentos_topicos.csv",
        "dimensiones.csv           ------------->  las seis columnas booleanas de",
        "                                          fragmentos_topicos.csv",
        "fragmentos_topicos.csv    --topico----->  temas_consolidado.csv",
        "```", "",
    ]

    for fila in manifiesto.itertuples(index=False):
        tabla = pd.read_csv(DESTINO / fila.archivo)
        lineas += [
            f"## `{fila.archivo}`", "",
            f"**Unidad de análisis:** {fila.unidad_de_analisis} · "
            f"**{miles(fila.filas)} filas × {fila.columnas} columnas**", "",
            f"**Procedencia:** {fila.procedencia}", "",
            *tabla_columnas(tabla, desc[fila.archivo]), "",
        ]

    lineas += [
        "## Manifiesto de integridad", "",
        "Hash SHA-256 de cada archivo, para verificar que es el mismo que se usó en el",
        "estudio:", "",
        "| Archivo | Bytes | SHA-256 |", "|---|---:|---|",
    ]
    for fila in manifiesto.itertuples(index=False):
        lineas.append(f"| `{fila.archivo}` | {miles(fila.bytes)} | `{fila.sha256}` |")
    lineas += [
        "", "Para comprobarlo:", "", "```bash", "shasum -a 256 dataset/*.csv", "```", "",
        "`manifiesto.csv`, en esta misma carpeta, trae los mismos datos en formato",
        "tabular.", "",
    ]

    (DESTINO / "diccionario_datos.md").write_text("\n".join(lineas), encoding="utf-8")
    print(f"  diccionario_datos.md · {len(lineas)} líneas")


if __name__ == "__main__":
    main()
