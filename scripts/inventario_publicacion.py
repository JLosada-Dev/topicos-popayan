"""Muestra qué quedaría incluido si el repositorio se publicara.

No publica nada: solo lista lo que git incluiría y lo que dejaría fuera, con el tamaño
de cada bloque, para poder decidir con la información delante.
"""

import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import RAIZ  # noqa: E402


def archivos_incluidos() -> list[Path]:
    """Lo que git versionaría: lo ya seguido más lo nuevo no ignorado."""
    seguidos = subprocess.run(
        ["git", "ls-files"], cwd=RAIZ, capture_output=True, text=True, check=True
    ).stdout.split()
    nuevos = subprocess.run(
        ["git", "ls-files", "--others", "--exclude-standard"],
        cwd=RAIZ, capture_output=True, text=True, check=True,
    ).stdout.split()
    return sorted({Path(p) for p in seguidos + nuevos})


def archivos_ignorados() -> list[Path]:
    salida = subprocess.run(
        ["git", "status", "--porcelain", "--ignored"],
        cwd=RAIZ, capture_output=True, text=True, check=True,
    ).stdout.splitlines()
    return [Path(l[3:]) for l in salida if l.startswith("!!")]


def tamano(ruta: Path) -> int:
    completa = RAIZ / ruta
    if completa.is_dir():
        return sum(f.stat().st_size for f in completa.rglob("*") if f.is_file())
    return completa.stat().st_size if completa.exists() else 0


def por_bloque(rutas: list[Path]) -> dict:
    bloques: dict[str, list] = {}
    for ruta in rutas:
        clave = ruta.parts[0] if len(ruta.parts) > 1 else "(raíz)"
        bloques.setdefault(clave, []).append(ruta)
    return bloques


def mostrar(titulo: str, rutas: list[Path]) -> int:
    print(f"\n{titulo}")
    print("-" * 66)
    total = 0
    for bloque, archivos in sorted(por_bloque(rutas).items()):
        bytes_bloque = sum(tamano(a) for a in archivos)
        total += bytes_bloque
        print(f"  {bloque + '/':<22} {len(archivos):>4} archivos  "
              f"{bytes_bloque / 1024 / 1024:>7.2f} MB")
    print(f"  {'TOTAL':<22} {len(rutas):>4} archivos  {total / 1024 / 1024:>7.2f} MB")
    return total


def main() -> None:
    incluidos = archivos_incluidos()
    mostrar("SE PUBLICARÍA", incluidos)
    mostrar("QUEDA FUERA (.gitignore)", archivos_ignorados())

    print("\nArchivos de más de 1 MB")
    print("-" * 66)
    grandes = sorted(((tamano(r), r) for r in incluidos), reverse=True)[:8]
    for bytes_archivo, ruta in grandes:
        if bytes_archivo > 1024 * 1024:
            print(f"  {bytes_archivo / 1024 / 1024:>7.2f} MB  {ruta}")

    print("\nComprobaciones de seguridad")
    print("-" * 66)
    patrones = {
        "rutas personales": r"/Users/[a-z]",
        "credenciales": r"(api[_-]?key|secret|passwd|password)\s*=",
        "correos": r"[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}",
    }
    for etiqueta, patron in patrones.items():
        resultado = subprocess.run(
            ["git", "grep", "-l", "-i", "-E", patron, "--", ".", ":!docs/bitacora.md"],
            cwd=RAIZ, capture_output=True, text=True,
        )
        encontrados = [l for l in resultado.stdout.splitlines() if l]
        estado = "limpio" if not encontrados else f"revisar: {encontrados[:3]}"
        print(f"  {etiqueta:<20} {estado}")


if __name__ == "__main__":
    main()
