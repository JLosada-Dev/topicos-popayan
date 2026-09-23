"""Aplicación del diccionario de dimensiones a los textos.

Copiado de `src/diccionario.py` del proyecto `reputacion-popayan` (módulo completo:
`normalizar`, `cargar_diccionario`, `compilar_dimension`, `patron_nombre`,
`veta_contexto`, `ocurrencias`, `spans_nombre`, `aplicar_diccionario`,
`detalle_ocurrencias`). Se copia en vez de importarse porque aquel proyecto es de
solo lectura.

Único cambio respecto al original: `RUTA_DICCIONARIO` apunta al CSV del proyecto
original a través de `src.config`, en vez de a una carpeta local. El diccionario no
se duplica; queda registrado en `data/external/manifiesto.csv` con su hash.

El diccionario vive en `diccionario/dimensiones.csv`, no en el código. Cada término
trae una raíz que se compara contra el texto normalizado (minúsculas, sin acentos),
de modo que «Salpicón», «salpicon» y «SALPICÓN» cuentan igual y las variantes
morfológicas (plural, género) se cubren con una sola raíz.

Dos controles vetan coincidencias que no son menciones reales de la dimensión:

- Contexto: `patron_contexto` se evalúa según `modo_contexto`. `veta_posterior`
  descarta por lo que sigue («auténtico sabor mexicano» no es patrimonio payanés),
  `veta_previa` por lo que antecede («comidas rápidas» no es rapidez del servicio) y
  `requiere` exige que el patrón aparezca en la oración («calidad» solo cuenta como
  precio si hay precio, costo o relación cerca).
- Nombre del establecimiento: una coincidencia que cae dentro de una mención del
  nombre del local no cuenta, igual que las referencias territoriales genéricas.
  Se exige que aparezcan al menos dos tokens contiguos del nombre para no vetar
  menciones legítimas del producto («aplanchados» suelto en Aplanchados Doña Chepa).
"""

import re
import unicodedata
from functools import lru_cache
from pathlib import Path

import pandas as pd

from src.config import DICCIONARIO_DIMENSIONES

RUTA_DICCIONARIO = DICCIONARIO_DIMENSIONES

COLUMNAS_DICCIONARIO = [
    "dimension",
    "termino",
    "raiz",
    "categoria",
    "estado",
    "patron_contexto",
    "modo_contexto",
    "nota",
]

ESTADO_INCLUIDO = "incluido"

# Modos de `modo_contexto`, que determinan cómo se evalúa `patron_contexto`
MODO_REQUIERE = "requiere"          # debe aparecer en la oración de la coincidencia
MODO_VETA_PREVIA = "veta_previa"    # veta si cierra el texto anterior a la coincidencia
MODO_VETA_POSTERIOR = "veta_posterior"  # veta si abre el texto posterior a la coincidencia

# Mínimo de tokens contiguos del nombre que deben aparecer para vetar por nombre
TOKENS_MINIMOS_NOMBRE = 2

# Caracteres a cada lado que forman la ventana de `MODO_REQUIERE`, recortada a la oración
VENTANA_CONTEXTO = 50
DELIMITADORES_ORACION = ".!?\n"

CONTADA = "contada"
VETADA_NOMBRE = "vetada_nombre"
VETADA_CONTEXTO = "vetada_contexto"


def normalizar(texto: str) -> str:
    """Minúsculas y sin diacríticos, para que la comparación no dependa de la ortografía."""
    if not isinstance(texto, str):
        return ""
    descompuesto = unicodedata.normalize("NFKD", texto.lower())
    return "".join(c for c in descompuesto if not unicodedata.combining(c))


def cargar_diccionario(
    ruta: Path = RUTA_DICCIONARIO, solo_incluidos: bool = True
) -> pd.DataFrame:
    """Carga el diccionario versionado. Por defecto omite los términos descartados."""
    diccionario = pd.read_csv(ruta, dtype=str).fillna("")
    faltantes = set(COLUMNAS_DICCIONARIO) - set(diccionario.columns)
    if faltantes:
        raise ValueError(f"Diccionario sin columnas {sorted(faltantes)}")
    diccionario["raiz"] = diccionario["raiz"].map(normalizar)
    if solo_incluidos:
        diccionario = diccionario[diccionario["estado"] == ESTADO_INCLUIDO]
    return diccionario.reset_index(drop=True)


