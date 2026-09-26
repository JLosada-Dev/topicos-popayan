# Diccionario de datos

Este paquete reúne los cinco archivos necesarios para entender y reproducir el
estudio: las tres entradas que se heredan del proyecto previo y las dos salidas
propias.

Todos son CSV con codificación UTF-8, separador coma y encabezado en la primera
fila.

## Resumen

| Archivo | Unidad de análisis | Filas | Columnas | Procedencia |
|---|---|---:|---:|---|
| `corpus_final.csv` | una reseña | 8.451 | 15 | Proyecto previo `reputacion-popayan`, captura de Google Maps vía Apify |
| `marco_muestral_final.csv` | un establecimiento | 133 | 19 | Proyecto previo `reputacion-popayan`, marco muestral del estudio |
| `dimensiones.csv` | un término del diccionario | 144 | 8 | Proyecto previo `reputacion-popayan`, diccionario construido y validado allí |
| `fragmentos_topicos.csv` | un fragmento (cláusula) | 5.913 | 22 | Producido por este proyecto con `scripts/construir_fragmentos.py` |
| `temas_consolidado.csv` | un tema | 14 | 10 | Producido por este proyecto con `scripts/tabla_temas.py` |

## Cómo se enlazan entre sí

```
marco_muestral_final.csv  --place_id-->   corpus_final.csv
corpus_final.csv          --review_id-->  fragmentos_topicos.csv
dimensiones.csv           ------------->  las seis columnas booleanas de
                                          fragmentos_topicos.csv
fragmentos_topicos.csv    --topico----->  temas_consolidado.csv
```

## `corpus_final.csv`

**Unidad de análisis:** una reseña · **8.451 filas × 15 columnas**

**Procedencia:** Proyecto previo `reputacion-popayan`, captura de Google Maps vía Apify

| Columna | Tipo | Vacíos | Descripción |
|---|---|---:|---|
| `review_id` | texto | 0 | Identificador único de la reseña, asignado por Google Maps. |
| `place_id` | texto | 0 | Identificador del establecimiento, asignado por Google Maps. |
| `establecimiento` | texto | 0 | Nombre comercial del establecimiento. |
| `rating` | entero | 0 | Calificación en estrellas que dio la persona, de 1 a 5. |
| `texto` | texto | 4349 | Texto de la reseña, tal como se publicó. |
| `fecha` | texto | 0 | Fecha y hora de publicación. |
| `respuesta_dueno` | booleano | 0 | Si el propietario respondió la reseña. |
| `autor_n_resenas` | entero | 0 | Número de reseñas que ha escrito esa persona. **Es el único dato de autoría: no hay nombre ni identificador.** |
| `rat_comida` | decimal | 3270 | Calificación de comida, cuando la persona la dio por separado. |
| `rat_servicio` | decimal | 3261 | Calificación de servicio por separado. Vacío si no la dio. |
| `rat_ambiente` | decimal | 3341 | Calificación de ambiente por separado. Vacío si no la dio. |
| `fuente` | texto | 0 | Origen de la captura. |
| `tiene_texto` | booleano | 0 | Si la reseña trae texto o es solo una calificación. |
| `largo` | decimal | 0 | Longitud del texto en caracteres. |
| `apto` | booleano | 0 | Si la reseña entra al estudio: tiene texto y al menos 50 caracteres. |

## `marco_muestral_final.csv`

**Unidad de análisis:** un establecimiento · **133 filas × 19 columnas**

**Procedencia:** Proyecto previo `reputacion-popayan`, marco muestral del estudio

| Columna | Tipo | Vacíos | Descripción |
|---|---|---:|---|
| `place_id` | texto | 0 | Identificador del establecimiento; enlaza con `corpus_final.csv`. |
| `name` | texto | 0 | Nombre comercial. |
| `type` | texto | 0 | Categoría principal en Google Maps. |
| `subtypes` | texto | 0 | Categorías secundarias, separadas por coma. |
| `address` | texto | 0 | Dirección comercial. |
| `latitude` | decimal | 0 | Latitud. |
| `longitude` | decimal | 0 | Longitud. |
| `dist_parque_caldas` | decimal | 0 | Distancia en metros al Parque Caldas, centro de la ciudad. |
| `zona` | texto | 0 | `centro` o `fuera`, según la distancia al centro histórico. |
| `rating` | decimal | 0 | Calificación media del establecimiento en Google Maps. |
| `reviews` | decimal | 0 | Número total de reseñas del establecimiento. |
| `reviews_per_score_1` | decimal | 0 | Cuántas reseñas de 1 estrella tiene. |
| `reviews_per_score_2` | decimal | 0 | Cuántas de 2 estrellas. |
| `reviews_per_score_3` | decimal | 0 | Cuántas de 3 estrellas. |
| `reviews_per_score_4` | decimal | 0 | Cuántas de 4 estrellas. |
| `reviews_per_score_5` | decimal | 0 | Cuántas de 5 estrellas. |
| `query` | texto | 0 | Consulta con la que se encontró el establecimiento. |
| `incluido` | booleano | 0 | Si entró al marco muestral del estudio. |
| `motivo_exclusion` | texto | 127 | Por qué se excluyó, cuando aplica. |

## `dimensiones.csv`

**Unidad de análisis:** un término del diccionario · **144 filas × 8 columnas**

**Procedencia:** Proyecto previo `reputacion-popayan`, diccionario construido y validado allí

