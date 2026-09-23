"""Inventario y verificacion de los archivos leidos del proyecto original.

Genera `data/external/manifiesto.csv` (ruta, filas, columnas, hash SHA-256) y
reporta el esquema de cada archivo mas los cruces que validan el corpus antes de
construir el pipeline. Solo lee del original; no transforma ni escribe alli.

Se usa la libreria estandar a proposito: en este paso todavia no hay dependencias
instaladas en el entorno de uv.
"""

import csv
import hashlib
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import (  # noqa: E402
    ARCHIVOS_ORIGEN,
    CORPUS,
    DICCIONARIO_DIMENSIONES,
    DIMENSIONES,
    DIMENSIONES_APTAS_ES,
    IDIOMA_RESENAS,
    MANIFIESTO,
    ORIGEN,
    SENTIMIENTO_FRAGMENTOS,
)

# Los textos de resena superan el limite por campo que trae csv por defecto
csv.field_size_limit(sys.maxsize)

BLOQUE_HASH = 1 << 20
MUESTRA_TIPOS = 500
RECORTE_MUESTRA = 70
VERDADEROS = {"true", "verdadero", "1"}
FALSOS = {"false", "falso", "0"}
BOOLEANOS = VERDADEROS | FALSOS


def hash_sha256(ruta: Path) -> str:
    """Hash del archivo completo, leido por bloques."""
    resumen = hashlib.sha256()
    with ruta.open("rb") as archivo:
        for bloque in iter(lambda: archivo.read(BLOQUE_HASH), b""):
            resumen.update(bloque)
    return resumen.hexdigest()


def leer_csv(ruta: Path) -> list[dict[str, str]]:
    """Filas como diccionarios, sin conversion de tipos."""
    with ruta.open(encoding="utf-8", newline="") as archivo:
        return list(csv.DictReader(archivo))


def _es_entero(valor: str) -> bool:
    return valor.lstrip("-").isdigit()


def _es_decimal(valor: str) -> bool:
    try:
        float(valor)
    except ValueError:
        return False
    return True


def inferir_tipo(valores: list[str]) -> str:
    """Tipo aparente de una columna a partir de sus valores no vacios."""
    presentes = [v for v in valores if v != ""]
    if not presentes:
        return "vacio"
    if all(v.lower() in BOOLEANOS for v in presentes):
        return "booleano"
    if all(_es_entero(v) for v in presentes):
        return "entero"
    if all(_es_decimal(v) for v in presentes):
        return "decimal"
    return "texto"


def esquema(filas: list[dict[str, str]], columnas: list[str]) -> list[dict[str, object]]:
    """Tipo, vacios y un valor de ejemplo por columna."""
    muestra = filas[:MUESTRA_TIPOS]
    descripcion = []
    for columna in columnas:
        valores = [fila[columna] for fila in muestra]
        ejemplo = next((v for v in valores if v != ""), "")
        descripcion.append(
            {
                "columna": columna,
                "tipo": inferir_tipo(valores),
                "vacios": sum(1 for fila in filas if fila[columna] == ""),
                "ejemplo": recortar(ejemplo),
            }
        )
    return descripcion


def recortar(valor: str) -> str:
    """Muestra acotada: el inventario no vuelca textos completos."""
    plano = valor.replace("\n", " ").replace("\r", " ")
    if len(plano) <= RECORTE_MUESTRA:
        return plano
    return plano[:RECORTE_MUESTRA] + "..."


def es_verdadero(valor: str) -> bool:
    return valor.strip().lower() in VERDADEROS


def ruta_relativa(ruta: Path) -> str:
    return str(ruta.relative_to(ORIGEN))


def escribir_manifiesto(entradas: list[dict[str, object]]) -> None:
    MANIFIESTO.parent.mkdir(parents=True, exist_ok=True)
    campos = ["ruta", "filas", "columnas", "hash_sha256", "bytes"]
    with MANIFIESTO.open("w", encoding="utf-8", newline="") as archivo:
        escritor = csv.DictWriter(archivo, fieldnames=campos)
        escritor.writeheader()
        escritor.writerows(entradas)


