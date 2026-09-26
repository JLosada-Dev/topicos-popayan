"""Modo presentación: once pantallas para proyectar en una sustentación de 15 minutos.

Una idea por pantalla, tipografía grande y poco texto. No hay tablas anchas ni salidas
de código: lo que necesita detalle se explora después, en las otras secciones.

Las figuras son las mismas del informe, para que lo proyectado y lo entregado digan lo
mismo. La única vista propia es la de atributos emergentes, que no existe como figura.
"""

import pandas as pd
import streamlit as st

from app import datos
from src.etiquetas import legible
from src.paleta import COLOR_POR_TIPO, REJILLA, TINTA, TINTA_TENUE

CLAVE_PANTALLA = "pantalla"
CONSULTA_DEMO = "comida en mal estado"

TITULOS = (
    "Contexto",
    "El problema",
    "Objetivos",
    "La pregunta",
    "Los datos",
    "Las técnicas",
    "Resultados",
    "Atributos emergentes",
    "Insights",
    "Recomendaciones",
    "Limitaciones y cierre",
)

ESTILO = """
<style>
.pres h1 { font-size: 2.8rem; line-height: 1.15; margin: 0 0 1.2rem 0; }
.pres h2 { font-size: 1.9rem; line-height: 1.25; font-weight: 600; margin: 0 0 .8rem 0; }
.pres p, .pres li { font-size: 1.35rem; line-height: 1.55; }
.pres li { margin-bottom: .5rem; }
.pres .cifra { font-size: 4.2rem; font-weight: 700; line-height: 1; }
.pres .cifra-sm { font-size: 2.6rem; font-weight: 700; line-height: 1.1; }
.pres .pie { font-size: 1.05rem; color: #52514e; }
.pres .destacado { font-size: 1.6rem; font-weight: 600; line-height: 1.4; }
.pres .tenue { color: #52514e; }
</style>
"""


def _abrir(texto: str) -> None:
    st.markdown(f'{ESTILO}<div class="pres">{texto}</div>', unsafe_allow_html=True)


def _coma(numero: float, decimales: int = 2) -> str:
    """Decimal con coma, que es el separador del español."""
    return f"{numero:.{decimales}f}".replace(".", ",")


def _cifra(valor: str, etiqueta: str, pequena: bool = False) -> str:
    clase = "cifra-sm" if pequena else "cifra"
    return f'<div class="{clase}">{valor}</div><div class="pie">{etiqueta}</div>'


# --------------------------------------------------------------- navegación
#
# Una sola fuente de verdad: el valor del selector de salto. Si los botones escribieran
# en una variable aparte, el selector conservaría su valor anterior entre recargas y
# devolvería la presentación a la pantalla de la que se acaba de salir.
OPCIONES = tuple(f"{n + 1}. {t}" for n, t in enumerate(TITULOS))


def _indice_actual() -> int:
    elegida = st.session_state.setdefault(CLAVE_PANTALLA, OPCIONES[0])
    return OPCIONES.index(elegida)


def _ir_a(indice: int) -> None:
    st.session_state[CLAVE_PANTALLA] = OPCIONES[max(0, min(indice, len(OPCIONES) - 1))]


def _al_explorador() -> None:
    """Salta al explorador con la consulta de demostración ya escrita."""
    st.session_state["consulta"] = CONSULTA_DEMO
    st.session_state["seccion"] = "Explorador"


def _navegacion(indice: int) -> None:
    izquierda, centro, derecha = st.columns([1, 3, 1])
    izquierda.button(
        "◀ Anterior", width="stretch", disabled=indice == 0,
        on_click=_ir_a, args=(indice - 1,), key="pres_atras",
    )
    derecha.button(
        "Siguiente ▶", width="stretch", disabled=indice == len(OPCIONES) - 1,
        on_click=_ir_a, args=(indice + 1,), key="pres_adelante",
    )
    # El selector escribe directamente en CLAVE_PANTALLA, que es la misma variable que
    # leen los botones
    centro.selectbox(
        "Ir a", OPCIONES, label_visibility="collapsed", key=CLAVE_PANTALLA,
    )


# ---------------------------------------------------------------- pantallas
def _p1_contexto() -> None:
    _abrir("""
<h1>Temas emergentes en las reseñas gastronómicas de Popayán</h1>
<p class="tenue">Trabajo final · Text &amp; Web Analytics<br>
Especialización en Data Analytics para Marketing Digital · FUP</p>
""")
    st.divider()
    columnas = st.columns(3)
    for columna, (valor, etiqueta) in zip(columnas, [
        ("2.430", "reseñas de Google Maps"),
        ("122", "establecimientos de Popayán"),
        ("6", "dimensiones con las que se evalúan"),
    ]):
        columna.markdown(f'{ESTILO}<div class="pres">{_cifra(valor, etiqueta)}</div>',
                         unsafe_allow_html=True)
    _abrir("""
<p style="margin-top:2rem">Comida · servicio · precio · ambiente · tiempo de espera ·
patrimonio</p>
""")


