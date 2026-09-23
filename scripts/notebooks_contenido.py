"""Contenido de los cuatro notebooks, en una sola fuente.

Las versiones local y Colab comparten estas celdas exactamente; solo difieren en el
preámbulo, que resuelve dependencias y acceso a los datos. Así no hay dos copias que
puedan divergir.
"""


def md(texto: str) -> tuple:
    return ("markdown", texto.strip())


def code(texto: str) -> tuple:
    return ("code", texto.strip())


CIERRE_COMUN = md("""
---

*Este notebook lee de `data/processed/` los resultados ya calculados. Los scripts que
los producen están en `scripts/` y las decisiones que los sustentan, con sus cifras, en
`docs/bitacora.md` y `docs/decisiones_metodologicas.md`.*
""")


# --------------------------------------------------------------------------- 00
PREPARACION = [
    md("""
# 00 · Preparación del corpus de fragmentos

**Etapa de CRISP-DM:** preparación de los datos. Alimenta el **objetivo específico 1**
—caracterizar el corpus y definir los requerimientos de su preparación— y construye la
unidad de análisis que usan los objetivos 2 y 3.

Parte de las 2.432 reseñas en español ya seleccionadas en el proyecto previo
`reputacion-popayan` (solo lectura) y produce `data/processed/fragmentos.csv`.

**La unidad de análisis es el fragmento**: la reseña partida en cláusulas, es decir la
oración más los cortes en conectores adversativos. Cada fragmento conserva el
`review_id` de su reseña de origen.

Dos decisiones separan este trabajo del original y se validan más abajo:

1. Se **re-segmentan** las reseñas en vez de reutilizar `sentimiento_fragmentos.csv`,
   que solo guarda las cláusulas que activan alguna dimensión y está sesgado hacia el
   vocabulario del diccionario.
2. Las dimensiones se **recalculan sobre cada fragmento**, no se heredan de la reseña.
"""),
    code("""
import pandas as pd

from src.config import DIMENSIONES, DATOS_PROCESADOS, MANIFIESTO
from src.diccionario import cargar_diccionario
from src.preparacion import nombres_establecimientos, patron_nombres_completos, patrones_para
from src.preparacion import enmascarar_locales, texto_para_ctfidf
from src.segmentacion import LARGO_MINIMO_FRAGMENTO, segmentar

pd.set_option("display.max_colwidth", 95)

fragmentos = pd.read_csv(DATOS_PROCESADOS / "fragmentos.csv")
print(f"{len(fragmentos)} fragmentos · {fragmentos['review_id'].nunique()} reseñas")
"""),
    md("""
## 1. Trazabilidad de lo heredado

Cada archivo leído del proyecto original queda registrado con su número de filas y su
hash SHA-256. Si alguno cambiara, el hash lo delata y el análisis deja de ser
reproducible sin que nadie se entere.
"""),
    code("""
pd.read_csv(MANIFIESTO)
"""),
    md("""
## 2. Embudo: de 8.451 reseñas a 5.913 fragmentos

El filtro de idioma y el de largo mínimo vienen del proyecto original y no se
recalculan. La única pérdida que introduce este trabajo son los 2 duplicados reales.

Ojo con la lectura: **la unidad cambia a mitad del embudo**. Las 2.430 reseñas producen
5.913 fragmentos porque cada reseña se parte en 2,4 cláusulas en promedio.
"""),
    code("""
embudo = pd.DataFrame(
    [
        ("Reseñas del corpus heredado", 8451, "reseñas"),
        ("Con texto y ≥ 50 caracteres", 2645, "reseñas"),
        ("En español", 2432, "reseñas"),
        ("Sin duplicado real", 2430, "reseñas"),
        ("Fragmentos por cláusula", len(fragmentos), "fragmentos"),
    ],
    columns=["etapa", "n", "unidad"],
)
embudo
"""),
    md("""
### Los duplicados, y una limitación que hay que declarar

Se elimina solo el duplicado real: misma persona y mismo texto. **El corpus heredado no
trae identificador de autor**, solo `autor_n_resenas`, que es el único proxy disponible.
Es débil en ambas direcciones y afecta a 2 filas de 2.432, así que no altera ningún
resultado, pero la deduplicación no debe presentarse como exacta.
"""),
    md("""
## 3. Segmentación por cláusula

La regla se copió sin cambios de `src/sentimiento.py` del proyecto original, para que
los resultados sigan siendo comparables entre los dos trabajos. Corta en puntuación
`.!?;¡¿`, salto de línea, `<br>` y los conectores adversativos (*pero, aunque, sin
embargo, no obstante, eso sí, lo malo, lo único, mientras que*), que **se consumen en el
corte**. Descarta los fragmentos de menos de 10 caracteres.

El corte en conectores es lo que separa opiniones de signo opuesto dentro de una misma
oración, que es justo donde la reseña dice dos cosas distintas.
"""),
    code("""
ejemplos = [
    "Un lugar pequeño pero con comida deliciosa",
    "La comida deliciosa. El servicio muy lento.",
    "Comida rica, aunque el precio es alto. Ok.",
]
for texto in ejemplos:
    print(f"{texto!r}\\n   -> {segmentar(texto)}\\n")
print(f"largo mínimo aplicado: {LARGO_MINIMO_FRAGMENTO} caracteres")
"""),
    md("""
## 4. Enmascarado de nombres de establecimiento

Los nombres propios se reemplazan por `[LOCAL]` para que el modelo agrupe por *lo que se
dice* y no por *de quién se habla*. La búsqueda es insensible a mayúsculas y tildes,
pero el reemplazo se hace sobre el texto original, que conserva sus tildes.

Tres reglas evitan que el enmascarado se coma texto legítimo. Sin ellas afectaba al
14,0 % de los fragmentos por falsos positivos; con ellas, al 1,8 %:

- **Los nombres de un solo token no se enmascaran.** «Carantanta» es a la vez un local y
  un plato patrimonial.
- **Para el local de la propia reseña** se aceptan abreviaturas; **para los demás** se
  exige el nombre completo.
- **La secuencia debe aportar algo propio del local**: se descartan las que son solo
  palabras funcionales (`de la`, de «El Fogón de la Abuela») y las que son funcionales
  más un término del diccionario (`de comidas`, de «Plazoleta de Comidas»), que borrarían
  justo la señal que se quiere medir.
"""),
    code("""
patron = patron_nombres_completos(nombres_establecimientos())
casos = [
    ("En La Cosecha probé el salpicón payanés", "La Cosecha Parrillada"),
    ("la calidad de la comida es buena", "El Fogón de la Abuela"),
    ("amplia variedad de comidas", "Plazoleta de Comidas"),
]
for texto, propio in casos:
    salida, n = enmascarar_locales(texto, patrones_para(propio, patron))
    print(f"{texto!r}\\n   local: {propio!r}\\n   -> {salida!r}  ({n} marcas)\\n")
"""),
    md("""
## 5. Dos textos con propósitos distintos

- **`texto`** es el fragmento enmascarado pero natural: conserva mayúsculas, tildes y
  stopwords. Va a los **embeddings**, porque el modelo de lenguaje espera texto tal como
  se escribe.
- **`texto_limpio`** es minúsculas, sin puntuación y sin stopwords. Solo alimenta el
  **c-TF-IDF**, que nombra los tópicos.

Las **negaciones se conservan** en `texto_limpio`. Quitarlas, como haría una lista de
stopwords estándar, etiquetaba un tópico con su contrario exacto: el tópico de «no
recomiendo», con rating medio 1,53, aparecía rotulado «recomiendo».
"""),
    code("""
for texto in ["No lo recomiendo", "Lo recomiendo mucho", "¡Comida DELICIOSA, excelente!"]:
    print(f"{texto!r:<36} -> {texto_para_ctfidf(texto)!r}")
"""),
    md("""
## 6. Validación: las etiquetas por fragmento reproducen la medición del original

Esta es la comprobación que autoriza a recalcular las dimensiones por fragmento en vez
de heredarlas. Si se agregan de vuelta a nivel de reseña con un `any` por `review_id`,
deben coincidir con la medición del proyecto original, que se hizo sobre el texto
completo y está validada.
"""),
    code("""
from src.config import DIMENSIONES_APTAS_ES

heredada = pd.read_csv(DIMENSIONES_APTAS_ES)
heredada = heredada[heredada["review_id"].isin(fragmentos["review_id"])]

comparacion = pd.DataFrame({
    "heredada": [int(heredada[d].sum()) for d in DIMENSIONES],
    "recalculada": [int(fragmentos.groupby("review_id")[d].any().sum()) for d in DIMENSIONES],
}, index=list(DIMENSIONES))
comparacion["diferencia"] = comparacion["recalculada"] - comparacion["heredada"]
comparacion["pct_diferencia"] = (100 * comparacion["diferencia"] / comparacion["heredada"]).round(2)
comparacion.sort_values("heredada", ascending=False)
"""),
    md("""
**La diferencia máxima es de 10 reseñas en `ambiente`, un 1,0 %**, y se explica por las
2 reseñas eliminadas y por el enmascarado. Recalcular sobre cláusulas no pierde señal,
así que la decisión queda validada.

A nivel de fragmento las cifras son mucho más bajas porque cambia el denominador: una
reseña de tres cláusulas habla de comida en una sola de ellas.
"""),
    code("""
prevalencia = pd.DataFrame({
    "fragmentos": [int(fragmentos[d].sum()) for d in DIMENSIONES],
    "pct_fragmentos": [round(100 * fragmentos[d].mean(), 1) for d in DIMENSIONES],
    "pct_resenas": [round(100 * fragmentos.groupby("review_id")[d].any().mean(), 1)
                    for d in DIMENSIONES],
}, index=list(DIMENSIONES))
prevalencia.sort_values("fragmentos", ascending=False)
"""),
    md("""
## 7. Dimensiones activas por fragmento

El AMI del objetivo 3 se calcula solo sobre fragmentos con **exactamente una** dimensión
activa. Esta tabla dice cuánto corpus queda disponible para esa medida.
"""),
    code("""
reparto = fragmentos["n_dim"].value_counts().sort_index().to_frame("fragmentos")
reparto["%"] = (100 * reparto["fragmentos"] / len(fragmentos)).round(1)
reparto.index.name = "n_dim"
print(reparto.to_string())
print(f"\\ndisponible para AMI: {(fragmentos['n_dim'] == 1).sum()} fragmentos "
      f"({100 * (fragmentos['n_dim'] == 1).mean():.1f} %)")
print(f"sin ninguna dimensión: {(fragmentos['n_dim'] == 0).sum()} "
      f"({100 * (fragmentos['n_dim'] == 0).mean():.1f} %)")
"""),
    md("""
## 8. Estructura del archivo de salida
"""),
    code("""
print(f"{len(fragmentos)} filas × {len(fragmentos.columns)} columnas")
fragmentos[["fragmento_id", "establecimiento", "zona", "rating",
            "texto", "texto_limpio", "n_dim"]].head(4)
"""),
    md("""
## Hallazgos

1. **El embudo cierra sin pérdidas inesperadas.** De 8.451 reseñas quedan 2.432 en
   español con al menos 50 caracteres, exactamente la cifra esperada, y tras eliminar 2
   duplicados reales se obtienen **5.913 fragmentos de 2.430 reseñas**. Ninguna reseña
   pierde todos sus fragmentos.

2. **Recalcular las dimensiones por fragmento no pierde señal.** Al reagregarlas a nivel
   de reseña coinciden con la medición validada del proyecto original con una diferencia
   máxima del 1,0 %. Esto autoriza la decisión de no heredarlas.

3. **Segmentar por cláusula mejora la pureza temática.** El 42,0 % de los fragmentos
   tiene exactamente una dimensión activa, contra el 20,9 % de las reseñas completas.
   El AMI del objetivo 3 dispone entonces del doble de corpus limpio.

4. **El 29,1 % de los fragmentos no activa ninguna dimensión.** Casi un tercio del corpus
   queda fuera del esquema a priori. Son los fragmentos donde el modelado de tópicos
   puede aportar algo que el diccionario no ve, y son exactamente los que
   `sentimiento_fragmentos.csv` habría descartado.

5. **Dos correcciones fueron necesarias y quedan documentadas:** la regla de enmascarado
   del proyecto original, aplicada globalmente, producía un 14,0 % de falsos positivos;
   y quitar las negaciones del texto de c-TF-IDF invertía la etiqueta de los tópicos
   negativos.
"""),
    CIERRE_COMUN,
]