def resumen_longitudes(longitudes: list[int]) -> dict[str, float]:
    """Minimo, cuartiles, p90 y maximo de una lista de largos."""
    ordenadas = sorted(longitudes)
    cuantil = lambda p: ordenadas[min(int(p * len(ordenadas)), len(ordenadas) - 1)]  # noqa: E731
    return {
        "n": len(ordenadas),
        "min": ordenadas[0],
        "p25": cuantil(0.25),
        "mediana": statistics.median(ordenadas),
        "p75": cuantil(0.75),
        "p90": cuantil(0.90),
        "max": ordenadas[-1],
        "media": round(statistics.mean(ordenadas), 1),
    }


def inventariar() -> list[dict[str, object]]:
    """Manifiesto y esquema de cada archivo del original."""
    entradas = []
    for ruta in ARCHIVOS_ORIGEN:
        filas = leer_csv(ruta)
        columnas = list(filas[0].keys()) if filas else []
        entradas.append(
            {
                "ruta": ruta_relativa(ruta),
                "filas": len(filas),
                "columnas": len(columnas),
                "hash_sha256": hash_sha256(ruta),
                "bytes": ruta.stat().st_size,
            }
        )
        print(f"\n=== {ruta_relativa(ruta)} ===")
        print(f"filas: {len(filas)}   columnas: {len(columnas)}")
        print(f"{'columna':<22}{'tipo':<11}{'vacios':>8}  ejemplo")
        for campo in esquema(filas, columnas):
            print(
                f"{campo['columna']:<22}{campo['tipo']:<11}{campo['vacios']:>8}  {campo['ejemplo']}"
            )
    return entradas


