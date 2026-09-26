"""Rutas y constantes compartidas del proyecto."""

import os
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent

# Proyecto previo sobre el mismo corpus (capitulo de libro): SOLO LECTURA.
# Nunca escribir, mover ni borrar nada bajo esta ruta.
#
# No es publico, asi que la ruta depende de cada maquina: se toma de la variable de
# entorno REPUTACION_POPAYAN y, si no esta, del sitio donde suele clonarse. Solo hace
# falta para regenerar el corpus desde cero; `dataset/` y `data/processed/` ya traen
# todo lo que se necesita para reproducir el analisis.
ORIGEN = Path(
    os.environ.get("REPUTACION_POPAYAN", Path.home() / "dev" / "fup" / "reputacion-popayan")
)

CORPUS = ORIGEN / "data" / "raw" / "corpus_final.csv"
MARCO_MUESTRAL = ORIGEN / "data" / "raw" / "marco_muestral_final.csv"
IDIOMA_RESENAS = ORIGEN / "data" / "interim" / "idioma_resenas.csv"
DIMENSIONES_APTAS_ES = ORIGEN / "data" / "interim" / "dimensiones_aptas_es.csv"
SENTIMIENTO_FRAGMENTOS = ORIGEN / "data" / "interim" / "sentimiento_fragmentos.csv"
DICCIONARIO_DIMENSIONES = ORIGEN / "diccionario" / "dimensiones.csv"

# Orden estable para el inventario y el manifiesto
ARCHIVOS_ORIGEN = (
    CORPUS,
    MARCO_MUESTRAL,
    IDIOMA_RESENAS,
    DIMENSIONES_APTAS_ES,
    SENTIMIENTO_FRAGMENTOS,
    DICCIONARIO_DIMENSIONES,
)

DATOS_EXTERNOS = RAIZ / "data" / "external"
DATOS_INTERIM = RAIZ / "data" / "interim"
DATOS_PROCESADOS = RAIZ / "data" / "processed"
FIGURAS = RAIZ / "figuras"
BITACORA = RAIZ / "docs" / "bitacora.md"

MANIFIESTO = DATOS_EXTERNOS / "manifiesto.csv"

# Dashboard desplegado en Streamlit Community Cloud, para quien revise sin instalar nada
URL_DASHBOARD = "https://topicos-popayan.streamlit.app"

# Dimensiones definidas a priori, en el orden del diccionario del original
DIMENSIONES = ("ambiente", "comida", "espera", "patrimonio", "precio", "servicio")

# Largo minimo de resena para entrar al corpus, ya aplicado por el original
LARGO_MINIMO_RESENA = 50

SEMILLA = 42
