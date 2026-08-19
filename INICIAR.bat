@echo off
title Deposito de Herramientas
cd /d "%~dp0"

where python >nul 2>nul
if errorlevel 1 (
    echo.
    echo  ERROR: No esta instalado Python.
    echo  Descargalo de https://python.org/downloads
    echo  IMPORTANTE: tildar "Add Python to PATH" al instalar.
    echo.
    pause
    exit /b
)

if not exist "venv\" (
    echo  Primera vez: instalando... esto tarda 1-2 minutos.
    python -m venv venv
    call venv\Scripts\activate.bat
    python -m pip install --quiet --upgrade pip
    pip install --quiet -r requirements.txt
    echo  Listo.
) else (
    call venv\Scripts\activate.bat
)

python app.py
pause
