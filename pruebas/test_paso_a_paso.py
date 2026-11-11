"""Pruebas del modo paso a paso (Fase II).

Ejecutar desde la raiz del repositorio:  python -m unittest discover -s pruebas -v
"""

import random
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src" / "codigo_fuente"))

from planificpu.algoritmos import simular
from planificpu.modelos import Proceso
from planificpu.paso_a_paso import EJECUCION, LISTO, NUEVO, TERMINADO, trazar


def traza(ps, algoritmo, quantum=None, expropiativo=False):
    r = simular(ps, algoritmo, quantum, expropiativo)
    return r, trazar(ps, r)


def texto(instante):
    return " | ".join(instante.eventos)


class TestEjemploFicha(unittest.TestCase):
    """Ejemplo de la ficha tecnica con FCFS: P1(0,5) P2(1,3) P3(2,4)."""

    def setUp(self):
        ps = [Proceso("P1", 0, 5, 2), Proceso("P2", 1, 3, 1), Proceso("P3", 2, 4, 3)]
        self.r, self.ins = traza(ps, "FCFS")

    def test_un_instante_por_unidad_mas_el_final(self):
        self.assertEqual(len(self.ins), self.r.tiempo_total + 1)
        self.assertEqual([i.t for i in self.ins], list(range(13)))

    def test_cola_de_listos(self):
        self.assertEqual(self.ins[0].cola, [])
        self.assertEqual(self.ins[1].cola, ["P2"])
        self.assertEqual(self.ins[2].cola, ["P2", "P3"])
        self.assertEqual(self.ins[5].en_cpu, "P2")
        self.assertEqual(self.ins[5].cola, ["P3"])

    def test_eventos_en_t5(self):
        eventos = texto(self.ins[5])
        self.assertIn("P1 termina", eventos)
        self.assertIn("Cambio de contexto: P1 -> P2", eventos)

    def test_estados_y_restante(self):
        i = self.ins[6]
        self.assertEqual(i.estados, {"P1": TERMINADO, "P2": EJECUCION, "P3": LISTO})
        self.assertEqual(i.restante, {"P1": 0, "P2": 2, "P3": 4})

    def test_instante_final(self):
        final = self.ins[-1]
        self.assertIsNone(final.en_cpu)
        self.assertEqual(set(final.estados.values()), {TERMINADO})
        self.assertIn("Fin de la simulación", texto(final))
        self.assertEqual(final.cambios_contexto, self.r.cambios_contexto)


class TestOrdenDeLaCola(unittest.TestCase):
    def test_round_robin_llegadas_antes_que_el_expropiado(self):
        ps = [Proceso("P1", 0, 5), Proceso("P2", 1, 3), Proceso("P3", 2, 1)]
        _, ins = traza(ps, "Round Robin", quantum=2)
        self.assertEqual(ins[1].cola, ["P2"])
        self.assertEqual(ins[2].en_cpu, "P2")
        self.assertEqual(ins[2].cola, ["P3", "P1"])   # P3 llego antes de que P1 vuelva

    def test_round_robin_quantum_agotado_con_cola_vacia(self):
        _, ins = traza([Proceso("A", 0, 5)], "Round Robin", quantum=2)
        self.assertIn("Quantum agotado", texto(ins[2]))
        self.assertIn("Quantum agotado", texto(ins[4]))
        self.assertNotIn("Quantum agotado", texto(ins[3]))

    def test_sjf_ordena_por_rafaga(self):
        ps = [Proceso("P1", 0, 6), Proceso("P2", 1, 4), Proceso("P3", 2, 2)]
        _, ins = traza(ps, "SJF")
        self.assertEqual(ins[2].cola, ["P3", "P2"])
        self.assertEqual(ins[6].en_cpu, "P3")

    def test_prioridad_ordena_por_numero_menor(self):
        ps = [Proceso("P1", 0, 3, 2), Proceso("P2", 1, 2, 3), Proceso("P3", 1, 2, 1)]
        _, ins = traza(ps, "Prioridad")
        self.assertEqual(ins[1].cola, ["P3", "P2"])

    def test_srtf_registra_la_expropiacion(self):
        ps = [Proceso("P1", 0, 8), Proceso("P2", 1, 4)]
        _, ins = traza(ps, "SJF", expropiativo=True)
        self.assertEqual(ins[1].en_cpu, "P2")
        self.assertIn("P1 es expropiado (le faltan 7)", texto(ins[1]))
        self.assertEqual(ins[1].cola, ["P1"])


