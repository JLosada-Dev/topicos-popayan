"""Segmentación de reseñas en cláusulas.

Copiado de `src/sentimiento.py` del proyecto `reputacion-popayan`
(`CONECTORES_ADVERSATIVOS`, `SEPARADOR_CLAUSULA`, `LARGO_MINIMO_FRAGMENTO`,
`segmentar`). Se copia en vez de importarse porque aquel proyecto es de solo
lectura. La regla no se modifica: mantenerla idéntica es lo que permite comparar
resultados entre los dos trabajos.

La unidad es la cláusula: la oración, más los cortes en conectores adversativos.
El 19,4 % de las reseñas trae uno de esos conectores y son justamente donde el tono
cambia de signo dentro de una misma oración («un lugar pequeño pero con comida
deliciosa»). El conector se consume en el corte y no queda en ninguno de los dos
lados.
"""

import re

CONECTORES_ADVERSATIVOS = (
    r"pero|aunque|sin\s+embargo|no\s+obstante|eso\s+s[íi]|"
    r"lo\s+malo|lo\s+[úu]nico|mientras\s+que"
)
SEPARADOR_CLAUSULA = re.compile(
    rf"(?:<br\s*/?>|[.!?;¡¿]+|\n|,?\s+(?:{CONECTORES_ADVERSATIVOS})\b)+",
    re.IGNORECASE,
)

# Por debajo de este largo el fragmento no da señal
LARGO_MINIMO_FRAGMENTO = 10


def segmentar(texto: str) -> list[str]:
    """Divide una reseña en cláusulas, descartando los fragmentos demasiado cortos."""
    if not isinstance(texto, str):
        return []
    partes = (p.strip() for p in SEPARADOR_CLAUSULA.split(texto))
    return [p for p in partes if len(p) >= LARGO_MINIMO_FRAGMENTO]


def segmentar_sin_filtrar(texto: str) -> list[str]:
    """Cláusulas sin aplicar el largo mínimo, para contar cuántas se descartan."""
    if not isinstance(texto, str):
        return []
    return [p.strip() for p in SEPARADOR_CLAUSULA.split(texto) if p.strip()]
