"""Captura el dashboard pantalla a pantalla, para revisar el maquetado.

Streamlit se hidrata por websocket, así que una captura ingenua sale con el esqueleto
de carga. Aquí se espera a que aparezca contenido real antes de fotografiar.

    uv run python -m scripts.revisar_dashboard              # todo
    uv run python -m scripts.revisar_dashboard presentacion # solo la presentación

Las capturas van al directorio temporal, no al repositorio: son para mirarlas, no para
versionarlas.
"""

import subprocess
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import RAIZ  # noqa: E402

PUERTO = 8599
URL = f"http://localhost:{PUERTO}"
DESTINO = Path(tempfile.gettempdir()) / "revision-dashboard"

ANCHO, ALTO = 1600, 2400
ESPERA_CARGA = 25_000
ESPERA_RENDER = 1800

SECCIONES = ("Presentación", "Resumen", "Temas", "Tópicos",
             "Contraste con el diccionario", "Explorador")


def _levantar():
    proceso = subprocess.Popen(
        [sys.executable, "-m", "streamlit", "run", str(RAIZ / "app" / "main.py"),
         "--server.port", str(PUERTO), "--server.headless", "true",
         "--browser.gatherUsageStats", "false"],
        cwd=RAIZ, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    import urllib.error
    import urllib.request

    for _ in range(40):
        time.sleep(1)
        try:
            urllib.request.urlopen(f"{URL}/_stcore/health", timeout=2)
            return proceso
        except (urllib.error.URLError, OSError):
            continue
    proceso.terminate()
    raise RuntimeError("el dashboard no arrancó")


def _esperar_contenido(pagina) -> None:
    """Hasta que Streamlit termine de ejecutar y de pintar.

    No basta con que desaparezca el esqueleto de carga: al cambiar de sección
    Streamlit no lo muestra, y una captura tomada a media ejecución sale con el
    contenido de la sección anterior debajo del encabezado de la nueva. El indicador
    de estado —el botón «Stop» de la barra superior— es el que dice si sigue corriendo.
    """
    pagina.wait_for_selector("[data-testid='stAppViewContainer']", timeout=ESPERA_CARGA)
    pagina.wait_for_function(
        "() => document.querySelectorAll('[data-testid=\"stSkeleton\"]').length === 0",
        timeout=ESPERA_CARGA,
    )
    pagina.wait_for_function(
        "() => document.querySelectorAll('[data-testid=\"stStatusWidget\"]').length === 0",
        timeout=ESPERA_CARGA,
    )
    pagina.wait_for_timeout(ESPERA_RENDER)


def _errores_de_consola(mensajes) -> list[str]:
    return [m for m in mensajes if "favicon" not in m.lower()]


def capturar(solo: str = "") -> None:
    from playwright.sync_api import sync_playwright

    DESTINO.mkdir(parents=True, exist_ok=True)
    for viejo in DESTINO.glob("*.png"):
        viejo.unlink()

    servidor = _levantar()
    try:
        with sync_playwright() as play:
            navegador = play.chromium.launch()
            pagina = navegador.new_page(viewport={"width": ANCHO, "height": ALTO})
            mensajes: list[str] = []
            pagina.on("console", lambda m: mensajes.append(f"{m.type}: {m.text}")
                      if m.type == "error" else None)
            pagina.on("pageerror", lambda e: mensajes.append(f"pageerror: {e}"))

            pagina.goto(URL, wait_until="networkidle")
            _esperar_contenido(pagina)

            if not solo or solo == "presentacion":
                _capturar_presentacion(pagina)
            if not solo or solo == "secciones":
                _capturar_secciones(pagina)

            errores = _errores_de_consola(mensajes)
            print(f"\nerrores de consola: {len(errores)}")
            for error in errores[:5]:
                print(f"  {error[:160]}")
            navegador.close()
    finally:
        servidor.terminate()
        servidor.wait(timeout=10)

    print(f"\ncapturas en {DESTINO}")


def _elegir_seccion(pagina, nombre: str) -> None:
    pagina.get_by_test_id("stSidebar").get_by_text(nombre, exact=True).click()
    _esperar_contenido(pagina)


def _capturar_presentacion(pagina) -> None:
    from app.presentacion import TITULOS

    _elegir_seccion(pagina, "Presentación")
    for numero, titulo in enumerate(TITULOS, start=1):
        archivo = DESTINO / f"pres_{numero:02d}_{titulo.split()[0].lower()}.png"
        pagina.screenshot(path=str(archivo), full_page=True)
        print(f"  {archivo.name:<34} {archivo.stat().st_size // 1024:>4} KB")
        if numero < len(TITULOS):
            pagina.get_by_role("button", name="Siguiente ▶").click()
            _esperar_contenido(pagina)


def _capturar_secciones(pagina) -> None:
    for nombre in SECCIONES[1:]:
        _elegir_seccion(pagina, nombre)
        archivo = DESTINO / f"sec_{nombre.split()[0].lower()}.png"
        pagina.screenshot(path=str(archivo), full_page=True)
        print(f"  {archivo.name:<34} {archivo.stat().st_size // 1024:>4} KB")


if __name__ == "__main__":
    capturar(sys.argv[1] if len(sys.argv) > 1 else "")
