"""Validacion del motor con ejercicios resueltos y publicados en la bibliografia del curso (Fase III).

Los valores esperados se copiaron de los libros, no del simulador:
- Stallings (2018), Operating Systems, 9.a ed., tabla 9.5: cinco procesos A-E.
- Tanenbaum y Bos (2015), Modern Operating Systems, 4.a ed., seccion 2.4.3: trabajos A-D.

Ejecutar desde la raiz del repositorio:  python -m unittest discover -s pruebas -v
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src" / "codigo_fuente"))

from planificpu.algoritmos import simular
from planificpu.modelos import Proceso


def stallings():
    # proceso, llegada, tiempo de servicio (rafaga)
    return [Proceso("A", 0, 3), Proceso("B", 2, 6), Proceso("C", 4, 4),
            Proceso("D", 6, 5), Proceso("E", 8, 2)]


def secuencia(r):
    """Gantt en una cadena con una letra por unidad de tiempo ('-' = ocio)."""
    return "".join((s.pid or "-") * s.duracion for s in r.gantt)


class TestStallingsTabla95(unittest.TestCase):
    """Tiempos de fin y de retorno (turnaround) de la tabla 9.5 de Stallings."""

    CASOS = {
        # nombre: (algoritmo, quantum, expropiativo, fin A..E, retorno A..E, retorno promedio)
        "FCFS": ("FCFS", None, False, [3, 9, 13, 18, 20], [3, 7, 9, 12, 12], 8.60),
        "RR q=1": ("Round Robin", 1, False, [4, 18, 17, 20, 15], [4, 16, 13, 14, 7], 10.80),
        "RR q=4": ("Round Robin", 4, False, [3, 17, 11, 20, 19], [3, 15, 7, 14, 11], 10.00),
        "SPN (SJF)": ("SJF", None, False, [3, 9, 15, 20, 11], [3, 7, 11, 14, 3], 7.60),
        "SRT (SRTF)": ("SJF", None, True, [3, 15, 8, 20, 10], [3, 13, 4, 14, 2], 7.20),
    }

    def test_tiempos_de_fin_y_retorno(self):
        for nombre, (alg, q, exp, fin, retorno, promedio) in self.CASOS.items():
            with self.subTest(algoritmo=nombre):
                r = simular(stallings(), alg, q, exp)
                self.assertEqual([p.fin for p in r.procesos], fin)
                self.assertEqual([p.retorno for p in r.procesos], retorno)
                self.assertAlmostEqual(r.retorno_promedio, promedio)

    def test_secuencia_round_robin_q1(self):
        # orden unidad por unidad que produce los tiempos de la tabla (llegadas antes que el expropiado)
        r = simular(stallings(), "Round Robin", 1)
        self.assertEqual(secuencia(r), "AABABCBDCBEDCBEDCBDD")

    def test_secuencia_srt(self):
        r = simular(stallings(), "SJF", expropiativo=True)
        self.assertEqual(secuencia(r), "AAABCCCCEEBBBBBDDDDD")


class TestTanenbaum(unittest.TestCase):
    """Tanenbaum: A=8, B=4, C=4, D=4 llegan juntos; promedio de retorno 14 (FCFS) y 11 (SJF)."""

    def setUp(self):
        self.ps = [Proceso("A", 0, 8), Proceso("B", 0, 4), Proceso("C", 0, 4), Proceso("D", 0, 4)]

    def test_fcfs(self):
        r = simular(self.ps, "FCFS")
        self.assertEqual([p.retorno for p in r.procesos], [8, 12, 16, 20])
        self.assertAlmostEqual(r.retorno_promedio, 14.0)

    def test_sjf(self):
        r = simular(self.ps, "SJF")
        self.assertEqual(secuencia(r), "BBBBCCCCDDDDAAAAAAAA")
        self.assertAlmostEqual(r.retorno_promedio, 11.0)


if __name__ == "__main__":
    unittest.main()
