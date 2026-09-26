"""Exporta la presentación como imágenes y como PDF, listo para proyectar o imprimir.

Captura **solo el área de contenido**: sin la barra lateral del dashboard y sin los
controles de anterior y siguiente, para que parezca una presentación y no una captura
de pantalla.

    uv run python -m scripts.exportar_presentacion

Produce `entrega/3_presentacion/capturas/NN_nombre.png`, una por pantalla, y
`entrega/3_presentacion/presentacion.pdf` con una pantalla por página.
"""

import subprocess
import sys
import time
import unicodedata
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import RAIZ  # noqa: E402

PUERTO = 8596
URL = f"http://localhost:{PUERTO}"

DESTINO = RAIZ / "entrega" / "3_presentacion"
CAPTURAS = DESTINO / "capturas"
PDF = DESTINO / "presentacion.pdf"

# La ventana va alta a propósito: con 900 px de alto el contenedor de las imágenes
# recorta el mapa de calor. Cada pantalla se captura completa y después se compone
# sobre un lienzo 16:9 uniforme.
ANCHO, ALTO = 1600, 2000
ESCALA = 2

# Lienzo final de cada página, 16:9 a 3200 px: proyecta bien y da 300 ppp en A4 apaisado
LIENZO = (3200, 1800)
ESPERA = 30_000
ESPERA_PINTADO = 1500

CONTENIDO = "[data-testid='stMainBlockContainer']"

# Se oculta justo antes de cada captura y se restaura para poder seguir navegando
OCULTAR = """
[data-testid='stSidebar'], [data-testid='stToolbar'], [data-testid='stHeader'] {
    display: none !important;
}
[data-testid='stMain'] { left: 0 !important; width: 100vw !important; }
.ocultar-navegacion { display: none !important; }
"""

# La fila de botones y el separador que la precede llevan una marca desde JS, porque no
# tienen un identificador propio en el DOM de Streamlit
MARCAR_NAVEGACION = """
() => {
  const boton = [...document.querySelectorAll('button')]
      .find(b => b.innerText.includes('Siguiente'));
  if (!boton) return false;
  const fila = boton.closest("[data-testid='stHorizontalBlock']");
  if (!fila) return false;
  fila.classList.add('ocultar-navegacion');
  // Solo se oculta el hermano anterior si de verdad es un separador: antes se ocultaba
  // cualquiera, y en la pantalla 7 se llevaba por delante el bloque de demostración
  const previo = fila.previousElementSibling;
  if (previo && previo.querySelector('hr')) {
      previo.classList.add('ocultar-navegacion');
  }
  return true;
}
"""

DESMARCAR = """
() => document.querySelectorAll('.ocultar-navegacion')
    .forEach(e => e.classList.remove('ocultar-navegacion'))
"""


def _sin_tildes(texto: str) -> str:
    plano = unicodedata.normalize("NFKD", texto.lower())
    limpio = "".join(c for c in plano if not unicodedata.combining(c))
    return "".join(c if c.isalnum() else "_" for c in limpio).strip("_")


