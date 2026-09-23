from src.texto import (
    limpiar_resena,
    normalizar_espacios,
    plegar,
    quitar_emojis,
    quitar_urls,
)


def test_plegar_quita_tildes_y_baja_a_minusculas():
    assert plegar("Salpicón PAYANÉS") == "salpicon payanes"


def test_plegar_conserva_la_longitud():
    for texto in ["Salpicón", "Café ñoño", "ÁÉÍÓÚü", "sin tildes"]:
        assert len(plegar(texto)) == len(texto), texto


def test_plegar_alinea_indices_con_el_original():
    texto = "El Fogón de la Abuela sirve pipián"
    plegado = plegar(texto)
    inicio = plegado.index("fogon")
    assert texto[inicio : inicio + 5] == "Fogón"


def test_quitar_urls():
    assert "http" not in quitar_urls("Miren https://ejemplo.com/foto aqui")
    assert "www" not in quitar_urls("Visiten www.ejemplo.com ya")


def test_quitar_emojis():
    assert quitar_emojis("Excelente 👍👍 comida 🍽️").strip().startswith("Excelente")
    assert "👍" not in quitar_emojis("Excelente 👍")


def test_normalizar_espacios():
    assert normalizar_espacios("  hola   que \n\n tal  ") == "hola que tal"


def test_limpiar_resena_conserva_los_separadores_de_clausula():
    # Los saltos y <br> son cortes de clausula: no deben desaparecer antes de segmentar
    limpio = limpiar_resena("Comida buena\nServicio lento<br>Precio alto")
    assert "\n" in limpio
    assert "<br>" in limpio


def test_limpiar_resena_no_string():
    assert limpiar_resena(None) == ""
