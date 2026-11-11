"""Interfaz grafica de PlanifiCPU (Tkinter + Matplotlib)."""

from __future__ import annotations

import tkinter as tk
from datetime import datetime
from tkinter import filedialog, messagebox, simpledialog, ttk

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from . import csv_io
from .algoritmos import ALGORITMOS, admite_expropiacion, comparar, simular
from .bd import BaseDatos
from .metricas import formato
from .modelos import ErrorValidacion, Proceso, Resultado
from .paso_a_paso import EJECUCION, LISTO, NUEVO, TERMINADO, Instante, trazar

ROJO = "#9b1027"
ROJO_OSCURO = "#7a0c1f"
FONDO = "#f4f6fa"
COLORES = ["#1f5fbf", "#1e8a4c", "#d99a00", "#b3122e", "#6b3fa0",
           "#0f8b8d", "#c4561d", "#4b5d73", "#c2387a", "#5b8c1a"]
EJEMPLO = [Proceso("P1", 0, 5, 2), Proceso("P2", 1, 3, 1), Proceso("P3", 2, 4, 3)]


class App(tk.Tk):
    def __init__(self, ruta_bd=None):
        super().__init__()
        self.title("PlanifiCPU - Simulador de planificación de procesos en la CPU")
        self.geometry("1320x780")
        self.minsize(1150, 700)
        try:
            self.state("zoomed")  # maximizada en Windows
        except tk.TclError:
            pass
        self.configure(bg=FONDO)

        self.bd = BaseDatos(ruta_bd)
        self.procesos: list[Proceso] = []
        self.id_escenario: int | None = None
        self.nombre_escenario: str | None = None
        self.resultados: list[Resultado] = []   # ultimo resultado o comparacion
        self.instantes: list[Instante] = []      # traza del modo paso a paso
        self.resultado_paso: Resultado | None = None
        self.t_paso = 0
        self.id_reproduccion: str | None = None

        self._estilos()
        self._construir()
        self._refrescar_historial()
        self.protocol("WM_DELETE_WINDOW", self._cerrar)

    # ------------------------------------------------------------------ estilo
    def _estilos(self) -> None:
        e = ttk.Style(self)
        e.theme_use("clam")
        e.configure(".", background=FONDO, font=("Segoe UI", 10))
        e.configure("TLabelframe", background="white", bordercolor="#d9dde5")
        e.configure("TLabelframe.Label", background="white", foreground=ROJO,
                    font=("Segoe UI", 10, "bold"))
        e.configure("Blanco.TFrame", background="white")
        e.configure("Blanco.TLabel", background="white")
        e.configure("Blanco.TCheckbutton", background="white")
        e.configure("Acento.TButton", background=ROJO, foreground="white",
                    font=("Segoe UI", 10, "bold"), padding=6)
        e.map("Acento.TButton", background=[("active", ROJO_OSCURO)])
        e.configure("TButton", padding=4)
        e.configure("Treeview", rowheight=24)
        e.configure("Treeview.Heading", font=("Segoe UI", 9, "bold"))
        e.configure("TNotebook.Tab", padding=(14, 6), font=("Segoe UI", 10))
        e.map("TNotebook.Tab", foreground=[("selected", ROJO)])

    # ------------------------------------------------------------- construccion
    def _construir(self) -> None:
        cabecera = tk.Frame(self, bg=ROJO, height=58)
        cabecera.pack(fill="x")
        tk.Label(cabecera, text="PlanifiCPU", bg=ROJO, fg="white",
                 font=("Segoe UI", 18, "bold")).pack(side="left", padx=(18, 10), pady=8)
        tk.Label(cabecera, text="Simulador de algoritmos de planificación de procesos en la CPU",
                 bg=ROJO, fg="#f3d6dc", font=("Segoe UI", 11)).pack(side="left")
        self.lbl_escenario = tk.Label(cabecera, text="Escenario: sin guardar", bg=ROJO,
                                      fg="white", font=("Segoe UI", 10))
        self.lbl_escenario.pack(side="right", padx=18)

        cuerpo = ttk.Frame(self)
        cuerpo.pack(fill="both", expand=True, padx=10, pady=10)
        izquierda = ttk.Frame(cuerpo)
        izquierda.pack(side="left", fill="y")
        derecha = ttk.Frame(cuerpo)
        derecha.pack(side="left", fill="both", expand=True, padx=(10, 0))

        # los paneles 3 y 2 se anclan abajo para que siempre queden visibles
        self._panel_archivos(izquierda)
        self._panel_algoritmo(izquierda)
        self._panel_procesos(izquierda)
        self._panel_resultados(derecha)

        self.barra = tk.Label(self, text="Listo. Registre procesos o cargue un CSV.",
                              anchor="w", bg="#e6e9ef", fg="#333", font=("Segoe UI", 9))
        self.barra.pack(fill="x", side="bottom")

    def _panel_procesos(self, padre) -> None:
        marco = ttk.LabelFrame(padre, text="1. Registrar procesos", padding=8)
        marco.pack(side="top", fill="both", expand=True)

        form = ttk.Frame(marco, style="Blanco.TFrame")
        form.pack(fill="x")
        self.var_pid = tk.StringVar(value="P1")
        self.var_llegada = tk.StringVar(value="0")
        self.var_rafaga = tk.StringVar(value="1")
        self.var_prioridad = tk.StringVar(value="0")
        campos = (("PID", self.var_pid), ("Llegada", self.var_llegada),
                  ("Ráfaga", self.var_rafaga), ("Prioridad", self.var_prioridad))
        for col, (texto, var) in enumerate(campos):
            ttk.Label(form, text=texto, style="Blanco.TLabel").grid(row=0, column=col, sticky="w")
            ttk.Entry(form, textvariable=var, width=8).grid(row=1, column=col, padx=(0, 6))
        ttk.Button(form, text="Agregar / actualizar", command=self._agregar_proceso).grid(
            row=2, column=0, columnspan=4, sticky="ew", pady=(6, 0))
        ttk.Label(marco, text="Prioridad: número menor = mayor prioridad.",
                  style="Blanco.TLabel", foreground="#666").pack(anchor="w", pady=(4, 4))

        self.tabla_procesos = ttk.Treeview(marco, columns=("pid", "llegada", "rafaga", "prioridad"),
                                           show="headings", height=8, selectmode="browse")
        for col, texto in zip(("pid", "llegada", "rafaga", "prioridad"),
                              ("PID", "Llegada", "Ráfaga", "Prioridad")):
            self.tabla_procesos.heading(col, text=texto)
            self.tabla_procesos.column(col, width=78, anchor="center")
        self.tabla_procesos.pack(fill="both", expand=True)
        self.tabla_procesos.bind("<<TreeviewSelect>>", self._seleccionar_proceso)

        botones = ttk.Frame(marco, style="Blanco.TFrame")
        botones.pack(fill="x", pady=(6, 0))
        ttk.Button(botones, text="Eliminar", command=self._eliminar_proceso).pack(side="left")
        ttk.Button(botones, text="Limpiar todo", command=self._limpiar).pack(side="left", padx=4)
        ttk.Button(botones, text="Cargar ejemplo", command=self._cargar_ejemplo).pack(side="right")

    def _panel_algoritmo(self, padre) -> None:
        marco = ttk.LabelFrame(padre, text="2. Elegir algoritmo", padding=8)
        marco.pack(side="bottom", fill="x", pady=(8, 0))
        fila = ttk.Frame(marco, style="Blanco.TFrame")
        fila.pack(fill="x")
        ttk.Label(fila, text="Algoritmo", style="Blanco.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(fila, text="Quantum", style="Blanco.TLabel").grid(row=0, column=1, sticky="w",
                                                                   padx=(10, 0))
        self.var_algoritmo = tk.StringVar(value="FCFS")
        combo = ttk.Combobox(fila, textvariable=self.var_algoritmo, values=ALGORITMOS,
                             state="readonly", width=16)
        combo.grid(row=1, column=0, sticky="w")
        combo.bind("<<ComboboxSelected>>", lambda _e: self._actualizar_opciones())
        self.var_quantum = tk.StringVar(value="2")
        self.spin_quantum = ttk.Spinbox(fila, from_=1, to=50, textvariable=self.var_quantum,
                                        width=6)
        self.spin_quantum.grid(row=1, column=1, sticky="w", padx=(10, 0))
        self.var_expropiativo = tk.BooleanVar(value=False)
        self.chk_expropiativo = ttk.Checkbutton(
            marco, text="Modo expropiativo", variable=self.var_expropiativo,
            style="Blanco.TCheckbutton")
        self.chk_expropiativo.pack(anchor="w", pady=(6, 0))
        ttk.Label(marco, text="Aplica a SJF (SRTF) y Prioridad.", style="Blanco.TLabel",
                  foreground="#666").pack(anchor="w", pady=(0, 6))
        fila_sim = ttk.Frame(marco, style="Blanco.TFrame")
        fila_sim.pack(fill="x")
        ttk.Button(fila_sim, text="Simular", style="Acento.TButton",
                   command=self._simular).grid(row=0, column=0, sticky="ew", padx=(0, 3))
        ttk.Button(fila_sim, text="Paso a paso", style="Acento.TButton",
                   command=lambda: self._simular(paso_a_paso=True)).grid(row=0, column=1,
                                                                          sticky="ew", padx=(3, 0))
        fila_sim.columnconfigure((0, 1), weight=1)
        ttk.Button(marco, text="Comparar los 4 algoritmos",
                   command=self._comparar).pack(fill="x", pady=(6, 0))
        self._actualizar_opciones()

    def _panel_archivos(self, padre) -> None:
        marco = ttk.LabelFrame(padre, text="3. Escenarios y reportes", padding=8)
        marco.pack(side="bottom", fill="x", pady=(8, 0))
        rejilla = ttk.Frame(marco, style="Blanco.TFrame")
        rejilla.pack(fill="x")
        acciones = (("Cargar CSV", self._cargar_csv), ("Guardar CSV", self._guardar_csv),
                    ("Guardar en BD", self._guardar_escenario),
                    ("Abrir de BD", self._abrir_escenario),
                    ("Exportar resultados", self._exportar_resultados),
                    ("Exportar Gantt PNG", self._exportar_png))
        for n, (texto, cmd) in enumerate(acciones):
            ttk.Button(rejilla, text=texto, command=cmd).grid(row=n // 2, column=n % 2,
                                                              sticky="ew", padx=2, pady=2)
        rejilla.columnconfigure((0, 1), weight=1)

    def _panel_resultados(self, padre) -> None:
        self.pestanas = ttk.Notebook(padre)
        self.pestanas.pack(fill="both", expand=True)

        # Gantt
        tab_gantt = ttk.Frame(self.pestanas, style="Blanco.TFrame", padding=8)
        self.pestanas.add(tab_gantt, text="Diagrama de Gantt")
        self.fig_gantt = Figure(figsize=(8, 2.6), dpi=100)
        self.canvas_gantt = FigureCanvasTkAgg(self.fig_gantt, master=tab_gantt)
        self.canvas_gantt.get_tk_widget().pack(fill="x")
        ttk.Label(tab_gantt, text="Registro de ejecución (cada tramo y cambio de contexto)",
                  style="Blanco.TLabel", font=("Segoe UI", 10, "bold"),
                  foreground=ROJO).pack(anchor="w", pady=(8, 4))
        cols = ("tramo", "proceso", "inicio", "fin", "duracion", "evento")
        self.tabla_tramos = ttk.Treeview(tab_gantt, columns=cols, show="headings")
        for col, texto, ancho in zip(cols, ("Tramo", "Proceso", "Inicio", "Fin", "Duración",
                                            "Evento"), (60, 90, 70, 70, 80, 420)):
            self.tabla_tramos.heading(col, text=texto)
            self.tabla_tramos.column(col, width=ancho, anchor="center" if col != "evento" else "w")
        self.tabla_tramos.pack(fill="both", expand=True)
        self._dibujar_vacio(self.fig_gantt, self.canvas_gantt, "Ejecute una simulación para "
                                                               "ver el diagrama de Gantt")

        self._pestana_paso_a_paso()

        # Metricas
        tab_met = ttk.Frame(self.pestanas, style="Blanco.TFrame", padding=8)
        self.pestanas.add(tab_met, text="Métricas")
        self.lbl_titulo_met = ttk.Label(tab_met, text="Sin resultados", style="Blanco.TLabel",
                                        font=("Segoe UI", 12, "bold"), foreground=ROJO)
        self.lbl_titulo_met.pack(anchor="w", pady=(0, 6))
        columnas = ("pid", "llegada", "rafaga", "prioridad", "inicio", "fin",
                    "espera", "retorno", "respuesta")
        self.tabla_met = ttk.Treeview(tab_met, columns=columnas, show="headings", height=12)
        titulos = ("Proceso", "Llegada", "Ráfaga", "Prioridad", "Inicio", "Fin",
                   "Espera", "Retorno", "Respuesta")
        for col, texto in zip(columnas, titulos):
            self.tabla_met.heading(col, text=texto)
            self.tabla_met.column(col, width=90, anchor="center")
        self.tabla_met.tag_configure("promedio", background="#fbe9ec",
                                     font=("Segoe UI", 10, "bold"))
        self.tabla_met.pack(fill="both", expand=True)
        ttk.Label(tab_met, style="Blanco.TLabel", foreground="#555", justify="left",
                  text="Espera = retorno - ráfaga  |  Retorno = fin - llegada  |  "
                       "Respuesta = primer uso de CPU - llegada").pack(anchor="w", pady=(6, 0))

        # Comparacion
        tab_comp = self.tab_comp = ttk.Frame(self.pestanas, style="Blanco.TFrame", padding=8)
        self.pestanas.add(tab_comp, text="Comparación")
        cols = ("algoritmo", "espera", "retorno", "respuesta", "cambios")
        self.tabla_comp = ttk.Treeview(tab_comp, columns=cols, show="headings", height=5)
        for col, texto, ancho in zip(cols, ("Algoritmo", "Espera promedio", "Retorno promedio",
                                            "Respuesta promedio", "Cambios de contexto"),
                                     (220, 130, 130, 140, 140)):
            self.tabla_comp.heading(col, text=texto)
            self.tabla_comp.column(col, width=ancho, anchor="center")
        self.tabla_comp.tag_configure("mejor", background="#e3f3e8")
        self.tabla_comp.pack(fill="x")
        self.fig_comp = Figure(figsize=(8, 3.4), dpi=100)
        self.canvas_comp = FigureCanvasTkAgg(self.fig_comp, master=tab_comp)
        self.canvas_comp.get_tk_widget().pack(fill="both", expand=True, pady=(8, 0))
        self._dibujar_vacio(self.fig_comp, self.canvas_comp,
                            "Use 'Comparar los 4 algoritmos' con el mismo conjunto de procesos")

        # Historial
        tab_hist = ttk.Frame(self.pestanas, style="Blanco.TFrame", padding=8)
        self.pestanas.add(tab_hist, text="Historial (BD)")
        cols = ("id", "fecha", "escenario", "algoritmo", "espera", "retorno", "respuesta",
                "cambios")
        self.tabla_hist = ttk.Treeview(tab_hist, columns=cols, show="headings")
        for col, texto, ancho in zip(cols, ("#", "Fecha", "Escenario", "Algoritmo", "Espera prom.",
                                            "Retorno prom.", "Respuesta prom.", "Cambios ctx."),
                                     (40, 150, 230, 190, 110, 110, 120, 110)):
            self.tabla_hist.heading(col, text=texto)
            self.tabla_hist.column(col, width=ancho, anchor="center")
        self.tabla_hist.pack(fill="both", expand=True)
        botones = ttk.Frame(tab_hist, style="Blanco.TFrame")
        botones.pack(fill="x", pady=(6, 0))
        ttk.Button(botones, text="Abrir escenario de la simulación seleccionada",
                   command=self._abrir_desde_historial).pack(side="left")
        ttk.Button(botones, text="Actualizar", command=self._refrescar_historial).pack(side="right")

    # ------------------------------------------------------------ paso a paso
    def _pestana_paso_a_paso(self) -> None:
        tab = self.tab_paso = ttk.Frame(self.pestanas, style="Blanco.TFrame", padding=8)
        self.pestanas.add(tab, text="Paso a paso")

        controles = ttk.Frame(tab, style="Blanco.TFrame")
        controles.pack(fill="x")
        for texto, cmd in (("|< Inicio", lambda: self._ir_a(0)),
                           ("< Anterior", lambda: self._ir_a(self.t_paso - 1)),
                           ("Siguiente >", lambda: self._ir_a(self.t_paso + 1)),
                           ("Fin >|", lambda: self._ir_a(len(self.instantes) - 1))):
            ttk.Button(controles, text=texto, command=cmd).pack(side="left", padx=(0, 4))
        self.btn_reproducir = ttk.Button(controles, text="Reproducir", style="Acento.TButton",
                                         command=self._alternar_reproduccion)
        self.btn_reproducir.pack(side="left", padx=(8, 0))
        ttk.Label(controles, text="Velocidad", style="Blanco.TLabel").pack(side="left",
                                                                          padx=(16, 4))
        self.var_velocidad = tk.IntVar(value=800)
        ttk.Scale(controles, from_=1500, to=150, variable=self.var_velocidad,
                  length=140).pack(side="left")
        self.lbl_t = ttk.Label(controles, text="t = -", style="Blanco.TLabel",
                               font=("Segoe UI", 16, "bold"), foreground=ROJO)
        self.lbl_t.pack(side="right")
        self.lbl_titulo_paso = ttk.Label(tab, text="Use 'Simular paso a paso' para empezar",
                                         style="Blanco.TLabel", font=("Segoe UI", 11, "bold"),
                                         foreground="#333")
        self.lbl_titulo_paso.pack(anchor="w", pady=(6, 2))

        self.lienzo_cola = tk.Canvas(tab, height=104, bg="white", highlightthickness=1,
                                     highlightbackground="#d9dde5")
        self.lienzo_cola.pack(fill="x", pady=(2, 6))
        self.lienzo_cola.bind("<Configure>", lambda _e: self._dibujar_cola())

        self.fig_paso = Figure(figsize=(8, 1.7), dpi=100)
        self.canvas_paso = FigureCanvasTkAgg(self.fig_paso, master=tab)
        self.canvas_paso.get_tk_widget().pack(fill="x")
        self._dibujar_vacio(self.fig_paso, self.canvas_paso,
                            "El diagrama de Gantt se construirá unidad por unidad")

        abajo = ttk.Frame(tab, style="Blanco.TFrame")
        abajo.pack(fill="both", expand=True, pady=(6, 0))
        izq = ttk.Frame(abajo, style="Blanco.TFrame")
        izq.pack(side="left", fill="both")
        der = ttk.Frame(abajo, style="Blanco.TFrame")
        der.pack(side="left", fill="both", expand=True, padx=(10, 0))

        ttk.Label(izq, text="Estado de los procesos", style="Blanco.TLabel",
                  font=("Segoe UI", 10, "bold"), foreground=ROJO).pack(anchor="w")
        cols = ("pid", "llegada", "rafaga", "restante", "estado")
        self.tabla_estados = ttk.Treeview(izq, columns=cols, show="headings", height=7)
        for col, texto, ancho in zip(cols, ("Proceso", "Llegada", "Ráfaga", "Restante", "Estado"),
                                     (70, 65, 65, 70, 110)):
            self.tabla_estados.heading(col, text=texto)
            self.tabla_estados.column(col, width=ancho, anchor="center")
        for estado, color in ((EJECUCION, "#e3f3e8"), (LISTO, "#fff4d6"),
                              (TERMINADO, "#eceef2"), (NUEVO, "white")):
            self.tabla_estados.tag_configure(estado, background=color)
        self.tabla_estados.pack(fill="both", expand=True)

        ttk.Label(der, text="Bitácora de eventos del planificador", style="Blanco.TLabel",
                  font=("Segoe UI", 10, "bold"), foreground=ROJO).pack(anchor="w")
        self.tabla_bitacora = ttk.Treeview(der, columns=("t", "evento"), show="headings",
                                           height=7)
        self.tabla_bitacora.heading("t", text="t")
        self.tabla_bitacora.heading("evento", text="Evento")
        self.tabla_bitacora.column("t", width=45, anchor="center", stretch=False)
        self.tabla_bitacora.column("evento", width=480, anchor="w")
        self.tabla_bitacora.tag_configure("actual", background="#fbe9ec",
                                          font=("Segoe UI", 10, "bold"))
        self.tabla_bitacora.pack(fill="both", expand=True)

        self.bind_all("<Right>", lambda e: self._tecla_paso(e, +1))
        self.bind_all("<Left>", lambda e: self._tecla_paso(e, -1))

    def _preparar_paso_a_paso(self, r: Resultado) -> None:
        self._detener_reproduccion()
        self.resultado_paso = r
        self.procesos_paso = list(self.procesos)   # copia: la tabla puede editarse despues
        self.instantes = trazar(self.procesos_paso, r)
        self._ir_a(0)

    def _tecla_paso(self, evento, delta: int) -> None:
        if (not self.instantes or self.pestanas.select() != str(self.tab_paso)
                or isinstance(evento.widget, (ttk.Entry, tk.Entry, ttk.Combobox))):
            return
        self._detener_reproduccion()
        self._ir_a(self.t_paso + delta)

    def _ir_a(self, t: int) -> None:
        if not self.instantes:
            return
        self.t_paso = max(0, min(t, len(self.instantes) - 1))
        self._mostrar_instante()

    def _alternar_reproduccion(self) -> None:
        if self.id_reproduccion is not None:
            self._detener_reproduccion()
            return
        if not self.instantes:
            return
        if self.t_paso >= len(self.instantes) - 1:
            self._ir_a(0)
        self.btn_reproducir.config(text="Pausa")
        self.id_reproduccion = self.after(self.var_velocidad.get(), self._avanzar_reproduccion)

    def _avanzar_reproduccion(self) -> None:
        self._ir_a(self.t_paso + 1)
        if self.t_paso >= len(self.instantes) - 1:
            self._detener_reproduccion()
        else:
            self.id_reproduccion = self.after(self.var_velocidad.get(),
                                              self._avanzar_reproduccion)

    def _detener_reproduccion(self) -> None:
        if self.id_reproduccion is not None:
            self.after_cancel(self.id_reproduccion)
            self.id_reproduccion = None
        self.btn_reproducir.config(text="Reproducir")

    def _mostrar_instante(self) -> None:
        r, i = self.resultado_paso, self.instantes[self.t_paso]
        total = len(self.instantes) - 1
        self.lbl_t.config(text=f"t = {i.t} / {total}")
        self.lbl_titulo_paso.config(
            text=f"{r.nombre}  |  Unidad de tiempo [{i.t}, {i.t + 1})  |  "
                 f"Cambios de contexto hasta ahora: {i.cambios_contexto}"
            if i.t < total else f"{r.nombre}  |  Simulación terminada en t = {total}  |  "
                                f"Cambios de contexto: {i.cambios_contexto}")
        self._dibujar_cola()
        self._dibujar_gantt_parcial()

        self.tabla_estados.delete(*self.tabla_estados.get_children())
        for p in self.procesos_paso:
            estado = i.estados[p.pid]
            self.tabla_estados.insert("", "end", tags=(estado,), values=(
                p.pid, p.llegada, p.rafaga, i.restante[p.pid], estado))

        self.tabla_bitacora.delete(*self.tabla_bitacora.get_children())
        ultima = None
        for anterior in self.instantes[:self.t_paso + 1]:
            for evento in anterior.eventos:
                etiqueta = ("actual",) if anterior.t == i.t else ()
                ultima = self.tabla_bitacora.insert("", "end", tags=etiqueta,
                                                    values=(anterior.t, evento))
        if ultima:
            self.tabla_bitacora.see(ultima)

    def _dibujar_cola(self) -> None:
        c = self.lienzo_cola
        c.delete("all")
        if not self.instantes:
            c.create_text(16, 52, anchor="w", fill="#888", font=("Segoe UI", 10),
                          text="Aquí se verá el proceso en CPU y la cola de listos en cada instante")
            return
        i = self.instantes[self.t_paso]
        c.create_text(16, 16, anchor="w", text="CPU", fill=ROJO, font=("Segoe UI", 9, "bold"))
        if i.en_cpu is None:
            c.create_rectangle(16, 28, 136, 88, fill="#eeeeee", outline="#999", dash=(3, 2))
            c.create_text(76, 58, text="Ociosa", fill="#555", font=("Segoe UI", 11))
        else:
            c.create_rectangle(16, 28, 136, 88, fill=self._color(i.en_cpu), outline="")
            c.create_text(76, 50, text=i.en_cpu, fill="white", font=("Segoe UI", 16, "bold"))
            c.create_text(76, 74, text=f"le faltan {i.restante[i.en_cpu]}", fill="white",
                          font=("Segoe UI", 9))
        c.create_line(150, 58, 190, 58, arrow="first", width=2, fill="#666")
        c.create_text(200, 16, anchor="w", fill=ROJO, font=("Segoe UI", 9, "bold"),
                      text="Cola de listos (el primero es el siguiente en obtener la CPU)")
        if not i.cola:
            c.create_text(200, 58, anchor="w", text="(vacía)", fill="#888", font=("Segoe UI", 11))
        for n, pid in enumerate(i.cola):
            x = 200 + n * 82
            c.create_rectangle(x, 32, x + 72, 84, fill=self._color(pid), outline="")
            c.create_text(x + 36, 50, text=pid, fill="white", font=("Segoe UI", 13, "bold"))
            c.create_text(x + 36, 72, text=f"faltan {i.restante[pid]}", fill="white",
                          font=("Segoe UI", 8))

    def _dibujar_gantt_parcial(self) -> None:
        r, t = self.resultado_paso, self.t_paso
        fig = self.fig_paso
        fig.clear()
        ax = fig.add_subplot(111)
        for s in r.gantt:
            if s.inicio > t:
                break
            fin = min(s.fin, t + 1)
            hecho = min(s.fin, t) - s.inicio    # unidades ya ejecutadas
            color = "#eeeeee" if s.pid is None else self._color(s.pid)
            if hecho > 0:
                ax.broken_barh([(s.inicio, hecho)], (0, 1), facecolors=color,
                               edgecolor="#999" if s.pid is None else "white",
                               hatch="//" if s.pid is None else None, linewidth=1.5)
            if fin > max(s.inicio, t):          # unidad en curso, resaltada
                ax.broken_barh([(t, 1)], (0, 1), facecolors=color, alpha=0.5,
                               edgecolor=ROJO, linewidth=2)
            centro = s.inicio + (fin - s.inicio) / 2
            ax.text(centro, 0.5, s.pid or "Ocioso", ha="center", va="center",
                    color="white" if s.pid else "#555", fontsize=10 if s.pid else 8,
                    fontweight="bold" if s.pid else "normal")
        ax.axvline(t, color=ROJO, linewidth=2)
        ax.set_xlim(0, max(r.tiempo_total, 1))
        ax.set_ylim(0, 1)
        ax.set_xticks(range(0, r.tiempo_total + 1))
        ax.tick_params(axis="x", labelsize=8)
        ax.set_yticks([])
        for lado in ("top", "right", "left"):
            ax.spines[lado].set_visible(False)
        fig.subplots_adjust(left=0.03, right=0.98, top=0.95, bottom=0.3)
        self.canvas_paso.draw()

    # --------------------------------------------------------------- procesos
    def _estado(self, texto: str) -> None:
        self.barra.config(text=texto)

    def _marcar_modificado(self) -> None:
        self.id_escenario = None
        self.nombre_escenario = None
        self.lbl_escenario.config(text="Escenario: sin guardar")

    def _refrescar_procesos(self) -> None:
        self.tabla_procesos.delete(*self.tabla_procesos.get_children())
        for p in self.procesos:
            self.tabla_procesos.insert("", "end", iid=p.pid,
                                       values=(p.pid, p.llegada, p.rafaga, p.prioridad))
        self.var_pid.set(f"P{len(self.procesos) + 1}")

    def _agregar_proceso(self) -> None:
        try:
            nuevo = Proceso(self.var_pid.get().strip(), int(self.var_llegada.get()),
                            int(self.var_rafaga.get()), int(self.var_prioridad.get()))
        except ValueError:
            messagebox.showerror("Dato inválido", "Llegada, ráfaga y prioridad deben ser enteros.")
            return
        if not nuevo.pid:
            messagebox.showerror("Dato inválido", "Escriba un PID.")
            return
        if nuevo.llegada < 0 or nuevo.rafaga < 1 or nuevo.prioridad < 0:
            messagebox.showerror("Dato inválido",
                                 "Llegada y prioridad deben ser >= 0 y la ráfaga >= 1.")
            return
        existente = next((i for i, p in enumerate(self.procesos) if p.pid == nuevo.pid), None)
        if existente is None:
            self.procesos.append(nuevo)
            self._estado(f"Proceso {nuevo.pid} agregado.")
        else:
            self.procesos[existente] = nuevo
            self._estado(f"Proceso {nuevo.pid} actualizado.")
        self._marcar_modificado()
        self._refrescar_procesos()

    def _seleccionar_proceso(self, _evento=None) -> None:
        sel = self.tabla_procesos.selection()
        if not sel:
            return
        p = next(p for p in self.procesos if p.pid == sel[0])
        self.var_pid.set(p.pid)
        self.var_llegada.set(str(p.llegada))
        self.var_rafaga.set(str(p.rafaga))
        self.var_prioridad.set(str(p.prioridad))

    def _eliminar_proceso(self) -> None:
        sel = self.tabla_procesos.selection()
        if not sel:
            return
        self.procesos = [p for p in self.procesos if p.pid != sel[0]]
        self._marcar_modificado()
        self._refrescar_procesos()

    def _limpiar(self) -> None:
        self.procesos = []
        self._marcar_modificado()
        self._refrescar_procesos()

    def _cargar_ejemplo(self) -> None:
        self.procesos = [Proceso(p.pid, p.llegada, p.rafaga, p.prioridad) for p in EJEMPLO]
        self._marcar_modificado()
        self._refrescar_procesos()
        self._estado("Ejemplo de la ficha técnica cargado (P1, P2, P3).")

    def _actualizar_opciones(self) -> None:
        alg = self.var_algoritmo.get()
        self.spin_quantum.config(state="normal" if alg == "Round Robin" else "disabled")
        self.chk_expropiativo.config(state="normal" if admite_expropiacion(alg) else "disabled")

    # ------------------------------------------------------------- simulacion
    def _quantum(self) -> int:
        try:
            q = int(self.var_quantum.get())
        except ValueError:
            raise ErrorValidacion("El quantum debe ser un entero.")
        if q < 1:
            raise ErrorValidacion("El quantum debe ser mayor o igual a 1.")
        return q

    def _asegurar_escenario(self) -> int:
        """Guarda automaticamente el escenario si cambio desde la ultima vez."""
        if self.id_escenario is None:
            nombre = "Escenario " + datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.id_escenario = self.bd.guardar_escenario(nombre, self.procesos)
            self.nombre_escenario = nombre
            self.lbl_escenario.config(text=f"Escenario: {nombre}")
        return self.id_escenario

    def _simular(self, paso_a_paso: bool = False) -> None:
        try:
            alg = self.var_algoritmo.get()
            q = self._quantum() if alg == "Round Robin" else None
            r = simular(self.procesos, alg, q, self.var_expropiativo.get())
        except (ErrorValidacion, ValueError) as e:
            messagebox.showerror("No se puede simular", str(e))
            return
        id_esc = self._asegurar_escenario()
        self.bd.guardar_simulacion(id_esc, r)
        self.resultados = [r]
        self._mostrar_gantt(r)
        self._mostrar_metricas(r)
        self._preparar_paso_a_paso(r)
        self._refrescar_historial()
        if paso_a_paso:
            self.pestanas.select(self.tab_paso)
            self._estado(f"{r.nombre} paso a paso: use Siguiente o Reproducir para avanzar "
                         f"(flechas izquierda/derecha del teclado).")
            return
        self.pestanas.select(0)
        self._estado(f"{r.nombre}: espera promedio {formato(r.espera_promedio)}, retorno "
                     f"promedio {formato(r.retorno_promedio)}. Guardado en la BD.")

    def _comparar(self) -> None:
        try:
            resultados = comparar(self.procesos, self._quantum(), self.var_expropiativo.get())
        except (ErrorValidacion, ValueError) as e:
            messagebox.showerror("No se puede comparar", str(e))
            return
        id_esc = self._asegurar_escenario()
        for r in resultados:
            self.bd.guardar_simulacion(id_esc, r)
        self.resultados = resultados
        self._mostrar_comparacion(resultados)
        actual = next(r for r in resultados if r.algoritmo == self.var_algoritmo.get())
        self._mostrar_gantt(actual)
        self._mostrar_metricas(actual)
        self._preparar_paso_a_paso(actual)
        self._refrescar_historial()
        self.pestanas.select(self.tab_comp)
        mejor = min(resultados, key=lambda r: r.espera_promedio)
        self._estado(f"Comparación lista. Menor espera promedio: {mejor.nombre} "
                     f"({formato(mejor.espera_promedio)}).")

    # ---------------------------------------------------------------- dibujos
    @staticmethod
    def _dibujar_vacio(fig, canvas, texto) -> None:
        fig.clear()
        ax = fig.add_subplot(111)
        ax.axis("off")
        ax.text(0.5, 0.5, texto, ha="center", va="center", color="#888", fontsize=11)
        canvas.draw()

    def _color(self, pid: str) -> str:
        pids = [p.pid for p in self.procesos]
        return COLORES[pids.index(pid) % len(COLORES)] if pid in pids else "#888"

    def _mostrar_gantt(self, r: Resultado) -> None:
        fig = self.fig_gantt
        fig.clear()
        ax = fig.add_subplot(111)
        for s in r.gantt:
            if s.pid is None:
                ax.broken_barh([(s.inicio, s.duracion)], (0, 1), facecolors="#eeeeee",
                               edgecolor="#999", hatch="//")
                ax.text(s.inicio + s.duracion / 2, 0.5, "Ocioso", ha="center", va="center",
                        fontsize=8, color="#555")
            else:
                ax.broken_barh([(s.inicio, s.duracion)], (0, 1), facecolors=self._color(s.pid),
                               edgecolor="white", linewidth=1.5)
                ax.text(s.inicio + s.duracion / 2, 0.5, s.pid, ha="center", va="center",
                        color="white", fontsize=11, fontweight="bold")
        marcas = sorted({0} | {s.inicio for s in r.gantt} | {s.fin for s in r.gantt})
        ax.set_xticks(marcas)
        ax.set_xlim(0, r.tiempo_total)
        ax.set_ylim(0, 1)
        ax.set_yticks([])
        for lado in ("top", "right", "left"):
            ax.spines[lado].set_visible(False)
        ax.set_xlabel("Tiempo (unidades)")
        ax.set_title(f"{r.nombre}  |  Espera prom. {formato(r.espera_promedio)}  |  Retorno prom. "
                     f"{formato(r.retorno_promedio)}  |  Cambios de contexto {r.cambios_contexto}",
                     fontsize=10, color=ROJO, loc="left")
        fig.subplots_adjust(left=0.03, right=0.98, top=0.84, bottom=0.25)
        self.canvas_gantt.draw()
        self._mostrar_tramos(r)

    def _mostrar_tramos(self, r: Resultado) -> None:
        self.tabla_tramos.delete(*self.tabla_tramos.get_children())
        rafaga = {p.pid: p.rafaga for p in r.procesos}
        ejecutado: dict[str, int] = {}
        anterior = None
        for n, s in enumerate(r.gantt, start=1):
            if s.pid is None:
                evento = "CPU ociosa: no hay procesos en la cola de listos"
            else:
                ejecutado[s.pid] = ejecutado.get(s.pid, 0) + s.duracion
                if anterior is None:
                    evento = f"{s.pid} toma la CPU"
                elif anterior == s.pid:
                    evento = f"{s.pid} continúa en la CPU"
                else:
                    evento = f"Cambio de contexto: {anterior} -> {s.pid}"
                if ejecutado[s.pid] == rafaga[s.pid]:
                    evento += f"; {s.pid} termina en t={s.fin}"
                else:
                    evento += f"; {s.pid} es expropiado (le faltan {rafaga[s.pid] - ejecutado[s.pid]})"
                anterior = s.pid
            self.tabla_tramos.insert("", "end", values=(n, s.pid or "Ocioso", s.inicio, s.fin,
                                                         s.duracion, evento))

    def _mostrar_metricas(self, r: Resultado) -> None:
        self.lbl_titulo_met.config(text=f"Métricas por proceso - {r.nombre}")
        self.tabla_met.delete(*self.tabla_met.get_children())
        for p in r.procesos:
            self.tabla_met.insert("", "end", values=(p.pid, p.llegada, p.rafaga, p.prioridad,
                                                     p.inicio, p.fin, p.espera, p.retorno,
                                                     p.respuesta))
        self.tabla_met.insert("", "end", tags=("promedio",), values=(
            "Promedio", "", "", "", "", "", formato(r.espera_promedio),
            formato(r.retorno_promedio), formato(r.respuesta_promedio)))

    def _mostrar_comparacion(self, resultados: list[Resultado]) -> None:
        self.tabla_comp.delete(*self.tabla_comp.get_children())
        menor = min(r.espera_promedio for r in resultados)
        for r in resultados:
            etiqueta = ("mejor",) if r.espera_promedio == menor else ()
            self.tabla_comp.insert("", "end", tags=etiqueta, values=(
                r.nombre, formato(r.espera_promedio), formato(r.retorno_promedio),
                formato(r.respuesta_promedio), r.cambios_contexto))

        fig = self.fig_comp
        fig.clear()
        ax = fig.add_subplot(111)
        series = (("Espera", "espera_promedio", "#1f5fbf"),
                  ("Retorno", "retorno_promedio", ROJO),
                  ("Respuesta", "respuesta_promedio", "#d99a00"))
        ancho = 0.26
        for k, (nombre, attr, color) in enumerate(series):
            xs = [i + (k - 1) * ancho for i in range(len(resultados))]
            ys = [getattr(r, attr) for r in resultados]
            barras = ax.bar(xs, ys, ancho, label=nombre, color=color)
            ax.bar_label(barras, labels=[formato(y) for y in ys], fontsize=8, padding=2)
        ax.set_xticks(range(len(resultados)), [r.nombre for r in resultados], fontsize=9)
        ax.set_ylabel("Tiempo promedio")
        ax.legend(frameon=False, ncol=3, loc="upper left")
        ax.margins(y=0.2)
        for lado in ("top", "right"):
            ax.spines[lado].set_visible(False)
        fig.tight_layout()
        self.canvas_comp.draw()

    # ------------------------------------------------------- archivos y BD
    def _cargar_csv(self) -> None:
        ruta = filedialog.askopenfilename(title="Cargar escenario CSV",
                                          filetypes=[("CSV", "*.csv"), ("Todos", "*.*")])
        if not ruta:
            return
        try:
            self.procesos = csv_io.cargar_procesos(ruta)
        except (ErrorValidacion, OSError, KeyError) as e:
            messagebox.showerror("CSV inválido", str(e))
            return
        self._marcar_modificado()
        self._refrescar_procesos()
        self._estado(f"{len(self.procesos)} procesos cargados desde {ruta}.")

    def _guardar_csv(self) -> None:
        if not self.procesos:
            return
        ruta = filedialog.asksaveasfilename(title="Guardar escenario CSV", defaultextension=".csv",
                                            filetypes=[("CSV", "*.csv")])
        if ruta:
            csv_io.guardar_procesos(ruta, self.procesos)
            self._estado(f"Escenario guardado en {ruta}.")

    def _guardar_escenario(self) -> None:
        if not self.procesos:
            messagebox.showinfo("Sin procesos", "Registre al menos un proceso.")
            return
        nombre = simpledialog.askstring("Guardar escenario", "Nombre del escenario:", parent=self)
        if not nombre:
            return
        self.id_escenario = self.bd.guardar_escenario(nombre.strip(), self.procesos)
        self.nombre_escenario = nombre.strip()
        self.lbl_escenario.config(text=f"Escenario: {self.nombre_escenario}")
        self._estado(f"Escenario '{self.nombre_escenario}' guardado en la BD.")

    def _abrir_escenario(self) -> None:
        escenarios = self.bd.listar_escenarios()
        if not escenarios:
            messagebox.showinfo("Base de datos", "Aún no hay escenarios guardados.")
            return
        ventana = tk.Toplevel(self)
        ventana.title("Abrir escenario")
        ventana.geometry("520x320")
        ventana.transient(self)
        tabla = ttk.Treeview(ventana, columns=("id", "nombre", "fecha", "procesos"),
                             show="headings")
        for col, texto, ancho in (("id", "#", 40), ("nombre", "Nombre", 220),
                                  ("fecha", "Fecha", 150), ("procesos", "Procesos", 70)):
            tabla.heading(col, text=texto)
            tabla.column(col, width=ancho, anchor="center")
        for e in escenarios:
            tabla.insert("", "end", iid=str(e["id_escenario"]), values=(
                e["id_escenario"], e["nombre"], e["fecha_creacion"], e["procesos"]))
        tabla.pack(fill="both", expand=True, padx=8, pady=8)

        def abrir() -> None:
            sel = tabla.selection()
            if sel:
                self._cargar_escenario(int(sel[0]))
                ventana.destroy()

        def eliminar() -> None:
            sel = tabla.selection()
            if sel and messagebox.askyesno("Eliminar", "Se borrará el escenario y sus "
                                           "simulaciones. ¿Continuar?", parent=ventana):
                self.bd.eliminar_escenario(int(sel[0]))
                tabla.delete(sel[0])
                if self.id_escenario == int(sel[0]):
                    self._marcar_modificado()
                self._refrescar_historial()

        tabla.bind("<Double-1>", lambda _e: abrir())
        fila = ttk.Frame(ventana)
        fila.pack(fill="x", padx=8, pady=(0, 8))
        ttk.Button(fila, text="Abrir", style="Acento.TButton", command=abrir).pack(side="right")
        ttk.Button(fila, text="Eliminar", command=eliminar).pack(side="left")

    def _cargar_escenario(self, id_escenario: int) -> None:
        nombre, procesos = self.bd.cargar_escenario(id_escenario)
        self.procesos = procesos
        self._refrescar_procesos()
        self.id_escenario = id_escenario
        self.nombre_escenario = nombre
        self.lbl_escenario.config(text=f"Escenario: {nombre}")
        self._estado(f"Escenario '{nombre}' abierto desde la BD.")

    def _abrir_desde_historial(self) -> None:
        sel = self.tabla_hist.selection()
        if sel:
            self._cargar_escenario(int(self.tabla_hist.item(sel[0], "values")[-1]))

    def _refrescar_historial(self) -> None:
        self.tabla_hist.delete(*self.tabla_hist.get_children())
        for s in self.bd.listar_simulaciones():
            r = Resultado(s["algoritmo"], s["quantum"], bool(s["expropiativo"]))
            # el ultimo valor (oculto) es el id del escenario
            self.tabla_hist.insert("", "end", values=(
                s["id_simulacion"], s["fecha"], s["escenario"], r.nombre,
                formato(s["espera_promedio"]), formato(s["retorno_promedio"]),
                formato(s["respuesta_promedio"]), s["cambios_contexto"], s["id_escenario"]))

    def _exportar_resultados(self) -> None:
        if not self.resultados:
            messagebox.showinfo("Sin resultados", "Primero ejecute una simulación.")
            return
        ruta = filedialog.asksaveasfilename(title="Exportar resultados", defaultextension=".csv",
                                            filetypes=[("CSV", "*.csv")])
        if ruta:
            csv_io.exportar_resultados(ruta, self.resultados)
            self._estado(f"Resultados exportados a {ruta}.")

    def _exportar_png(self) -> None:
        if not self.resultados:
            messagebox.showinfo("Sin resultados", "Primero ejecute una simulación.")
            return
        ruta = filedialog.asksaveasfilename(title="Exportar Gantt", defaultextension=".png",
                                            filetypes=[("PNG", "*.png")])
        if ruta:
            self.fig_gantt.savefig(ruta, dpi=150, bbox_inches="tight")
            self._estado(f"Diagrama de Gantt exportado a {ruta}.")

    def _cerrar(self) -> None:
        self._detener_reproduccion()
        self.bd.cerrar()
        self.destroy()
