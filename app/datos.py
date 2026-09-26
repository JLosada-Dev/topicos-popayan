"""Carga de los resultados que consume el dashboard.

El dashboard **solo lee** de `data/processed/`. No recalcula nada ni carga el modelo de
BERTopic: todo lo que muestra ya está producido por los scripts de `scripts/`.
"""

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from src.config import DATOS_PROCESADOS, DIMENSIONES, FIGURAS  # noqa: E402

ATIPICO = -1

# Archivo -> si su ausencia impide arrancar
REQUERIDOS = (
    "fragmentos.csv",
    "fragmentos_topicos.csv",
    "topicos_etiquetados.csv",
    "topicos_resumen.csv",
    "temas_consolidado.csv",
    "cruzada_topico_dimension.csv",
    "ami_resultados.csv",
    "dispersion_dimensiones.csv",
    "calidad_modelo.csv",
)


def faltantes() -> list[str]:
    return [n for n in REQUERIDOS if not (DATOS_PROCESADOS / n).exists()]


@st.cache_data
def _leer(nombre: str) -> pd.DataFrame:
    return pd.read_csv(DATOS_PROCESADOS / nombre)


@st.cache_data
def fragmentos() -> pd.DataFrame:
    """Fragmentos con su tópico asignado."""
    return _leer("fragmentos.csv").merge(
        _leer("fragmentos_topicos.csv"), on=["fragmento_id", "review_id"]
    )


def topicos() -> pd.DataFrame:
    """Un tópico por fila: tema, tipo, polaridad, cifras y términos."""
    etiquetas = _leer("topicos_etiquetados.csv")
    resumen = _leer("topicos_resumen.csv").rename(columns={"topico": "topico_id"})
    columnas = ["topico_id", "terminos", "local_top", "pct_local_top",
                "n_locales", "dimension_dominante", "largo_mediano"]
    unido = etiquetas.merge(resumen[columnas], on="topico_id", how="left")
    unido["subtema"] = unido["subtema"].fillna("")
    return unido


def temas() -> pd.DataFrame:
    return _leer("temas_consolidado.csv").fillna({"subtemas": ""})


def cruzada() -> pd.DataFrame:
    return _leer("cruzada_topico_dimension.csv")


def ami() -> pd.DataFrame:
    return _leer("ami_resultados.csv")


def dispersion() -> pd.DataFrame:
    return _leer("dispersion_dimensiones.csv")


def calidad() -> pd.DataFrame:
    return _leer("calidad_modelo.csv")


def indicador(nombre: str) -> float:
    """Un valor suelto de `calidad_modelo.csv`."""
    tabla = calidad()
    return float(tabla.loc[tabla["indicador"] == nombre, "valor"].iloc[0])


def resumen_atipicos() -> dict:
    datos = fragmentos()
    sin_asignar = datos[datos["topico"] == ATIPICO]
    return {
        "n": len(sin_asignar),
        "pct": 100 * len(sin_asignar) / len(datos),
        "rating": float(sin_asignar["rating"].mean()),
        "pct_1_2": 100 * (sin_asignar["rating"] <= 2).mean(),
    }


def nombre_largo(fila) -> str:
    """Etiqueta legible de un tópico: «T4 · comida» o «T15 · comida / pizza»."""
    from src.etiquetas import legible

    subtema = fila["subtema"] if isinstance(fila["subtema"], str) else ""
    nombre = f"T{fila['topico_id']} · {legible(fila['tema'])}"
    return nombre + (f" / {legible(subtema)}" if subtema else "")


def figura(nombre: str) -> Path:
    return FIGURAS / nombre
