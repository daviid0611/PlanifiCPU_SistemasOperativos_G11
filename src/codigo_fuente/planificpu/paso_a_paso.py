"""Modo paso a paso: estado del planificador en cada unidad de tiempo.

A partir del resultado de una simulacion se reconstruye, instante por instante,
que proceso tiene la CPU, como esta ordenada la cola de listos, cuanto le falta
a cada proceso y que eventos ocurrieron (llegadas, despachos, expropiaciones,
cambios de contexto y terminaciones).

El instante t representa la unidad de tiempo [t, t+1). Se agrega un instante
final (t = tiempo total) en el que todos los procesos ya terminaron.

Orden de la cola de listos:
- FCFS, SJF y Prioridad: el orden en que el planificador elegiria a los procesos
  (misma clave y mismos desempates que el motor), asi el primero de la cola es
  el siguiente en obtener la CPU.
- Round Robin: el orden real de la cola FIFO, respetando que las llegadas
  durante un quantum entran antes que el proceso expropiado.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field

from .algoritmos import _CLAVES
from .modelos import Proceso, Resultado

NUEVO, LISTO, EJECUCION, TERMINADO = "Nuevo", "Listo", "En ejecución", "Terminado"


@dataclass
class Instante:
    """Foto del planificador al inicio de la unidad de tiempo t."""

    t: int
    en_cpu: str | None                 # None = CPU ociosa
    cola: list[str]                    # cola de listos (sin el proceso en CPU)
    restante: dict[str, int]           # rafaga pendiente al inicio de t
    estados: dict[str, str]            # Nuevo / Listo / En ejecucion / Terminado
    eventos: list[str] = field(default_factory=list)
    cambios_contexto: int = 0          # acumulados hasta este instante


def _cpu_por_unidad(resultado: Resultado) -> list[str | None]:
    """Expande el Gantt a una lista con el proceso que ocupa cada unidad."""
    cpu: list[str | None] = []
    for seg in resultado.gantt:
        cpu.extend([seg.pid] * seg.duracion)
    return cpu


def _orden_round_robin(procesos: list[Proceso], quantum: int,
                       total: int) -> list[list[str]]:
    """Reproduce la cola FIFO de Round Robin unidad por unidad."""
    orden = sorted(range(len(procesos)), key=lambda i: (procesos[i].llegada, i))
    restante = [p.rafaga for p in procesos]
    cola: deque[int] = deque()
    colas: list[list[str]] = []
    k, actual, fin_quantum = 0, None, 0
    for t in range(total + 1):
        while k < len(orden) and procesos[orden[k]].llegada <= t:
            cola.append(orden[k])           # las llegadas entran primero
            k += 1
        if actual is not None and (t == fin_quantum or restante[actual] == 0):
            if restante[actual] > 0:
                cola.append(actual)         # el expropiado va al final
            actual = None
        if actual is None and cola:
            actual = cola.popleft()
            fin_quantum = t + min(quantum, restante[actual])
        colas.append([procesos[i].pid for i in cola])
        if actual is not None:
            restante[actual] -= 1
    return colas


def trazar(procesos: list[Proceso], resultado: Resultado) -> list[Instante]:
    """Devuelve la lista de instantes 0..tiempo_total de la simulacion."""
    cpu = _cpu_por_unidad(resultado)
    total = len(cpu)
    idx = {p.pid: i for i, p in enumerate(procesos)}
    restante = {p.pid: p.rafaga for p in procesos}
    colas_rr = (_orden_round_robin(procesos, resultado.quantum, total)
                if resultado.algoritmo == "Round Robin" else None)
    clave = _CLAVES.get(resultado.algoritmo)

    instantes: list[Instante] = []
    anterior: str | None = None      # proceso de la unidad anterior (o None)
    ultimo: str | None = None        # ultimo proceso que uso la CPU
    cambios = 0
    for t in range(total + 1):
        actual = cpu[t] if t < total else None
        eventos: list[str] = []

        if anterior is not None and restante[anterior] == 0:
            eventos.append(f"{anterior} termina su ráfaga y sale del sistema")
        for p in procesos:
            if p.llegada == t:
                eventos.append(f"{p.pid} llega al sistema y entra a la cola de listos")

        if actual is None:
            if t == total:
                eventos.append("Fin de la simulación: todos los procesos terminaron")
            elif anterior is not None or t == 0:
                eventos.append("CPU ociosa: no hay procesos en la cola de listos")
        elif actual != anterior:
            if ultimo is None:
                eventos.append(f"{actual} toma la CPU")
            elif ultimo == actual:
                eventos.append(f"{actual} vuelve a la CPU")
            else:
                cambios += 1
                if anterior is not None and restante[anterior] > 0:
                    eventos.append(f"Cambio de contexto: {anterior} es expropiado "
                                   f"(le faltan {restante[anterior]}) y entra {actual}")
                else:
                    eventos.append(f"Cambio de contexto: {ultimo} -> {actual}")
        elif (resultado.algoritmo == "Round Robin" and t > 0
              and (t - _inicio_tramo(cpu, t)) % resultado.quantum == 0):
            eventos.append(f"Quantum agotado: {actual} sigue en la CPU porque la cola está vacía")

        listos = [p.pid for p in procesos
                  if p.llegada <= t and restante[p.pid] > 0 and p.pid != actual]
        if colas_rr is not None:
            cola = [pid for pid in colas_rr[t] if pid in listos]
        else:
            cola = sorted(listos, key=lambda pid: (
                clave(procesos[idx[pid]], restante[pid]), procesos[idx[pid]].llegada, idx[pid]))

        estados = {}
        for p in procesos:
            if restante[p.pid] == 0:
                estados[p.pid] = TERMINADO
            elif p.pid == actual:
                estados[p.pid] = EJECUCION
            elif p.llegada <= t:
                estados[p.pid] = LISTO
            else:
                estados[p.pid] = NUEVO

        instantes.append(Instante(t=t, en_cpu=actual, cola=cola, restante=dict(restante),
                                  estados=estados, eventos=eventos, cambios_contexto=cambios))
        if actual is not None:
            restante[actual] -= 1
            ultimo = actual
        anterior = actual
    return instantes


def _inicio_tramo(cpu: list[str | None], t: int) -> int:
    """Primer instante del tramo continuo que contiene a t."""
    inicio = t
    while inicio > 0 and cpu[inicio - 1] == cpu[t]:
        inicio -= 1
    return inicio