def _p2_problema() -> None:
    _abrir("""
<h1>El problema</h1>
<h2>Un establecimiento tiene cientos de reseñas y ninguna forma barata de saber
<span class="tenue">de qué hablan</span>.</h2>
<p>La práctica habitual es evaluarlas con un esquema fijo de seis dimensiones. Viene de
la literatura de calidad del servicio y sirve para comparar locales entre sí.</p>
<p><strong>Pero tiene un supuesto que nadie comprueba:</strong> que esas seis dimensiones
agotan lo que los comensales quieren decir.</p>
<p class="destacado">Si los clientes hablan de algo que el esquema no contempla, el
establecimiento no se entera. Y ahí puede estar lo que lo diferencia — o lo que lo está
hundiendo.</p>
""")


def _p3_objetivos() -> None:
    _abrir("""
<h1>Objetivos</h1>
<h2>Identificar los temas emergentes y establecer su correspondencia con las dimensiones
tradicionales, para orientar la comunicación digital.</h2>
<ol>
<li><strong>Caracterizar</strong> el corpus y definir los requerimientos de su
preparación.</li>
<li><strong>Determinar</strong> los temas emergentes mediante modelado de tópicos.</li>
<li><strong>Evaluar</strong> su correspondencia con las dimensiones y su relación con la
calificación.</li>
</ol>
""")


def _p4_pregunta() -> None:
    _abrir("""
<h1>La pregunta</h1>
<h2>¿Los temas que emergen de las reseñas coinciden con las seis dimensiones con las que
tradicionalmente se evalúa la experiencia gastronómica?</h2>
<p>Hacen falta dos cosas: <strong>una lectura que no sepa nada del esquema</strong> —el
modelado de tópicos— y <strong>una medida de acuerdo</strong> entre esa lectura y la del
esquema.</p>
<p class="destacado">Si coincidieran del todo, el esquema bastaría.<br>
Si no coincidieran en nada, el esquema sería inútil.<br>
Lo interesante está en el medio, y es lo que se mide.</p>
""")


def _p5_datos() -> None:
    _abrir("<h1>Los datos</h1>")
    izquierda, derecha = st.columns([3, 2])
    with izquierda:
        st.image(str(datos.figura("04_embudo_corpus.png")))
    with derecha:
        _abrir("""
<h2>Componente textual</h2>
<p>El <strong>texto libre</strong> de cada reseña, que es el objeto del análisis, y el
<strong>diccionario</strong> de 81 términos que constituye la lectura a priori.</p>
<h2 style="margin-top:1.6rem">Componente Web</h2>
<p>Los metadatos que registra la plataforma: la <strong>calificación en estrellas</strong>,
la ficha del establecimiento, la <strong>zona</strong>, si el propietario respondió y la
fecha.</p>
<p class="pie" style="margin-top:1rem">Los temas salen del texto. Su interpretación se
apoya en la calificación y la zona: un tema sin su calificación no dice si es una
fortaleza o un problema.</p>
""")


def _p6_tecnicas() -> None:
    _abrir("""
<h1>Las técnicas</h1>
<h2>De la reseña al fragmento, y del fragmento al tema.</h2>
<ol>
<li><strong>Segmentar por cláusula.</strong> «La comida deliciosa, pero tardaron una
hora» son dos opiniones, no una.</li>
<li><strong>Anonimizar.</strong> Los nombres de local se reemplazan por
<code>[LOCAL]</code>, para agrupar por lo que se dice y no por de quién se habla.</li>
<li><strong>Representar.</strong> Embeddings multilingües de 384 dimensiones.</li>
<li><strong>Agrupar.</strong> BERTopic: UMAP + HDBSCAN + c-TF-IDF.</li>
<li><strong>Etiquetar.</strong> Los 41 tópicos se agrupan a mano en 14 temas, tras
leerlos.</li>
</ol>
<p class="destacado">Segmentar duplica la pureza: el 42 % de los fragmentos habla de una
sola dimensión, frente al 21 % de las reseñas completas.</p>
""")


