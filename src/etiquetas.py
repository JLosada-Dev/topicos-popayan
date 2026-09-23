"""Estructura de dos niveles sobre los tópicos del modelo congelado.

La asignación es manual, hecha leyendo términos y fragmentos de cada tópico
(`docs/evidencia_topicos.md`). Se versiona aquí para que sea revisable y reversible:
el modelo no se toca.

`tipo` responde a si el tópico habla de un atributo del servicio gastronómico y, en
ese caso, si ese atributo está o no en el esquema de seis dimensiones a priori.
"""

import pandas as pd

ATRIBUTO_ESQUEMA = "atributo_esquema"
ATRIBUTO_NUEVO = "atributo_nuevo"
VALORACION_GLOBAL = "valoracion_global"

POSITIVA, NEGATIVA, MIXTA = "positiva", "negativa", "mixta"

# Cortes de polaridad sobre el rating medio del tópico
UMBRAL_POSITIVA = 4.2
UMBRAL_NEGATIVA = 2.5

# topico_id: (tema, subtema, tipo)
ASIGNACION = {
    0: ("espera", "", ATRIBUTO_ESQUEMA),
    1: ("servicio", "", ATRIBUTO_ESQUEMA),
    2: ("ambiente", "", ATRIBUTO_ESQUEMA),
    3: ("experiencia global", "", VALORACION_GLOBAL),
    4: ("comida", "", ATRIBUTO_ESQUEMA),
    5: ("recomendacion", "", VALORACION_GLOBAL),
    6: ("comida", "", ATRIBUTO_ESQUEMA),
    7: ("servicio", "", ATRIBUTO_ESQUEMA),
    8: ("ocasion de consumo", "", ATRIBUTO_NUEVO),
    9: ("referente en la ciudad", "", ATRIBUTO_NUEVO),
    10: ("precio", "", ATRIBUTO_ESQUEMA),
    11: ("comida", "presentacion y variedad", ATRIBUTO_ESQUEMA),
    12: ("referente en la ciudad", "", ATRIBUTO_NUEVO),
    13: ("comida", "", ATRIBUTO_ESQUEMA),
    14: ("comida", "", ATRIBUTO_ESQUEMA),
    15: ("comida", "pizza", ATRIBUTO_ESQUEMA),
    16: ("infraestructura y espacio", "", ATRIBUTO_NUEVO),
    17: ("patrimonio", "", ATRIBUTO_ESQUEMA),
    18: ("servicio", "", ATRIBUTO_ESQUEMA),
    19: ("patrimonio", "centro historico", ATRIBUTO_ESQUEMA),
    20: ("comida", "bebidas", ATRIBUTO_ESQUEMA),
    21: ("experiencia global", "", VALORACION_GLOBAL),
    22: ("comida", "hamburguesas", ATRIBUTO_ESQUEMA),
    23: ("servicio", "", ATRIBUTO_ESQUEMA),
    24: ("ocasion de consumo", "", ATRIBUTO_NUEVO),
    25: ("experiencia global", "", VALORACION_GLOBAL),
    26: ("comida", "carnes", ATRIBUTO_ESQUEMA),
    27: ("comida", "asiatica", ATRIBUTO_ESQUEMA),
    28: ("comida", "cafe", ATRIBUTO_ESQUEMA),
    29: ("comida", "cocina por origen", ATRIBUTO_ESQUEMA),
    30: ("comida", "postres", ATRIBUTO_ESQUEMA),
    31: ("intencion de volver", "", VALORACION_GLOBAL),
    32: ("experiencia global", "", VALORACION_GLOBAL),
    33: ("satisfaccion", "", VALORACION_GLOBAL),
    34: ("recomendacion", "", VALORACION_GLOBAL),
    35: ("comida", "pollo asado", ATRIBUTO_ESQUEMA),
    36: ("comida", "carta y menu", ATRIBUTO_ESQUEMA),
    37: ("experiencia global", "", VALORACION_GLOBAL),
    38: ("comida", "", ATRIBUTO_ESQUEMA),
    39: ("recomendacion", "", VALORACION_GLOBAL),
    40: ("medios de pago", "", ATRIBUTO_NUEVO),
}


def polaridad(rating_medio: float) -> str:
    if rating_medio >= UMBRAL_POSITIVA:
        return POSITIVA
    if rating_medio <= UMBRAL_NEGATIVA:
        return NEGATIVA
    return MIXTA


def etiquetar(fragmentos: pd.DataFrame) -> pd.DataFrame:
    """Una fila por tópico, con su tema, subtema, tipo, polaridad y cifras."""
    filas = []
    for topico, (tema, subtema, tipo) in sorted(ASIGNACION.items()):
        sub = fragmentos[fragmentos["topico"] == topico]
        rating = float(sub["rating"].mean())
        filas.append(
            {
                "topico_id": topico,
                "tema": tema,
                "subtema": subtema,
                "tipo": tipo,
                "polaridad": polaridad(rating),
                "n": len(sub),
                "pct_corpus": round(100 * len(sub) / len(fragmentos), 2),
                "rating": round(rating, 2),
                "pct_1_2_estrellas": round(100 * (sub["rating"] <= 2).mean(), 1),
            }
        )
    return pd.DataFrame(filas)
