@echo off

title Simulador de Pseudocodigo - Crear EXE

REM  ==============================================
REM  Codigo para hacer un archivo EXE
REM ==============================================

cd /d "%~dp0"

echo.
echo ==============================================
echo     SIMULADOR DE PSEUDOCODIGO
echo         GENERADOR DE EXE
echo ==============================================
echo.

echo Carpeta del proyecto:
echo %cd%
echo.

REM 
REM 
REM 

echo [1/4] Verificando archivos...
echo.

if not exist "app.py" (
    echo.
    echo ==============================================
    echo ERROR: NO SE ENCONTRO app.py
    echo ==============================================
    echo.
    echo Este archivo debe estar en:
    echo.
    echo %cd%
    echo.
    echo Asegurate de que app.py este en esta misma
    echo carpeta que crear_exe.bat.
    echo.
    pause
    exit /b 1
)

echo OK: app.py encontrado.
echo.

REM 
REM 
REM 

if not exist "requirements.txt" (
    echo.
    echo ==============================================
    echo ERROR: NO SE ENCONTRO requirements.txt
    echo ==============================================
    echo.
    echo Debes crear requirements.txt en:
    echo.
    echo %cd%
    echo.
    pause
    exit /b 1
)

echo OK: requirements.txt encontrado.
echo.

REM 
REM 
REM 

echo [2/4] Instalando dependencias...
echo.

python -m pip install -r requirements.txt

if errorlevel 1 (
    echo.
    echo ==============================================
    echo ERROR AL INSTALAR DEPENDENCIAS
    echo ==============================================
    echo.
    pause
    exit /b 1
)

echo.
echo Dependencias instaladas correctamente.
echo.

REM 
REM 
REM 

echo [3/4] Limpiando compilaciones anteriores...
echo.

if exist "build" (
    rmdir /s /q "build"
)

if exist "dist" (
    rmdir /s /q "dist"
)

if exist "SimuladorPseudocodigo.spec" (
    del /q "SimuladorPseudocodigo.spec"
)

echo Limpieza terminada.
echo.

REM 
REM 
REM 

echo [4/4] Creando EXE...
echo.

python -m PyInstaller ^
    --onefile ^
    --console ^
    --name "SimuladorPseudocodigo" ^
    app.py

if errorlevel 1 (
    echo.
    echo ==============================================
    echo ERROR AL CREAR EL EXE
    echo ==============================================
    echo.
    echo Revisa los mensajes anteriores.
    echo.
    pause
    exit /b 1
)

REM 
REM 
REM 

echo.
echo ==============================================
echo       EXE CREADO CORRECTAMENTE
echo ==============================================
echo.
echo El archivo se encuentra en:
echo.
echo %cd%\dist\SimuladorPseudocodigo.exe
echo.
echo ==============================================
echo.

pause