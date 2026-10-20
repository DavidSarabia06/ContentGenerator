@echo off
title ContentGenerator API

cd /d "%~dp0ContentGeneratorAPI"

echo ========================================
echo   ContentGenerator API
echo ========================================
echo.

REM Comprobar que existe el entorno virtual
if not exist ".venv\Scripts\python.exe" (
    echo [ERROR] No existe el entorno virtual .venv
    echo Creando entorno virtual...
    py -3.12 -m venv .venv

    if errorlevel 1 (
        echo [ERROR] No se pudo crear el entorno virtual. Comprueba que Python 3.12 esta instalado.
        pause
        exit /b 1
    )
)

echo [1/2] Instalando dependencias...
".venv\Scripts\python.exe" -m pip install -r requirements.txt

if errorlevel 1 (
    echo.
    echo [ERROR] Ha fallado la instalacion de requirements.txt
    pause
    exit /b 1
)

echo.
echo [2/2] Iniciando API...
echo.

".venv\Scripts\python.exe" -m uvicorn app.main:app --reload

pause