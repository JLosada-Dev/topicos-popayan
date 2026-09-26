"""Dashboard de resultados.

    uv run streamlit run app/main.py

Solo lee de `data/processed/`. No recalcula nada ni carga el modelo de BERTopic, así
que arranca en segundos y no necesita GPU ni descargar modelos.
"""

import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import datos, presentacion, secciones  # noqa: E402

SECCIONES = {
    "Presentación": presentacion.presentacion,
    "Resumen": secciones.resumen,
    "Temas": secciones.temas,
    "Tópicos": secciones.topicos,
    "Contraste con el diccionario": secciones.contraste,
    "Explorador": secciones.explorador,
}


def main() -> None:
    st.set_page_config(page_title="Tópicos · Popayán", page_icon="🍽️", layout="wide")

    ausentes = datos.faltantes()
    if ausentes:
        st.error(
            "Faltan archivos en `data/processed/`: " + ", ".join(f"`{n}`" for n in ausentes)
        )
        st.markdown(
            "Genera los resultados antes de abrir el dashboard. El orden de los scripts "
            "está en el README, en la sección «Notebooks»."
        )
        return

    with st.sidebar:
        st.title("Tópicos en reseñas gastronómicas de Popayán")
        st.caption(
            "Trabajo final de Text & Web Analytics · Especialización en Data Analytics "
            "para Marketing Digital, FUP"
        )
        eleccion = st.radio("Sección", list(SECCIONES), label_visibility="collapsed",
                            key="seccion")
        st.divider()
        st.caption(
            "Los resultados están calculados de antemano: este panel solo los muestra. "
            "El detalle metodológico está en `docs/bitacora.md` y "
            "`docs/decisiones_metodologicas.md`."
        )

    SECCIONES[eleccion]()


if __name__ == "__main__":
    main()
