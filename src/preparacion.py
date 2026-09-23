"""Construcción del corpus de fragmentos a partir de las reseñas heredadas.

Orden del pipeline: cargar, unir zona, desduplicar, enmascarar nombres, limpiar,
segmentar por cláusula, aplicar el diccionario a cada fragmento y generar el texto
de c-TF-IDF.

Dos precisiones sobre el orden:

- Los saltos de línea y las etiquetas `<br>` se normalizan DESPUÉS de segmentar, no
  antes: son separadores de cláusula y colapsarlos antes perdería esos cortes. Antes
  de segmentar solo se quitan URLs y emojis, que no afectan los límites.
- Las dimensiones se recalculan sobre cada fragmento, no se heredan de la reseña.
"""

import re
from functools import lru_cache

import pandas as pd

from src.config import (
    CORPUS,
    DIMENSIONES,
    DIMENSIONES_APTAS_ES,
    IDIOMA_RESENAS,
    MARCO_MUESTRAL,
)
from src.diccionario import (
    TOKENS_MINIMOS_NOMBRE,
    aplicar_diccionario,
    cargar_diccionario,
    normalizar,
)
from src.segmentacion import LARGO_MINIMO_FRAGMENTO, segmentar, segmentar_sin_filtrar
from src.stopwords import NEGACIONES, STOPWORDS, STOPWORDS_ES
from src.texto import MARCADOR_LOCAL, limpiar_resena, normalizar_espacios, plegar

COLUMNAS_CORPUS = ["review_id", "place_id", "establecimiento", "rating", "texto"]

# Clave del duplicado real. El corpus no trae identificador de autor, solo su número
# de reseñas, que es el unico proxy disponible del autor anonimizado.
CLAVE_DUPLICADO = ["autor_n_resenas", "texto"]

PATRON_NO_PALABRA = re.compile(r"[^a-záéíóúüñ\s]+")


def cargar_resenas() -> pd.DataFrame:
    """Las 2.432 reseñas aptas en español, con zona del marco muestral."""
    corpus = pd.read_csv(CORPUS)
    idioma = pd.read_csv(IDIOMA_RESENAS)
    aptas = pd.read_csv(DIMENSIONES_APTAS_ES)["review_id"]

    en_espanol = idioma.loc[idioma["apto"] & idioma["es_espanol"], "review_id"]
    resenas = corpus[corpus["review_id"].isin(en_espanol)].copy()

    # `dimensiones_aptas_es` es la lista maestra: debe coincidir exactamente
    faltan = set(aptas) - set(resenas["review_id"])
    if faltan:
        raise ValueError(f"{len(faltan)} reseñas de la lista maestra no están en el corpus")

    marco = pd.read_csv(MARCO_MUESTRAL)[["place_id", "zona"]]
    return resenas.merge(marco, on="place_id", how="left")


