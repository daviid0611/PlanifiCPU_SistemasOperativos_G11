"""Modo consola: simula desde la terminal, sin interfaz grafica.

Sirve para revisar ejercicios rapido, para equipos sin pantalla (servidores,
GitHub Actions) y para generar evidencias en texto. Usa el mismo motor que la
interfaz, asi que los resultados son identicos.

Ejemplos (desde la raiz del repositorio):
    python src/codigo_fuente/main.py --consola
    python src/codigo_fuente/main.py --consola recursos/datos_ejemplo/ejemplo_cinco_procesos.csv -a rr -q 3
    python src/codigo_fuente/main.py --consola mi_escenario.csv --comparar --exportar resultados.csv
    python src/codigo_fuente/main.py --consola -a srtf --traza

Solo se usan caracteres ASCII y letras del espanol para que la salida funcione en
la consola de Windows y al redirigirla a un archivo.
"""

from __future__ import annotations

from pathlib import Path
from typing import TextIO

from . import __version__, csv_io
from .algoritmos import comparar, simular
from .metricas import formato
from .modelos import Proceso, Resultado
from .paso_a_paso import trazar

EJEMPLO_FICHA = [Proceso("P1", 0, 5, 2), Proceso("P2", 1, 3, 1), Proceso("P3", 2, 4, 3)]

# alias aceptados en --algoritmo -> (algoritmo del motor, expropiativo)
ALIAS = {
    "fcfs": ("FCFS", False),
    "sjf": ("SJF", False),
    "srtf": ("SJF", True),
    "rr": ("Round Robin", False),
    "round-robin": ("Round Robin", False),
    "prioridad": ("Prioridad", False),
    "prioridad-exp": ("Prioridad", True),
}


# ----------------------------------------------------------------- formatos
def tabla(encabezados: list[str], filas: list[list[str]], alinear_izq: int = 1) -> str:
    """Tabla ASCII. Las primeras `alinear_izq` columnas se alinean a la izquierda."""
    anchos = [max(len(str(x)) for x in col) for col in zip(encabezados, *filas)]
    borde = "+" + "+".join("-" * (a + 2) for a in anchos) + "+"

    def linea(valores) -> str:
        celdas = []
        for n, (v, a) in enumerate(zip(valores, anchos)):
            v = str(v)
            celdas.append(" " + (v.ljust(a) if n < alinear_izq else v.rjust(a)) + " ")
        return "|" + "|".join(celdas) + "|"

    return "\n".join([borde, linea(encabezados), borde, *[linea(f) for f in filas], borde])


def gantt_texto(r: Resultado, escala: int = 3) -> str:
    """Diagrama de Gantt en texto: cada unidad de tiempo ocupa `escala` caracteres."""
    if not r.gantt:
        return "(sin tramos)"
    celdas, bordes = [], [0]
    for s in r.gantt:
        etiqueta = s.pid or "--"
        ancho = max(s.duracion * escala, len(etiqueta) + 2)
        celdas.append(etiqueta.center(ancho))
        bordes.append(bordes[-1] + ancho + 1)
    barra = "|" + "|".join(celdas) + "|"
    marco = "+" + "+".join("-" * len(c) for c in celdas) + "+"

    tiempos = [r.gantt[0].inicio] + [s.fin for s in r.gantt]
    regla = [" "] * (bordes[-1] + 6)
    ocupado_hasta = -1
    for pos, t in zip(bordes, tiempos):
        texto = str(t)
        if pos <= ocupado_hasta:          # no se encima con el numero anterior
            continue
        regla[pos:pos + len(texto)] = texto
        ocupado_hasta = pos + len(texto)
    return "\n".join([marco, barra, marco, "".join(regla).rstrip()])


def reporte(r: Resultado) -> str:
    filas = [[p.pid, p.llegada, p.rafaga, p.prioridad, p.inicio, p.fin,
              p.espera, p.retorno, p.respuesta] for p in r.procesos]
    filas.append(["Promedio", "", "", "", "", "", formato(r.espera_promedio),
                  formato(r.retorno_promedio), formato(r.respuesta_promedio)])
    partes = [
        f"Algoritmo: {r.nombre}",
        "",
        "Diagrama de Gantt (-- = CPU ociosa)",
        gantt_texto(r),
        "",
        "Métricas por proceso",
        tabla(["Proceso", "Llegada", "Ráfaga", "Prioridad", "Inicio", "Fin",
               "Espera", "Retorno", "Respuesta"], filas),
        "",
        f"Tiempo total: {r.tiempo_total} u.t.  |  CPU ociosa: {r.tiempo_ocioso} u.t.  |  "
        f"Utilización de CPU: {formato(r.utilizacion_cpu)} %",
        f"Rendimiento: {formato(r.rendimiento)} procesos/u.t.  |  "
        f"Espera máxima: {r.espera_maxima} ({r.proceso_mayor_espera})  |  "
        f"Cambios de contexto: {r.cambios_contexto}",
    ]
    return "\n".join(partes)