def compilar_dimension(grupo: pd.DataFrame) -> tuple[re.Pattern, dict[str, pd.Series]]:
    """Un patrón por dimensión con un grupo nombrado por término, para saber cuál coincidió.

    Las raíces largas van primero para que una coincidencia prefiera el término
    más específico cuando dos raíces comparten prefijo.

    Convención de la columna `raiz`: se envuelve como \\b(?:raiz)\\w*, de modo que una
    raíz cubre las variantes morfológicas. Para exigir palabra exacta, la raíz termina
    en \\b (p. ej. `horas?\\b` no captura «horario»).
    """
    ordenado = grupo.sort_values("raiz", key=lambda s: s.str.len(), ascending=False)
    filas: dict[str, pd.Series] = {}
    partes = []
    for indice, (_, fila) in enumerate(ordenado.iterrows()):
        etiqueta = f"t{indice}"
        filas[etiqueta] = fila
        # La raíz va en grupo propio: sin él, un `|` interno dejaría el \b y el \w*
        # pegados solo a la primera y la última alternativa
        partes.append(rf"(?P<{etiqueta}>\b(?:{fila['raiz']})\w*)")
    return re.compile("|".join(partes)), filas


@lru_cache(maxsize=1024)
def patron_nombre(nombre: str) -> re.Pattern | None:
    """Patrón que reconoce menciones del nombre del establecimiento en el texto.

    Acepta cualquier subsecuencia contigua de al menos `TOKENS_MINIMOS_NOMBRE`
    tokens, de la más larga a la más corta, para tolerar que la reseña use el
    nombre abreviado. Un nombre de un solo token no genera patrón: sería
    indistinguible de la mención del producto.
    """
    tokens = [t for t in re.split(r"\W+", normalizar(nombre)) if t]
    if len(tokens) < TOKENS_MINIMOS_NOMBRE:
        return None
    subsecuencias = [
        r"\W+".join(re.escape(t) for t in tokens[inicio : inicio + largo])
        for largo in range(len(tokens), TOKENS_MINIMOS_NOMBRE - 1, -1)
        for inicio in range(len(tokens) - largo + 1)
    ]
    return re.compile(rf"\b(?:{'|'.join(subsecuencias)})\b")


@lru_cache(maxsize=256)
def _patron_contexto(patron: str, modo: str) -> re.Pattern:
    # El veto previo se ancla al final del texto que precede a la coincidencia
    if modo == MODO_VETA_PREVIA:
        return re.compile(rf"(?:{patron})$")
    return re.compile(patron)


def _solapa(span: tuple[int, int], spans: list[tuple[int, int]]) -> bool:
    inicio, fin = span
    return any(inicio < fin_veto and fin > inicio_veto for inicio_veto, fin_veto in spans)


def _ventana(texto: str, inicio: int, fin: int) -> str:
    """Entorno de la coincidencia, recortado a la oración que la contiene."""
    izquierda = texto[max(0, inicio - VENTANA_CONTEXTO) : inicio]
    derecha = texto[fin : fin + VENTANA_CONTEXTO]
    corte_izquierdo = max(izquierda.rfind(c) for c in DELIMITADORES_ORACION)
    if corte_izquierdo != -1:
        izquierda = izquierda[corte_izquierdo + 1 :]
    cortes_derechos = [pos for pos in (derecha.find(c) for c in DELIMITADORES_ORACION) if pos != -1]
    if cortes_derechos:
        derecha = derecha[: min(cortes_derechos)]
    return izquierda + texto[inicio:fin] + derecha