def eliminar_duplicados(resenas: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Quita el duplicado real y devuelve también las filas eliminadas, para auditar."""
    repetidas = resenas.duplicated(subset=CLAVE_DUPLICADO, keep="first")
    return resenas[~repetidas].copy(), resenas[repetidas].copy()


def nombres_establecimientos() -> list[str]:
    """Nombres del marco muestral más los del corpus, sin repetir."""
    marco = pd.read_csv(MARCO_MUESTRAL)["name"].dropna()
    corpus = pd.read_csv(CORPUS)["establecimiento"].dropna()
    return sorted(set(marco) | set(corpus))


def _tokens_nombre(nombre: str) -> list[str]:
    return [t for t in re.split(r"\W+", normalizar(nombre)) if t]


@lru_cache(maxsize=1)
def _patron_terminos_diccionario() -> re.Pattern:
    """Une las raíces incluidas del diccionario, para reconocer palabras de dominio."""
    raices = cargar_diccionario()["raiz"].tolist()
    return re.compile(rf"^(?:{'|'.join(f'(?:{r})' for r in raices)})\w*$")


def _es_distintiva(tokens: list[str]) -> bool:
    """Una secuencia sirve para enmascarar solo si aporta algo propio del local.

    Se descartan dos casos que producirían falsos positivos en todo el corpus:

    - Solo palabras funcionales: «de la», sacada de «El fogón de la abuela»,
      coincide en casi cualquier reseña.
    - Palabras funcionales más un término del diccionario: «de comidas», sacada de
      «Plazoleta de Comidas», enmascararía «amplia variedad de comidas» y borraría
      justo la señal de la dimensión que se quiere medir.
    """
    termino = _patron_terminos_diccionario()
    return any(
        token not in STOPWORDS_ES and not termino.match(token) for token in tokens
    )


def _patron_de_secuencias(secuencias: list[list[str]]) -> re.Pattern | None:
    if not secuencias:
        return None
    alternativas = [r"\W+".join(re.escape(t) for t in s) for s in secuencias]
    return re.compile(rf"\b(?:{'|'.join(alternativas)})\b")


@lru_cache(maxsize=512)
def patron_nombre_propio(nombre: str) -> re.Pattern | None:
    """Patrón para el establecimiento de la propia reseña.

    Acepta subsecuencias contiguas de al menos `TOKENS_MINIMOS_NOMBRE` tokens, como
    hace `diccionario.patron_nombre`, porque la reseña suele abreviar el nombre del
    local del que habla. Se exige además que la subsecuencia tenga alguna palabra
    distintiva.
    """
    tokens = _tokens_nombre(nombre)
    if len(tokens) < TOKENS_MINIMOS_NOMBRE:
        return None
    secuencias = [
        tokens[inicio : inicio + largo]
        for largo in range(len(tokens), TOKENS_MINIMOS_NOMBRE - 1, -1)
        for inicio in range(len(tokens) - largo + 1)
    ]
    return _patron_de_secuencias([s for s in secuencias if _es_distintiva(s)])


def patron_nombres_completos(nombres: list[str]) -> re.Pattern | None:
    """Patrón de todos los establecimientos, exigiendo el nombre completo.

    Para un local que no es el de la reseña no hay evidencia de que una abreviatura
    se refiera a él, así que aquí no se admiten subsecuencias: «la casa», sacada de
    «La casa del té popayán», enmascararía «comida típica de la casa» en cualquier
    reseña. Se compila una sola vez para todo el corpus.
    """
    secuencias = [_tokens_nombre(nombre) for nombre in nombres]
    utiles = [s for s in secuencias if len(s) >= TOKENS_MINIMOS_NOMBRE and _es_distintiva(s)]
    return _patron_de_secuencias(utiles)


def enmascarar_locales(texto: str, patrones: list[re.Pattern]) -> tuple[str, int]:
    """Reemplaza menciones de establecimientos por `[LOCAL]` en el texto original.

    La búsqueda corre sobre el texto plegado (minúsculas, sin tildes) y el reemplazo
    sobre el original, que es el que va a los embeddings. `plegar` conserva la
    longitud carácter a carácter, de modo que los índices coinciden en ambos.
    """
    if not isinstance(texto, str) or not texto:
        return "", 0
    vigentes = [p for p in patrones if p is not None]
    plegado = plegar(texto)
    tramos = [m.span() for patron in vigentes for m in patron.finditer(plegado)]
    if not tramos:
        return texto, 0

    fusionados = []
    for inicio, fin in sorted(tramos):
        if fusionados and inicio <= fusionados[-1][1]:
            fusionados[-1][1] = max(fusionados[-1][1], fin)
            continue
        fusionados.append([inicio, fin])

    salida = texto
    for inicio, fin in reversed(fusionados):
        salida = salida[:inicio] + MARCADOR_LOCAL + salida[fin:]
    return salida, len(fusionados)


def patrones_para(nombre_propio: str, patron_completos: re.Pattern | None) -> list:
    """Patrones aplicables a una reseña: su propio local, abreviable, y el resto."""
    return [patron_nombre_propio(nombre_propio), patron_completos]


def texto_para_ctfidf(fragmento: str) -> str:
    """Minúsculas, sin marcador, sin puntuación y sin stopwords."""
    sin_marcador = fragmento.replace(MARCADOR_LOCAL, " ")
    minusculas = sin_marcador.lower()
    solo_palabras = PATRON_NO_PALABRA.sub(" ", minusculas)
    # Las negaciones se conservan aunque tengan dos letras: «no» invierte el sentido
    util = lambda p: p not in STOPWORDS and (len(p) > 2 or p in NEGACIONES)  # noqa: E731
    return " ".join(p for p in solo_palabras.split() if util(p))


def _filas_de_fragmentos(resenas: pd.DataFrame, patron_completos) -> list[dict]:
    """Una fila por cláusula, ya enmascarada, limpia y con espacios normalizados."""
    filas = []
    for resena in resenas.itertuples(index=False):
        patrones = patrones_para(resena.establecimiento, patron_completos)
        enmascarado, n_marcas = enmascarar_locales(resena.texto, patrones)
        limpio = limpiar_resena(enmascarado)
        clausulas = segmentar(limpio)
        for numero, clausula in enumerate(clausulas, start=1):
            filas.append(
                {
                    "fragmento_id": f"{resena.review_id}_{numero:02d}",
                    "review_id": resena.review_id,
                    "place_id": resena.place_id,
                    "establecimiento": resena.establecimiento,
                    "zona": resena.zona,
                    "rating": resena.rating,
                    "fragmento_num": numero,
                    "n_fragmentos_resena": len(clausulas),
                    "texto": normalizar_espacios(clausula),
                    "marcas_local_resena": n_marcas,
                }
            )
    return filas


def construir_fragmentos(resenas: pd.DataFrame) -> pd.DataFrame:
    """Corpus de fragmentos con las seis dimensiones recalculadas por cláusula."""
    patron_completos = patron_nombres_completos(nombres_establecimientos())
    fragmentos = pd.DataFrame(_filas_de_fragmentos(resenas, patron_completos))

    diccionario = cargar_diccionario()
    detectadas = aplicar_diccionario(
        fragmentos["texto"], diccionario, fragmentos["establecimiento"]
    )
    for dimension in DIMENSIONES:
        fragmentos[dimension] = detectadas[dimension].to_numpy()
    fragmentos["n_dim"] = fragmentos[list(DIMENSIONES)].sum(axis=1)

    fragmentos["texto_limpio"] = fragmentos["texto"].map(texto_para_ctfidf)
    fragmentos["largo_caracteres"] = fragmentos["texto"].str.len()
    fragmentos["largo_palabras"] = fragmentos["texto"].str.split().str.len()
    fragmentos["tiene_local"] = fragmentos["texto"].str.contains(
        re.escape(MARCADOR_LOCAL), regex=True
    )
    return fragmentos


def contar_descartes_por_largo(resenas: pd.DataFrame, patron_completos) -> dict:
    """Cláusulas que caen por el largo mínimo, para reportar el descarte."""
    totales, cortas = 0, 0
    for resena in resenas.itertuples(index=False):
        patrones = patrones_para(resena.establecimiento, patron_completos)
        enmascarado, _ = enmascarar_locales(resena.texto, patrones)
        limpio = limpiar_resena(enmascarado)
        todas = segmentar_sin_filtrar(limpio)
        totales += len(todas)
        cortas += sum(1 for c in todas if len(c) < LARGO_MINIMO_FRAGMENTO)
    return {"clausulas_totales": totales, "descartadas_por_largo": cortas}
