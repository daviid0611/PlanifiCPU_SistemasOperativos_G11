"""Experimentos de la Fase III: resultados obtenidos con PlanifiCPU.

Usa el mismo motor de la aplicacion para responder preguntas del curso con datos:

E1. Que algoritmo gana en cada escenario de ejemplo (tabla y grafica).
E2. Como se comportan en promedio sobre 500 cargas aleatorias.
E3. Como cambia Round Robin con el quantum (q = 1 a 12).
E4. Efecto convoy en FCFS (un proceso largo delante de varios cortos).
E5. Inanicion: cuanto espera un proceso de baja prioridad cuando siguen llegando
    procesos de prioridad alta.
E6. Tiempo de ejecucion del simulador segun la cantidad de procesos (RNF05).

Uso, desde la raiz del repositorio (tarda menos de un minuto):
    python src/codigo_fuente/analisis_resultados.py
Genera CSV, graficas PNG y resumen.txt en documentacion/fase3/resultados/.
Las cargas aleatorias usan semilla fija, por lo que los resultados se repiten igual.
"""

from __future__ import annotations

import argparse
import csv
import platform
import random
import statistics
import sys
import time
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.ticker import FuncFormatter  # noqa: E402

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))

from planificpu import __version__, csv_io  # noqa: E402
from planificpu.algoritmos import simular  # noqa: E402
from planificpu.modelos import Proceso  # noqa: E402
from planificpu.paso_a_paso import trazar  # noqa: E402

DATOS = RAIZ / "recursos" / "datos_ejemplo"
SEMILLA = 2026

# nombre corto, algoritmo, quantum, expropiativo
CONFIGS = [("FCFS", "FCFS", None, False), ("SJF", "SJF", None, False),
           ("SRTF", "SJF", None, True), ("RR q=3", "Round Robin", 3, False),
           ("Prioridad", "Prioridad", None, False), ("Prioridad exp.", "Prioridad", None, True)]
