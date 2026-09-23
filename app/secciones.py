"""Las cuatro secciones del dashboard.

Cada indicador va acompañado de una línea que explica qué significa para alguien que no
conoce el detalle técnico. No hay gráficos decorativos: las únicas figuras son las tres
del informe, que aportan algo que la tabla no da.
"""

import pandas as pd
import streamlit as st

from app import datos
from src.config import DIMENSIONES

SEMILLA = 42
N_EJEMPLOS = 5

NOMBRE_TIPO = {
    "atributo_esquema": "Atributo del esquema a priori",
    "atributo_nuevo": "Atributo emergente",
    "valoracion_global": "Valoración global (sin atributo)",
}


def _nota(texto: str) -> None:
    """Línea explicativa bajo un indicador."""
    st.caption(texto)


def _ejemplos(sub: pd.DataFrame, n: int = N_EJEMPLOS) -> None:
    """Fragmentos de muestra, reproducibles, con sus dimensiones activas."""
    if sub.empty:
        st.info("No hay fragmentos para mostrar.")
        return
    muestra = sub.sample(min(n, len(sub)), random_state=SEMILLA)
    for fila in muestra.itertuples(index=False):
        activas = [d for d in DIMENSIONES if getattr(fila, d)]
        etiqueta = ", ".join(activas) if activas else "ninguna dimensión"
        st.markdown(f"> {fila.texto}")
        st.caption(f"{fila.rating}★ · {etiqueta} · {fila.establecimiento}")


# --------------------------------------------------------------------- Resumen
def resumen() -> None:
    st.header("Resumen")
    st.markdown(
        "Qué temas aparecen en las reseñas de Google Maps de establecimientos "
        "gastronómicos de Popayán, y hasta qué punto coinciden con las seis dimensiones "
        "con las que se suele evaluar la experiencia gastronómica."
    )

    marco = datos.fragmentos()
    tabla_topicos = datos.topicos()
    tabla_temas = datos.temas()
    atipicos = datos.resumen_atipicos()
    asignados = len(marco) - atipicos["n"]

    st.subheader("El corpus, paso a paso")
    _nota(
        "Cada reseña se parte en cláusulas. La unidad que se analiza es el fragmento, "
        "no la reseña completa, porque una misma reseña suele hablar de varias cosas."
    )
    columnas = st.columns(4)
    embudo = [
        ("Reseñas del corpus", "8.451", None),
        ("Aptas y en español", "2.430", "con texto, ≥ 50 caracteres y sin duplicados"),
        ("Fragmentos", f"{len(marco):,}".replace(",", "."), "2,4 por reseña en promedio"),
        ("Asignados a un tema", f"{asignados:,}".replace(",", "."),
         f"{100 * asignados / len(marco):.1f} % del total"),
    ]
    for columna, (titulo, valor, pie) in zip(columnas, embudo):
        columna.metric(titulo, valor)
        if pie:
            columna.caption(pie)

    st.subheader("Qué salió")
    columnas = st.columns(4)
    columnas[0].metric("Tópicos", len(tabla_topicos))
    columnas[0].caption("Grupos que encontró el modelo por sí solo")
    columnas[1].metric("Temas", len(tabla_temas))
    columnas[1].caption("Agrupación de esos tópicos, hecha a mano tras leerlos")

    valor_ami = datos.ami().iloc[0]
    columnas[2].metric("Acuerdo con el esquema (AMI)", f"{valor_ami['ami']:.2f}")
    columnas[2].caption("0 = ninguna coincidencia · 1 = coincidencia total")
    columnas[3].metric("Sin asignar", f"{atipicos['pct']:.1f} %")
    columnas[3].caption(f"{atipicos['n']} fragmentos que no encajaron en ningún grupo")

    st.markdown(
        f"**Cómo leerlo.** Un AMI de **{valor_ami['ami']:.2f}** indica un acuerdo "
        "*moderado*: los temas que emergen de las reseñas y las seis dimensiones "
        "tradicionales describen el mismo corpus, pero no son lo mismo. Hay una parte "
        "de lo que dicen los comensales que el esquema tradicional no recoge."
    )
    st.markdown(
        f"Los fragmentos sin asignar son más críticos que el resto: promedian "
        f"**{atipicos['rating']:.2f} estrellas** frente a {marco['rating'].mean():.2f} "
        f"del corpus completo. Lo que el método no agrupa tiende a ser negativo."
    )

    st.subheader("De dónde salen los fragmentos")
    st.image(str(datos.figura("04_embudo_corpus.png")))

    st.subheader("De qué hablan los fragmentos agrupados")
    _nota(
        "Tres clases: los que hablan de una de las seis dimensiones tradicionales, "
        "los que hablan de algo que el esquema no contempla, y los que no describen "
        "nada en concreto sino que dan un veredicto («recomendado», «volvería»)."
    )
    st.image(str(datos.figura("01_distribucion_por_tipo.png")))
    st.markdown(
        "**Un quinto del corpus agrupado no describe ningún atributo.** Son juicios "
        "sobre la experiencia, no descripciones de ella, y por eso no tienen con qué "
        "contrastarse frente al esquema de seis dimensiones."
    )


