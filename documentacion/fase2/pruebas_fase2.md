# Pruebas de funcionamiento · Fase II

**PlanifiCPU · Grupo G11**

## 1. Cómo ejecutarlas

```bash
python -m unittest discover -s pruebas -v
```

Entorno usado: Windows 11 de 64 bits, Python 3.14.6, Matplotlib 3.11.2, SQLite 3.50.4, Tk 8.6.

**Resultado: 27 pruebas, 27 correctas** (13 de la Fase I + 14 nuevas). Salida completa en [salida_pruebas.txt](salida_pruebas.txt).

## 2. Pruebas automáticas nuevas (`pruebas/test_paso_a_paso.py`)

| # | Prueba | Escenario | Qué verifica | Resultado |
|---|---|---|---|---|
| 1 | `test_un_instante_por_unidad_mas_el_final` | Ficha técnica FCFS (P1 0/5, P2 1/3, P3 2/4) | 13 instantes, de t=0 a t=12. | OK |
| 2 | `test_cola_de_listos` | Ficha técnica FCFS | Cola en t=1 `[P2]`, en t=2 `[P2, P3]`; en t=5 P2 en CPU y cola `[P3]`. | OK |
| 3 | `test_eventos_en_t5` | Ficha técnica FCFS | En t=5: "P1 termina" y "Cambio de contexto: P1 -> P2". | OK |
| 4 | `test_estados_y_restante` | Ficha técnica FCFS | En t=6: P1 Terminado, P2 En ejecución (faltan 2), P3 Listo. | OK |
| 5 | `test_instante_final` | Ficha técnica FCFS | Último instante: CPU libre, todos terminados, cambios de contexto iguales al motor. | OK |
| 6 | `test_round_robin_llegadas_antes_que_el_expropiado` | RR q=2: P1 0/5, P2 1/3, P3 2/1 | En t=2 la cola es `[P3, P1]`: P3 llegó antes de que P1 vuelva. | OK |
| 7 | `test_round_robin_quantum_agotado_con_cola_vacia` | RR q=2, un proceso de ráfaga 5 | Evento "Quantum agotado" en t=2 y t=4, no en t=3. | OK |
| 8 | `test_sjf_ordena_por_rafaga` | SJF: P1 0/6, P2 1/4, P3 2/2 | Cola en t=2 `[P3, P2]`; P3 entra en t=6. | OK |
| 9 | `test_prioridad_ordena_por_numero_menor` | Prioridad: P2 (3) y P3 (1) llegan en t=1 | Cola `[P3, P2]`. | OK |
| 10 | `test_srtf_registra_la_expropiacion` | SRTF: P1 0/8, P2 1/4 | En t=1 P2 expropia a P1 ("le faltan 7") y P1 vuelve a la cola. | OK |
| 11 | `test_cpu_ociosa_y_proceso_nuevo` | FCFS: P1 0/2, P2 5/1 | Ocio de t=2 a t=5, P2 en estado Nuevo, 1 cambio de contexto. | OK |
| 12 | `test_todos_llegan_al_mismo_tiempo` | FCFS: A, B y C llegan en t=0 | Desempate por orden de registro: A en CPU, cola `[B, C]`. | OK |
| 13 | `test_quantum_mayor_que_todas_las_rafagas_equivale_a_fcfs` | RR q=50 contra FCFS | La CPU y la cola son idénticas en cada instante. | OK |
| 14 | `test_escenarios_aleatorios` | 60 escenarios aleatorios (semilla 2026) × 7 configuraciones = 420 simulaciones | En cada instante: la CPU coincide con el Gantt del motor, la cola tiene exactamente los procesos Listos, el proceso en CPU no está en la cola, el despachado no tiene peor clave que el primero de la cola y el total de cambios de contexto coincide con el motor. | OK |

La prueba 14 es la más fuerte: compara el componente nuevo contra el motor validado en la Fase I con datos que nadie escogió a mano.

## 3. Pruebas manuales de la interfaz

| # | Acción | Resultado esperado | Resultado obtenido |
|---|---|---|---|
| M1 | Cargar `ejemplo_cinco_procesos.csv`, Round Robin q=3, **Paso a paso** | Se abre la pestaña Paso a paso en t=0 con P1 en CPU. | OK |
| M2 | Pulsar **Siguiente >** hasta t=7 | CPU: P3 (faltan 8); cola `P4, P1, P2`; 2 cambios de contexto. Coincide con el ejercicio resuelto a mano. | OK ([captura](../../recursos/imagenes/06_paso_a_paso_round_robin.png)) |
| M3 | SJF + **Modo expropiativo**, **Paso a paso**, ir a t=1 | Bitácora: "P1 es expropiado (le faltan 7) y entra P2". | OK ([captura](../../recursos/imagenes/07_paso_a_paso_srtf_expropiacion.png)) |
| M4 | **Reproducir** | Avanza solo hasta el final y el botón vuelve a "Reproducir". | OK ([animación](../../recursos/imagenes/08_paso_a_paso.gif)) |
| M5 | Flechas izquierda/derecha con la pestaña activa | Retrocede o avanza un instante; no interfiere al escribir en los campos. | OK |
| M6 | Editar la tabla de procesos después de preparar la traza | La pestaña sigue funcionando con los procesos simulados. | OK |
| M7 | **Simular** y **Comparar** | Las pestañas de la Fase I siguen funcionando y el historial guarda cada simulación. | OK |

### Verificación a mano de M2 (Round Robin, q = 3)

| Tramo | CPU | Cola de listos al terminar el tramo |
|---|---|---|
| 0–3 | P1 | Llegan P2, P3 y P4; P1 vuelve al final: `P2, P3, P4, P1` |
| 3–6 | P2 | P2 vuelve al final: `P3, P4, P1, P2` |
| 6–9 | P3 | En t=7 (dentro del tramo) la cola es `P4, P1, P2` |
