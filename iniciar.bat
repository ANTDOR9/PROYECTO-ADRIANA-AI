@echo off
title Adriana AI
cd /d "%~dp0"
if not exist venv\Scripts\activate.bat (
  echo No existe el entorno virtual. Ejecutando instalar.bat...
  call instalar.bat
)
call venv\Scripts\activate
python adriana_ui.py
if errorlevel 1 pause
