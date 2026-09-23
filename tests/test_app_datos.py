import pandas as pd
import pytest

from app import datos
from src.config import DIMENSIONES


def test_no_faltan_archivos():
    assert datos.faltantes() == []


def test_topicos_trae_lo_que_muestra_el_panel():
    tabla = datos.topicos()
    assert len(tabla) == 41
    for columna in ("terminos", "local_top", "pct_local_top", "n_locales",
                    "dimension_dominante", "rating", "polaridad", "tipo"):
        assert columna in tabla.columns, columna
    # El panel formatea estos campos sin comprobar nulos
    assert not tabla[["terminos", "local_top", "rating", "n"]].isna().any().any()


def test_todo_topico_tiene_fragmentos():
    marco = datos.fragmentos()
    for identificador in datos.topicos()["topico_id"]:
        assert (marco["topico"] == identificador).any(), identificador


def test_temas_cubren_todos_los_topicos():
    temas = datos.temas()
    assert len(temas) == 14
    assert int(temas["n_topicos"].sum()) == len(datos.topicos())
    assert int(temas["fragmentos"].sum()) == int((datos.fragmentos()["topico"] != datos.ATIPICO).sum())


def test_cada_tema_de_un_topico_existe_en_la_tabla_de_temas():
    assert set(datos.topicos()["tema"]) == set(datos.temas()["tema"])


def test_ami_trae_su_linea_base():
    tabla = datos.ami()
    fila = tabla.iloc[0]
    assert 0 < fila["ami"] < 1
    assert abs(fila["nulo"]) < 0.01          # el azar debe rondar cero
    assert fila["exceso"] == pytest.approx(fila["ami"] - fila["nulo"], abs=1e-3)


def test_dispersion_cubre_las_seis_dimensiones():
    assert set(datos.dispersion()["dimension"]) == set(DIMENSIONES)


def test_cruzada_tiene_una_fila_por_topico():
    cruzada = datos.cruzada()
    assert set(cruzada["topico"]) == set(datos.topicos()["topico_id"])
    for dimension in DIMENSIONES:
        assert cruzada[dimension].between(0, 100).all(), dimension


def test_indicadores_de_calidad_disponibles():
    for nombre in ("c_v", "c_npmi", "diversidad_top10"):
        assert isinstance(datos.indicador(nombre), float)


def test_resumen_de_atipicos():
    resumen = datos.resumen_atipicos()
    assert resumen["n"] > 0
    assert 0 < resumen["pct"] < 100
    # El hallazgo que el panel afirma: los sin asignar son mas criticos que el corpus
    assert resumen["rating"] < datos.fragmentos()["rating"].mean()


def test_nombre_largo_incluye_subtema_solo_si_existe():
    tabla = datos.topicos().set_index("topico_id")
    con_subtema = tabla.loc[15]
    sin_subtema = tabla.loc[0]
    assert datos.nombre_largo({**con_subtema, "topico_id": 15}) == "T15 · comida / pizza"
    assert datos.nombre_largo({**sin_subtema, "topico_id": 0}) == "T0 · espera"


def test_las_figuras_que_muestra_existen():
    for nombre in ("04_embudo_corpus.png", "01_distribucion_por_tipo.png",
                   "03_mapa_topico_dimension.png"):
        assert datos.figura(nombre).exists(), nombre
