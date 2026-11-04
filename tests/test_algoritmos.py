"""Pruebas del motor de planificacion con ejercicios de resultado conocido.

Ejecutar:  python -m unittest discover -s tests -v
"""

import tempfile
import unittest
from pathlib import Path

from planificpu import csv_io
from planificpu.algoritmos import comparar, simular
from planificpu.bd import BaseDatos
from planificpu.modelos import ErrorValidacion, Proceso


def gantt(r):
    return [(s.pid, s.inicio, s.fin) for s in r.gantt]


class TestFCFS(unittest.TestCase):
    def test_ejemplo_ficha_tecnica(self):
        ps = [Proceso("P1", 0, 5), Proceso("P2", 1, 3), Proceso("P3", 2, 4)]
        r = simular(ps, "FCFS")
        self.assertEqual(gantt(r), [("P1", 0, 5), ("P2", 5, 8), ("P3", 8, 12)])
        self.assertEqual([p.espera for p in r.procesos], [0, 4, 6])
        self.assertEqual([p.retorno for p in r.procesos], [5, 7, 10])
        self.assertAlmostEqual(r.espera_promedio, 10 / 3)
        self.assertAlmostEqual(r.retorno_promedio, 22 / 3)

    def test_cpu_ociosa(self):
        r = simular([Proceso("A", 2, 3), Proceso("B", 10, 1)], "FCFS")
        self.assertEqual(gantt(r), [(None, 0, 2), ("A", 2, 5), (None, 5, 10), ("B", 10, 11)])
        self.assertEqual(r.cambios_contexto, 1)


class TestSJF(unittest.TestCase):
    def test_no_expropiativo(self):
        # Silberschatz: P1=6, P2=8, P3=7, P4=3 en t=0 -> espera promedio 7
        ps = [Proceso("P1", 0, 6), Proceso("P2", 0, 8), Proceso("P3", 0, 7), Proceso("P4", 0, 3)]
        r = simular(ps, "SJF")
        self.assertEqual([s[0] for s in gantt(r)], ["P4", "P1", "P3", "P2"])
        self.assertAlmostEqual(r.espera_promedio, 7.0)

    def test_expropiativo_srtf(self):
        # Silberschatz: espera promedio 6,5
        ps = [Proceso("P1", 0, 8), Proceso("P2", 1, 4), Proceso("P3", 2, 9), Proceso("P4", 3, 5)]
        r = simular(ps, "SJF", expropiativo=True)
        self.assertEqual(gantt(r), [("P1", 0, 1), ("P2", 1, 5), ("P4", 5, 10),
                                    ("P1", 10, 17), ("P3", 17, 26)])
        self.assertAlmostEqual(r.espera_promedio, 6.5)


class TestRoundRobin(unittest.TestCase):
    def test_quantum_4(self):
        # Silberschatz: P1=24, P2=3, P3=3, q=4 -> espera promedio 17/3
        ps = [Proceso("P1", 0, 24), Proceso("P2", 0, 3), Proceso("P3", 0, 3)]
        r = simular(ps, "Round Robin", quantum=4)
        self.assertEqual(gantt(r)[:4], [("P1", 0, 4), ("P2", 4, 7), ("P3", 7, 10), ("P1", 10, 30)])
        self.assertAlmostEqual(r.espera_promedio, 17 / 3)

    def test_llegadas_entran_antes_que_el_expropiado(self):
        ps = [Proceso("P1", 0, 5), Proceso("P2", 1, 3), Proceso("P3", 2, 4)]
        r = simular(ps, "Round Robin", quantum=2)
        self.assertEqual([s[0] for s in gantt(r)], ["P1", "P2", "P3", "P1", "P2", "P3", "P1"])

    def test_quantum_invalido(self):
        with self.assertRaises(ValueError):
            simular([Proceso("P1", 0, 3)], "Round Robin", quantum=0)


class TestPrioridad(unittest.TestCase):
    def test_no_expropiativa(self):
        # Silberschatz: espera promedio 8,2
        ps = [Proceso("P1", 0, 10, 3), Proceso("P2", 0, 1, 1), Proceso("P3", 0, 2, 4),
              Proceso("P4", 0, 1, 5), Proceso("P5", 0, 5, 2)]
        r = simular(ps, "Prioridad")
        self.assertEqual([s[0] for s in gantt(r)], ["P2", "P5", "P1", "P3", "P4"])
        self.assertAlmostEqual(r.espera_promedio, 8.2)

    def test_expropiativa(self):
        ps = [Proceso("A", 0, 4, 3), Proceso("B", 1, 2, 1)]
        r = simular(ps, "Prioridad", expropiativo=True)
        self.assertEqual(gantt(r), [("A", 0, 1), ("B", 1, 3), ("A", 3, 6)])
        self.assertEqual(r.procesos[0].respuesta, 0)
        self.assertEqual(r.cambios_contexto, 2)


class TestValidacionYArchivos(unittest.TestCase):
    def test_pid_repetido(self):
        with self.assertRaises(ErrorValidacion):
            simular([Proceso("P1", 0, 2), Proceso("P1", 1, 2)], "FCFS")

    def test_rafaga_cero(self):
        with self.assertRaises(ErrorValidacion):
            simular([Proceso("P1", 0, 0)], "FCFS")

    def test_csv_ida_y_vuelta(self):
        ps = [Proceso("P1", 0, 5, 2), Proceso("P2", 1, 3, 1)]
        with tempfile.TemporaryDirectory() as d:
            ruta = Path(d) / "escenario.csv"
            csv_io.guardar_procesos(ruta, ps)
            self.assertEqual(csv_io.cargar_procesos(ruta), ps)
            csv_io.exportar_resultados(Path(d) / "res.csv", comparar(ps, 2))

    def test_bd_guarda_escenario_y_simulacion(self):
        ps = [Proceso("P1", 0, 5), Proceso("P2", 1, 3), Proceso("P3", 2, 4)]
        with tempfile.TemporaryDirectory() as d:
            bd = BaseDatos(Path(d) / "prueba.db")
            id_esc = bd.guardar_escenario("Ficha", ps)
            bd.guardar_simulacion(id_esc, simular(ps, "FCFS"))
            nombre, cargados = bd.cargar_escenario(id_esc)
            self.assertEqual((nombre, cargados), ("Ficha", ps))
            hist = bd.listar_simulaciones()
            self.assertEqual(hist[0]["algoritmo"], "FCFS")
            self.assertAlmostEqual(hist[0]["espera_promedio"], 10 / 3)
            bd.eliminar_escenario(id_esc)
            self.assertEqual(bd.listar_simulaciones(), [])
            bd.cerrar()


if __name__ == "__main__":
    unittest.main()