# ----------------------------------------------------------------------- Temas
def temas() -> None:
    st.header("Temas")
    st.markdown(
        "Los 41 tópicos del modelo, agrupados en 14 temas. La agrupación se hizo a mano "
        "después de leer los términos y los fragmentos de cada tópico."
    )

    tabla = datos.temas()
    tabla_topicos = datos.topicos()
    marco = datos.fragmentos()

    st.subheader("Los 14 temas")
    _nota(
        "Ordena haciendo clic en cualquier encabezado. «% del corpus» es sobre los "
        "fragmentos que sí quedaron agrupados. La polaridad sale de la calificación "
        "media: positiva si es 4,2 o más, negativa si es 2,5 o menos, mixta en medio."
    )
    vista = tabla[[
        "tema", "tipo", "n_topicos", "fragmentos", "pct_asignado",
        "rating", "pct_1_2_estrellas", "polaridad_dominante",
    ]].rename(columns={
        "tema": "Tema", "tipo": "Tipo", "n_topicos": "Tópicos",
        "fragmentos": "Fragmentos", "pct_asignado": "% del corpus",
        "rating": "Calificación media", "pct_1_2_estrellas": "% de 1-2★",
        "polaridad_dominante": "Polaridad",
    })
    vista["Tipo"] = vista["Tipo"].map(NOMBRE_TIPO)
    st.dataframe(vista, hide_index=True, width="stretch")

    st.subheader("Ver un tema en detalle")
    elegido = st.selectbox(
        "Tema", tabla.sort_values("fragmentos", ascending=False)["tema"],
        label_visibility="collapsed",
    )
    fila = tabla[tabla["tema"] == elegido].iloc[0]

    columnas = st.columns(4)
    columnas[0].metric("Fragmentos", int(fila["fragmentos"]))
    columnas[1].metric("Calificación media", f"{fila['rating']:.2f}")
    columnas[2].metric("% de 1-2★", f"{fila['pct_1_2_estrellas']:.1f} %")
    columnas[3].metric("Tópicos que lo componen", int(fila["n_topicos"]))

    st.caption(f"Tipo: {NOMBRE_TIPO[fila['tipo']]} · polaridad {fila['polaridad_dominante']}")
    if fila["subtemas"]:
        st.caption(f"Subtemas: {fila['subtemas']}")

    st.markdown("**Tópicos que componen el tema**")
    del_tema = tabla_topicos[tabla_topicos["tema"] == elegido].sort_values("n", ascending=False)
    vista_topicos = del_tema[["topico_id", "subtema", "n", "rating",
                              "pct_1_2_estrellas", "terminos"]].rename(columns={
        "topico_id": "Tópico", "subtema": "Subtema", "n": "Fragmentos",
        "rating": "Calificación", "pct_1_2_estrellas": "% de 1-2★",
        "terminos": "Términos principales",
    })
    st.dataframe(vista_topicos, hide_index=True, width="stretch")

    st.markdown("**Fragmentos de ejemplo**")
    _nota("Muestra aleatoria reproducible de los fragmentos del tema.")
    _ejemplos(marco[marco["topico"].isin(del_tema["topico_id"])])


