"""Acceso a la base de datos SQLite (escenarios e historial de simulaciones)."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from .modelos import Proceso, Resultado

RAIZ = Path(__file__).resolve().parent.parent
RUTA_ESQUEMA = RAIZ / "bd" / "schema.sql"
RUTA_BD = RAIZ / "bd" / "planificpu.db"


class BaseDatos:
    def __init__(self, ruta: str | Path | None = None):
        self.ruta = str(ruta or RUTA_BD)
        self.con = sqlite3.connect(self.ruta)
        self.con.row_factory = sqlite3.Row
        self.con.execute("PRAGMA foreign_keys = ON")
        self.con.executescript(RUTA_ESQUEMA.read_text(encoding="utf-8"))

    def cerrar(self) -> None:
        self.con.close()

    # ---------- Escenarios ----------
    def guardar_escenario(self, nombre: str, procesos: list[Proceso]) -> int:
        with self.con:
            cur = self.con.execute("INSERT INTO escenario (nombre) VALUES (?)", (nombre,))
            id_escenario = cur.lastrowid
            self.con.executemany(
                "INSERT INTO proceso (id_escenario, pid, llegada, rafaga, prioridad, orden) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                [(id_escenario, p.pid, p.llegada, p.rafaga, p.prioridad, n)
                 for n, p in enumerate(procesos)])
        return id_escenario

    def listar_escenarios(self) -> list[sqlite3.Row]:
        return self.con.execute(
            "SELECT e.id_escenario, e.nombre, e.fecha_creacion, "
            "       COUNT(p.id_proceso) AS procesos "
            "FROM escenario e LEFT JOIN proceso p ON p.id_escenario = e.id_escenario "
            "GROUP BY e.id_escenario ORDER BY e.id_escenario DESC").fetchall()

    def cargar_escenario(self, id_escenario: int) -> tuple[str, list[Proceso]]:
        fila = self.con.execute("SELECT nombre FROM escenario WHERE id_escenario = ?",
                                (id_escenario,)).fetchone()
        if fila is None:
            raise KeyError(f"No existe el escenario {id_escenario}")
        procesos = [Proceso(r["pid"], r["llegada"], r["rafaga"], r["prioridad"])
                    for r in self.con.execute(
                        "SELECT pid, llegada, rafaga, prioridad FROM proceso "
                        "WHERE id_escenario = ? ORDER BY orden", (id_escenario,))]
        return fila["nombre"], procesos

    def eliminar_escenario(self, id_escenario: int) -> None:
        with self.con:
            self.con.execute("DELETE FROM escenario WHERE id_escenario = ?", (id_escenario,))

    # ---------- Simulaciones ----------
    def guardar_simulacion(self, id_escenario: int, r: Resultado) -> int:
        ids = {row["pid"]: row["id_proceso"] for row in self.con.execute(
            "SELECT pid, id_proceso FROM proceso WHERE id_escenario = ?", (id_escenario,))}
        id_algoritmo = self.con.execute("SELECT id_algoritmo FROM algoritmo WHERE nombre = ?",
                                        (r.algoritmo,)).fetchone()["id_algoritmo"]
        with self.con:
            cur = self.con.execute(
                "INSERT INTO simulacion (id_escenario, id_algoritmo, quantum, expropiativo, "
                "espera_promedio, retorno_promedio, respuesta_promedio, cambios_contexto) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (id_escenario, id_algoritmo, r.quantum, int(r.expropiativo), r.espera_promedio,
                 r.retorno_promedio, r.respuesta_promedio, r.cambios_contexto))
            id_sim = cur.lastrowid
            self.con.executemany(
                "INSERT INTO resultado_proceso (id_simulacion, id_proceso, inicio, fin, espera, "
                "retorno, respuesta) VALUES (?, ?, ?, ?, ?, ?, ?)",
                [(id_sim, ids[p.pid], p.inicio, p.fin, p.espera, p.retorno, p.respuesta)
                 for p in r.procesos])
            self.con.executemany(
                "INSERT INTO segmento_gantt (id_simulacion, orden, id_proceso, inicio, fin) "
                "VALUES (?, ?, ?, ?, ?)",
                [(id_sim, n, ids.get(s.pid), s.inicio, s.fin) for n, s in enumerate(r.gantt)])
        return id_sim

    def listar_simulaciones(self, limite: int = 200) -> list[sqlite3.Row]:
        return self.con.execute(
            "SELECT s.id_simulacion, s.fecha, e.id_escenario, e.nombre AS escenario, "
            "       a.nombre AS algoritmo, s.quantum, s.expropiativo, s.espera_promedio, "
            "       s.retorno_promedio, s.respuesta_promedio, s.cambios_contexto "
            "FROM simulacion s "
            "JOIN escenario e ON e.id_escenario = s.id_escenario "
            "JOIN algoritmo a ON a.id_algoritmo = s.id_algoritmo "
            "ORDER BY s.id_simulacion DESC LIMIT ?", (limite,)).fetchall()
