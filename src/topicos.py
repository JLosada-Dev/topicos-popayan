"""Modelado de tópicos con BERTopic.

Dos textos, dos papeles:

- Los **embeddings** vienen de `texto` (el fragmento natural, enmascarado). Son los que
  definen la geometría: UMAP y HDBSCAN trabajan sobre ellos.
- El **c-TF-IDF** corre sobre `texto_limpio` (minúsculas, sin stopwords). Solo nombra
  los tópicos ya formados; no influye en el agrupamiento.

Este módulo es la corrida diagnóstica: parámetros razonables, sin optimizar.
"""

import numpy as np
import pandas as pd

from src.config import DATOS_PROCESADOS, SEMILLA

# CONFIGURACION DEFINITIVA, congelada el 2026-09-22 tras la rejilla de la bitacora.
# `min_samples = 15` evita el cajon negativo que aparecia con min_cluster_size = 50.
MIN_TOPIC_SIZE = 30
MIN_SAMPLES = 15
N_COMPONENTES_UMAP = 5
N_VECINOS_UMAP = 15
DISTANCIA_MINIMA_UMAP = 0.0
METRICA_UMAP = "cosine"

RANGO_NGRAMAS = (1, 2)
MIN_DF_VECTORIZADOR = 2
# Exige al menos dos caracteres y admite apostrofos y guiones internos
PATRON_TOKEN = r"(?u)\b\w[\w'-]+\b"

# BERTopic solo deja `[A-Za-z0-9 ]` en sus documentos cuando `language == "english"`
# (bertopic/_bertopic.py, `_preprocess_text`), lo que convertiria «atención» en
# «atencin». Cualquier otro valor desactiva ese filtro.
IDIOMA = "multilingual"

ATIPICO = -1


def construir_modelo(min_topic_size: int = MIN_TOPIC_SIZE, min_samples: int | None = None):
    """BERTopic con UMAP sembrado, para que la corrida sea reproducible."""
    from bertopic import BERTopic
    from bertopic.vectorizers import ClassTfidfTransformer
    from sklearn.feature_extraction.text import CountVectorizer
    from umap import UMAP

    reductor = UMAP(
        n_neighbors=N_VECINOS_UMAP,
        n_components=N_COMPONENTES_UMAP,
        min_dist=DISTANCIA_MINIMA_UMAP,
        metric=METRICA_UMAP,
        random_state=SEMILLA,
    )
    # Las stopwords ya se quitaron al construir `texto_limpio`; aqui solo se exige que
    # el termino aparezca en dos fragmentos, para podar el ruido de escritura
    vectorizador = CountVectorizer(
        ngram_range=RANGO_NGRAMAS,
        min_df=MIN_DF_VECTORIZADOR,
        token_pattern=PATRON_TOKEN,
    )
    agrupador = None
    if min_samples is not None:
        from hdbscan import HDBSCAN

        agrupador = HDBSCAN(
            min_cluster_size=min_topic_size,
            min_samples=min_samples,
            metric="euclidean",
            cluster_selection_method="eom",
            prediction_data=True,
        )

    return BERTopic(
        language=IDIOMA,
        hdbscan_model=agrupador,
        umap_model=reductor,
        vectorizer_model=vectorizador,
        ctfidf_model=ClassTfidfTransformer(reduce_frequent_words=True),
        min_topic_size=min_topic_size,
        calculate_probabilities=False,
        verbose=False,
    )


def ajustar(
    fragmentos: pd.DataFrame,
    embeddings: np.ndarray,
    min_topic_size: int = MIN_TOPIC_SIZE,
    min_samples: int | None = None,
):
    """Ajusta el modelo y devuelve (modelo, asignaciones).

    `texto_limpio` puede quedar vacío en unos pocos fragmentos; se pasa una cadena
    vacía y el vectorizador simplemente no aporta términos para ellos.
    """
    modelo = construir_modelo(min_topic_size, min_samples)
    documentos = fragmentos["texto_limpio"].fillna("").tolist()
    asignaciones, _ = modelo.fit_transform(documentos, embeddings=embeddings)
    return modelo, np.asarray(asignaciones)


def resumen_topicos(modelo, fragmentos: pd.DataFrame, n_terminos: int = 10) -> pd.DataFrame:
    """Una fila por tópico: tamaño, términos, calificación media y concentración."""
    filas = []
    for topico in sorted(fragmentos["topico"].unique()):
        sub = fragmentos[fragmentos["topico"] == topico]
        terminos = [t for t, _ in (modelo.get_topic(topico) or [])][:n_terminos]
        conteo_local = sub["establecimiento"].value_counts()
        filas.append(
            {
                "topico": topico,
                "n": len(sub),
                "porcentaje": round(100 * len(sub) / len(fragmentos), 1),
                "terminos": ", ".join(terminos),
                "rating_medio": round(sub["rating"].mean(), 2),
                "pct_1_2_estrellas": round(100 * (sub["rating"] <= 2).mean(), 1),
                "largo_mediano": int(sub["largo_caracteres"].median()),
                "local_top": conteo_local.index[0] if len(conteo_local) else "",
                "pct_local_top": round(100 * conteo_local.iloc[0] / len(sub), 1),
                "n_locales": int(sub["place_id"].nunique()),
                "dimension_dominante": _dimension_dominante(sub),
            }
        )
    return pd.DataFrame(filas)


