import threading
import tempfile
import os
import time
import numpy as np
import pyaudiowpatch as pyaudio
import whisper
import soundfile as sf
import keyboard
import tkinter as tk
from tkinter import font
import argostranslate.translate

# ══════════════════════════════════════════
#  CONFIGURACIÓN
# ══════════════════════════════════════════
DURACION_GRABACION = 25  # segundos
MODELO_WHISPER = "base"  # o "small" si quieres más precisión

PALABRAS_PREGUNTA = [
    "what", "how", "do you", "can you", "why",
    "where", "when", "who", "which", "is it",
    "are you", "could you", "would you", "did you"
]

RESPUESTAS_SUGERIDAS = {
    "what":     [("I think it means...", "Creo que significa..."),
                 ("Can you repeat that?", "¿Puedes repetirlo?"),
                 ("I don't understand.", "No entiendo.")],
    "how":      [("I'm not sure how.", "No estoy seguro de cómo."),
                 ("Can you show me?", "¿Puedes mostrarme?"),
                 ("Step by step, please.", "Paso a paso, por favor.")],
    "do you":   [("Yes, I do.", "Sí, lo hago."),
                 ("No, I don't.", "No, no lo hago."),
                 ("Sometimes.", "A veces.")],
    "can you":  [("Yes, I can.", "Sí, puedo."),
                 ("No, I can't.", "No, no puedo."),
                 ("I'll try.", "Lo intentaré.")],
    "why":      [("Because...", "Porque..."),
                 ("I'm not sure why.", "No estoy seguro por qué."),
                 ("Good question!", "¡Buena pregunta!")],
    "default":  [("I understand.", "Entiendo."),
                 ("Can you repeat?", "¿Puedes repetir?"),
                 ("Yes, of course.", "Sí, por supuesto.")],
}

# ══════════════════════════════════════════
#  CARGAR MODELOS (una sola vez al inicio)
# ══════════════════════════════════════════
print("⏳ Cargando Whisper (puede tardar 30s la primera vez)...")
modelo_whisper = whisper.load_model(MODELO_WHISPER)
print("✅ Whisper listo")

print("⏳ Cargando traductor...")
traductor = argostranslate.translate.get_translation_from_codes("en", "es")
print("✅ Traductor listo")
print()
print("🎯 Asistente listo — presiona Ctrl+Space para activar")

# ══════════════════════════════════════════
#  GRABACIÓN DE AUDIO
# ══════════════════════════════════════════
def grabar_audio(duracion=DURACION_GRABACION):
    p = pyaudio.PyAudio()
    wasapi_info = p.get_host_api_info_by_type(pyaudio.paWASAPI)
    default_speakers = p.get_device_info_by_index(wasapi_info["defaultOutputDevice"])

    if not default_speakers.get("isLoopbackDevice", False):
        for loopback in p.get_loopback_device_info_generator():
            if default_speakers["name"] in loopback["name"]:
                default_speakers = loopback
                break

    sample_rate = int(default_speakers["defaultSampleRate"])
    channels = int(default_speakers["maxInputChannels"])
    chunk = 1024

    stream = p.open(
        format=pyaudio.paFloat32,
        channels=channels,
        rate=sample_rate,
        input=True,
        input_device_index=default_speakers["index"],
        frames_per_buffer=chunk
    )

    frames = []
    for _ in range(int(sample_rate / chunk * duracion)):
        data = stream.read(chunk, exception_on_overflow=False)
        frames.append(np.frombuffer(data, dtype=np.float32))

    stream.stop_stream()
    stream.close()
    p.terminate()

    audio = np.concatenate(frames)
    if channels > 1:
        audio = audio.reshape(-1, channels).mean(axis=1)

    tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    sf.write(tmp.name, audio, sample_rate)
    return tmp.name

# ══════════════════════════════════════════
#  DETECCIÓN DE PREGUNTA
# ══════════════════════════════════════════
def es_pregunta(texto):
    texto_lower = texto.lower().strip()
    if texto_lower.endswith("?"):
        return True
    return any(p in texto_lower for p in PALABRAS_PREGUNTA)

def obtener_sugerencias(texto):
    texto_lower = texto.lower()
    for clave in PALABRAS_PREGUNTA:
        if clave in texto_lower and clave in RESPUESTAS_SUGERIDAS:
            return RESPUESTAS_SUGERIDAS[clave]
    return RESPUESTAS_SUGERIDAS["default"]