def _p7_resultados() -> None:
    ami = datos.ami().iloc[0]
    _abrir("<h1>Resultados</h1>")
    izquierda, derecha = st.columns([2, 3])
    with izquierda:
        _abrir(f"""
<h2>Acuerdo con el esquema tradicional</h2>
{_cifra(_coma(ami["ami"]), "AMI · la línea base del azar es 0,00")}
<p class="destacado" style="margin-top:1.4rem">Parcial, no equivalencia.</p>
<p>Comparten estructura real, pero <strong>los temas emergentes no son otra forma de
nombrar las seis dimensiones</strong>.</p>
<p style="margin-top:1.2rem"><strong>espera</strong> · 62,7 % en un solo tópico<br>
<strong>comida</strong> · 11,8 %, repartida en 38</p>
<p class="destacado">La espera se comporta como una categoría bien definida. La comida,
como un dominio entero que el modelo descompone en dieciséis tópicos.</p>
""")
    with derecha:
        st.image(str(datos.figura("03_mapa_topico_dimension.png")))
        st.caption("Cada celda: % de los fragmentos del tópico que activan esa dimensión.")

    st.divider()
    izquierda, derecha = st.columns([3, 2])
    izquierda.markdown(
        f'{ESTILO}<div class="pres"><p class="destacado">Y hay temas que el método no '
        f'puede encontrar.</p><p>«{CONSULTA_DEMO}» no forma tópico: el modelo lo acerca '
        f'a las quejas sobre el plato.</p></div>', unsafe_allow_html=True)
    derecha.button(
        f"Demostrar: «{CONSULTA_DEMO}» ▶", width="stretch",
        on_click=_al_explorador, key="pres_demo",
    )


def _p8_emergentes(temas: pd.DataFrame, marco: pd.DataFrame) -> None:
    """La figura arriba y el gráfico a ancho completo abajo.

    En dos columnas, los nombres de tema —«infraestructura y espacio»— no caben junto a
    un eje de 1 a 5 y quedan cortados por las barras.
    """
    _abrir("<h1>Atributos emergentes</h1>")
    izquierda, derecha = st.columns([3, 2])
    with izquierda:
        st.image(str(datos.figura("01_distribucion_por_tipo.png")))
    with derecha:
        _abrir("""
<p class="destacado">El 13 % del corpus habla de algo que el esquema no contempla.</p>
<p>Y un 20 % no describe nada: emite un veredicto. «Recomendado», «volvería».</p>
""")
    st.divider()
    _grafico_emergentes(temas, marco)


def _grafico_emergentes(temas: pd.DataFrame, marco: pd.DataFrame) -> None:
    """Solo los atributos emergentes, por calificación, con la media del corpus."""
    import altair as alt

    media = float(marco["rating"].mean())
    sub = temas[temas["tipo"] == "atributo_nuevo"].assign(
        tema=lambda d: d["tema"].map(legible),
        etiqueta=lambda d: d["fragmentos"].map(lambda n: f"{n:,}".replace(",", ".")),
    )
    # El nombre del tema va DENTRO de la barra, no en el eje. Vega calcula el espacio
    # del eje a partir del ancho disponible y con nombres largos —«infraestructura y
    # espacio»— los recorta contra el borde del contenedor. Dentro de la barra siempre
    # caben y además se leen mejor proyectados.
    #
    # El orden se fija como lista en vez de con `sort="-x"`, porque la capa del nombre
    # no tiene codificación `x` de la que ordenar.
    orden = sub.sort_values("rating", ascending=False)["tema"].tolist()
    eje_y = alt.Y("tema:N", sort=orden, title=None, axis=None)
    eje_x = alt.X("rating:Q", title="Calificación media (estrellas)",
                  scale=alt.Scale(domain=[1, 5.2]),
                  axis=alt.Axis(grid=True, gridColor=REJILLA, labelFontSize=14,
                                titleFontSize=15))

    barras = alt.Chart(sub).mark_bar(
        height=48, cornerRadiusEnd=5, color=COLOR_POR_TIPO["atributo_nuevo"]
    ).encode(y=eje_y, x=eje_x)
    nombres = alt.Chart(sub.assign(inicio=1.0)).mark_text(
        align="left", dx=14, fontSize=19, fontWeight=600, color=TINTA
    ).encode(y=eje_y, x=alt.X("inicio:Q", scale=alt.Scale(domain=[1, 5.2])),
             text="tema:N")
    cuentas = alt.Chart(sub).mark_text(
        align="left", dx=10, fontSize=17, color=TINTA_TENUE
    ).encode(y=eje_y, x=eje_x, text="etiqueta:N")
    referencia = alt.Chart(pd.DataFrame({"x": [media]})).mark_rule(
        strokeDash=[5, 4], color=TINTA_TENUE, strokeWidth=2
    ).encode(x=alt.X("x:Q", scale=alt.Scale(domain=[1, 5.2])))

    grafico = (barras + nombres + cuentas + referencia).properties(width=880, height=300)
    st.altair_chart(grafico, width="content")
    izquierda, derecha = st.columns([2, 3])
    izquierda.markdown(
        f'{ESTILO}<div class="pres"><p class="destacado">Ninguno resulta negativo.</p>'
        f'<p class="pie">El número es la cantidad de fragmentos. Línea punteada: media '
        f'del corpus, {_coma(media)} estrellas.</p></div>', unsafe_allow_html=True)
    derecha.markdown(
        f'{ESTILO}<div class="pres"><p>No es que no haya quejas sobre atributos nuevos: '
        f'inocuidad (1,62) y cobro (1,87) son de lo peor del corpus, pero '
        f'<strong>no llegaron a formar tópico</strong>.</p></div>',
        unsafe_allow_html=True)


