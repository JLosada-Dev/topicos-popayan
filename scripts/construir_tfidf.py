"""Precalcula la matriz TF-IDF que usa el explorador del dashboard.

Se guarda la matriz ya normalizada, el vocabulario con su idf y el índice de
`fragmento_id`. En vez de serializar el objeto `TfidfVectorizer`, que ata el archivo a
una versión concreta de scikit-learn, se guardan sus dos piezas: vocabulario e idf. El
dashboard reconstruye el vector de la consulta a partir de ellas.

Mismo preprocesamiento que el c-TF-IDF del modelo: se parte de `texto_limpio`
—minúsculas, sin puntuación, sin stopwords y con las negaciones conservadas— con
unigramas y bigramas.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from scipy import sparse  # noqa: E402
from sklearn.feature_extraction.text import TfidfVectorizer  # noqa: E402

from src.config import DATOS_PROCESADOS  # noqa: E402
from src.topicos import MIN_DF_VECTORIZADOR, PATRON_TOKEN, RANGO_NGRAMAS  # noqa: E402

RUTA_MATRIZ = DATOS_PROCESADOS / "tfidf_matriz.npz"
RUTA_VOCABULARIO = DATOS_PROCESADOS / "tfidf_vocabulario.csv"
RUTA_INDICE = DATOS_PROCESADOS / "tfidf_indice.csv"


def construir_vectorizador() -> TfidfVectorizer:
    """Los mismos parámetros que el c-TF-IDF del modelo, para que sean comparables."""
    return TfidfVectorizer(
        ngram_range=RANGO_NGRAMAS,
        min_df=MIN_DF_VECTORIZADOR,
        token_pattern=PATRON_TOKEN,
        norm="l2",
        sublinear_tf=True,
    )


def main() -> None:
    fragmentos = pd.read_csv(DATOS_PROCESADOS / "fragmentos.csv")
    documentos = fragmentos["texto_limpio"].fillna("").tolist()

    vectorizador = construir_vectorizador()
    matriz = vectorizador.fit_transform(documentos)

    vocabulario = pd.DataFrame({
        "termino": vectorizador.get_feature_names_out(),
        "idf": vectorizador.idf_,
    })
    vocabulario["indice"] = range(len(vocabulario))

    RUTA_MATRIZ.parent.mkdir(parents=True, exist_ok=True)
    sparse.save_npz(RUTA_MATRIZ, matriz.tocsr())
    vocabulario.to_csv(RUTA_VOCABULARIO, index=False)
    fragmentos[["fragmento_id"]].to_csv(RUTA_INDICE, index=False)

    densidad = matriz.nnz / (matriz.shape[0] * matriz.shape[1])
    print(f"matriz: {matriz.shape[0]} fragmentos × {matriz.shape[1]} términos")
    print(f"  no ceros: {matriz.nnz:,} (densidad {100 * densidad:.3f} %)".replace(",", "."))
    print(f"  unigramas: {sum(1 for t in vocabulario['termino'] if ' ' not in t)}")
    print(f"  bigramas:  {sum(1 for t in vocabulario['termino'] if ' ' in t)}")
    print(f"  tamaño en disco: {RUTA_MATRIZ.stat().st_size / 1024:.0f} KB")
    vacios = int((np.asarray(matriz.sum(axis=1)).ravel() == 0).sum())
    print(f"  fragmentos sin ningún término del vocabulario: {vacios}")


if __name__ == "__main__":
    main()
