"""Búsqueda de fragmentos por consulta libre, con dos representaciones.

**TF-IDF** compara palabras: recupera fragmentos que contienen los mismos términos que
la consulta. Es inmediato y no necesita cargar nada pesado, pero no reconoce sinónimos.

**Embeddings** compara significado: el modelo sitúa consulta y fragmentos en un espacio
donde la cercanía es semántica, así que «demora» recupera «tardaron una hora» aunque no
compartan ninguna palabra. A cambio hay que cargar el modelo, lo que tarda unos segundos
la primera vez de cada sesión.

El modelo se carga de forma **diferida**: solo cuando el usuario elige ese método, para
que el arranque del panel no lo pague.
"""

import time

import numpy as np
import pandas as pd
import streamlit as st
from scipy import sparse

from app import datos
from src.config import DATOS_PROCESADOS
from src.embeddings import MODELO_EMBEDDINGS, PREFIJOS, rutas
from src.preparacion import texto_para_ctfidf

TFIDF = "TF-IDF (coincidencia de palabras)"
EMBEDDINGS = "Embeddings (significado)"

CONSULTAS_EJEMPLO = (
    "comida en mal estado",
    "demora en la atención",
    "cobro incorrecto",
    "comida típica payanesa",
    "horarios desactualizados",
    "buen lugar para ir en familia",
)

# Por debajo de esto la coincidencia es ruido, no un resultado
SIMILITUD_MINIMA = 1e-6


ARCHIVOS_TFIDF = ("tfidf_matriz.npz", "tfidf_vocabulario.csv", "tfidf_indice.csv")


def falta_tfidf() -> bool:
    return any(not (DATOS_PROCESADOS / n).exists() for n in ARCHIVOS_TFIDF)


def hay_embeddings() -> bool:
    """Si la búsqueda por significado se puede ofrecer en este despliegue.

    Necesita `sentence-transformers`, que arrastra torch: más de 1 GB instalado. En
    local está; en Streamlit Community Cloud no cabe en la memoria disponible, así que
    allí el explorador ofrece solo TF-IDF y lo dice en pantalla.
    """
    ruta_matriz, _ = rutas(MODELO_EMBEDDINGS)
    if not ruta_matriz.exists():
        return False
    try:
        import sentence_transformers  # noqa: F401
    except ImportError:
        return False
    return True


def precargar_embeddings() -> None:
    """Fuerza la carga del modelo dentro del spinner, no en mitad de la búsqueda."""
    _modelo_embeddings()
    _matriz_embeddings()


# ------------------------------------------------------------------- TF-IDF
@st.cache_resource
def _recursos_tfidf():
    """Matriz normalizada, vocabulario con su idf y el analizador de texto."""
    from sklearn.feature_extraction.text import TfidfVectorizer

    from src.topicos import MIN_DF_VECTORIZADOR, PATRON_TOKEN, RANGO_NGRAMAS

    matriz = sparse.load_npz(DATOS_PROCESADOS / "tfidf_matriz.npz").tocsr()
    vocabulario = pd.read_csv(DATOS_PROCESADOS / "tfidf_vocabulario.csv")
    indice = pd.read_csv(DATOS_PROCESADOS / "tfidf_indice.csv")["fragmento_id"]

    # El analizador no necesita estar ajustado: depende solo de los parámetros
    analizador = TfidfVectorizer(
        ngram_range=RANGO_NGRAMAS, min_df=MIN_DF_VECTORIZADOR, token_pattern=PATRON_TOKEN
    ).build_analyzer()
    posiciones = dict(zip(vocabulario["termino"], vocabulario["indice"]))
    return matriz, posiciones, vocabulario["idf"].to_numpy(), analizador, indice


def vector_consulta(consulta: str):
    """Vector TF-IDF de la consulta, con el mismo peso que los documentos.

    Se replica a mano lo que haría `transform`: contar términos, aplicar `sublinear_tf`,
    multiplicar por el idf guardado y normalizar. Así el archivo no queda atado a una
    versión concreta de scikit-learn.
    """
    _, posiciones, idf, analizador, _ = _recursos_tfidf()
    terminos = analizador(texto_para_ctfidf(consulta))
    presentes = [posiciones[t] for t in terminos if t in posiciones]
    if not presentes:
        return None, terminos

    cuenta = np.bincount(presentes, minlength=len(idf)).astype(float)
    usados = cuenta > 0
    pesos = np.zeros_like(cuenta)
    pesos[usados] = (1 + np.log(cuenta[usados])) * idf[usados]
    norma = np.linalg.norm(pesos)
    return (pesos / norma if norma else None), terminos


def buscar_tfidf(consulta: str, k: int) -> tuple[pd.DataFrame, float, list[str]]:
    matriz, _, _, _, indice = _recursos_tfidf()
    inicio = time.perf_counter()
    vector, terminos = vector_consulta(consulta)
    if vector is None:
        return pd.DataFrame(), time.perf_counter() - inicio, terminos
    similitudes = matriz @ vector
    resultado = _mejores(similitudes, indice, k)
    return resultado, time.perf_counter() - inicio, terminos


# --------------------------------------------------------------- Embeddings
@st.cache_resource(show_spinner=False)
def _modelo_embeddings():
    """El modelo, cargado una sola vez por sesión. Solo se invoca si hace falta."""
    from src.embeddings import cargar_modelo

    return cargar_modelo(MODELO_EMBEDDINGS)


@st.cache_resource
def _matriz_embeddings():
    """Embeddings normalizados, para que el coseno sea un producto punto."""
    ruta_matriz, ruta_indice = rutas(MODELO_EMBEDDINGS)
    matriz = np.load(ruta_matriz)
    indice = pd.read_csv(ruta_indice)["fragmento_id"]
    return matriz / np.linalg.norm(matriz, axis=1, keepdims=True), indice


def buscar_embeddings(consulta: str, k: int) -> tuple[pd.DataFrame, float]:
    matriz, indice = _matriz_embeddings()
    inicio = time.perf_counter()
    modelo = _modelo_embeddings()
    prefijo = PREFIJOS.get(MODELO_EMBEDDINGS, "")
    vector = modelo.encode([prefijo + consulta], convert_to_numpy=True)[0]
    vector = vector / np.linalg.norm(vector)
    return _mejores(matriz @ vector, indice, k), time.perf_counter() - inicio


# ------------------------------------------------------------------ Comunes
def _mejores(similitudes: np.ndarray, indice: pd.Series, k: int) -> pd.DataFrame:
    """Los k fragmentos más parecidos, con sus datos para mostrar."""
    orden = np.argsort(-similitudes)[: k * 2]
    orden = [i for i in orden if similitudes[i] > SIMILITUD_MINIMA][:k]
    if not orden:
        return pd.DataFrame()

    marco = datos.fragmentos().set_index("fragmento_id")
    topicos = datos.topicos().set_index("topico_id")
    filas = []
    for posicion in orden:
        identificador = indice.iloc[posicion]
        fragmento = marco.loc[identificador]
        topico = int(fragmento["topico"])
        etiqueta = topicos.loc[topico] if topico in topicos.index else None
        filas.append({
            "similitud": round(float(similitudes[posicion]), 3),
            "texto": fragmento["texto"],
            "topico": f"T{topico}" if etiqueta is not None else "sin asignar",
            "tema": etiqueta["tema"] if etiqueta is not None else "—",
            "rating": int(fragmento["rating"]),
            "establecimiento": fragmento["establecimiento"],
        })
    return pd.DataFrame(filas)
