import pandas as pd
import pytest

from app import datos
from src.config import DIMENSIONES


def test_no_faltan_archivos():
    assert datos.faltantes() == []


def test_topicos_trae_lo_que_muestra_el_panel():
    tabla = datos.topicos()
    assert len(tabla) == 41
    for columna in ("terminos", "local_top", "pct_local_top", "n_locales",
                    "dimension_dominante", "rating", "polaridad", "tipo"):
        assert columna in tabla.columns, columna
    # El panel formatea estos campos sin comprobar nulos
    assert not tabla[["terminos", "local_top", "rating", "n"]].isna().any().any()


def test_todo_topico_tiene_fragmentos():
    marco = datos.fragmentos()
    for identificador in datos.topicos()["topico_id"]:
        assert (marco["topico"] == identificador).any(), identificador


def test_temas_cubren_todos_los_topicos():
    temas = datos.temas()
    assert len(temas) == 14
    assert int(temas["n_topicos"].sum()) == len(datos.topicos())
    assert int(temas["fragmentos"].sum()) == int((datos.fragmentos()["topico"] != datos.ATIPICO).sum())


def test_cada_tema_de_un_topico_existe_en_la_tabla_de_temas():
    assert set(datos.topicos()["tema"]) == set(datos.temas()["tema"])


def test_ami_trae_su_linea_base():
    tabla = datos.ami()
    fila = tabla.iloc[0]
    assert 0 < fila["ami"] < 1
    assert abs(fila["nulo"]) < 0.01          # el azar debe rondar cero
    assert fila["exceso"] == pytest.approx(fila["ami"] - fila["nulo"], abs=1e-3)


def test_dispersion_cubre_las_seis_dimensiones():
    assert set(datos.dispersion()["dimension"]) == set(DIMENSIONES)


def test_cruzada_tiene_una_fila_por_topico():
    cruzada = datos.cruzada()
    assert set(cruzada["topico"]) == set(datos.topicos()["topico_id"])
    for dimension in DIMENSIONES:
        assert cruzada[dimension].between(0, 100).all(), dimension


def test_indicadores_de_calidad_disponibles():
    for nombre in ("c_v", "c_npmi", "diversidad_top10"):
        assert isinstance(datos.indicador(nombre), float)


def test_resumen_de_atipicos():
    resumen = datos.resumen_atipicos()
    assert resumen["n"] > 0
    assert 0 < resumen["pct"] < 100
    # El hallazgo que el panel afirma: los sin asignar son mas criticos que el corpus
    assert resumen["rating"] < datos.fragmentos()["rating"].mean()


def test_nombre_largo_incluye_subtema_solo_si_existe():
    tabla = datos.topicos().set_index("topico_id")
    con_subtema = tabla.loc[15]
    sin_subtema = tabla.loc[0]
    assert datos.nombre_largo({**con_subtema, "topico_id": 15}) == "T15 · comida / pizza"
    assert datos.nombre_largo({**sin_subtema, "topico_id": 0}) == "T0 · espera"


def test_las_figuras_que_muestra_existen():
    for nombre in ("04_embudo_corpus.png", "01_distribucion_por_tipo.png",
                   "03_mapa_topico_dimension.png"):
        assert datos.figura(nombre).exists(), nombre


def test_el_dashboard_no_carga_matplotlib(tmp_path):
    """Matplotlib no está en `requirements.txt`: si el dashboard lo importara, el
    despliegue en Streamlit Community Cloud fallaría. Va en un subproceso porque otra
    prueba pudo haberlo cargado ya."""
    import subprocess
    import sys
    from pathlib import Path as Ruta

    guion = tmp_path / "comprobar.py"
    guion.write_text(
        "import sys\n"
        f"sys.path.insert(0, {str(Ruta.cwd())!r})\n"
        "import streamlit as st\n"
        "st.radio = lambda l, o, **k: list(o)[0]\n"
        "st.selectbox = lambda l, o, **k: list(o)[0]\n"
        "st.text_input = lambda l, **k: ''\n"
        "st.slider = lambda l, a, b, c, **k: 5\n"
        "st.button = lambda *a, **k: False\n"
        "from app import secciones\n"
        "for f in (secciones.resumen, secciones.temas, secciones.topicos,\n"
        "          secciones.contraste, secciones.explorador):\n"
        "    f()\n"
        "print('MATPLOTLIB:' + str('matplotlib' in sys.modules))\n",
        encoding="utf-8",
    )
    salida = subprocess.run([sys.executable, str(guion)], capture_output=True, text=True)
    linea = next(l for l in salida.stdout.splitlines() if l.startswith("MATPLOTLIB:"))
    assert linea == "MATPLOTLIB:False", "el dashboard importó matplotlib"


def test_nombres_de_tema_legibles():
    from src.etiquetas import legible

    assert legible("ocasion de consumo") == "ocasión de consumo"
    assert legible("comida") == "comida"          # sin cambio cuando no hace falta


def test_las_once_pantallas_de_presentacion_existen():
    from app import presentacion

    assert len(presentacion.TITULOS) == 11


def test_la_navegacion_no_se_sale_de_rango():
    import streamlit as st

    from app import presentacion

    st.session_state = {}
    for pedido, esperado in [(-5, 0), (0, 0), (10, 10), (99, 10)]:
        presentacion._ir_a(pedido)
        assert st.session_state[presentacion.CLAVE_PANTALLA] == esperado


def test_el_acceso_al_explorador_precarga_la_consulta():
    import streamlit as st

    from app import busqueda, presentacion

    st.session_state = {}
    presentacion._al_explorador()
    assert st.session_state["seccion"] == "Explorador"
    assert st.session_state["consulta"] == presentacion.CONSULTA_DEMO
    # Y esa consulta tiene que devolver algo, o la demostracion en vivo falla
    tabla, _, _ = busqueda.buscar_tfidf(presentacion.CONSULTA_DEMO, 3)
    assert not tabla.empty


def test_la_presentacion_usa_las_figuras_existentes():
    from app import datos, presentacion

    fuente = (datos.RAIZ / "app" / "presentacion.py").read_text(encoding="utf-8")
    for figura in ("04_embudo_corpus", "03_mapa_topico_dimension",
                   "01_distribucion_por_tipo", "02_temas_por_rating"):
        assert figura in fuente, figura
        assert datos.figura(f"{figura}.png").exists()
