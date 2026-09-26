# Bitácora

Registro de decisiones y resultados, en orden cronológico.

---

## 2026-09-22 — Inventario y verificación del corpus heredado

**Qué se hizo.** Primer paso del proyecto: inventariar los archivos que se leerán del
proyecto original (`reputacion-popayan`, solo lectura) y verificar que el corpus
coincide con lo esperado, sin transformar nada. Se crearon `src/config.py` (rutas,
`SEMILLA = 42`) y `scripts/inventario.py`, que genera `data/external/manifiesto.csv`
y reporta esquemas y cruces.

El inventario usa solo la librería estándar (`csv`, `hashlib`, `statistics`), porque
en este paso el entorno de uv todavía no tiene dependencias instaladas.

### Manifiesto

| Archivo del original | Filas | Columnas | SHA-256 (12) |
|---|---:|---:|---|
| `data/raw/corpus_final.csv` | 8.451 | 15 | `8478fa5ace84` |
| `data/raw/marco_muestral_final.csv` | 133 | 19 | `2c4a8587aed8` |
| `data/interim/idioma_resenas.csv` | 4.102 | 7 | `0a567e58e490` |
| `data/interim/dimensiones_aptas_es.csv` | 2.432 | 11 | `52a10c944a62` |
| `data/interim/sentimiento_fragmentos.csv` | 6.562 | 4 | `bee608b5665b` |
| `diccionario/dimensiones.csv` | 144 | 8 | `67393d3a4e7c` |

Hashes completos en `data/external/manifiesto.csv`.

### Embudo del corpus

| Etapa | Reseñas |
|---|---:|
| Corpus total | 8.451 |
| Con texto y ≥ 50 caracteres (`apto = True`) | 2.645 |
| De esas, idioma español | **2.432** |

**Coincide con las 2.432 esperadas.** El largo mínimo entre las aptas es exactamente
50 caracteres, así que el umbral ya viene aplicado en `apto` y no hay que recalcularlo.
`idioma_resenas.csv` tiene 4.102 filas porque cubre también reseñas no aptas (3.439 en
español en total); el cruce que importa es `apto = True` y `es_espanol = True`.

`dimensiones_aptas_es.csv` tiene exactamente esas 2.432 reseñas, una por fila. Sirve
como la lista maestra del corpus de trabajo.

### Cobertura de los fragmentos

`sentimiento_fragmentos.csv` tiene 6.562 filas `(clave, dimension, fragmento, origen)`,
con 4.121 textos de fragmento únicos y 5.346 pares reseña-dimensión. `clave` es el
`review_id`.

- **Los fragmentos existen solo para las reseñas con alguna dimensión activa**: 2.318
  de las 2.432. Las 114 restantes (4,7 %) no tienen ninguna fila. El conjunto de claves
  del archivo es idéntico al de reseñas con `n_dim > 0`, y no hay ninguna clave fuera
  de las aptas en español.
- Más importante: **el archivo no contiene todas las cláusulas, solo las que activan
  alguna dimensión**. Replicando la segmentación del original sobre las 2.432 reseñas
  se obtienen 5.919 cláusulas (5.694 únicas); 1.590 cláusulas únicas no aparecen en el
  archivo porque no disparan ninguna dimensión.

**Consecuencia para el modelado.** Como la unidad de análisis es el fragmento y el
modelado de tópicos debe ver *todo* lo que dicen los comensales (incluido lo que el
diccionario no cubre), `sentimiento_fragmentos.csv` no sirve como corpus de fragmentos:
está sesgado hacia el vocabulario del diccionario. Hay que re-segmentar las 2.432
reseñas con la misma regla, copiando la función a `src/`. El archivo sí sirve como
insumo de la etiqueta de dimensión por fragmento, para el contraste del objetivo 3.

### Nivel de las etiquetas de dimensión

Están en **ambos niveles**, y son mediciones distintas:

- **Por reseña**, en `dimensiones_aptas_es.csv`: seis columnas booleanas más `n_dim`.
  Es la medición validada del original, tomada sobre el texto completo.
- **Por fragmento**, en `sentimiento_fragmentos.csv`: cada fila asocia un fragmento a
  una dimensión. Es derivada, no independiente: una dimensión solo aparece si ya estaba
  activa en la reseña completa.

| Dimensión | Reseñas | % de 2.432 | Filas de fragmento | Fragmentos únicos |
|---|---:|---:|---:|---:|
| comida | 1.885 | 77,5 % | 2.563 | 2.527 |
| servicio | 1.419 | 58,3 % | 1.703 | 1.661 |
| ambiente | 993 | 40,8 % | 1.120 | 1.107 |
| precio | 431 | 17,7 % | 469 | 468 |
| espera | 374 | 15,4 % | 415 | 415 |
| patrimonio | 244 | 10,0 % | 292 | 291 |

Dimensiones activas por reseña: 0 → 114 (4,7 %), 1 → 509 (20,9 %), 2 → 864 (35,5 %),
3 → 705 (29,0 %), 4 → 209 (8,6 %), 5 → 28 (1,2 %), 6 → 3 (0,1 %).

Solo el 20,9 % de las reseñas tiene exactamente una dimensión activa. El AMI del
objetivo 3, que se calcula sobre fragmentos con una sola dimensión, trabajará entonces
sobre un subconjunto bastante menor que el corpus; hay que reportar su tamaño.

### Longitud de los fragmentos

Sobre las 6.562 filas del archivo, en caracteres: mínimo 10, p25 52, mediana 77, p75
120, p90 180, máximo 2.026, media 98,3. En palabras: mediana 13, p75 21, p90 32,
máximo 351.

Sobre los 4.121 textos únicos: mediana 69, p75 109, máximo 2.026.

Sobre la segmentación completa de las 2.432 reseñas (5.919 cláusulas): mediana 59
caracteres, p25 33, p75 94, máximo 1.298. Media de 2,43 cláusulas por reseña, mediana
2; el 39,1 % de las reseñas no se parte.

El máximo de 2.026 caracteres viene de las 17 filas con `origen = respaldo`, donde se
usa la reseña entera. Ninguna reseña apta queda sin al menos una cláusula de 10
caracteres.

### Segmentación por cláusula en el original

En `src/sentimiento.py` del original (`segmentar`, `SEPARADOR_CLAUSULA`,
`fragmentos_por_dimension`):

- Se corta con una sola expresión regular que une tres tipos de separador: la etiqueta
  `<br>`, los signos de puntuación `.!?;¡¿` y el salto de línea, más una coma opcional
  seguida de un conector adversativo (`pero`, `aunque`, `sin embargo`, `no obstante`,
  `eso sí`, `lo malo`, `lo único`, `mientras que`). Separadores consecutivos colapsan
  en un solo corte y el conector se consume, así que no queda en ninguno de los dos
  lados.
- **Sí descarta fragmentos cortos**: `LARGO_MINIMO_FRAGMENTO = 10`. Tras hacer `strip`,
  todo fragmento de menos de 10 caracteres se elimina, con el argumento de que no da
  señal al clasificador de sentimiento.
- La atribución de dimensiones no se recalcula sobre las cláusulas: se toma la del
  texto completo y las cláusulas solo deciden cuál sustenta cada dimensión. Si ninguna
  la sostiene, se usa la reseña entera y se marca `origen = respaldo` (17 filas, 0,3 %).

Todavía no se copió código. Cuando se copie, irá a `src/` con referencia al archivo y
función de origen.

### Discrepancia con la bitácora del original

La bitácora del original (entrada del 2026-09-10) reporta 6.493 filas de fragmento,
4.110 textos únicos, 5.275 pares reseña-dimensión y 10 filas de respaldo. El archivo
en disco tiene 6.562, 4.121, 5.346 y 17. El diccionario se modificó después de esa
corrida (`dimensiones.csv` con fecha posterior), así que el CSV es una regeneración más
reciente que el texto de la bitácora. Se toman como válidas las cifras del archivo, que
son las que quedaron en el manifiesto con su hash.

### Pendiente antes del siguiente paso

- Instalar dependencias (pandas y el resto) con `uv add`.
- Confirmar la re-segmentación completa de las 2.432 reseñas como fuente de fragmentos
  para el modelado, en vez de reutilizar `sentimiento_fragmentos.csv`.

---

## 2026-09-22 — Preparación: corpus de fragmentos

**Qué se hizo.** Construcción de `data/processed/fragmentos.csv`, la tabla sobre la que
se modelarán los tópicos. Se re-segmentaron las 2.432 reseñas y se recalcularon las
dimensiones por fragmento, según lo confirmado tras el inventario.

**Entorno.** `uv add pandas numpy pyarrow ipykernel` y `pytest`/`nbconvert` como dev.
Python 3.12.12, pandas 3.0.6, numpy 2.5.3, pyarrow 25.0.1. Kernel `topicos-popayan`
registrado desde el entorno de uv.

**Código copiado del original.** `src/segmentacion.py` (de `src/sentimiento.py`:
`CONECTORES_ADVERSATIVOS`, `SEPARADOR_CLAUSULA`, `LARGO_MINIMO_FRAGMENTO`, `segmentar`)
y `src/diccionario.py` (módulo completo). Único cambio: la ruta del diccionario apunta
al CSV del original vía `src.config`, en vez de a una carpeta local. Se añadió
`segmentar_sin_filtrar`, que no existe en el original, para poder contar cuántas
cláusulas caen por el largo mínimo.

### Embudo

| Etapa | Cifra |
|---|---:|
| Reseñas aptas en español | 2.432 |
| Duplicados reales eliminados | 2 |
| Reseñas de trabajo | 2.430 |
| Cláusulas antes del largo mínimo | 6.073 |
| Descartadas por < 10 caracteres | 160 (2,6 %) |
| **Fragmentos finales** | **5.913** |

Las 2.430 reseñas quedan todas representadas: ninguna pierde todos sus fragmentos.

**Duplicados.** El corpus no trae identificador de autor, solo `autor_n_resenas`, que
es el único proxy disponible del autor anonimizado. Con la clave
`(autor_n_resenas, texto)` se eliminan 2 filas. Con solo `texto` serían 3, y la tercera
es un texto genérico de autores distintos, que la decisión manda conservar.

> **LIMITACIÓN — deduplicación por proxy débil.** El corpus heredado no tiene
> identificador de autor. La clave de duplicado usa `autor_n_resenas` (el número de
> reseñas que ha escrito esa persona) como sustituto del autor anonimizado, que es lo
> único disponible. Es un proxy débil en ambas direcciones: dos autores distintos con
> el mismo número de reseñas y el mismo texto se confundirían y se eliminaría una
> opinión legítima; y el mismo autor con su contador actualizado entre dos capturas no
> se detectaría. En este corpus afecta a 2 filas de 2.432, así que no altera ningún
> resultado aguas abajo, pero la deduplicación **no debe presentarse como exacta** en
> el informe final. Si el corpus se ampliara, habría que conseguir un identificador de
> autor real antes de confiar en este paso.

### Enmascarado de nombres: dos correcciones

La primera versión aplicaba `patron_nombre` del original —que acepta cualquier
subsecuencia de dos o más tokens— a los 139 nombres sobre todo el corpus. Enmascaró
**825 fragmentos (14,0 %)**, casi todos falsos positivos: «El Fogón de la Abuela»
genera la subsecuencia `de la`, que coincide en cualquier reseña. Aparecían fragmentos
como `la calidad [LOCAL] comida` y `[LOCAL] carta es excelente`.

Esa lógica es correcta en el original, donde se aplica al nombre de **una sola** reseña
y solo para vetar coincidencias del diccionario. Aplicada globalmente no sirve. Se
cambió la regla para el enmascarado (el veto del diccionario queda intacto):

1. **Local propio de la reseña**: se aceptan subsecuencias, porque la reseña suele
   abreviar el nombre del sitio del que habla.
2. **Los demás locales**: se exige el nombre completo.
3. **La secuencia debe aportar algo propio del local**: se descartan las que son solo
   palabras funcionales (`de la`) y las que son funcionales más un término del
   diccionario (`de comidas`, de «Plazoleta de Comidas»), que borraban justamente la
   señal de la dimensión a medir.

Resultado: **106 fragmentos (1,8 %)** y 91 reseñas (3,7 %). La prevalencia recalculada
de `comida` subió de 1.868 a 1.878 reseñas al dejar de borrar el término.

Los nombres de un solo token siguen sin enmascararse, como en el original:
«Carantanta» es a la vez un local y un plato patrimonial.

### Orden de la limpieza

Los saltos de línea y las etiquetas `<br>` se normalizan **después** de segmentar, no
antes. Son separadores de cláusula y colapsarlos antes perdería esos cortes. Antes de
segmentar solo se quitan URLs y emojis, que no afectan los límites; los espacios se
normalizan al final, ya sobre cada fragmento.

### Longitudes

| Medida | min | p25 | mediana | p75 | p90 | max | media |
|---|---:|---:|---:|---:|---:|---:|---:|
| Fragmentos por reseña | 1 | 1 | 2 | 3 | 5 | 25 | 2,4 |
| Caracteres | 10 | 33 | 59 | 93 | 143 | 1.295 | 74,2 |
| Palabras | 1 | 6 | 10 | 17 | 25 | 246 | 13,0 |

Mediana de 10 palabras: fragmentos cortos, muy por debajo del truncado de cualquier
modelo de embeddings. 11 fragmentos (0,2 %) quedan con `texto_limpio` vacío tras las
stopwords; no se eliminan, porque conservan su `texto` para los embeddings.

### Prevalencia: fragmento contra reseña

| Dimensión | Fragmentos | % frag. | Reseñas heredada | % | Reseñas recalculada | % |
|---|---:|---:|---:|---:|---:|---:|
| comida | 2.555 | 43,2 % | 1.883 | 77,5 % | 1.878 | 77,3 % |
| servicio | 1.700 | 28,8 % | 1.417 | 58,3 % | 1.416 | 58,3 % |
| ambiente | 1.109 | 18,8 % | 992 | 40,8 % | 982 | 40,4 % |
| precio | 468 | 7,9 % | 431 | 17,7 % | 431 | 17,7 % |
| espera | 415 | 7,0 % | 374 | 15,4 % | 374 | 15,4 % |
| patrimonio | 291 | 4,9 % | 244 | 10,0 % | 243 | 10,0 % |

La columna *recalculada* agrega nuestras etiquetas por fragmento de vuelta a nivel de
reseña. Coincide casi exactamente con la *heredada* del original, que se midió sobre el
texto completo: la diferencia máxima es de 10 reseñas en `ambiente` (1,0 %) y se explica
por las 2 reseñas eliminadas y por el enmascarado. Esa coincidencia es la validación de
que recalcular sobre cláusulas no pierde señal.

Las cifras por fragmento son mucho más bajas porque cambia el denominador: una reseña
de tres cláusulas habla de comida en una sola. El orden de las dimensiones se conserva
en ambos niveles, así que la estructura relativa no cambia.

### Dimensiones por fragmento

| n_dim | Fragmentos | % |
|---:|---:|---:|
| 0 | 1.722 | 29,1 % |
| 1 | 2.483 | 42,0 % |
| 2 | 1.156 | 19,6 % |
| 3 | 470 | 7,9 % |
| 4 | 77 | 1,3 % |
| 5 | 5 | 0,1 % |

Ningún fragmento activa las seis. **El AMI del objetivo 3 dispone de 2.483 fragmentos,
el 42,0 % del corpus.** Es bastante mejor que el 20,9 % que daba el criterio equivalente
a nivel de reseña: segmentar por cláusula sí separa los asuntos, que era el argumento
para elegir el fragmento como unidad.

El 29,1 % sin ninguna dimensión es el hallazgo más relevante para el objetivo 2: casi un
tercio del corpus queda fuera del esquema a priori. Son justamente los fragmentos donde
el modelado de tópicos puede aportar algo que el diccionario no ve, y son los que
`sentimiento_fragmentos.csv` habría descartado.

