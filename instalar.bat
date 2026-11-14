@echo off
title Instalando Adriana AI...
cd /d "%~dp0"
echo.
echo ============================================
echo    INSTALADOR - ADRIANA AI
echo ============================================
echo.
echo [1/5] Creando entorno virtual Python 3.11...
py -3.11 -m venv venv
echo.
echo [2/5] Instalando librerias...
call venv\Scripts\activate
pip install -r requirements.txt
echo.
echo [3/5] Descargando modelo de traduccion...
python descargar_modelo.py
echo.
echo [4/5] Aceleracion con grafica NVIDIA (opcional, ~1 GB)
set /p GPU="Tienes una grafica NVIDIA y quieres usarla? (s/n): "
if /i "%GPU%"=="s" pip install -r requirements-gpu.txt
echo.
echo [5/5] Instalacion completa!
echo.
echo IMPORTANTE: Asegurate de tener FFmpeg en C:\ffmpeg
echo Luego ejecuta iniciar.bat para abrir el programa.
echo.
pause