# --------------------------------------------------------------------- Tópicos
def topicos() -> None:
    st.header("Tópicos")
    st.markdown(
        "Cada tópico es un grupo que el modelo formó por su cuenta, reuniendo "
        "fragmentos que se parecen entre sí. Los términos los resume después un "
        "segundo cálculo, que busca las palabras propias de ese grupo y de ningún otro."
    )

    tabla = datos.topicos().sort_values("n", ascending=False)
    marco = datos.fragmentos()

    opciones = {datos.nombre_largo(f): int(f["topico_id"]) for _, f in tabla.iterrows()}
    elegido = st.selectbox("Tópico", list(opciones), label_visibility="collapsed")
    identificador = opciones[elegido]
    fila = tabla[tabla["topico_id"] == identificador].iloc[0]
    sub = marco[marco["topico"] == identificador]

    columnas = st.columns(4)
    columnas[0].metric("Fragmentos", int(fila["n"]))
    columnas[0].caption(f"{fila['pct_corpus']:.1f} % del corpus")
    columnas[1].metric("Calificación media", f"{fila['rating']:.2f}")
    columnas[1].caption(f"{fila['pct_1_2_estrellas']:.1f} % de reseñas de 1-2★")
    columnas[2].metric("Concentración", f"{fila['pct_local_top']:.0f} %")
    columnas[2].caption(f"en «{fila['local_top']}», de {int(fila['n_locales'])} locales")
    columnas[3].metric("Polaridad", fila["polaridad"].capitalize())
    columnas[3].caption(NOMBRE_TIPO[fila["tipo"]])

    st.markdown("**Términos principales**")
    _nota(
        "Las palabras más características del tópico frente a los demás. No son "
        "las más frecuentes, sino las más distintivas."
    )
    st.markdown(" · ".join(f"`{t.strip()}`" for t in str(fila["terminos"]).split(",")))

    columnas = st.columns(2)
    columnas[0].markdown(f"**Dimensión dominante:** {fila['dimension_dominante']}")
    columnas[0].caption(
        "Dimensión del diccionario que más aparece en los fragmentos del tópico, "
        "con el porcentaje que la activa."
    )
    sin_dimension = 100 * (sub["n_dim"] == 0).mean() if len(sub) else 0.0
    columnas[1].markdown(f"**Sin ninguna dimensión:** {sin_dimension:.0f} %")
    columnas[1].caption(
        "Fragmentos del tópico que el diccionario de dimensiones no reconoce. "
        "Cuanto más alto, más ajeno es el tópico al esquema tradicional."
    )

    if pd.notna(fila["c_v"]):
        st.caption(
            f"Coherencia del tópico (c_v): {fila['c_v']:.3f}. Mide si sus términos "
            "aparecen juntos en los mismos fragmentos; el promedio del modelo es "
            f"{datos.indicador('c_v'):.3f}."
        )

    st.markdown("**Cinco fragmentos de ejemplo**")
    _nota("Muestra aleatoria reproducible, no los fragmentos más típicos, para no "
          "dar una imagen más limpia de la real.")
    _ejemplos(sub)


