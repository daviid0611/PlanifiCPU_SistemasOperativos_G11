@echo off
REM Genera dist\PlanifiCPU.exe en Windows 10/11.
REM Ejecutar con doble clic o desde la raiz del repositorio:  empaquetado\empaquetar_windows.bat
setlocal
cd /d "%~dp0.."

where python >nul 2>nul
if errorlevel 1 (
    echo No se encontro Python. Instale Python 3.12 o superior desde python.org
    echo y marque "Add python.exe to PATH" y "tcl/tk and IDLE".
    pause
    exit /b 1
)

echo [1/4] Creando el entorno virtual .venv-empaquetado ...
python -m venv .venv-empaquetado || goto :error
call .venv-empaquetado\Scripts\activate.bat

echo [2/4] Instalando dependencias y PyInstaller ...
python -m pip install --upgrade pip >nul
python -m pip install -r requirements.txt pyinstaller || goto :error

echo [3/4] Corriendo las pruebas automaticas ...
python -m unittest discover -s pruebas || goto :error

echo [4/4] Construyendo el ejecutable ...
pyinstaller --noconfirm --clean empaquetado\PlanifiCPU.spec || goto :error

echo Verificando el ejecutable ...
dist\PlanifiCPU.exe --diagnostico
if errorlevel 1 goto :error

echo.
echo Listo: dist\PlanifiCPU.exe
echo La base de datos del ejecutable queda en %%APPDATA%%\PlanifiCPU\planificpu.db
call deactivate
pause
exit /b 0

:error
echo.
echo Ocurrio un error. Revise los mensajes anteriores.
pause
exit /b 1
