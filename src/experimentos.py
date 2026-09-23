"""Métricas comparables entre corridas de BERTopic.

Las reglas de «tópico basura» y «tópico duplicado» se fijan aquí y no se tocan entre
experimentos: sirven para comparar configuraciones, no para juzgar un modelo en
abstracto.
"""

import numpy as np
import pandas as pd

from src.topicos import ATIPICO

# Un tópico cuyo fragmento mediano no llega a este largo agrupa por brevedad, no por
# tema: en la corrida diagnóstica esos tópicos mezclaban asuntos sin relación
LARGO_MEDIANO_BASURA = 30

# Dos tópicos se consideran redundantes por la similitud coseno de sus centroides en
# el espacio de embeddings, no por sus términos. En la corrida diagnóstica los pares
# claramente redundantes (T10/T37 «excelente servicio») compartían casi ningún bigrama
# —Jaccard 0,18— pero tenían coseno 0,90. El umbral es el percentil 99 de la
# distribución de pares de esa corrida.
COSENO_DUPLICADO = 0.85
JACCARD_DUPLICADO = 0.3
N_TERMINOS_COMPARADOS = 10


def eta_cuadrado_nulo(
    valores: pd.Series, grupos: pd.Series, repeticiones: int = 30, semilla: int = 42
) -> float:
    """eta² esperado por azar con esta misma partición.

    eta² crece mecánicamente con el número de grupos, así que el valor crudo no es
    comparable entre configuraciones con distinto número de tópicos. Permutar los
    valores deja intacto el tamaño de los grupos y da la referencia a descontar.
    """
    generador = np.random.default_rng(semilla)
    barajados = valores.to_numpy()
    return float(
        np.mean(
            [
                eta_cuadrado(pd.Series(generador.permutation(barajados), index=valores.index), grupos)
                for _ in range(repeticiones)
            ]
        )
    )


def eta_cuadrado(valores: pd.Series, grupos: pd.Series) -> float:
    """Proporción de varianza de `valores` explicada por `grupos`."""
    media = valores.mean()
    entre = sum(len(g) * (g.mean() - media) ** 2 for _, g in valores.groupby(grupos))
    total = ((valores - media) ** 2).sum()
    return float(entre / total) if total else 0.0


def terminos_por_topico(modelo, topicos: list[int]) -> dict[int, set[str]]:
    return {
        t: {termino for termino, _ in (modelo.get_topic(t) or [])[:N_TERMINOS_COMPARADOS]}
        for t in topicos
    }


def centroides(embeddings: np.ndarray, asignaciones: np.ndarray, topicos: list[int]):
    """Centroide normalizado de cada tópico en el espacio de embeddings."""
    matriz = np.vstack([embeddings[asignaciones == t].mean(axis=0) for t in topicos])
    return matriz / np.linalg.norm(matriz, axis=1, keepdims=True)


def pares_duplicados(
    embeddings: np.ndarray,
    asignaciones: np.ndarray,
    topicos: list[int],
    umbral: float = COSENO_DUPLICADO,
) -> list[tuple[int, int, float]]:
    """Pares de tópicos cuyos centroides superan el umbral de similitud."""
    if len(topicos) < 2:
        return []
    matriz = centroides(embeddings, asignaciones, topicos)
    similitud = matriz @ matriz.T
    pares = []
    for i, a in enumerate(topicos):
        for j, b in enumerate(topicos[i + 1 :], start=i + 1):
            if similitud[i, j] >= umbral:
                pares.append((a, b, round(float(similitud[i, j]), 3)))
    return pares


def umbral_relativo(
    embeddings: np.ndarray, semilla: int = 42, muestra: int = 2000, cuantil: float = 0.99
) -> float:
    """Umbral de duplicado calibrado al propio espacio del modelo.

    El coseno absoluto no se puede comparar entre modelos: e5 tiene un espacio
    anisótropo donde dos fragmentos cualesquiera ya están a coseno 0,84, mientras que
    MiniLM promedia 0,25. Se toma el percentil 99 de los pares de fragmentos del
    propio modelo, de modo que «duplicado» significa lo mismo en ambos.
    """
    generador = np.random.default_rng(semilla)
    filas = generador.choice(len(embeddings), min(muestra, len(embeddings)), replace=False)
    normalizados = embeddings[filas] / np.linalg.norm(embeddings[filas], axis=1, keepdims=True)
    similitud = normalizados @ normalizados.T
    return float(np.quantile(similitud[np.triu_indices_from(similitud, k=1)], cuantil))


def metricas(
    modelo, fragmentos: pd.DataFrame, embeddings: np.ndarray, etiqueta: str = ""
) -> dict:
    """Resumen comparable de una corrida."""
    asignados = fragmentos[fragmentos["topico"] != ATIPICO]
    topicos = sorted(asignados["topico"].unique())
    asignaciones = fragmentos["topico"].to_numpy()
    relativo = umbral_relativo(embeddings)
    pares = pares_duplicados(embeddings, asignaciones, topicos)
    pares_rel = pares_duplicados(embeddings, asignaciones, topicos, relativo)
    en_algun_par = {t for a, b, _ in pares_rel for t in (a, b)}

    # Un topico que acapara el corpus no se detecta con las otras medidas: en la
    # rejilla, mts=50 minimizaba eta2 justamente porque fundia todo lo negativo en un
    # solo cajon del 27 % unificado por polaridad, no por tema
    tamanos = asignados["topico"].value_counts()
    mayor = int(tamanos.iloc[0]) if len(tamanos) else 0

    largos = asignados.groupby("topico")["largo_caracteres"].median()
    basura = largos[largos <= LARGO_MEDIANO_BASURA].index.tolist()

    return {
        "config": etiqueta,
        "n_topicos": len(topicos),
        "pct_atipicos": round(100 * (fragmentos["topico"] == ATIPICO).mean(), 1),
        "eta2_rating": round(eta_cuadrado(asignados["rating"], asignados["topico"]), 3),
        "eta2_rating_nulo": round(
            eta_cuadrado_nulo(asignados["rating"], asignados["topico"]), 3
        ),
        "eta2_largo": round(
            eta_cuadrado(np.log1p(asignados["largo_caracteres"]), asignados["topico"]), 3
        ),
        "pct_topico_mayor": round(100 * mayor / len(fragmentos), 1),
        "rating_topico_mayor": round(
            float(asignados[asignados["topico"] == tamanos.index[0]]["rating"].mean()), 2
        ) if len(tamanos) else 0.0,
        "n_basura_largo": len(basura),
        "topicos_basura": basura,
        "umbral_relativo": round(relativo, 3),
        "n_pares_duplicados": len(pares_rel),
        "n_topicos_duplicados": len(en_algun_par),
        "n_duplicados_absoluto": len({t for a, b, _ in pares for t in (a, b)}),
        "pares": pares_rel,
    }