def veta_contexto(texto: str, coincidencia: re.Match, patron: str, modo: str) -> bool:
    """Decide si el contexto invalida esta coincidencia, según el modo declarado."""
    if not patron or not modo:
        return False
    compilado = _patron_contexto(patron, modo)
    if modo == MODO_VETA_POSTERIOR:
        return bool(compilado.match(texto, coincidencia.end()))
    if modo == MODO_VETA_PREVIA:
        return bool(compilado.search(texto[: coincidencia.start()]))
    if modo == MODO_REQUIERE:
        return not compilado.search(_ventana(texto, *coincidencia.span()))
    raise ValueError(f"modo_contexto desconocido: {modo!r}")


def ocurrencias(
    texto: str, nombre: str, patron: re.Pattern, filas: dict[str, pd.Series]
) -> list[dict]:
    """Coincidencias de una dimensión en un texto, cada una con su estado de veto."""
    texto_norm = normalizar(texto)
    if not texto_norm:
        return []
    spans_veto = spans_nombre(texto_norm, nombre)
    salida = []
    for coincidencia in patron.finditer(texto_norm):
        fila = filas[coincidencia.lastgroup]
        contexto_veta = veta_contexto(
            texto_norm, coincidencia, fila["patron_contexto"], fila["modo_contexto"]
        )
        if _solapa(coincidencia.span(), spans_veto):
            estado = VETADA_NOMBRE
        elif contexto_veta:
            estado = VETADA_CONTEXTO
        else:
            estado = CONTADA
        salida.append(
            {
                "termino": fila["termino"],
                "coincidencia": coincidencia.group(),
                "estado": estado,
                "inicio": coincidencia.start(),
            }
        )
    return salida


def spans_nombre(texto_norm: str, nombre: str) -> list[tuple[int, int]]:
    """Tramos del texto normalizado ocupados por menciones del nombre del establecimiento."""
    if not isinstance(nombre, str) or not nombre.strip():
        return []
    patron = patron_nombre(nombre)
    if patron is None:
        return []
    return [m.span() for m in patron.finditer(texto_norm)]


def _serie_nombres(textos: pd.Series, nombres: pd.Series | None) -> pd.Series:
    if nombres is None:
        return pd.Series("", index=textos.index)
    return nombres.reindex(textos.index).fillna("")


def aplicar_diccionario(
    textos: pd.Series, diccionario: pd.DataFrame, nombres: pd.Series | None = None
) -> pd.DataFrame:
    """Binaria por dimensión, más los términos contados y los vetados de cada reseña."""
    nombres = _serie_nombres(textos, nombres)
    salida = pd.DataFrame(index=textos.index)
    for dimension, grupo in diccionario.groupby("dimension"):
        patron, filas = compilar_dimension(grupo)
        contados, vetados = [], []
        for texto, nombre in zip(textos, nombres, strict=True):
            encontradas = ocurrencias(texto, nombre, patron, filas)
            contados.append([o["coincidencia"] for o in encontradas if o["estado"] == CONTADA])
            vetados.append([o["coincidencia"] for o in encontradas if o["estado"] != CONTADA])
        salida[dimension] = [bool(c) for c in contados]
        salida[f"{dimension}_terminos"] = ["|".join(dict.fromkeys(c)) for c in contados]
        salida[f"{dimension}_vetados"] = ["|".join(dict.fromkeys(v)) for v in vetados]
    return salida


def detalle_ocurrencias(
    textos: pd.Series,
    diccionario: pd.DataFrame,
    nombres: pd.Series | None = None,
    identificadores: pd.Series | None = None,
) -> pd.DataFrame:
    """Tabla larga de una fila por coincidencia, para auditar los vetos."""
    nombres = _serie_nombres(textos, nombres)
    claves = (
        identificadores
        if identificadores is not None
        else pd.Series(textos.index, index=textos.index)
    )
    filas_salida = []
    for dimension, grupo in diccionario.groupby("dimension"):
        patron, filas = compilar_dimension(grupo)
        for clave, texto, nombre in zip(claves, textos, nombres, strict=True):
            for encontrada in ocurrencias(texto, nombre, patron, filas):
                filas_salida.append({"clave": clave, "dimension": dimension, **encontrada})
    return pd.DataFrame(filas_salida)
