import pytest

from src.preparacion import (
    _es_distintiva,
    enmascarar_locales,
    patron_nombre_propio,
    patron_nombres_completos,
    patrones_para,
)
from src.texto import MARCADOR_LOCAL


@pytest.fixture(scope="module")
def patron_completos():
    return patron_nombres_completos(
        ["La Cosecha Parrillada", "El Fogón de la Abuela", "Plazoleta de Comidas"]
    )


def enmascarar(texto, propio, patron_completos=None):
    return enmascarar_locales(texto, patrones_para(propio, patron_completos))


def test_enmascara_el_nombre_propio():
    salida, n = enmascarar("Fui a La Cosecha Parrillada ayer", "La Cosecha Parrillada")
    assert salida == f"Fui a {MARCADOR_LOCAL} ayer"
    assert n == 1


def test_enmascara_el_nombre_propio_abreviado():
    salida, _ = enmascarar("La Cosecha tiene buena carne", "La Cosecha Parrillada")
    assert salida == f"{MARCADOR_LOCAL} tiene buena carne"


def test_es_insensible_a_mayusculas_y_tildes():
    salida, _ = enmascarar("fui a el fogon de la abuela", "El Fogón de la Abuela")
    assert salida == f"fui a {MARCADOR_LOCAL}"


def test_conserva_tildes_del_resto_del_texto():
    salida, _ = enmascarar(
        "En La Cosecha probé el salpicón payanés", "La Cosecha Parrillada"
    )
    assert "salpicón payanés" in salida


def test_no_enmascara_secuencias_solo_funcionales():
    # «de la», subsecuencia de «El Fogón de la Abuela», no debe tocar texto generico
    salida, n = enmascarar("la calidad de la comida es buena", "El Fogón de la Abuela")
    assert MARCADOR_LOCAL not in salida
    assert n == 0


def test_no_enmascara_secuencias_que_son_solo_termino_de_diccionario():
    # «de comidas», subsecuencia de «Plazoleta de Comidas», borraria la dimension comida
    salida, _ = enmascarar("amplia variedad de comidas", "Plazoleta de Comidas")
    assert MARCADOR_LOCAL not in salida


def test_otros_locales_solo_con_el_nombre_completo(patron_completos):
    propio = "Otro Restaurante Cualquiera"
    completo, _ = enmascarar("comimos en La Cosecha Parrillada", propio, patron_completos)
    assert MARCADOR_LOCAL in completo

    parcial, _ = enmascarar("una buena cosecha de café", propio, patron_completos)
    assert MARCADOR_LOCAL not in parcial


def test_nombre_de_un_solo_token_no_genera_patron():
    # «Carantanta» es a la vez local y plato patrimonial: no debe enmascararse
    assert patron_nombre_propio("Carantanta") is None
    salida, _ = enmascarar("pedimos carantanta con hogao", "Carantanta")
    assert MARCADOR_LOCAL not in salida


def test_tramos_solapados_se_fusionan_en_una_sola_marca():
    salida, n = enmascarar("La Cosecha Parrillada es buena", "La Cosecha Parrillada")
    assert salida.count(MARCADOR_LOCAL) == 1
    assert n == 1


def test_es_distintiva():
    assert not _es_distintiva(["de", "la"])
    assert not _es_distintiva(["de", "comidas"])
    assert _es_distintiva(["cosecha", "parrillada"])


def test_texto_vacio():
    assert enmascarar("", "La Cosecha Parrillada") == ("", 0)
    assert enmascarar(None, "La Cosecha Parrillada") == ("", 0)