def _levantar():
    proceso = subprocess.Popen(
        [sys.executable, "-m", "streamlit", "run", str(RAIZ / "app" / "main.py"),
         "--server.port", str(PUERTO), "--server.headless", "true",
         "--browser.gatherUsageStats", "false"],
        cwd=RAIZ, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    for _ in range(40):
        time.sleep(1)
        try:
            urllib.request.urlopen(f"{URL}/_stcore/health", timeout=2)
            return proceso
        except (urllib.error.URLError, OSError):
            continue
    proceso.terminate()
    raise RuntimeError("el dashboard no arrancó")


def _esperar(pagina) -> None:
    pagina.wait_for_selector("[data-testid='stAppViewContainer']", timeout=ESPERA)
    for prueba in ("stSkeleton", "stStatusWidget"):
        pagina.wait_for_function(
            f"() => document.querySelectorAll('[data-testid=\\'{prueba}\\']').length === 0",
            timeout=ESPERA,
        )
    pagina.wait_for_timeout(ESPERA_PINTADO)


def _capturar_pantalla(pagina, ruta: Path) -> None:
    """Oculta la interfaz, fotografía solo el contenido y vuelve a mostrarla."""
    pagina.evaluate(MARCAR_NAVEGACION)
    estilo = pagina.add_style_tag(content=OCULTAR)
    pagina.wait_for_timeout(400)
    pagina.locator(CONTENIDO).first.screenshot(path=str(ruta))
    pagina.evaluate("(e) => e.remove()", estilo)
    pagina.evaluate(DESMARCAR)
    pagina.wait_for_timeout(200)


def _recortar_blanco(imagen, margen: int = 60):
    """Quita el blanco sobrante del final de la captura.

    Streamlit deja el contenedor con la altura de la ventana, así que cada pantalla
    arrastra una franja vacía. Si no se recorta, al encajarla en 16:9 el contenido
    queda mucho más pequeño de lo necesario.
    """
    import numpy as np

    gris = np.asarray(imagen.convert("L"), dtype=int)
    fondo_claro = gris > 245
    filas_con_algo = np.where(~fondo_claro.all(axis=1))[0]
    if len(filas_con_algo) == 0:
        return imagen
    fin = min(imagen.height, int(filas_con_algo[-1]) + margen)
    inicio = max(0, int(filas_con_algo[0]) - margen)
    return imagen.crop((0, inicio, imagen.width, fin))


def _a_lienzo(imagen, fondo=(252, 252, 251)):
    """Encaja la captura en un lienzo 16:9 uniforme, centrada y sin deformarla.

    Sin esto cada página del PDF tendría el alto de su propio contenido —de 1.500 a
    2.800 px— y al proyectarlo cada pantalla saldría a una escala distinta.
    """
    from PIL import Image

    ancho, alto = LIENZO
    escala = min(ancho / imagen.width, alto / imagen.height)
    nuevo = imagen.resize(
        (max(1, int(imagen.width * escala)), max(1, int(imagen.height * escala))),
        Image.LANCZOS,
    )
    lienzo = Image.new("RGB", LIENZO, fondo)
    lienzo.paste(nuevo, ((ancho - nuevo.width) // 2, (alto - nuevo.height) // 2))
    return lienzo


def _a_pdf(imagenes: list[Path]) -> None:
    """Un PDF de una sola pasada, una pantalla por página, en orden y todas iguales."""
    from PIL import Image

    paginas = [_a_lienzo(_recortar_blanco(Image.open(r).convert("RGB")))
               for r in imagenes]
    paginas[0].save(PDF, save_all=True, append_images=paginas[1:], resolution=200.0)


def main() -> None:
    from app.presentacion import TITULOS

    from playwright.sync_api import sync_playwright

    CAPTURAS.mkdir(parents=True, exist_ok=True)
    for viejo in CAPTURAS.glob("*.png"):
        viejo.unlink()

    servidor = _levantar()
    imagenes: list[Path] = []
    try:
        with sync_playwright() as play:
            navegador = play.chromium.launch()
            pagina = navegador.new_page(
                viewport={"width": ANCHO, "height": ALTO}, device_scale_factor=ESCALA
            )
            pagina.goto(URL, wait_until="networkidle")
            _esperar(pagina)
            pagina.get_by_test_id("stSidebar").get_by_text("Presentación", exact=True).click()
            _esperar(pagina)

            for numero, titulo in enumerate(TITULOS, start=1):
                ruta = CAPTURAS / f"{numero:02d}_{_sin_tildes(titulo)}.png"
                _capturar_pantalla(pagina, ruta)
                imagenes.append(ruta)
                print(f"  {ruta.name:<32} {ruta.stat().st_size // 1024:>5} KB")
                if numero < len(TITULOS):
                    pagina.get_by_role("button", name="Siguiente ▶").click()
                    _esperar(pagina)
            navegador.close()
    finally:
        servidor.terminate()
        servidor.wait(timeout=10)

    _a_pdf(imagenes)
    print(f"\n  {PDF.name:<32} {PDF.stat().st_size // 1024:>5} KB "
          f"({len(imagenes)} páginas)")


if __name__ == "__main__":
    main()