# ══════════════════════════════════════════
#  VENTANA FLOTANTE
# ══════════════════════════════════════════
def mostrar_ventana(texto_en, texto_es, sugerencias=None):
    ventana = tk.Tk()
    ventana.title("Asistente Inglés")
    ventana.attributes("-topmost", True)
    ventana.attributes("-alpha", 0.93)
    ventana.configure(bg="#1e1e2e")
    ventana.resizable(False, False)

    # Posición: esquina inferior derecha
    ancho, alto = 480, 320 if sugerencias else 200
    x = ventana.winfo_screenwidth() - ancho - 20
    y = ventana.winfo_screenheight() - alto - 60
    ventana.geometry(f"{ancho}x{alto}+{x}+{y}")

    fuente_titulo = font.Font(family="Segoe UI", size=9, weight="bold")
    fuente_texto  = font.Font(family="Segoe UI", size=10)
    fuente_suger  = font.Font(family="Segoe UI", size=9)

    # Header
    tk.Label(ventana, text="🎧 LO QUE DIJO (EN)",
             bg="#313244", fg="#cdd6f4",
             font=fuente_titulo, anchor="w",
             padx=8, pady=4).pack(fill="x")

    tk.Label(ventana, text=texto_en,
             bg="#1e1e2e", fg="#a6e3a1",
             font=fuente_texto, wraplength=460,
             justify="left", anchor="w",
             padx=10, pady=6).pack(fill="x")

    tk.Label(ventana, text="🌐 TRADUCCIÓN (ES)",
             bg="#313244", fg="#cdd6f4",
             font=fuente_titulo, anchor="w",
             padx=8, pady=4).pack(fill="x")

    tk.Label(ventana, text=texto_es,
             bg="#1e1e2e", fg="#89dceb",
             font=fuente_texto, wraplength=460,
             justify="left", anchor="w",
             padx=10, pady=6).pack(fill="x")

    if sugerencias:
        tk.Label(ventana, text="💬 RESPUESTAS SUGERIDAS",
                 bg="#313244", fg="#cdd6f4",
                 font=fuente_titulo, anchor="w",
                 padx=8, pady=4).pack(fill="x")

        for en, es in sugerencias:
            tk.Label(ventana,
                     text=f"• {en}  →  {es}",
                     bg="#1e1e2e", fg="#f38ba8",
                     font=fuente_suger, wraplength=460,
                     justify="left", anchor="w",
                     padx=14, pady=2).pack(fill="x")

    # Botón cerrar
    tk.Button(ventana, text="✕ Cerrar",
              command=ventana.destroy,
              bg="#45475a", fg="#cdd6f4",
              relief="flat", padx=10, pady=4,
              cursor="hand2").pack(pady=8)

    ventana.mainloop()

# ══════════════════════════════════════════
#  PROCESO PRINCIPAL
# ══════════════════════════════════════════
def procesar():
    # Ventana de "grabando..."
    def mostrar_grabando():
        global ventana_grabando
        ventana_grabando = tk.Tk()
        ventana_grabando.title("")
        ventana_grabando.attributes("-topmost", True)
        ventana_grabando.attributes("-alpha", 0.90)
        ventana_grabando.configure(bg="#1e1e2e")
        ventana_grabando.geometry("280x60+{}+{}".format(
            ventana_grabando.winfo_screenwidth() - 300,
            ventana_grabando.winfo_screenheight() - 120
        ))
        ventana_grabando.overrideredirect(True)
        tk.Label(ventana_grabando,
                 text=f"🔴 Grabando {DURACION_GRABACION}s...",
                 bg="#1e1e2e", fg="#f38ba8",
                 font=font.Font(family="Segoe UI", size=12, weight="bold"),
                 pady=15).pack()
        ventana_grabando.mainloop()

    hilo_grab = threading.Thread(target=mostrar_grabando, daemon=True)
    hilo_grab.start()
    time.sleep(0.3)

    try:
        print("🔴 Grabando...")
        archivo = grabar_audio()

        try:
            ventana_grabando.destroy()
        except:
            pass

        print("🧠 Transcribiendo con Whisper...")
        resultado = modelo_whisper.transcribe(archivo, language="en")
        texto_en = resultado["text"].strip()
        os.unlink(archivo)

        if not texto_en:
            print("⚠️ No se detectó audio")
            return

        print(f"📝 EN: {texto_en}")

        print("🌐 Traduciendo...")
        texto_es = traductor.translate(texto_en)
        print(f"📝 ES: {texto_es}")

        sugerencias = None
        if es_pregunta(texto_en):
            sugerencias = obtener_sugerencias(texto_en)
            print("❓ Pregunta detectada — mostrando sugerencias")

        mostrar_ventana(texto_en, texto_es, sugerencias)

    except Exception as e:
        print(f"❌ Error: {e}")

# ══════════════════════════════════════════
#  ATAJO DE TECLADO
# ══════════════════════════════════════════
def al_presionar():
    hilo = threading.Thread(target=procesar, daemon=True)
    hilo.start()

keyboard.add_hotkey("ctrl+space", al_presionar, trigger_on_release=True)

print("⌨️  Presiona Ctrl+Space para grabar | Ctrl+C para salir")
keyboard.wait()
