# topicos-popayan

Trabajo final de Text & Web Analytics (Especialización en Data Analytics para Marketing
Digital, FUP). Identifica los temas emergentes en reseñas de Google Maps de
establecimientos gastronómicos de Popayán mediante modelado de tópicos, y los contrasta
con seis dimensiones definidas a priori: comida, servicio, precio, ambiente, tiempo de
espera y patrimonio.

**Resultado:** 5.913 fragmentos de 2.430 reseñas, 41 tópicos agrupados en 14 temas,
AMI de 0,406 contra las dimensiones a priori. Las cifras y su justificación están en
`docs/bitacora.md`.

## Entorno

El proyecto usa **uv exclusivamente**. Python 3.12.

```bash
uv sync                    # instala dependencias desde uv.lock
uv run pytest              # pruebas
```

Para los notebooks, registra el kernel del entorno una sola vez:

```bash
uv run python -m ipykernel install --user --name topicos-popayan
```

## Estructura

```
src/          código reutilizable
scripts/      scripts puntuales que producen los artefactos de data/processed/
app/          dashboard de Streamlit
notebooks/    notebooks locales
  colab/      versiones equivalentes para Google Colab
data/
  external/   manifiesto de lo leído del proyecto original
  processed/  fragmentos, embeddings, modelo, tablas de resultados
figuras/      figuras del informe en PNG y PDF a 300 dpi
docs/         bitácora, evidencia por tópico, decisiones metodológicas
  notebooks_html/  los cuatro notebooks en HTML, con sus salidas, para anexar al informe
tests/        pytest
```

El corpus proviene de un proyecto previo, `reputacion-popayan`, que es **solo lectura**.
Cada archivo leído de allí queda registrado en `data/external/manifiesto.csv` con su
número de filas y su hash SHA-256.

## Notebooks

Cuatro, uno por etapa. Cada uno abre enunciando el objetivo específico que cubre y
cierra con sus hallazgos.

| Notebook | Cubre |
|---|---|
| `00_preparacion` | Del corpus heredado a los fragmentos. Embudo y validación de las etiquetas por fragmento. |
| `01_caracterizacion` | **Objetivo 1.** Composición, calidad, distribución por calificación, establecimiento y zona. |
| `02_topicos` | **Objetivo 2.** Embeddings, BERTopic, los 41 tópicos, los 14 temas y el análisis de sensibilidad. |
| `03_evaluacion` | **Objetivo 3.** Coherencia, tabla cruzada, AMI, relación con la calificación, temas transversales y limitaciones. |

**Los notebooks no recalculan lo costoso.** Leen de `data/processed/` los resultados que
producen los scripts, de modo que corren de arriba abajo en segundos. Si esa carpeta no
existe, hay que generarla primero:

```bash
uv run python -m scripts.inventario            # manifiesto de lo heredado
uv run python -m scripts.construir_fragmentos  # fragmentos.csv
uv run python -m scripts.entrenar_modelo       # modelo y asignaciones
uv run python -m scripts.tabla_temas           # temas consolidados
uv run python -m scripts.contraste_dimensiones # tabla cruzada, AMI y dispersión
uv run python -m scripts.temas_baja_masa       # temas transversales
uv run python -m scripts.persistir_analisis    # coherencia, cohesión, sensibilidad
uv run python -m scripts.generar_figuras       # figuras/
uv run python -m scripts.evidencia_topicos     # docs/evidencia_topicos.md
uv run python -m scripts.construir_tfidf       # matriz TF-IDF del explorador
```

Los notebooks se generan desde una sola fuente, para que la versión local y la de Colab
no puedan divergir:

```bash
uv run python -m scripts.generar_notebooks
```

### Versión HTML, para anexar al informe

`docs/notebooks_html/` tiene los cuatro notebooks exportados **con sus salidas ya
ejecutadas**: tablas, cifras y figuras. Se abren con doble clic en cualquier navegador y
**no requieren instalar nada, ejecutar nada ni tener conexión** — las figuras van
incrustadas en el propio archivo y no hay ninguna referencia externa.

| Archivo | Tamaño |
|---|---:|
| `00_preparacion.html` | 322 KB |
| `01_caracterizacion.html` | 518 KB |
| `02_topicos.html` | 450 KB |
| `03_evaluacion.html` | 1,0 MB |

Para regenerarlos después de cambiar un notebook o los datos:

```bash
uv run python -m scripts.exportar_notebooks
```

El script vuelve a ejecutar cada notebook antes de exportarlo, de modo que lo que se
anexa corresponde siempre al estado actual de `data/processed/`.

### Ejecutar en local