### Verificación manual

Las reglas de contexto se comportan bien a nivel de cláusula. «Estos son los sitios que
necesita Popayán» no activa `ambiente`, porque `sitio` exige un adjetivo de ambiente en
la misma oración y no lo hay: el veto `requiere` funciona igual con la cláusula como
ventana.

Se observan fallos de **recall** del diccionario, heredados, no introducidos aquí:

- «muy representativo de la cultura gastronómica de Popayán» no activa `patrimonio`.
- «Un buen detalle con sabor patojo» activa `comida` pero no `patrimonio`.
- «el establecimiento no estaba lleno, habían poquitas mesas ocupadas» no activa
  `ambiente`.

No se toca el diccionario: es la medición validada del original y cambiarla rompería la
comparabilidad. Queda anotado porque afecta la lectura del contraste del objetivo 3: el
29,1 % sin dimensión mezcla temas genuinamente fuera del esquema con fallos de recall.

### Salida

`data/processed/fragmentos.csv`, 5.913 filas y 20 columnas: `fragmento_id`, `review_id`,
`place_id`, `establecimiento`, `zona`, `rating`, `fragmento_num`, `n_fragmentos_resena`,
`texto`, `texto_limpio`, `largo_caracteres`, `largo_palabras`, `tiene_local`, las seis
dimensiones booleanas y `n_dim`. Sin embeddings todavía.

`texto` conserva mayúsculas, tildes y stopwords (va a los embeddings). `texto_limpio` es
para c-TF-IDF. La lista propia de stopwords se dejó corta a propósito —solo `popayan`,
`cauca`, `colombia`, `restaurante(s)`— y **no incluye** las palabras que nombran
dimensiones (`comida`, `servicio`, `lugar`, `sitio`), porque son las que hacen
interpretable cada tópico.

**Pruebas.** 46 pruebas en `tests/`, sobre segmentación (9), limpieza de texto (8),
enmascarado (12), diccionario (10) y texto de c-TF-IDF (8). Todas pasan.

**Notebook.** `notebooks/00_preparacion.ipynb`, verificado de arriba abajo con kernel
limpio vía `nbconvert --execute`. La versión Colab queda pendiente hasta que el pipeline
esté estable.

---

## 2026-09-22 — Embeddings y primer modelo de tópicos (diagnóstico)

**Qué se hizo.** Corrida diagnóstica, sin optimizar: embeddings de los 5.913 fragmentos
y un primer BERTopic con parámetros razonables, para ver qué sale.

**Entorno.** `uv add sentence-transformers bertopic`. bertopic 0.17.4,
sentence-transformers 6.1.0, torch 2.14.0 (MPS disponible), transformers 5.17.0,
umap-learn 0.5.12, hdbscan 0.8.44, scikit-learn 1.9.1.

### Embeddings

`paraphrase-multilingual-MiniLM-L12-v2` sobre la columna `texto` (el fragmento
enmascarado con `[LOCAL]`, natural: con mayúsculas, tildes y stopwords). **384
dimensiones**, 5.913 × 384, **5,8 s** en MPS.

Se guardan en `data/processed/embeddings.npy` junto a `embeddings_indice.csv` con el
`fragmento_id` en el mismo orden. `obtener()` lee de disco si el índice cubre los mismos
fragmentos y **realinea por `fragmento_id`**, no por posición, de modo que reordenar el
CSV no rompe la correspondencia. Verificado con una permutación aleatoria.

Nota de nomenclatura: la columna con el texto natural enmascarado se llama `texto`, no
`texto_enmascarado`; el identificador es `fragmento_id`, no `id_fragmento`.

### Bug corregido: BERTopic borraba las tildes

La primera corrida devolvió términos como `atencin`, `pequeo`, `msica`, `pipin`. No era
el vectorizador ni `texto_limpio`, que sí conservan tildes. Es BERTopic: en
`_preprocess_text` (`bertopic/_bertopic.py:4813`) aplica
`re.sub(r"[^A-Za-z0-9 ]+", "", doc)` cuando `language == "english"`, que es su valor por
defecto. Se corrigió con `language="multilingual"`. Cualquier valor distinto de
`"english"` desactiva ese filtro.

Afectaba solo a las etiquetas de los tópicos, no al agrupamiento (los embeddings se
calculan aparte), pero habría hecho ilegible todo el c-TF-IDF.

### Parámetros

UMAP `n_neighbors=15`, `n_components=5`, `min_dist=0.0`, métrica coseno,
`random_state=42`. HDBSCAN vía `min_topic_size=30`. c-TF-IDF con `CountVectorizer`
sobre `texto_limpio`, unigramas y bigramas, `min_df=2`. Sin reducción de atípicos.

### Resultado

**38 tópicos** y **2.131 fragmentos sin asignar (36,0 %)**.

Los diez mayores: servicio positivo (334), ambiente y decoración (328), tiempos de
espera (263), precio y medios de pago (241), un tópico incoherente (219), elogio
general de lugar y comida (170), problemas con el plato (152), «el mejor de la ciudad»
(147), mal servicio (139) y ocasión de consumo —familia, amigos, música— (125).

Salidas en `data/processed/`: `fragmentos_topicos.csv` (asignaciones),
`topicos_resumen.csv` (tamaño, términos, rating, concentración, dimensión dominante) y
`topicos_ejemplos.csv`.

### Diagnóstico: los tópicos se parten por tono

| Medida | Valor |
|---|---:|
| eta² `rating ~ tópico` | 0,392 |
| eta² `log(largo) ~ tópico` | 0,321 |

El tono explica el 39 % de la varianza entre tópicos. No es un artefacto: la partición
es visible término a término. **Servicio se abre en seis tópicos que son el mismo tema
en distinta polaridad**: T8 «mal servicio, grosero, pésimo» (rating 1,66), T20 «mala
experiencia, decepcionada, terrible» (1,97), T0 «atento, rápido, amables» (4,15), T26
«volvería, volveré» (4,79), T10 «excelente servicio» (4,82) y T37 «excelente servicio,
excelente excelente» (5,00). T10 y T37 comparten casi todos sus términos y se separan
solo por intensidad.

Lo mismo en comida: 23 de los 38 tópicos tienen `comida` como dimensión dominante, y
seis de ellos (T5, T14, T24, T29, T31, T36) son variantes de «comida deliciosa» que se
distinguen por el adjetivo, no por el asunto.

Hay además tópicos puramente evaluativos, sin tema: T32 «experiencia, buena
experiencia», T33 «negativa, triste, peores», T26 «volvería», T35 «recomiendo».

### Bug de etiquetado: la negación se pierde en c-TF-IDF

**T35 tiene rating medio 1,53 y sus términos son «recomiendo, lugar recomiendo,
recomendar».** El 97 % de sus fragmentos contienen «no»: son «No lo recomiendo», «No
recomiendo este lugar en ningún sentido». La palabra `no` está en las stopwords
españolas, así que `texto_limpio` la elimina y el c-TF-IDF etiqueta el tópico como su
contrario exacto.

El agrupamiento es correcto —los embeddings ven el texto completo, con la negación— y
por eso el rating del tópico delata el error. Lo que falla es la etiqueta. Afecta
potencialmente a todos los tópicos negativos. Hay que resolverlo antes de interpretar
nada: sacar `no`, `nunca`, `nada`, `ni`, `sin` de las stopwords, o trabajar la negación
explícitamente.

### Tópicos por longitud

T4 (n=219, 3,7 % del corpus) es un cajón de sastre de fragmentos cortos: largo mediano
19 caracteres, términos incoherentes («bueno, jamas, general bueno, rappi, gracias,
mágico, pulpo»), ratings de 1 a 5 y ejemplos sin relación entre sí («Excelente todo»,
«AÚN USAN PLÁSTICO DE UN SOLO USO», «Las cocciones en su punto»). Otros tres tópicos
tienen el mismo patrón: T36 (15 car.), T35 (26), T26 (32).

La tasa de atípicos sí crece con la longitud, pero poco: 35,0 % en el cuartil más corto
contra 39,9 % en el más largo. La longitud no domina la asignación, pero sí genera
tópicos basura en el extremo corto.

### Concentración por establecimiento

Mediana de 11,9 %. Ocho tópicos de 38 superan el 20 % en un solo local:

| Tópico | n | % local top | Local | Locales |
|---|---:|---:|---|---:|
| T23 café | 56 | 35,7 % | Togoima - Café Ritual | 14 |
| T37 elogio servicio | 31 | 32,3 % | Il Gallo Restaurante | 16 |
| T32 experiencia | 38 | 26,3 % | Il Gallo Restaurante | 25 |
| T21 empanadas y pipián | 61 | 26,2 % | Mora Castilla | 27 |
| T22 comida típica | 57 | 24,6 % | Mora Castilla | 33 |
| T30 sushi y ramen | 45 | 24,4 % | HOSHI | 12 |
| T11 pizza | 100 | 24,0 % | Pizza Club | 10 |
| T18 hamburguesas | 72 | 23,6 % | Dom Burger | 24 |

Hay que distinguir dos casos. En los tópicos de plato (T11 pizza, T30 sushi, T18
hamburguesas, T23 café) la concentración es esperable: son locales especializados, y el
tema y el local coinciden en la realidad. En T37 y T32, en cambio, la concentración no
tiene justificación temática: son elogios genéricos, y que un tercio venga del mismo
local sugiere que el modelo está capturando el estilo de escritura de sus reseñas.

El enmascarado con `[LOCAL]` funcionó —solo el 1,8 % de los fragmentos lo lleva— pero no
impide que el modelo agrupe por carta, que es un rasgo del local igual de identificable.

### Los fragmentos fuera del esquema a priori

Los fragmentos con `n_dim = 0` quedan sin asignar el **44,6 %** de las veces, contra el
**32,5 %** de los que tienen alguna dimensión. Es decir, lo que el diccionario no ve
también le cuesta más al modelo. Con 36 % de atípicos global, buena parte de lo que
debía aportar el objetivo 2 está hoy en el montón de los no asignados.

### Conclusión del diagnóstico

El modelo no está listo para interpretarse. Tres problemas, en orden de gravedad:

1. **La negación se pierde en las etiquetas** (T35). Es un bug, no un ajuste.
2. **Los tópicos se parten por polaridad**, no por tema. Con 38 tópicos para seis
   dimensiones, la redundancia es alta y el contraste del objetivo 3 saldría inflado.
3. **36 % de atípicos**, concentrados justo en los fragmentos fuera del esquema a
   priori.

Ninguno se resuelve tocando `min_topic_size` solamente. Pendiente de acordar el
siguiente paso antes de tocar parámetros.

---

## 2026-09-22 — Corrección de la negación, comparación de modelos y ajuste

**Qué se hizo.** Se corrigió el bug de la negación, se comparó un segundo modelo de
embeddings, se barrió una rejilla de parámetros, se calibró la reducción de atípicos y
se diagnosticó el largo mínimo. Sigue siendo diagnóstico: no se agrupan ni se nombran
tópicos.

### Paso 1 — La negación

Se sacaron de las stopwords `no`, `ni`, `sin`, `nada`, `nunca`, `jamás`, `ningún`,
`ninguna`, `ninguno`, `tampoco`, declaradas ahora en `NEGACIONES`. Hizo falta un cambio
extra: `texto_para_ctfidf` descartaba las palabras de dos letras o menos, así que `no` y
`ni` se habrían perdido igual; ahora las negaciones quedan exentas de ese mínimo.

**T35 queda bien etiquetado**: sus términos pasan de `recomiendo, recomendar` a
`no recomiendo, recomiendo no, recomiendo nada`, con su rating medio de 1,53. Otros
nueve tópicos incorporaron marcas de negación a su representación: T6 `carne no`, T20
`no buena`, T30 `consistencia no`, T33 `no puedes, no puede`, T34 `menú no`. T26 recogió
`sin duda` —el «sin» positivo de «sin duda volvería»—, que también se perdía.

El agrupamiento **no cambió en absoluto**: 38 tópicos, 36,0 % de atípicos, mismo eta².
Era lo esperado, porque los embeddings se calculan sobre `texto`, que nunca perdió la
negación. El bug era solo de etiquetado, como se había diagnosticado.

### Dos métricas que hubo que rehacer

**Duplicados.** El criterio inicial (Jaccard ≥ 0,3 sobre los términos principales)
detectaba cero duplicados, aunque T10 y T37 son el mismo tópico. Comparten pocos
bigramas exactos —Jaccard 0,18— pero sus centroides están a coseno 0,90. Se cambió a
similitud coseno entre centroides. Y como el coseno absoluto no es comparable entre
modelos —el espacio de e5 tiene coseno medio 0,838 frente al 0,252 de MiniLM—, el umbral
se calibra al percentil 99 de los pares del propio modelo: 0,72 para MiniLM, 0,91 para
e5.

**eta² del rating.** Crece mecánicamente con el número de tópicos, así que 0,392 con 38
tópicos y 0,024 con 5 no se pueden comparar. Se añadió una línea base por permutación
(30 repeticiones, se baraja el rating dejando intactos los tamaños de grupo) y se
reporta el exceso sobre ella.

### Paso 2 — MiniLM contra e5-small

`intfloat/multilingual-e5-small` con el prefijo `query: ` que pide su documentación para
tareas simétricas. 384 dimensiones, 5,1 s.

| Configuración | Tópicos | Atípicos | eta² rating (exceso) | Basura | Duplicados |
|---|---:|---:|---:|---:|---:|
| minilm mts=30 | 38 | 36,0 % | 0,392 (+0,382) | 5 | 22 |
| e5-small mts=30 | 5 | 1,5 % | 0,024 (+0,023) | 2 | 5 |
| e5-small mts=15 | 51 | 31,4 % | 0,487 (+0,475) | 20 | 51 |
| e5-small mts=8 | 107 | 41,2 % | 0,559 (+0,529) | 41 | 107 |
| e5-small mts=5 | 188 | 38,0 % | 0,567 (+0,516) | 67 | 188 |

Con el mismo `min_topic_size` e5 colapsa en 5 tópicos. La causa es geométrica: e5 emite
vectores ya normalizados y **muy anisótropos**, con cosenos entre pares de 0,79 a 0,89
(media 0,838), mientras MiniLM va de −0,02 a 0,58 (media 0,252). Con tan poco rango
relativo, HDBSCAN no encuentra estructura fina.

**Respuesta a la pregunta: la partición por polaridad es del corpus, no del modelo.** A
granularidad comparable e5 la exhibe **más**, no menos: 0,487 con 51 tópicos contra
0,392 con 38 de MiniLM. Además e5 produce el cuádruple de tópicos basura (20 contra 5) y
el 100 % de sus tópicos son mutuamente redundantes en todas las granularidades, incluso
con su umbral relativo.

**Se sigue con MiniLM.** Gana en las cuatro medidas.

### Paso 3 — Rejilla, y una métrica que faltaba

| Configuración | Tópicos | Atípicos | eta² (exceso) | Basura | Duplicados | Tópico mayor |
|---|---:|---:|---:|---:|---:|---:|
| mts=20 ms=def | 55 | 38,5 % | 0,412 (+0,397) | 11 | 36 | 5,9 % (r 4,08) |
| mts=20 ms=10 | 74 | 36,4 % | 0,417 (+0,398) | 19 | 56 | 3,2 % (r 4,78) |
| mts=30 ms=def | 38 | 36,0 % | 0,392 (+0,382) | 5 | 22 | 5,6 % (r 4,15) |
| **mts=30 ms=15** | **42** | **31,1 %** | **0,400 (+0,390)** | **5** | **26** | **5,9 % (r 4,07)** |
| mts=50 ms=def | 23 | 42,7 % | 0,418 (+0,411) | 1 | 13 | 8,9 % (r 1,76) |
| mts=50 ms=25 | 22 | 26,1 % | 0,332 (+0,328) | 1 | 12 | 26,9 % (r 2,40) |

