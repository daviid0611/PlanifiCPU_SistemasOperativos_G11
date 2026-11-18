"""Propiedades que todo planificador correcto debe cumplir (Fase III).

En lugar de comparar contra un resultado escrito a mano, se generan escenarios
aleatorios (semilla fija, reproducibles) y se verifican reglas de la teoria de
Sistemas Operativos: el Gantt no tiene huecos ni solapes, cada proceso recibe
exactamente su rafaga, la CPU no queda ociosa si hay procesos listos, SRTF da la
menor espera promedio posible, etc.

Ejecutar desde la raiz del repositorio:  python -m unittest discover -s pruebas -v
"""

import itertools
import random
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src" / "codigo_fuente"))

from planificpu.algoritmos import simular
from planificpu.modelos import Proceso

CONFIGS = [("FCFS", None, False), ("SJF", None, False), ("SJF", None, True),
           ("Prioridad", None, False), ("Prioridad", None, True),
           ("Round Robin", 1, False), ("Round Robin", 2, False), ("Round Robin", 4, False)]
NO_EXPROPIATIVOS = {("FCFS", False), ("SJF", False), ("Prioridad", False)}


def escenarios(cantidad, semilla, max_procesos=8, max_llegada=15, max_rafaga=8):
    azar = random.Random(semilla)
    for _ in range(cantidad):
        yield [Proceso(f"P{i + 1}", azar.randint(0, max_llegada), azar.randint(1, max_rafaga),
                       azar.randint(0, 4)) for i in range(azar.randint(1, max_procesos))]


def cpu_por_unidad(r):
    return [s.pid for s in r.gantt for _ in range(s.duracion)]


class TestPropiedadesDelGantt(unittest.TestCase):
    def test_invariantes_en_escenarios_aleatorios(self):
        for n, ps in enumerate(escenarios(150, semilla=11)):
            datos = {p.pid: p for p in ps}
            for alg, q, exp in CONFIGS:
                with self.subTest(escenario=n, algoritmo=alg, quantum=q, expropiativo=exp):
                    r = simular(ps, alg, q, exp)
                    g = r.gantt
                    # 1. empieza en 0, sin huecos, sin tramos vacios y sin tramos repetidos
                    self.assertEqual(g[0].inicio, 0)
                    for a, b in zip(g, g[1:]):
                        self.assertEqual(a.fin, b.inicio)
                        self.assertNotEqual(a.pid, b.pid)
                    self.assertTrue(all(s.duracion > 0 for s in g))

                    # 2. cada proceso recibe exactamente su rafaga y nunca antes de llegar
                    cpu = cpu_por_unidad(r)
                    for p in ps:
                        unidades = [t for t, pid in enumerate(cpu) if pid == p.pid]
                        self.assertEqual(len(unidades), p.rafaga)
                        self.assertGreaterEqual(min(unidades), p.llegada)

                    # 3. la CPU solo esta ociosa si no hay procesos listos
                    hechos = {p.pid: 0 for p in ps}
                    for t, pid in enumerate(cpu):
                        if pid is None:
                            listos = [x for x in ps if x.llegada <= t and hechos[x.pid] < x.rafaga]
                            self.assertEqual(listos, [], f"CPU ociosa en t={t} con procesos listos")
                        else:
                            hechos[pid] += 1

                    # 4. definiciones de las metricas
                    for m in r.procesos:
                        p = datos[m.pid]
                        self.assertEqual(m.retorno, m.fin - p.llegada)
                        self.assertEqual(m.espera, m.retorno - p.rafaga)
                        self.assertEqual(m.respuesta, m.inicio - p.llegada)
                        self.assertGreaterEqual(m.respuesta, 0)
                        self.assertLessEqual(m.respuesta, m.espera)

                    # 5. utilizacion: la CPU trabaja exactamente la suma de las rafagas
                    self.assertEqual(r.tiempo_ocupado, sum(p.rafaga for p in ps))
                    self.assertAlmostEqual(r.utilizacion_cpu,
                                           100 * r.tiempo_ocupado / r.tiempo_total)
                    self.assertAlmostEqual(r.rendimiento, len(ps) / r.tiempo_total)
                    self.assertEqual(r.espera_maxima, max(m.espera for m in r.procesos))

                    # 6. cambios de contexto: al menos uno por cada proceso adicional
                    self.assertGreaterEqual(r.cambios_contexto, len(ps) - 1)

    def test_no_expropiativos_ejecutan_cada_proceso_de_una_vez(self):
        for ps in escenarios(150, semilla=12):
            for alg, q, exp in CONFIGS:
                if (alg, exp) not in NO_EXPROPIATIVOS:
                    continue
                with self.subTest(algoritmo=alg):
                    r = simular(ps, alg, q, exp)
                    tramos = [s.pid for s in r.gantt if s.pid is not None]
                    self.assertEqual(len(tramos), len(ps))      # un solo tramo por proceso
                    for m in r.procesos:
                        self.assertEqual(m.respuesta, m.espera)
                    self.assertEqual(r.cambios_contexto, len(ps) - 1)

    def test_expropiativos_respetan_la_regla_de_seleccion(self):
        """SRTF y Prioridad expropiativa: en cada unidad corre el de menor clave; ante un
        empate sigue el que ya estaba en la CPU, luego el que llego primero y luego el
        que se registro primero (reglas de calculo del README)."""
        for ps in escenarios(150, semilla=13, max_rafaga=5):
            for alg in ("SJF", "Prioridad"):
                with self.subTest(algoritmo=alg):
                    r = simular(ps, alg, expropiativo=True)
                    restante = {p.pid: p.rafaga for p in ps}
                    anterior = None
                    for t, pid in enumerate(cpu_por_unidad(r)):
                        if pid is None:
                            anterior = None
                            continue
                        listos = [p for p in ps if p.llegada <= t and restante[p.pid] > 0]
                        clave = ((lambda p: restante[p.pid]) if alg == "SJF"
                                 else (lambda p: p.prioridad))
                        esperado = min(listos, key=lambda p: (clave(p), p.pid != anterior,
                                                              p.llegada, ps.index(p)))
                        self.assertEqual(pid, esperado.pid, f"t={t}")
                        restante[pid] -= 1
                        anterior = pid

    def test_no_expropiativos_respetan_la_regla_de_seleccion(self):
        """Al liberarse la CPU se elige la menor clave; empates por llegada y registro."""
        for ps in escenarios(150, semilla=18, max_rafaga=4):
            for alg in ("SJF", "Prioridad"):
                with self.subTest(algoritmo=alg):
                    r = simular(ps, alg)
                    hechos = set()
                    for s in r.gantt:
                        if s.pid is None:
                            continue
                        listos = [p for p in ps if p.llegada <= s.inicio and p.pid not in hechos]
                        clave = ((lambda p: p.rafaga) if alg == "SJF" else (lambda p: p.prioridad))
                        esperado = min(listos, key=lambda p: (clave(p), p.llegada, ps.index(p)))
                        self.assertEqual(s.pid, esperado.pid, f"t={s.inicio}")
                        hechos.add(s.pid)