def _dimension_dominante(sub: pd.DataFrame) -> str:
    """Dimensión del diccionario más frecuente en el tópico, con su cobertura."""
    from src.config import DIMENSIONES

    tasas = {d: sub[d].mean() for d in DIMENSIONES}
    mejor = max(tasas, key=tasas.get)
    if tasas[mejor] == 0:
        return "—"
    return f"{mejor} ({100 * tasas[mejor]:.0f}%)"


def representativos(modelo, fragmentos: pd.DataFrame, topico: int, n: int = 3) -> list[str]:
    """Fragmentos que BERTopic considera más representativos del tópico."""
    documentos = modelo.get_representative_docs(topico) or []
    limpio_a_texto = dict(zip(fragmentos["texto_limpio"].fillna(""), fragmentos["texto"]))
    return [limpio_a_texto.get(d, d) for d in documentos[:n]]


# Umbral de la reduccion de atipicos: similitud minima al centroide del topico para
# aceptar la reasignacion. Por debajo, el fragmento se queda sin asignar.
# 0,65 queda justo bajo el coseno medio de los fragmentos ya asignados a su centroide
# (0,676): un atipico se reasigna solo si encaja tan bien como uno tipico.
UMBRAL_REDUCCION = 0.65


def reducir_atipicos(
    modelo, fragmentos: pd.DataFrame, embeddings: np.ndarray, umbral: float = UMBRAL_REDUCCION
) -> np.ndarray:
    """Reasigna atípicos por cercanía al centroide del tópico, sin reajustar el modelo.

    Los que no alcanzan el umbral siguen en -1: la reduccion no debe forzar a que todo
    quede asignado, porque parte de los atípicos son texto sin contenido temático.
    """
    documentos = fragmentos["texto_limpio"].fillna("").tolist()
    return np.asarray(
        modelo.reduce_outliers(
            documentos,
            fragmentos["topico"].tolist(),
            strategy="embeddings",
            embeddings=embeddings,
            threshold=umbral,
        )
    )


RUTA_MODELO = DATOS_PROCESADOS / "modelo_bertopic"

# Fusiones aplicadas a mano. No se usa un umbral automatico de similitud entre
# centroides: en este corpus los pares mas similares lo son por compartir registro
# evaluativo, no tema. El umbral relativo (0,72) fundiria 24 topicos en el 45 % del
# corpus, y aun a 0,90 juntaria el elogio generico con el tema de compartir en familia.
# Solo se fusiona el par que es el mismo asunto: referente gastronomico de la ciudad.
FUSIONES = [[21, 30]]


def ajustar_definitivo(fragmentos: pd.DataFrame, embeddings: np.ndarray):
    """Modelo con la configuración congelada, ya con los atípicos reducidos."""
    modelo, asignaciones = ajustar(fragmentos, embeddings, MIN_TOPIC_SIZE, MIN_SAMPLES)
    copia = fragmentos.copy()
    copia["topico_sin_reduccion"] = asignaciones
    copia["topico"] = asignaciones
    copia["topico"] = reducir_atipicos(modelo, copia, embeddings, UMBRAL_REDUCCION)
    actualizar_representacion(modelo, copia)
    if FUSIONES:
        modelo.merge_topics(copia["texto_limpio"].fillna("").tolist(), FUSIONES)
        copia["topico"] = modelo.topics_
    return modelo, copia


def actualizar_representacion(modelo, fragmentos: pd.DataFrame) -> None:
    """Recalcula el c-TF-IDF tras cambiar las asignaciones."""
    modelo.update_topics(
        fragmentos["texto_limpio"].fillna("").tolist(),
        topics=fragmentos["topico"].tolist(),
        vectorizer_model=modelo.vectorizer_model,
    )


def guardar_modelo(modelo, ruta=RUTA_MODELO) -> None:
    from src.embeddings import MODELO_EMBEDDINGS

    ruta.parent.mkdir(parents=True, exist_ok=True)
    modelo.save(
        str(ruta),
        serialization="safetensors",
        save_ctfidf=True,
        save_embedding_model=MODELO_EMBEDDINGS,
    )


def cargar_modelo_guardado(ruta=RUTA_MODELO):
    from bertopic import BERTopic

    return BERTopic.load(str(ruta))