# paleta categorica validada (orden fijo: el color sigue al algoritmo en todas las graficas)
COLOR = dict(zip([c[0] for c in CONFIGS],
                 ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300"]))
TEXTO, TEXTO_2, REJILLA, FONDO = "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb"

ESCENARIOS = [("Ficha técnica", "ejemplo_ficha.csv"),
              ("Cinco procesos", "ejemplo_cinco_procesos.csv"),
              ("Stallings (A-E)", "stallings.csv"),
              ("Silberschatz prioridad", "silberschatz_prioridad.csv"),
              ("Efecto convoy", "efecto_convoy.csv"),
              ("Interactivos vs. CPU", "interactivos_vs_cpu.csv")]


# ------------------------------------------------------------------ utilidades
def correr(ps, config):
    _, alg, q, exp = config
    return simular(ps, alg, q, exp)


def coma(x: float, decimales: int = 2) -> str:
    return f"{x:.{decimales}f}".replace(".", ",")


def cargas_aleatorias(cantidad=500, n=8, max_llegada=20, max_rafaga=10, semilla=SEMILLA):
    azar = random.Random(semilla)
    return [[Proceso(f"P{i + 1}", azar.randint(0, max_llegada), azar.randint(1, max_rafaga),
                     azar.randint(0, 4)) for i in range(n)] for _ in range(cantidad)]


def guardar_csv(ruta: Path, encabezados, filas) -> None:
    with open(ruta, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(encabezados)
        for fila in filas:
            w.writerow([coma(v) if isinstance(v, float) else v for v in fila])


def tabla_texto(encabezados, filas) -> str:
    filas = [[coma(v) if isinstance(v, float) else str(v) for v in f] for f in filas]
    anchos = [max(len(x) for x in col) for col in zip(encabezados, *filas)]
    lineas = [" | ".join(h.ljust(a) for h, a in zip(encabezados, anchos)),
              "-+-".join("-" * a for a in anchos)]
    lineas += [" | ".join(v.ljust(a) for v, a in zip(f, anchos)) for f in filas]
    return "\n".join(lineas)


def estilo(ax, eje_valores="x") -> None:
    ax.set_facecolor(FONDO)
    for lado in ("top", "right"):
        ax.spines[lado].set_visible(False)
    for lado in ("left", "bottom"):
        ax.spines[lado].set_color("#b9b8b2")
    ax.tick_params(colors=TEXTO_2, labelsize=9)
    ax.grid(axis=eje_valores, color=REJILLA, linewidth=0.8)
    ax.set_axisbelow(True)
    decimal_con_coma = FuncFormatter(lambda v, _: f"{v:g}".replace(".", ","))
    (ax.xaxis if eje_valores == "x" else ax.yaxis).set_major_formatter(decimal_con_coma)


def figura(ancho, alto, filas=1, columnas=1, **kw):
    fig, ejes = plt.subplots(filas, columnas, figsize=(ancho, alto), dpi=150, **kw)
    fig.patch.set_facecolor(FONDO)
    return fig, ejes


def barras_horizontales(ax, nombres, valores, titulo, formato=coma, maximo=None):
    """Barras horizontales delgadas, un color por algoritmo y el valor al final."""
    ys = list(range(len(nombres)))[::-1]
    ax.barh(ys, valores, height=0.62, color=[COLOR[n] for n in nombres],
            edgecolor=FONDO, linewidth=1.5)
    ax.set_yticks(ys, nombres)
    tope = maximo or max(valores) or 1
    ax.set_xlim(0, tope * 1.22)
    for y, v in zip(ys, valores):
        ax.text(v + tope * 0.02, y, formato(v), va="center", fontsize=8.5, color=TEXTO)
    ax.set_title(titulo, loc="left", fontsize=10.5, color=TEXTO, fontweight="bold")
    estilo(ax, "x")


def titulo_figura(fig, titulo, subtitulo, extra_pulgadas=0.0) -> tuple:
    """Titulo y subtitulo arriba a la izquierda; devuelve el rect para tight_layout."""
    alto = fig.get_figheight()
    fig.text(0.01, 1 - 0.22 / alto, titulo, ha="left", va="top", fontsize=13,
             fontweight="bold", color=TEXTO)
    fig.text(0.01, 1 - 0.52 / alto, subtitulo, ha="left", va="top", fontsize=9.5,
             color=TEXTO_2)
    return (0, 0, 1, 1 - (0.8 + extra_pulgadas) / alto)


def separar_etiquetas(ax, etiquetas, x, minimo):
    """Etiquetas directas al final de lineas horizontales, sin que se encimen."""
    etiquetas = sorted(etiquetas, key=lambda e: e[1])
    posiciones = []
    for texto, y in etiquetas:
        if posiciones and y - posiciones[-1] < minimo:
            y = posiciones[-1] + minimo
        posiciones.append(y)
        ax.text(x, y, texto, va="center", fontsize=8.5, color=TEXTO)


# ----------------------------------------------------------------- experimentos
def e1_escenarios(salida: Path) -> str:
    filas, resumen = [], []
    fig, ejes = figura(12, 7.2, 2, 3)
    for ax, (nombre, archivo) in zip(ejes.flat, ESCENARIOS):
        ps = csv_io.cargar_procesos(DATOS / archivo)
        resultados = [(c[0], correr(ps, c)) for c in CONFIGS]
        for corto, r in resultados:
            filas.append([nombre, corto, r.espera_promedio, r.retorno_promedio,
                          r.respuesta_promedio, r.espera_maxima, r.cambios_contexto,
                          r.utilizacion_cpu, r.rendimiento])
        mejor = min(r.espera_promedio for _, r in resultados)
        ganadores = [c for c, r in resultados if r.espera_promedio == mejor]
        resumen.append([nombre, len(ps), ", ".join(ganadores), mejor,
                        max(r.espera_promedio for _, r in resultados)])
        barras_horizontales(ax, [c for c, _ in resultados],
                            [r.espera_promedio for _, r in resultados],
                            f"{nombre} ({len(ps)} procesos)")
    rect = titulo_figura(fig, "E1. Espera promedio por algoritmo en seis escenarios",
                         "Unidades de tiempo; menor es mejor. Round Robin con quantum 3. "
                         "Datos en recursos/datos_ejemplo/.")
    fig.tight_layout(rect=rect)
    fig.savefig(salida / "e1_espera_por_escenario.png", facecolor=FONDO)
    plt.close(fig)
    guardar_csv(salida / "e1_comparacion_escenarios.csv",
                ["Escenario", "Algoritmo", "Espera prom.", "Retorno prom.", "Respuesta prom.",
                 "Espera max.", "Cambios ctx.", "Utilizacion CPU (%)", "Rendimiento"], filas)
    return ("E1. Menor espera promedio por escenario\n" +
            tabla_texto(["Escenario", "Procesos", "Menor espera", "Valor", "Peor valor"], resumen)
            + "\n\nDetalle (escenario | algoritmo | espera | retorno | respuesta | espera max | "
              "cambios | uso CPU %)\n" +
            tabla_texto(["Escenario", "Algoritmo", "Espera", "Retorno", "Respuesta", "Esp. max",
                         "Cambios", "Uso CPU"], [f[:8] for f in filas]))


def e2_aleatorias(salida: Path, cargas) -> str:
    datos = {c[0]: [] for c in CONFIGS}
    mejor_espera = {c[0]: 0 for c in CONFIGS}
    mejor_respuesta = {c[0]: 0 for c in CONFIGS}
    for ps in cargas:
        rs = {c[0]: correr(ps, c) for c in CONFIGS}
        for corto, r in rs.items():
            datos[corto].append(r)
        for dic, attr in ((mejor_espera, "espera_promedio"),
                          (mejor_respuesta, "respuesta_promedio")):
            menor = min(getattr(r, attr) for r in rs.values())
            for corto, r in rs.items():
                dic[corto] += abs(getattr(r, attr) - menor) < 1e-9

    def media(corto, attr):
        return statistics.fmean(getattr(r, attr) for r in datos[corto])

    filas = []
    for corto, *_ in CONFIGS:
        filas.append([corto, media(corto, "espera_promedio"), media(corto, "retorno_promedio"),
                      media(corto, "respuesta_promedio"), media(corto, "espera_maxima"),
                      media(corto, "cambios_contexto"),
                      100 * mejor_espera[corto] / len(cargas),
                      100 * mejor_respuesta[corto] / len(cargas)])
    guardar_csv(salida / "e2_cargas_aleatorias.csv",
                ["Algoritmo", "Espera prom.", "Retorno prom.", "Respuesta prom.", "Espera max.",
                 "Cambios ctx.", "% cargas con menor espera", "% cargas con menor respuesta"],
                filas)

    nombres = [c[0] for c in CONFIGS]
    fig, ejes = figura(12, 3.9, 1, 3)
    barras_horizontales(ejes[0], nombres, [f[1] for f in filas], "Espera promedio")
    barras_horizontales(ejes[1], nombres, [f[3] for f in filas], "Respuesta promedio")
    barras_horizontales(ejes[2], nombres, [f[5] for f in filas], "Cambios de contexto")
    rect = titulo_figura(fig, f"E2. Promedio sobre {len(cargas)} cargas aleatorias de 8 procesos",
                         "Llegadas 0-20, ráfagas 1-10, prioridades 0-4 (semilla 2026). "
                         "Menor es mejor en las tres métricas.")
    fig.tight_layout(rect=rect)
    fig.savefig(salida / "e2_cargas_aleatorias.png", facecolor=FONDO)
    plt.close(fig)
    return (f"E2. Promedios sobre {len(cargas)} cargas aleatorias de 8 procesos\n" +
            tabla_texto(["Algoritmo", "Espera", "Retorno", "Respuesta", "Espera max",
                         "Cambios", "% mejor espera", "% mejor respuesta"], filas))


def e3_quantum(salida: Path, cargas) -> str:
    quantums = list(range(1, 13))
    filas = []
    for q in quantums:
        rs = [simular(ps, "Round Robin", q) for ps in cargas]
        filas.append([q, statistics.fmean(r.espera_promedio for r in rs),
                      statistics.fmean(r.respuesta_promedio for r in rs),
                      statistics.fmean(r.cambios_contexto for r in rs)])
    ref = {}
    for corto, alg, q, exp in (CONFIGS[0], CONFIGS[2]):
        rs = [simular(ps, alg, q, exp) for ps in cargas]
        ref[corto] = (statistics.fmean(r.espera_promedio for r in rs),
                      statistics.fmean(r.respuesta_promedio for r in rs),
                      statistics.fmean(r.cambios_contexto for r in rs))
    guardar_csv(salida / "e3_sensibilidad_quantum.csv",
                ["Quantum", "Espera prom.", "Respuesta prom.", "Cambios ctx."], filas)

    fig, ejes = figura(12, 4.3, 1, 3, sharex=True)
    titulos = ("Espera promedio", "Respuesta promedio", "Cambios de contexto")
    for k, (ax, titulo) in enumerate(zip(ejes, titulos)):
        ys = [f[k + 1] for f in filas]
        ax.plot(quantums, ys, color=COLOR["RR q=3"], linewidth=2, marker="o", markersize=5,
                markeredgecolor=FONDO, markeredgewidth=1.2, zorder=3, label="Round Robin")
        for corto, estilo_linea in (("FCFS", (0, (4, 3))), ("SRTF", (0, (1, 2)))):
            ax.plot([0.6, 12.3], [ref[corto][k]] * 2, color=COLOR[corto], linewidth=1.6,
                    linestyle=estilo_linea, zorder=2, label=corto)
        tope = max(max(ys), *(ref[c][k] for c in ref))
        separar_etiquetas(ax, [(c, ref[c][k]) for c in ref], 12.45, tope * 0.07)
        ax.set_title(titulo, loc="left", fontsize=10.5, color=TEXTO, fontweight="bold")
        ax.set_xticks(quantums)
        ax.set_xlim(0.6, 13.6)
        ax.set_xlabel("Quantum", color=TEXTO_2, fontsize=9)
        ax.set_ylim(0, tope * 1.08)
        estilo(ax, "y")
    rect = titulo_figura(fig, "E3. Round Robin según el quantum (500 cargas aleatorias)",
                         "Con q ≥ 10 (la ráfaga máxima de estas cargas) Round Robin se comporta "
                         "igual que FCFS.", extra_pulgadas=0.3)
    manijas, nombres = ejes[0].get_legend_handles_labels()
    fig.legend(manijas, nombres, loc="upper left", bbox_to_anchor=(0.008, rect[3] + 0.3 /
               fig.get_figheight() + 0.02), ncol=3, frameon=False, fontsize=9)
    fig.tight_layout(rect=rect)
    fig.savefig(salida / "e3_sensibilidad_quantum.png", facecolor=FONDO)
    plt.close(fig)
    refs = [[c, *ref[c]] for c in ref]
    return ("E3. Round Robin segun el quantum (promedios sobre las mismas cargas)\n" +
            tabla_texto(["Quantum", "Espera", "Respuesta", "Cambios"], filas) +
            "\nReferencias\n" + tabla_texto(["Algoritmo", "Espera", "Respuesta", "Cambios"], refs))


def e4_convoy(salida: Path) -> str:
    primero = csv_io.cargar_procesos(DATOS / "efecto_convoy.csv")
    al_final = [Proceso(p.pid, 3 if p.pid == "LARGO" else p.llegada - 1, p.rafaga, p.prioridad)
                for p in primero]
    filas = []
    variantes = (("El largo llega primero (t=0)", primero),
                 ("El largo llega al final (t=3)", al_final))
    fig, ejes = figura(11, 3.9, 1, 2, sharex=True)
    tope = 0
    datos = []
    for titulo, ps in variantes:
        rs = [(c[0], correr(ps, c)) for c in CONFIGS]
        cortos = [statistics.fmean(m.espera for m in r.procesos if m.pid != "LARGO")
                  for _, r in rs]
        datos.append((titulo, rs, cortos))
        tope = max(tope, *[r.espera_promedio for _, r in rs])
        for (corto, r), ec in zip(rs, cortos):
            filas.append([titulo, corto, r.espera_promedio, ec, r.espera_maxima])
    for ax, (titulo, rs, _) in zip(ejes, datos):
        barras_horizontales(ax, [c for c, _ in rs], [r.espera_promedio for _, r in rs], titulo,
                            maximo=tope)
    rect = titulo_figura(fig, "E4. Efecto convoy: espera promedio con un proceso de ráfaga 20 y "
                              "cuatro cortos",
                         "Mismos procesos; solo cambia cuándo llega el largo. Menor es mejor.")
    fig.tight_layout(rect=rect)
    fig.savefig(salida / "e4_efecto_convoy.png", facecolor=FONDO)
    plt.close(fig)
    guardar_csv(salida / "e4_efecto_convoy.csv",
                ["Variante", "Algoritmo", "Espera prom.", "Espera prom. de los cortos",
                 "Espera max."], filas)
    return ("E4. Efecto convoy\n" +
            tabla_texto(["Variante", "Algoritmo", "Espera", "Espera cortos", "Espera max"],
                        filas))


def e5_inanicion(salida: Path) -> str:
    """BAJA (prioridad 4, rafaga 3) llega en t=1; cada 2 u.t. llega un proceso ALTA."""
    ks = list(range(0, 13))
    series = {c[0]: [] for c in CONFIGS}
    filas = []
    for k in ks:
        ps = [Proceso("BAJA", 1, 3, 4)] + [Proceso(f"ALTA{i + 1}", 2 * i, 2, 1) for i in range(k)]
        fila = [k]
        for c in CONFIGS:
            r = correr(ps, c)
            espera = next(m.espera for m in r.procesos if m.pid == "BAJA")
            series[c[0]].append(espera)
            fila.append(espera)
        filas.append(fila)
    guardar_csv(salida / "e5_inanicion.csv", ["Procesos ALTA"] + [c[0] for c in CONFIGS], filas)

    fig, ax = figura(9, 4.6)
    grupos: dict[tuple, list[str]] = {}
    for corto, ys in series.items():
        grupos.setdefault(tuple(ys), []).append(corto)
    marcadores = ["o", "s", "D", "^", "v", "P"]
    for n, (ys, nombres) in enumerate(grupos.items()):
        ax.plot(ks, ys, color=COLOR[nombres[0]], linewidth=2, marker=marcadores[n],
                markersize=6, markeredgecolor=FONDO, markeredgewidth=1.2,
                label=" = ".join(nombres))
        ax.text(ks[-1] + 0.25, ys[-1], " = ".join(nombres), va="center", fontsize=8.5,
                color=TEXTO)
    ax.set_xticks(ks)
    ax.set_xlim(-0.3, ks[-1] + 3.6)
    ax.set_ylim(bottom=0)
    ax.set_xlabel("Procesos de prioridad alta que llegan (uno cada 2 u.t.)", color=TEXTO_2,
                  fontsize=9)
    ax.set_ylabel("Espera del proceso BAJA (u.t.)", color=TEXTO_2, fontsize=9)
    ax.legend(frameon=False, fontsize=8.5, loc="upper left")
    estilo(ax, "y")
    rect = titulo_figura(fig, "E5. Inanición: espera de un proceso de baja prioridad",
                         "BAJA: llegada 1, ráfaga 3, prioridad 4. Cada proceso ALTA: ráfaga 2, "
                         "prioridad 1. Las líneas iguales se agrupan.")
    fig.tight_layout(rect=rect)
    fig.savefig(salida / "e5_inanicion.png", facecolor=FONDO)
    plt.close(fig)
    return ("E5. Espera del proceso BAJA segun cuantos procesos ALTA llegan\n" +
            tabla_texto(["ALTA"] + [c[0] for c in CONFIGS], filas))


def e6_tiempos(salida: Path, rapido: bool) -> str:
    tamanos = [10, 50, 100, 500] if rapido else [10, 50, 100, 500, 1000]
    azar = random.Random(SEMILLA)
    filas = []
    for n in tamanos:
        ps = [Proceso(f"P{i + 1}", azar.randint(0, 2 * n), azar.randint(1, 10),
                      azar.randint(0, 9)) for i in range(n)]
        fila = [n]
        for c in CONFIGS:
            medidas = []
            for _ in range(3):
                inicio = time.perf_counter()
                correr(ps, c)
                medidas.append(time.perf_counter() - inicio)
            fila.append(1000 * statistics.median(medidas))
        if n <= 100:   # simulacion + traza paso a paso del caso mas costoso (RR q=3)
            inicio = time.perf_counter()
            trazar(ps, correr(ps, CONFIGS[3]))
            fila.append(1000 * (time.perf_counter() - inicio))
        else:
            fila.append("-")
        filas.append(fila)
    guardar_csv(salida / "e6_tiempos_ms.csv",
                ["Procesos"] + [c[0] for c in CONFIGS] + ["RR q=3 + paso a paso"], filas)
    return ("E6. Tiempo de simulacion en milisegundos (mediana de 3 corridas)\n" +
            tabla_texto(["Procesos"] + [c[0] for c in CONFIGS] + ["RR+paso a paso"], filas))


def equipo() -> str:
    cpu = platform.processor() or platform.machine()
    try:
        for linea in Path("/proc/cpuinfo").read_text().splitlines():
            if linea.startswith("model name"):
                cpu = linea.split(":", 1)[1].strip()
                break
    except OSError:
        pass
    return (f"PlanifiCPU {__version__} | {platform.system()} {platform.release()} | "
            f"Python {platform.python_version()} | Matplotlib {matplotlib.__version__} | {cpu}")


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--salida", default=str(RAIZ / "documentacion" / "fase3" / "resultados"))
    p.add_argument("--rapido", action="store_true", help="menos cargas (para pruebas)")
    args = p.parse_args(argv)
    salida = Path(args.salida)
    salida.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({"font.family": "DejaVu Sans", "axes.titlepad": 8})

    cargas = cargas_aleatorias(60 if args.rapido else 500)
    partes = [f"Resultados generados con: {equipo()}", "",
              e1_escenarios(salida), "", e2_aleatorias(salida, cargas), "",
              e3_quantum(salida, cargas), "", e4_convoy(salida), "", e5_inanicion(salida), "",
              e6_tiempos(salida, args.rapido)]
    texto = "\n".join(partes)
    (salida / "resumen.txt").write_text(texto + "\n", encoding="utf-8")
    print(texto)
    print(f"\nArchivos generados en {salida}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