class TestPropiedadesTeoricas(unittest.TestCase):
    def test_fcfs_atiende_por_orden_de_llegada(self):
        for ps in escenarios(100, semilla=14):
            r = simular(ps, "FCFS")
            orden = [s.pid for s in r.gantt if s.pid is not None]
            esperado = [p.pid for p in sorted(ps, key=lambda p: (p.llegada, ps.index(p)))]
            self.assertEqual(orden, esperado)

    def test_round_robin_con_quantum_grande_es_fcfs(self):
        for ps in escenarios(100, semilla=15):
            q = max(p.rafaga for p in ps)
            rr = simular(ps, "Round Robin", q)
            fcfs = simular(ps, "FCFS")
            self.assertEqual(cpu_por_unidad(rr), cpu_por_unidad(fcfs))

    def test_srtf_da_la_menor_espera_promedio(self):
        """SRTF es optimo para la espera promedio (Silberschatz, sec. 5.3.2)."""
        for n, ps in enumerate(escenarios(200, semilla=16)):
            srtf = simular(ps, "SJF", expropiativo=True).espera_promedio
            for alg, q, exp in CONFIGS:
                with self.subTest(escenario=n, algoritmo=alg, quantum=q, expropiativo=exp):
                    self.assertLessEqual(srtf, simular(ps, alg, q, exp).espera_promedio + 1e-9)

    def test_sjf_es_optimo_cuando_todos_llegan_juntos(self):
        """Ningun orden posible de los procesos da menor espera promedio que SJF."""
        azar = random.Random(17)
        for _ in range(40):
            ps = [Proceso(f"P{i + 1}", 0, azar.randint(1, 9)) for i in range(azar.randint(2, 6))]
            sjf = simular(ps, "SJF").espera_promedio
            for orden in itertools.permutations(ps):
                t, espera = 0, 0
                for p in orden:
                    espera += t
                    t += p.rafaga
                self.assertLessEqual(sjf, espera / len(ps) + 1e-9)

    def test_cpu_ociosa_reduce_la_utilizacion(self):
        r = simular([Proceso("A", 0, 2), Proceso("B", 6, 2)], "FCFS")
        self.assertEqual(r.tiempo_ocioso, 4)
        self.assertAlmostEqual(r.utilizacion_cpu, 50.0)
        self.assertAlmostEqual(r.rendimiento, 0.25)


if __name__ == "__main__":
    unittest.main()