# --------------------------------------------------------------------------- 01
CARACTERIZACION = [
    md("""
# 01 · Caracterización del corpus

**Objetivo específico 1.** Caracterizar el corpus de reseñas mediante análisis
descriptivo y verificación de calidad, para definir los requerimientos de su
preparación.

El notebook describe qué hay en el corpus —composición, calidad, distribución por
calificación, establecimiento y zona— y deja explícitos los problemas que condicionan
todo lo que viene después.
"""),
    code("""
import pandas as pd

from src.config import DIMENSIONES, DATOS_PROCESADOS, FIGURAS

pd.set_option("display.max_colwidth", 95)

fragmentos = pd.read_csv(DATOS_PROCESADOS / "fragmentos.csv")
resenas = fragmentos.groupby("review_id").agg(
    establecimiento=("establecimiento", "first"),
    zona=("zona", "first"),
    rating=("rating", "first"),
    n_fragmentos=("fragmento_id", "size"),
    largo=("largo_caracteres", "sum"),
)
print(f"{len(fragmentos)} fragmentos · {len(resenas)} reseñas · "
      f"{fragmentos['place_id'].nunique()} establecimientos")
"""),
    md("""
## 1. Composición

El corpus es de reseñas de Google Maps de establecimientos gastronómicos de Popayán,
en español y con al menos 50 caracteres. La unidad de análisis es el fragmento.
"""),
    code("""
composicion = pd.Series({
    "Reseñas": len(resenas),
    "Fragmentos": len(fragmentos),
    "Establecimientos": fragmentos["place_id"].nunique(),
    "Zonas": fragmentos["zona"].nunique(),
    "Fragmentos por reseña (mediana)": resenas["n_fragmentos"].median(),
    "Fragmentos por reseña (máximo)": resenas["n_fragmentos"].max(),
}, name="valor").to_frame()
composicion
"""),
    md("""
## 2. Longitud de las unidades

El fragmento mediano tiene 10 palabras. Es una unidad corta, muy por debajo del truncado
de cualquier modelo de embeddings, pero también **demasiado corta para que dos términos
de un mismo tópico coaparezcan en ella**, lo que penaliza las medidas de coherencia por
co-ocurrencia que se calculan en el notebook 03.
"""),
    code("""
largos = pd.DataFrame({
    "caracteres": fragmentos["largo_caracteres"],
    "palabras": fragmentos["largo_palabras"],
}).describe(percentiles=[.25, .5, .75, .9]).round(1)
largos
"""),
    md("""
## 3. Verificación de calidad

Cuatro comprobaciones sobre el corpus que se hereda.
"""),
    code("""
nulos = fragmentos.isna().sum()
print("columnas con nulos:")
print(nulos[nulos > 0].to_string() if nulos.any() else "  ninguna")

vacios = int((fragmentos["texto_limpio"].fillna("").str.len() == 0).sum())
print(f"\\ntexto_limpio vacío tras las stopwords: {vacios} "
      f"({100 * vacios / len(fragmentos):.1f} %) — se conservan, porque su `texto` sí sirve")
print(f"texto duplicado exacto entre fragmentos: {fragmentos['texto'].duplicated().sum()}")
"""),
    md("""
### Una fuga en la detección de idioma heredada

Un fragmento está escrito en alfabeto árabe y pasó el filtro como apto en español. Es
1 de 5.913 (0,02 %) y quedó sin asignar a ningún tópico, así que no afecta ningún
resultado. Se deja constancia porque indica que la selección del corpus, que se reutiliza
por decisión, no es perfecta.
"""),
    code("""
import unicodedata

# La comprobación va en Python y no en `str.contains`: el motor de regex de pandas 3
# es RE2 vía Arrow, que no admite escapes \\uXXXX
ESCRITURAS_LATINAS = ("LATIN", "COMMON", "INHERITED")

def es_no_latino(texto):
    return any(
        not unicodedata.name(c, "").startswith(ESCRITURAS_LATINAS) and c.isalpha()
        for c in str(texto)
    )

fuga = fragmentos[fragmentos["texto"].map(es_no_latino)]
print(f"fragmentos con escritura no latina: {len(fuga)}")
fuga[["fragmento_id", "texto", "rating"]]
"""),
    md("""
## 4. Distribución por calificación

El corpus está **fuertemente sesgado hacia los extremos**, que es el patrón habitual de
las reseñas en línea: se escribe cuando se está muy satisfecho o muy molesto.
"""),
    code("""
por_rating = resenas["rating"].value_counts().sort_index().to_frame("reseñas")
por_rating["% reseñas"] = (100 * por_rating["reseñas"] / len(resenas)).round(1)
por_rating["fragmentos"] = fragmentos["rating"].value_counts().sort_index()
por_rating["% fragmentos"] = (100 * por_rating["fragmentos"] / len(fragmentos)).round(1)
por_rating.index.name = "estrellas"
print(por_rating.to_string())
print(f"\\nrating medio: reseña {resenas['rating'].mean():.2f} · "
      f"fragmento {fragmentos['rating'].mean():.2f}")
"""),
    md("""
**Cada fragmento hereda la calificación de su reseña**, y esa es una limitación
estructural del diseño: la calificación es una sola por reseña y se replica en sus 2,4
fragmentos promedio. De ahí que el rating medio por fragmento difiera del de reseña —las
reseñas largas pesan más— y que los fragmentos de una misma reseña no sean
observaciones independientes.
"""),
    code("""
comparacion = pd.DataFrame({
    "media de fragmentos por reseña": resenas.groupby("rating")["n_fragmentos"].mean().round(2),
    "reseñas": resenas["rating"].value_counts().sort_index(),
})
comparacion.index.name = "estrellas"
comparacion
"""),
    md("""
Las reseñas de 1 estrella son las más largas: quien se queja explica. Eso las
sobrerrepresenta en el corpus de fragmentos respecto al de reseñas, y hay que tenerlo
presente al leer cualquier porcentaje calculado sobre fragmentos.
"""),
    md("""
## 5. Distribución por establecimiento

Importa porque un corpus concentrado en pocos locales produciría tópicos que en realidad
describen un restaurante, no un tema.
"""),
    code("""
por_local = fragmentos["establecimiento"].value_counts()
resumen = pd.Series({
    "Establecimientos con fragmentos": len(por_local),
    "Fragmentos del local mayor": por_local.iloc[0],
    "% del corpus en el local mayor": round(100 * por_local.iloc[0] / len(fragmentos), 1),
    "% del corpus en los 10 mayores": round(100 * por_local.head(10).sum() / len(fragmentos), 1),
    "Mediana de fragmentos por local": int(por_local.median()),
}, name="valor").to_frame()
print(resumen.to_string())
por_local.head(8).to_frame("fragmentos")
"""),
    md("""
## 6. Distribución por zona

La zona viene del marco muestral y distingue si el establecimiento está dentro o fuera
del centro histórico, que es la variable con carga patrimonial del estudio.
"""),
    code("""
por_zona = fragmentos.groupby("zona").agg(
    fragmentos=("fragmento_id", "size"),
    resenas=("review_id", "nunique"),
    locales=("place_id", "nunique"),
    rating=("rating", "mean"),
).round(2)
por_zona["% fragmentos"] = (100 * por_zona["fragmentos"] / len(fragmentos)).round(1)
por_zona["% patrimonio"] = (100 * fragmentos.groupby("zona")["patrimonio"].mean()).round(1)
por_zona.sort_values("fragmentos", ascending=False)
"""),
    md("""
## 7. Prevalencia de las seis dimensiones
"""),
    code("""
prevalencia = pd.DataFrame({
    "fragmentos": [int(fragmentos[d].sum()) for d in DIMENSIONES],
    "% fragmentos": [round(100 * fragmentos[d].mean(), 1) for d in DIMENSIONES],
    "% reseñas": [round(100 * fragmentos.groupby("review_id")[d].any().mean(), 1)
                  for d in DIMENSIONES],
    "rating medio": [round(fragmentos.loc[fragmentos[d], "rating"].mean(), 2)
                     for d in DIMENSIONES],
}, index=list(DIMENSIONES))
prevalencia.sort_values("fragmentos", ascending=False)
"""),
    md("""
## 8. El embudo del corpus
"""),
    code("""
from IPython.display import Image, display

display(Image(filename=str(FIGURAS / "04_embudo_corpus.png"), width=900))
"""),
    md("""
## Hallazgos

1. **El corpus es pequeño y desbalanceado hacia los extremos.** 2.430 reseñas y 5.913
   fragmentos de unos 120 establecimientos, con una distribución de calificaciones en U
   típica de las reseñas en línea. Cualquier media hay que leerla sabiendo que la mezcla
   no es la de la población de comensales, sino la de quienes deciden escribir.

2. **Las reseñas negativas son más largas.** Las de 1 estrella aportan más fragmentos
   por reseña que las de 5, lo que las sobrerrepresenta en el corpus de fragmentos.
   Es el motivo por el que el rating medio del fragmento difiere del de la reseña.

3. **La concentración por establecimiento es moderada** y no amenaza la validez del
   modelado: ningún local domina el corpus.

4. **El fragmento mediano tiene 10 palabras.** Es bueno para los embeddings, pero
   demasiado corto para que dos términos de un tópico coaparezcan, lo que condiciona las
   medidas de coherencia del notebook 03 y hay que advertirlo antes de interpretarlas.

5. **Requerimientos de preparación que se derivan de aquí:** segmentar por cláusula para
   ganar pureza temática, enmascarar los nombres de establecimiento para que el modelo no
   agrupe por local, conservar las negaciones en el texto de c-TF-IDF, y no aplicar
   pruebas que asuman independencia entre fragmentos.
"""),
    CIERRE_COMUN,
]


