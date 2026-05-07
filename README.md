markdown# 🎙️ PROYECTO-ADRIANA-AI



Asistente de inglés en tiempo real para clases virtuales por Zoom.

100% local, sin APIs de pago, sin internet requerido durante el uso.



---



\## ¿Qué hace?



\- 🔴 Graba el audio del sistema (lo que sale por los parlantes)

\- ⚡ Transcribe en tiempo real cada 6 segundos con Faster-Whisper

\- 🌐 Traduce automáticamente de inglés a español

\- 🔍 Detecta preguntas del profesor y muestra respuestas sugeridas

\- 📚 Glosario editable con pestañas por semana

\- 🖥️ Ventana flotante siempre encima de Zoom



---



\## Requisitos



\- Windows 10/11

\- Python 3.11

\- FFmpeg instalado en `C:\\ffmpeg`



---



\## Instalación



1\. Clona el repositorio:

git clone https://github.com/ANTDOR9/PROYECTO-ADRIANA-AI.git

cd PROYECTO-ADRIANA-AI



2\. Crea el entorno virtual:

py -3.11 -m venv venv

venv\\Scripts\\activate



3\. Instala las dependencias:

pip install openai-whisper faster-whisper pyaudiowpatch soundfile numpy argostranslate keyboard pystray pillow scikit-learn



4\. Descarga el modelo de traducción:

python descargar\_modelo.py



5\. Ejecuta:

iniciar.bat



---



\## Uso



\- Doble clic en `iniciar.bat` para abrir el programa

\- Presiona \*\*GRABAR\*\* o `Ctrl+Space` para iniciar la grabación

\- Presiona \*\*DETENER\*\* para procesar y ver resultados

\- Usa \*\*📚 Editor de Glosario\*\* para agregar preguntas de tu guía mensual



---



\## Tecnologías



| Librería | Uso |

|---|---|

| Faster-Whisper | Transcripción de audio |

| Argos Translate | Traducción EN → ES |

| PyAudioWPatch | Captura de audio WASAPI |

| scikit-learn | Búsqueda por similitud |

| tkinter | Interfaz gráfica |

| pystray | Icono en bandeja del sistema |



---



\## Estructura

PROYECT-Adriana-AI/

├── adriana\_ui.py        # Programa principal

├── glosario.json        # Glosario guardado automáticamente

├── descargar\_modelo.py  # Descarga modelo de traducción

├── iniciar.bat          # Lanzador con doble clic

└── README.md