# ------------------------------------------------------- Contraste diccionario
def contraste() -> None:
    st.header("Contraste con el esquema de seis dimensiones")
    st.markdown(
        "Las seis dimensiones —comida, servicio, precio, ambiente, tiempo de espera y "
        "patrimonio— se detectan con un diccionario de términos construido y validado "
        "en un trabajo anterior sobre el mismo corpus. Aquí se compara esa lectura "
        "con los tópicos que el modelo encontró sin conocerlas."
    )

    st.subheader("Qué dimensión activa cada tópico")
    _nota(
        "Cada celda es el porcentaje de fragmentos del tópico que menciona esa "
        "dimensión. Un tópico puede activar varias, porque las dimensiones no son "
        "excluyentes. Se muestran los 15 tópicos mayores."
    )
    st.image(str(datos.figura("03_mapa_topico_dimension.png")))

    with st.expander("Ver la tabla completa de los 41 tópicos"):
        vista = datos.cruzada().rename(columns={
            "topico": "Tópico", "tema": "Tema", "n": "Fragmentos", "sin_dim": "Sin dimensión",
            **{d: d.capitalize() for d in DIMENSIONES},
        })
        st.dataframe(vista, hide_index=True, width="stretch")

    st.subheader("Cuánto coinciden las dos lecturas")
    _nota(
        "El AMI compara dos formas de agrupar los mismos fragmentos. Vale 0 cuando "
        "coinciden lo que coincidirían dos agrupaciones al azar, y 1 cuando son "
        "idénticas. Se calcula solo sobre los fragmentos que activan exactamente una "
        "dimensión, que son los únicos con los que la comparación tiene sentido."
    )
    tabla_ami = datos.ami()
    principal = tabla_ami.iloc[0]

    columnas = st.columns(3)
    columnas[0].metric("AMI", f"{principal['ami']:.3f}")
    columnas[0].caption(f"sobre {int(principal['n'])} fragmentos")
    columnas[1].metric("Línea base (azar)", f"{principal['nulo']:.3f}")
    columnas[1].caption(f"media de {int(principal['repeticiones'])} permutaciones")
    columnas[2].metric("Diferencia", f"+{principal['exceso']:.3f}")
    columnas[2].caption("lo que el acuerdo supera al azar")

    st.markdown(
        "**Cómo leerlo.** La línea base se obtiene barajando las etiquetas de dimensión "
        "muchas veces: es el acuerdo que saldría por pura casualidad. Que el AMI real "
        f"esté **{principal['exceso']:.2f} puntos por encima** confirma que la "
        "coincidencia es real y no un artefacto. Pero un valor de "
        f"**{principal['ami']:.2f}**, lejos de 1, dice que **los temas emergentes no "
        "son una forma distinta de nombrar las seis dimensiones**: hay estructura "
        "compartida y hay estructura propia."
    )
    with st.expander("Ver las dos formas de calcularlo"):
        vista = tabla_ami.rename(columns={
            "base": "Base de cálculo", "n": "Fragmentos", "ami": "AMI", "ari": "ARI",
            "nulo": "Línea base", "sd_nulo": "Desv. línea base", "exceso": "Diferencia",
            "repeticiones": "Permutaciones",
        })
        st.dataframe(vista, hide_index=True, width="stretch")
        st.caption(
            "El ARI mide lo mismo contando pares de fragmentos en vez de información "
            "compartida. Que sea más bajo indica que un tópico suele repartirse entre "
            "varias dimensiones y una dimensión entre muchos tópicos."
        )

    st.subheader("En cuántos tópicos se reparte cada dimensión")
    _nota(
        "Si una dimensión tuviera su tópico propio, casi todos sus fragmentos estarían "
        "en uno solo. Cuanto más repartida, menos se parece esa dimensión a un tema "
        "que los comensales traten como una unidad."
    )
    vista = datos.dispersion().rename(columns={
        "dimension": "Dimensión", "fragmentos": "Fragmentos", "topicos": "Tópicos",
        "pct_en_el_mayor": "% en el tópico mayor",
        "pct_en_los_3_mayores": "% en los 3 mayores",
        "topico_principal": "Tópico principal", "tema_principal": "Tema de ese tópico",
    })
    st.dataframe(vista, hide_index=True, width="stretch")
    st.markdown(
        "**La espera es la única dimensión con correspondencia fuerte**: casi dos "
        "tercios de sus fragmentos caen en un mismo tópico. Es un asunto acotado y con "
        "vocabulario propio. **Comida es el caso opuesto**: se reparte en 38 tópicos y "
        "su tópico principal ni siquiera es de comida, sino de valoración global. Es la "
        "dimensión más grande y la menos específica: casi cualquier elogio la menciona."
    )


# ------------------------------------------------------------------ Explorador
def _resultados(tabla: pd.DataFrame, segundos: float, titulo: str, nota: str) -> None:
    """Un ranking, con su tiempo de respuesta."""
    st.markdown(f"**{titulo}**")
    st.caption(f"{nota} · {segundos * 1000:.0f} ms")
    if tabla.empty:
        st.info("Ningún fragmento coincide con la consulta.")
        return
    for fila in tabla.itertuples(index=False):
        st.markdown(f"> {fila.texto}")
        st.caption(
            f"similitud {fila.similitud:.3f} · {fila.topico} {fila.tema} · "
            f"{fila.rating}★ · {fila.establecimiento}"
        )


