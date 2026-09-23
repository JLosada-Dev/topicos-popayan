# CLAUDE.md — topicos-popayan

## Qué es este proyecto

Trabajo final de la asignatura Text & Web Analytics (Especialización en Data Analytics
para Marketing Digital, FUP). Identifica los temas emergentes en reseñas de Google Maps
de establecimientos gastronómicos de Popayán mediante modelado de tópicos, y los
contrasta con seis dimensiones definidas a priori (comida, servicio, precio, ambiente,
tiempo de espera, patrimonio o tradición).

Metodología CRISP-DM. Este repositorio cubre preparación, modelado, evaluación y
despliegue.

### Objetivo general
Identificar los temas emergentes en las reseñas de establecimientos gastronómicos de
Popayán, mediante técnicas de análisis de texto, para establecer su correspondencia con
las dimensiones tradicionalmente utilizadas para evaluar la experiencia gastronómica y
orientar la comunicación digital de los establecimientos.

### Objetivos específicos
1. Caracterizar el corpus de reseñas mediante análisis descriptivo y verificación de
   calidad, para definir los requerimientos de su preparación.
2. Determinar los temas emergentes mediante modelado de tópicos, para representar los
   asuntos que abordan los comensales.
3. Evaluar la correspondencia de los temas con las dimensiones predefinidas y su
   relación con la calificación, mediante medidas de acuerdo y análisis descriptivo,
   para derivar orientaciones de comunicación digital.

## Entorno de trabajo (obligatorio)

- Este proyecto usa **uv exclusivamente**. Instalar con `uv add`, ejecutar con `uv run`.
- NUNCA usar pip, pip install, conda, virtualenv, ni invocar `python` directamente.
- Toda dependencia queda registrada en `pyproject.toml` y `uv.lock`.
- Kernel de notebooks registrado desde el entorno de uv.
- Python 3.12.

## Relación con el proyecto original

Existe un proyecto previo (`reputacion-popayan`, capítulo de libro) sobre el mismo
corpus, en `/Users/noovou/dev/fup/reputacion-popayan`. Ese proyecto es SOLO LECTURA.

- Nunca escribir, mover ni borrar nada dentro de esa ruta.
- No importar módulos del original. Si se necesita una función (segmentación,
  diccionario), se COPIA a `src/` con un comentario que indique archivo y función de
  origen.
- Cada archivo leído del original se registra en `data/external/manifiesto.csv` con su
  ruta, número de filas y hash SHA-256.

## Decisiones ya tomadas (no cambiar sin consultar)

- Unidad de análisis del modelado: fragmento (reseña segmentada por cláusula, es decir,
  oración dividida en conectores adversativos). Cada fragmento conserva el id de su
  reseña de origen.
- Los fragmentos se generan re-segmentando las 2.432 reseñas con la regla del proyecto
  original. `sentimiento_fragmentos.csv` NO se usa: solo contiene las cláusulas que
  activan alguna dimensión (4.121 de 5.694 únicas), así que está sesgado hacia el
  vocabulario del diccionario.
- Las etiquetas de dimensión se recalculan por fragmento, aplicando el diccionario a
  cada cláusula. No se heredan de la reseña, a diferencia del proyecto original.
- Las reseñas sin ninguna dimensión activa se conservan (114 de 2.432).
- Corpus: reseñas en español con al menos 50 caracteres (2.432 esperadas). Se reutiliza
  la selección e identificación de idioma del proyecto original, no se recalcula.
- Texto para embeddings: el texto ORIGINAL, sin minúsculas forzadas, sin quitar tildes,
  sin quitar stopwords, sin lematizar. La normalización del proyecto original NO se usa
  para embeddings.
- Nombres de establecimientos dentro del texto: se reemplazan por el marcador `[LOCAL]`
  antes de generar embeddings.
- Texto para c-TF-IDF: minúsculas, stopwords en español más lista propia
  (`popayan`, `restaurante`, etc.), unigramas y bigramas.
- Datos faltantes: no se imputan. Las calificaciones por dimensión vacías quedan vacías.
- Duplicados: se elimina solo el duplicado real (mismo autor anonimizado y mismo texto).
  Textos genéricos idénticos de autores distintos se conservan.
- Modelo: BERTopic (UMAP + HDBSCAN + c-TF-IDF) con embeddings de sentence-transformers.
- Contraste con dimensiones: tabla cruzada tópico por dimensión sobre todos los
  fragmentos, y AMI solo sobre fragmentos con exactamente una dimensión activa.
- Relación con la calificación: descriptiva (media y porcentaje de 1-2 estrellas por
  tópico). Sin pruebas de significancia que asuman independencia, porque los fragmentos
  de una misma reseña no son independientes.
- Semilla fija `SEMILLA = 42` en todo procedimiento aleatorio (UMAP, muestreos).
- La variable `tipo_cocina` NO existe y no se usa.

## Notebooks

- Un notebook por etapa: `00_preparacion`, `01_caracterizacion`, `02_topicos`,
  `03_evaluacion`.
- De cada notebook se mantienen DOS versiones equivalentes, una para ejecución local y
  otra para Google Colab. La versión Colab monta Drive o pide subir los archivos, e
  instala dependencias en su primera celda.
- Los notebooks importan funciones desde `src/`. Las celdas quedan cortas y legibles,
  acompañadas de celdas de texto que expliquen qué se hace, por qué y qué dice el
  resultado.
- Todo notebook debe correr de arriba abajo tras reiniciar el kernel.
- Lo costoso (embeddings) se calcula una vez y se guarda en disco.

## Convenciones

- Nombres de variables, columnas, funciones y archivos en español, sin tildes.
- Código reutilizable en `src/`, scripts puntuales en `scripts/`, pruebas en `tests/`
  con pytest.
- Salidas intermedias en `data/interim/`, finales en `data/processed/`, figuras en
  `figuras/`. Formato CSV salvo embeddings, que van en `.npy`.
- Cada decisión o resultado relevante se registra en `docs/bitacora.md` con fecha,
  qué se hizo, por qué y cifras obtenidas.

## Forma de trabajar

- Antes de implementar algo que no esté en "Decisiones ya tomadas", proponer y esperar
  confirmación.
- Trabajar por pasos pequeños. Al terminar cada paso, reportar cifras (filas de entrada
  y salida, descartes y motivo) antes de seguir.
- No inventar resultados ni cifras. Si algo no se puede verificar, decirlo.
