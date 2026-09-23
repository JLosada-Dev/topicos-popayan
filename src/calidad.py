"""Indicadores de calidad del modelo de tópicos.

Coherencia `c_v` (Röder et al., 2015) con gensim, que es la medida de referencia en la
literatura de modelado de tópicos y la que permite comparar con trabajos publicados.
Se acompaña de `c_npmi`, que es más conservadora y no tiene el sesgo optimista que se
le reprocha a `c_v`.

La diversidad es la proporción de palabras distintas entre las principales de todos los
tópicos (Dieng et al., 2020): 1,0 significa que ningún término se repite entre tópicos.
"""

import numpy as np
import pandas as pd

from src.topicos import ATIPICO

N_TERMINOS_CALIDAD = 10


def terminos_principales(modelo, topicos: list[int], n: int = N_TERMINOS_CALIDAD):
    """Términos de cada tópico, como listas de palabras sueltas.

    Los bigramas del c-TF-IDF se parten en sus palabras: las medidas de coherencia
    trabajan sobre el vocabulario de los documentos, donde el bigrama no existe.
    """
    salida = []
    for topico in topicos:
        palabras, vistas = [], set()
        for termino, _ in (modelo.get_topic(topico) or []):
            for palabra in termino.split():
                if palabra not in vistas:
                    vistas.add(palabra)
                    palabras.append(palabra)
            if len(palabras) >= n:
                break
        salida.append(palabras[:n])
    return salida


def coherencia(modelo, fragmentos: pd.DataFrame, medidas=("c_v", "c_npmi")) -> dict:
    """Coherencia de los tópicos sobre el mismo texto que alimentó el c-TF-IDF."""
    from gensim.corpora import Dictionary
    from gensim.models import CoherenceModel

    textos = [t.split() for t in fragmentos["texto_limpio"].fillna("") if t.strip()]
    diccionario = Dictionary(textos)
    topicos = sorted(t for t in fragmentos["topico"].unique() if t != ATIPICO)
    palabras = terminos_principales(modelo, topicos)
    # Un termino que no esta en el vocabulario rompe el calculo
    palabras = [[p for p in grupo if p in diccionario.token2id] for grupo in palabras]
    palabras = [g for g in palabras if len(g) >= 2]

    resultado = {"n_topicos_evaluados": len(palabras)}
    for medida in medidas:
        # processes=1: el paralelismo de gensim usa multiprocessing y falla cuando el
        # script no se ejecuta desde un archivo con guarda __main__
        modelo_coherencia = CoherenceModel(
            topics=palabras,
            texts=textos,
            dictionary=diccionario,
            coherence=medida,
            processes=1,
        )
        por_topico = modelo_coherencia.get_coherence_per_topic()
        resultado[medida] = round(float(np.mean(por_topico)), 4)
        resultado[f"{medida}_por_topico"] = dict(
            zip([t for t, g in zip(topicos, palabras) if g], [round(v, 3) for v in por_topico])
        )
    return resultado


def diversidad(modelo, fragmentos: pd.DataFrame, n: int = N_TERMINOS_CALIDAD) -> float:
    """Proporción de palabras únicas entre las principales de todos los tópicos."""
    topicos = sorted(t for t in fragmentos["topico"].unique() if t != ATIPICO)
    palabras = [p for grupo in terminos_principales(modelo, topicos, n) for p in grupo]
    return round(len(set(palabras)) / len(palabras), 4) if palabras else 0.0
