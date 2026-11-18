"""Punto de entrada de PlanifiCPU.

Uso:
    python main.py                      abre la interfaz grafica
    python main.py --consola [CSV] ...  simula en la terminal (ver --help)
    python main.py --diagnostico        revisa el entorno y corre una autoprueba
    python main.py --version
"""

from __future__ import annotations

import argparse
import os
import sys


def _argumentos(argv: list[str] | None = None) -> argparse.Namespace:
    from planificpu import __version__
    from planificpu.consola import ALIAS

    p = argparse.ArgumentParser(
        prog="PlanifiCPU",
        description="Simulador de algoritmos de planificación de procesos en la CPU. "
                    "Sin opciones abre la interfaz gráfica.")
    p.add_argument("--version", action="version", version=f"PlanifiCPU {__version__}")
    p.add_argument("--diagnostico", action="store_true",
                   help="revisa Python, Tkinter, Matplotlib, SQLite y el motor, y termina")
    p.add_argument("--consola", action="store_true",
                   help="simula en la terminal en lugar de abrir la ventana")
    p.add_argument("csv", nargs="?",
                   help="escenario CSV para --consola (por defecto, el ejemplo de la ficha)")
    p.add_argument("-a", "--algoritmo", choices=sorted(ALIAS), default="fcfs",
                   help="algoritmo para --consola (srtf = SJF expropiativo)")
    p.add_argument("-q", "--quantum", type=int, default=2,
                   help="quantum de Round Robin (por defecto 2)")
    p.add_argument("-e", "--expropiativo", action="store_true",
                   help="modo expropiativo para SJF y Prioridad")
    p.add_argument("--comparar", action="store_true", help="compara los 4 algoritmos")
    p.add_argument("--traza", action="store_true", help="muestra la simulación paso a paso")
    p.add_argument("--exportar", metavar="RUTA.csv", help="exporta los resultados a CSV")
    args = p.parse_args(argv)
    if args.csv and not args.consola:
        p.error("el archivo CSV solo se usa con --consola")
    return args


def main(argv: list[str] | None = None) -> int:
    # en el .exe sin consola stdout/stderr no existen
    if sys.stdout is None:
        sys.stdout = open(os.devnull, "w", encoding="utf-8")
    if sys.stderr is None:
        sys.stderr = open(os.devnull, "w", encoding="utf-8")
    for flujo in (sys.stdout, sys.stderr):
        if hasattr(flujo, "reconfigure"):
            flujo.reconfigure(errors="replace")

    args = _argumentos(argv)

    if args.diagnostico:
        from planificpu import diagnostico
        return diagnostico.ejecutar(sys.stdout)

    if args.consola:
        from planificpu import consola
        from planificpu.modelos import ErrorValidacion
        try:
            return consola.ejecutar(args, sys.stdout)
        except FileNotFoundError as e:
            print(f"Error: no se encuentra el archivo {e.filename}", file=sys.stderr)
            return 2
        except (ErrorValidacion, ValueError, OSError) as e:
            print(f"Error: {e}", file=sys.stderr)
            return 2

    if sys.platform == "win32":
        try:  # texto nitido en pantallas con escalado (Windows 10/11)
            import ctypes
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except (AttributeError, OSError):
            pass
    from planificpu.gui import App
    App().mainloop()
    return 0


if __name__ == "__main__":
    sys.exit(main())