**Corrección de lectura.** En una primera pasada se eligió `mts=50 ms=25`, que ganaba en
las cinco métricas a la vez. Al inspeccionar sus tópicos apareció el problema: su T0
tenía **1.600 fragmentos, el 27,1 % del corpus**, con rating medio 2,40 y el 61 % de
reseñas de una o dos estrellas. Es un cajón negativo que abarca 120 locales y fusiona lo
que en `mts=30` eran tópicos separados —espera (263), plato (152), servicio (139),
experiencia (68)—, unificados solo por la polaridad. Dentro de T0 la espera está
sobrerrepresentada (19,4 % contra 7,0 % del corpus) y el ambiente casi ausente (3,6 %
contra 18,8 %).

Esa configuración **minimizaba eta² precisamente porque fundía lo negativo en un solo
grupo**: con un único cajón no hay varianza de rating *entre* tópicos que medir. La
métrica premiaba el defecto.

Se añadió `pct_topico_mayor` con su rating. Con ella la rejilla se lee al revés: las dos
configuraciones de `mts=50` son las peores, no las mejores. **`mts=30 ms=15` es la
mejor**: no tiene cajón (mayor 5,9 %, rating 4,07), tiene la menor tasa de atípicos entre
las configuraciones sanas (31,1 %) y mantiene la basura en 5.

### Paso 4 — Reducción de atípicos

Estrategia `embeddings` sobre `mts=30 ms=15`. El umbral por defecto de BERTopic (0,3)
reasigna 1.821 de 1.839 atípicos y deja el 0,3 %, pero a costa de la calidad: metía
«Volveremos» en el tópico de quejas y «Hay una persona en la entrada que vende
aguacates» en el de comida rica.

Se calibró con un criterio explícito: los fragmentos **ya asignados** están a coseno
0,676 de su centroide en promedio. Un umbral justo por debajo exige que el atípico
encaje tan bien como uno típico.

| Umbral | Reasignados | Atípicos | Tópico mayor |
|---:|---:|---:|---:|
| 0,30 | 1.821 | 0,3 % | 7,8 % |
| 0,50 | 1.473 | 6,2 % | 7,3 % |
| 0,60 | 1.003 | 14,1 % | 6,5 % |
| **0,65** | **698** | **19,3 %** | **6,0 %** |
| 0,70 | 463 | 23,3 % | 6,0 % |

**Elegido 0,65**: atípicos del 31,1 % al 19,3 %, sin crear cajón. En la revisión manual
de 10 reasignados, 8 son coherentes («Una hora y 45 esperando a ser atendidos» → tópico
de espera; «los almuerzos son excelentes» → comida; «hubo un mal servicio» → mala
atención). Dos fallan: «hay una cerca», que no tiene contenido y no debería asignarse, y
un fragmento que menciona buena atención y cae en el tópico de mala atención.

### Paso 5 — Largo mínimo (diagnóstico, no se cambia)

| Mínimo | Fragmentos | Pierde | Reseñas perdidas | Tópicos | Atípicos | eta² | Basura | Mayor |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 10 | 5.913 | — | — | 42 | 31,1 % | 0,400 | 5 | 5,9 % (r 4,07) |
| 20 | 5.295 | 10,5 % | 3 | 39 | 27,6 % | 0,469 | 2 | 17,0 % (r 1,89) |
| 25 | 4.982 | 15,7 % | 12 | 33 | 30,8 % | 0,434 | 0 | 11,4 % (r 1,86) |

**Recomendación: dejar el mínimo en 10.** Subirlo sí reduce la basura, pero reintroduce
el cajón negativo —17,0 % con rating 1,89 en el umbral de 20— y empeora la partición por
polaridad (eta² de 0,400 a 0,469). Se pagaría entre el 10 % y el 16 % del corpus por un
resultado peor en lo que más importa. Los cinco tópicos basura salen más baratos vía
reducción de atípicos y, más adelante, fusión.

Nota metodológica: el diagnóstico filtra la tabla existente por `largo_caracteres` en
vez de volver a segmentar. Subir el mínimo solo elimina cláusulas y las que quedan son
idénticas, así que el atajo es fiel salvo por el margen de la normalización de espacios.

### Paso 6 — Atípicos y dimensiones

Sobre la configuración final (mts=30, ms=15, reducción a 0,65; 19,3 % de atípicos):

| | % atípico | n |
|---|---:|---:|
| `n_dim = 0` | 36,3 % | 1.722 |
| `n_dim = 1` | 14,1 % | 2.483 |
| `n_dim >= 2` | 9,8 % | 1.708 |

**Los fragmentos fuera del esquema a priori siguen sobrerrepresentados**, casi cuatro
veces más que los de dos o más dimensiones. La reducción de atípicos no corrigió el
sesgo, solo bajó el nivel general.

De los 625 atípicos con `n_dim = 0`, la revisión de 20 ejemplos da tres grupos:

1. **Sin contenido temático (unos 10 de 20).** «Recomendado», «Recomendadisimo»,
   «Sobrevalorado», «no vale la pena», «Pierden su dinero», «Recomendado 100%». Son
   juicios sin asunto. Que queden fuera es correcto.
2. **Temas genuinamente nuevos (unos 6 de 20).** Y son los interesantes: **la carta o
   menú** («Variada carta», «La carta es bastante variada, por lo cual pensaba probar
   algo más»), **la inocuidad** («pedí un pie de limón y estaba dañado (moho)»), **la
   infraestructura frente al clima** («si les llueve en la sede del centro y están en la
   mesa abajo de la ventana se mojaron fijo») y **la honestidad en el cobro** («nadie
   debe tomarse siquiera 50 pesos que no son suyos»). Ninguno cabe en las seis
   dimensiones. Esto es exactamente lo que el objetivo 2 debía encontrar.
3. **Fallos de recall del diccionario (unos 4 de 20).** «La mejor chuleta del Cauca»,
   «Buenos almuerzos ejecutivos», «Ese toque picante combinado con la miel», «La masa
   merece mención» son todos comida, y el diccionario no los ve.

### Recomendación de configuración

| Componente | Valor |
|---|---|
| Embeddings | `paraphrase-multilingual-MiniLM-L12-v2` sobre `texto` |
| UMAP | `n_neighbors=15`, `n_components=5`, `min_dist=0.0`, coseno, `random_state=42` |
| HDBSCAN | `min_cluster_size=30`, `min_samples=15` |
| c-TF-IDF | `texto_limpio` con negaciones, unigramas y bigramas, `min_df=2` |
| Reducción de atípicos | estrategia `embeddings`, umbral 0,65 |
| Largo mínimo de fragmento | 10 caracteres (sin cambio) |

Resultado: **42 tópicos, 19,3 % de atípicos**, tópico mayor del 6,0 %, cinco tópicos
basura por longitud y 28 tópicos implicados en algún par redundante.

Queda pendiente, y es lo que sigue: la partición por polaridad (eta² 0,400) y los 28
tópicos redundantes. Ambos apuntan a que hay que fusionar, pero eso es agrupar y nombrar
tópicos, que todavía no toca.

---

## 2026-09-22 — Configuración congelada, fusión y evidencia por tópico

**Qué se hizo.** Se congeló la configuración aprobada, se entrenó y guardó el modelo,
se evaluó la fusión de tópicos redundantes, se levantó la evidencia por tópico y se
cuantificaron los temas fuera del esquema a priori. No se calcula AMI ni coherencia
todavía, y la estructura de dos niveles queda propuesta, no aplicada.

### Configuración congelada

En `src/topicos.py`: `MIN_TOPIC_SIZE = 30`, `MIN_SAMPLES = 15`,
`UMBRAL_REDUCCION = 0.65`, `FUSIONES = [[21, 30]]`. El modelo se entrena con
`scripts/entrenar_modelo.py` y se guarda en `data/processed/modelo_bertopic`
(safetensors, con c-TF-IDF y el nombre del modelo de embeddings).

**Resultado: 41 tópicos, 19,3 % de atípicos**, tópico mayor 6,0 %, eta² 0,415.

### Paso 1 — Fusión: ningún umbral automático es defendible

Similitud coseno entre centroides de tópico: mediana 0,413, p90 0,701, p99 0,861,
máximo 0,913.

El problema no es elegir un umbral sino la **cascada transitiva**: la fusión por pares
propaga, y unos pocos enlaces arrastran a decenas de tópicos.

| Umbral | Grupos que fusionan | Tópicos finales | Mayor grupo | % del corpus |
|---:|---:|---:|---:|---:|
| 0,72 (relativo, p99) | 3 | 17 | 24 tópicos | **45,2 %** |
| 0,80 | 1 | 26 | 17 tópicos | 38,7 % |
| 0,85 | 2 | 33 | 9 tópicos | 23,7 % |
| 0,88 | 3 | 38 | 3 tópicos | 9,3 % |
| 0,90 | 2 | 40 | 2 tópicos | 6,2 % |
| 0,92 | 0 | 41 | — | — |

**El umbral relativo que se venía usando para contar duplicados (0,72) fundiría 24
tópicos en uno solo con el 45,2 % del corpus.** Sirve para señalar redundancia, no para
decidir fusiones.

Los umbrales altos no crean cajón —a 0,88 el mayor grupo es del 9,3 % con rating 4,77,
no un cajón negativo— pero **son semánticamente erróneos**, porque lo que acerca a esos
centroides es el registro evaluativo compartido, no el tema:

- A 0,90 se fusionarían T3 (elogio global del lugar y la comida, r 4,75) con T24
  («compartir, familia, amigos, cenar», r 4,82). T24 es un tema propio e interpretable
  —la ocasión de consumo: «Ambiente familiar excelente», «Un lugar muy agradable para
  compartir momentos especiales», «atención como en casa»— y disolverlo dentro del
  elogio genérico perdería justo lo que sirve para orientar la comunicación digital de
  un establecimiento.
- A 0,88 se sumaría además T7 (servicio excelente, r 4,79) al mismo grupo, borrando la
  única distinción de servicio positivo.

Métricas de las fusiones automáticas, para dejarlas registradas: a 0,90, 40 tópicos,
atípicos 19,3 %, mayor 6,2 % (r 4,76), eta² 0,415. A 0,88, 38 tópicos, atípicos 19,3 %,
mayor 9,3 % (r 4,77), eta² 0,413. Es decir, **la fusión no mejora ninguna métrica**: el
eta² de la polaridad no baja y los atípicos no se mueven.

**Decisión: no se usa umbral automático.** Se fusiona a mano el único par que es el
mismo asunto, **T21 + T30 → referente gastronómico de Popayán**, verificado por sus
fragmentos («un restaurante emblemático de comida típica payanesa y un referente
gastronómico», «El mejor lugar en Popayán para probar varios platos típicos»). De 42
tópicos se pasa a 41. Las demás agrupaciones se resuelven en el nivel de `tema` de la
estructura de dos niveles, que es reversible y revisable.

### Paso 3 — Evidencia por tópico

`docs/evidencia_topicos.md`: para los 41 tópicos y el grupo de atípicos, sus 10
términos, tamaño, rating medio, porcentaje de 1-2 estrellas, concentración por local,
dimensión dominante, largo mediano y **5 fragmentos completos**. Los ejemplos son una
muestra aleatoria con `random_state=SEMILLA`, no los documentos representativos de
BERTopic, para no sesgar hacia el centro del tópico.

### Paso 4 — Los cuatro temas nuevos

Cada tema se acota con una expresión regular sobre el texto plegado. Son reglas
estrechas: dan un **piso** de cuántos fragmentos hay, no una medición precisa, y tienen
falsos positivos (el detalle está en `scripts/temas_nuevos.py`).

Dos reglas hubo que corregirlas:

- **Infraestructura y clima** incluía `fri[oa]` y `calor`, que capturaban «comida fría»
  —temperatura del plato, no del local—. Con esos términos daba 55 fragmentos, de los
  que la mayoría eran falsos positivos. Quitados, quedan 11.
- **Inocuidad** mezclaba el incidente concreto con la mención genérica de higiene, que
  suele ser elogio («qué limpieza»). Se separaron.

| Tema | Fragmentos | % corpus | Rating medio | 1-2★ | Atípicos | ¿Tópico propio? |
|---|---:|---:|---:|---:|---:|---|
| Carta o menú | 211 | 3,6 % | 3,64 | 28 % | 22 % | Parcial: T36 concentra el 21 % |
| Inocuidad (incidente) | 53 | 0,9 % | **1,62** | **79 %** | 28 % | No, disperso en 13 tópicos |
| Honestidad en el cobro | 39 | 0,7 % | **2,08** | **69 %** | **44 %** | No; los atípicos son su mayor grupo |
| Infraestructura y clima | 11 | 0,2 % | 3,55 | 27 % | **55 %** | No; los atípicos son su mayor grupo |
| Inocuidad (higiene, cualquier signo) | 12 | 0,2 % | 3,50 | 42 % | 33 % | No |

Corpus de referencia: rating medio 3,70, 28 % de 1-2 estrellas.

Lecturas:

- **Ninguno de los cuatro tiene tópico propio.** El más cerca es la carta o menú, con
  T36 («menú, variado, menú variado») quedándose con el 21 % de sus menciones; el resto
  se reparte en 29 tópicos.
- **Inocuidad y cobro son los temas más negativos del corpus**: 1,62 y 2,08 de rating
  medio, contra 3,70 general. Son pocos fragmentos pero altamente destructivos por
  reseña.
- **Cobro e infraestructura viven sobre todo en los atípicos** (44 % y 55 %). Son los
  temas que el modelo no alcanza a formar porque no llegan al `min_cluster_size` de 30.
- La carta o menú es el único con masa suficiente (211 fragmentos, 3,6 %) para sostener
  un tópico propio si se bajara el mínimo, a costa de los problemas ya documentados.

### Paso 5 — Qué hay dentro del 19,3 % de atípicos

Clasificación manual de 60 atípicos (muestra con `random_state=SEMILLA`, guardada en
`data/processed/muestra_atipicos.csv`). Se usan tres categorías, con la segunda
subdividida para distinguir el fallo de recall:

| Categoría | n | % |
|---|---:|---:|
| Sin contenido temático | 21 | 35 % |
| Tema dentro de las seis dimensiones | 24 | 40 % |
| · el diccionario sí lo detectó | 17 | 28 % |
| · fallo de recall del diccionario | 7 | 12 % |
| **Tema fuera de las seis dimensiones** | **15** | **25 %** |

Extrapolado a los 1.141 atípicos: unos 399 sin contenido, unos 456 de las seis
dimensiones (de los cuales ~80 son fallos de recall) y unos **285 de temas nuevos**.

**Sin contenido temático** son juicios e intenciones sin asunto: «Recomendado» (aparece
cinco veces en la muestra de 60), «Totalmente recomendado», «no pienso volver», «Hay
mejores opciones muy cerca», más meta-comentarios sobre la propia reseña («Es imposible
que todos opinemos igual y estemos equivocados»). Que queden fuera es correcto.

**Temas fuera del esquema** confirman y amplían los cuatro ya identificados, y aparecen
dos más que no se habían visto:

- Medios de pago: «que no tienen datáfono», «no reciben tarjetas».
- Horarios e información digital: «No contestan para hacer un domicilio y uno va a las
  9 y está todo cerrado cuando los horarios de Google dicen que cierran...». Es
  directamente relevante para el objetivo de comunicación digital.
- Políticas del local: mascotas, ingreso de bebidas propias.
- Publicidad engañosa: «eso se puede catalogar como un engaño y una publicidad
  engañosa».