def explorador() -> None:
    from app import busqueda

    st.header("Explorador")
    st.markdown(
        "Busca fragmentos parecidos a lo que escribas. Sirve para comprobar qué hay en "
        "el corpus sobre un asunto concreto, incluso si ese asunto no llegó a formar un "
        "tópico propio."
    )

    if busqueda.falta_tfidf():
        st.error(
            "Falta la matriz TF-IDF. Genérala con "
            "`uv run python -m scripts.construir_tfidf`."
        )
        return

    st.markdown("**Consultas de ejemplo**")
    columnas = st.columns(3)
    for posicion, ejemplo in enumerate(busqueda.CONSULTAS_EJEMPLO):
        if columnas[posicion % 3].button(ejemplo, key=f"ej{posicion}", width="stretch"):
            st.session_state["consulta"] = ejemplo

    consulta = st.text_input(
        "Consulta", key="consulta", placeholder="Escribe aquí, o usa un ejemplo de arriba"
    )

    columnas = st.columns([3, 1])
    metodo = columnas[0].radio(
        "Método", [busqueda.TFIDF, busqueda.EMBEDDINGS, "Comparar los dos"],
        horizontal=True,
    )
    cuantos = columnas[1].slider("Resultados", 3, 15, 5)

    st.caption(
        "**La diferencia entre los dos métodos.** TF-IDF busca **coincidencia de "
        "palabras**: recupera fragmentos que usan los mismos términos que escribiste, y "
        "no reconoce sinónimos. Los embeddings buscan **significado**: un modelo sitúa "
        "consulta y fragmentos en un espacio donde la cercanía es semántica, así que "
        "«demora» puede recuperar «tardaron una hora» aunque no compartan ninguna "
        "palabra. TF-IDF es más literal y más rápido; los embeddings son más flexibles "
        "y a veces demasiado, porque también acercan cosas que solo se parecen de lejos."
    )

    if not consulta:
        return

    usa_embeddings = metodo in (busqueda.EMBEDDINGS, "Comparar los dos")
    if usa_embeddings:
        with st.spinner(
            "Cargando el modelo de significado. La primera búsqueda de la sesión tarda "
            "unos diez segundos; las siguientes son inmediatas."
        ):
            busqueda.precargar_embeddings()

    st.divider()

    nota_tfidf = "coincidencia de palabras"
    nota_emb = "significado"

    if metodo == busqueda.TFIDF:
        tabla, segundos, terminos = busqueda.buscar_tfidf(consulta, cuantos)
        _resultados(tabla, segundos, busqueda.TFIDF, nota_tfidf)
        st.caption(f"Términos buscados: {', '.join(terminos) if terminos else 'ninguno'}")

    elif metodo == busqueda.EMBEDDINGS:
        tabla, segundos = busqueda.buscar_embeddings(consulta, cuantos)
        _resultados(tabla, segundos, busqueda.EMBEDDINGS, nota_emb)

    else:
        izquierda, derecha = st.columns(2)
        tabla_tfidf, segundos_tfidf, terminos = busqueda.buscar_tfidf(consulta, cuantos)
        tabla_emb, segundos_emb = busqueda.buscar_embeddings(consulta, cuantos)
        with izquierda:
            _resultados(tabla_tfidf, segundos_tfidf, busqueda.TFIDF, nota_tfidf)
            st.caption(f"Términos buscados: {', '.join(terminos) if terminos else 'ninguno'}")
        with derecha:
            _resultados(tabla_emb, segundos_emb, busqueda.EMBEDDINGS, nota_emb)

        comunes = set(tabla_tfidf.get("texto", [])) & set(tabla_emb.get("texto", []))
        st.divider()
        st.markdown(
            f"**Coinciden en {len(comunes)} de {cuantos} resultados.** "
            "Cuantos menos comparten, más distinta es la lectura que hace cada "
            "representación de la misma consulta."
        )