def reporte_comparacion(resultados: list[Resultado]) -> str:
    filas = [[r.nombre, formato(r.espera_promedio), formato(r.retorno_promedio),
              formato(r.respuesta_promedio), r.espera_maxima, r.cambios_contexto,
              formato(r.utilizacion_cpu) + " %"] for r in resultados]
    lineas = [
        "Comparación de algoritmos con el mismo conjunto de procesos",
        tabla(["Algoritmo", "Espera prom.", "Retorno prom.", "Respuesta prom.",
               "Espera máx.", "Cambios ctx.", "Uso de CPU"], filas),
        "",
        "Mejor en cada métrica (menor es mejor):",
    ]
    for titulo, valor in (("Espera promedio", lambda r: r.espera_promedio),
                          ("Retorno promedio", lambda r: r.retorno_promedio),
                          ("Respuesta promedio", lambda r: r.respuesta_promedio),
                          ("Espera máxima", lambda r: r.espera_maxima),
                          ("Cambios de contexto", lambda r: r.cambios_contexto)):
        mejor = min(valor(r) for r in resultados)
        nombres = [r.nombre for r in resultados if valor(r) == mejor]
        texto = formato(mejor) if isinstance(mejor, float) else str(mejor)
        lineas.append(f"  - {titulo}: {', '.join(nombres)} ({texto})")
    return "\n".join(lineas)


def traza_texto(procesos: list[Proceso], r: Resultado) -> str:
    lineas = [f"Paso a paso - {r.nombre}"]
    for i in trazar(procesos, r):
        cpu = "ociosa" if i.en_cpu is None else f"{i.en_cpu} (faltan {i.restante[i.en_cpu]})"
        if i.t == r.tiempo_total:
            cpu = "libre"
        cola = ", ".join(i.cola) if i.cola else "vacía"
        lineas.append(f"t={i.t:>3} | CPU: {cpu:<14} | Cola: {cola}")
        lineas.extend(f"        * {e}" for e in i.eventos)
    return "\n".join(lineas)


# -------------------------------------------------------------- ejecucion
def ejecutar(args, salida: TextIO) -> int:
    """Corre el modo consola con los argumentos de main.py. Devuelve el codigo de salida."""
    if args.csv:
        procesos = csv_io.cargar_procesos(args.csv)
        origen = f"{args.csv} ({len(procesos)} procesos)"
    else:
        procesos = [Proceso(p.pid, p.llegada, p.rafaga, p.prioridad) for p in EJEMPLO_FICHA]
        origen = "ejemplo de la ficha técnica (3 procesos)"
    algoritmo, expropiativo = ALIAS[args.algoritmo]
    expropiativo = expropiativo or args.expropiativo

    def escribir(texto: str = "") -> None:
        print(texto, file=salida)

    escribir(f"PlanifiCPU {__version__} - modo consola")
    escribir(f"Escenario: {origen}")
    escribir()
    escribir(tabla(["Proceso", "Llegada", "Ráfaga", "Prioridad"],
                   [[p.pid, p.llegada, p.rafaga, p.prioridad] for p in procesos]))
    escribir()

    if args.comparar:
        resultados = comparar(procesos, args.quantum, expropiativo)
        for r in resultados:
            escribir("=" * 78)
            escribir(reporte(r))
            escribir()
        escribir("=" * 78)
        escribir(reporte_comparacion(resultados))
    else:
        quantum = args.quantum if algoritmo == "Round Robin" else None
        r = simular(procesos, algoritmo, quantum, expropiativo)
        resultados = [r]
        escribir(reporte(r))
        if args.traza:
            escribir()
            escribir(traza_texto(procesos, r))

    if args.exportar:
        csv_io.exportar_resultados(args.exportar, resultados)
        escribir()
        escribir(f"Resultados exportados a {Path(args.exportar)}")
    return 0