# --------------------------------------------------------------------------- 02
TOPICOS = [
    md("""
# 02 · Modelado de tópicos

**Objetivo específico 2.** Determinar los temas emergentes mediante modelado de tópicos,
para representar los asuntos que abordan los comensales.

El notebook carga el modelo ya entrenado y congelado, describe sus 41 tópicos, presenta
la estructura de dos niveles que los agrupa en 14 temas y cierra con el análisis de
sensibilidad que delimita qué puede y qué no puede encontrar este método.
"""),
    code("""
import pandas as pd

from src.config import DATOS_PROCESADOS, SEMILLA
from src.embeddings import MODELO_EMBEDDINGS, obtener
from src.topicos import ATIPICO, MIN_SAMPLES, MIN_TOPIC_SIZE, UMBRAL_REDUCCION
from src.topicos import cargar_modelo_guardado

pd.set_option("display.max_colwidth", 110)

fragmentos = pd.read_csv(DATOS_PROCESADOS / "fragmentos.csv").merge(
    pd.read_csv(DATOS_PROCESADOS / "fragmentos_topicos.csv"),
    on=["fragmento_id", "review_id"],
)
etiquetas = pd.read_csv(DATOS_PROCESADOS / "topicos_etiquetados.csv")
print(f"{len(fragmentos)} fragmentos · {len(etiquetas)} tópicos")
"""),
    md("""
## 1. Embeddings

`paraphrase-multilingual-MiniLM-L12-v2` sobre la columna `texto`, que es el fragmento
enmascarado pero natural. Se calculan una sola vez y se guardan en disco junto a un
índice de `fragmento_id`; la función los **realinea por identificador, no por posición**,
así que reordenar el CSV no rompe la correspondencia.

Se comparó contra `intfloat/multilingual-e5-small` y se descartó: su espacio es muy
anisótropo —el coseno entre dos fragmentos cualesquiera está entre 0,79 y 0,89, contra
0,25 de media en MiniLM— y con el mismo umbral colapsa en 5 tópicos.
"""),
    code("""
embeddings, info = obtener(fragmentos, MODELO_EMBEDDINGS)
print(f"modelo: {info['modelo']}")
print(f"matriz: {embeddings.shape}  ({info['dimension']} dimensiones)  origen: {info['origen']}")
"""),
    md("""
## 2. Configuración congelada

| Componente | Valor |
|---|---|
| UMAP | `n_neighbors=15`, `n_components=5`, `min_dist=0.0`, coseno, `random_state=42` |
| HDBSCAN | `min_cluster_size=30`, `min_samples=15` |
| c-TF-IDF | `texto_limpio` con negaciones, unigramas y bigramas, `min_df=2` |
| Reducción de atípicos | estrategia `embeddings`, umbral 0,65 |
| Fusión | manual, un solo par (referente gastronómico de la ciudad) |

Dos parámetros merecen explicación porque no son los valores por defecto:

- **`min_samples=15`.** Con `min_cluster_size=50` el modelo minimizaba la partición por
  tono, pero solo porque fundía todo lo negativo en un cajón del 26,9 % del corpus con
  rating 2,40. La métrica premiaba el defecto.
- **Umbral de reducción 0,65.** El de BERTopic (0,30) reasigna el 99 % de los atípicos
  pero mal: metía «Volveremos» en el tópico de quejas. 0,65 queda justo bajo el coseno
  medio de los fragmentos ya asignados a su centroide (0,676), de modo que un atípico se
  reasigna solo si encaja tan bien como uno típico.
""" ),
    code("""
modelo = cargar_modelo_guardado()
asignados = int((fragmentos["topico"] != ATIPICO).sum())
print(f"min_cluster_size={MIN_TOPIC_SIZE} · min_samples={MIN_SAMPLES} · "
      f"umbral_reduccion={UMBRAL_REDUCCION} · semilla={SEMILLA}")
print(f"\\ntópicos: {len(etiquetas)}")
print(f"asignados: {asignados} ({100 * asignados / len(fragmentos):.1f} %)")
print(f"atípicos:  {len(fragmentos) - asignados} "
      f"({100 * (1 - asignados / len(fragmentos)):.1f} %)")
"""),
    md("""
## 3. Los 41 tópicos

Ordenados por tamaño, con su tema, polaridad y calificación media. Los umbrales de
polaridad son **positiva ≥ 4,2 · negativa ≤ 2,5 · mixta en el resto**, y son
convencionales: se declaran para que el lector sepa de dónde sale la etiqueta.
"""),
    code("""
tabla = etiquetas.sort_values("n", ascending=False)[
    ["topico_id", "tema", "subtema", "tipo", "polaridad", "n", "pct_corpus",
     "rating", "pct_1_2_estrellas"]
].fillna("")
tabla
"""),
    md("""
## 4. Términos y ejemplos de los tópicos mayores

Los términos vienen del c-TF-IDF sobre `texto_limpio`; los ejemplos son una muestra
aleatoria reproducible de cada tópico, **no** los documentos representativos de
BERTopic, para no sesgar la lectura hacia el centro del tópico.

La evidencia completa de los 41 tópicos, con cinco fragmentos cada uno, está en
`docs/evidencia_topicos.md`.
"""),
    code("""
nombres = etiquetas.set_index("topico_id")

def describir(topico, n_ejemplos=3):
    sub = fragmentos[fragmentos["topico"] == topico]
    fila = nombres.loc[topico]
    subtema = fila["subtema"] if isinstance(fila["subtema"], str) and fila["subtema"] else ""
    titulo = f"T{topico} · {fila['tema']}" + (f" / {subtema}" if subtema else "")
    terminos = [t for t, _ in (modelo.get_topic(topico) or [])][:8]
    print(f"{titulo}  (n={len(sub)}, rating {fila['rating']}, {fila['polaridad']})")
    print(f"   {', '.join(terminos)}")
    for texto in sub.sample(n_ejemplos, random_state=SEMILLA)["texto"]:
        print(f"   · {texto[:120]}")
    print()

for topico in etiquetas.nlargest(8, "n")["topico_id"]:
    describir(topico)
"""),
    md("""
## 5. Estructura de dos niveles

Los 41 tópicos se agrupan en **14 temas**, clasificados en tres tipos:

- **`atributo_esquema`** — habla de una de las seis dimensiones a priori.
- **`atributo_nuevo`** — habla de un atributo que el esquema no contempla.
- **`valoracion_global`** — no describe ningún atributo, emite un veredicto sobre la
  experiencia.

La asignación es manual, hecha leyendo términos y fragmentos, y vive en
`src/etiquetas.py` para que sea revisable y reversible. El modelo no se modifica.
"""),
    code("""
temas = pd.read_csv(DATOS_PROCESADOS / "temas_consolidado.csv")
temas[["tema", "tipo", "n_topicos", "fragmentos", "pct_asignado",
       "rating", "pct_1_2_estrellas", "polaridad_dominante"]]
"""),
    code("""
por_tipo = temas.groupby("tipo").agg(
    topicos=("n_topicos", "sum"), fragmentos=("fragmentos", "sum")
)
por_tipo["% del corpus asignado"] = (100 * por_tipo["fragmentos"] / asignados).round(1)
por_tipo.sort_values("fragmentos", ascending=False)
"""),
    md("""
**Un quinto del corpus asignado no describe ningún atributo.** Son 970 fragmentos de
valoración global, recomendación, intención de volver y satisfacción. Para el objetivo 3
no tienen con qué contrastarse, porque no describen un aspecto de la experiencia sino un
veredicto sobre ella.

Los **atributos emergentes** son el 13,0 % del corpus asignado: ocasión de consumo,
referente en la ciudad, infraestructura y espacio, y medios de pago. Ninguno cabe en las
seis dimensiones.
"""),
    code("""
from IPython.display import Image, display
from src.config import FIGURAS

display(Image(filename=str(FIGURAS / "01_distribucion_por_tipo.png"), width=900))
"""),
    md("""
### Una asimetría con consecuencias

Ninguno de los seis tópicos de tipo `atributo_nuevo` es negativo. No significa que no
haya quejas sobre atributos nuevos —inocuidad y cobro son de los temas más negativos del
corpus— sino que **los atributos emergentes que alcanzaron masa y cohesión para formar
tópico son los positivos**. Interpretar los atributos emergentes solo por los tópicos
formados subestimaría sistemáticamente lo negativo.
"""),
    code("""
polaridad = temas.pivot_table(index="tipo", columns="polaridad_dominante",
                              values="fragmentos", aggfunc="sum", fill_value=0)
polaridad
"""),
    md("""
## 6. Análisis de sensibilidad: qué NO puede encontrar este método

Cuatro temas aparecieron al leer los atípicos —inocuidad, honestidad en el cobro,
horarios e información digital, infraestructura frente al clima— pero **ninguno forma
tópico propio**. La hipótesis inicial fue que se debía al umbral de tamaño mínimo. Se
puso a prueba corriendo la misma configuración con `min_cluster_size` en 20 y en 15.

Un tema «forma tópico propio» si existe un tópico donde al menos el 25 % de sus
fragmentos son del tema y que concentra al menos el 20 % del tema.
"""),
    code("""
sensibilidad = pd.read_csv(DATOS_PROCESADOS / "sensibilidad_umbral.csv")
sensibilidad
"""),
    md("""
**La hipótesis no se sostiene: bajar el umbral no los agrupa, los dispersa más.** La
concentración de cada tema en su tópico mayor *cae* al bajar `min_cluster_size` —de
26,4 % a 11,3 % en inocuidad, de 38,3 % a 12,8 % en horarios.

La causa real es la **cohesión** en el espacio de embeddings, no la masa. Se compara la
similitud media entre los pares de cada grupo contra una línea base de grupos aleatorios
del mismo tamaño.
"""),
    code("""
cohesion = pd.read_csv(DATOS_PROCESADOS / "cohesion_temas.csv")
cohesion
"""),
    md("""
La comparación decisiva es **medios de pago contra inocuidad**: medios de pago tiene 34
fragmentos, menos que los 53 de inocuidad, y aun así formó tópico propio con
`min_cluster_size=30`, porque su exceso de cohesión sobre el azar es +0,336 contra
+0,101.

La explicación es que el embedding agrupa por lo que la cláusula *dice*, no por la marca
superficial que usa la regla de búsqueda. Una queja por moho es, semánticamente, una
queja sobre el plato, y cae junto a las demás quejas sobre platos. «No tienen datáfono»,
en cambio, no se parece a nada más del corpus, y por eso se agrupa.
"""),
    md("""
## Hallazgos

1. **Emergen 41 tópicos que se agrupan en 14 temas**, sobre el 80,7 % del corpus. El
   tópico mayor es solo el 6,0 %, así que no hay ningún cajón que acapare la solución.

2. **Los temas emergentes existen y son cuatro:** ocasión de consumo, referente
   gastronómico de la ciudad, infraestructura y espacio, y medios de pago. Suman el
   13,0 % del corpus asignado y ninguno cabe en las seis dimensiones a priori. Dos de
   ellos —medios de pago e infraestructura— son además invisibles para el diccionario:
   el 91 % y el 76 % de sus fragmentos no activan ninguna dimensión.

3. **Un quinto del corpus asignado no habla de atributos**, sino que emite veredictos.
   Es un hallazgo sobre el género discursivo de la reseña, y limita lo que el objetivo 3
   puede contrastar.

4. **Los atributos emergentes que el método encuentra son sistemáticamente los
   positivos.** Los negativos —inocuidad, cobro, horarios— existen en el corpus pero no
   forman tópico.

5. **Y no lo forman por cohesión, no por masa.** El análisis de sensibilidad descarta la
   explicación del umbral: bajar `min_cluster_size` los dispersa más. Son **temas
   transversales**, que atraviesan cláusulas de asuntos distintos en vez de constituir un
   asunto propio. El modelado de tópicos es la herramienta equivocada para ellos, y hay
   que sostenerlos con reglas de recuperación y análisis cualitativo.
"""),
    CIERRE_COMUN,
]