Abre el notebook y selecciona el kernel **topicos-popayan (uv)**. La primera celda
resuelve la raíz del proyecto, tanto si abres desde la raíz como desde `notebooks/`.

### Ejecutar en Google Colab

Las versiones de `notebooks/colab/` tienen el mismo contenido; solo cambian las dos
primeras celdas. Necesitan que el proyecto viaje con su carpeta `data/processed/`,
porque no recalculan nada.

**Opción A, con Google Drive (recomendada).** Sube la carpeta del proyecto a tu Drive,
en `MyDrive/topicos-popayan`, y sube el notebook a Colab. Al ejecutar la segunda celda,
Colab pedirá autorización para montar Drive y el proyecto se detectará solo.

Si lo guardaste en otra ruta, cambia esta línea de la segunda celda:

```python
CARPETA_EN_DRIVE = "MyDrive/topicos-popayan"
```

**Opción B, subiendo un zip.** Si no montas Drive o el proyecto no está allí, la celda
ofrece un diálogo de subida. Comprime la carpeta del proyecto y súbela cuando lo pida:

```bash
zip -r topicos-popayan.zip src data/processed figuras -x '*__pycache__*'
```

El zip debe contener `src/` y `data/processed/` juntos; la celda verifica que así sea y
falla con un mensaje claro si no.

**Qué hace cada celda del preámbulo:**

1. **Dependencias.** Instala con `pip` solo si detecta Colab. En local no hace nada,
   porque el entorno de uv ya las tiene.
2. **Acceso a los datos.** Intenta Drive, luego la subida manual, y si no está en Colab
   usa la carpeta del repositorio. Deja `RAIZ` apuntando al proyecto y lo añade a
   `sys.path`.
3. **Comprobación.** Verifica que `data/processed/` tenga los archivos que el notebook
   va a leer, y lo dice antes de que falle una celda más abajo.

Los notebooks de Colab se pueden ejecutar también en local sin cambios: la detección de
entorno cae en la rama local. Es como se verifican antes de publicarlos.

## Dashboard

Para presentar los resultados. Cuatro secciones: resumen, temas, tópicos y contraste con
el diccionario.

```bash
uv run streamlit run app/main.py
```

Se abre en `http://localhost:8501`. **Solo lee de `data/processed/`**: no recalcula nada
ni carga el modelo de BERTopic, así que arranca en segundos y no necesita GPU ni
descargar modelos. Si falta algún archivo, lo dice al abrir en vez de fallar a media
navegación.

| Sección | Qué muestra |
|---|---|
| **Resumen** | El embudo del corpus, cuántos tópicos y temas salieron, el AMI y los fragmentos sin asignar, con las figuras del embudo y de distribución por tipo. |
| **Temas** | Tabla ordenable de los 14 temas. Al elegir uno: sus tópicos, términos, calificación media, % de 1-2★ y fragmentos de ejemplo. |
| **Tópicos** | Selector de tópico con sus 10 términos, tamaño, calificación, concentración por establecimiento, dimensión dominante y cinco fragmentos completos. |
| **Contraste** | Mapa de calor tópico por dimensión, el AMI con su línea base por permutación, y en cuántos tópicos se reparte cada dimensión. |
| **Explorador** | Buscador de fragmentos por consulta libre, con dos métodos comparables lado a lado. |

Cada indicador lleva una línea que explica qué significa, para que se entienda sin
conocer el detalle técnico.

### El explorador

Busca los fragmentos más parecidos a una consulta libre, con dos representaciones:

- **TF-IDF** compara palabras. La matriz está precalculada
  (`scripts/construir_tfidf.py`); el panel solo vectoriza la consulta. Responde en
  **3-30 ms** y no carga nada pesado.
- **Embeddings** compara significado, reutilizando los ya calculados. El modelo se
  carga **de forma diferida y cacheada**, solo si eliges ese método: la primera
  búsqueda de la sesión tarda unos **10 s** y las siguientes **15-500 ms**. El arranque
  del panel no se ve afectado.

La opción «Comparar los dos» muestra ambos rankings lado a lado y cuenta cuántos
resultados comparten, que es la forma más directa de ver en qué se diferencian.

## Documentación

| Archivo | Contenido |
|---|---|
| `docs/bitacora.md` | Cada decisión y resultado con fecha, motivo y cifras. |
| `docs/decisiones_metodologicas.md` | Tabla para el informe: decisión, valor, alternativa y por qué se descartó. |
| `docs/evidencia_topicos.md` | Los 41 tópicos con términos, cifras y cinco fragmentos cada uno. |
| `CLAUDE.md` | Convenciones del proyecto y decisiones cerradas. |
