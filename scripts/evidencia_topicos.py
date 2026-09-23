"""Documento de evidencia por tópico, para validar los nombres a mano."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd  # noqa: E402

from src.config import DIMENSIONES, DATOS_PROCESADOS, RAIZ, SEMILLA  # noqa: E402
from src.topicos import ATIPICO, cargar_modelo_guardado  # noqa: E402

SALIDA = RAIZ / "docs" / "evidencia_topicos.md"
N_EJEMPLOS = 5
N_TERMINOS = 10


def main() -> None:
    fragmentos = pd.read_csv(DATOS_PROCESADOS / "fragmentos.csv").merge(
        pd.read_csv(DATOS_PROCESADOS / "fragmentos_topicos.csv"),
        on=["fragmento_id", "review_id"],
    )
    modelo = cargar_modelo_guardado()

    lineas = [
        "# Evidencia por tópico",
        "",
        f"Modelo congelado: {len(fragmentos)} fragmentos, "
        f"{fragmentos['topico'].nunique() - 1} tópicos, "
        f"{100 * (fragmentos['topico'] == ATIPICO).mean():.1f} % de atípicos.",
        "",
        "Los ejemplos son una muestra reproducible (`random_state=SEMILLA`), no los",
        "documentos representativos de BERTopic, para no sesgar hacia el centro del tópico.",
        "",
    ]

    orden = fragmentos["topico"].value_counts().index
    for topico in [t for t in orden if t != ATIPICO] + [ATIPICO]:
        sub = fragmentos[fragmentos["topico"] == topico]
        terminos = [x for x, _ in (modelo.get_topic(topico) or [])][:N_TERMINOS]
        locales = sub["establecimiento"].value_counts()
        tasas = {d: sub[d].mean() for d in DIMENSIONES}
        dominante = max(tasas, key=tasas.get)

        titulo = "Atípicos (-1)" if topico == ATIPICO else f"Tópico {topico}"
        lineas += [
            f"## {titulo}",
            "",
            f"- **n** {len(sub)} ({100 * len(sub) / len(fragmentos):.1f} % del corpus)",
            f"- **rating medio** {sub['rating'].mean():.2f} · "
            f"**1-2 estrellas** {100 * (sub['rating'] <= 2).mean():.1f} %",
            f"- **concentración** {100 * locales.iloc[0] / len(sub):.1f} % en "
            f"«{locales.index[0]}», sobre {sub['place_id'].nunique()} locales",
            f"- **dimensión dominante** {dominante} ({100 * tasas[dominante]:.0f} %) · "
            f"**sin dimensión** {100 * (sub['n_dim'] == 0).mean():.0f} %",
            f"- **largo mediano** {int(sub['largo_caracteres'].median())} caracteres",
            f"- **términos** {', '.join(terminos)}",
            "",
        ]
        muestra = sub.sample(min(N_EJEMPLOS, len(sub)), random_state=SEMILLA)
        for fila in muestra.itertuples(index=False):
            activas = [d for d in DIMENSIONES if getattr(fila, d)]
            lineas.append(
                f"> ({fila.rating}★, {'/'.join(activas) or 'sin dimensión'}) {fila.texto}"
            )
            lineas.append(">")
        lineas.append("")

    SALIDA.write_text("\n".join(lineas), encoding="utf-8")
    print(f"escrito {SALIDA} ({len(lineas)} líneas)")


if __name__ == "__main__":
    main()
