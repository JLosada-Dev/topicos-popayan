"""Contenido del notebook consolidado `proyecto_final.ipynb`.

Sigue la cadena problema → objetivo → pregunta analítica → datos → técnicas →
resultados → insights → recomendaciones. No repite los cuatro notebooks por etapa, que
quedan como anexo: aquí se cuenta el estudio entero de corrido, para leerlo de una vez.
"""

from scripts.notebooks_contenido import code, md

PROYECTO_FINAL = [
    md("""
# Temas emergentes en las reseñas gastronómicas de Popayán

**Trabajo final · Text & Web Analytics**
Especialización en Data Analytics para Marketing Digital · Fundación Universitaria de
Popayán

---

Este notebook cuenta el estudio completo, de la pregunta a las recomendaciones. Los
cuatro notebooks por etapa —`00_preparacion`, `01_caracterizacion`, `02_topicos` y
`03_evaluacion`— quedan como anexo, con el detalle técnico de cada paso.

Todo lo que aparece aquí está calculado de antemano y se lee de `data/processed/`: el
notebook corre en segundos y no necesita GPU ni descargar modelos.
"""),
    code("""
import pandas as pd

from src.config import DIMENSIONES, DATOS_PROCESADOS, FIGURAS
from src.topicos import ATIPICO

pd.set_option("display.max_colwidth", 110)

fragmentos = pd.read_csv(DATOS_PROCESADOS / "fragmentos.csv").merge(
    pd.read_csv(DATOS_PROCESADOS / "fragmentos_topicos.csv"),
    on=["fragmento_id", "review_id"],
)
topicos = pd.read_csv(DATOS_PROCESADOS / "topicos_etiquetados.csv")
temas = pd.read_csv(DATOS_PROCESADOS / "temas_consolidado.csv")
asignados = int((fragmentos["topico"] != ATIPICO).sum())

print(f"{len(fragmentos)} fragmentos · {fragmentos['review_id'].nunique()} reseñas · "
      f"{len(topicos)} tópicos · {len(temas)} temas")
"""),

    # ------------------------------------------------------------------ problema
    md("""
## 1. El problema

Un establecimiento gastronómico que quiere mejorar su comunicación digital tiene delante
cientos de reseñas en Google Maps y ninguna forma barata de saber **de qué hablan**.

La práctica habitual es evaluarlas con un esquema fijo de dimensiones —comida, servicio,
precio, ambiente, tiempo de espera y, en una ciudad como Popayán, patrimonio o
tradición—. Ese esquema viene de la literatura de calidad del servicio y funciona bien
para comparar establecimientos entre sí.

Pero tiene un supuesto que nadie comprueba: **que esas seis dimensiones agotan lo que
los comensales quieren decir.** Si los clientes están hablando de algo que el esquema no
contempla, el establecimiento no se entera, y justamente ahí puede estar lo que lo
diferencia o lo que lo está hundiendo.

Este trabajo pone a prueba ese supuesto.
"""),

    # ------------------------------------------------------------------ objetivo
    md("""
## 2. Objetivo

**Objetivo general.** Identificar los temas emergentes en las reseñas de establecimientos
gastronómicos de Popayán, mediante técnicas de análisis de texto, para establecer su
correspondencia con las dimensiones tradicionalmente utilizadas para evaluar la
experiencia gastronómica y orientar la comunicación digital de los establecimientos.

**Objetivos específicos**

1. **Caracterizar** el corpus mediante análisis descriptivo y verificación de calidad,
   para definir los requerimientos de su preparación.
2. **Determinar** los temas emergentes mediante modelado de tópicos, para representar los
   asuntos que abordan los comensales.
3. **Evaluar** la correspondencia de los temas con las dimensiones predefinidas y su
   relación con la calificación, para derivar orientaciones de comunicación digital.
"""),

    # ---------------------------------------------------------- pregunta analítica
    md("""
## 3. La pregunta analítica

> **¿Los temas que emergen de las reseñas coinciden con las seis dimensiones con las que
> tradicionalmente se evalúa la experiencia gastronómica, o hay asuntos que ese esquema
> no captura?**

Y si los hay, tres preguntas derivadas:

- ¿Cuánto pesan en el corpus?
- ¿Con qué calificación se asocian?
- ¿Qué puede hacer un establecimiento con esa información?

Para responderlas hacen falta dos cosas: **una lectura que no sepa nada del esquema** —el
modelado de tópicos— y **una medida de acuerdo** entre esa lectura y la del esquema —el
AMI—. Si las dos coincidieran del todo, el esquema bastaría. Si no coincidieran en
nada, el esquema sería inútil. Lo interesante está en el medio, y es lo que medimos.
"""),

    # -------------------------------------------------------------------- datos
    md("""
## 4. Los datos

### De dónde vienen

Reseñas de Google Maps de establecimientos gastronómicos de Popayán, capturadas en un
estudio previo (`reputacion-popayan`) del que este trabajo hereda el corpus, el marco
muestral y el diccionario de dimensiones. Ese proyecto se trata como **solo lectura**, y
cada archivo que se toma de allí queda registrado con su hash SHA-256 en
`data/external/manifiesto.csv`.

**Las personas que escribieron las reseñas no son identificables**: el corpus no trae
nombre ni identificador de autor, solo cuántas reseñas ha escrito cada una.
"""),
    md("""
### Los dos componentes de los datos

El corpus tiene una naturaleza doble, y el estudio usa las dos caras.

**Componente Text Analytics** — el contenido de la reseña.

- El **texto libre** que escribió cada comensal, que es el objeto del análisis: se
  segmenta, se vectoriza y se agrupa.
- El **diccionario de dimensiones**: 81 términos con sus raíces y sus reglas de contexto,
  que constituyen la lectura *a priori* contra la que se contrasta.

**Componente Web Analytics** — los metadatos que Google Maps registra alrededor del
texto, y que no son texto.

- La **calificación en estrellas**, que es la medida de satisfacción declarada.
- La **ficha del establecimiento**: nombre, categoría, dirección, coordenadas, su
  calificación media y su histograma de estrellas.
- La **zona**, derivada de la distancia al Parque Caldas: dentro o fuera del centro
  histórico.
- Señales de comportamiento en la plataforma: si el propietario **respondió** la reseña,
  cuántas reseñas ha escrito esa persona, la **fecha** de publicación y el **volumen**
  total de reseñas del local.

El trabajo es Text & Web Analytics porque **cruza las dos**: los temas salen del texto,
pero su interpretación se apoya en la calificación, la zona y el establecimiento, que son
metadatos de la plataforma. Un tema sin su calificación no dice si es un problema o una
fortaleza.
"""),
    code("""
corpus_columnas = pd.DataFrame([
    ("texto", "Text Analytics", "El contenido de la reseña; es el objeto del análisis"),
    ("rating", "Web Analytics", "Satisfacción declarada, de 1 a 5 estrellas"),
    ("respuesta_dueno", "Web Analytics", "Si el propietario respondió en la plataforma"),
    ("autor_n_resenas", "Web Analytics", "Actividad de quien escribe; único dato de autoría"),
    ("fecha", "Web Analytics", "Cuándo se publicó"),
    ("establecimiento / place_id", "Web Analytics", "Ficha del local en Google Maps"),
    ("zona", "Web Analytics", "Centro histórico o fuera, por distancia al Parque Caldas"),
], columns=["Campo", "Componente", "Qué aporta"])
corpus_columnas
"""),
    md("""
### El embudo

El filtro de idioma y el de longitud mínima vienen del estudio previo y no se recalculan.
Lo único que añade este trabajo es la eliminación de duplicados reales.

**La unidad de análisis cambia a mitad del embudo**, y es una decisión central: de la
reseña se pasa al **fragmento**, la reseña partida en cláusulas.
"""),
    code("""
from IPython.display import Image, display

display(Image(filename=str(FIGURAS / "04_embudo_corpus.png"), width=880))
"""),
    md("""
**Por qué el fragmento y no la reseña.** Una reseña suele hablar de varias cosas a la
vez: «la comida deliciosa, pero tardaron una hora». Medida como unidad entera, mezcla
asuntos y hace imposible atribuir un tema. Partida en cláusulas —por puntuación y por
conectores adversativos— cada trozo habla de una sola cosa con mucha más frecuencia.

El efecto se mide: el **42,0 %** de los fragmentos activa exactamente una dimensión,
contra el **20,9 %** de las reseñas completas. Segmentar duplica el corpus limpio sobre
el que se puede medir el acuerdo.
"""),
    code("""
una_dimension = (fragmentos["n_dim"] == 1).mean()
por_resena = fragmentos.groupby("review_id")[list(DIMENSIONES)].any().sum(axis=1)
print(f"fragmentos con exactamente una dimensión: {100 * una_dimension:.1f} %")
print(f"reseñas  con exactamente una dimensión:   {100 * (por_resena == 1).mean():.1f} %")
print(f"\\nfragmentos sin ninguna dimensión: {100 * (fragmentos['n_dim'] == 0).mean():.1f} %")
"""),

    # ------------------------------------------------------------------ técnicas
    md("""
## 5. Las técnicas

El pipeline tiene cinco pasos. Cada decisión de parámetro está justificada en
`docs/decisiones_metodologicas.md` con la alternativa que se consideró y por qué se
descartó.

| Paso | Técnica | Decisión clave |
|---|---|---|
| Segmentación | Cláusula: oración más cortes en conectores adversativos | Se copia la regla del estudio previo, sin cambios, para que los resultados sigan siendo comparables |
| Anonimización | Los nombres de local se reemplazan por `[LOCAL]` | Tres reglas evitan falsos positivos; sin ellas el enmascarado afectaba al 14 % del corpus en vez del 1,8 % |
| Representación | Embeddings `paraphrase-multilingual-MiniLM-L12-v2`, 384 dimensiones | Se descartó `multilingual-e5-small`: su espacio es tan anisótropo que colapsa en 5 tópicos |
| Agrupamiento | BERTopic: UMAP + HDBSCAN + c-TF-IDF | `min_cluster_size=30`, `min_samples=15`; con 50 aparecía un cajón negativo del 27 % del corpus |
| Etiquetado | Los 41 tópicos se agrupan a mano en 14 temas | La fusión automática por similitud no es defendible: une por registro evaluativo, no por tema |

**Dos textos con papeles distintos.** Los embeddings se calculan sobre el texto natural
—con mayúsculas, tildes y stopwords—, porque el modelo de lenguaje espera texto tal como
se escribe. El c-TF-IDF, que solo pone nombre a los tópicos ya formados, corre sobre
texto limpio. **Las negaciones se conservan**: quitarlas etiquetaba un tópico con su
contrario exacto —el de «no recomiendo», con 1,53 estrellas de media, aparecía rotulado
«recomiendo»—.
"""),
    code("""
from src.embeddings import MODELO_EMBEDDINGS
from src.topicos import MIN_SAMPLES, MIN_TOPIC_SIZE, UMBRAL_REDUCCION
from src.config import SEMILLA

print(f"embeddings         {MODELO_EMBEDDINGS}")
print(f"min_cluster_size   {MIN_TOPIC_SIZE}")
print(f"min_samples        {MIN_SAMPLES}")
print(f"umbral de atípicos {UMBRAL_REDUCCION}")
print(f"semilla            {SEMILLA}")
"""),

    # ----------------------------------------------------------------- resultados
    md("""
## 6. Resultados

### 6.1 Emergen 41 tópicos, que se agrupan en 14 temas

El modelo asigna el **80,7 %** de los fragmentos. El tópico mayor es solo el 6,0 % del
corpus, así que no hay ningún grupo que acapare la solución.
"""),
    code("""
resumen = pd.Series({
    "Fragmentos": len(fragmentos),
    "Asignados a un tópico": asignados,
    "Sin asignar": len(fragmentos) - asignados,
    "Tópicos": len(topicos),
    "Temas": len(temas),
    "Tópico mayor (% del corpus)": round(100 * topicos["n"].max() / len(fragmentos), 1),
}, name="valor").to_frame()
resumen
"""),
    md("""
### 6.2 Los temas se reparten en tres clases, y una no describe nada

Al leer los 41 tópicos aparece una distinción que el esquema a priori no contempla: no
todos hablan de un **atributo** del servicio. Una quinta parte emite un **veredicto**
sobre la experiencia sin describir ningún aspecto de ella.
"""),
    code("""
display(Image(filename=str(FIGURAS / "01_distribucion_por_tipo.png"), width=880))
"""),
    code("""
por_tipo = temas.groupby("tipo").agg(
    temas=("tema", "size"), topicos=("n_topicos", "sum"), fragmentos=("fragmentos", "sum")
)
por_tipo["% del corpus asignado"] = (100 * por_tipo["fragmentos"] / asignados).round(1)
por_tipo.sort_values("fragmentos", ascending=False)
"""),
    md("""
- **Atributo del esquema a priori (66,6 %)** — habla de una de las seis dimensiones.
- **Valoración global (20,3 %)** — «recomendado», «volvería», «excelente experiencia». No
  describe un aspecto: lo juzga en bloque. Para el objetivo 3 estos 970 fragmentos **no
  tienen con qué contrastarse**, porque no hay atributo que comparar.
- **Atributo emergente (13,0 %)** — habla de algo que el esquema no contempla.
"""),
    code("""
temas[["tema", "tipo", "n_topicos", "fragmentos", "pct_asignado",
       "rating", "pct_1_2_estrellas", "polaridad_dominante"]]
"""),
    md("""
### 6.3 Los cuatro atributos emergentes

| Tema | Fragmentos | Calificación | De qué habla |
|---|---:|---:|---|
| Referente en la ciudad | 276 | 4,55 | «el mejor de Popayán», «restaurante emblemático» |
| Ocasión de consumo | 223 | 4,58 | para quién y para qué: familia, amigos, celebración |
| Infraestructura y espacio | 89 | 3,69 | tamaño del local, parqueo, mesas |
| Medios de pago | 34 | 3,26 | efectivo, datáfono, transferencia |

Dos de ellos son **invisibles para el diccionario**: el 91 % de los fragmentos de medios
de pago y el 76 % de los de infraestructura no activan ninguna de las seis dimensiones.
"""),
    code("""
nuevos = topicos.loc[topicos["tipo"] == "atributo_nuevo", "topico_id"]
sub = fragmentos[fragmentos["topico"].isin(nuevos)]
resto = fragmentos[(fragmentos["topico"] != ATIPICO) & (~fragmentos["topico"].isin(nuevos))]

detalle = sub.groupby("topico").agg(
    n=("fragmento_id", "size"),
    pct_sin_dimension=("n_dim", lambda s: round(100 * (s == 0).mean(), 1)),
).join(topicos.set_index("topico_id")["tema"])
print(f"atributos emergentes sin ninguna dimensión: {100 * (sub['n_dim'] == 0).mean():.1f} %")
print(f"resto del corpus asignado:                  {100 * (resto['n_dim'] == 0).mean():.1f} %")
detalle.sort_values("pct_sin_dimension", ascending=False)
"""),
    md("""
### 6.4 La correspondencia con el esquema es parcial

El AMI compara dos formas de agrupar los mismos fragmentos: la del modelo y la del
diccionario. Se calcula sobre los fragmentos que activan **exactamente una** dimensión,
que son los únicos con los que la comparación tiene sentido.

La línea base se estima permutando las etiquetas 200 veces: es el acuerdo que saldría por
pura casualidad.
"""),
    code("""
ami = pd.read_csv(DATOS_PROCESADOS / "ami_resultados.csv")
ami[["base", "n", "ami", "ari", "nulo", "exceso"]]
"""),
    md("""
**AMI = 0,406 sobre una línea base de cero.** Hay acuerdo real y sustancial, pero muy
lejos de 1: **los temas emergentes no son una forma distinta de nombrar las seis
dimensiones.** El ARI, mucho más bajo, lo confirma desde otro ángulo: la coincidencia por
pares es escasa porque un tópico se reparte entre varias dimensiones y una dimensión
entre muchos tópicos.
"""),
    code("""
display(Image(filename=str(FIGURAS / "03_mapa_topico_dimension.png"), width=840))
"""),
    code("""
pd.read_csv(DATOS_PROCESADOS / "dispersion_dimensiones.csv")
"""),
    md("""
**Ninguna dimensión se concentra en un solo tópico.** La espera es la única con
correspondencia fuerte —el 62,7 % en uno—, y era previsible: es un asunto acotado con
vocabulario propio. **Comida es el caso opuesto**: se reparte en 38 tópicos y su tópico
principal ni siquiera es de comida, sino de valoración global. Es la dimensión más grande
y la menos específica: casi cualquier elogio la menciona.

### 6.5 La espera concentra el malestar
"""),
    code("""
display(Image(filename=str(FIGURAS / "02_temas_por_rating.png"), width=880))
"""),
    code("""
atipicos = fragmentos[fragmentos["topico"] == ATIPICO]
print(f"media del corpus:          {fragmentos['rating'].mean():.2f} estrellas")
print(f"fragmentos sin asignar:    {atipicos['rating'].mean():.2f} estrellas "
      f"({100 * (atipicos['rating'] <= 2).mean():.1f} % de 1-2★)")
temas.sort_values("rating")[["tema", "tipo", "fragmentos", "rating", "pct_1_2_estrellas"]].head(5)
"""),
    md("""
### 6.6 Hay temas que el método no puede encontrar

Al leer los fragmentos sin asignar aparecieron cuatro asuntos que **no forman tópico**:
inocuidad, honestidad en el cobro, horarios e información digital, e infraestructura
frente al clima. Son de los más negativos del corpus.

La hipótesis inicial fue que el umbral de tamaño mínimo los ocultaba. Se puso a prueba
bajando `min_cluster_size` a 20 y a 15.
"""),
    code("""
pd.read_csv(DATOS_PROCESADOS / "sensibilidad_umbral.csv")[
    ["min_cluster_size", "min_samples", "n_topicos", "pct_atipicos",
     "inocuidad_forma_topico", "inocuidad_max_concentracion",
     "horarios_forma_topico", "horarios_max_concentracion"]
]
"""),
    md("""
**La hipótesis no se sostiene: bajar el umbral no los agrupa, los dispersa más.** La
concentración de inocuidad en su tópico mayor cae del 26,4 % al 11,3 %.

La causa real es la **cohesión** en el espacio de embeddings, no la masa.
"""),
    code("""
pd.read_csv(DATOS_PROCESADOS / "cohesion_temas.csv")
"""),
    md("""
La comparación decisiva es **medios de pago contra inocuidad**: medios de pago tiene 34
fragmentos, *menos* que los 53 de inocuidad, y aun así formó tópico propio, porque su
exceso de cohesión sobre el azar es +0,336 contra +0,101.

El embedding agrupa por lo que la cláusula **dice**. Una queja por moho es, semánticamente,
una queja sobre el plato, y cae junto a las demás quejas sobre platos. **Son temas
transversales, no tópicos**, y el modelado de tópicos es la herramienta equivocada para
ellos.
"""),
    code("""
baja_masa = pd.read_csv(DATOS_PROCESADOS / "temas_baja_masa.csv")
baja_masa[["tema", "fragmentos", "rating", "pct_1_2_estrellas", "pct_atipicos"]]
"""),
    md("""
> **Cómo hay que leer estas cifras.** Salen de expresiones regulares estrechas sobre el
> texto: recuperan un subconjunto reconocible de cada tema y tienen falsos positivos y
> negativos documentados. **Acotan el orden de magnitud; no lo miden.** No deben
> presentarse como prevalencias.

### 6.7 Calidad del modelo, sin adornos
"""),
    code("""
pd.read_csv(DATOS_PROCESADOS / "calidad_modelo.csv")
"""),
    md("""
Un `c_v` de 0,484 es moderado: aceptable para texto corto, lejos del 0,55-0,65 que suele
considerarse bueno. **El `c_npmi` cercano a cero es el dato incómodo**: dice que los
términos de un tópico no coaparecen mucho más de lo que cabría por azar.

Hay una causa estructural —el fragmento mediano tiene 10 palabras, así que dos términos
rara vez caben en el mismo documento— pero **no se puede afirmar que los tópicos sean
léxicamente coherentes**. Lo que sostiene su interpretación es la lectura de sus
fragmentos, que está en `docs/evidencia_topicos.md` con cinco ejemplos por tópico.
"""),

    # ------------------------------------------------------------------- insights
    md("""
## 7. Insights

**1. El esquema tradicional captura la mayor parte, pero no todo.** Dos tercios del
corpus agrupado hablan de las seis dimensiones. Un 13 % habla de atributos que el esquema
no contempla, y dos de ellos son completamente invisibles para el diccionario.

**2. Una quinta parte de las reseñas no describe: juzga.** «Recomendado», «volvería»,
«excelente experiencia». Es un hallazgo sobre el género discursivo de la reseña: mucha
gente escribe para emitir un veredicto, no para informar. Ese 20 % no sirve para evaluar
atributos, ni con el esquema ni con el modelo.

**3. Las dimensiones no son igual de reales.** La espera se comporta como un tema
verdadero: vocabulario propio y concentración del 62,7 % en un tópico. Comida se comporta
como una etiqueta que lo toca todo: 38 tópicos, 11,8 % de concentración. Tratarlas como
seis categorías equivalentes es una simplificación que los datos no respaldan.

**4. La espera es el problema, y es el único.** 1,88 estrellas de media y el 75,8 % de
reseñas de una o dos. Ningún otro tema baja de tres. No es un problema entre varios: es
**el** problema.

**5. Lo mejor valorado no está en el esquema.** Ocasión de consumo (4,58) y referente en
la ciudad (4,55) son los dos atributos mejor calificados del corpus, y los dos son
emergentes. Los comensales valoran **para quién sirve el sitio** y **qué lugar ocupa en
la ciudad**, y el esquema tradicional no pregunta por ninguna de las dos cosas.

**6. Lo que el método no ve es desproporcionadamente crítico.** Los fragmentos sin
asignar promedian 3,20 estrellas contra 3,70 del corpus. Los temas transversales
—inocuidad 1,62, cobro 1,87— son lo peor calificado del estudio. **Cualquier lectura que
se quede en los tópicos formados dará una imagen más amable de la que el corpus
sostiene.**

**7. Y hay un sesgo con signo.** Ninguno de los seis tópicos de atributo emergente es
negativo. No es que no haya quejas sobre atributos nuevos: es que los emergentes que
alcanzaron masa y cohesión para formar tópico son **los positivos**. Los negativos se
quedaron dispersos.
"""),

    # ------------------------------------------------------------ recomendaciones
    md("""
## 8. Recomendaciones

### Para el establecimiento

**Atacar la espera antes que nada.** Es el único tema por debajo de tres estrellas y
concentra el malestar del corpus. Cualquier inversión en comunicación digital rinde poco
mientras ese tema siga generando reseñas de una estrella.

**Comunicar la ocasión, no solo el producto.** El atributo mejor valorado del corpus es
*para quién es el sitio*: familia, amigos, celebración. Casi ningún establecimiento lo
usa como eje de su comunicación, y es el que los clientes premian con mejor calificación.

**Reivindicar el lugar en la ciudad.** «Referente gastronómico de Popayán» es el segundo
mejor valorado. Para los locales del centro histórico se solapa con el patrimonio, que
también puntúa alto (4,45).

**Resolver lo operativo invisible.** Medios de pago y horarios desactualizados generan
reseñas muy negativas y no cuestan nada de arreglar: poner un datáfono, actualizar el
horario en Google Maps, contestar el teléfono.

**Vigilar la inocuidad por separado.** Es el tema peor calificado del estudio (1,62) y
ningún panel de dimensiones lo va a mostrar, porque se disuelve dentro de «comida». Hay
que buscarlo explícitamente.

### Para quien haga análisis de reseñas

**Segmentar antes de analizar.** Pasar de la reseña al fragmento duplica la proporción
de unidades con un solo tema, del 20,9 % al 42,0 %.

**No confiar en las métricas de coherencia para texto corto.** El `c_npmi` cercano a cero
no significa que los tópicos sean malos: significa que la métrica no puede funcionar con
fragmentos de 10 palabras. La validación tiene que ser por lectura.

**Combinar modelado de tópicos con búsqueda dirigida.** Los asuntos transversales
—inocuidad, cobro— no forman tópico con ningún parámetro, porque su cohesión semántica es
baja. Hacen falta las dos herramientas: el modelo para lo que emerge, reglas de
recuperación para lo que atraviesa.

**Reportar siempre la línea base.** Un AMI de 0,41 no significa nada sin saber que el
azar da 0,00 en esa misma partición.

### Trabajo futuro

- **Ampliar el corpus** a más ciudades, para ver si los atributos emergentes son de
  Popayán o del género de la reseña gastronómica.
- **Conseguir un identificador de autor real**, que permitiría deduplicar con precisión y
  analizar trayectorias de quienes reseñan varias veces.
- **Modelar la inocuidad como clasificación supervisada**, ya que el agrupamiento no
  llega: etiquetar unos cientos de fragmentos y entrenar un clasificador.
- **Medir el efecto de la respuesta del propietario** sobre la calificación posterior,
  cruzando el componente Web Analytics con el temporal.
"""),

    # -------------------------------------------------------------- limitaciones
    md("""
## 9. Limitaciones

1. **La coherencia por co-ocurrencia es prácticamente nula** (`c_npmi` −0,038). Hay causa
   estructural, pero no se puede afirmar que los tópicos sean léxicamente coherentes.
2. **Los temas de baja masa se miden con reglas de piso**, con falsos positivos y
   negativos documentados. Acotan el orden de magnitud; no lo miden.
3. **La deduplicación usa un proxy débil**: sin identificador de autor, la clave usa el
   número de reseñas de la persona. Afecta a 2 filas de 2.432.
4. **Hay una fuga en la detección de idioma heredada**: un fragmento en alfabeto árabe
   pasó el filtro. Es 1 de 5.913 y quedó sin asignar.
5. **El umbral de agrupamiento sesga qué atributos emergentes se ven**, y el sesgo tiene
   signo: los que forman tópico son los positivos.
6. **Cada fragmento hereda la calificación de su reseña.** El rating de un tópico no es la
   valoración del tema, sino la de las reseñas donde aparece. Por eso no se aplica
   ninguna prueba de significancia que asuma independencia.
7. **Los temas transversales no son tópicos**, y su presencia se sostiene con reglas de
   recuperación y lectura, no con el modelo.
"""),
    md("""
---

Todos los recursos están disponibles en el repositorio del proyecto,
[github.com/JLosada-Dev/topicos-popayan](https://github.com/JLosada-Dev/topicos-popayan).
Las rutas de la tabla son relativas a su raíz.

## Anexos

| Recurso | Qué contiene |
|---|---|
| `notebooks/proyecto_final.ipynb` | Este mismo notebook, el estudio completo |
| `notebooks/00_preparacion.ipynb` | Del corpus a los fragmentos, con la validación de las etiquetas |
| `notebooks/01_caracterizacion.ipynb` | Objetivo 1: composición, calidad, distribuciones |
| `notebooks/02_topicos.ipynb` | Objetivo 2: embeddings, BERTopic, sensibilidad |
| `notebooks/03_evaluacion.ipynb` | Objetivo 3: coherencia, AMI, temas transversales |
| `docs/evidencia_topicos.md` | Los 41 tópicos con cinco fragmentos cada uno |
| `docs/decisiones_metodologicas.md` | 15 decisiones con su alternativa y por qué se descartó |
| `docs/bitacora.md` | Trazabilidad completa, con fecha y cifras |
| `dataset/` | Los cinco archivos de datos con su diccionario y sus hashes |
| `app/` | El dashboard: `uv run streamlit run app/main.py` |
"""),
]
