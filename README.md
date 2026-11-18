# PlanifiCPU

**Simulador de algoritmos de planificación de procesos en la CPU**

Universidad Manuela Beltrán · Sistemas Operativos · Grupo G11 · 2026<br>
**Fase III: versión final** · versión 2.0.0

[![Pruebas](https://github.com/daviid0611/PlanifiCPU_SistemasOperativos_G11/actions/workflows/pruebas.yml/badge.svg)](https://github.com/daviid0611/PlanifiCPU_SistemasOperativos_G11/actions/workflows/pruebas.yml)
![Python 3.12+](https://img.shields.io/badge/Python-3.12%2B-3776AB)
![Pruebas automáticas](https://img.shields.io/badge/pruebas-65%20OK-1e8a4c)
![Mutaciones](https://img.shields.io/badge/mutaciones-10%2F10%20detectadas-1e8a4c)
[![Licencia MIT](https://img.shields.io/badge/licencia-MIT-lightgrey)](LICENSE)

> **Para revisar la entrega final** vaya a la [sección 14](#14-fase-iii-versión-final): reúne la solución, el entorno, las pruebas, los resultados y la documentación, con un enlace a cada evidencia.

![Modo paso a paso de PlanifiCPU con Round Robin](recursos/imagenes/08_paso_a_paso.gif)

## Contenido

1. [Nombre del proyecto](#1-nombre-del-proyecto)
2. [Descripción general](#2-descripción-general)
3. [Levantamiento de información](#3-levantamiento-de-información)
4. [Problemática que aborda](#4-problemática-que-aborda)
5. [Objetivos](#5-objetivos)
6. [Alcance](#6-alcance)
7. [Funcionalidades principales](#7-funcionalidades-principales)
8. [Arquitectura y estructura general](#8-arquitectura-y-estructura-general)
   1. [Componentes y módulos](#81-componentes-y-módulos)
   2. [Arquitectura inicial](#82-arquitectura-inicial)
   3. [Organización de archivos y directorios](#83-organización-de-archivos-y-directorios)
   4. [Frontend](#84-frontend)
   5. [Commits](#85-commits)
   6. [Base de datos](#86-base-de-datos)
   7. [Modelo relacional](#87-modelo-relacional)
9. [Tecnologías utilizadas](#9-tecnologías-utilizadas)
10. [Requisitos iniciales de ejecución](#10-requisitos-iniciales-de-ejecución)
11. [Integrantes del equipo](#11-integrantes-del-equipo)
12. [Estado actual y próximos avances](#12-estado-actual-y-próximos-avances)
13. [Fase II: avance realizado](#13-fase-ii-avance-realizado)
14. [Fase III: versión final](#14-fase-iii-versión-final)
    1. [Evidencias de la entrega](#141-evidencias-de-la-entrega)
    2. [Solución final y componentes](#142-solución-final-y-componentes)
    3. [Configuración del entorno](#143-configuración-del-entorno)
    4. [Pruebas de funcionamiento](#144-pruebas-de-funcionamiento)
    5. [Resultados obtenidos](#145-resultados-obtenidos)
    6. [Cumplimiento de objetivos y requerimientos](#146-cumplimiento-de-objetivos-y-requerimientos)
    7. [Conclusiones y trabajo futuro](#147-conclusiones-y-trabajo-futuro)
15. [Documentación técnica y referencias](#15-documentación-técnica-y-referencias)

---

## 1. Nombre del proyecto

**PlanifiCPU**: simulador de algoritmos de planificación de procesos en la CPU.

## 2. Descripción general

PlanifiCPU es una aplicación de escritorio desarrollada en Python que simula los algoritmos de planificación de CPU **FCFS, SJF (con y sin expropiación), Round Robin y por Prioridad (con y sin expropiación)**. A partir de una lista de procesos con su tiempo de llegada, ráfaga de CPU y prioridad, genera el **diagrama de Gantt** de la ejecución, permite recorrerla **paso a paso** viendo la CPU y la cola de listos en cada instante, registra cada **cambio de contexto**, calcula los tiempos de **espera, retorno y respuesta**, la **utilización de CPU**, el **rendimiento** y la **espera máxima**, y **compara** el desempeño de los cuatro algoritmos con el mismo conjunto de procesos. Los escenarios y el historial de simulaciones se guardan en una base de datos SQLite local.

La versión final también funciona **desde la terminal** (modo consola), trae un **diagnóstico del entorno**, se distribuye como **ejecutable de Windows** que no necesita Python y está validada con 65 pruebas automáticas, ejercicios publicados en tres libros del curso y pruebas de mutación.

## 3. Levantamiento de información

**Contexto.** En la asignatura de Sistemas Operativos, la planificación de CPU se estudia resolviendo ejercicios en papel: se entrega una tabla de procesos con su tiempo de llegada, ráfaga de CPU y prioridad, y el estudiante debe dibujar el diagrama de Gantt y calcular los tiempos de espera, retorno y respuesta para cada algoritmo.

| Técnica | Qué se hizo | Qué se obtuvo |
|---|---|---|
| Revisión documental | Lectura de la bibliografía del curso sobre planificación de CPU. | Definición de los algoritmos, fórmulas de las métricas y convenciones de desempate. |
| Análisis de ejercicios del curso | Revisión del formato de los ejercicios que se resuelven a mano (PID, llegada, ráfaga, prioridad). | Formato de entrada del simulador y del archivo CSV. |
| Identificación de usuarios | Se identificó quién usa la herramienta y para qué. | Dos actores: estudiante y docente. |
| Ficha técnica del proyecto | Definición de objetivo, funcionalidad, entradas, procesamiento, salidas y alcance. | Requerimientos funcionales y no funcionales ([requerimientos.pdf](documentacion/requerimientos.pdf)). |

**Usuarios o beneficiarios**

| Usuario | Tipo | Necesidad que atiende |
|---|---|---|
| Estudiante de Sistemas Operativos | Beneficiario principal | Comprobar sus ejercicios resueltos a mano y entender por qué un algoritmo da mejores tiempos que otro. |
| Docente de Sistemas Operativos | Usuario | Mostrar en clase la ejecución paso a paso y preparar ejemplos con resultado verificable. |
| Equipo de desarrollo (G11) | Beneficiario indirecto | Aplicar en un producto real los conceptos de planificación vistos en el curso. |

**Requerimientos funcionales**

| ID | Requerimiento | Prioridad |
|---|---|---|
| RF01 | Registrar, editar y eliminar procesos con PID, tiempo de llegada, ráfaga de CPU y prioridad. | Alta |
| RF02 | Validar los datos: PID único y obligatorio, llegada ≥ 0, ráfaga ≥ 1, prioridad ≥ 0, valores enteros. | Alta |
| RF03 | Elegir el algoritmo: FCFS, SJF, Round Robin (con quantum) o Prioridad. | Alta |
| RF04 | Permitir el modo expropiativo en SJF (SRTF) y en Prioridad. | Media |
| RF05 | Generar el diagrama de Gantt y el registro de cada tramo y cambio de contexto. | Alta |
| RF06 | Calcular por proceso el tiempo de espera, retorno y respuesta, y sus promedios. | Alta |
| RF07 | Comparar los cuatro algoritmos con el mismo conjunto de procesos (tabla y gráfica). | Media |
| RF08 | Cargar escenarios desde CSV y exportar escenarios, resultados (CSV) y el Gantt (PNG). | Media |
| RF09 | Guardar escenarios en una base de datos local y consultar el historial de simulaciones. | Baja |

**Requerimientos no funcionales**

| ID | Atributo | Requerimiento |
|---|---|---|
| RNF01 | Portabilidad | Aplicación de escritorio para Windows 10/11, sin conexión a internet ni servidor. |
| RNF02 | Usabilidad | Interfaz en español organizada en pasos; decimales con coma (3,33). |
| RNF03 | Exactitud | Los cálculos deben coincidir con los ejercicios resueltos a mano; se verifican con pruebas automáticas. |
| RNF04 | Mantenibilidad | Código separado por capas: interfaz, motor, métricas, archivos y base de datos. |
| RNF05 | Rendimiento | Una simulación de hasta 50 procesos se muestra en menos de 1 segundo. |
| RNF06 | Integridad de datos | Llaves foráneas, restricciones CHECK y borrado en cascada en la base de datos. |
| RNF07 | Control de versiones | Código versionado en GitHub con commits descriptivos de cada avance. |

**Reglas de cálculo** (las mismas de los ejercicios del curso)

- El reloj avanza en unidades enteras de tiempo.
- **Retorno** = fin − llegada · **Espera** = retorno − ráfaga · **Respuesta** = primer uso de CPU − llegada.
- **Prioridad**: número menor = prioridad mayor.
- **Empates**: gana el proceso que llegó primero; si llegaron al mismo tiempo, el que se registró primero.
- **Modo expropiativo**: ante un empate se mantiene el proceso que ya está en la CPU.
- **Round Robin**: los procesos que llegan durante un quantum entran a la cola antes que el proceso expropiado.
- **Cambio de contexto**: cada vez que la CPU pasa a ejecutar un proceso distinto del anterior. Sin procesos listos, la CPU queda **ociosa**.

## 4. Problemática que aborda

**Problemática.** La planificación de CPU es un tema **abstracto** y en el curso se resuelve **a mano en papel**. Esto genera tres dificultades:

1. **No hay forma rápida de verificar** si el Gantt y los tiempos calculados son correctos; un error en un tramo se arrastra a todas las métricas.
2. **Comparar algoritmos es lento**: hay que repetir el ejercicio completo cuatro veces con los mismos datos.
3. **No se ve la ejecución en el tiempo**: en papel no es evidente cuándo ocurre una expropiación o un cambio de contexto, que es lo que diferencia a los algoritmos.

**Necesidad.** Una herramienta que permita **ver y comparar de forma visual** la planificación de CPU: ingresar los procesos una sola vez, obtener el Gantt con sus métricas, comparar los cuatro algoritmos y guardar los escenarios.

**Justificación de la solución.**

- Convierte un tema abstracto en algo visible: el Gantt y el registro de ejecución muestran cada despacho, expropiación y cambio de contexto.
- Permite verificar los ejercicios hechos a mano: el motor sigue las convenciones del curso y se valida con pruebas sobre ejercicios de resultado conocido.
- Ahorra tiempo al comparar: con un clic se ejecutan los cuatro algoritmos sobre los mismos procesos.
- Es viable para el equipo: Python y herramientas incluidas en él (Tkinter, SQLite), sin servidor ni internet, en los equipos con Windows de estudiantes y docente.

## 5. Objetivos

**General.** Desarrollar una aplicación de escritorio en Python que simule los algoritmos de planificación de CPU FCFS, SJF, Round Robin y por Prioridad, para visualizar mediante diagramas de Gantt cómo el sistema operativo asigna el procesador a los procesos y comparar su desempeño con métricas de tiempo.

**Específicos.**

1. Implementar los algoritmos FCFS, SJF (con y sin expropiación), Round Robin y Prioridad (con y sin expropiación).
2. Generar el diagrama de Gantt y el registro de cambios de contexto de cada simulación.
3. Calcular los tiempos de espera, retorno y respuesta por proceso y en promedio.
4. Comparar los cuatro algoritmos con el mismo conjunto de procesos mediante una tabla y una gráfica.
5. Guardar escenarios y resultados en archivos CSV y en una base de datos SQLite local.

## 6. Alcance

| Incluye | No incluye |
|---|---|
| 4 algoritmos: FCFS, SJF, Round Robin y Prioridad (SJF y Prioridad con y sin expropiación) | Planificar procesos reales del sistema operativo |
| Diagrama de Gantt, registro de ejecución y métricas por proceso | Sistemas multiprocesador o multinúcleo |
| Comparación de los 4 algoritmos | Operaciones de E/S ni gestión de memoria |
| Carga y exportación en CSV; Gantt en PNG | Versión web o móvil |
| Base de datos SQLite local para escenarios e historial | Usuarios, login o servidor de base de datos |
| Modo consola, diagnóstico del entorno y ejecutable `.exe` para Windows | |
| Código en GitHub, pruebas automáticas, integración continua y manual de usuario | |

## 7. Funcionalidades principales

| # | Funcionalidad | Descripción |
|---|---|---|
| 1 | Registrar procesos | PID, tiempo de llegada, ráfaga de CPU y prioridad; editar y eliminar. |
| 2 | Elegir algoritmo | FCFS, SJF, Round Robin (con quantum) o Prioridad; modo expropiativo en SJF y Prioridad. |
| 3 | Generar el diagrama de Gantt | Tramos de ejecución, CPU ociosa y registro de cada cambio de contexto. |
| 4 | Calcular métricas | Tiempo de espera, de retorno y de respuesta por proceso y promedios. |
| 5 | Comparar algoritmos | Los 4 algoritmos con el mismo conjunto de procesos, en tabla y gráfica. |
| 6 | Cargar y exportar | Escenarios en CSV, resultados en CSV y el Gantt en PNG. |
| 7 | Historial | Escenarios y simulaciones guardados en SQLite, con opción de reabrirlos. |
| 8 | Paso a paso (Fase II) | Recorre la simulación unidad por unidad: proceso en CPU, cola de listos, estados, ráfaga restante y bitácora de eventos. |
| 9 | Métricas ampliadas (Fase III) | Utilización de CPU, rendimiento, tiempo ocioso y espera máxima; conclusión de cuál algoritmo gana en cada métrica. |
| 10 | Modo consola (Fase III) | `--consola`: Gantt en texto, métricas, comparación, traza paso a paso y exportación, sin abrir la ventana. |
| 11 | Diagnóstico (Fase III) | `--diagnostico`: revisa Python, Tkinter, Matplotlib, SQLite y el motor, y dice si el equipo está listo. |
| 12 | Ejecutable (Fase III) | `PlanifiCPU.exe` para Windows, generado con PyInstaller; guarda la BD en `%APPDATA%\PlanifiCPU`. |

### Relación con los conceptos de Sistemas Operativos

| Concepto | Cómo se aplica en PlanifiCPU |
|---|---|
| Planificador de corto plazo (despachador) | El motor decide en cada instante qué proceso de la cola de listos pasa a ejecución. |
| Estados de un proceso | Nuevo (registro), listo (cola de listos), ejecución (tramo del Gantt) y terminado. |
| Algoritmos de planificación | FCFS, SJF/SRTF, Round Robin y Prioridad, con sus reglas de selección. |
| Expropiación | Modo no expropiativo vs. expropiativo; quantum en Round Robin. |
| Cambio de contexto | Se cuenta y se registra cada vez que la CPU pasa a otro proceso. |
| Métricas de planificación | Tiempo de espera, retorno y respuesta; tiempos de CPU ociosa. |
| Inanición | Se observa en Prioridad y SJF cuando llegan de forma continua procesos más prioritarios o más cortos; la **espera máxima** la deja ver (experimento E5). |
| Utilización y rendimiento | Porcentaje del tiempo con la CPU ocupada y procesos terminados por unidad de tiempo. |

![Relación con los conceptos de Sistemas Operativos](documentacion/diagramas/05_relacion_conceptos_so.png)

## 8. Arquitectura y estructura general

### 8.1 Componentes y módulos

| Módulo | Archivo(s) | Responsabilidad |
|---|---|---|
| Interfaz gráfica | `gui.py` | Formularios, tablas, pestañas de resultados y diálogos de archivo (Tkinter + Matplotlib). |
| Gestor de procesos | `modelos.py`, `csv_io.py` | Crea y valida los procesos; carga escenarios desde CSV. |
| Motor de planificación | `algoritmos.py` | Un algoritmo por función con una interfaz común: `simular(procesos, algoritmo, quantum, expropiativo)`. |
| Traza paso a paso (Fase II) | `paso_a_paso.py` | Expande el Gantt en instantes con CPU, cola de listos, estados y eventos: `trazar(procesos, resultado)`. |
| Métricas y reportes | `metricas.py`, `modelos.py`, `csv_io.py` | Tiempos por proceso, utilización, rendimiento, espera máxima, comparación y exportación a CSV/PNG. |
| Persistencia | `bd.py`, `bd/schema.sql` | Guarda escenarios, simulaciones, resultados y tramos del Gantt en SQLite (en `%APPDATA%` cuando corre como .exe). |
| Modo consola (Fase III) | `consola.py` | Gantt en texto, métricas, comparación y traza paso a paso en la terminal. |
| Diagnóstico (Fase III) | `diagnostico.py` | Verifica el entorno y corre una autoprueba; devuelve 0 o 1. |
| Punto de entrada | `main.py` | Abre la interfaz o, con opciones, el modo consola o el diagnóstico. |
| Análisis de resultados (Fase III) | `analisis_resultados.py` | Seis experimentos con el motor; genera CSV y gráficas. |

![Diagrama de estructura del producto](documentacion/diagramas/01_estructura_producto.png)

### 8.2 Arquitectura inicial

Arquitectura en **tres capas** dentro de una aplicación de escritorio. La capa de presentación (Tkinter y Matplotlib) recoge datos y muestra resultados, pero no calcula; delega en la capa de lógica, que valida los procesos, ejecuta el algoritmo y calcula las métricas. Solo la capa de datos lee y escribe archivos CSV/PNG y la base de datos SQLite. Así el motor se prueba sin la interfaz.

![Diagrama de arquitectura inicial](documentacion/diagramas/02_arquitectura_inicial.png)

```mermaid
flowchart LR
    U([Usuario]) --> G[Interfaz gráfica<br/>gui.py]
    G -->|procesos, algoritmo, quantum| M[Motor<br/>algoritmos.py]
    M --> V[Validación<br/>modelos.py]
    M --> R[Métricas<br/>metricas.py]
    M -->|Resultado: Gantt + métricas| G
    G -->|Resultado| P[Paso a paso<br/>paso_a_paso.py]
    P -->|instantes| G
    G --> C[Archivos<br/>csv_io.py]
    G --> B[Acceso a datos<br/>bd.py]
    C --> F[(CSV / PNG)]
    B --> D[(SQLite<br/>planificpu.db)]
    T([Terminal]) --> K[Modo consola<br/>consola.py]
    K --> M
    K --> P
    K --> C
    T --> X[Diagnóstico<br/>diagnostico.py]
    X --> M
    X --> B
```

### 8.3 Organización de archivos y directorios

```text
PlanifiCPU_SistemasOperativos_G11/
├── README.md                       # presentación del proyecto (este archivo)
├── CHANGELOG.md                    # cambios de cada versión (1.0, 1.1, 2.0)
├── LICENSE                         # licencia MIT
├── requirements.txt                # dependencias (matplotlib)
├── .github/workflows/              # pruebas en Windows/Linux y construcción del .exe
├── documentacion/
│   ├── descripcion_proyecto.pdf    # descripción y formulación del proyecto
│   ├── requerimientos.pdf          # requerimientos funcionales y no funcionales
│   ├── arquitectura_inicial.pdf    # componentes, arquitectura, archivos y BD
│   ├── tecnologias_y_referencias.pdf
│   ├── diagramas/                  # diagramas en PNG y su fuente HTML
│   ├── fase2/                      # componente paso a paso, pruebas y su salida
│   └── fase3/                      # manual, entorno, pruebas, resultados y evidencias
├── empaquetado/                    # PyInstaller: PlanifiCPU.spec, icono y script .bat
├── src/
│   └── codigo_fuente/
│       ├── main.py                 # punto de entrada (interfaz, --consola, --diagnostico)
│       ├── analisis_resultados.py  # experimentos de la Fase III
│       ├── planificpu/             # gui, algoritmos, paso_a_paso, metricas, modelos,
│       │                           # csv_io, bd, consola, diagnostico
│       └── bd/schema.sql           # esquema de la base de datos
├── recursos/
│   ├── imagenes/                   # capturas (version_final/ = Fase III)
│   └── datos_ejemplo/              # 7 escenarios CSV de ejemplo
└── pruebas/
    ├── test_algoritmos.py          # motor (Fase I)
    ├── test_paso_a_paso.py         # modo paso a paso (Fase II)
    ├── test_validacion_bibliografia.py  # Stallings y Tanenbaum (Fase III)
    ├── test_propiedades.py         # reglas del planificador en cargas aleatorias (Fase III)
    ├── test_version_final.py       # métricas, consola, diagnóstico, BD y rendimiento (Fase III)
    ├── test_interfaz.py            # interfaz gráfica (Fase III)
    └── mutaciones.py               # pruebas de mutación (Fase III)
```

### 8.4 Frontend

Interfaz de escritorio con **Tkinter** (widgets `ttk`) y gráficas de **Matplotlib** incrustadas, con los colores institucionales. Se abre maximizada y tiene un panel izquierdo de trabajo y un panel derecho de resultados con cinco pestañas. Las capturas de esta sección son de la versión final (Fase III); el manual completo está en [manual_usuario.md](documentacion/fase3/manual_usuario.md).

| Sección | Controles |
|---|---|
| 1. Registrar procesos | Campos PID, Llegada, Ráfaga y Prioridad; *Agregar / actualizar*; tabla de procesos (al seleccionar una fila se carga para editarla); *Eliminar*, *Limpiar todo*, *Cargar ejemplo*. |
| 2. Elegir algoritmo | Lista con los 4 algoritmos, quantum (solo Round Robin), *Modo expropiativo* (solo SJF y Prioridad), *Simular*, *Paso a paso* y *Comparar los 4 algoritmos*. |
| 3. Escenarios y reportes | *Cargar CSV*, *Guardar CSV*, *Exportar resultados*, *Guardar en BD*, *Abrir de BD* y *Exportar Gantt PNG*. |

**Diagrama de Gantt** con el registro de ejecución (quién toma la CPU, cambios de contexto, expropiaciones y fin de cada proceso). Cinco procesos con Round Robin q=3:

![Gantt Round Robin](recursos/imagenes/version_final/01_gantt.png)

**Paso a paso** (Fase II): controles para avanzar, retroceder o reproducir; proceso en CPU y cola de listos; Gantt que se construye unidad por unidad; estado de cada proceso y bitácora de eventos. Round Robin q=3 en t=7:

![Paso a paso con Round Robin](recursos/imagenes/version_final/02_paso_a_paso.png)

**Métricas** por proceso con la fila de promedios y, en la versión final, la línea de resumen con tiempo total, CPU ociosa, utilización, rendimiento, espera máxima y cambios de contexto (FCFS, ficha técnica):

![Métricas FCFS](recursos/imagenes/version_final/03_metricas.png)

**Comparación** de los cuatro algoritmos con el mismo conjunto de procesos, con las columnas *Espera máxima* y *Utilización CPU* y la conclusión por métrica:

![Comparación de los 4 algoritmos](recursos/imagenes/version_final/04_comparacion.png)

**Historial (BD)** de simulaciones guardadas:

![Historial de simulaciones](recursos/imagenes/version_final/07_historial.png)

> Las capturas son de la aplicación real con los escenarios de `recursos/datos_ejemplo/`. Las de la versión final se tomaron en Ubuntu 24.04; las de las Fases I y II (Windows 11) siguen en [`recursos/imagenes/`](recursos/imagenes).

### 8.5 Commits

El historial sigue **Conventional Commits** (`tipo(ámbito): descripción`) y registra la creación y cada avance del proyecto:

| # | Commit | Tipo | Qué agrega |
|---|---|---|---|
| 1 | [`96616e3`](https://github.com/daviid0611/PlanifiCPU_SistemasOperativos_G11/commit/96616e3) | chore | Estructura inicial: paquete `planificpu`, `.gitignore` y `requirements.txt`. |
| 2 | [`435a2b2`](https://github.com/daviid0611/PlanifiCPU_SistemasOperativos_G11/commit/435a2b2) | feat(motor) | Modelos `Proceso`, `Segmento`, `Resultado` y validación de datos. |
| 3 | [`3b0e152`](https://github.com/daviid0611/PlanifiCPU_SistemasOperativos_G11/commit/3b0e152) | feat(motor) | Algoritmos FCFS, SJF, Round Robin y Prioridad, y cálculo de métricas. |
| 4 | [`ede08a4`](https://github.com/daviid0611/PlanifiCPU_SistemasOperativos_G11/commit/ede08a4) | feat(csv) | Carga de escenarios y exportación de resultados en CSV. |
| 5 | [`f6231b3`](https://github.com/daviid0611/PlanifiCPU_SistemasOperativos_G11/commit/f6231b3) | feat(bd) | Esquema SQLite y persistencia de escenarios y simulaciones. |
| 6 | [`3122de2`](https://github.com/daviid0611/PlanifiCPU_SistemasOperativos_G11/commit/3122de2) | feat(gui) | Interfaz Tkinter con Gantt, métricas, comparación e historial. |
| 7 | [`0c245e2`](https://github.com/daviid0611/PlanifiCPU_SistemasOperativos_G11/commit/0c245e2) | test | 13 pruebas automáticas del motor. |
| 8 | [`bd8ddd9`](https://github.com/daviid0611/PlanifiCPU_SistemasOperativos_G11/commit/bd8ddd9) | docs | Capturas reales de la interfaz. |
| 9 | [`a65d8de`](https://github.com/daviid0611/PlanifiCPU_SistemasOperativos_G11/commit/a65d8de) | docs | Primera versión del README. |
| 10 | [`53d48d6`](https://github.com/daviid0611/PlanifiCPU_SistemasOperativos_G11/commit/53d48d6) | refactor | Estructura de carpetas de la guía (`src/`, `pruebas/`, `recursos/`, `documentacion/`) y licencia MIT. |
| 11 | [`6769e16`](https://github.com/daviid0611/PlanifiCPU_SistemasOperativos_G11/commit/6769e16) | docs | Diagramas de estructura, arquitectura, archivos, modelo relacional y conceptos de S.O. |
| 12 | [`286ce53`](https://github.com/daviid0611/PlanifiCPU_SistemasOperativos_G11/commit/286ce53) | docs | Documentos PDF de la carpeta `documentacion/`. |
| 13 | [`76865e6`](https://github.com/daviid0611/PlanifiCPU_SistemasOperativos_G11/commit/76865e6) | docs | README completo según la guía. |
| 14 | [`09f7f5e`](https://github.com/daviid0611/PlanifiCPU_SistemasOperativos_G11/commit/09f7f5e) | chore | `.gitattributes` para que GitHub no cuente los HTML de diagramas como código; ajuste del encabezado del README. |
| 15 | [`491e0f4`](https://github.com/daviid0611/PlanifiCPU_SistemasOperativos_G11/commit/491e0f4) | feat(paso-a-paso) | **Fase II.** Módulo `paso_a_paso.py`: traza instante por instante con CPU, cola de listos, estados y eventos. |
| 16 | [`2f8faf3`](https://github.com/daviid0611/PlanifiCPU_SistemasOperativos_G11/commit/2f8faf3) | test(paso-a-paso) | **Fase II.** 14 pruebas: casos límite y 420 simulaciones aleatorias contra el motor. |
| 17 | [`6f3bd28`](https://github.com/daviid0611/PlanifiCPU_SistemasOperativos_G11/commit/6f3bd28) | feat(gui) | **Fase II.** Pestaña *Paso a paso* con controles, reproducción, Gantt parcial y bitácora. |
| 18 | [`0add69c`](https://github.com/daviid0611/PlanifiCPU_SistemasOperativos_G11/commit/0add69c) | docs | **Fase II.** Capturas y animación del modo paso a paso. |
| 19 | [`a8a8221`](https://github.com/daviid0611/PlanifiCPU_SistemasOperativos_G11/commit/a8a8221) | docs(fase2) | **Fase II.** Documentación del componente y reporte de pruebas. |
| 20 | [`5bc5f54`](https://github.com/daviid0611/PlanifiCPU_SistemasOperativos_G11/commit/5bc5f54) | docs | **Fase II.** README actualizado con el avance, el entorno, las pruebas y las evidencias. |
| 21 | [`3e786e4`](https://github.com/daviid0611/PlanifiCPU_SistemasOperativos_G11/commit/3e786e4) | feat(metricas) | **Fase III.** Utilización de CPU, rendimiento, tiempo ocioso y espera máxima; exportación CSV ampliada. |
| 22 | [`f53d534`](https://github.com/daviid0611/PlanifiCPU_SistemasOperativos_G11/commit/f53d534) | fix(bd) | **Fase III.** La BD del ejecutable se guarda en `%APPDATA%\PlanifiCPU`. |
| 23 | [`8ab0534`](https://github.com/daviid0611/PlanifiCPU_SistemasOperativos_G11/commit/8ab0534) | feat(consola) | **Fase III.** Modo consola, diagnóstico del entorno y versión 2.0.0. |
| 24 | [`b78d9eb`](https://github.com/daviid0611/PlanifiCPU_SistemasOperativos_G11/commit/b78d9eb) | feat(gui) | **Fase III.** Métricas nuevas en la interfaz, conclusión de la comparación, icono y ajustes para 1366 × 768. |
| 25 | [`bed0d4b`](https://github.com/daviid0611/PlanifiCPU_SistemasOperativos_G11/commit/bed0d4b) | build | **Fase III.** Empaquetado como ejecutable de Windows con PyInstaller. |
| 26 | [`66bc323`](https://github.com/daviid0611/PlanifiCPU_SistemasOperativos_G11/commit/66bc323) | feat(analisis) | **Fase III.** Experimentos de resultados y cinco escenarios de ejemplo nuevos. |
| 27 | [`c97411e`](https://github.com/daviid0611/PlanifiCPU_SistemasOperativos_G11/commit/c97411e) | test | **Fase III.** 38 pruebas nuevas (bibliografía, propiedades, interfaz, versión final) y pruebas de mutación. |
| 28 | [`431a5b9`](https://github.com/daviid0611/PlanifiCPU_SistemasOperativos_G11/commit/431a5b9) | ci | **Fase III.** GitHub Actions: pruebas en Windows y Linux y construcción del `.exe`. |
| 29 | [`af2d3e8`](https://github.com/daviid0611/PlanifiCPU_SistemasOperativos_G11/commit/af2d3e8) | docs(fase3) | **Fase III.** Resultados obtenidos con tablas y gráficas. |
| 30 | [`37a842b`](https://github.com/daviid0611/PlanifiCPU_SistemasOperativos_G11/commit/37a842b) | docs(fase3) | **Fase III.** Manual de usuario, configuración del entorno, reporte de pruebas y evidencias. |
| 31 | [`bceb9c6`](https://github.com/daviid0611/PlanifiCPU_SistemasOperativos_G11/commit/bceb9c6) | docs | **Fase III.** Capturas de la versión final. |
| 32 | [`c91381d`](https://github.com/daviid0611/PlanifiCPU_SistemasOperativos_G11/commit/c91381d) | docs | **Fase III.** Registro de cambios (`CHANGELOG.md`). |
| 33 | último commit | docs | **Fase III.** README de la versión final. |

Historial completo: [commits/main](https://github.com/daviid0611/PlanifiCPU_SistemasOperativos_G11/commits/main)

### 8.6 Base de datos

| Aspecto | Detalle |
|---|---|
| Motor | **SQLite 3** (módulo `sqlite3` de Python). |
| Archivo | `src/codigo_fuente/bd/planificpu.db`; se crea solo la primera vez que se abre la aplicación. No se sube a GitHub. |
| Esquema | [`src/codigo_fuente/bd/schema.sql`](src/codigo_fuente/bd/schema.sql), con `CREATE TABLE IF NOT EXISTS`. |
| Integridad | `PRAGMA foreign_keys = ON`, restricciones `CHECK` (ráfaga ≥ 1, llegada ≥ 0, quantum ≥ 1) y `UNIQUE (id_escenario, pid)`. |
| Borrado | `ON DELETE CASCADE`: al eliminar un escenario se borran sus procesos, simulaciones, resultados y tramos. |
| Guardado | Cada *Simular* o *Comparar* guarda la simulación; si el escenario no tiene nombre, se crea uno con la fecha y hora. |

| Tabla | Qué guarda |
|---|---|
| `algoritmo` | Catálogo de los 4 algoritmos y si permiten expropiación o usan quantum. |
| `escenario` | Conjunto de procesos con nombre y fecha de creación. |
| `proceso` | Procesos de cada escenario (PID, llegada, ráfaga, prioridad y orden de registro). |
| `simulacion` | Cada ejecución de un algoritmo sobre un escenario, con quantum, modo y promedios. |
| `resultado_proceso` | Métricas de cada proceso en una simulación. |
| `segmento_gantt` | Tramos del Gantt en orden; `id_proceso` nulo = CPU ociosa. |

### 8.7 Modelo relacional

![Modelo relacional](documentacion/diagramas/04_modelo_relacional.png)

| Relación | Cardinalidad | Explicación |
|---|---|---|
| ESCENARIO – PROCESO | 1 : N | Un escenario tiene varios procesos; cada proceso pertenece a uno solo. |
| ESCENARIO – SIMULACION | 1 : N | El mismo escenario se puede simular muchas veces. |
| ALGORITMO – SIMULACION | 1 : N | Cada simulación usa un algoritmo del catálogo. |
| SIMULACION – PROCESO | N : M | Se resuelve con RESULTADO_PROCESO, que guarda las métricas de cada proceso en cada simulación. |
| SIMULACION – SEGMENTO_GANTT | 1 : N | Una simulación tiene varios tramos ordenados. |
| PROCESO – SEGMENTO_GANTT | 0..1 : N | Un tramo pertenece a un proceso o a ninguno (CPU ociosa). |

**Normalización.** Tercera forma normal (3FN): cada atributo depende solo de la llave de su tabla y los datos del proceso no se repiten en los resultados. Los promedios de `simulacion` son datos derivados que se guardan a propósito para consultar el historial sin recalcular.

## 9. Tecnologías utilizadas

| Tecnología / herramienta | Versión | Uso en el proyecto | Por qué se eligió |
|---|---|---|---|
| **Python** | 3.12+ (probado en 3.14.6) | Lenguaje de toda la aplicación. | Visto en la carrera, sintaxis clara para los algoritmos, librería estándar amplia. |
| **Tkinter / ttk** | Tk 8.6 (incluido) | Interfaz gráfica de escritorio. | Viene con Python y funciona en Windows 10/11 sin instalar nada más. |
| **Matplotlib** | 3.8+ (probado en 3.11.2) | Diagrama de Gantt y gráfica comparativa. | Librería estándar de gráficas; exporta el Gantt a PNG. |
| **SQLite** | 3 (probado en 3.50.4) | Base de datos local de escenarios e historial. | Un solo archivo, sin servidor ni usuarios. |
| **csv, argparse y unittest** | Librería estándar | Archivos CSV, modo consola y pruebas automáticas. | Sin dependencias externas. |
| **PyInstaller** | 6.x (probado en 6.22) | Ejecutable `PlanifiCPU.exe` de un solo archivo. | Empaqueta Python, Tkinter y Matplotlib para usar la app sin instalar nada. |
| **GitHub Actions** | `windows-latest`, `ubuntu-latest` | Pruebas en cada `push` y construcción del `.exe` en cada versión. | Verifica que el proyecto funcione en Windows y Linux, no solo en un equipo. |
| **Xvfb** | Ubuntu 24.04 | Pantalla virtual para probar la interfaz en Linux sin monitor. | Permite correr las pruebas de la interfaz en servidores. |
| **Git y GitHub** | Git 2.54 | Control de versiones y repositorio público. | Centraliza el desarrollo y evidencia los avances. |
| **Visual Studio Code** | Actual | Editor de código. | Ligero, con soporte para Python y Git. |
| **HTML/CSS + Chrome** | Actual | Diagramas y documentos PDF. | Diagramas versionables como texto y exportables a PNG/PDF. |
| **Microsoft Word** | Microsoft 365 | Documento técnico en formato APA 7. | Plantilla institucional de la universidad. |
| **Windows 10/11** | 64 bits | Sistema operativo de desarrollo y ejecución. | Sistema de los equipos de estudiantes y docente. |

## 10. Requisitos iniciales de ejecución

| Hardware | Mínimo recomendado |
|---|---|
| Procesador | Doble núcleo de 1,6 GHz o superior |
| Memoria RAM | 4 GB (recomendado 8 GB) |
| Almacenamiento | 500 MB libres |
| Pantalla | 1366 × 768 o superior |

| Software | Requisito |
|---|---|
| Sistema operativo | Windows 10 u 11 de 64 bits (entorno previsto); también Linux y macOS con Python |
| Intérprete | Python 3.12 o superior, con Tkinter y sqlite3 (incluidos en el instalador oficial). No se necesita con el `.exe`. |
| Librerías | Matplotlib 3.8 o superior |

No requiere virtualización, servidor ni conexión a internet. La guía paso a paso (Windows, Linux, ejecutable y problemas frecuentes) está en [configuracion_entorno.md](documentacion/fase3/configuracion_entorno.md).

**Con el ejecutable (sin Python):** descargue `PlanifiCPU.exe` de [Releases](https://github.com/daviid0611/PlanifiCPU_SistemasOperativos_G11/releases) o genérelo con [`empaquetado/empaquetar_windows.bat`](empaquetado/empaquetar_windows.bat), y ábralo con doble clic.

**Instalación y ejecución**

```bash
git clone https://github.com/daviid0611/PlanifiCPU_SistemasOperativos_G11.git
cd PlanifiCPU_SistemasOperativos_G11
python -m pip install -r requirements.txt
python src/codigo_fuente/main.py --diagnostico   # opcional: verifica el entorno
python src/codigo_fuente/main.py
```

**Uso básico**

1. Pulse **Cargar ejemplo** o **Cargar CSV** (archivos en `recursos/datos_ejemplo/`), o registre los procesos uno a uno.
2. Elija el algoritmo; para Round Robin indique el quantum.
3. Pulse **Simular** para ver el Gantt y las métricas, **Paso a paso** para recorrer la ejecución instante por instante (botones o flechas del teclado), o **Comparar los 4 algoritmos**.
4. Exporte los resultados (CSV) o el Gantt (PNG). Cada simulación queda en el **Historial (BD)**.

Formato del CSV (coma o punto y coma; `prioridad` es opcional):

```csv
pid;llegada;rafaga;prioridad
P1;0;5;2
P2;1;3;1
P3;2;4;3
```

**Modo consola** (sin abrir la ventana):

```bash
python src/codigo_fuente/main.py --consola recursos/datos_ejemplo/ejemplo_cinco_procesos.csv -a rr -q 3
python src/codigo_fuente/main.py --consola recursos/datos_ejemplo/stallings.csv --comparar --exportar resultados.csv
python src/codigo_fuente/main.py --consola -a srtf --traza
```

**Pruebas automáticas** (65 pruebas: motor, paso a paso, bibliografía, propiedades, versión final e interfaz) y **pruebas de mutación**:

```bash
python -m unittest discover -s pruebas -v
python pruebas/mutaciones.py
```

## 11. Integrantes del equipo

| Integrante | Usuario de GitHub | Rol en el proyecto |
|---|---|---|
| David Zambrano | [@daviid0611](https://github.com/daviid0611) | Integrante |
| Daniel Pérez | [@monarca1290](https://github.com/monarca1290) | Integrante |
| Axel Salgado | [@AxelN28](https://github.com/AxelN28) | Integrante |

Grupo G11 · Sistemas Operativos · Facultad de Ingeniería · Universidad Manuela Beltrán.

## 12. Estado actual y próximos avances

**Estado actual: versión 2.0.0, final (Fase III).** Están implementados los cuatro algoritmos (con y sin expropiación), el diagrama de Gantt con registro de ejecución, el modo paso a paso, las métricas (incluidas utilización, rendimiento y espera máxima), la comparación de algoritmos, la carga y exportación en CSV/PNG, la base de datos SQLite con historial, el modo consola, el diagnóstico del entorno y el ejecutable de Windows. Pasan 65 pruebas automáticas y se detectan 10 de 10 mutaciones.

**Avances**

- [x] Modo paso a paso: avanzar la simulación unidad por unidad mostrando la cola de listos en cada instante (Fase II).
- [x] Pruebas con casos límite del modo paso a paso: misma llegada, CPU ociosa, quantum grande y 420 simulaciones aleatorias (Fase II).
- [x] Validar el simulador con ejercicios resueltos de la bibliografía del curso: Silberschatz, Stallings (tabla 9.5) y Tanenbaum (Fase III).
- [x] Manual de usuario con capturas: [manual_usuario.md](documentacion/fase3/manual_usuario.md) (Fase III).
- [x] Empaquetar la aplicación como ejecutable `.exe` para Windows con PyInstaller (Fase III).
- [x] Métricas de utilización, rendimiento y espera máxima; modo consola y diagnóstico (Fase III).
- [x] Pruebas de la interfaz, propiedades, mutación e integración continua en Windows y Linux (Fase III).

El trabajo futuro está en la [sección 14.7](#147-conclusiones-y-trabajo-futuro).

## 13. Fase II: avance realizado

**Objetivo de la fase.** Pasar de mostrar solo el resultado final a mostrar **cómo decide el planificador de corto plazo** en cada instante, que es lo que en papel no se ve (problemática 3 de la sección 4).

| Evidencia pedida | Dónde está |
|---|---|
| Avance funcional | Modo **paso a paso** en la interfaz: botón *Paso a paso* y pestaña nueva ([animación](recursos/imagenes/08_paso_a_paso.gif)). |
| Configuración del entorno | Tabla siguiente y [sección 10](#10-requisitos-iniciales-de-ejecución). |
| Componentes principales | [`paso_a_paso.py`](src/codigo_fuente/planificpu/paso_a_paso.py) (lógica) y la pestaña en [`gui.py`](src/codigo_fuente/planificpu/gui.py), documentados en [componente_paso_a_paso.md](documentacion/fase2/componente_paso_a_paso.md). |
| Pruebas de funcionamiento | [`test_paso_a_paso.py`](pruebas/test_paso_a_paso.py) y el reporte [pruebas_fase2.md](documentacion/fase2/pruebas_fase2.md): 27 de 27 correctas ([salida](documentacion/fase2/salida_pruebas.txt)). |
| Evidencias del desarrollo | Capturas [06](recursos/imagenes/06_paso_a_paso_round_robin.png) y [07](recursos/imagenes/07_paso_a_paso_srtf_expropiacion.png), animación [08](recursos/imagenes/08_paso_a_paso.gif) y commits de la fase. |

**Configuración del entorno de trabajo**

| Elemento | Configuración usada |
|---|---|
| Sistema operativo | Windows 11 de 64 bits con escalado de pantalla; `main.py` activa `SetProcessDpiAwareness(1)` para que la interfaz se vea nítida. |
| Intérprete | Python 3.14.6 (instalador oficial, con Tkinter 8.6 y sqlite3). |
| Dependencias | `python -m pip install -r requirements.txt` (Matplotlib 3.11.2). Opcional: entorno virtual con `python -m venv .venv` y `.venv\Scripts\activate`; la carpeta `.venv/` está en `.gitignore`. |
| Base de datos | SQLite 3.50.4; `src/codigo_fuente/bd/planificpu.db` se crea sola desde `schema.sql` en la primera ejecución. |
| Control de versiones | Git 2.54 y GitHub, rama `main`, mensajes con Conventional Commits. |

**Qué muestra el modo paso a paso en cada instante `t`**

- Proceso en la **CPU** (o CPU ociosa) y cuánto le falta.
- **Cola de listos** en el orden en que el planificador los atenderá; en Round Robin, el orden real de la cola FIFO.
- **Estado** de cada proceso (Nuevo, Listo, En ejecución, Terminado) y su ráfaga restante.
- **Bitácora**: llegadas, despachos, expropiaciones, fin de quantum, cambios de contexto y terminaciones.
- **Gantt parcial** que se construye unidad por unidad, con la unidad actual resaltada.

![Expropiación en SRTF](recursos/imagenes/07_paso_a_paso_srtf_expropiacion.png)

**Resultados obtenidos**

- El paso a paso se calcula a partir del Gantt del motor, así que **siempre coincide** con el Gantt y las métricas de la Fase I; la prueba con 420 simulaciones aleatorias lo comprueba instante por instante.
- El ejercicio de cinco procesos con Round Robin (q=3) se verificó a mano en t=7: CPU P3, cola P4, P1, P2 ([verificación](documentacion/fase2/pruebas_fase2.md)).
- Las funciones de la Fase I (Simular, Comparar, CSV, BD) siguen funcionando: sus 13 pruebas pasan sin cambios.

**Commits de la Fase II**: filas 15 a 20 de la [sección 8.5](#85-commits).

## 14. Fase III: versión final

**Objetivo de la fase.** Consolidar en una versión final (2.0.0) lo construido en las Fases I y II, cerrar los pendientes que dejó la Fase II y demostrar con pruebas y datos que el simulador cumple los objetivos del proyecto.

### 14.1 Evidencias de la entrega

| Lo que pide la guía | Dónde está |
|---|---|
| Solución final implementada | Versión 2.0.0 en `main`: [código fuente](src/codigo_fuente), [ejecutable de Windows](empaquetado) y [registro de cambios](CHANGELOG.md). |
| Funcionamiento de los componentes | [Sección 14.2](#142-solución-final-y-componentes), [capturas de la versión final](recursos/imagenes/version_final) y [manual de usuario](documentacion/fase3/manual_usuario.md). |
| Configuración del sistema operativo o entorno | [Sección 14.3](#143-configuración-del-entorno), [configuracion_entorno.md](documentacion/fase3/configuracion_entorno.md) y el comando `--diagnostico`. |
| Pruebas de funcionamiento | [Sección 14.4](#144-pruebas-de-funcionamiento), [pruebas_fase3.md](documentacion/fase3/pruebas_fase3.md), [salida de las 65 pruebas](documentacion/fase3/salida_pruebas.txt) y [salida de las mutaciones](documentacion/fase3/salida_mutaciones.txt). |
| Resultados obtenidos | [Sección 14.5](#145-resultados-obtenidos) y [resultados.md](documentacion/fase3/resultados.md) con sus [CSV y gráficas](documentacion/fase3/resultados). |
| Documentación básica del proyecto | Este README, la [sección 15](#15-documentación-técnica-y-referencias), los PDF de la Fase I y los documentos de las fases II y III. |
| Repositorio actualizado con la versión final | Rama `main` con la versión 2.0.0. |
| Código fuente organizado | Capas separadas ([sección 8.1](#81-componentes-y-módulos)) y estructura de la guía ([sección 8.3](#83-organización-de-archivos-y-directorios)). |
| Evidencias de funcionamiento | Capturas de la interfaz y de la terminal, salidas en [`documentacion/fase3/evidencias/`](documentacion/fase3/evidencias) y la pestaña [Actions](https://github.com/daviid0611/PlanifiCPU_SistemasOperativos_G11/actions) con cada ejecución de las pruebas. |
| Registro de avances mediante commits | 33 commits con Conventional Commits; los de esta fase son las filas 21 a 33 de la [sección 8.5](#85-commits). |
| Pruebas realizadas y resultados obtenidos | Secciones [14.4](#144-pruebas-de-funcionamiento) y [14.5](#145-resultados-obtenidos). |

### 14.2 Solución final y componentes

Cambios de la versión final sobre la Fase II (detalle en el [CHANGELOG](CHANGELOG.md)):

| Componente | Qué se agregó o cambió | Evidencia |
|---|---|---|
| Métricas (`modelos.py`, `csv_io.py`) | Utilización de CPU, rendimiento, tiempo ocioso y espera máxima, también en la exportación CSV. | [Captura](recursos/imagenes/version_final/03_metricas.png) |
| Interfaz (`gui.py`) | Resumen de métricas, columnas nuevas y conclusión en *Comparación*, versión e icono, y distribución que cabe en 1366 × 768. | [Captura](recursos/imagenes/version_final/05_comparacion_expropiativa.png) |
| Modo consola (`consola.py`) | Gantt en texto, métricas, comparación, traza paso a paso y exportación. | [Captura](recursos/imagenes/version_final/08_modo_consola.png) |
| Diagnóstico (`diagnostico.py`) | Revisión del entorno y autoprueba con código de salida. | [Captura](recursos/imagenes/version_final/10_diagnostico_y_pruebas.png) |
| Persistencia (`bd.py`) | En el ejecutable, la BD va a `%APPDATA%\PlanifiCPU`; variable `PLANIFICPU_BD` para otra ruta. | `test_ejecutable_guarda_en_appdata` |
| Empaquetado (`empaquetado/`) | `PlanifiCPU.spec`, icono y `empaquetar_windows.bat`. | [Guía](documentacion/fase3/configuracion_entorno.md#3-opción-a-ejecutable-de-windows-sin-instalar-python) |
| Integración continua (`.github/workflows/`) | Pruebas en Windows y Ubuntu con Python 3.12 y 3.13; `.exe` en cada versión. | Insignia *Pruebas* al inicio |
| Análisis (`analisis_resultados.py`) | Seis experimentos reproducibles. | [resultados.md](documentacion/fase3/resultados.md) |

La espera máxima se agregó porque el promedio puede esconder la inanición. Con [`inanicion.csv`](recursos/datos_ejemplo/inanicion.csv) y Prioridad, la espera promedio es la menor de los cuatro algoritmos (1,57), pero el proceso BAJA espera 11 unidades:

![Inanición revelada por la espera máxima](recursos/imagenes/version_final/06_inanicion_metricas.png)

El modo consola da los mismos resultados que la interfaz, porque usa el mismo motor:

![Comparación y traza en la terminal](recursos/imagenes/version_final/09_consola_comparacion_y_traza.png)

### 14.3 Configuración del entorno

| Entorno | Sistema operativo | Python | Qué se ejecutó |
|---|---|---|---|
| Desarrollo (Fases I y II) | Windows 11, 64 bits | 3.14.6 | Aplicación, 27 pruebas y capturas de esas fases |
| Versión final (Fase III) | Ubuntu 24.04, x86_64, con Xvfb | 3.12.3 | Aplicación, 65 pruebas, mutaciones, análisis, ejecutable con PyInstaller y capturas de la versión final |
| GitHub Actions | `windows-latest` y `ubuntu-latest` | 3.12 y 3.13 | Diagnóstico, pruebas, mutaciones y modo consola en cada `push`; `.exe` en cada etiqueta `v*` |

Pasos resumidos en Windows (la guía completa, con Linux, el ejecutable y los problemas frecuentes, está en [configuracion_entorno.md](documentacion/fase3/configuracion_entorno.md)):

1. Instalar Python 3.12+ marcando *Add python.exe to PATH* y *tcl/tk and IDLE*.
2. `git clone`, crear el entorno virtual (`python -m venv .venv` y `.venv\Scripts\activate`) e instalar `requirements.txt`.
3. Verificar con `python src/codigo_fuente/main.py --diagnostico`: todos los chequeos deben salir en OK.
4. Ejecutar `python src/codigo_fuente/main.py`, o usar `PlanifiCPU.exe` sin instalar nada.

![Diagnóstico del entorno, pruebas y mutaciones](recursos/imagenes/version_final/10_diagnostico_y_pruebas.png)

### 14.4 Pruebas de funcionamiento

| Tipo | Archivo | Pruebas | Resultado |
|---|---|---|---|
| Motor (Fase I) | `test_algoritmos.py` | 13 | 13 OK |
| Paso a paso (Fase II) | `test_paso_a_paso.py` | 14 | 14 OK |
| Validación con la bibliografía | `test_validacion_bibliografia.py` | 5 | 5 OK |
| Propiedades del planificador | `test_propiedades.py` | 9 | 9 OK |
| Funciones de la versión final | `test_version_final.py` | 17 | 17 OK |
| Interfaz gráfica | `test_interfaz.py` | 7 | 7 OK |
| **Total automáticas** | | **65** | **65 OK** |
| Mutación | `mutaciones.py` | 10 errores introducidos | 10 detectados |
| Manuales | [pruebas_fase3.md §7](documentacion/fase3/pruebas_fase3.md#7-pruebas-manuales) | 12 | 12 OK |

- **Validación externa:** el motor reproduce exactamente los ejercicios publicados por Silberschatz (SJF 7,0; SRTF 6,5; RR q=4 17/3; Prioridad 8,2), Stallings (tabla 9.5: FCFS 8,60; RR q=1 10,80; RR q=4 10,00; SPN 7,60; SRT 7,20) y Tanenbaum (FCFS 14; SJF 11).
- **Propiedades:** en miles de simulaciones aleatorias se comprueba que el Gantt no tiene huecos ni solapes, que cada proceso recibe su ráfaga completa, que la CPU nunca queda ociosa con procesos listos, que se respetan las reglas de desempate y que SRTF nunca es superado en espera promedio.
- **Mutación:** se introducen 10 errores a propósito (empates, cola de Round Robin, quantum, prioridad invertida, métricas, validación) y las pruebas detectan los 10.
- **Rendimiento (RNF05):** una prueba falla si 50 procesos tardan 1 segundo o más.

```bash
python -m unittest discover -s pruebas -v
python pruebas/mutaciones.py
```

### 14.5 Resultados obtenidos

El script [`analisis_resultados.py`](src/codigo_fuente/analisis_resultados.py) corre seis experimentos con el mismo motor (análisis completo en [resultados.md](documentacion/fase3/resultados.md)):

| Experimento | Resultado principal |
|---|---|
| E1. Seis escenarios de ejemplo | SRTF tiene la menor espera promedio en los seis; Round Robin la mayor en tres, aunque con una de las mejores respuestas. |
| E2. 500 cargas aleatorias | SRTF da la menor espera en el **100 %** de las cargas (7,97 promedio); Round Robin q=3 la menor respuesta en el 74,4 % (5,60), con más del doble de cambios de contexto (16,11 frente a 7). |
| E3. Quantum de 1 a 12 | Con q=1 la respuesta es 1,88 pero hay 40 cambios de contexto; desde q=10 (la ráfaga máxima) Round Robin es igual a FCFS. |
| E4. Efecto convoy | Con los mismos procesos, FCFS pasa de 2,80 a 17,00 de espera promedio si el proceso largo llega primero. |
| E5. Inanición | Con Prioridad, SJF y SRTF la espera del proceso de baja prioridad crece sin límite (2k − 1); con FCFS y Round Robin se mantiene en 1. |
| E6. Tiempo de ejecución | 50 procesos con traza paso a paso en 7,67 ms (límite del RNF05: 1 s); 1000 procesos en menos de 0,7 s con cualquier algoritmo. |

![Promedio sobre 500 cargas aleatorias](documentacion/fase3/resultados/e2_cargas_aleatorias.png)

![Round Robin según el quantum](documentacion/fase3/resultados/e3_sensibilidad_quantum.png)

### 14.6 Cumplimiento de objetivos y requerimientos

| Objetivo | Estado | Evidencia |
|---|---|---|
| **General:** simular FCFS, SJF, Round Robin y Prioridad, visualizar con Gantt cómo se asigna la CPU y comparar con métricas | Cumplido | Secciones 7, 8.4 y 14; 65 pruebas |
| 1. Implementar los algoritmos con y sin expropiación | Cumplido | `algoritmos.py`; validación con tres libros y pruebas de propiedades |
| 2. Generar el Gantt y el registro de cambios de contexto | Cumplido | Pestañas *Diagrama de Gantt* y *Paso a paso*; Gantt en texto en el modo consola |
| 3. Calcular espera, retorno y respuesta por proceso y en promedio | Cumplido | Pestaña *Métricas*, más utilización, rendimiento y espera máxima |
| 4. Comparar los cuatro algoritmos con tabla y gráfica | Cumplido | Pestaña *Comparación*, `--comparar` y experimentos E1–E5 |
| 5. Guardar escenarios y resultados en CSV y SQLite | Cumplido | *Cargar/Guardar CSV*, *Exportar resultados*, *Historial (BD)* |

| Requerimiento | Estado | Evidencia |
|---|---|---|
| RF01 Registrar, editar y eliminar procesos | Cumplido | `test_agregar_y_editar_proceso` |
| RF02 Validar los datos | Cumplido | `test_validacion_de_datos`, `test_pid_repetido`, mutación M10 |
| RF03 Elegir el algoritmo | Cumplido | `test_algoritmos.py`, `test_validacion_bibliografia.py` |
| RF04 Modo expropiativo | Cumplido | `test_expropiativos_respetan_la_regla_de_seleccion` |
| RF05 Gantt y cambios de contexto | Cumplido | `test_invariantes_en_escenarios_aleatorios`, `test_paso_a_paso.py` |
| RF06 Métricas y promedios | Cumplido | `test_tiempos_de_fin_y_retorno`, `test_ficha_tecnica` |
| RF07 Comparar los 4 algoritmos | Cumplido | `test_comparar_los_cuatro_algoritmos` |
| RF08 CSV y PNG | Cumplido | `test_exportar_csv_y_png`, `test_csv_ida_y_vuelta` |
| RF09 BD e historial | Cumplido | `test_guardar_y_abrir_escenario_de_la_bd`, `test_bd_guarda_escenario_y_simulacion` |
| RNF01 Portabilidad | Cumplido | Ejecutable de Windows; pruebas en Windows y Linux con GitHub Actions |
| RNF02 Usabilidad | Cumplido | Interfaz en español por pasos, coma decimal, manual de usuario |
| RNF03 Exactitud | Cumplido | Tres libros, propiedades y 10/10 mutaciones |
| RNF04 Mantenibilidad | Cumplido | Motor sin Tkinter; la consola y la interfaz usan el mismo motor |
| RNF05 Rendimiento | Cumplido | 7,67 ms con 50 procesos; `test_50_procesos_en_menos_de_un_segundo` |
| RNF06 Integridad de datos | Cumplido | Llaves foráneas, CHECK y cascada; `test_entorno_listo` revisa el esquema |
| RNF07 Control de versiones | Cumplido | 33 commits con Conventional Commits y CI en cada `push` |

### 14.7 Conclusiones y trabajo futuro

**Conclusiones**

1. PlanifiCPU cumple el objetivo general y los cinco específicos: simula los cuatro algoritmos con y sin expropiación, muestra el Gantt y la ejecución paso a paso, calcula las métricas y compara los algoritmos con el mismo conjunto de procesos.
2. Los resultados coinciden con los ejercicios publicados en Silberschatz, Stallings y Tanenbaum, así que la herramienta sirve para comprobar los ejercicios que se resuelven a mano en el curso.
3. Los experimentos confirman la teoría con datos: no hay un algoritmo mejor en todo. SRTF minimiza la espera, Round Robin la respuesta y los no expropiativos los cambios de contexto; FCFS sufre el efecto convoy y Prioridad sin envejecimiento produce inanición.
4. Separar el motor de la interfaz permitió probarlo a fondo (65 pruebas, propiedades y mutación) y reutilizarlo en el modo consola y en el análisis de resultados sin duplicar código.

**Trabajo futuro**

- Algoritmos adicionales: HRRN, colas multinivel con retroalimentación (MLFQ) y prioridad con envejecimiento para corregir la inanición.
- Ráfagas de E/S y estados bloqueados, y simulación con varios núcleos.
- Costo configurable del cambio de contexto para ver su efecto en Round Robin.
- Agregar como casos de prueba los ejercicios que proponga el docente en clase.

## 15. Documentación técnica y referencias

| Documento | Contenido |
|---|---|
| [descripcion_proyecto.pdf](documentacion/descripcion_proyecto.pdf) | Descripción y formulación: problemática, justificación, objetivos, alcance, usuarios, funcionalidades y relación con S.O. |
| [requerimientos.pdf](documentacion/requerimientos.pdf) | Requerimientos funcionales y no funcionales, reglas de cálculo, hardware y software. |
| [arquitectura_inicial.pdf](documentacion/arquitectura_inicial.pdf) | Componentes, diagrama de estructura, arquitectura, organización de archivos y modelo relacional. |
| [tecnologias_y_referencias.pdf](documentacion/tecnologias_y_referencias.pdf) | Relación de tecnologías y herramientas, y referencias bibliográficas. |
| [diagramas/](documentacion/diagramas) | Diagramas en PNG con su fuente HTML. |
| [fase2/componente_paso_a_paso.md](documentacion/fase2/componente_paso_a_paso.md) | Fase II: diseño, estructura de datos, eventos y decisiones del modo paso a paso. |
| [fase2/pruebas_fase2.md](documentacion/fase2/pruebas_fase2.md) | Fase II: pruebas automáticas y manuales con sus resultados. |
| [fase3/manual_usuario.md](documentacion/fase3/manual_usuario.md) | Fase III: manual de usuario de la interfaz, el modo consola y el ejercicio guiado. |
| [fase3/configuracion_entorno.md](documentacion/fase3/configuracion_entorno.md) | Fase III: instalación en Windows y Linux, ejecutable, diagnóstico, configuración y problemas frecuentes. |
| [fase3/pruebas_fase3.md](documentacion/fase3/pruebas_fase3.md) | Fase III: 65 pruebas automáticas, mutaciones, pruebas manuales y trazabilidad de requerimientos. |
| [fase3/resultados.md](documentacion/fase3/resultados.md) | Fase III: seis experimentos con tablas, gráficas y conclusiones. |
| [CHANGELOG.md](CHANGELOG.md) | Cambios de cada versión. |

**Referencias**

- Silberschatz, A., Galvin, P. B. y Gagne, G. (2018). *Operating system concepts* (10.ª ed.). Wiley.
- Tanenbaum, A. S. y Bos, H. (2015). *Modern operating systems* (4.ª ed.). Pearson.
- Stallings, W. (2018). *Operating systems: Internals and design principles* (9.ª ed.). Pearson.
- PyInstaller Development Team. (2026). *PyInstaller manual*. https://pyinstaller.org/
- GitHub. (2026). *GitHub Actions documentation*. https://docs.github.com/actions
- Python Software Foundation. (2026). *tkinter* y *sqlite3*. https://docs.python.org/3/library/
- Matplotlib Development Team. (2026). *Matplotlib: Visualization with Python*. https://matplotlib.org/
- SQLite Consortium. (2026). *SQLite documentation*. https://www.sqlite.org/docs.html
- Chacon, S. y Straub, B. (2014). *Pro Git* (2.ª ed.). Apress. https://git-scm.com/book/es/v2

---

Licencia [MIT](LICENSE) · Grupo G11 · Sistemas Operativos · Universidad Manuela Beltrán · 2026