- Cobro: propina «voluntaria» incluida en la factura sin preguntar.
- Inocuidad: intoxicación alimentaria, moho.
- **Trato al personal**, que no se había visto: dos fragmentos donde el comensal critica
  cómo el dueño trata a sus empleados («si no hubiera quien lave platos, quien cocine,
  quien sirva, su NEGOCIO NO FUNCIONARÍA»).

**Conclusión del paso 5: en torno a un 35 % del 19,3 % de atípicos es ruido y un 25 % es
señal temática nueva.** El resto son temas de las seis dimensiones que el agrupamiento
no alcanzó a capturar.

### Hallazgo lateral: una reseña en árabe

Un fragmento del corpus está escrito en alfabeto árabe («شكراً، بارك الله فيك») y llegó
hasta aquí como apto en español. Es 1 de 5.913 fragmentos (0,02 %), en 1 reseña, y quedó
como atípico, así que no afecta ningún resultado. Se deja constancia porque indica que
la detección de idioma heredada tiene alguna fuga; no se corrige, porque la selección
del corpus se reutiliza del proyecto original por decisión registrada.

---

## 2026-09-22 — Estructura de dos niveles, calidad y contraste con el diccionario

**Qué se hizo.** Se aplicó la estructura de dos niveles aprobada, se midió la calidad
del modelo, se contrastó contra el diccionario y se consolidaron los temas de baja masa.
El modelo no se tocó: la asignación vive en `src/etiquetas.py` y es reversible.

### Decisión sobre T29: es comida, no patrimonio

Se leyeron sus 56 fragmentos. El principio que organiza el tópico es **la procedencia
de la cocina**, no el patrimonio payanés:

- Cocina mexicana: unos 18 fragmentos, el bloque mayor, sin ninguna relación con
  Popayán («La mejor comida mexicana de Popayán con auténtico sabor mexicano»).
- Cocina del Pacífico colombiano y afrocolombiana: unos 9 («gastronomía ancestral
  afrocolombiana del Pacífico, contando con sabedoras ancestrales»).
- Cocina colombiana tradicional y caucana: unos 8.
- Española: 3. Peruana: 1.
- Postre Eduardo Santos, que sí es payanés: 5.

Tres razones para **comida, subtema «cocina por origen»**:

1. El eje del tópico es de dónde viene la cocina, y el componente mayoritario —el
   mexicano— no tiene nada de patrimonial para Popayán.
2. El diccionario coincide: comida 75 %, patrimonio 20 %.
3. El contenido genuinamente patrimonial ya tiene tópicos propios, T17 (empanadas,
   pipián, salpicón; patrimonio 61 %) y T19 (centro histórico). Etiquetar T29 como
   patrimonio diluiría la dimensión con tacos mexicanos.

### Corrección: «carta o menú» no es un atributo nuevo

Al revisar el diccionario para asignar el `tipo`, resulta que **`menú` y `bebida` son
términos de la dimensión `comida`** (junto con plato, porción, ingredientes, pizza,
hamburguesa, postre, pollo, arroz, carne). T36 está tagueado comida al 100 % y T20 al
57 %.

Es decir, la lectura del paso anterior —que la carta o menú era uno de los cuatro temas
fuera del esquema— **era incorrecta**: el diccionario lo cubre. Lo que sí es
distinguible es tratar la *oferta* como atributo propio en vez de como calidad de la
comida, pero eso es un refinamiento dentro de `comida`, no un tema externo. Quedan
`tipo = atributo_esquema`, con subtemas `carta y menu` y `bebidas`.

### Paso 1 — Estructura aplicada

`data/processed/topicos_etiquetados.csv`, 41 filas con `topico_id`, `tema`, `subtema`,
`tipo`, `polaridad`, `n`, `pct_corpus`, `rating`, `pct_1_2_estrellas` y `c_v`.

**Umbrales de polaridad, declarados:** `positiva` si el rating medio del tópico es
**≥ 4,2**; `negativa` si es **≤ 2,5**; `mixta` en el resto.

Los ocho subtemas de comida: pizza, hamburguesas, carnes, asiática, café, postres,
pollo asado y cocina por origen (T29), más `presentacion y variedad`, `bebidas` y
`carta y menu`. Patrimonio lleva el subtema `centro historico` (T19).

### Paso 2 — Agregados

De 5.913 fragmentos, **4.772 están asignados (80,7 %)** y 1.141 son atípicos. Los
porcentajes siguientes son sobre el corpus asignado.

| Tipo | Tópicos | Fragmentos | % asignado | Rating |
|---|---:|---:|---:|---:|
| atributo_esquema | 25 | 3.180 | 66,6 % | 3,68 |
| valoracion_global | 10 | 970 | 20,3 % | 3,95 |
| atributo_nuevo | 6 | 622 | 13,0 % | 4,37 |

**Un quinto del corpus asignado no habla de ningún atributo**: son valoraciones
globales, recomendaciones, intención de volver y satisfacción. Para el objetivo 3 esos
970 fragmentos no tienen con qué contrastarse, porque no describen un aspecto de la
experiencia sino un veredicto sobre ella.

Ranking de temas por tamaño:

| Tema | Tópicos | n | % asignado | Rating | % 1-2★ | Tipo |
|---|---:|---:|---:|---:|---:|---|
| comida | 16 | 1.500 | 31,4 % | 3,83 | 23,9 | esquema |
| servicio | 4 | 690 | 14,5 % | 3,78 | 26,5 | esquema |
| experiencia global | 5 | 526 | 11,0 % | 4,12 | 18,8 | valoración |
| espera | 1 | 355 | 7,4 % | **1,88** | **75,8** | esquema |
| recomendación | 3 | 347 | 7,3 % | 3,47 | 33,1 | valoración |
| ambiente | 1 | 334 | 7,0 % | 4,34 | 11,1 | esquema |
| referente en la ciudad | 2 | 276 | 5,8 % | 4,55 | 7,2 | **nuevo** |
| ocasión de consumo | 2 | 223 | 4,7 % | 4,58 | 4,9 | **nuevo** |
| patrimonio | 2 | 161 | 3,4 % | 4,45 | 11,8 | esquema |
| precio | 1 | 140 | 2,9 % | 3,70 | 25,0 | esquema |
| infraestructura y espacio | 1 | 89 | 1,9 % | 3,69 | 21,3 | **nuevo** |
| intención de volver | 1 | 50 | 1,0 % | 4,80 | 4,0 | valoración |
| satisfacción | 1 | 47 | 1,0 % | 4,74 | 4,3 | valoración |
| medios de pago | 1 | 34 | 0,7 % | 3,26 | 29,4 | **nuevo** |

Ranking por rating: arriba intención de volver (4,80), satisfacción (4,74), ocasión de
consumo (4,58) y referente en la ciudad (4,55); abajo, y muy separada, **la espera
(1,88, con el 75,8 % de reseñas de una o dos estrellas)**. La espera es el único tema
cuyo rating cae por debajo de 3 y concentra el malestar del corpus.

**Asimetría de polaridad en los atributos nuevos.** Ninguno de los seis tópicos de tipo
`atributo_nuevo` es negativo: el 80,2 % de sus fragmentos está en tópicos positivos y
el 19,8 % en mixtos, contra un 23,9 % de fragmentos negativos en `atributo_esquema`. No
significa que no haya quejas sobre atributos nuevos: significa que **los atributos
nuevos que alcanzaron masa para formar tópico son los positivos** (ocasión de consumo,
referente en la ciudad), mientras que los nuevos negativos —inocuidad, cobro,
infraestructura frente al clima— se quedaron dispersos y en los atípicos por no llegar
al `min_cluster_size` de 30. Es un sesgo del método, no del corpus, y hay que decirlo
al interpretar.

### Paso 3 — Calidad

| Indicador | Valor |
|---|---:|
| Coherencia `c_v` (Röder et al., 2015) | **0,484** |
| Coherencia `c_npmi` | **−0,038** |
| Diversidad top-10 (Dieng et al., 2020) | **0,664** |

Se reportan las dos coherencias a propósito. `c_v` es la medida de referencia y permite
comparar con la literatura; `c_npmi` es más conservadora y se le reprocha menos sesgo
optimista. Los bigramas del c-TF-IDF se parten en palabras sueltas, porque las medidas
de coherencia trabajan sobre el vocabulario de los documentos, donde el bigrama no
existe.

**Interpretación.** Un `c_v` de 0,48 es moderado: aceptable para texto corto, pero lejos
del 0,55-0,65 que se suele considerar bueno. El `c_npmi` cercano a cero es el dato
incómodo: dice que los términos principales de un tópico **no coaparecen en el mismo
fragmento mucho más de lo que cabría por azar**. Hay una razón estructural: el fragmento
mediano tiene 10 palabras, así que dos términos del tópico rara vez caben en el mismo
documento. La coherencia por co-ocurrencia está penalizada por la unidad de análisis
elegida, no solo por el modelo. Aun así, no se puede afirmar que los tópicos sean
léxicamente coherentes.

La diversidad de 0,664 significa que **un tercio de los términos principales se repite
entre tópicos**, lo que concuerda con los 27 tópicos implicados en algún par redundante.

Los seis tópicos menos coherentes son todos de plato o de oferta: bebidas (0,249),
infraestructura y espacio (0,265), carta y menú (0,276), cocina por origen (0,293),
hamburguesas (0,297) y café (0,301). Tiene sentido: su vocabulario es una lista de cosas
que no coaparecen («limonada, vinos, jugo, mango»). Los más coherentes son los grandes
tópicos de dimensión: patrimonio (0,784), experiencia global (0,761), espera (0,740),
servicio (0,735), ambiente (0,711).

El `c_v` medio por tipo es prácticamente igual en los tres (0,475 esquema, 0,505 nuevo,
0,495 valoración): los atributos nuevos no son menos coherentes que los del esquema.

### Paso 4 — Contraste con el diccionario

Tabla cruzada completa en `data/processed/cruzada_topico_dimension.csv`: para cada uno
de los 41 tópicos, el porcentaje de sus fragmentos que activa cada dimensión, más el
porcentaje sin ninguna.

**AMI entre tópico y dimensión**, sobre los fragmentos con exactamente una dimensión
activa (2.483 fragmentos, el 42,0 % del corpus):

| Base | n | AMI | ARI | Nulo por permutación | Exceso |
|---|---:|---:|---:|---|---:|
| Solo fragmentos asignados | 2.134 | **0,4056** | 0,1698 | −0,0000 ± 0,0020 | +0,4056 |
| Incluyendo atípicos como categoría | 2.483 | 0,3522 | 0,1253 | −0,0002 ± 0,0018 | +0,3523 |

De los 2.483 fragmentos con una sola dimensión, 2.134 (85,9 %) están asignados a un
tópico. El nulo se estima con 200 permutaciones de la etiqueta de dimensión.

**Lectura: hay acuerdo moderado, no equivalencia.** Un AMI de 0,41 sobre un nulo de cero
dice que los tópicos y las dimensiones comparten estructura real, pero que **los tópicos
no son una redescripción de las seis dimensiones**. El ARI, mucho más bajo (0,17), lo
confirma desde otro ángulo: la partición por pares coincide poco, porque un tópico suele
repartirse entre varias dimensiones y una dimensión entre muchos tópicos.

**En cuántos tópicos se reparte cada dimensión:**

| Dimensión | Fragmentos | Tópicos | En el mayor | En los 3 mayores | Tópico principal |
|---|---:|---:|---:|---:|---|
| espera | 338 | 32 | **62,7 %** | 70,7 % | T0 (espera) |
| precio | 409 | 36 | 30,8 % | 49,4 % | T10 (precio) |
| ambiente | 1.024 | 37 | 25,2 % | 57,6 % | T2 (ambiente) |
| servicio | 1.482 | 40 | 22,5 % | 46,7 % | T1 (servicio) |
| patrimonio | 252 | 34 | 19,8 % | 42,1 % | T17 (patrimonio) |
| comida | 2.312 | 38 | **11,8 %** | 29,8 % | T3 (experiencia global) |

Ninguna dimensión se concentra en un solo tópico. **La espera es la única con una
correspondencia fuerte**: casi dos tercios en T0, lo que era previsible porque es un
asunto acotado y con vocabulario propio (hora, minutos, esperando). **Comida es el caso
opuesto**: se reparte en 38 tópicos y su tópico principal ni siquiera es de comida, sino
el de experiencia global. Es la dimensión más grande y la menos específica: casi
cualquier elogio la menciona.

**Tópicos de tipo `atributo_nuevo` y el diccionario:** de sus 622 fragmentos, **234
(37,6 %) no activan ninguna dimensión**, contra el 20,8 % del resto del corpus asignado:
casi el doble. El desglose muestra que el promedio esconde dos situaciones distintas:

| Tópico | Tema | Sin dimensión | n |
|---|---|---:|---:|
| T40 | medios de pago | **91,2 %** | 34 |
| T16 | infraestructura y espacio | **76,4 %** | 89 |
| T9 | referente en la ciudad | 38,3 % | 154 |
| T8 | ocasión de consumo | 25,8 % | 155 |
| T12 | referente en la ciudad | 23,0 % | 122 |
| T24 | ocasión de consumo | 11,8 % | 68 |

Medios de pago e infraestructura son **invisibles para el diccionario** (91 % y 76 % sin
dimensión): son atributos nuevos en sentido estricto. Ocasión de consumo y referente en
la ciudad sí rozan el diccionario —lo activan por las palabras de ambiente y comida que
traen— pero lo que los agrupa (para quién es el sitio, qué lugar ocupa en la ciudad) no
está en el esquema.

### Paso 5 — Temas emergentes de baja masa

**Advertencia obligatoria: las reglas son de piso, no una medición.** Cada tema se
recupera con una expresión regular estrecha sobre el texto plegado. Tiene falsos
negativos (formulaciones que no usan esas palabras) y falsos positivos documentados. Las
cifras acotan el orden de magnitud. Las reglas completas están en
`scripts/temas_baja_masa.py` y la tabla en `data/processed/temas_baja_masa.csv`.

Referencia del corpus: rating 3,70, 28 % de 1-2 estrellas, 19,3 % de atípicos.

| Tema | Frag. | % corpus | Reseñas | Rating | % 1-2★ | % atípicos | Tópicos | % sin dim. |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Inocuidad | 53 | 0,90 % | 52 | **1,62** | **79,2** | 28,3 | 13 | 24,5 |
| Honestidad en el cobro | 52 | 0,88 % | 47 | **1,87** | **75,0** | **51,9** | 13 | 36,5 |
| Horarios e información digital | 47 | 0,79 % | 42 | 2,49 | 59,6 | 29,8 | 14 | 36,2 |
| Infraestructura y clima | 11 | 0,19 % | 11 | 3,91 | 18,2 | **54,5** | 6 | 27,3 |
| Trato al personal | 1 | 0,02 % | 1 | — | — | 100 | 1 | 100 |

Ejemplos:

- **Inocuidad** — «Lamentablemente, el pollo estaba crudo y, como consecuencia, todos
  los que lo consumimos nos enfermamos»; «pedimos un pie de limón y estaba dañado
  (moho), solicito revisar estrictamente que los alimentos cumplan...».
- **Cobro** — «Pésima idea de cobrar al realizar el pedido y preguntar si se desea
  incluir el servicio, ya que después de recibirlo...»; «te cobran hasta por pedir salsa
  de tomate».
- **Horarios e información digital** — «Uno llama y no contestan, para qué tienen un
  número si no contestan»; «uno va a las 9 y está todo cerrado cuando los horarios de
  Google dicen que cierran...».
- **Infraestructura y clima** — «Cuando llueve toda la zona del patio se inunda,
  deberían mejorar el drenaje»; «Al mediodía hace mucho calor bajo el techo plástico».
