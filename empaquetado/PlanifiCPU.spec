# -*- mode: python ; coding: utf-8 -*-
# Empaquetado de PlanifiCPU como un solo ejecutable con PyInstaller.
#
# Uso, desde la raiz del repositorio:
#     python -m pip install -r requirements.txt pyinstaller
#     pyinstaller --noconfirm --clean empaquetado/PlanifiCPU.spec
#
# Resultado: dist/PlanifiCPU.exe en Windows (dist/PlanifiCPU en Linux).
# El ejecutable incluye Python, Tkinter, Matplotlib, el esquema de la BD y el icono;
# la base de datos se guarda en %APPDATA%\PlanifiCPU\planificpu.db (ver planificpu/bd.py).

import os

RAIZ = os.path.abspath(os.path.join(SPECPATH, ".."))
SRC = os.path.join(RAIZ, "src", "codigo_fuente")

a = Analysis(
    [os.path.join(SRC, "main.py")],
    pathex=[SRC],
    datas=[
        (os.path.join(SRC, "bd", "schema.sql"), "bd"),
        (os.path.join(SRC, "planificpu", "icono.png"), "planificpu"),
    ],
    hiddenimports=["matplotlib.backends.backend_tkagg"],
    excludes=["PyQt5", "PyQt6", "PySide2", "PySide6", "IPython", "pandas", "scipy",
              "pytest", "notebook"],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="PlanifiCPU",
    icon=os.path.join(SPECPATH, "planificpu.ico"),
    console=False,          # aplicacion de ventana: no abre la consola negra
    upx=False,
    strip=False,
    debug=False,
)