| Columna | Tipo | Vacíos | Descripción |
|---|---|---:|---|
| `dimension` | texto | 0 | A cuál de las seis dimensiones pertenece el término. |
| `termino` | texto | 0 | El término, en su forma legible. |
| `raiz` | texto | 0 | Raíz o expresión regular con la que se busca en el texto normalizado. |
| `categoria` | texto | 0 | Tipo de término: genérico, plato, atributo. |
| `estado` | texto | 0 | `incluido` o `excluido`. Solo se usan los incluidos, 81 de 144. |
| `patron_contexto` | texto | 135 | Expresión regular de contexto, cuando el término la necesita. |
| `modo_contexto` | texto | 135 | Cómo se evalúa el contexto: `requiere`, `veta_previa` o `veta_posterior`. |
| `nota` | texto | 5 | Observación de quien construyó el diccionario. |

## `fragmentos_topicos.csv`

**Unidad de análisis:** un fragmento (cláusula) · **5.913 filas × 22 columnas**

**Procedencia:** Producido por este proyecto con `scripts/construir_fragmentos.py`

| Columna | Tipo | Vacíos | Descripción |
|---|---|---:|---|
| `fragmento_id` | texto | 0 | Identificador del fragmento: `review_id` más su número de orden. |
| `review_id` | texto | 0 | Reseña de la que procede. Permite reagrupar por reseña. |
| `place_id` | texto | 0 | Establecimiento; enlaza con `marco_muestral_final.csv`. |
| `establecimiento` | texto | 0 | Nombre comercial. |
| `zona` | texto | 0 | `centro` o `fuera`. |
| `rating` | entero | 0 | Calificación de la reseña de origen. **Se hereda: todos los fragmentos de una misma reseña comparten la misma calificación.** |
| `fragmento_num` | entero | 0 | Posición del fragmento dentro de su reseña. |
| `n_fragmentos_resena` | entero | 0 | Cuántos fragmentos produjo esa reseña. |
| `texto` | texto | 0 | El fragmento, enmascarado con `[LOCAL]` pero natural: conserva mayúsculas, tildes y stopwords. **Es el que alimenta los embeddings.** |
| `texto_limpio` | texto | 10 | Minúsculas, sin puntuación ni stopwords, con las negaciones conservadas. **Solo alimenta el c-TF-IDF.** |
| `largo_caracteres` | entero | 0 | Longitud del fragmento en caracteres. |
| `largo_palabras` | entero | 0 | Longitud en palabras. |
| `tiene_local` | booleano | 0 | Si el fragmento contiene el marcador `[LOCAL]`. |
| `ambiente` | booleano | 0 | Si el fragmento activa la dimensión ambiente. |
| `comida` | booleano | 0 | Si activa la dimensión comida. |
| `espera` | booleano | 0 | Si activa la dimensión tiempo de espera. |
| `patrimonio` | booleano | 0 | Si activa la dimensión patrimonio o tradición. |
| `precio` | booleano | 0 | Si activa la dimensión precio. |
| `servicio` | booleano | 0 | Si activa la dimensión servicio. |
| `n_dim` | entero | 0 | Cuántas dimensiones activa, de 0 a 5. |
| `topico` | entero | 0 | Tópico asignado por el modelo. `-1` significa sin asignar. |
| `topico_sin_reduccion` | entero | 0 | Tópico antes de reasignar atípicos, para auditar ese paso. |

## `temas_consolidado.csv`

**Unidad de análisis:** un tema · **14 filas × 10 columnas**

**Procedencia:** Producido por este proyecto con `scripts/tabla_temas.py`

| Columna | Tipo | Vacíos | Descripción |
|---|---|---:|---|
| `tema` | texto | 0 | Nombre del tema, asignado a mano tras leer los tópicos que lo componen. |
| `tipo` | texto | 0 | `atributo_esquema`, `atributo_nuevo` o `valoracion_global`. |
| `topicos` | texto | 0 | Qué tópicos lo componen. |
| `n_topicos` | entero | 0 | Cuántos tópicos lo componen. |
| `fragmentos` | entero | 0 | Cuántos fragmentos reúne. |
| `pct_asignado` | decimal | 0 | Porcentaje sobre los fragmentos asignados a algún tópico. |
| `rating` | decimal | 0 | Calificación media, ponderada por el tamaño de cada tópico. |
| `pct_1_2_estrellas` | decimal | 0 | Porcentaje de fragmentos de reseñas de 1 o 2 estrellas. |
| `polaridad_dominante` | texto | 0 | `positiva`, `negativa` o `mixta`. |
| `subtemas` | texto | 12 | Subtemas, cuando el tema se subdivide. |

## Manifiesto de integridad

Hash SHA-256 de cada archivo, para verificar que es el mismo que se usó en el
estudio:

| Archivo | Bytes | SHA-256 |
|---|---:|---|
| `corpus_final.csv` | 1.979.504 | `8478fa5ace844b13c3dcc239f753e327af52e1bc607590e5dddba2c2f90c6fbd` |
| `marco_muestral_final.csv` | 32.933 | `2c4a8587aed84d48dc42b2d8928e14e6c54a332af546daf9d385bdf0069ec175` |
| `dimensiones.csv` | 15.231 | `67393d3a4e7cf1ff0187bdad49a5ecf9b6e6beec7dcd5fe12fb2ea35124a21df` |
| `fragmentos_topicos.csv` | 2.106.948 | `fc84f8893ed9ed194538240cc105d9a9000381ea96b2614c91b84cac0cb1a0ba` |
| `temas_consolidado.csv` | 1.281 | `8e73d16c341a8e2c86bd423c66151975c58e2f4a130f42b03e8ba1030a2f2856` |

Para comprobarlo:

```bash
shasum -a 256 dataset/*.csv
```

`manifiesto.csv`, en esta misma carpeta, trae los mismos datos en formato
tabular.