- **Trato al personal** — «Con qué derecho maltrata a mi hija, si bien sabido es que los
  negocios FUNCIONAN POR LOS TRABAJADORES».

Lecturas:

- **Los tres primeros son los temas más negativos del corpus.** Inocuidad (1,62) y cobro
  (1,87) están muy por debajo de la espera (1,88), que es el tema negativo más grande.
  Son pocos fragmentos, pero cada uno pesa mucho en la reseña donde aparece.
- **Cobro e infraestructura viven sobre todo en los atípicos** (51,9 % y 54,5 %, contra
  19,3 % del corpus). Son precisamente los temas que el modelo no alcanza a formar.
- **«Trato al personal» no es cuantificable con esta herramienta.** La regla amplia
  (`emplead\w*`) recuperaba quejas *sobre* el personal, no críticas a *cómo se le trata*,
  que es el tema. La regla estrecha deja 1 fragmento. Cualitativamente sí aparece —2 de
  los 60 atípicos clasificados a mano—, pero no se puede dar una cifra defendible. Se
  reporta como observación cualitativa, no como medición.

### Estado

`data/processed/`: `topicos_etiquetados.csv`, `cruzada_topico_dimension.csv`,
`temas_baja_masa.csv`, `temas_baja_masa_ejemplos.csv`, `muestra_atipicos.csv`, más el
modelo en `modelo_bertopic`. Dependencia añadida: `gensim` (dev) para la coherencia.

---

## 2026-09-22 — Sensibilidad, figuras, decisiones y limitaciones

### Paso 1 — Sensibilidad al tamaño mínimo: la hipótesis del umbral NO se sostiene

El modelo congelado no se tocó. Se corrió la misma configuración con
`min_cluster_size` en 20 y 15 para comprobar si inocuidad, honestidad en el cobro y
horarios forman tópico propio cuando el umbral se lo permite.

Regla: un tema «forma tópico propio» si existe un tópico donde al menos el **25 % de
sus fragmentos** pertenecen al tema y que además concentra al menos el **20 % del
tema**. Las dos condiciones son necesarias: la primera evita contar un tópico grande
que apenas lo roza, la segunda un tópico minúsculo que casualmente es puro.

| Configuración | Tópicos | Atípicos | Mayor | Inocuidad | Cobro | Horarios |
|---|---:|---:|---:|---|---|---|
| **30 / 15 (congelada)** | 42 | 19,3 % | 6,0 % | no (26 % en T6) | no (10 % en T1) | no (38 % en T1) |
| 20 / 10 | 74 | 19,2 % | 4,4 % | no (11 % en T50) | no (8 % en T15) | no (21 % en T2) |
| 15 / 7 | 100 | 15,2 % | 4,2 % | no (11 % en T51) | no (10 % en T12) | no (13 % en T8) |

**Bajar el umbral no hace que estos temas formen tópico: los dispersa más.** La
concentración de cada tema en su tópico mayor *cae* al bajar `min_cluster_size` (del
26 % al 11 % en inocuidad, del 38 % al 13 % en horarios). El análisis de sensibilidad
**no sustenta** que su ausencia sea un efecto del umbral.

**La causa es la cohesión, no la masa.** Cohesión media de los pares dentro de cada
grupo en el espacio de embeddings, contra una línea base de grupos aleatorios del mismo
tamaño (200 repeticiones):

| Grupo | n | Cohesión | Nulo | Exceso |
|---|---:|---:|---:|---:|
| T15 comida / pizza | 100 | 0,682 | 0,247 | **+0,435** |
| T40 medios de pago | 34 | 0,586 | 0,250 | **+0,336** |
| T17 patrimonio | 82 | 0,547 | 0,246 | +0,301 |
| T0 espera | 355 | 0,376 | 0,247 | +0,130 |
| T16 infraestructura y espacio | 89 | 0,364 | 0,249 | +0,115 |
| Inocuidad (regla) | 53 | 0,351 | 0,250 | +0,101 |
| Honestidad en el cobro (regla) | 52 | 0,336 | 0,247 | +0,089 |
| Infraestructura y clima (regla) | 11 | 0,267 | 0,244 | +0,023 |
| Horarios e información digital (regla) | 47 | 0,261 | 0,247 | +0,014 |

La comparación decisiva es **medios de pago contra inocuidad**: medios de pago tiene 34
fragmentos —menos que los 53 de inocuidad— y aun así formó tópico propio con
`min_cluster_size = 30`, porque su cohesión es +0,336 contra +0,101.

La explicación es que el embedding agrupa por lo que la cláusula *dice*, no por la marca
superficial que usa la regla. Una queja por moho es, semánticamente, una queja sobre el
plato, y cae junto a las demás quejas sobre platos (14 de 53 fragmentos de inocuidad
están en T6, el tópico de comida negativa). «No tienen datáfono», en cambio, no se
parece a nada más del corpus, y por eso se agrupa.

**Consecuencia para el informe:** la afirmación correcta no es «el umbral los oculta»
sino **«son temas transversales, no tópicos»**: atraviesan varias cláusulas de asuntos
distintos en vez de constituir un asunto propio. Hay que sostenerlos con la regla de
recuperación y el análisis cualitativo, no con el modelo de tópicos, y decirlo así.

### Paso 2 — Tabla consolidada de temas

`data/processed/temas_consolidado.csv`: una fila por tema con los tópicos que lo
componen, número de tópicos, fragmentos, porcentaje del corpus asignado, rating medio,
porcentaje de 1-2 estrellas, tipo, polaridad dominante y subtemas.

La polaridad dominante del tema es la de la mayoría de sus fragmentos, y se declara
`mixta` si ninguna polaridad alcanza el 60 %. Con esa regla, comida, servicio, precio,
recomendación, infraestructura y medios de pago quedan mixtos; espera queda negativo, y
el resto positivos.

Los atípicos, que no entran en la tabla por no tener tema, tienen rating medio 3,20 y un
39,9 % de reseñas de una o dos estrellas: **son más negativos que el corpus** (3,70 y
28 %). Es coherente con el paso anterior: los temas negativos emergentes son los que se
quedan sin agrupar.

### Paso 3 — Figuras

En `figuras/`, PNG y PDF a 300 dpi:

1. `01_distribucion_por_tipo` — barra apilada horizontal, tres clases.
2. `02_temas_por_rating` — puntos ordenados por rating, área proporcional a n, con la
   media del corpus como referencia.
3. `03_mapa_topico_dimension` — mapa de calor de los 15 tópicos mayores.
4. `04_embudo_corpus` — embudo en dos paneles.

Tres reglas para que sean legibles impresas en blanco y negro:

- **La identidad nunca depende del tono.** Las tres clases usan pasos distantes de una
  sola rampa azul (luminancias 58, 122 y 191 sobre 255, a unos 64 puntos entre sí) y,
  en la figura apilada, además tramas distintas. Verificado convirtiendo las figuras a
  escala de grises.
- **Toda magnitud lleva etiqueta directa**, de modo que el valor se lee sin recurrir al
  color ni a la escala.
- **El mapa de calor usa una rampa secuencial de un solo tono**, que en gris se traduce
  en una progresión monótona de luminosidad.

El embudo va en **dos paneles** porque la unidad cambia a mitad de camino: las cuatro
primeras filas son reseñas y las dos últimas fragmentos. En un solo panel, las 5.913
barras de fragmentos parecerían un crecimiento sobre las 2.430 reseñas.

### Paso 4 — Decisiones metodológicas

`docs/decisiones_metodologicas.md`: 15 decisiones con su valor, la alternativa
considerada y la razón del descarte, incluidas las seis pedidas (largo mínimo,
`min_cluster_size`, umbral de reducción de atípicos, modelo de embeddings, fusión manual
y umbrales de polaridad).

### Paso 5 — Limitaciones consolidadas

Las siete limitaciones que deben aparecer en el informe, con su alcance real.

**1. La coherencia por co-ocurrencia es prácticamente nula.** `c_npmi = −0,038`: los
términos principales de un tópico no coaparecen en el mismo fragmento mucho más de lo
que cabría por azar. El `c_v` de 0,484 es moderado. Hay una causa estructural —el
fragmento mediano tiene 10 palabras, así que dos términos del tópico rara vez caben en
el mismo documento, y la medida penaliza la unidad de análisis elegida— pero **no se
puede afirmar que los tópicos sean léxicamente coherentes**. Lo que sostiene su
interpretación es la lectura de fragmentos (`docs/evidencia_topicos.md`), no el
indicador.

**2. Los temas de baja masa se miden con reglas de piso, no con una medición.** Las
cifras de inocuidad, cobro, horarios, infraestructura y trato al personal vienen de
expresiones regulares estrechas sobre el texto. Recuperan un subconjunto reconocible del
tema y tienen falsos negativos (formulaciones que no usan esas palabras) y falsos
positivos documentados por tema. **Acotan el orden de magnitud; no lo miden.** Dos de
las reglas ya tuvieron que corregirse: `fri[oa]` capturaba «comida fría» como si fuera
clima, y la versión amplia de trato al personal recuperaba quejas *sobre* el personal en
vez de críticas a *cómo se le trata*. Con la regla estrecha, trato al personal queda en
1 fragmento: **no es cuantificable con esta herramienta** y se reporta solo como
observación cualitativa, respaldada por 2 de los 60 atípicos clasificados a mano.

**3. La deduplicación usa un proxy débil.** El corpus heredado no tiene identificador de
autor. La clave de duplicado usa `autor_n_resenas` como sustituto, que es lo único
disponible. Falla en ambas direcciones: dos autores distintos con el mismo número de
reseñas y el mismo texto se confundirían; el mismo autor con su contador actualizado
entre capturas no se detectaría. Afecta a 2 filas de 2.432, así que no altera ningún
resultado, pero **la deduplicación no debe presentarse como exacta**.

**4. Hay una fuga en la detección de idioma heredada.** Un fragmento está escrito en
alfabeto árabe («شكراً، بارك الله فيك») y pasó el filtro como apto en español. Es 1 de
5.913 (0,02 %), quedó como atípico y no afecta ningún resultado. Indica que la selección
del corpus, que se reutiliza por decisión, no es perfecta.

**5. El umbral de agrupamiento sesga qué atributos emergentes llegan a verse, y el sesgo
tiene signo.** Ninguno de los seis tópicos de tipo `atributo_nuevo` es negativo: el
80,2 % de sus fragmentos está en tópicos positivos y el resto en mixtos. No es que no
haya quejas sobre atributos nuevos —inocuidad, cobro e infraestructura frente al clima
son de los temas más negativos del corpus, con ratings de 1,62 a 2,49—, sino que **los
atributos emergentes que alcanzaron masa y cohesión para formar tópico son los
positivos**. Los atípicos, donde quedan los otros, son más negativos que el corpus
(3,20 contra 3,70). Interpretar los atributos emergentes solo por los tópicos formados
**subestimaría sistemáticamente lo negativo**.

**6. Cada fragmento hereda la calificación de su reseña.** La calificación es una sola
por reseña y se replica en sus fragmentos, que son 2,4 en promedio y hasta 25. De ahí
tres consecuencias: el rating de un tópico **no es la valoración de ese tema**, sino la
de las reseñas donde aparece; una reseña larga pesa más que una corta en el rating de
cualquier tópico que toque; y los fragmentos de una misma reseña no son observaciones
independientes. Por eso la relación con la calificación se reporta de forma **descriptiva
y no se aplica ninguna prueba de significancia** que asuma independencia. Un caso
concreto: «Aunque la comida estuvo rica, se presentó un inconveniente con el pedido»
aporta dos fragmentos de signo opuesto y ambos heredan las 2 estrellas de la reseña.

**7. Los temas transversales no son tópicos, y el modelo no puede encontrarlos.** El
análisis de sensibilidad de este mismo día muestra que inocuidad, cobro y horarios no
forman tópico propio con ningún `min_cluster_size` probado, porque su cohesión en el
espacio de embeddings es baja (exceso de +0,014 a +0,101 sobre el azar, contra +0,30 o
más de los tópicos que sí se formaron). Son asuntos que atraviesan cláusulas de temas
distintos. **El modelado de tópicos es la herramienta equivocada para ellos**, y su
presencia en el informe se sostiene con la regla de recuperación y el análisis
cualitativo, no con el modelo.

### Estado

`data/processed/`: `temas_consolidado.csv` nuevo, más lo anterior. `figuras/`: ocho
archivos (cuatro figuras en PNG y PDF). `docs/`: `decisiones_metodologicas.md` nuevo,
`evidencia_topicos.md` y esta bitácora. Dependencia añadida: `matplotlib`.

---

## 2026-09-22 — Notebooks definitivos

### Revisión previa de la documentación

Se revisaron `docs/bitacora.md` (1.242 líneas) y `docs/decisiones_metodologicas.md`
buscando frases truncadas: párrafos de prosa que no cierran, ítems de lista cortados,
filas de tabla mal formadas y marcado sin cerrar. **No hay ninguna.** Los dos casos que
marcó la comprobación automática —un ítem sobre horarios y otro sobre cobro— continúan
en la línea siguiente, y las «negritas impares» son spans que envuelven dos líneas, que
es Markdown válido.

### Los notebooks no recalculan

Requisito de partida: deben correr de arriba abajo con kernel limpio leyendo de
`data/processed/`. Dos cálculos lo impedían: la coherencia `c_v` tarda minutos y la
rejilla de sensibilidad reajusta el modelo tres veces. Se añadió
`scripts/persistir_analisis.py`, que los calcula una vez y guarda
`calidad_modelo.csv`, `cohesion_temas.csv` y `sensibilidad_umbral.csv`.

Con eso, los cuatro notebooks corren en segundos.

### Una sola fuente para las dos versiones

El contenido vive en `scripts/notebooks_contenido.py` y el generador
`scripts/generar_notebooks.py` produce las ocho variantes. **La versión local y la de
Colab comparten las celdas exactamente**; solo difiere el preámbulo. Se verificó
comparando el cuerpo celda a celda: idénticos en los cuatro (22, 24, 23 y 32 celdas
compartidas).

Es deliberado: mantener dos copias a mano garantiza que diverjan.

### Contenido

| Notebook | Celdas | Cubre |
|---|---:|---|
| `00_preparacion` | 24 | Del corpus a los fragmentos, embudo y validación de las etiquetas |
| `01_caracterizacion` | 26 | Objetivo 1: composición, calidad, calificación, establecimiento, zona |
| `02_topicos` | 25 | Objetivo 2: embeddings, BERTopic, 41 tópicos, 14 temas, sensibilidad |
| `03_evaluacion` | 34 | Objetivo 3: coherencia, cruzada, AMI, calificación, transversales, limitaciones |

Cada uno abre enunciando el objetivo específico que cubre y cierra con una celda de
hallazgos numerados. La validación del notebook 00 es la que autoriza la decisión de
recalcular las dimensiones por fragmento: reagregadas a nivel de reseña coinciden con la
medición del original con una diferencia máxima del 1,0 %.

### Preámbulo de Colab

Tres celdas. La primera instala dependencias solo si detecta Colab. La segunda resuelve
el acceso a los datos en tres pasos: Drive montado en `MyDrive/topicos-popayan`, subida
de un zip, o la carpeta del repositorio si no se está en Colab. La tercera comprueba que
`data/processed/` tenga lo que el notebook va a leer y lo dice antes de que falle una
celda más abajo.

### Dos errores encontrados al ejecutarlos

Ambos aparecieron al correr los notebooks de verdad, no al escribirlos:

1. **`01_caracterizacion` fallaba con `ArrowInvalid: invalid escape sequence: \u`.** La
   detección de escritura no latina usaba `str.contains` con una clase de caracteres
   `[؀-ۿ...]`. pandas 3 delega las expresiones regulares en RE2 vía Arrow, que
   no admite escapes `\uXXXX`. Se reemplazó por una comprobación en Python sobre el
   nombre Unicode de cada carácter, que además es más legible.
