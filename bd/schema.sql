-- PlanifiCPU - Esquema de la base de datos (SQLite 3)
-- Guarda los escenarios de procesos y el historial de simulaciones.
-- Se ejecuta automaticamente al abrir la aplicacion (CREATE ... IF NOT EXISTS).

PRAGMA foreign_keys = ON;

-- Catalogo de algoritmos soportados.
CREATE TABLE IF NOT EXISTS algoritmo (
    id_algoritmo   INTEGER PRIMARY KEY,
    nombre         TEXT    NOT NULL UNIQUE,
    permite_expropiacion INTEGER NOT NULL CHECK (permite_expropiacion IN (0, 1)),
    usa_quantum    INTEGER NOT NULL CHECK (usa_quantum IN (0, 1))
);

INSERT OR IGNORE INTO algoritmo (id_algoritmo, nombre, permite_expropiacion, usa_quantum) VALUES
    (1, 'FCFS',        0, 0),
    (2, 'SJF',         1, 0),
    (3, 'Round Robin', 1, 1),
    (4, 'Prioridad',   1, 0);

-- Conjunto de procesos que el usuario registra o carga desde CSV.
CREATE TABLE IF NOT EXISTS escenario (
    id_escenario   INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre         TEXT    NOT NULL,
    fecha_creacion TEXT    NOT NULL DEFAULT (datetime('now', 'localtime'))
);

-- Procesos de cada escenario.
CREATE TABLE IF NOT EXISTS proceso (
    id_proceso     INTEGER PRIMARY KEY AUTOINCREMENT,
    id_escenario   INTEGER NOT NULL REFERENCES escenario (id_escenario) ON DELETE CASCADE,
    pid            TEXT    NOT NULL,
    llegada        INTEGER NOT NULL CHECK (llegada >= 0),
    rafaga         INTEGER NOT NULL CHECK (rafaga >= 1),
    prioridad      INTEGER NOT NULL DEFAULT 0 CHECK (prioridad >= 0),
    orden          INTEGER NOT NULL,
    UNIQUE (id_escenario, pid)
);

-- Cada ejecucion de un algoritmo sobre un escenario.
CREATE TABLE IF NOT EXISTS simulacion (
    id_simulacion      INTEGER PRIMARY KEY AUTOINCREMENT,
    id_escenario       INTEGER NOT NULL REFERENCES escenario (id_escenario) ON DELETE CASCADE,
    id_algoritmo       INTEGER NOT NULL REFERENCES algoritmo (id_algoritmo),
    quantum            INTEGER CHECK (quantum IS NULL OR quantum >= 1),
    expropiativo       INTEGER NOT NULL CHECK (expropiativo IN (0, 1)),
    fecha              TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
    espera_promedio    REAL    NOT NULL,
    retorno_promedio   REAL    NOT NULL,
    respuesta_promedio REAL    NOT NULL,
    cambios_contexto   INTEGER NOT NULL
);

-- Metricas de cada proceso en una simulacion.
CREATE TABLE IF NOT EXISTS resultado_proceso (
    id_simulacion  INTEGER NOT NULL REFERENCES simulacion (id_simulacion) ON DELETE CASCADE,
    id_proceso     INTEGER NOT NULL REFERENCES proceso (id_proceso) ON DELETE CASCADE,
    inicio         INTEGER NOT NULL,
    fin            INTEGER NOT NULL,
    espera         INTEGER NOT NULL,
    retorno        INTEGER NOT NULL,
    respuesta      INTEGER NOT NULL,
    PRIMARY KEY (id_simulacion, id_proceso)
);

-- Tramos del diagrama de Gantt. id_proceso NULL = CPU ociosa.
CREATE TABLE IF NOT EXISTS segmento_gantt (
    id_simulacion  INTEGER NOT NULL REFERENCES simulacion (id_simulacion) ON DELETE CASCADE,
    orden          INTEGER NOT NULL,
    id_proceso     INTEGER REFERENCES proceso (id_proceso) ON DELETE CASCADE,
    inicio         INTEGER NOT NULL,
    fin            INTEGER NOT NULL CHECK (fin > inicio),
    PRIMARY KEY (id_simulacion, orden)
);

CREATE INDEX IF NOT EXISTS ix_proceso_escenario   ON proceso (id_escenario);
CREATE INDEX IF NOT EXISTS ix_simulacion_escenario ON simulacion (id_escenario);
