"""Carga de escenarios y exportacion de resultados en CSV.

Se aceptan archivos separados por coma o por punto y coma (Excel en espanol
usa punto y coma). Los resultados se exportan con punto y coma y coma decimal
para que abran bien en Excel con configuracion regional de Colombia.
"""

from __future__ import annotations

import csv
from pathlib import Path

from .metricas import formato
from .modelos import ErrorValidacion, Proceso, Resultado

COLUMNAS = ("pid", "llegada", "rafaga", "prioridad")


def cargar_procesos(ruta: str | Path) -> list[Proceso]:
    texto = Path(ruta).read_text(encoding="utf-8-sig")
    if not texto.strip():
        raise ErrorValidacion("El archivo CSV está vacío.")
    primera = texto.splitlines()[0]
    delimitador = ";" if primera.count(";") > primera.count(",") else ","
    lector = csv.DictReader(texto.splitlines(), delimiter=delimitador)
    encabezados = [c.strip().lower() for c in (lector.fieldnames or [])]
    faltantes = [c for c in COLUMNAS[:3] if c not in encabezados]
    if faltantes:
        raise ErrorValidacion("Al CSV le faltan columnas: " + ", ".join(faltantes))

    procesos = []
    for n, fila in enumerate(lector, start=2):
        fila = {k.strip().lower(): (v or "").strip() for k, v in fila.items() if k}
        if not any(fila.values()):
            continue
        try:
            procesos.append(Proceso(
                pid=fila["pid"],
                llegada=int(fila["llegada"]),
                rafaga=int(fila["rafaga"]),
                prioridad=int(fila.get("prioridad") or 0),
            ))
        except ValueError:
            raise ErrorValidacion(f"Fila {n}: llegada, ráfaga y prioridad deben ser enteros.")
    return procesos


def guardar_procesos(ruta: str | Path, procesos: list[Proceso]) -> None:
    with open(ruta, "w", newline="", encoding="utf-8-sig") as f:
        escritor = csv.writer(f, delimiter=";")
        escritor.writerow(COLUMNAS)
        for p in procesos:
            escritor.writerow((p.pid, p.llegada, p.rafaga, p.prioridad))


def exportar_resultados(ruta: str | Path, resultados: list[Resultado]) -> None:
    """Exporta la tabla de metricas de uno o varios algoritmos y el Gantt de cada uno."""
    with open(ruta, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f, delimiter=";")
        for r in resultados:
            w.writerow(["Algoritmo", r.nombre])
            w.writerow(["Proceso", "Llegada", "Rafaga", "Prioridad", "Inicio", "Fin",
                        "Espera", "Retorno", "Respuesta"])
            for p in r.procesos:
                w.writerow([p.pid, p.llegada, p.rafaga, p.prioridad, p.inicio, p.fin,
                            p.espera, p.retorno, p.respuesta])
            w.writerow(["Promedio", "", "", "", "", "", formato(r.espera_promedio),
                        formato(r.retorno_promedio), formato(r.respuesta_promedio)])
            w.writerow(["Cambios de contexto", r.cambios_contexto])
            w.writerow(["Gantt"] + [f"{s.pid or 'Ocioso'} [{s.inicio}-{s.fin}]" for s in r.gantt])
            w.writerow([])
        if len(resultados) > 1:
            w.writerow(["Comparativo", "Espera promedio", "Retorno promedio",
                        "Respuesta promedio", "Cambios de contexto"])
            for r in resultados:
                w.writerow([r.nombre, formato(r.espera_promedio), formato(r.retorno_promedio),
                            formato(r.respuesta_promedio), r.cambios_contexto])
