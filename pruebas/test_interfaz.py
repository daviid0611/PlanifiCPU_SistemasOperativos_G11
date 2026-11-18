"""Pruebas de la interfaz grafica (Fase III).

Abren la ventana real de PlanifiCPU (oculta), pulsan los mismos botones que el
usuario y revisan lo que muestran las tablas y etiquetas. Los dialogos de archivo
se reemplazan por rutas temporales. Si el equipo no tiene pantalla (por ejemplo un
servidor Linux sin Xvfb) las pruebas se omiten.

Ejecutar desde la raiz del repositorio:  python -m unittest discover -s pruebas -v
"""

import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src" / "codigo_fuente"))

CINCO = RAIZ / "recursos" / "datos_ejemplo" / "ejemplo_cinco_procesos.csv"

try:
    import tkinter as tk
    _raiz = tk.Tk()
    _raiz.destroy()
    HAY_PANTALLA, MOTIVO = True, ""
except Exception as e:  # ImportError o TclError (sin pantalla)
    HAY_PANTALLA, MOTIVO = False, f"sin interfaz gráfica disponible: {e}"


@unittest.skipUnless(HAY_PANTALLA, MOTIVO)
class TestInterfaz(unittest.TestCase):
    def setUp(self):
        from planificpu import gui
        self.gui = gui
        self.dir = tempfile.TemporaryDirectory()
        self.app = gui.App(ruta_bd=Path(self.dir.name) / "interfaz.db")
        self.app.withdraw()

    def tearDown(self):
        self.app._cerrar()
        self.dir.cleanup()

    # ----------------------------------------------------------- utilidades
    def filas(self, tabla):
        return [tuple(str(v) for v in tabla.item(i, "values")) for i in tabla.get_children()]

    def cargar_cinco(self):
        with mock.patch.object(self.gui.filedialog, "askopenfilename", return_value=str(CINCO)):
            self.app._cargar_csv()

    def elegir(self, algoritmo, quantum=None, expropiativo=False):
        self.app.var_algoritmo.set(algoritmo)
        if quantum is not None:
            self.app.var_quantum.set(str(quantum))
        self.app.var_expropiativo.set(expropiativo)
        self.app._actualizar_opciones()

    # ---------------------------------------------------------------- casos
    def test_simular_ejemplo_de_la_ficha(self):
        self.app._cargar_ejemplo()
        self.app._simular()
        metricas = self.filas(self.app.tabla_met)
        self.assertEqual(len(metricas), 4)
        self.assertEqual(metricas[-1][6:], ("3,33", "7,33", "3,33"))
        self.assertIn("Utilización de CPU: 100,00 %", self.app.lbl_resumen_met.cget("text"))
        self.assertIn("Espera máxima: 6 (P3)", self.app.lbl_resumen_met.cget("text"))
        self.assertEqual([f[1] for f in self.filas(self.app.tabla_tramos)], ["P1", "P2", "P3"])
        self.assertEqual(len(self.filas(self.app.tabla_hist)), 1)
        self.assertIn("espera promedio 3,33", self.app.barra.cget("text"))

    def test_comparar_los_cuatro_algoritmos(self):
        self.cargar_cinco()
        self.assertEqual(len(self.filas(self.app.tabla_procesos)), 5)
        self.elegir("Round Robin", 3)
        self.app._comparar()
        comp = self.filas(self.app.tabla_comp)
        self.assertEqual([f[0] for f in comp], ["FCFS", "SJF", "Round Robin (q=3)", "Prioridad"])
        self.assertEqual(comp[1], ("SJF", "7,00", "12,60", "7,00", "17", "4", "100,00 %"))
        mejor = [self.app.tabla_comp.item(i, "tags") for i in self.app.tabla_comp.get_children()]
        self.assertIn("mejor", mejor[1])
        self.assertIn("Menor espera promedio: SJF (7,00)",
                      self.app.lbl_conclusion_comp.cget("text"))
        self.assertEqual(self.app.pestanas.select(), str(self.app.tab_comp))
        self.assertEqual(len(self.filas(self.app.tabla_hist)), 4)

    def test_paso_a_paso_round_robin(self):
        self.cargar_cinco()
        self.elegir("Round Robin", 3)
        self.app._simular(paso_a_paso=True)
        self.assertEqual(self.app.pestanas.select(), str(self.app.tab_paso))
        self.app._ir_a(7)
        self.assertEqual(self.app.lbl_t.cget("text"), "t = 7 / 28")
        instante = self.app.instantes[7]
        self.assertEqual((instante.en_cpu, instante.cola), ("P3", ["P4", "P1", "P2"]))
        estados = {f[0]: f[4] for f in self.filas(self.app.tabla_estados)}
        self.assertEqual(estados["P3"], "En ejecución")
        self.assertEqual(estados["P5"], "Nuevo")
        # editar la tabla de procesos no rompe la traza ya preparada (prueba manual M6)
        self.app._limpiar()
        self.app._ir_a(999)
        self.assertEqual(self.app.lbl_t.cget("text"), "t = 28 / 28")
        self.app._alternar_reproduccion()                 # desde el final vuelve a t=0
        self.assertEqual(self.app.t_paso, 0)
        self.assertEqual(self.app.btn_reproducir.cget("text"), "Pausa")
        self.app._detener_reproduccion()
        self.assertEqual(self.app.btn_reproducir.cget("text"), "Reproducir")

    def test_validacion_de_datos(self):
        with mock.patch.object(self.gui.messagebox, "showerror") as error:
            self.app.var_rafaga.set("0")
            self.app._agregar_proceso()
            self.app.var_rafaga.set("tres")
            self.app._agregar_proceso()
            self.app._simular()                           # sin procesos
        self.assertEqual(error.call_count, 3)
        self.assertEqual(self.app.procesos, [])

    def test_agregar_y_editar_proceso(self):
        for pid, llegada, rafaga in (("A", "0", "4"), ("B", "1", "2"), ("A", "0", "6")):
            self.app.var_pid.set(pid)
            self.app.var_llegada.set(llegada)
            self.app.var_rafaga.set(rafaga)
            self.app._agregar_proceso()
        self.assertEqual(self.filas(self.app.tabla_procesos),
                         [("A", "0", "6", "0"), ("B", "1", "2", "0")])

    def test_exportar_csv_y_png(self):
        self.app._cargar_ejemplo()
        self.app._simular()
        csv = Path(self.dir.name) / "resultados.csv"
        png = Path(self.dir.name) / "gantt.png"
        with mock.patch.object(self.gui.filedialog, "asksaveasfilename",
                               side_effect=[str(csv), str(png)]):
            self.app._exportar_resultados()
            self.app._exportar_png()
        self.assertIn("Utilizacion de CPU (%)", csv.read_text(encoding="utf-8-sig"))
        self.assertEqual(png.read_bytes()[:8], b"\x89PNG\r\n\x1a\n")

    def test_guardar_y_abrir_escenario_de_la_bd(self):
        self.cargar_cinco()
        with mock.patch.object(self.gui.simpledialog, "askstring", return_value="Clase 12"):
            self.app._guardar_escenario()
        self.assertEqual(self.app.lbl_escenario.cget("text"), "Escenario: Clase 12")
        id_escenario = self.app.id_escenario
        self.app._limpiar()
        self.app._cargar_escenario(id_escenario)
        self.assertEqual([p.pid for p in self.app.procesos], ["P1", "P2", "P3", "P4", "P5"])


if __name__ == "__main__":
    unittest.main()
