"""Colores compartidos por las figuras del informe y el dashboard.

Módulo sin dependencias a propósito: lo importan tanto `src/figuras.py`, que usa
matplotlib, como `app/secciones.py`, que corre en Streamlit Community Cloud donde
matplotlib no está instalado.

Rampa secuencial azul de la guía de visualización. El orden va de claro a oscuro, que
en escala de grises se traduce en una progresión monótona de luminosidad.
"""

RAMPA = {
    100: "#cde2fb", 150: "#b7d3f6", 200: "#9ec5f4", 250: "#86b6ef",
    300: "#6da7ec", 350: "#5598e7", 400: "#3987e5", 450: "#2a78d6",
    500: "#256abf", 550: "#1c5cab", 600: "#184f95", 650: "#104281", 700: "#0d366b",
}

SUPERFICIE = "#fcfcfb"
TINTA = "#0b0b0b"
TINTA_SECUNDARIA = "#52514e"
TINTA_TENUE = "#8a8984"
REJILLA = "#e3e2de"

# Pasos separados a proposito: en gris quedan a unos 64 puntos de luminosidad entre si
PASOS_CATEGORIA = (RAMPA[650], RAMPA[400], RAMPA[200])
TRAMAS = ("", "///", "...")

# Orden fijo de los tres tipos de tema, para que el color signifique lo mismo en toda
# figura y en toda pantalla
ORDEN_TIPOS = ("atributo_esquema", "valoracion_global", "atributo_nuevo")
COLOR_POR_TIPO = dict(zip(ORDEN_TIPOS, PASOS_CATEGORIA))
