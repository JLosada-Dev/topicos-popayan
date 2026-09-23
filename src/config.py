"""Rutas y constantes compartidas del proyecto."""

from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent

# Proyecto previo sobre el mismo corpus (capitulo de libro): SOLO LECTURA.
# Nunca escribir, mover ni borrar nada bajo esta ruta.
ORIGEN = Path("/Users/noovou/dev/fup/reputacion-popayan")

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

# Dimensiones definidas a priori, en el orden del diccionario del original
DIMENSIONES = ("ambiente", "comida", "espera", "patrimonio", "precio", "servicio")

# Largo minimo de resena para entrar al corpus, ya aplicado por el original
LARGO_MINIMO_RESENA = 50

SEMILLA = 42
