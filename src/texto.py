"""Limpieza y normalización de texto.

Separado de `preparacion` porque son utilidades sin estado, reutilizables por el
resto de las etapas.
"""

import re
import unicodedata

MARCADOR_LOCAL = "[LOCAL]"

PATRON_URL = re.compile(r"(?:https?://|www\.)\S+", re.IGNORECASE)

# Emojis, pictogramas, banderas, dingbats y los modificadores que los acompañan
PATRON_EMOJI = re.compile(
    "[\U0001f000-\U0001faff☀-➿⬀-⯿️‍\U0001f1e6-\U0001f1ff]"
)

PATRON_ESPACIOS = re.compile(r"\s+")


def plegar(texto: str) -> str:
    """Minúsculas y sin tildes, conservando la longitud carácter a carácter.

    A diferencia de `diccionario.normalizar`, el plegado va carácter a carácter para
    que los índices del resultado coincidan con los del texto de entrada. Eso permite
    buscar sobre la versión plegada y reemplazar sobre el texto original.
    """
    if not isinstance(texto, str):
        return ""
    salida = []
    for caracter in texto:
        base = "".join(
            c for c in unicodedata.normalize("NFD", caracter) if not unicodedata.combining(c)
        )
        # Si el plegado no da exactamente un carácter (ligaduras, tildes sueltas) se
        # conserva el original, para no desalinear los índices
        salida.append(base.lower() if len(base) == 1 else caracter.lower())
    return "".join(salida)


def quitar_urls(texto: str) -> str:
    return PATRON_URL.sub(" ", texto)


def quitar_emojis(texto: str) -> str:
    return PATRON_EMOJI.sub(" ", texto)


def normalizar_espacios(texto: str) -> str:
    """Colapsa cualquier corrida de espacios, tabuladores o saltos en un espacio."""
    return PATRON_ESPACIOS.sub(" ", texto).strip()


def limpiar_resena(texto: str) -> str:
    """Limpieza previa a la segmentación: URLs y emojis.

    Los saltos de línea y las etiquetas `<br>` NO se tocan aquí: son separadores de
    cláusula y colapsarlos antes de segmentar perdería esos cortes. Los espacios se
    normalizan después, ya sobre cada fragmento.
    """
    if not isinstance(texto, str):
        return ""
    return quitar_emojis(quitar_urls(texto))