2. **Los cuatro notebooks de Colab fallaban con `ModuleNotFoundError: No module named
   'google'`.** La detección de entorno usaba
   `importlib.util.find_spec("google.colab")`, que no devuelve `None` cuando falta el
   paquete padre, sino que lanza la excepción. Se reemplazó por un `try/except ImportError`.

Verificación final: los ocho notebooks ejecutados con `nbconvert --execute` y kernel
limpio, sin errores. Los de Colab se ejecutan en local porque su detección de entorno
cae en la rama local; es el procedimiento con el que se validan antes de publicarlos.

### README

Documenta el entorno, la estructura, el orden de los scripts que producen
`data/processed/`, cómo ejecutar en local y las dos rutas de Colab (Drive y zip), con
qué hace cada celda del preámbulo y cómo cambiar la carpeta de Drive.

### Estado

`notebooks/`: cuatro locales. `notebooks/colab/`: cuatro de Colab. `scripts/`:
`notebooks_contenido.py`, `generar_notebooks.py` y `persistir_analisis.py` nuevos.
`data/processed/`: `calidad_modelo.csv`, `cohesion_temas.csv` y
`sensibilidad_umbral.csv` nuevos. README reescrito.

---

## 2026-09-23 — Dashboard de resultados

**Qué se hizo.** Un dashboard en Streamlit para presentar los resultados, en `app/`,
ejecutable con `uv run streamlit run app/main.py`. Dependencia añadida: `streamlit`
1.64.0.

### Solo lectura, y se verificó que lo sea

El requisito era que no recalculara nada ni cargara el modelo de BERTopic. Se comprobó
ejecutando las cuatro secciones y revisando `sys.modules` después: **ninguno de
`bertopic`, `umap`, `hdbscan`, `torch`, `sentence_transformers` ni `gensim` llega a
importarse**. El panel arranca en segundos y no necesita GPU ni descargar modelos.

Faltaban dos artefactos que el dashboard necesitaba y que hasta ahora solo se imprimían
por consola. Se añadieron a `scripts/contraste_dimensiones.py`:

- `ami_resultados.csv` — AMI, ARI, línea base por permutación, desviación y exceso, en
  las dos formas de calcularlo.
- `dispersion_dimensiones.csv` — en cuántos tópicos se reparte cada dimensión.

`app/datos.py` comprueba al arrancar que estén los nueve archivos que va a leer, y si
falta alguno lo dice en pantalla en vez de fallar a media navegación.

### Las cuatro secciones

| Sección | Contenido |
|---|---|
| **Resumen** | Embudo (8.451 → 2.430 → 5.913 → 4.772), número de tópicos y temas, AMI y atípicos, más las figuras del embudo y de distribución por tipo. |
| **Temas** | Tabla ordenable de los 14 temas; al elegir uno, sus tópicos con términos, calificación, % de 1-2★ y fragmentos de ejemplo. |
| **Tópicos** | Selector con los 10 términos, tamaño, calificación, concentración por local, dimensión dominante, % sin dimensión, coherencia y cinco fragmentos completos. |
| **Contraste** | Mapa de calor tópico por dimensión, AMI con su línea base, y dispersión de cada dimensión. |

### Decisiones de presentación

**Cada indicador lleva una línea que lo explica.** El destinatario no tiene por qué
saber qué es un AMI ni un c-TF-IDF. Por ejemplo, el AMI se presenta como «compara dos
formas de agrupar los mismos fragmentos; vale 0 cuando coinciden lo que coincidirían dos
agrupaciones al azar, y 1 cuando son idénticas», con su línea base al lado para que se
vea que el 0,41 no es casualidad.

**Sin gráficos decorativos.** Las únicas tres figuras son las del informe, que muestran
algo que la tabla no da: el cambio de unidad del embudo, la proporción entre los tres
tipos de tema, y el patrón del mapa de calor. Todo lo demás son tablas ordenables y
métricas.

**Los ejemplos son muestra aleatoria reproducible**, no los fragmentos más
representativos del tópico. Mostrar los más típicos daría una imagen más limpia que la
real, que es justo lo que no conviene en una presentación de resultados.

**Se conservan las advertencias incómodas.** El resumen dice que los fragmentos sin
asignar promedian 3,20 estrellas contra 3,70 del corpus, y que un quinto de lo agrupado
no describe ningún atributo. El panel no vende el resultado.

### Verificación

- Las cuatro secciones ejecutadas fuera del servidor sustituyendo los widgets, sin
  errores.
- **Barrido completo: los 14 temas y los 41 tópicos**, uno por uno, para descartar
  fallos en casos concretos (subtema vacío, `c_v` nulo, local sin nombre). Cero fallos.
- Servidor arrancado en el puerto 8511: responde 200 y `/_stcore/health` da `ok`, sin
  una sola línea de error en el log.
- 12 pruebas nuevas en `tests/test_app_datos.py` sobre la capa de datos: que no falten
  archivos, que cada tópico tenga fragmentos, que los temas cubran los 41 tópicos, que
  el AMI traiga su línea base y que las figuras que muestra existan. **60 pruebas en
  total, todas pasan.**

### Estado

`app/`: `main.py`, `datos.py`, `secciones.py`. `data/processed/`: `ami_resultados.csv`
y `dispersion_dimensiones.csv` nuevos. README con la sección «Dashboard».

---

## 2026-09-23 — Explorador de fragmentos

**Qué se hizo.** Una quinta sección en el dashboard: un buscador que recibe una consulta
libre y devuelve los K fragmentos más similares, con dos representaciones comparables.

### El modelo de embeddings sí es viable

La pregunta era si cargar el modelo hacía el arranque inaceptable. Medido:

| Operación | Tiempo |
|---|---:|
| `import sentence_transformers` | 5,8 s |
| Cargar el modelo (ya en caché local) | 4,0 s |
| Codificar una consulta | 0,17 s |

Son ~10 s la primera vez. **Con carga diferida y cacheada por sesión el arranque no lo
paga**: el panel sigue levantando en 1 segundo, verificado tras añadir la sección. Solo
la primera búsqueda semántica de cada sesión espera esos 10 s, y se avisa en pantalla
con un spinner que lo dice. No hizo falta renunciar a los embeddings.

### TF-IDF precalculado

`scripts/construir_tfidf.py` produce la matriz con el mismo preprocesamiento del
modelo: parte de `texto_limpio` —minúsculas, sin puntuación, sin stopwords y con las
negaciones conservadas— con unigramas y bigramas, `min_df = 2` y el mismo patrón de
token, importados de `src/topicos.py` para que no puedan divergir.

Resultado: **5.913 fragmentos × 5.823 términos** (3.020 unigramas, 2.803 bigramas),
46.578 valores no nulos, densidad 0,135 %, 400 KB en disco. 38 fragmentos no contienen
ningún término del vocabulario y quedan con norma cero; no se eliminan, simplemente no
son recuperables por este método.

**No se serializa el objeto `TfidfVectorizer`.** Un pickle de scikit-learn ata el
archivo a una versión concreta de la librería. Se guardan sus dos piezas —vocabulario
con su idf, y la matriz ya normalizada— y el dashboard reconstruye el vector de la
consulta replicando lo que haría `transform`: contar términos, aplicar `sublinear_tf`,
multiplicar por idf y normalizar. El analizador se obtiene de un `TfidfVectorizer` sin
ajustar, porque depende solo de los parámetros.

### La sección

Entrada de texto libre, seis consultas de ejemplo como botones, selector de método
(TF-IDF, embeddings o «Comparar los dos») y control de cuántos resultados. Cada
resultado muestra el fragmento completo con su similitud, tópico, tema, calificación y
establecimiento. **Se reporta el tiempo de respuesta de cada método** en cada búsqueda.

En modo comparación los dos rankings van lado a lado y se cuenta cuántos resultados
comparten, que es la forma más directa de ver en qué se diferencian.

La nota en pantalla explica la diferencia sin jerga: TF-IDF busca coincidencia de
palabras y no reconoce sinónimos; los embeddings buscan significado, así que «demora»
puede recuperar «tardaron una hora» aunque no compartan ninguna palabra.

### Lo que muestra la comparación

Con las seis consultas de ejemplo, K = 5:

| Consulta | TF-IDF | Emb. | Comunes |
|---|---:|---:|---:|
| comida en mal estado | 31 ms | 100 ms | 0 |
| demora en la atención | 3 ms | 18 ms | 0 |
| cobro incorrecto | 3 ms | 16 ms | 0 |
| comida típica payanesa | 3 ms | 18 ms | 1 |
| horarios desactualizados | 3 ms | 12 ms | 1 |
| buen lugar para ir en familia | 3 ms | 460 ms | 0 |

**Los dos métodos casi nunca coinciden**, y cada uno falla de una forma distinta que
ilustra bien el punto:

- «comida en mal estado» → TF-IDF devuelve *«El restaurante es de los mejores en los que
  he estado»*, porque «estado» coincide como participio. Los embeddings devuelven
  *«la comida muy mala, sin sabor»*: correcto en polaridad pero desplazado de la
  inocuidad hacia la calidad general.
- «horarios desactualizados» → TF-IDF acierta con *«Dijeron que estaban
  desactualizados»*; los embeddings se van a *«la demora es mucha»*, que es otro asunto.
- «buen lugar para ir en familia» → los embeddings ganan con claridad: *«Un lugar
  estupendo para disfrutar en familia»*, mientras TF-IDF se queda en *«Muy buen lugar»*.

La lectura para el informe es que **ninguna de las dos representaciones es mejor en
abstracto**, y que la búsqueda semántica no resuelve el problema de los temas
transversales: «comida en mal estado» sigue sin recuperar los fragmentos de inocuidad
como grupo, porque el embedding los acerca a las quejas sobre el plato, que es
exactamente lo que ya mostraba el análisis de cohesión.

### Verificación

- **Las 18 combinaciones** de tres métodos por seis consultas de ejemplo, sin errores.
- **Seis casos borde**: consulta vacía, solo espacios, palabra inexistente, solo signos,
  solo stopwords y una sola letra. Todos se manejan sin excepción.
- Arranque del panel medido tras añadir la sección: **1 segundo**, sin cambios.
- 17 pruebas nuevas en `tests/test_busqueda.py`. Una de ellas comprueba la carga
  diferida **en un subproceso**, porque en el mismo proceso cualquier otra prueba ya
  pudo haber traído `torch` a memoria; la primera versión de esa prueba llevaba un
  `or True` que la hacía pasar siempre y se corrigió. **77 pruebas en total.**

### Estado

`app/busqueda.py` nuevo, `app/secciones.py` con la sección `explorador`.
`scripts/construir_tfidf.py` nuevo. `data/processed/`: `tfidf_matriz.npz`,
`tfidf_vocabulario.csv` y `tfidf_indice.csv`. `src/topicos.py` expone `PATRON_TOKEN`,
que antes estaba escrito dentro de la llamada al vectorizador. README con la subsección
«El explorador».

---

## 2026-09-24 — Notebooks exportados a HTML

**Qué se hizo.** Los cuatro notebooks exportados a `docs/notebooks_html/` con sus
salidas ya ejecutadas, para anexarlos al informe sin que el lector tenga que instalar ni
ejecutar nada. El script es `scripts/exportar_notebooks.py`.

**Se vuelven a ejecutar antes de exportar**, en vez de reutilizar salidas guardadas, de
modo que lo que se anexa corresponda al estado actual de `data/processed/`. Los cuatro
corrieron sin errores.

| Archivo | Tamaño | Figuras | Tablas |
|---|---:|---:|---:|
| `00_preparacion.html` | 322 KB | 0 | 5 |
| `01_caracterizacion.html` | 518 KB | 1 | 7 |
| `02_topicos.html` | 450 KB | 1 | 7 |
| `03_evaluacion.html` | 1.008 KB | 2 | 7 |

`00_preparacion` no muestra ninguna figura; las cuatro del informe se reparten entre los
otros tres notebooks.

### Se quitaron los enlaces a CDN

nbconvert enlaza MathJax y require.js desde `cdnjs.cloudflare.com`. Se comprobó que el
contenido no los necesita —cero usos de `require()` y cero fórmulas LaTeX en los cuatro
notebooks—, así que el script los elimina después de exportar. **Los HTML quedan con
cero referencias externas**: se leen sin conexión, que es lo que hace falta en un anexo.

### Verificación

No basta con que el archivo exista; había que comprobar que se vea:

- **Figuras**: se extrajeron las cuatro imágenes de su base64 y se comprobó que son PNG
  válidos con las dimensiones de las figuras originales (2.254 × 1.414, 2.193 × 784,
  2.254 × 1.834 y 2.314 × 1.594). Una se abrió para mirarla: se ve completa, con sus
  etiquetas y su leyenda.
- **Tablas**: se extrajo el contenido de celdas de una tabla y trae los datos reales
  (`c_v 0.4844`, `c_npmi -0.0382`, `diversidad_top10 0.6637`).
- **Salidas de texto**: las tablas impresas con `to_string` aparecen dentro de `<pre>`,
  con su alineación.
- **Markdown**: los encabezados de sección se renderizan como `<h1>` y `<h2>`.
- **Valores esperados**: se buscaron cifras y términos concretos en cada archivo
  (5.913 y 2.430 en el 00, el fragmento en árabe en el 01, `min_cluster_size` en el 02,
  `0.4056` e `inocuidad` en el 03). Todos presentes.
- **Errores**: cero `jp-RenderedError` y cero trazas en los cuatro archivos.

### Sobre el enlace al repositorio

**No se publicó.** El repositorio es local y no tiene remoto configurado, y publicar es
una acción que saca el trabajo fuera de la máquina, así que queda pendiente de decisión
explícita. El README no lleva enlace por ahora; se añadirá cuando se decida dónde
publicarlo.

### Estado

`docs/notebooks_html/` con los cuatro HTML (2,3 MB en total).
`scripts/exportar_notebooks.py` nuevo. README con la subsección «Versión HTML, para
anexar al informe».

---

## 2026-09-24 — Notebooks versionados con sus salidas

**Qué se hizo.** Los cuatro notebooks de `notebooks/` quedan versionados **con sus
salidas guardadas**, para que se lean en GitHub o en Jupyter sin ejecutarlos. Antes solo
existía la versión HTML.

### Una ejecución en vez de dos

`scripts/exportar_notebooks.py` se reestructuró. Antes exportaba a HTML con `--execute`,
lo que ejecutaba los notebooks pero **no guardaba las salidas en el `.ipynb`**. Ahora:

1. `--to notebook --execute --inplace` guarda las salidas en el propio notebook.
2. El HTML se genera **a partir de ese archivo ya ejecutado**, sin volver a ejecutar.

Además de ahorrar una ejecución, garantiza que los dos formatos muestren exactamente las
mismas cifras, que es justo lo que no aseguraba ejecutar dos veces: entre una corrida y
otra podrían cambiar los datos.

### Se limpia el ruido de stderr

La celda que carga el modelo de BERTopic en `02_topicos` dejaba cinco salidas de
`stderr`: un aviso de tqdm, otro del hub de modelos y dos barras de progreso. No son
resultados y además **delataban la ruta local absoluta** de quien ejecutó el notebook.

El script las elimina después de ejecutar. Solo toca `stderr`: los resultados, la salida
estándar y los errores reales quedan intactos, y de todas formas un error haría fallar
la ejecución antes de llegar a este paso.

### Estado de los archivos

