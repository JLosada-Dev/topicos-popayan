from src.segmentacion import (
    LARGO_MINIMO_FRAGMENTO,
    segmentar,
    segmentar_sin_filtrar,
)


def test_corta_en_punto():
    assert segmentar("La comida deliciosa. El servicio muy lento.") == [
        "La comida deliciosa",
        "El servicio muy lento",
    ]


def test_corta_en_conector_adversativo_y_lo_consume():
    partes = segmentar("Un lugar pequeño pero con comida deliciosa")
    assert partes == ["Un lugar pequeño", "con comida deliciosa"]
    assert not any("pero" in p for p in partes)


def test_corta_en_todos_los_conectores():
    for conector in ["pero", "aunque", "sin embargo", "no obstante", "eso sí",
                     "lo malo", "lo único", "mientras que"]:
        texto = f"La comida buena {conector} el servicio lento"
        assert len(segmentar(texto)) == 2, conector


def test_corta_en_salto_de_linea_y_br():
    assert len(segmentar("La comida buena\nEl servicio lento")) == 2
    assert len(segmentar("La comida buena<br>El servicio lento")) == 2


def test_separadores_consecutivos_no_generan_vacios():
    assert segmentar("Comida deliciosa!!!... Servicio excelente") == [
        "Comida deliciosa",
        "Servicio excelente",
    ]


def test_descarta_fragmentos_cortos():
    assert segmentar("Comida muy deliciosa. Ok.") == ["Comida muy deliciosa"]


def test_largo_minimo_es_el_declarado():
    justo = "a" * LARGO_MINIMO_FRAGMENTO
    corto = "a" * (LARGO_MINIMO_FRAGMENTO - 1)
    assert segmentar(justo) == [justo]
    assert segmentar(corto) == []


def test_sin_filtrar_conserva_los_cortos():
    assert segmentar_sin_filtrar("Comida muy deliciosa. Ok.") == [
        "Comida muy deliciosa",
        "Ok",
    ]


def test_texto_no_string_devuelve_vacio():
    assert segmentar(None) == []
    assert segmentar(3.5) == []
