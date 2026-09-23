"""Temas emergentes de baja masa, consolidados.

Cada tema se acota con una expresión regular sobre el texto plegado. **Son reglas de
piso, no una medición exacta**: recuperan un subconjunto reconocible del tema y tienen
tanto falsos negativos (formulaciones que no usan esas palabras) como falsos positivos
(que se documentan por tema). Las cifras acotan el orden de magnitud, no lo miden.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd  # noqa: E402

from src.config import DATOS_PROCESADOS, SEMILLA  # noqa: E402
from src.texto import plegar  # noqa: E402
from src.topicos import ATIPICO  # noqa: E402

REGLAS = {
    "inocuidad": (
        r"\b(?:moho|hongo|da[ñn]ad\w*|podrid\w*|descompuest\w*|vencid\w*|crud[oa]s?|"
        r"mal estado|intoxicac\w*|indigest\w*|vomit\w*|diarrea|pelo en|cabello en|"
        r"mosca|cucarach\w*|insecto|sucio|suci[ao]s?)\b"
    ),
    "honestidad en el cobro": (
        r"\b(?:cobrar|cobrad\w*|cobro|cobran|sobrecost\w*|propina|devuelt\w*|vuelto|"
        r"estaf\w*|no devolv\w*|cuenta mal|cobraron de mas|publicidad enga[ñn]osa)\b"
    ),
    "infraestructura y clima": (
        r"\b(?:llov\w*|lluvia|llueve|mojar|mojad\w*|techo|carpa|toldo|intemperie|"
        r"ventilac\w*|aire acondicionad\w*|abanico|ventilador|gotea|goter\w*)\b"
    ),
    "horarios e informacion digital": (
        r"\b(?:horarios?|abren|cierran|cerrad[oa]s?|google maps|en google|"
        r"redes sociales|instagram|facebook|whatsapp|pagina web|"
        r"no contestan|no responden)\b"
    ),
    # Regla estrecha a proposito: la version amplia (`emplead\w*`) recuperaba quejas
    # SOBRE el personal, no criticas a COMO se le trata, que es el tema
    "trato al personal": (
        r"\b(?:explotac\w*|explotad\w*|mal pagad\w*|sueldos?|salarios?|"
        r"no les pagan|merecen un mejor|trata mal a sus|maltrata)\b"
    ),
}

FALSOS_POSITIVOS = {
    "inocuidad": "«crudo» como término de cocción; «limpio» en elogio",
    "honestidad en el cobro": "«propina» mencionada de forma neutra",
    "infraestructura y clima": "«humedad» como textura de un plato (ya excluida)",
    "horarios e informacion digital": "«cerrado» referido a un espacio cerrado",
    "trato al personal": "«sueldo» en comentarios ajenos al local",
}


def main() -> None:
    fragmentos = pd.read_csv(DATOS_PROCESADOS / "fragmentos.csv").merge(
        pd.read_csv(DATOS_PROCESADOS / "fragmentos_topicos.csv"),
        on=["fragmento_id", "review_id"],
    )
    fragmentos["plegado"] = fragmentos["texto"].map(plegar)

    filas, ejemplos = [], []
    for tema, patron in REGLAS.items():
        sub = fragmentos[fragmentos["plegado"].str.contains(patron, regex=True, na=False)]
        atipicos = int((sub["topico"] == ATIPICO).sum())
        filas.append(
            {
                "tema": tema,
                "fragmentos": len(sub),
                "pct_corpus": round(100 * len(sub) / len(fragmentos), 2),
                "resenas": sub["review_id"].nunique(),
                "rating": round(float(sub["rating"].mean()), 2),
                "pct_1_2_estrellas": round(100 * (sub["rating"] <= 2).mean(), 1),
                "pct_atipicos": round(100 * atipicos / len(sub), 1),
                "topicos_distintos": sub["topico"].nunique(),
                "pct_sin_dimension": round(100 * (sub["n_dim"] == 0).mean(), 1),
                "falsos_positivos_conocidos": FALSOS_POSITIVOS[tema],
            }
        )
        for fila in sub.sample(min(2, len(sub)), random_state=SEMILLA).itertuples(index=False):
            ejemplos.append({"tema": tema, "rating": fila.rating,
                             "topico": fila.topico, "texto": fila.texto})

    tabla = pd.DataFrame(filas).sort_values("fragmentos", ascending=False)
    tabla.to_csv(DATOS_PROCESADOS / "temas_baja_masa.csv", index=False)
    pd.DataFrame(ejemplos).to_csv(DATOS_PROCESADOS / "temas_baja_masa_ejemplos.csv", index=False)

    referencia = fragmentos["rating"].mean()
    print(f"corpus de referencia: rating {referencia:.2f}, "
          f"1-2★ {100 * (fragmentos['rating'] <= 2).mean():.0f} %, "
          f"atípicos {100 * (fragmentos['topico'] == ATIPICO).mean():.1f} %\n")
    with pd.option_context("display.width", 220, "display.max_colwidth", 44):
        print(tabla.drop(columns="falsos_positivos_conocidos").to_string(index=False))

    print("\n=== Ejemplos ===")
    for tema in REGLAS:
        print(f"\n{tema}:")
        for fila in [e for e in ejemplos if e["tema"] == tema]:
            print(f"  ({fila['rating']}★, T{fila['topico']}) {fila['texto'][:112]}")


if __name__ == "__main__":
    main()
