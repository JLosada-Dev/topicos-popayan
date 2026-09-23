import pandas as pd
import pytest

from src.config import DIMENSIONES
from src.diccionario import (
    aplicar_diccionario,
    cargar_diccionario,
    normalizar,
    patron_nombre,
)


@pytest.fixture(scope="module")
def diccionario():
    return cargar_diccionario()


def dimensiones_de(textos, diccionario, nombres=None):
    serie_nombres = None if nombres is None else pd.Series(nombres)
    salida = aplicar_diccionario(pd.Series(textos), diccionario, serie_nombres)
    return [
        {d for d in DIMENSIONES if fila[d]}
        for _, fila in salida.iterrows()
    ]


def test_normalizar():
    assert normalizar("SALPICÓN Payanés") == "salpicon payanes"
    assert normalizar(None) == ""


def test_solo_carga_terminos_incluidos(diccionario):
    assert (diccionario["estado"] == "incluido").all()
    assert set(diccionario["dimension"]) == set(DIMENSIONES)


def test_detecta_dimensiones_basicas(diccionario):
    detectadas = dimensiones_de(
        ["la comida estaba deliciosa", "la atención fue excelente"], diccionario
    )
    assert "comida" in detectadas[0]
    assert "servicio" in detectadas[1]


def test_una_clausula_puede_activar_varias_dimensiones(diccionario):
    (detectadas,) = dimensiones_de(["comida rica y precio muy alto"], diccionario)
    assert {"comida", "precio"} <= detectadas


def test_una_clausula_puede_no_activar_ninguna(diccionario):
    (detectadas,) = dimensiones_de(["volveremos la próxima semana"], diccionario)
    assert detectadas == set()


def test_las_raices_cubren_variantes_morfologicas(diccionario):
    singular, plural = dimensiones_de(
        ["el mesero fue amable", "los meseros fueron amables"], diccionario
    )
    assert "servicio" in singular
    assert "servicio" in plural


def test_marcador_local_no_activa_ninguna_dimension(diccionario):
    # `local` esta excluido del diccionario, asi que el marcador es inerte
    (detectadas,) = dimensiones_de(["[LOCAL] [LOCAL] [LOCAL]"], diccionario)
    assert detectadas == set()


def test_veta_por_nombre_del_establecimiento(diccionario):
    sin_veto = dimensiones_de(["fuimos a la casa del té"], diccionario)[0]
    con_veto = dimensiones_de(
        ["fuimos a la casa del té"], diccionario, ["La casa del té popayán"]
    )[0]
    assert con_veto <= sin_veto


def test_patron_nombre_exige_dos_tokens():
    assert patron_nombre("Carantanta") is None
    assert patron_nombre("La Cosecha") is not None


def test_es_insensible_a_mayusculas_y_tildes(diccionario):
    con, sin = dimensiones_de(["El SALPICÓN estaba rico", "el salpicon estaba rico"], diccionario)
    assert con == sin
    assert "patrimonio" in con
