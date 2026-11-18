"""Diagnostico del entorno y autoprueba de PlanifiCPU.

    python src/codigo_fuente/main.py --diagnostico

Revisa el sistema operativo, la version de Python, Tkinter, Matplotlib y SQLite,
que la carpeta de la base de datos se pueda escribir, y corre el ejercicio de la
ficha tecnica con todos los algoritmos y el modo paso a paso. Devuelve 0 si todo
esta bien y 1 si algo falla, por lo que tambien sirve en GitHub Actions para
probar el ejecutable .exe.
"""

from __future__ import annotations

import os
import platform
import sqlite3
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import TextIO

from . import __version__

OK, AVISO, FALLA = "OK", "AVISO", "FALLA"


@dataclass
class Chequeo:
    nombre: str
    detalle: str
    estado: str


def _python() -> Chequeo:
    v = sys.version_info
    texto = f"{v.major}.{v.minor}.{v.micro} ({platform.architecture()[0]})"
    if v >= (3, 12):
        return Chequeo("Python", texto, OK)
    if v >= (3, 10):
        return Chequeo("Python", texto + " - se recomienda 3.12 o superior", AVISO)
    return Chequeo("Python", texto + " - se necesita 3.10 o superior", FALLA)


def _tkinter(probar_ventana: bool) -> list[Chequeo]:
    try:
        import tkinter as tk
    except ImportError:
        return [Chequeo("Tkinter", "no está instalado (marque 'tcl/tk' al instalar Python)",
                        FALLA)]
    chequeos = [Chequeo("Tkinter / Tk", str(tk.TkVersion), OK)]
    if probar_ventana:
        try:
            raiz = tk.Tk()
            raiz.withdraw()
            raiz.update_idletasks()
            raiz.destroy()
            chequeos.append(Chequeo("Ventana gráfica", "se puede abrir", OK))
        except tk.TclError as e:
            chequeos.append(Chequeo("Ventana gráfica",
                                    f"no hay pantalla ({e}); use --consola", AVISO))
    return chequeos


def _matplotlib() -> Chequeo:
    try:
        import matplotlib
        from matplotlib.backends import backend_tkagg  # noqa: F401  (backend de la GUI)
    except ImportError as e:
        return Chequeo("Matplotlib", f"falta ({e}); ejecute pip install -r requirements.txt",
                       FALLA)
    return Chequeo("Matplotlib", matplotlib.__version__, OK)


def _base_datos() -> list[Chequeo]:
    from .bd import RUTA_ESQUEMA, BaseDatos, ruta_bd_por_defecto

    chequeos = [Chequeo("SQLite", sqlite3.sqlite_version, OK)]
    if not RUTA_ESQUEMA.exists():
        return chequeos + [Chequeo("Esquema de la BD", f"no se encuentra {RUTA_ESQUEMA}", FALLA)]
    ruta = ruta_bd_por_defecto()
    carpeta = ruta.parent
    try:
        carpeta.mkdir(parents=True, exist_ok=True)
        escribible = os.access(carpeta, os.W_OK)
    except OSError:
        escribible = False
    chequeos.append(Chequeo("Archivo de la BD", f"{ruta}" + ("" if escribible else
                            " (la carpeta no permite escribir)"), OK if escribible else FALLA))
    try:  # el esquema se prueba en una BD temporal para no tocar el historial
        with tempfile.TemporaryDirectory() as d:
            bd = BaseDatos(Path(d) / "diagnostico.db")
            tablas = {f["name"] for f in bd.con.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'")}
            bd.cerrar()
        esperadas = {"algoritmo", "escenario", "proceso", "simulacion",
                     "resultado_proceso", "segmento_gantt"}
        faltan = esperadas - tablas
        chequeos.append(Chequeo("Esquema de la BD", "6 tablas creadas" if not faltan
                                else "faltan " + ", ".join(sorted(faltan)),
                                OK if not faltan else FALLA))
    except sqlite3.Error as e:
        chequeos.append(Chequeo("Esquema de la BD", str(e), FALLA))
    return chequeos


def _motor() -> list[Chequeo]:
    from .algoritmos import simular
    from .metricas import formato
    from .modelos import Proceso
    from .paso_a_paso import trazar

    ps = [Proceso("P1", 0, 5, 2), Proceso("P2", 1, 3, 1), Proceso("P3", 2, 4, 3)]
    chequeos = []
    r = simular(ps, "FCFS")
    bien = (round(r.espera_promedio, 2), round(r.retorno_promedio, 2)) == (3.33, 7.33)
    chequeos.append(Chequeo("Ejercicio de la ficha", f"FCFS espera {formato(r.espera_promedio)}"
                            f", retorno {formato(r.retorno_promedio)}", OK if bien else FALLA))
    esperados = {("SJF", None, False): 3.33, ("SJF", None, True): 3.0,
                 ("Round Robin", 2, False): 5.67, ("Prioridad", None, False): 3.33,
                 ("Prioridad", None, True): 3.0}
    malos = [f"{a}{' exp.' if e else ''}" for (a, q, e), espera in esperados.items()
             if round(simular(ps, a, q, e).espera_promedio, 2) != espera]
    chequeos.append(Chequeo("Algoritmos", "6 configuraciones simuladas" if not malos
                            else "resultado distinto en " + ", ".join(malos),
                            OK if not malos else FALLA))
    instantes = trazar(ps, simular(ps, "Round Robin", 2))
    coherente = (len(instantes) == 13 and instantes[-1].cambios_contexto == 6)
    chequeos.append(Chequeo("Paso a paso", f"{len(instantes)} instantes coherentes con el Gantt",
                            OK if coherente else FALLA))
    return chequeos


def ejecutar(salida: TextIO, probar_ventana: bool = True) -> int:
    """Imprime el diagnostico y devuelve 0 si no hay fallas."""
    chequeos = [
        Chequeo("PlanifiCPU", __version__ + (" (ejecutable)" if getattr(sys, "frozen", False)
                                             else " (código fuente)"), OK),
        Chequeo("Sistema operativo", f"{platform.system()} {platform.release()} "
                                     f"({platform.machine()})", OK),
        _python(),
        *_tkinter(probar_ventana),
        _matplotlib(),
    ]
    try:
        chequeos += _base_datos()
    except Exception as e:  # el diagnostico nunca debe caerse
        chequeos.append(Chequeo("Base de datos", repr(e), FALLA))
    try:
        chequeos += _motor()
    except Exception as e:
        chequeos.append(Chequeo("Motor", repr(e), FALLA))

    print(f"PlanifiCPU {__version__} - diagnóstico del entorno", file=salida)
    print("-" * 78, file=salida)
    ancho = max(len(c.nombre) for c in chequeos) + 2
    for c in chequeos:
        print(f"[{c.estado:^5}] {c.nombre.ljust(ancho, '.')} {c.detalle}", file=salida)
    print("-" * 78, file=salida)
    fallas = [c for c in chequeos if c.estado == FALLA]
    avisos = [c for c in chequeos if c.estado == AVISO]
    if fallas:
        print(f"Resultado: {len(fallas)} falla(s). Revise los puntos marcados con FALLA.",
              file=salida)
        return 1
    if avisos:
        print(f"Resultado: listo, con {len(avisos)} aviso(s).", file=salida)
    else:
        print("Resultado: el entorno está listo para ejecutar PlanifiCPU.", file=salida)
    return 0
