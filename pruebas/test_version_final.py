"""Pruebas de las funciones agregadas en la version final (Fase III).

Metricas nuevas, exportacion CSV, modo consola, diagnostico del entorno,
ubicacion de la base de datos del ejecutable y rendimiento (RNF05).

Ejecutar desde la raiz del repositorio:  python -m unittest discover -s pruebas -v
"""

import contextlib
import io
import os
import random
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src" / "codigo_fuente"))

import main as punto_de_entrada
from planificpu import __version__, bd, consola, csv_io, diagnostico
from planificpu.algoritmos import comparar, simular
from planificpu.modelos import Proceso
from planificpu.paso_a_paso import trazar

FICHA = [Proceso("P1", 0, 5, 2), Proceso("P2", 1, 3, 1), Proceso("P3", 2, 4, 3)]
CINCO = RAIZ / "recursos" / "datos_ejemplo" / "ejemplo_cinco_procesos.csv"


def correr(*argumentos):
    """Ejecuta main.py con argumentos y devuelve (codigo, salida, errores)."""
    salida, errores = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(salida), contextlib.redirect_stderr(errores):
        try:
            codigo = punto_de_entrada.main(list(argumentos))
        except SystemExit as e:  # argparse (--version, errores de uso)
            codigo = e.code
    return codigo, salida.getvalue(), errores.getvalue()


class TestMetricasNuevas(unittest.TestCase):
    def test_ficha_tecnica(self):
        r = simular(FICHA, "FCFS")
        self.assertEqual(r.tiempo_total, 12)
        self.assertEqual(r.tiempo_ocioso, 0)
        self.assertAlmostEqual(r.utilizacion_cpu, 100.0)
        self.assertAlmostEqual(r.rendimiento, 0.25)
        self.assertEqual((r.espera_maxima, r.proceso_mayor_espera), (6, "P3"))

    def test_round_robin_reparte_la_espera(self):
        r = simular(FICHA, "Round Robin", 2)
        self.assertEqual((r.espera_maxima, r.proceso_mayor_espera), (7, "P1"))
        self.assertEqual(r.cambios_contexto, 6)

    def test_cpu_ociosa_al_inicio(self):
        r = simular([Proceso("A", 4, 4)], "FCFS")
        self.assertEqual((r.tiempo_total, r.tiempo_ocioso), (8, 4))
        self.assertAlmostEqual(r.utilizacion_cpu, 50.0)

    def test_exportacion_incluye_las_metricas_nuevas(self):
        with tempfile.TemporaryDirectory() as d:
            ruta = Path(d) / "resultados.csv"
            csv_io.exportar_resultados(ruta, comparar(FICHA, 2))
            texto = ruta.read_text(encoding="utf-8-sig")
        self.assertIn("Utilizacion de CPU (%);100,00", texto)
        self.assertIn("Rendimiento (procesos/u.t.);0,25", texto)
        self.assertIn("Espera maxima;6;P3", texto)
        self.assertIn("Round Robin (q=2);5,67;9,67;1,00;7;6;100,00;0,25", texto)


class TestModoConsola(unittest.TestCase):
    def test_simulacion_con_gantt_en_texto(self):
        codigo, salida, _ = correr("--consola", "-a", "rr", "-q", "2")
        self.assertEqual(codigo, 0)
        self.assertIn("Algoritmo: Round Robin (q=2)", salida)
        self.assertIn("|  P1  |  P2  |  P3  |  P1  | P2 |  P3  | P1 |", salida)
        self.assertIn("0      2      4      6      8    9      11   12", salida)
        self.assertIn("| Promedio |         |        |           |        |     |   5,67 |", salida)
        self.assertIn("Utilización de CPU: 100,00 %", salida)

    def test_srtf_y_traza(self):
        codigo, salida, _ = correr("--consola", str(CINCO), "-a", "srtf", "--traza")
        self.assertEqual(codigo, 0)
        self.assertIn("SJF expropiativo (SRTF)", salida)
        self.assertIn("t=  1 | CPU: P2 (faltan 4)", salida)
        self.assertIn("Cambio de contexto: P1 es expropiado (le faltan 7) y entra P2", salida)
        self.assertIn("Fin de la simulación", salida)

    def test_comparar_y_exportar(self):
        with tempfile.TemporaryDirectory() as d:
            destino = Path(d) / "comparacion.csv"
            codigo, salida, _ = correr("--consola", str(CINCO), "--comparar", "-q", "3",
                                       "--exportar", str(destino))
            self.assertEqual(codigo, 0)
            self.assertTrue(destino.exists())
        self.assertIn("Mejor en cada métrica", salida)
        self.assertIn("Espera promedio: SJF (7,00)", salida)
        self.assertIn("Respuesta promedio: Round Robin (q=3) (3,80)", salida)

    def test_cpu_ociosa_en_el_gantt_de_texto(self):
        r = simular([Proceso("A", 0, 2), Proceso("B", 5, 1)], "FCFS")
        self.assertEqual(consola.gantt_texto(r).splitlines()[1:], [
            "|  A   |    --   | B |", "+------+---------+---+", "0      2         5   6"])

    def test_errores_devuelven_codigo_2(self):
        codigo, _, errores = correr("--consola", "no_existe.csv")
        self.assertEqual(codigo, 2)
        self.assertIn("no se encuentra el archivo", errores)
        with tempfile.TemporaryDirectory() as d:
            malo = Path(d) / "malo.csv"
            malo.write_text("pid,llegada,rafaga\nP1,0,cero\n", encoding="utf-8")
            codigo, _, errores = correr("--consola", str(malo))
        self.assertEqual(codigo, 2)
        self.assertIn("deben ser enteros", errores)
        codigo, _, _ = correr("--consola", "-a", "rr", "-q", "0")
        self.assertEqual(codigo, 2)

    def test_version(self):
        codigo, salida, _ = correr("--version")
        self.assertEqual(codigo, 0)
        self.assertEqual(salida.strip(), f"PlanifiCPU {__version__}")
        self.assertEqual(__version__, "2.0.0")


