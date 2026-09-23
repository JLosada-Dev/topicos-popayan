import pandas as pd

from src.preparacion import texto_para_ctfidf
from src.stopwords import STOPWORDS_ES, STOPWORDS_PROPIAS
from src.texto import MARCADOR_LOCAL


def test_pasa_a_minusculas_y_quita_puntuacion():
    assert texto_para_ctfidf("¡Comida DELICIOSA, excelente!") == "comida deliciosa excelente"


def test_quita_stopwords_del_espanol():
    limpio = texto_para_ctfidf("la comida de el restaurante estaba buena").split()
    assert not (set(limpio) & STOPWORDS_ES)
    assert "comida" in limpio


def test_quita_la_lista_propia():
    limpio = texto_para_ctfidf("el mejor restaurante de Popayan").split()
    assert not (set(limpio) & STOPWORDS_PROPIAS)


def test_conserva_las_palabras_que_nombran_dimensiones():
    limpio = texto_para_ctfidf("la comida y el servicio y el ambiente y el precio").split()
    assert {"comida", "servicio", "ambiente", "precio"} <= set(limpio)


def test_quita_el_marcador_sin_dejar_la_palabra_local():
    limpio = texto_para_ctfidf(f"{MARCADOR_LOCAL} tiene buena carne")
    assert "local" not in limpio.split()
    assert "carne" in limpio.split()


def test_conserva_tildes_y_enie():
    assert texto_para_ctfidf("salpicón payanés con ñame") == "salpicón payanés ñame"


def test_descarta_palabras_de_dos_letras_o_menos():
    assert texto_para_ctfidf("ir ya al bar") == "bar"


def test_texto_sin_contenido_queda_vacio():
    assert texto_para_ctfidf("de la y el") == ""


def test_conserva_las_negaciones_aunque_sean_cortas():
    # «no» invierte el sentido: sin ella el c-TF-IDF etiqueta un topico con su contrario
    assert texto_para_ctfidf("No lo recomiendo") == "no recomiendo"
    assert texto_para_ctfidf("ni sin nada nunca jamás tampoco ningún") != ""


def test_la_negacion_distingue_fragmentos_opuestos():
    assert texto_para_ctfidf("No lo recomiendo") != texto_para_ctfidf("Lo recomiendo")
