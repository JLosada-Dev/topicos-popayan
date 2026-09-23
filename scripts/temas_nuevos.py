"""DEPRECADO — sustituido por `scripts/temas_baja_masa.py` el 2026-09-22.

Se conserva porque la bitácora cita sus cifras en la entrada del 2026-09-22 «Estructura
de dos niveles». Su sucesor corrige dos reglas: `fri[oa]` capturaba «comida fría» como
si fuera clima, y la regla amplia de trato al personal recuperaba quejas *sobre* el
personal en vez de críticas a *cómo se le trata*. Para cifras nuevas usar el sucesor.

Rastreo de los temas emergentes de baja masa.

Cada tema se define por una expresión regular sobre el texto plegado (minúsculas,
sin tildes). Son reglas de recuperación deliberadamente estrechas: sirven para acotar
un piso de cuántos fragmentos hay, no para medir el tema con precisión.
"""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd  # noqa: E402

from src.config import DATOS_PROCESADOS, SEMILLA  # noqa: E402
from src.texto import plegar  # noqa: E402
from src.topicos import ATIPICO  # noqa: E402

REGLAS = {
    "horarios e informacion digital": (
        r"\b(?:horarios?|abren|cierran|cerrad[oa]s?|google maps|en google|"
        r"redes sociales|instagram|facebook|whatsapp|pagina web|"
        r"no contestan|no responden|no atienden el telefono)\b"
    ),
    "trato al personal": (
        r"\b(?:emplead[oa]s?|trabajador\w*|explotac\w*|explotad\w*|mal pagad\w*|"
        r"sueldos?|salarios?|contratan|despidi\w*|su personal merec\w*)\b"
    ),
    # Se separa el incidente concreto de la mencion generica de higiene, que suele ser
    # elogio («que limpieza») y no un problema de inocuidad
    "inocuidad (incidente)": (
        r"\b(?:moho|hongo|da[ñn]ad\w*|podrid\w*|descompuest\w*|vencid\w*|crud[oa]s?|"
        r"mal estado|intoxicac\w*|indigest\w*|vomit\w*|diarrea|pelo en|cabello en|"
        r"mosca|cucarach\w*|insecto|sucio|suci[ao]s?)\b"
    ),
    "inocuidad (higiene, cualquier signo)": r"\b(?:higien\w*|limpieza|aseo|pulcr\w*)\b",
    # Sin `fri[oa]` ni `calor`: capturaban «comida fria», que es temperatura del plato
    # y no del local. Solo quedan terminos inequivocos de clima o instalacion.
    "infraestructura y clima": (
        r"\b(?:llov\w*|lluvia|llueve|mojar|mojad|techo|carpa|toldo|intemperie|"
        r"ventilac\w*|aire acondicionad\w*|abanico|ventilador|gotea|goter|humedad)\b"
    ),
    "honestidad en el cobro": (
        r"\b(?:cobrar|cobrad|cobro|cobran|sobrecost|propina|devuelt|vuelto|"
        r"estaf|rob[oa]r?on?|no devolv|cuenta mal|cobraron de mas|sisas)\b"
    ),
}


def main() -> None:
    fragmentos = pd.read_csv(DATOS_PROCESADOS / "fragmentos.csv").merge(
        pd.read_csv(DATOS_PROCESADOS / "fragmentos_topicos.csv"),
        on=["fragmento_id", "review_id"],
    )
    fragmentos["plegado"] = fragmentos["texto"].map(plegar)
    total = len(fragmentos)

    for tema, patron in REGLAS.items():
        marca = fragmentos["plegado"].str.contains(patron, regex=True, na=False)
        sub = fragmentos[marca]
        atipicos = int((sub["topico"] == ATIPICO).sum())
        reparto = sub["topico"].value_counts()
        propios = reparto[reparto >= 0.30 * len(sub)]

        print(f"\n{'=' * 74}")
        print(f"{tema.upper()}  —  {len(sub)} fragmentos ({100 * len(sub) / total:.1f} % del corpus)")
        print(f"{'=' * 74}")
        print(f"  rating medio {sub['rating'].mean():.2f} · "
              f"1-2 estrellas {100 * (sub['rating'] <= 2).mean():.0f} % "
              f"(corpus: {fragmentos['rating'].mean():.2f} / "
              f"{100 * (fragmentos['rating'] <= 2).mean():.0f} %)")
        print(f"  sin dimensión del diccionario: {100 * (sub['n_dim'] == 0).mean():.0f} %")
        print(f"  atípicos: {atipicos} ({100 * atipicos / len(sub):.0f} %)")
        print(f"  disperso en {sub['topico'].nunique()} tópicos; "
              f"¿tópico propio (>=30 % del tema)? "
              f"{'sí -> T' + str(propios.index[0]) if len(propios) else 'no'}")
        print("  reparto principal: " + ", ".join(
            f"T{t}:{n} ({100 * n / len(sub):.0f}%)" for t, n in reparto.head(5).items()
        ))
        print("  ejemplos:")
        for fila in sub.sample(min(4, len(sub)), random_state=SEMILLA).itertuples(index=False):
            print(f"    ({fila.rating}★, T{fila.topico}) {fila.texto[:104]}")


if __name__ == "__main__":
    main()
