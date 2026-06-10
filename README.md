# ADRIANA AI 

Aplicación de escritorio para Windows que transcribe y traduce audio en inglés 
al español en tiempo real, con un sistema de respuestas sugeridas basado en 
un glosario personalizable.

---

## ¿Qué hace?

- Captura el audio del sistema en tiempo real
- Transcribe automáticamente de inglés a español cada 6 segundos
- Detecta preguntas y muestra respuestas sugeridas en una ventana flotante
- Permite cargar preguntas y respuestas personalizadas desde archivos JSON
- Glosario editable organizado por semanas sin tocar código

---

## Características principales

**Transcripción en tiempo real**
Usa Faster-Whisper para procesar el audio cada 6 segundos mientras escuchas,
sin necesidad de esperar al final.

**Sistema de glosario con semanas**
Organiza tus preguntas y respuestas por semanas. Activa o desactiva semanas
según lo que necesites en cada momento. Las preguntas generales siempre
están disponibles.

**Importar JSON**
Genera tus preguntas con cualquier IA (ChatGPT, Gemini) y cárgalas 
directamente al programa desde un archivo JSON.

**Ventana flotante configurable**
Aparece automáticamente al detectar una pregunta. Puedes ajustar su tamaño,
posición y transparencia desde la configuración.

**100% local**
No requiere internet durante el uso. Sin APIs de pago. Todo corre en tu PC.

---

## Requisitos

- Windows 10/11
- Python 3.11
- FFmpeg instalado en `C:\ffmpeg`

---

## Instalación

1. Clona el repositorio:
   ```
   git clone https://github.com/ANTDOR9/PROYECTO-ADRIANA-AI.git
   cd PROYECTO-ADRIANA-AI
   ```

2. Ejecuta el instalador:
   ```
   instalar.bat
   ```

3. Abre el programa:
   ```
   iniciar.bat
   ```

---

## Formato del JSON

Para importar preguntas al glosario el archivo debe seguir este formato:

```json
[
  {
    "pregunta_en_ingles": "How are you?",
    "respuestas_ingles": [
      "I'm fine, thank you.",
      "I'm great, thanks!",
      "I'm okay, and you?"
    ],
    "traducciones_espanol": [
      "Estoy bien, gracias.",
      "Estoy genial, gracias!",
      "Estoy bien, y tú?"
    ]
  }
]
```

---

## Tecnologías

| Librería | Uso |
|---|---|
| Faster-Whisper | Transcripción de audio |
| Argos Translate | Traducción EN → ES |
| PyAudioWPatch | Captura de audio WASAPI |
| scikit-learn | Búsqueda por similitud |
| tkinter | Interfaz gráfica |
| pystray | Icono en bandeja del sistema |

---

## Estructura

```
PROYECTO-ADRIANA-AI/
├── adriana_ui.py        # Programa principal
├── configuracion.py     # Módulo de configuración
├── glosario.json        # Glosario guardado automáticamente
├── config.json          # Configuración de la ventana flotante
├── descargar_modelo.py  # Descarga modelo de traducción
├── instalar.bat         # Instalador automático
├── iniciar.bat          # Lanzador
└── README.md
```