| Notebook | `.ipynb` | Salidas | Imágenes | HTML |
|---|---:|---:|---:|---:|
| `00_preparacion` | 36 KB | 12 | 0 | 322 KB |
| `01_caracterizacion` | 227 KB | 14 | 1 | 518 KB |
| `02_topicos` | 183 KB | 12 | 1 | 448 KB |
| `03_evaluacion` | 718 KB | 17 | 2 | 1.008 KB |

Las **50 celdas de código** de los cuatro notebooks tienen salida, con cero errores y
cero salidas de `stderr`.

**Los de `notebooks/colab/` siguen sin salidas, a propósito.** Están pensados para
ejecutarse en Colab; si se ejecutaran en local, sus primeras celdas mostrarían «no se
detectó Colab: se asume el entorno de uv», que en un notebook cuyo propósito es Colab
confundiría más de lo que aporta.

### Verificación

- Las 4 imágenes están guardadas dentro de los `.ipynb` como PNG en base64.
- **Consistencia entre formatos**: se comparó cada línea de salida de texto de los
  `.ipynb` contra el HTML —desescapando las entidades, porque `'` viaja como `&#39;` y
  `>=` como `&gt;=`— y cada imagen por su base64. **134 líneas y 4 imágenes, ninguna
  falta.**
- El HTML sigue sin referencias externas.

### Orden que hay que respetar

`scripts/generar_notebooks.py` reescribe los notebooks **sin** salidas, porque genera
desde el contenido fuente. Si se cambia el contenido: generar primero, ejecutar después.
Queda anotado en el README y en el docstring del script.

---

## 2026-09-25 — Notebook consolidado, dataset y preparación para publicar

### 1. `proyecto_final.ipynb`

Un notebook único que cuenta el estudio de corrido, siguiendo la cadena **problema →
objetivo → pregunta analítica → datos → técnicas → resultados → insights →
recomendaciones**, más limitaciones y anexos. 45 celdas, 19 de código, 4 figuras.

Los cuatro notebooks por etapa se conservan como **anexo**: el consolidado no los
repite, los referencia.

**Los dos componentes de los datos quedan explícitos**, que es lo que pedía la
asignatura:

- **Text Analytics** — el texto libre de la reseña, que es el objeto del análisis, y el
  diccionario de 81 términos que constituye la lectura a priori.
- **Web Analytics** — los metadatos de la plataforma: calificación en estrellas, ficha
  del establecimiento, zona por distancia al Parque Caldas, si el propietario respondió,
  actividad de quien escribe, fecha y volumen de reseñas del local.

El argumento que los une: los temas salen del texto, pero **su interpretación se apoya en
la calificación, la zona y el establecimiento**. Un tema sin su calificación no dice si
es una fortaleza o un problema.

Generado desde `scripts/notebook_final.py`, con versión Colab y HTML como los demás.

### 2. `dataset/`

Cinco archivos con su diccionario de datos y sus hashes:

| Archivo | Unidad | Filas × Col |
|---|---|---|
| `corpus_final.csv` | una reseña | 8.451 × 15 |
| `marco_muestral_final.csv` | un establecimiento | 133 × 19 |
| `dimensiones.csv` | un término | 144 × 8 |
| `fragmentos_topicos.csv` | un fragmento | 5.913 × 22 |
| `temas_consolidado.csv` | un tema | 14 × 10 |

`fragmentos_topicos.csv` une aquí el corpus de fragmentos con su tópico asignado, que en
`data/processed/` viven en archivos separados.

`diccionario_datos.md` describe cada archivo, su unidad de análisis, **todas sus columnas
con tipo y vacíos**, su procedencia y cómo se enlazan entre sí, más el manifiesto de
integridad con los SHA-256. Las tablas de columnas se generan desde los propios CSV; solo
las descripciones se escriben a mano, en `scripts/descripciones_columnas.py`.

**Un bug corregido sobre la marcha**: la primera versión aplicaba `replace(",", ".")` a
la línea entera para el separador de miles, y se comió las comas de la prosa
(«reputacion-popayan, captura de Google Maps» → «reputacion-popayan. captura»). Ahora el
formato se aplica solo al número.

### 3. README como portada

Reescrito: el hallazgo primero, las cuatro figuras embebidas, la tabla de notebooks con
badges de Colab, el dashboard, la estructura, el orden de ejecución completo y la nota de
uso académico.

**Los badges llevan `USUARIO` como marcador**, que hay que reemplazar por el usuario de
GitHub al publicar. Se deja explícito en el propio README para que no pase inadvertido.

### 4. Preparación para publicar — NO se publicó

Se dejó todo listo, pero **la publicación queda pendiente de decisión**, como se pidió.

**Rutas personales eliminadas.** `src/config.py` tenía `/Users/noovou/...` escrito a
mano. Ahora:

```python
ORIGEN = Path(os.environ.get("REPUTACION_POPAYAN", Path.home() / "dev" / "fup" / "..."))
```

Y los notebooks imprimían la ruta absoluta en sus salidas, lo que en un repositorio
público delata el nombre de usuario. El preámbulo ahora imprime solo el nombre de la
carpeta. Se regeneraron y reejecutaron los diez.

**GitHub Pages**: `docs/index.md` como portada con enlaces a los cinco HTML y a la
documentación, `docs/_config.yml` con el tema y `docs/.nojekyll`. Se configura en
Settings → Pages → Source: `main` / carpeta `/docs`.

**Streamlit Community Cloud**: `requirements.txt` y `.streamlit/config.toml`.

El requirements **no incluye `sentence-transformers`** a propósito: arrastra torch, más
de 1 GB instalado, y Community Cloud da 1 GB de RAM. En vez de que falle allí, el
explorador **degrada con elegancia**: `busqueda.hay_embeddings()` comprueba si la
librería y la matriz están disponibles, y si no, ofrece solo la búsqueda por coincidencia
de palabras y lo explica en pantalla. En local sigue funcionando todo.

**Inventario de publicación** (`scripts/inventario_publicacion.py`, no publica nada):

| Bloque | Archivos | Tamaño |
|---|---:|---:|
| `data/` | 26 | 13,07 MB |
| `dataset/` | 7 | 3,95 MB |
| `docs/` | 11 | 3,67 MB |
| `notebooks/` | 10 | 2,28 MB |
| `figuras/` | 8 | 0,90 MB |
| resto | 59 | 0,82 MB |
| **TOTAL** | **121** | **24,69 MB** |

Fuera del repositorio quedan 1.447 MB, casi todo el `.venv`.

**Comprobaciones**: sin rutas personales, sin credenciales. Aparece un correo, el del
autor en `pyproject.toml`, que es intencional.

### Revisión de datos personales del corpus

Hecha antes de preparar nada, porque condiciona la decisión de publicar:

- **Sin correos.** El único `@` del corpus era «meser@s», lenguaje inclusivo.
- **Sin autores identificables.** El corpus no trae nombre ni identificador: solo
  `autor_n_resenas`, un conteo. La anonimización viene de origen.
- **Cinco reseñas con 7+ dígitos**: cuatro son la dirección y el teléfono **comercial** de
  un local, una es «10000000/10» como broma sobre la calificación.
- **33 reseñas mencionan a personal por su nombre** de pila o apodo, tal como lo escribió
  quien reseñó. Ya están publicadas en Google Maps y se conservan porque eliminarlas
  alteraría el texto que se analiza. Queda advertido en el README.

### Estado

Nuevos: `notebooks/proyecto_final.ipynb` (+ Colab + HTML), `dataset/` con 7 archivos,
`requirements.txt`, `.streamlit/config.toml`, `docs/index.md`, `docs/_config.yml`,
`docs/.nojekyll`, y los scripts `construir_dataset`, `diccionario_datos`,
`descripciones_columnas`, `notebook_final` e `inventario_publicacion`. README reescrito.
77 pruebas pasan.

---

## 2026-09-25 — Decisiones previas a la publicación

Repositorio público en `github.com/JLosada-Dev/topicos-popayan`. Tres decisiones, con lo
que implicó cada una.

**1. Se conservan las 33 menciones a personal.** El README lleva ahora una línea
explícita: el corpus las conserva **tal como aparecen publicadas en Google Maps** y **el
análisis no las emplea como variable** —no se extraen, no se cuentan, no entran en
ninguna medición ni figura—. Se mantienen solo porque eliminarlas alteraría el texto que
se segmenta y se vectoriza, y los resultados dejarían de ser reproducibles desde la
fuente original.

**2. El correo del autor en `pyproject.toml` se queda.** Es intencional.

**3. Los embeddings de `multilingual-e5-small` quedan fuera: ahorran 9,0 MB.**

Se verificó antes de confirmarlo. Los notebooks `02_topicos` y `proyecto_final` los
mencionan, pero **solo en celdas de texto** que explican por qué se descartó el modelo:
ninguna celda de código los carga. El dashboard usa exclusivamente MiniLM. Las únicas
referencias en código son `src/embeddings.py`, que solo declara el nombre del modelo, y
`scripts/experimento_topicos.py`, que los regenera en cinco segundos si se quiere repetir
la comparación.

Ya estaban en `.gitignore` desde que se hicieron los primeros commits, así que no hubo
que sacarlos del historial. El README explica por qué no viajan.

**Badges de Colab**: el marcador `USUARIO` se reemplazó por `JLosada-Dev` en los cinco, y
se quitó la advertencia que pedía hacerlo.

### Lo que se publicaría

121 archivos, **24,69 MB**. Fuera quedan 1.447 MB, casi todo el entorno virtual, más los
9,0 MB de los embeddings descartados.

Comprobaciones: sin rutas personales, sin credenciales, un solo correo —el del autor, a
propósito—.

**El push queda preparado pero no ejecutado**, a la espera de revisar el commit.

---

## 2026-09-25 — Contexto de los anexos en el notebook consolidado

El autor añadió a mano, al final de `proyecto_final.ipynb`, una línea que da contexto a
la tabla de anexos: dice que todos los recursos están en el repositorio y que **las rutas
de la tabla son relativas a su raíz**. Sin ella, la tabla listaba rutas sin decir
respecto a qué.

**La edición se subió a la fuente.** Vivía solo en el `.ipynb`, y
`scripts/generar_notebooks.py` reconstruye los notebooks desde
`scripts/notebook_final.py`: la siguiente regeneración la habría borrado. Ahora está en
la fuente y sobrevive.

Dos ajustes menores al integrarla: la URL se convirtió en enlace de Markdown, para que
GitHub y el HTML la rendericen como tal, y se quitó el espacio que quedaba antes del
punto final.

Aprovechando el cambio se completó la tabla con los dos recursos que faltaban: el propio
notebook consolidado y `app/`, con el comando para lanzar el dashboard.

Regenerados y reejecutados los diez notebooks; la línea llega a los tres formatos
—`.ipynb`, Colab y HTML—.

---

## 2026-09-25 — También se ejecutan los notebooks de Colab

Antes se dejaban sin salidas a propósito, porque están pensados para ejecutarse en Colab
y unas salidas producidas en local podían despistar. El criterio cambia: **un revisor que
abra cualquiera de los diez debe ver resultados sin tener que ejecutar nada.**

`scripts/exportar_notebooks.py` ejecuta ahora también los de `notebooks/colab/`. Su
detección de entorno cae en la rama local, así que la primera celda muestra «no se
detectó Colab: se asume el entorno de uv, no se instala nada» y la tercera confirma que
los datos están. Es información honesta: enseña que el notebook funciona en los dos
entornos.

El HTML se sigue generando solo desde los locales, que son idénticos salvo el preámbulo.

**Los diez notebooks quedan con todas sus celdas ejecutadas y cero errores.**

### Qué entregar a un revisor

| Destinatario | Archivo |
|---|---|
| Informe y revisor | `notebooks/proyecto_final.ipynb` |
| Revisor sin Jupyter | `docs/notebooks_html/proyecto_final.html` |
| Quien quiera ejecutarlo sin instalar | `notebooks/colab/proyecto_final_colab.ipynb` |

Los cuatro por etapa son anexo en los tres casos.

---

## 2026-09-25 — Gráfico de temas en el dashboard

**Qué se hizo.** En la sección Temas, un gráfico de barras horizontales que acompaña a la
tabla sin reemplazarla: los 14 temas por calificación media, con línea de referencia en
la media del corpus y el número de fragmentos junto a cada barra.

### Encaja ahí, y no duplica nada

Se comprobó antes de implementarlo. La figura `02_temas_por_rating.png` **no se usa en
ninguna sección del dashboard** —solo están la 04, la 01 y la 03—, así que el gráfico es
aditivo. Y la secuencia tabla → gráfico → detalle es natural: el gráfico da la lectura
visual de lo que la tabla dice en números.

### Altair, no matplotlib

**Altair viene con Streamlit**, así que no añade dependencias. Matplotlib está en el
proyecto pero **no en `requirements.txt`**: usarlo habría roto el despliegue en Community
Cloud. Se añadió una prueba en subproceso que verifica que el dashboard no lo importe, y
así no se puede colar sin que salte.

### La paleta se extrajo a `src/paleta.py`

Los colores vivían en `src/figuras.py`, que importa matplotlib. Ahora están en un módulo
sin dependencias que importan tanto las figuras del informe como el dashboard, de modo
que **el mismo tipo de tema tiene el mismo color en el papel y en pantalla** sin duplicar
valores ni arrastrar matplotlib.

### Una tensión en los requisitos, y cómo se resolvió

«Ordenados por calificación media» y «agrupados por tipo en tres bloques separados» no
son del todo compatibles: al facetar por tipo no queda un ranking único de 14, sino tres
rankings. Se optó por **ordenar dentro de cada bloque**, que es lo que pedía la
especificación más concreta. El filtro permite además aislar un tipo.

El coste: no se lee de un vistazo cuál es el peor de los 14. Como los tipos tienen
calificaciones medias distintas, el conjunto se aproxima igualmente a un orden global.

### Nombres legibles, centralizados

El gráfico dejó a la vista que los temas se mostraban sin tildes —«ocasion de consumo»,
«satisfaccion»—, porque las columnas van sin tildes por convención del proyecto. El mapa
de nombres legibles estaba escrito dentro de `scripts/generar_figuras.py`; se movió a
`src/etiquetas.py`, su sitio natural, y ahora lo usan las figuras, la tabla del dashboard
y el gráfico. Se corrigió también la tabla, porque queda junto al gráfico y la
inconsistencia habría sido evidente.

### La línea de cierre

Bajo el gráfico se señala que **ningún atributo emergente con tópico propio resulta
negativo**, que no significa que no haya quejas sobre atributos nuevos —inocuidad 1,62 y
cobro 1,87 son de lo peor del corpus— sino que **no llegaron a formar tópico**. Remite a
la **limitación 5** del notebook `03_evaluacion` y de esta bitácora.

### Verificación

Los cuatro estados del filtro —Todos y cada tipo— sin errores. La especificación del
gráfico revisada campo a campo: tres facetas en orden, tres capas (barra, texto, línea),
orden descendente por calificación dentro de cada bloque, referencia en 3,70 y las
etiquetas numéricas. Las cinco secciones siguen funcionando, 79 pruebas pasan.

Los notebooks no se tocaron, como se pidió.

**Pendiente**: no se pudo revisar el gráfico renderizado en el navegador, porque esta
sesión no tiene esa herramienta. La verificación es estructural.

---

## 2026-09-25 — Sección Presentación en el dashboard

**Qué se hizo.** Once pantallas para proyectar en una sustentación de 15 minutos, en
`app/presentacion.py`. Una idea por pantalla, tipografía grande, sin tablas anchas ni
salidas de código. Las demás secciones quedan intactas para explorar después.

### Dos decisiones consultadas antes de implementar

**El mapa de calor.** Son 15 filas × 6 columnas con un número por celda: proyectado no se
lee. Se optó por que **el titular sea el AMI** —0,41 sobre una línea base de 0,00— con el
contraste espera 62,7 % contra comida 11,8 %, y el mapa debajo como respaldo visual.

