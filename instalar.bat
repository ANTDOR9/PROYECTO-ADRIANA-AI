@echo off
title Instalando Adriana AI...
cd /d "%~dp0"
echo.
echo ============================================
echo    INSTALADOR - ADRIANA AI
echo ============================================
echo.
echo [1/4] Creando entorno virtual Python 3.11...
py -3.11 -m venv venv
echo.
echo [2/4] Instalando librerias...
call venv\Scripts\activate
pip install faster-whisper pyaudiowpatch soundfile numpy argostranslate keyboard pystray pillow scikit-learn
echo.
echo [3/4] Descargando modelo de traduccion...
python descargar_modelo.py
echo.
echo [4/4] Instalacion completa!
echo.
echo IMPORTANTE: Asegurate de tener FFmpeg en C:\ffmpeg
echo Luego ejecuta iniciar.bat para abrir el programa.
echo.
pause