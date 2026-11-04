"""Calculo de tiempos de espera, retorno y respuesta a partir del diagrama de Gantt."""

from __future__ import annotations

from .modelos import Proceso, ResultadoProceso, Segmento


def calcular_metricas(procesos: list[Proceso], gantt: list[Segmento]) -> list[ResultadoProceso]:
    inicio: dict[str, int] = {}
    fin: dict[str, int] = {}
    for seg in gantt:
        if seg.pid is None:
            continue
        inicio.setdefault(seg.pid, seg.inicio)
        fin[seg.pid] = seg.fin

    resultados = []
    for p in procesos:
        retorno = fin[p.pid] - p.llegada
        resultados.append(ResultadoProceso(
            pid=p.pid, llegada=p.llegada, rafaga=p.rafaga, prioridad=p.prioridad,
            inicio=inicio[p.pid], fin=fin[p.pid],
            espera=retorno - p.rafaga,
            retorno=retorno,
            respuesta=inicio[p.pid] - p.llegada,
        ))
    return resultados


def formato(valor: float) -> str:
    """Numero con dos decimales y coma decimal (formato colombiano)."""
    return f"{valor:.2f}".replace(".", ",")