def verificar() -> None:
    """Cruces que validan el corpus antes de construir el pipeline."""
    corpus = leer_csv(CORPUS)
    idioma = leer_csv(IDIOMA_RESENAS)
    dimensiones = leer_csv(DIMENSIONES_APTAS_ES)
    fragmentos = leer_csv(SENTIMIENTO_FRAGMENTOS)
    diccionario = leer_csv(DICCIONARIO_DIMENSIONES)

    aptas_corpus = {f["review_id"] for f in corpus if es_verdadero(f["apto"])}
    aptas_idioma = {f["review_id"] for f in idioma if es_verdadero(f["apto"])}
    espanol = {f["review_id"] for f in idioma if es_verdadero(f["es_espanol"])}
    aptas_es = aptas_idioma & espanol
    con_dimensiones = {f["review_id"] for f in dimensiones}
    claves_fragmento = {f["clave"] for f in fragmentos}

    print("\n\n===== VERIFICACION =====")
    print(f"\nCorpus total                         {len(corpus):>6}")
    print(f"Corpus con apto = True               {len(aptas_corpus):>6}")
    print(f"Filas en idioma_resenas              {len(idioma):>6}")
    print(f"  de ellas apto = True               {len(aptas_idioma):>6}")
    print(f"  de ellas es_espanol = True         {len(espanol):>6}")
    print(f"apto = True y espanol                {len(aptas_es):>6}   (esperado 2432)")
    print(f"coincide con 2.432: {len(aptas_es) == 2432}")

    largos = [int(float(f["largo"])) for f in corpus if es_verdadero(f["apto"]) and f["largo"]]
    print(f"largo minimo entre las aptas         {min(largos):>6}")

    print(f"\nFilas en dimensiones_aptas_es        {len(dimensiones):>6}")
    print(f"Resenas distintas en ese archivo     {len(con_dimensiones):>6}")
    print(f"  identicas al conjunto apto+es      {con_dimensiones == aptas_es}")

    con_alguna = {f["review_id"] for f in dimensiones if int(f["n_dim"]) > 0}
    sin_ninguna = con_dimensiones - con_alguna
    print(f"  con al menos una dimension activa  {len(con_alguna):>6}")
    print(f"  sin ninguna dimension activa       {len(sin_ninguna):>6}")

    print(f"\nFilas en sentimiento_fragmentos      {len(fragmentos):>6}")
    print(f"Resenas distintas con fragmento      {len(claves_fragmento):>6}")
    aptas_con_fragmento = aptas_es & claves_fragmento
    print(f"  de las aptas en espanol            {len(aptas_con_fragmento):>6}")
    print(f"  aptas sin ningun fragmento         {len(aptas_es - claves_fragmento):>6}")
    print(f"claves de fragmento == con_alguna    {claves_fragmento == con_alguna}")
    print(f"claves fuera de las aptas en espanol {len(claves_fragmento - aptas_es):>6}")

    print("\n--- Prevalencia por dimension ---")
    print(f"{'dimension':<14}{'resenas':>9}{'% aptas':>9}{'filas frag':>12}{'frag unicos':>13}")
    for dimension in DIMENSIONES:
        activas = sum(1 for f in dimensiones if es_verdadero(f[dimension]))
        filas_dim = [f for f in fragmentos if f["dimension"] == dimension]
        unicos = {f["fragmento"] for f in filas_dim}
        porcentaje = 100 * activas / len(dimensiones)
        print(
            f"{dimension:<14}{activas:>9}{porcentaje:>8.1f}%{len(filas_dim):>12}{len(unicos):>13}"
        )

    reparto = {}
    for fila in dimensiones:
        reparto[fila["n_dim"]] = reparto.get(fila["n_dim"], 0) + 1
    print("\n--- Dimensiones activas por resena ---")
    for n_dim in sorted(reparto, key=int):
        cuota = 100 * reparto[n_dim] / len(dimensiones)
        print(f"  n_dim = {n_dim}: {reparto[n_dim]:>5}  ({cuota:.1f}%)")

    print("\n--- Fragmentos ---")
    textos_unicos = {f["fragmento"] for f in fragmentos}
    pares = {(f["clave"], f["dimension"]) for f in fragmentos}
    print(f"filas (clave, dimension, fragmento)  {len(fragmentos):>6}")
    print(f"textos de fragmento unicos           {len(textos_unicos):>6}")
    print(f"pares resena-dimension               {len(pares):>6}")

    reparto_origen = {}
    for fila in fragmentos:
        reparto_origen[fila["origen"]] = reparto_origen.get(fila["origen"], 0) + 1
    for origen, cuenta in sorted(reparto_origen.items()):
        print(f"origen = {origen:<10} {cuenta:>6}  ({100 * cuenta / len(fragmentos):.1f}%)")

    print("\nLongitud en caracteres:")
    for etiqueta, conjunto in (("todas las filas", fragmentos),):
        largos_fragmento = [len(f["fragmento"]) for f in conjunto]
        print(f"  {etiqueta}: {resumen_longitudes(largos_fragmento)}")
    largos_unicos = [len(t) for t in textos_unicos]
    print(f"  textos unicos:   {resumen_longitudes(largos_unicos)}")

    palabras = [len(f["fragmento"].split()) for f in fragmentos]
    print(f"\nLongitud en palabras (filas): {resumen_longitudes(palabras)}")

    incluidos = [f for f in diccionario if f["estado"] == "incluido"]
    print(f"\nDiccionario: {len(diccionario)} terminos, {len(incluidos)} incluidos")
    por_dimension = {}
    for fila in incluidos:
        por_dimension[fila["dimension"]] = por_dimension.get(fila["dimension"], 0) + 1
    for dimension in DIMENSIONES:
        print(f"  {dimension:<12} {por_dimension.get(dimension, 0):>3} terminos incluidos")


def main() -> None:
    entradas = inventariar()
    escribir_manifiesto(entradas)
    print(f"\n\nManifiesto escrito en {MANIFIESTO}")
    verificar()


if __name__ == "__main__":
    main()
