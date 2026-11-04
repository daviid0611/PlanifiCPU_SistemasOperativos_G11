"""Motor de planificacion: FCFS, SJF, Round Robin y Prioridad.

Convenciones (las mismas del curso):
- El reloj avanza en unidades enteras de tiempo.
- Empates: se elige el que llego primero y, si llegaron igual, el que se registro primero.
- En los modos expropiativos, ante un empate se mantiene el proceso que ya esta en CPU.
- En Round Robin, los procesos que llegan durante un quantum entran a la cola
  antes que el proceso expropiado al final de ese quantum.
- Prioridad: menor numero = mayor prioridad.
"""

from __future__ import annotations

from collections import deque
from typing import Callable

from .metricas import calcular_metricas
from .modelos import Proceso, Resultado, Segmento, validar_procesos

ALGORITMOS = ("FCFS", "SJF", "Round Robin", "Prioridad")


def admite_expropiacion(algoritmo: str) -> bool:
    return algoritmo in ("SJF", "Prioridad")


def _agregar(gantt: list[Segmento], pid: str | None, inicio: int, fin: int) -> None:
    """Agrega un tramo al Gantt, uniendolo con el anterior si es el mismo proceso."""
    if fin <= inicio:
        return
    if gantt and gantt[-1].pid == pid and gantt[-1].fin == inicio:
        gantt[-1].fin = fin
    else:
        gantt.append(Segmento(pid, inicio, fin))


Clave = Callable[[Proceso, int], int]


def _no_expropiativo(procesos: list[Proceso], clave: Clave) -> list[Segmento]:
    """Cada proceso elegido corre su rafaga completa."""
    pendientes = sorted(range(len(procesos)), key=lambda i: (procesos[i].llegada, i))
    listos: list[int] = []
    gantt: list[Segmento] = []
    t = 0
    while pendientes or listos:
        while pendientes and procesos[pendientes[0]].llegada <= t:
            listos.append(pendientes.pop(0))
        if not listos:
            siguiente = procesos[pendientes[0]].llegada
            _agregar(gantt, None, t, siguiente)
            t = siguiente
            continue
        i = min(listos, key=lambda j: (clave(procesos[j], procesos[j].rafaga),
                                       procesos[j].llegada, j))
        listos.remove(i)
        _agregar(gantt, procesos[i].pid, t, t + procesos[i].rafaga)
        t += procesos[i].rafaga
    return gantt


def _expropiativo(procesos: list[Proceso], clave: Clave) -> list[Segmento]:
    """Se reevalua la decision en cada unidad de tiempo."""
    restante = [p.rafaga for p in procesos]
    gantt: list[Segmento] = []
    t, actual = 0, None
    while any(restante):
        listos = [i for i, p in enumerate(procesos) if p.llegada <= t and restante[i] > 0]
        if not listos:
            siguiente = min(p.llegada for i, p in enumerate(procesos) if restante[i] > 0)
            _agregar(gantt, None, t, siguiente)
            t, actual = siguiente, None
            continue
        i = min(listos, key=lambda j: (clave(procesos[j], restante[j]), j != actual,
                                       procesos[j].llegada, j))
        _agregar(gantt, procesos[i].pid, t, t + 1)
        restante[i] -= 1
        t += 1
        actual = i
    return gantt


def _round_robin(procesos: list[Proceso], quantum: int) -> list[Segmento]:
    orden = sorted(range(len(procesos)), key=lambda i: (procesos[i].llegada, i))
    restante = [p.rafaga for p in procesos]
    cola: deque[int] = deque()
    gantt: list[Segmento] = []
    t, k = 0, 0

    def encolar_llegadas(hasta: int) -> None:
        nonlocal k
        while k < len(orden) and procesos[orden[k]].llegada <= hasta:
            cola.append(orden[k])
            k += 1

    encolar_llegadas(t)
    while cola or k < len(orden):
        if not cola:
            siguiente = procesos[orden[k]].llegada
            _agregar(gantt, None, t, siguiente)
            t = siguiente
            encolar_llegadas(t)
            continue
        i = cola.popleft()
        uso = min(quantum, restante[i])
        _agregar(gantt, procesos[i].pid, t, t + uso)
        t += uso
        restante[i] -= uso
        encolar_llegadas(t)
        if restante[i] > 0:
            cola.append(i)
    return gantt


_CLAVES: dict[str, Clave] = {
    "FCFS": lambda p, restante: p.llegada,
    "SJF": lambda p, restante: restante,
    "Prioridad": lambda p, restante: p.prioridad,
}


def simular(procesos: list[Proceso], algoritmo: str, quantum: int | None = None,
            expropiativo: bool = False) -> Resultado:
    """Ejecuta el algoritmo indicado y devuelve el Gantt con las metricas."""
    validar_procesos(procesos)
    if algoritmo not in ALGORITMOS:
        raise ValueError(f"Algoritmo desconocido: {algoritmo}")

    if algoritmo == "Round Robin":
        if not quantum or quantum < 1:
            raise ValueError("Round Robin necesita un quantum entero mayor o igual a 1.")
        gantt = _round_robin(procesos, quantum)
        expropiativo = True
    else:
        quantum = None
        expropiativo = expropiativo and admite_expropiacion(algoritmo)
        motor = _expropiativo if expropiativo else _no_expropiativo
        gantt = motor(procesos, _CLAVES[algoritmo])

    return Resultado(algoritmo=algoritmo, quantum=quantum, expropiativo=expropiativo,
                     gantt=gantt, procesos=calcular_metricas(procesos, gantt))


def comparar(procesos: list[Proceso], quantum: int, expropiativo: bool = False) -> list[Resultado]:
    """Corre los cuatro algoritmos con el mismo conjunto de procesos."""
    return [simular(procesos, a, quantum, expropiativo) for a in ALGORITMOS]
