# Registro de cambios

Todas las versiones de PlanifiCPU. Formato basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/) y numeración [SemVer](https://semver.org/lang/es/).

## [2.0.0] - 2026-11-18 · Fase III: versión final

### Agregado
- Métricas nuevas: **utilización de CPU**, **rendimiento** (procesos por unidad de tiempo), **tiempo ocioso** y **espera máxima** con el proceso que la sufre. Se muestran en las pestañas *Métricas* y *Comparación* y se incluyen al exportar a CSV.
- Conclusión automática en *Comparación*: qué algoritmo gana en espera, respuesta, espera máxima y cambios de contexto.
- **Modo consola** (`--consola`): Gantt en texto, métricas, comparación (`--comparar`), traza paso a paso (`--traza`) y exportación (`--exportar`).
- **Diagnóstico del entorno** (`--diagnostico`) y `--version`.
- **Ejecutable de Windows** con PyInstaller (`empaquetado/`), icono propio y script `empaquetar_windows.bat`.
- GitHub Actions: pruebas en Windows y Ubuntu con Python 3.12 y 3.13, y construcción del `.exe` en cada versión.
- 38 pruebas automáticas nuevas (65 en total): validación con Stallings y Tanenbaum, propiedades del planificador sobre cargas aleatorias, interfaz gráfica, consola, diagnóstico y rendimiento.
- Pruebas de mutación (`pruebas/mutaciones.py`): 10 de 10 errores introducidos detectados.
- Script de análisis de resultados con 6 experimentos, gráficas y CSV (`src/codigo_fuente/analisis_resultados.py`).
- Cinco escenarios de ejemplo nuevos en `recursos/datos_ejemplo/`.
- Documentación final: manual de usuario, configuración del entorno, reporte de pruebas y resultados obtenidos (`documentacion/fase3/`).

### Cambiado
- Panel *Escenarios y reportes* en 2 filas de 3 botones y la casilla de modo expropiativo con su descripción, para que la tabla de procesos se vea completa en pantallas de 1366 × 768.
- La barra de estado se reserva antes que el resto de la ventana y ya no se oculta.
- La tabla de *Comparación* ajusta sus columnas y la conclusión se parte en líneas en ventanas angostas.

### Corregido
- Al ejecutar como `.exe`, la base de datos se guarda en `%APPDATA%\PlanifiCPU\` en lugar de la carpeta temporal del ejecutable, que se borra al cerrarlo.
- Texto de ayuda de la pestaña *Paso a paso* que nombraba un botón inexistente.

## [1.1.0] - 2026-11-11 · Fase II: avance funcional

### Agregado
- Modo **paso a paso**: CPU, cola de listos, estados, bitácora de eventos y Gantt que se construye unidad por unidad, con reproducción automática.
- 14 pruebas del modo paso a paso, incluidas 420 simulaciones aleatorias contra el motor.
- Documentación del componente y reporte de pruebas (`documentacion/fase2/`).

## [1.0.0] - 2026-11-04 · Fase I: planteamiento y primera versión

### Agregado
- Motor con FCFS, SJF (con y sin expropiación), Round Robin y Prioridad (con y sin expropiación).
- Diagrama de Gantt, registro de cambios de contexto y métricas de espera, retorno y respuesta.
- Comparación de los 4 algoritmos, CSV, Gantt en PNG y base de datos SQLite con historial.
- Interfaz Tkinter, 13 pruebas automáticas, diagramas y documentos PDF del proyecto.