A petición del autor, el titular **interpreta** el contraste en vez de solo enunciarlo:
«la espera se comporta como una categoría bien definida; la comida, como un dominio
entero que el modelo descompone en dieciséis tópicos». Ojo con las dos cifras, que son
distintas y conviene no confundir: **16** son los tópicos cuyo *tema* es comida, y **38**
los tópicos que contienen algún fragmento que activa la dimensión comida.

**Objetivo y pregunta.** Se mantienen como pantallas separadas: la 3 enuncia los tres
objetivos específicos, que es lo que el jurado espera ver, y la 4 plantea la pregunta
como hipótesis contrastable junto con la medida que la responde.

### Dos decisiones propias, aprobadas

En **Recomendaciones** se conserva solo la audiencia del establecimiento —el notebook
tiene tres— porque es lo que dice el objetivo general y porque tres audiencias no caben
en una pantalla proyectada. En la **11** las limitaciones van arriba y el cierre abajo,
para no terminar la sustentación en tono de disculpa.

### Reparto de las figuras

| Pantalla | Figura |
|---|---|
| 5 · Los datos | Embudo del corpus |
| 7 · Resultados | Mapa de calor tópico × dimensión |
| 8 · Atributos emergentes | Distribución por tipo, más una vista propia |
| 9 · Insights | Temas por calificación |

La distribución por tipo se trasladó de Resultados a Atributos emergentes. Es el montaje
natural de esa pantalla —muestra el 13 % que el esquema no contempla— y además descarga
Resultados, que con el AMI y el mapa ya tiene bastante para 80 segundos.

La **vista de atributos emergentes** es la única que no existía como figura: barras
horizontales de los cuatro temas por calificación, con la media del corpus como
referencia. Se hizo en Altair, como el gráfico de la sección Temas, para no añadir
dependencias.

### Demostración en vivo

La pantalla de Resultados lleva un botón que **salta al explorador con la consulta
«comida en mal estado» ya escrita**. Sirve para enseñar en directo el límite de la
técnica: TF-IDF devuelve «el restaurante es de los mejores en los que he estado», porque
«estado» coincide como participio.

El salto se implementó con un callback que escribe `st.session_state["seccion"]` y
`st.session_state["consulta"]`; para que funcione, el selector de sección de la barra
lateral pasó a tener `key="seccion"`.

### Verificación

Las once pantallas se ejecutan sin errores. La navegación se comprobó en los bordes:
`_ir_a(-5)` da 0 y `_ir_a(99)` da 10. El salto al explorador deja la consulta cargada y
esa consulta devuelve resultados, que es lo que hace falta para que la demostración no
falle delante del jurado. **83 pruebas pasan**, cuatro de ellas nuevas y específicas de
esta sección.

**Pendiente**: no se pudo revisar la presentación proyectada ni en el navegador, porque
esta sesión no tiene esa herramienta. La verificación es estructural.

---

## 2026-09-25 — Revisión visual del dashboard con navegador

**Qué se hizo.** Se añadió la capacidad de revisar el dashboard renderizado, que hasta
ahora faltaba: la verificación era estructural y los defectos de maquetado quedaban para
que los viera el autor.

### Dos vías descartadas primero

**Captura con el Chrome del sistema.** Falla: Streamlit se hidrata por websocket y
`--virtual-time-budget` adelanta temporizadores pero no espera una conexión real. La
captura sale con el esqueleto de carga.

**`streamlit.testing.v1.AppTest`.** Sí funciona y viene con Streamlit, sin instalar nada:
ejecuta la aplicación real, permite simular clics y detecta excepciones. Pero **no da
píxeles**, que era justo lo que hacía falta.

### La vía elegida

`playwright` como dependencia de desarrollo, con Chromium headless (94 MB). No toca
`requirements.txt` ni el despliegue en Cloud. `scripts/revisar_dashboard.py` levanta el
dashboard en un puerto aparte, **espera a que desaparezca el esqueleto de carga**,
recorre las once pantallas y las cinco secciones, captura cada una y recoge los errores
de consola.

### Cuatro defectos que solo se ven renderizando

**1. La navegación no avanzaba.** El botón «Siguiente» cambiaba la pantalla y el selector
de salto, que conserva su valor entre recargas, la devolvía inmediatamente a la anterior.
Se peleaban por dos variables distintas. Corregido con una sola fuente de verdad: el
selector escribe en la misma clave que leen los botones. **Las once pantallas mostraban
la primera** y ninguna prueba estructural lo detectaba.

**2. Los decimales salían con punto.** `0.41` y `3.70` donde en español va coma.

**3. Las etiquetas del gráfico de atributos emergentes se cortaban.** Costó cuatro
intentos, cada uno verificado en el navegador:

- `autosize: fit/padding` sobre un gráfico por capas → `AttributeError`, la página entera
  reventó con una traza en rojo.
- El mismo `autosize` bien aplicado → las etiquetas desaparecieron del todo.
- Ancho explícito → Streamlit lo ignoraba, porque sin el parámetro `width` aplica el del
  contenedor; con `width="content"` sí lo respeta, pero seguían recortadas contra el
  borde.
- **Solución**: el nombre del tema va **dentro de la barra**, no en el eje. Vega calcula
  el espacio del eje a partir del ancho disponible y con «infraestructura y espacio» no
  llega. Dentro siempre cabe y además se lee mejor proyectado.

Dos detalles más que aparecieron por el camino: `alt.value(0)` sobre una capa con `x`
cuantitativo rompe Vega —hubo que construir las capas por separado y fijar el orden como
lista en vez de `sort="-x"`—, y si una capa declara `axis=None` en `x`, Vega suprime el
eje compartido de todas.

**4. La pantalla 8 se reestructuró.** El gráfico pasó de una columna estrecha a ancho
completo, debajo de la figura. En dos columnas no hay sitio para cuatro nombres largos
más un eje de 1 a 5.

### Estado

84 pruebas pasan, dos nuevas sobre el estado compartido de la navegación. Cero errores de
consola en las once pantallas y las cinco secciones. Las capturas van al directorio
temporal, no al repositorio.

A partir de ahora la revisión visual del dashboard **se puede hacer sin depender del
autor**:

```bash
uv run python -m scripts.revisar_dashboard              # todo
uv run python -m scripts.revisar_dashboard presentacion # solo la presentación
```

---

## 2026-09-25 — Revisión visual sección por sección

El autor detectó que el gráfico de la sección Temas salía **sin barras**. Tenía razón y
el fallo fue de método: lo capturé pero no lo miré. Se revisaron las cinco secciones, una
por una, y apareció más de lo previsto.

### El gráfico de Temas no dibujaba nada

Mismo origen que el de la presentación: con el ancho del contenedor, Streamlit aplica
`autosize: fit`, el área de trazado se queda sin espacio y **las barras salen con ancho
cero**. Reconstruido con el enfoque que ya funcionaba: nombre del tema dentro de la
barra, ancho explícito y `width="content"`. Se conservan las tres facetas por tipo y el
filtro.

### Un bug de rendimiento en el Explorador

La sección tardaba en cargar y las capturas salían a medio renderizar, con el contenido
de la sección anterior debajo. La causa: `hay_embeddings()` **importaba
`sentence_transformers` solo para comprobar si existe**, y esa importación tarda **5,3
segundos**. Se cambió a `importlib.util.find_spec`, que localiza el paquete sin
ejecutarlo: **0 ms**, y además cacheado.

No era solo un problema de captura: cada vez que alguien abría el Explorador esperaba
esos cinco segundos.

### La nota de métodos no se mostraba

El texto que explica la diferencia entre TF-IDF y embeddings estaba definido pero la
línea que lo pintaba se había perdido en una edición anterior. Repuesta, y ahora se
recorta sola cuando la búsqueda semántica no está disponible.

### Separadores a la española

Todo el panel mostraba `0.41`, `3.70`, `19.3 %` y `1141 fragmentos`. Se centralizaron
`coma()` y `miles()` en `src/etiquetas.py`, junto a `legible()`: las tres responden a la
misma pregunta, cómo se escribe algo para que lo lea una persona. Aplicados en las cinco
secciones y en la presentación.

### Tildes en los subtemas

`asiatica`, `cafe`, `presentacion y variedad` aparecían sin tildes en el detalle del tema
y en el selector de tópicos. Ya usan `legible()`.

### El script de revisión, corregido

Dos fallos propios que producían capturas engañosas:

- **Esperaba solo a que desapareciera el esqueleto de carga.** Al cambiar de sección
  Streamlit no lo muestra, así que capturaba a media ejecución. Ahora espera también a
  que desaparezca el indicador de estado, el botón «Stop» de la barra superior.
- **La ventana era de 1.000 px de alto** y las secciones largas salían cortadas, porque
  Streamlit usa scroll interno y `full_page` no lo extiende. Subida a 2.400 px.

### Nota sobre el servidor

El dashboard que el autor tenía abierto corría código anterior al arreglo de la
navegación: Streamlit sin `watchdog` no recarga al cambiar los archivos. Hay que
reiniciarlo tras cada cambio.

### Estado

84 pruebas pasan, cero errores de consola en las once pantallas y las cinco secciones,
todas revisadas de verdad esta vez.

---

## 2026-09-25 — Tres correcciones en la presentación

### El gráfico de atributos emergentes no era proporcional

El autor detectó que las barras no guardaban proporción con la calificación. Se midió en
píxeles sobre la captura, en vez de estimarlo a ojo:

| Barra | Fin observado | Fin esperado | Error |
|---|---:|---:|---:|
| ocasión de consumo · 4,58 | 1.151 | 1.151 | 0 |
| referente en la ciudad · 4,55 | 1.146 | 1.146 | 0 |
| infraestructura y espacio · 3,69 | 999 | 959 | **+40** |
| medios de pago · 3,26 | 925 | 867 | **+58** |

**La causa.** `mark_bar` con solo una codificación `x` dibuja la barra desde el cero de
la escala. Como el dominio empieza en 1, el cero queda fuera y Vega recorta la barra
contra el borde del área de trazado, con lo que su longitud deja de ser proporcional al
valor. Las barras cortas se alargaban más que las largas.

**La corrección.** Se ancla el origen explícitamente con `x2` a una columna `base = 1.0`.
Medido de nuevo: **error máximo de 1 píxel** en las cuatro barras.

**El número al final también era engañoso**: mostraba los fragmentos mientras el eje
estaba en estrellas. Ahora al final de la barra va **la calificación** —que es lo que
mide el eje— en grande y en negro, y el número de fragmentos debajo, más pequeño y en
gris, como dato secundario.

### Glosa de las técnicas

La pantalla 6 nombraba BERTopic, UMAP, HDBSCAN y c-TF-IDF sin explicar qué hacen. Ahora
cada una lleva su glosa: los *embeddings* convierten cada fragmento en 384 números que
resumen su significado, *UMAP* los comprime a 5 sin perder la vecindad, *HDBSCAN* busca
zonas densas y las declara grupos —dejando fuera lo que no encaja—, y *c-TF-IDF* nombra
cada grupo con las palabras que son suyas y de ningún otro.

### Primera limitación, reescrita

Atribuye la limitación a la medida y no al resultado, con el texto que dio el autor: los
indicadores de coherencia léxica **resultan poco informativos** con fragmentos de diez
palabras de mediana, porque los términos de un tópico rara vez caben en el mismo texto.

### Verificación

Los tres cambios revisados con el script, sobre la página renderizada. La proporción de
las barras se comprobó midiendo píxeles, no a ojo. Al reescribir la función del gráfico
se perdió el bloque de cierre —«Ninguno resulta negativo»— y se repuso, lo que la
revisión visual detectó. 84 pruebas pasan, cero errores de consola.

---

## 2026-09-25 — Paquete de entrega y presentación exportada

### `entrega/`

Estructura para subir a Classroom, con el informe aparte. Todo se **copia**, nunca se
mueve: el proyecto sigue funcionando igual. `scripts/armar_entrega.py` la regenera
entera en cada ejecución, así que no puede quedar desincronizada.

### La presentación, como PNG y como PDF

`scripts/exportar_presentacion.py` recorre las once pantallas con Playwright, oculta la
barra lateral y los controles de navegación, y fotografía **solo el área de contenido**.
Cada captura sale a 3.200 px de ancho —factor de escala 2— y el PDF sale en 16 × 9
pulgadas, apto para proyectar y para imprimir a 200 ppp.

**Cuatro problemas que solo aparecieron al mirar el resultado:**

1. **El mapa de calor salía cortado**, sin la fila T14. Con una ventana de 900 px de alto
   el contenedor de la imagen la recorta. Se subió la ventana a 2.000 px.
2. **Desapareció el bloque de demostración de la pantalla 7.** El código ocultaba el
   hermano anterior a la fila de navegación fuera lo que fuese; ahora solo lo oculta si
   de verdad es un separador.
3. **Las páginas tenían alturas distintas**, de 1.504 a 2.830 px, así que al proyectar
   cada pantalla habría salido a una escala diferente. Ahora cada una se compone sobre
   un lienzo 16:9 uniforme, centrada y sin deformarse.
4. **Sobraba blanco al final de cada captura**, porque Streamlit deja el contenedor con
   la altura de la ventana. Al encajarlo en 16:9 el contenido quedaba muy pequeño. Se
   recorta la franja vacía antes de componer.

### Verificación del PDF

Se renderizó de vuelta con `pdftoppm` y se comparó cada página con su captura de origen,
aplicándole la misma transformación:

- **Once páginas**, todas de 1.152 × 648 pt: 16:9 exacto.
- **Orden correcto**: cada página correlaciona entre 0,994 y 0,999 con la suya, y además
  se parece más a la suya que a cualquiera de las otras diez. El orden está comprobado,
  no supuesto.
- Gráficos completos, sin barra lateral ni controles de navegación.

Una primera versión del chequeo dio orden incorrecto: comparaba las páginas del PDF
—recortadas y encajadas— contra las capturas sin transformar. El fallo era de la
comprobación, no del PDF.

### `entrega/` sí se versiona

Se propuso ignorarla, por ser derivada al cien por cien de archivos que ya están en el
repositorio. **El autor decidió lo contrario**: prefiere tener congelado exactamente lo
que subió a Classroom, aunque se pueda regenerar. Queda versionada, 14 MB.

La consecuencia obligó a un cambio: `armar_entrega.py` borraba `entrega/` entera antes
de reconstruirla, y eso se habría llevado por delante las capturas y el PDF que produce
`exportar_presentacion.py`. Ahora solo rehace las carpetas que son suyas, `1_notebook/`
y `2_dataset/`, y respeta `3_presentacion/`.

Se añadió también `proyecto_final.html` a `1_notebook/html/`: el `.ipynb` necesita
Jupyter o Colab, y sin esa copia un docente que no use ninguno de los dos no podría leer
el estudio.

Para regenerar, en este orden:

```bash
uv run python -m scripts.armar_entrega          # estructura y copias
uv run python -m scripts.exportar_presentacion  # capturas y PDF
```

---

## 2026-09-25 — Las capturas sueltas salen del paquete

`entrega/3_presentacion/capturas/` se elimina: las once imágenes duplicaban 2,9 MB de lo
que el PDF ya contiene, y el entregable de esa carpeta es el PDF.

**El script que las genera se conserva**, porque el PDF se construye a partir de ellas.
Ahora las deja en `figuras/presentacion/`, fuera del paquete y sin versionar, con un
aviso en la salida de que no van a la entrega.

El README del paquete se actualizó: la carpeta se describe como el PDF con las once
pantallas en 16:9, una por página.

Verificado de nuevo tras el cambio: **once páginas, en orden y de tamaño uniforme**.

El paquete pasa de 14,1 MB a **12,0 MB**.