class TestDiagnostico(unittest.TestCase):
    def test_entorno_listo(self):
        salida = io.StringIO()
        codigo = diagnostico.ejecutar(salida, probar_ventana=False)
        texto = salida.getvalue()
        self.assertEqual(codigo, 0, texto)
        for linea in ("Python", "SQLite", "Esquema de la BD", "Ejercicio de la ficha",
                      "Algoritmos", "Paso a paso"):
            self.assertIn(linea, texto)
        self.assertNotIn("[FALLA]", texto)

    def test_reporta_falla(self):
        with mock.patch.object(diagnostico, "_motor",
                               return_value=[diagnostico.Chequeo("Motor", "x", "FALLA")]):
            self.assertEqual(diagnostico.ejecutar(io.StringIO(), probar_ventana=False), 1)


class TestUbicacionBaseDatos(unittest.TestCase):
    def test_variable_de_entorno(self):
        with tempfile.TemporaryDirectory() as d, \
                mock.patch.dict(os.environ, {"PLANIFICPU_BD": str(Path(d) / "x" / "h.db")}):
            self.assertEqual(bd.ruta_bd_por_defecto(), Path(d) / "x" / "h.db")
            base = bd.BaseDatos()                  # crea la carpeta si no existe
            base.guardar_escenario("Prueba", FICHA)
            base.cerrar()
            self.assertTrue((Path(d) / "x" / "h.db").exists())

    def test_ejecutable_guarda_en_appdata(self):
        entorno = {k: v for k, v in os.environ.items() if k != "PLANIFICPU_BD"}
        entorno["APPDATA"] = str(Path("C:/Users/ana/AppData/Roaming"))
        with mock.patch.object(bd, "EMPAQUETADO", True), mock.patch.dict(os.environ, entorno,
                                                                         clear=True):
            self.assertEqual(bd.ruta_bd_por_defecto(),
                             Path("C:/Users/ana/AppData/Roaming") / "PlanifiCPU" / "planificpu.db")

    def test_codigo_fuente_guarda_junto_al_esquema(self):
        entorno = {k: v for k, v in os.environ.items() if k != "PLANIFICPU_BD"}
        with mock.patch.object(bd, "EMPAQUETADO", False), mock.patch.dict(os.environ, entorno,
                                                                          clear=True):
            self.assertEqual(bd.ruta_bd_por_defecto(), bd.RUTA_ESQUEMA.parent / "planificpu.db")


class TestAnalisisDeResultados(unittest.TestCase):
    def test_genera_tablas_y_graficas(self):
        import analisis_resultados
        with tempfile.TemporaryDirectory() as d, contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(analisis_resultados.main(["--salida", d, "--rapido"]), 0)
            archivos = {p.name for p in Path(d).iterdir()}
            resumen = (Path(d) / "resumen.txt").read_text(encoding="utf-8")
        for nombre in ("e1_espera_por_escenario.png", "e2_cargas_aleatorias.png",
                       "e3_sensibilidad_quantum.png", "e4_efecto_convoy.png", "e5_inanicion.png",
                       "e1_comparacion_escenarios.csv", "e6_tiempos_ms.csv", "resumen.txt"):
            self.assertIn(nombre, archivos)
        # SRTF tiene la menor espera promedio en el 100 % de las cargas aleatorias
        fila_srtf = next(l for l in resumen.splitlines() if l.startswith("SRTF "))
        self.assertIn("| 100,00", fila_srtf)


class TestRendimiento(unittest.TestCase):
    """RNF05: una simulacion de hasta 50 procesos se muestra en menos de 1 segundo."""

    def test_50_procesos_en_menos_de_un_segundo(self):
        azar = random.Random(50)
        ps = [Proceso(f"P{i + 1}", azar.randint(0, 100), azar.randint(1, 20), azar.randint(0, 9))
              for i in range(50)]
        for alg, q, exp in [("FCFS", None, False), ("SJF", None, True),
                            ("Prioridad", None, True), ("Round Robin", 1, False)]:
            with self.subTest(algoritmo=alg, quantum=q, expropiativo=exp):
                inicio = time.perf_counter()
                r = simular(ps, alg, q, exp)
                trazar(ps, r)                       # incluye el modo paso a paso
                self.assertLess(time.perf_counter() - inicio, 1.0)
        inicio = time.perf_counter()
        comparar(ps, 2, True)
        self.assertLess(time.perf_counter() - inicio, 1.0)


if __name__ == "__main__":
    unittest.main()