class TestCasosLimite(unittest.TestCase):
    def test_cpu_ociosa_y_proceso_nuevo(self):
        _, ins = traza([Proceso("P1", 0, 2), Proceso("P2", 5, 1)], "FCFS")
        self.assertIsNone(ins[3].en_cpu)
        self.assertIn("CPU ociosa", texto(ins[2]))
        self.assertEqual(texto(ins[3]), "")             # el ocio continua sin eventos nuevos
        self.assertEqual(ins[3].estados["P2"], NUEVO)
        self.assertIn("P2 llega", texto(ins[5]))
        self.assertEqual(ins[5].cambios_contexto, 1)    # P1 -> P2 aunque hubo ocio

    def test_todos_llegan_al_mismo_tiempo(self):
        ps = [Proceso("A", 0, 2), Proceso("B", 0, 2), Proceso("C", 0, 2)]
        _, ins = traza(ps, "FCFS")
        self.assertEqual(ins[0].en_cpu, "A")
        self.assertEqual(ins[0].cola, ["B", "C"])       # orden de registro

    def test_quantum_mayor_que_todas_las_rafagas_equivale_a_fcfs(self):
        ps = [Proceso("P1", 0, 5), Proceso("P2", 1, 3), Proceso("P3", 2, 4)]
        _, rr = traza(ps, "Round Robin", quantum=50)
        _, fcfs = traza(ps, "FCFS")
        self.assertEqual([i.en_cpu for i in rr], [i.en_cpu for i in fcfs])
        self.assertEqual([i.cola for i in rr], [i.cola for i in fcfs])


class TestCoherenciaConElMotor(unittest.TestCase):
    """La traza debe coincidir con el Gantt del motor en escenarios aleatorios."""

    CONFIGS = [("FCFS", None, False), ("SJF", None, False), ("SJF", None, True),
               ("Prioridad", None, False), ("Prioridad", None, True),
               ("Round Robin", 1, False), ("Round Robin", 3, False)]

    def test_escenarios_aleatorios(self):
        azar = random.Random(2026)
        for caso in range(60):
            ps = [Proceso(f"P{i + 1}", azar.randint(0, 12), azar.randint(1, 6),
                          azar.randint(0, 4)) for i in range(azar.randint(1, 7))]
            for alg, q, exp in self.CONFIGS:
                with self.subTest(caso=caso, algoritmo=alg, quantum=q, expropiativo=exp):
                    r, ins = traza(ps, alg, q, exp)
                    cpu = [s.pid for s in r.gantt for _ in range(s.duracion)]
                    self.assertEqual([i.en_cpu for i in ins[:-1]], cpu)
                    self.assertEqual(ins[-1].cambios_contexto, r.cambios_contexto)
                    for i in ins:
                        self.assertNotIn(i.en_cpu, i.cola)
                        listos = {pid for pid, e in i.estados.items() if e == LISTO}
                        self.assertEqual(set(i.cola), listos)
                    if alg != "Round Robin":
                        self._despacho_respeta_la_cola(ps, alg, exp, ins)

    def _despacho_respeta_la_cola(self, ps, alg, exp, ins):
        """Al despachar (o en cada unidad si es expropiativo), el proceso elegido
        no puede tener peor clave que el primero de la cola."""
        datos = {p.pid: p for p in ps}

        def clave(pid, i):
            p = datos[pid]
            return {"FCFS": p.llegada, "SJF": i.restante[pid], "Prioridad": p.prioridad}[alg]

        for a, b in zip(ins, ins[1:]):
            despacho = b.en_cpu is not None and (b.en_cpu != a.en_cpu or exp)
            if despacho and b.cola:
                self.assertLessEqual(clave(b.en_cpu, b), clave(b.cola[0], b))


if __name__ == "__main__":
    unittest.main()
