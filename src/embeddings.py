"""Embeddings de los fragmentos.

Se calculan sobre `texto`, que es el fragmento enmascarado con `[LOCAL]` pero por lo
demás natural: conserva mayúsculas, tildes y stopwords. `texto_limpio` NO se usa aquí,
solo en el c-TF-IDF.

El cálculo es lo costoso del pipeline, así que se guarda en disco junto a un índice de
`fragmento_id` en el mismo orden. Ese índice es lo que permite realinear la matriz con
el CSV de fragmentos más adelante sin depender del orden de las filas.
"""

import time

import numpy as np
import pandas as pd

from src.config import DATOS_PROCESADOS, SEMILLA

MODELO_MINILM = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
MODELO_E5 = "intfloat/multilingual-e5-small"
MODELO_EMBEDDINGS = MODELO_MINILM

# Los modelos e5 esperan un prefijo de tarea. Para agrupamiento, que es simétrico, su
# documentación indica usar "query: " en ambos lados.
PREFIJOS = {MODELO_E5: "query: "}

COLUMNA_TEXTO = "texto"
COLUMNA_ID = "fragmento_id"

LOTE = 64


def _apodo(nombre_modelo: str) -> str:
    return nombre_modelo.split("/")[-1]


def rutas(nombre_modelo: str = MODELO_EMBEDDINGS) -> tuple:
    """Archivo de matriz y de índice para un modelo dado."""
    apodo = _apodo(nombre_modelo)
    return (
        DATOS_PROCESADOS / f"embeddings_{apodo}.npy",
        DATOS_PROCESADOS / f"embeddings_{apodo}_indice.csv",
    )


def cargar_modelo(nombre: str = MODELO_EMBEDDINGS):
    """Modelo de sentence-transformers, en MPS si está disponible."""
    import torch
    from sentence_transformers import SentenceTransformer

    dispositivo = "mps" if torch.backends.mps.is_available() else "cpu"
    return SentenceTransformer(nombre, device=dispositivo)


def calcular(
    textos: list[str], nombre_modelo: str = MODELO_EMBEDDINGS, modelo=None
) -> tuple[np.ndarray, float]:
    """Matriz de embeddings y segundos que tomó calcularla."""
    modelo = modelo or cargar_modelo(nombre_modelo)
    prefijo = PREFIJOS.get(nombre_modelo, "")
    entradas = [prefijo + t for t in textos] if prefijo else textos
    inicio = time.perf_counter()
    matriz = modelo.encode(
        entradas,
        batch_size=LOTE,
        show_progress_bar=False,
        convert_to_numpy=True,
        normalize_embeddings=False,
    )
    return matriz, time.perf_counter() - inicio


def obtener(
    fragmentos: pd.DataFrame,
    nombre_modelo: str = MODELO_EMBEDDINGS,
    recalcular: bool = False,
) -> tuple[np.ndarray, dict]:
    """Embeddings alineados con `fragmentos`, leídos de disco si ya existen.

    Devuelve la matriz en el orden de `fragmentos`, no en el orden en que se guardó:
    el realineado va por `fragmento_id`, así que el CSV puede reordenarse sin romper
    la correspondencia.
    """
    ruta_matriz, ruta_indice = rutas(nombre_modelo)
    esperados = fragmentos[COLUMNA_ID]

    if ruta_matriz.exists() and ruta_indice.exists() and not recalcular:
        matriz = np.load(ruta_matriz)
        indice = pd.read_csv(ruta_indice)[COLUMNA_ID]
        if set(indice) == set(esperados):
            posicion = pd.Series(range(len(indice)), index=indice)
            return matriz[posicion.reindex(esperados).to_numpy()], {
                "modelo": nombre_modelo,
                "origen": "disco",
                "segundos": 0.0,
                "dimension": int(matriz.shape[1]),
                "filas": int(matriz.shape[0]),
            }

    matriz, segundos = calcular(fragmentos[COLUMNA_TEXTO].tolist(), nombre_modelo)
    ruta_matriz.parent.mkdir(parents=True, exist_ok=True)
    np.save(ruta_matriz, matriz)
    esperados.to_frame(COLUMNA_ID).to_csv(ruta_indice, index=False)
    return matriz, {
        "modelo": nombre_modelo,
        "origen": "calculado",
        "segundos": round(segundos, 1),
        "dimension": int(matriz.shape[1]),
        "filas": int(matriz.shape[0]),
        "semilla": SEMILLA,
    }