# --------------------------------------------------------------------------- 03
EVALUACION = [
    md("""
# 03 · Evaluación y contraste con las dimensiones

**Objetivo específico 3.** Evaluar la correspondencia de los temas con las dimensiones
predefinidas y su relación con la calificación, mediante medidas de acuerdo y análisis
descriptivo, para derivar orientaciones de comunicación digital.

El notebook mide la calidad del modelo, cruza sus tópicos contra las seis dimensiones,
calcula el AMI con su línea base, describe la relación con la calificación, cuantifica
los temas transversales y cierra con las limitaciones que condicionan todo lo anterior.
"""),
    code("""
import numpy as np
import pandas as pd
from sklearn.metrics import adjusted_mutual_info_score, adjusted_rand_score

from src.config import DIMENSIONES, DATOS_PROCESADOS, FIGURAS, SEMILLA
from src.topicos import ATIPICO

pd.set_option("display.max_colwidth", 100)

fragmentos = pd.read_csv(DATOS_PROCESADOS / "fragmentos.csv").merge(
    pd.read_csv(DATOS_PROCESADOS / "fragmentos_topicos.csv"),
    on=["fragmento_id", "review_id"],
)
etiquetas = pd.read_csv(DATOS_PROCESADOS / "topicos_etiquetados.csv")
temas = pd.read_csv(DATOS_PROCESADOS / "temas_consolidado.csv")
asignados = fragmentos[fragmentos["topico"] != ATIPICO]
print(f"{len(fragmentos)} fragmentos · {len(asignados)} asignados · {len(etiquetas)} tópicos")
"""),
    md("""
## 1. Calidad del modelo

Se reportan **dos** coherencias a propósito. `c_v` (Röder et al., 2015) es la medida de
referencia y permite comparar con la literatura; `c_npmi` es más conservadora y se le
reprocha menos sesgo optimista. La diversidad (Dieng et al., 2020) es la proporción de
palabras distintas entre las principales de todos los tópicos.
"""),
    code("""
calidad = pd.read_csv(DATOS_PROCESADOS / "calidad_modelo.csv")
calidad
"""),
    md("""
**Interpretación, sin adornos.** Un `c_v` de 0,484 es moderado: aceptable para texto
corto, lejos del 0,55-0,65 que suele considerarse bueno. **El `c_npmi` cercano a cero es
el dato incómodo**: dice que los términos principales de un tópico no coaparecen en el
mismo fragmento mucho más de lo que cabría por azar.

Hay una causa estructural —el fragmento mediano tiene 10 palabras, así que dos términos
del tópico rara vez caben en el mismo documento, y la medida penaliza la unidad de
análisis elegida— pero **no se puede afirmar que los tópicos sean léxicamente
coherentes**. Lo que sostiene su interpretación es la lectura de fragmentos, no el
indicador.

La diversidad de 0,664 significa que un tercio de los términos principales se repite
entre tópicos, lo que concuerda con la redundancia detectada al evaluar la fusión.
"""),
    code("""
coherencia_topico = etiquetas.dropna(subset=["c_v"]).sort_values("c_v")
columnas = ["topico_id", "tema", "subtema", "n", "c_v"]
print("Menos coherentes:")
print(coherencia_topico.head(6)[columnas].fillna("").to_string(index=False))
print("\\nMás coherentes:")
print(coherencia_topico.tail(6)[columnas].fillna("").to_string(index=False))
"""),
    md("""
Los menos coherentes son los tópicos de plato y de oferta —bebidas, carta y menú, café,
hamburguesas—, y tiene sentido: su vocabulario es una lista de cosas que no coaparecen
(«limonada, vinos, jugo, mango»). Los más coherentes son los grandes tópicos de
dimensión. La coherencia léxica mide lo que puede medir, no la calidad temática.
"""),
    md("""
## 2. Tabla cruzada: tópico por dimensión

Para cada tópico, el porcentaje de sus fragmentos que activa cada dimensión del
diccionario. Un tópico puede activar varias, porque las dimensiones no son excluyentes.
"""),
    code("""
cruzada = pd.read_csv(DATOS_PROCESADOS / "cruzada_topico_dimension.csv")
cruzada.sort_values("n", ascending=False).head(15)
"""),
    code("""
from IPython.display import Image, display

display(Image(filename=str(FIGURAS / "03_mapa_topico_dimension.png"), width=850))
"""),
    md("""
### En cuántos tópicos se reparte cada dimensión
"""),
    code("""
dispersion = []
for dimension in DIMENSIONES:
    sub = asignados[asignados[dimension]]
    reparto = sub["topico"].value_counts()
    dispersion.append({
        "dimension": dimension,
        "fragmentos": len(sub),
        "topicos": len(reparto),
        "% en el mayor": round(100 * reparto.iloc[0] / len(sub), 1),
        "% en los 3 mayores": round(100 * reparto.head(3).sum() / len(sub), 1),
        "topico principal": f"T{reparto.index[0]}",
    })
pd.DataFrame(dispersion).sort_values("% en el mayor", ascending=False)
"""),
    md("""
**Ninguna dimensión se concentra en un solo tópico.** La espera es la única con
correspondencia fuerte —casi dos tercios en un tópico—, y era previsible porque es un
asunto acotado y con vocabulario propio. **Comida es el caso opuesto**: se reparte en 38
tópicos y su tópico principal ni siquiera es de comida, sino el de experiencia global.
Es la dimensión más grande y la menos específica: casi cualquier elogio la menciona.
"""),
    md("""
## 3. AMI entre tópicos y dimensiones

Se calcula sobre los fragmentos con **exactamente una** dimensión activa, que es donde
la comparación tiene sentido: si un fragmento activa tres dimensiones, no hay una
etiqueta única contra la cual contrastar el tópico.

La línea base se estima permutando la etiqueta de dimensión 200 veces, lo que deja
intactos los tamaños de grupo. Sin esa referencia, un AMI no se puede interpretar.
"""),
    code("""
una = fragmentos[fragmentos["n_dim"] == 1].copy()
una["dimension"] = una[list(DIMENSIONES)].idxmax(axis=1)
con_topico = una[una["topico"] != ATIPICO]

def nulo(topicos, dimensiones, repeticiones=200):
    generador = np.random.default_rng(SEMILLA)
    valores = [adjusted_mutual_info_score(topicos, generador.permutation(dimensiones))
               for _ in range(repeticiones)]
    return float(np.mean(valores)), float(np.std(valores))

filas = []
for etiqueta, base in [("solo fragmentos asignados", con_topico),
                       ("atípicos como categoría", una)]:
    ami = adjusted_mutual_info_score(base["topico"], base["dimension"])
    media, desviacion = nulo(base["topico"].to_numpy(), base["dimension"].to_numpy())
    filas.append({
        "base": etiqueta, "n": len(base), "AMI": round(ami, 4),
        "ARI": round(adjusted_rand_score(base["topico"], base["dimension"]), 4),
        "nulo": round(media, 4), "sd nulo": round(desviacion, 4),
        "exceso": round(ami - media, 4),
    })
pd.DataFrame(filas)
"""),
    code("""
print(f"cobertura: {len(una)} fragmentos con exactamente una dimensión "
      f"({100 * len(una) / len(fragmentos):.1f} % del corpus)")
print(f"de ellos asignados a un tópico: {len(con_topico)} "
      f"({100 * len(con_topico) / len(una):.1f} %)")
"""),
    md("""
**Hay acuerdo moderado, no equivalencia.** Un AMI de 0,41 sobre un nulo de cero dice que
los tópicos y las dimensiones comparten estructura real, pero que **los tópicos no son
una redescripción de las seis dimensiones**. El ARI, mucho más bajo, lo confirma desde
otro ángulo: la coincidencia por pares es escasa, porque un tópico suele repartirse
entre varias dimensiones y una dimensión entre muchos tópicos.

Es exactamente el resultado que el objetivo 3 buscaba establecer: correspondencia
parcial, con un remanente que el esquema a priori no cubre.
"""),
    md("""
### Cuánto de los atributos emergentes es invisible para el diccionario
"""),
    code("""
nuevos = etiquetas.loc[etiquetas["tipo"] == "atributo_nuevo", "topico_id"]
sub = asignados[asignados["topico"].isin(nuevos)]
resto = asignados[~asignados["topico"].isin(nuevos)]
print(f"tópicos de atributo emergente: {len(nuevos)} · {len(sub)} fragmentos")
print(f"  sin ninguna dimensión: {100 * (sub['n_dim'] == 0).mean():.1f} %")
print(f"  resto del corpus asignado: {100 * (resto['n_dim'] == 0).mean():.1f} %")

detalle = sub.groupby("topico").agg(
    n=("fragmento_id", "size"),
    pct_sin_dimension=("n_dim", lambda s: round(100 * (s == 0).mean(), 1)),
).join(etiquetas.set_index("topico_id")["tema"])
detalle.sort_values("pct_sin_dimension", ascending=False)
"""),
    md("""
**Medios de pago e infraestructura son invisibles para el diccionario** —el 91 % y el
76 % de sus fragmentos no activan ninguna dimensión—: son atributos nuevos en sentido
estricto. Ocasión de consumo y referente en la ciudad sí rozan el diccionario, porque
traen palabras de ambiente y comida, pero lo que los agrupa —para quién es el sitio, qué
lugar ocupa en la ciudad— no está en el esquema.
"""),
    md("""
## 4. Relación con la calificación

**Descriptiva y solo descriptiva.** Los fragmentos de una misma reseña comparten
calificación y no son independientes, así que cualquier prueba de significancia que
asuma independencia daría errores estándar demasiado pequeños.
"""),
    code("""
ranking = temas.sort_values("rating", ascending=False)[
    ["tema", "tipo", "fragmentos", "rating", "pct_1_2_estrellas", "polaridad_dominante"]
]
print(f"media del corpus: {fragmentos['rating'].mean():.2f} · "
      f"1-2 estrellas: {100 * (fragmentos['rating'] <= 2).mean():.1f} %")
ranking
"""),
    code("""
display(Image(filename=str(FIGURAS / "02_temas_por_rating.png"), width=900))
"""),
    md("""
**La espera es el único tema que cae por debajo de tres estrellas** (1,88, con el 75,8 %
de reseñas de una o dos estrellas) y concentra el malestar del corpus. En el extremo
opuesto, intención de volver y satisfacción no son atributos sino veredictos, así que su
rating alto no dice nada sobre qué hace bien un establecimiento.

Entre los atributos, los mejor calificados son **ocasión de consumo (4,58) y referente en
la ciudad (4,55)**, los dos emergentes. Es el insumo más directo para orientar la
comunicación digital: son los asuntos por los que los comensales valoran mejor y que el
esquema tradicional no contempla.
"""),
    code("""
atipicos = fragmentos[fragmentos["topico"] == ATIPICO]
print(f"atípicos: {len(atipicos)} ({100 * len(atipicos) / len(fragmentos):.1f} %)")
print(f"  rating medio {atipicos['rating'].mean():.2f} · "
      f"1-2 estrellas {100 * (atipicos['rating'] <= 2).mean():.1f} %")
print(f"  corpus: {fragmentos['rating'].mean():.2f} · "
      f"{100 * (fragmentos['rating'] <= 2).mean():.1f} %")
print(f"\\n% atípico según dimensiones activas:")
for n_dim, grupo in fragmentos.groupby(fragmentos["n_dim"].clip(upper=2)):
    nombre = {0: "n_dim = 0", 1: "n_dim = 1", 2: "n_dim >= 2"}[n_dim]
    print(f"  {nombre}: {100 * (grupo['topico'] == ATIPICO).mean():>5.1f} %  (n={len(grupo)})")
"""),
    md("""
**Lo que queda sin agrupar es más negativo que el corpus** y está sobrerrepresentado
entre los fragmentos que el diccionario no ve. Las dos cosas apuntan al mismo sitio: la
señal que ni el esquema ni el modelo capturan es desproporcionadamente crítica.
"""),
    md("""
## 5. Los temas transversales

Cuatro asuntos aparecen en el corpus, son de los más negativos, y **no forman tópico con
ningún umbral probado**. Se cuantifican con reglas de recuperación.

> **Advertencia obligatoria.** Estas reglas son de **piso, no una medición**. Cada tema
> se recupera con una expresión regular estrecha sobre el texto; tiene falsos negativos
> (formulaciones que no usan esas palabras) y falsos positivos documentados. Las cifras
> acotan el orden de magnitud. No deben presentarse como prevalencias.
"""),
    code("""
baja_masa = pd.read_csv(DATOS_PROCESADOS / "temas_baja_masa.csv")
baja_masa[["tema", "fragmentos", "pct_corpus", "resenas", "rating",
           "pct_1_2_estrellas", "pct_atipicos", "topicos_distintos"]]
"""),
    code("""
ejemplos = pd.read_csv(DATOS_PROCESADOS / "temas_baja_masa_ejemplos.csv")
for tema, grupo in ejemplos.groupby("tema", sort=False):
    print(f"{tema}:")
    for fila in grupo.itertuples(index=False):
        print(f"   ({fila.rating}★) {fila.texto[:115]}")
    print()
"""),
    md("""
**Inocuidad (1,62) y honestidad en el cobro (1,87) están por debajo incluso de la
espera**, que es el tema negativo más grande del corpus. Son pocos fragmentos, pero cada
uno pesa mucho en la reseña donde aparece.

**«Trato al personal» no es cuantificable con esta herramienta.** La regla amplia
recuperaba quejas *sobre* el personal, no críticas a *cómo se le trata*; la estrecha
deja 1 fragmento. Cualitativamente sí aparece —2 de los 60 atípicos clasificados a
mano— pero no se puede dar una cifra defendible, y se reporta solo como observación.
"""),
    md("""
## 6. Limitaciones

Siete, con su alcance real.

1. **La coherencia por co-ocurrencia es prácticamente nula** (`c_npmi = −0,038`). Hay
   causa estructural —el fragmento mediano tiene 10 palabras— pero no se puede afirmar
   que los tópicos sean léxicamente coherentes. Su interpretación se sostiene en la
   lectura de fragmentos.

2. **Los temas de baja masa se miden con reglas de piso**, con falsos positivos y
   negativos documentados. Acotan el orden de magnitud; no lo miden. Dos reglas ya
   tuvieron que corregirse.

3. **La deduplicación usa un proxy débil.** Sin identificador de autor, la clave usa
   `autor_n_resenas`. Afecta a 2 filas de 2.432 y no altera resultados, pero no debe
   presentarse como exacta.

4. **Hay una fuga en la detección de idioma heredada:** un fragmento en alfabeto árabe
   pasó el filtro. Es 1 de 5.913 y quedó como atípico.

5. **El umbral de agrupamiento sesga qué atributos emergentes se ven, y el sesgo tiene
   signo:** los que forman tópico son los positivos. Interpretar los atributos
   emergentes solo por los tópicos formados subestimaría lo negativo.

6. **Cada fragmento hereda la calificación de su reseña.** El rating de un tópico no es
   la valoración del tema, sino la de las reseñas donde aparece; una reseña larga pesa
   más que una corta; y los fragmentos de una reseña no son independientes. Por eso no
   se aplica ninguna prueba de significancia.

7. **Los temas transversales no son tópicos**, y el modelado de tópicos es la
   herramienta equivocada para ellos. Su presencia se sostiene con reglas de
   recuperación y análisis cualitativo.
"""),
    md("""
## Hallazgos

1. **La correspondencia entre temas emergentes y dimensiones a priori es parcial:
   AMI 0,406 sobre una línea base de cero.** Comparten estructura real, pero los tópicos
   no son una redescripción de las seis dimensiones.

2. **Ninguna dimensión se concentra en un solo tópico.** La espera es la única con
   correspondencia fuerte (62,7 % en un tópico); comida se reparte en 38 y su tópico
   principal ni siquiera es de comida. El esquema a priori y la estructura emergente
   describen el mismo corpus con cortes distintos.

3. **El 13,0 % del corpus asignado habla de atributos que el esquema no contempla**, y
   dos de ellos —medios de pago e infraestructura— son además invisibles para el
   diccionario en más del 75 % de sus fragmentos.

4. **La espera concentra el malestar** (1,88 estrellas, 75,8 % de reseñas de 1-2), y los
   atributos mejor valorados son los dos emergentes: ocasión de consumo (4,58) y
   referente en la ciudad (4,55). Ahí está la orientación más directa para la
   comunicación digital.

5. **Lo que el método no captura es desproporcionadamente crítico.** Los atípicos son
   más negativos que el corpus (3,20 contra 3,70) y los temas transversales —inocuidad
   1,62, cobro 1,87— son los peor calificados de todo el estudio. Cualquier lectura que
   se quede en los tópicos formados dará una imagen más amable de la que el corpus
   sostiene.

6. **La calidad léxica del modelo es moderada y hay que declararlo.** `c_v` 0,484 y
   `c_npmi` −0,038: la validez de los tópicos descansa en la lectura de sus fragmentos,
   no en los indicadores de coherencia.
"""),
    CIERRE_COMUN,
]

NOTEBOOKS = {
    "00_preparacion": PREPARACION,
    "01_caracterizacion": CARACTERIZACION,
    "02_topicos": TOPICOS,
    "03_evaluacion": EVALUACION,
}