def _p9_insights(marco: pd.DataFrame) -> None:
    _abrir("<h1>Insights</h1>")
    izquierda, derecha = st.columns([3, 2])
    with izquierda:
        st.image(str(datos.figura("02_temas_por_rating.png")))
    with derecha:
        _abrir("""
<p class="destacado">La espera es el problema, y es el único.</p>
<p>1,88 estrellas y el 76 % de reseñas de una o dos. Ningún otro tema baja de tres.</p>
<p class="destacado" style="margin-top:1.4rem">Lo mejor valorado no está en el
esquema.</p>
<p>Ocasión de consumo (4,58) y referente en la ciudad (4,55) son los dos atributos
mejor calificados — y los dos son emergentes.</p>
<p class="destacado" style="margin-top:1.4rem">Lo que el método no ve es más
crítico.</p>
<p>Los fragmentos sin asignar promedian 3,20 contra 3,70 del corpus.</p>
""")


def _p10_recomendaciones() -> None:
    _abrir("""
<h1>Recomendaciones</h1>
<h2>Para el establecimiento</h2>
<ol>
<li><strong>Atacar la espera antes que nada.</strong> Cualquier inversión en comunicación
rinde poco mientras ese tema siga generando reseñas de una estrella.</li>
<li><strong>Comunicar la ocasión, no solo el producto.</strong> Para quién es el sitio
—familia, amigos, celebración— es el atributo mejor valorado, y casi nadie lo usa como
eje.</li>
<li><strong>Reivindicar el lugar en la ciudad.</strong> «Referente gastronómico de
Popayán» es el segundo mejor valorado.</li>
<li><strong>Resolver lo operativo invisible.</strong> Datáfono, horario actualizado en
Google Maps, contestar el teléfono. No cuesta nada y genera reseñas muy negativas.</li>
<li><strong>Vigilar la inocuidad por separado.</strong> Es lo peor calificado del estudio
y ningún panel de dimensiones lo mostrará: se disuelve dentro de «comida».</li>
</ol>
""")


def _p11_cierre() -> None:
    _abrir("""
<h1>Limitaciones</h1>
<ul>
<li>La <strong>coherencia léxica es baja</strong>: los fragmentos tienen 10 palabras de
mediana y los términos de un tópico rara vez coaparecen. La validez se sostiene en la
lectura, no en el indicador.</li>
<li>Los <strong>temas transversales se miden con reglas de piso</strong>: acotan el orden
de magnitud, no lo miden.</li>
<li>Cada fragmento <strong>hereda la calificación de su reseña</strong>, así que no son
observaciones independientes y no se aplican pruebas de significancia.</li>
<li>El <strong>umbral de agrupamiento sesga</strong> qué atributos emergentes se ven, y
el sesgo tiene signo: los que forman tópico son los positivos.</li>
</ul>
""")
    st.divider()
    _abrir("""
<p class="destacado">El esquema tradicional captura la mayor parte de lo que dicen los
comensales, pero no todo.</p>
<p>Un 13 % del corpus habla de atributos que no contempla, y lo que el método no agrupa
es sistemáticamente lo más crítico. <strong>Quien lea solo las seis dimensiones tendrá
una imagen más amable de la que sus clientes sostienen.</strong></p>
""")


# -------------------------------------------------------------------- entrada
def presentacion() -> None:
    indice = _indice_actual()
    temas = datos.temas()
    marco = datos.fragmentos()

    st.caption(f"Pantalla {indice + 1} de {len(TITULOS)} · {TITULOS[indice]}")
    st.progress((indice + 1) / len(TITULOS))

    pantallas = [
        _p1_contexto, _p2_problema, _p3_objetivos, _p4_pregunta, _p5_datos,
        _p6_tecnicas, _p7_resultados,
        lambda: _p8_emergentes(temas, marco),
        lambda: _p9_insights(marco),
        _p10_recomendaciones, _p11_cierre,
    ]
    pantallas[indice]()

    st.divider()
    _navegacion(indice)
