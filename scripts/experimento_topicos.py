"""Banco de experimentos: negación, modelo de embeddings, rejilla y atípicos."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd  # noqa: E402

from src.config import DATOS_PROCESADOS  # noqa: E402
from src.embeddings import MODELO_E5, MODELO_MINILM, obtener  # noqa: E402
from src.experimentos import metricas  # noqa: E402
from src.topicos import ATIPICO, ajustar, reducir_atipicos  # noqa: E402

FRAGMENTOS = DATOS_PROCESADOS / "fragmentos.csv"


def corrida(fragmentos, embeddings, min_topic_size, min_samples=None, etiqueta=""):
    modelo, asignaciones = ajustar(fragmentos, embeddings, min_topic_size, min_samples)
    copia = fragmentos.copy()
    copia["topico"] = asignaciones
    return modelo, copia, metricas(modelo, copia, embeddings, etiqueta)


def imprimir(m):
    print(
        f"  {m['config']:<26} topicos={m['n_topicos']:>3}  atipicos={m['pct_atipicos']:>5}%  "
        f"eta2_rating={m['eta2_rating']:.3f} (nulo {m['eta2_rating_nulo']:.3f}, "
        f"exceso {m['eta2_rating'] - m['eta2_rating_nulo']:+.3f})  "
        f"basura={m['n_basura_largo']:>2}  duplic={m['n_topicos_duplicados']:>3}  "
        f"mayor={m['pct_topico_mayor']:>4}% (r={m['rating_topico_mayor']:.2f})"
    )


def paso1(fragmentos):
    print("\n### PASO 1 — negación corregida, mismo modelo y parámetros\n")
    emb, info = obtener(fragmentos, MODELO_MINILM)
    modelo, asignado, m = corrida(fragmentos, emb, 30, etiqueta="minilm mts=30")
    imprimir(m)

    print("\n  Tópicos con marca de negación en sus términos:")
    negaciones = {"no", "ni", "sin", "nada", "nunca", "jamás", "ningún", "ninguna", "tampoco"}
    for topico in sorted(asignado["topico"].unique()):
        if topico == ATIPICO:
            continue
        terminos = [t for t, _ in (modelo.get_topic(topico) or [])][:10]
        if not any(set(t.split()) & negaciones for t in terminos):
            continue
        sub = asignado[asignado["topico"] == topico]
        print(f"    T{topico:<3} n={len(sub):<4} rating={sub['rating'].mean():.2f}  {', '.join(terminos[:8])}")
    return emb, asignado, modelo





def paso2(fragmentos):
    print("\n### PASO 2 — comparación de modelos de embeddings\n")
    resultados = []
    # Se iguala la granularidad: eta2 crece con el numero de topicos, asi que hay que
    # comparar a un numero parecido de topicos, no al mismo min_topic_size
    for nombre, apodo, tamanos in [
        (MODELO_MINILM, "minilm", [30]),
        (MODELO_E5, "e5-small", [30, 15, 8, 5]),
    ]:
        emb, info = obtener(fragmentos, nombre)
        print(f"  {apodo}: dim={info['dimension']} origen={info['origen']} seg={info['segundos']}")
        for tamano in tamanos:
            _, _, m = corrida(fragmentos, emb, tamano, etiqueta=f"{apodo} mts={tamano}")
            resultados.append(m)
    print()
    for m in resultados:
        imprimir(m)
    return resultados


def paso3(fragmentos):
    print("\n### PASO 3 — rejilla de parámetros con MiniLM\n")
    emb, _ = obtener(fragmentos, MODELO_MINILM)
    resultados = []
    for tamano in (20, 30, 50):
        for min_samples in (None, tamano // 2):
            etiqueta = f"mts={tamano} ms={min_samples if min_samples else 'def'}"
            _, asignado, m = corrida(fragmentos, emb, tamano, min_samples, etiqueta)
            resultados.append(m)
            imprimir(m)
    print("\n  Tópicos basura por longitud (mediana <= 30 caracteres):")
    for m in resultados:
        print(f"    {m['config']:<20} {m['topicos_basura']}")
    return resultados


MEJOR_MTS, MEJOR_MS = 30, 15

# Los fragmentos ya asignados estan a coseno 0,676 de su centroide en promedio. Un
# umbral justo por debajo exige que un atipico encaje tan bien como uno tipico.
UMBRAL_ELEGIDO = 0.65


def paso4(fragmentos):
    print(f"\n### PASO 4 — reducción de atípicos sobre mts={MEJOR_MTS} ms={MEJOR_MS}\n")
    emb, _ = obtener(fragmentos, MODELO_MINILM)
    modelo, asignado, antes = corrida(fragmentos, emb, MEJOR_MTS, MEJOR_MS, "antes")
    imprimir(antes)

    previos = asignado["topico"].to_numpy().copy()
    print("\n  barrido de umbral:")
    for umbral in (0.3, 0.5, 0.6, 0.65, 0.7):
        prueba = asignado.copy()
        prueba["topico"] = reducir_atipicos(modelo, asignado, emb, umbral)
        reasignados = int(((previos == ATIPICO) & (prueba["topico"] != ATIPICO)).sum())
        m = metricas(modelo, prueba, emb, f"umbral={umbral}")
        print(
            f"    umbral={umbral:<5} reasignados={reasignados:>5}  "
            f"atípicos={m['pct_atipicos']:>5}%  mayor={m['pct_topico_mayor']:>5}%"
        )

    print(f"\n  elegido: {UMBRAL_ELEGIDO}\n")
    asignado["topico"] = reducir_atipicos(modelo, asignado, emb, UMBRAL_ELEGIDO)
    modelo.update_topics(
        asignado["texto_limpio"].fillna("").tolist(),
        topics=asignado["topico"].tolist(),
        vectorizer_model=modelo.vectorizer_model,
    )
    despues = metricas(modelo, asignado, emb, "después")
    imprimir(despues)

    movidos = asignado[(previos == ATIPICO) & (asignado["topico"] != ATIPICO)]
    print(f"\n  reasignados: {len(movidos)} de {(previos == ATIPICO).sum()} atípicos")
    print("\n  10 ejemplos reasignados, con los términos de su tópico nuevo:")
    for fila in movidos.sample(10, random_state=42).itertuples(index=False):
        terminos = [x for x, _ in (modelo.get_topic(fila.topico) or [])][:6]
        print(f"    -> T{fila.topico}  [{', '.join(terminos)}]")
        print(f"       {fila.texto[:110]}")
    return modelo, asignado, despues


def paso5(fragmentos):
    print("\n### PASO 5 — diagnóstico del largo mínimo (no se cambia todavía)\n")
    emb_total, _ = obtener(fragmentos, MODELO_MINILM)
    # Subir el minimo solo elimina clausulas; las que quedan son identicas, asi que
    # basta filtrar la tabla y quedarse con sus embeddings
    for minimo in (10, 20, 25):
        mascara = (fragmentos["largo_caracteres"] >= minimo).to_numpy()
        sub = fragmentos[mascara].reset_index(drop=True)
        perdidos = len(fragmentos) - len(sub)
        resenas = sub["review_id"].nunique()
        _, _, m = corrida(sub, emb_total[mascara], MEJOR_MTS, MEJOR_MS, f"largo>={minimo}")
        imprimir(m)
        print(
            f"      fragmentos {len(sub)} (pierde {perdidos}, {100*perdidos/len(fragmentos):.1f}%)"
            f"  reseñas {resenas} (pierde {fragmentos['review_id'].nunique() - resenas})"
        )


def paso6(fragmentos):
    print("\n### PASO 6 — atípicos y dimensiones, configuración final\n")
    emb, _ = obtener(fragmentos, MODELO_MINILM)
    modelo, asignado, _ = corrida(fragmentos, emb, MEJOR_MTS, MEJOR_MS, "final")
    asignado["topico"] = reducir_atipicos(modelo, asignado, emb, UMBRAL_ELEGIDO)

    es_atipico = asignado["topico"] == ATIPICO
    print(f"  atípicos tras la reducción: {es_atipico.sum()} ({100*es_atipico.mean():.1f}%)")
    for n_dim, grupo in asignado.groupby(asignado["n_dim"].clip(upper=2)):
        etiqueta = {0: "n_dim = 0", 1: "n_dim = 1", 2: "n_dim >= 2"}[n_dim]
        print(f"    {etiqueta}: {100*(grupo['topico'] == ATIPICO).mean():>5.1f}% atípico  (n={len(grupo)})")

    sin_dim = asignado[es_atipico & (asignado["n_dim"] == 0)]
    print(f"\n  atípicos con n_dim = 0: {len(sin_dim)}")
    print("\n  20 ejemplos:")
    for fila in sin_dim.sample(20, random_state=11).itertuples(index=False):
        print(f"    ({fila.largo_caracteres:>3} car., rating {fila.rating})  {fila.texto[:96]}")
    return modelo, asignado


PASOS = {"1": paso1, "2": paso2, "3": paso3, "4": paso4, "5": paso5, "6": paso6}

if __name__ == "__main__":
    fragmentos = pd.read_csv(FRAGMENTOS)
    for clave in sys.argv[1:] or sorted(PASOS):
        PASOS[clave](fragmentos)
