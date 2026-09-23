import numpy as np
import pytest

from app import busqueda

CONSULTA = "demora en la atención"


def test_la_matriz_tfidf_existe():
    assert not busqueda.falta_tfidf()


def test_recursos_tfidf_estan_alineados():
    matriz, posiciones, idf, _, indice = busqueda._recursos_tfidf()
    assert matriz.shape[0] == len(indice)
    assert matriz.shape[1] == len(idf) == len(posiciones)


def test_las_filas_de_la_matriz_estan_normalizadas():
    matriz, *_ = busqueda._recursos_tfidf()
    normas = np.sqrt(matriz.multiply(matriz).sum(axis=1)).A.ravel()
    # Hay 38 fragmentos sin ningun termino del vocabulario: su norma es cero
    assert np.allclose(normas[normas > 0], 1.0, atol=1e-6)


def test_vector_de_consulta_esta_normalizado():
    vector, terminos = busqueda.vector_consulta(CONSULTA)
    assert terminos
    assert vector is not None
    assert np.isclose(np.linalg.norm(vector), 1.0)


def test_consulta_sin_terminos_conocidos_no_rompe():
    vector, _ = busqueda.vector_consulta("xyzqw zzzz")
    assert vector is None
    tabla, segundos, _ = busqueda.buscar_tfidf("xyzqw zzzz", 5)
    assert tabla.empty
    assert segundos >= 0


def test_consulta_de_solo_stopwords_no_rompe():
    tabla, _, _ = busqueda.buscar_tfidf("de la y el", 5)
    assert tabla.empty


@pytest.mark.parametrize("consulta", busqueda.CONSULTAS_EJEMPLO)
def test_las_consultas_de_ejemplo_devuelven_algo(consulta):
    tabla, segundos, _ = busqueda.buscar_tfidf(consulta, 5)
    assert not tabla.empty, consulta
    assert segundos < 5


def test_el_ranking_viene_ordenado_y_acotado():
    tabla, _, _ = busqueda.buscar_tfidf(CONSULTA, 7)
    assert len(tabla) <= 7
    assert tabla["similitud"].is_monotonic_decreasing
    assert tabla["similitud"].between(0, 1).all()


def test_los_resultados_traen_los_datos_que_muestra_el_panel():
    tabla, _, _ = busqueda.buscar_tfidf(CONSULTA, 5)
    for columna in ("similitud", "texto", "topico", "tema", "rating", "establecimiento"):
        assert columna in tabla.columns, columna
    assert not tabla[list(tabla.columns)].isna().any().any()


def test_tfidf_recupera_por_coincidencia_de_palabra():
    tabla, _, _ = busqueda.buscar_tfidf("pipián", 5)
    assert tabla["texto"].str.contains("pipi", case=False).any()


def test_el_modelo_de_embeddings_no_se_carga_al_usar_tfidf(tmp_path):
    """La carga diferida es lo que mantiene rápido el arranque del panel.

    Va en un subproceso porque cualquier otra prueba del archivo pudo haber traído
    torch a memoria ya.
    """
    import subprocess
    import sys
    from pathlib import Path as Ruta

    guion = tmp_path / "comprobar.py"
    guion.write_text(
        "import sys\n"
        f"sys.path.insert(0, {str(Ruta.cwd())!r})\n"
        "from app import busqueda\n"
        "busqueda.buscar_tfidf('demora en la atención', 3)\n"
        "pesados = [m for m in ('torch', 'sentence_transformers') if m in sys.modules]\n"
        "print('PESADOS:' + ','.join(pesados))\n",
        encoding="utf-8",
    )
    salida = subprocess.run(
        [sys.executable, str(guion)], capture_output=True, text=True, check=True
    )
    linea = next(l for l in salida.stdout.splitlines() if l.startswith("PESADOS:"))
    assert linea == "PESADOS:", f"la búsqueda TF-IDF cargó {linea}"


def test_matriz_de_embeddings_normalizada_y_alineada():
    matriz, indice = busqueda._matriz_embeddings()
    assert matriz.shape[0] == len(indice)
    assert np.allclose(np.linalg.norm(matriz, axis=1), 1.0, atol=1e-5)
