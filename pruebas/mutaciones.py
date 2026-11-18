"""Pruebas de mutacion: comprueban que las pruebas automaticas detectan errores reales.

Se copia el proyecto a una carpeta temporal, se introduce a proposito un error
pequeno en el codigo (una "mutacion") y se corren las pruebas. Si alguna prueba
falla, la mutacion queda DETECTADA; si todas pasan, las pruebas tienen un hueco.

Ejecutar desde la raiz del repositorio (tarda unos segundos por mutacion):
    python pruebas/mutaciones.py
"""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent

# (archivo dentro de planificpu/, texto original, texto con el error, descripcion)
MUTACIONES = [
    ("algoritmos.py",
     "i = min(listos, key=lambda j: (clave(procesos[j], restante[j]), j != actual,",
     "i = min(listos, key=lambda j: (clave(procesos[j], restante[j]), j == actual,",
     "En modo expropiativo, ante un empate se cambia de proceso en vez de mantenerlo"),
    ("algoritmos.py",
     "                                       procesos[j].llegada, j))\n        listos.remove(i)",
     "                                       -j, j))\n        listos.remove(i)",
     "En modo no expropiativo, el empate no se resuelve por orden de llegada"),
    ("algoritmos.py",
     "        restante[i] -= uso\n        encolar_llegadas(t)\n        if restante[i] > 0:\n"
     "            cola.append(i)",
     "        restante[i] -= uso\n        if restante[i] > 0:\n            cola.append(i)\n"
     "        encolar_llegadas(t)",
     "Round Robin: el expropiado entra a la cola antes que los que llegaron"),
    ("algoritmos.py", "uso = min(quantum, restante[i])", "uso = min(quantum + 1, restante[i])",
     "Round Robin: el quantum dura una unidad de mas"),
    ("algoritmos.py", '"Prioridad": lambda p, restante: p.prioridad,',
     '"Prioridad": lambda p, restante: -p.prioridad,',
     "Prioridad invertida (numero mayor = mayor prioridad)"),
    ("metricas.py", "inicio.setdefault(seg.pid, seg.inicio)", "inicio[seg.pid] = seg.inicio",
     "Respuesta calculada con el ultimo tramo y no con el primero"),
    ("modelos.py", "return sum(s.duracion for s in self.gantt if s.pid is not None)",
     "return sum(s.duracion for s in self.gantt)",
     "La CPU ociosa se cuenta como tiempo ocupado"),
    ("modelos.py", "            if anterior is not None and seg.pid != anterior:",
     "            if seg.pid != anterior:",
     "El primer despacho se cuenta como cambio de contexto"),
    ("paso_a_paso.py", "                cola.append(actual)         # el expropiado va al final",
     "                cola.appendleft(actual)",
     "Paso a paso: el expropiado vuelve al frente de la cola de Round Robin"),
    ("modelos.py", "            if valor < minimo:", "            if valor < minimo - 1:",
     "La validacion acepta rafaga 0 y valores negativos"),
]


def correr_pruebas(carpeta: Path) -> list[str]:
    salida = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "pruebas"],
                            cwd=carpeta, capture_output=True, text=True).stderr
    return sorted({re.sub(r" \(.*", "", linea.split(": ", 1)[1])
                   for linea in salida.splitlines() if linea.startswith(("FAIL:", "ERROR:"))})


def main() -> int:
    detectadas = 0
    ignorar = shutil.ignore_patterns(".git", ".venv*", "venv", "build", "dist", "__pycache__",
                                     "*.db")
    for n, (archivo, original, mutado, descripcion) in enumerate(MUTACIONES, start=1):
        with tempfile.TemporaryDirectory() as d:
            copia = Path(d) / "proyecto"
            shutil.copytree(RAIZ, copia, ignore=ignorar)
            ruta = copia / "src" / "codigo_fuente" / "planificpu" / archivo
            texto = ruta.read_text(encoding="utf-8")
            if texto.count(original) != 1:
                print(f"M{n:02d} NO APLICA   {descripcion} (el codigo cambio)")
                continue
            ruta.write_text(texto.replace(original, mutado), encoding="utf-8")
            fallas = correr_pruebas(copia)
        detectadas += bool(fallas)
        estado = "DETECTADA  " if fallas else "NO DETECTADA"
        print(f"M{n:02d} {estado} {descripcion}")
        if fallas:
            print(f"     {len(fallas)} prueba(s) fallaron, p. ej.: {', '.join(fallas[:3])}")
    print(f"\nMutaciones detectadas: {detectadas} de {len(MUTACIONES)}")
    return 0 if detectadas == len(MUTACIONES) else 1


if __name__ == "__main__":
    sys.exit(main())
