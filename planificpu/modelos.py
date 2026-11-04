"""Modelos de datos de PlanifiCPU: procesos, segmentos del Gantt y resultados."""

from __future__ import annotations

from dataclasses import dataclass, field


class ErrorValidacion(ValueError):
    """Se lanza cuando los datos de entrada de los procesos no son validos."""


@dataclass
class Proceso:
    """Proceso de entrada. Menor numero de prioridad = mayor prioridad."""

    pid: str
    llegada: int
    rafaga: int
    prioridad: int = 0


@dataclass
class Segmento:
    """Tramo del diagrama de Gantt. pid None significa CPU ociosa."""

    pid: str | None
    inicio: int
    fin: int

    @property
    def duracion(self) -> int:
        return self.fin - self.inicio


@dataclass
class ResultadoProceso:
    """Metricas de tiempo de un proceso despues de la simulacion."""

    pid: str
    llegada: int
    rafaga: int
    prioridad: int
    inicio: int       # primera vez que obtiene la CPU
    fin: int          # instante en que termina
    espera: int       # retorno - rafaga
    retorno: int      # fin - llegada
    respuesta: int    # inicio - llegada


@dataclass
class Resultado:
    """Resultado completo de ejecutar un algoritmo sobre un conjunto de procesos."""

    algoritmo: str
    quantum: int | None
    expropiativo: bool
    gantt: list[Segmento] = field(default_factory=list)
    procesos: list[ResultadoProceso] = field(default_factory=list)

    @property
    def nombre(self) -> str:
        if self.algoritmo == "Round Robin":
            return f"Round Robin (q={self.quantum})"
        if self.expropiativo:
            return {"SJF": "SJF expropiativo (SRTF)",
                    "Prioridad": "Prioridad expropiativa"}.get(self.algoritmo, self.algoritmo)
        return self.algoritmo

    def _promedio(self, campo: str) -> float:
        if not self.procesos:
            return 0.0
        return sum(getattr(p, campo) for p in self.procesos) / len(self.procesos)

    @property
    def espera_promedio(self) -> float:
        return self._promedio("espera")

    @property
    def retorno_promedio(self) -> float:
        return self._promedio("retorno")

    @property
    def respuesta_promedio(self) -> float:
        return self._promedio("respuesta")

    @property
    def cambios_contexto(self) -> int:
        """Veces que la CPU pasa a ejecutar un proceso distinto del anterior."""
        cambios, anterior = 0, None
        for seg in self.gantt:
            if seg.pid is None:
                continue
            if anterior is not None and seg.pid != anterior:
                cambios += 1
            anterior = seg.pid
        return cambios

    @property
    def tiempo_total(self) -> int:
        return self.gantt[-1].fin if self.gantt else 0


def validar_procesos(procesos: list[Proceso]) -> None:
    """Valida la lista de procesos. Lanza ErrorValidacion con un mensaje claro."""
    if not procesos:
        raise ErrorValidacion("Debe registrar al menos un proceso.")
    vistos: set[str] = set()
    for p in procesos:
        if not str(p.pid).strip():
            raise ErrorValidacion("Todos los procesos deben tener PID.")
        if p.pid in vistos:
            raise ErrorValidacion(f"El PID {p.pid} está repetido.")
        vistos.add(p.pid)
        for nombre, valor, minimo in (("llegada", p.llegada, 0),
                                      ("ráfaga", p.rafaga, 1),
                                      ("prioridad", p.prioridad, 0)):
            if not isinstance(valor, int) or isinstance(valor, bool):
                raise ErrorValidacion(f"{p.pid}: el tiempo de {nombre} debe ser un entero.")
            if valor < minimo:
                raise ErrorValidacion(f"{p.pid}: el tiempo de {nombre} debe ser >= {minimo}.")
