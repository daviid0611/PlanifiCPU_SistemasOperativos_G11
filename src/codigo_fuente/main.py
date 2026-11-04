"""Punto de entrada de PlanifiCPU.  Uso:  python main.py"""

import sys


def main() -> None:
    if sys.platform == "win32":
        try:  # texto nitido en pantallas con escalado (Windows 10/11)
            import ctypes
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except (AttributeError, OSError):
            pass
    from planificpu.gui import App
    App().mainloop()


if __name__ == "__main__":
    main()
