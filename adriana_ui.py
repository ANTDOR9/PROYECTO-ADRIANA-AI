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
from tkinter import font, scrolledtext, filedialog, messagebox
import argostranslate.translate
from PIL import Image, ImageDraw
import pystray
import datetime

# Ruta directa a FFmpeg
os.environ["PATH"] = r"C:\ffmpeg\bin" + os.pathsep + os.environ.get("PATH", "")

# ══════════════════════════════════════════
#  CONFIGURACIÓN
# ══════════════════════════════════════════
MODELO_WHISPER = "base"

COLORES = {
    "fondo":        "#0d0d1a",
    "fondo2":       "#13132b",
    "panel":        "#1a1a35",
    "borde":        "#6c63ff",
    "borde2":       "#9d4edd",
    "neon":         "#7c3aed",
    "texto":        "#e0e0ff",
    "texto2":       "#a0a0cc",
    "verde":        "#00ff9d",
    "cyan":         "#00d4ff",
    "rosa":         "#ff6b9d",
    "amarillo":     "#ffd93d",
    "boton":        "#6c63ff",
    "boton_hover":  "#7c3aed",
    "grabando":     "#ff4444",
}

PALABRAS_PREGUNTA = [
    "what", "how", "do you", "can you", "why",
    "where", "when", "who", "which", "is it",
    "are you", "could you", "would you", "did you"
]

RESPUESTAS_SUGERIDAS = {
    "what":    [("I think it means...", "Creo que significa..."),
                ("Can you repeat that?", "¿Puedes repetirlo?"),
                ("I don't understand.", "No entiendo.")],
    "how":     [("I'm not sure how.", "No estoy seguro de cómo."),
                ("Can you show me?", "¿Puedes mostrarme?"),
                ("Step by step, please.", "Paso a paso, por favor.")],
    "do you":  [("Yes, I do.", "Sí, lo hago."),
                ("No, I don't.", "No, no lo hago."),
                ("Sometimes.", "A veces.")],
    "can you": [("Yes, I can.", "Sí, puedo."),
                ("No, I can't.", "No, no puedo."),
                ("I'll try.", "Lo intentaré.")],
    "why":     [("Because...", "Porque..."),
                ("I'm not sure why.", "No estoy seguro por qué."),
                ("Good question!", "¡Buena pregunta!")],
    "default": [("I understand.", "Entiendo."),
                ("Can you repeat?", "¿Puedes repetir?"),
                ("Yes, of course.", "Sí, por supuesto.")],
}

# ══════════════════════════════════════════
#  ESTADO GLOBAL
# ══════════════════════════════════════════
historial = []
grabando = False
ventana_principal = None
label_estado = None
historial_widget = None
tray_icon = None
boton_grabar = None
detener_grabacion = threading.Event()

# ══════════════════════════════════════════
#  CARGAR MODELOS
# ══════════════════════════════════════════
print("⏳ Cargando Whisper...")
modelo_whisper = whisper.load_model(MODELO_WHISPER)
print("✅ Whisper listo")

print("⏳ Cargando traductor...")
traductor = argostranslate.translate.get_translation_from_codes("en", "es")
print("✅ Traductor listo")

# ══════════════════════════════════════════
#  GRABACIÓN MANUAL
# ══════════════════════════════════════════
def grabar_audio_manual():
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
    detener_grabacion.clear()
    while not detener_grabacion.is_set():
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
#  DETECCIÓN DE PREGUNTAS
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
def mostrar_flotante(texto_en, texto_es, sugerencias=None):
    flotante = tk.Toplevel()
    flotante.title("")
    flotante.attributes("-topmost", True)
    flotante.attributes("-alpha", 0.96)
    flotante.overrideredirect(True)
    flotante.configure(bg=COLORES["fondo"])

    alto = 260 if sugerencias else 180
    ancho = 500
    sw = flotante.winfo_screenwidth()
    sh = flotante.winfo_screenheight()
    flotante.geometry(f"{ancho}x{alto}+{sw - ancho - 20}+{sh - alto - 70}")

    marco = tk.Frame(flotante, bg=COLORES["borde"], padx=2, pady=2)
    marco.pack(fill="both", expand=True)

    interior = tk.Frame(marco, bg=COLORES["fondo"])
    interior.pack(fill="both", expand=True)

    header = tk.Frame(interior, bg=COLORES["panel"], pady=6)
    header.pack(fill="x")

    tk.Label(header, text="◈ ADRIANA AI  —  Asistente de Inglés",
             bg=COLORES["panel"], fg=COLORES["borde"],
             font=("Consolas", 9, "bold")).pack(side="left", padx=10)

    tk.Button(header, text="✕", command=flotante.destroy,
              bg=COLORES["panel"], fg=COLORES["rosa"],
              relief="flat", font=("Consolas", 10, "bold"),
              cursor="hand2", bd=0).pack(side="right", padx=8)

    fila_en = tk.Frame(interior, bg=COLORES["fondo"], pady=4)
    fila_en.pack(fill="x", padx=10)
    tk.Label(fila_en, text="EN›", bg=COLORES["fondo"],
             fg=COLORES["borde"], font=("Consolas", 9, "bold")).pack(side="left")
    tk.Label(fila_en, text=texto_en, bg=COLORES["fondo"],
             fg=COLORES["verde"], font=("Consolas", 10),
             wraplength=420, justify="left").pack(side="left", padx=6)

    tk.Frame(interior, bg=COLORES["borde2"], height=1).pack(fill="x", padx=10)

    fila_es = tk.Frame(interior, bg=COLORES["fondo"], pady=4)
    fila_es.pack(fill="x", padx=10)
    tk.Label(fila_es, text="ES›", bg=COLORES["borde2"],
             fg=COLORES["borde2"], font=("Consolas", 9, "bold")).pack(side="left")
    tk.Label(fila_es, text=texto_es, bg=COLORES["fondo"],
             fg=COLORES["cyan"], font=("Consolas", 10),
             wraplength=420, justify="left").pack(side="left", padx=6)

    if sugerencias:
        tk.Frame(interior, bg=COLORES["neon"], height=1).pack(fill="x", padx=10, pady=4)
        tk.Label(interior, text="💬 Respuestas sugeridas:",
                 bg=COLORES["fondo"], fg=COLORES["amarillo"],
                 font=("Consolas", 8, "bold")).pack(anchor="w", padx=12)
        for en, es in sugerencias:
            tk.Label(interior, text=f"  › {en}  ·  {es}",
                     bg=COLORES["fondo"], fg=COLORES["rosa"],
                     font=("Consolas", 9),
                     wraplength=470, justify="left").pack(anchor="w", padx=12)

# flotante.after(30000, lambda: flotante.destroy() if flotante.winfo_exists() else None)

    def iniciar_arrastre(e):
        flotante._drag_x = e.x
        flotante._drag_y = e.y

    def arrastrar(e):
        x = flotante.winfo_x() + e.x - flotante._drag_x
        y = flotante.winfo_y() + e.y - flotante._drag_y
        flotante.geometry(f"+{x}+{y}")

    header.bind("<Button-1>", iniciar_arrastre)
    header.bind("<B1-Motion>", arrastrar)

# ══════════════════════════════════════════
#  ACTUALIZAR UI
# ══════════════════════════════════════════
def actualizar_estado(texto, color=None):
    if label_estado:
        label_estado.config(text=texto, fg=color or COLORES["texto2"])

def agregar_al_historial(texto_en, texto_es, hora):
    if historial_widget:
        historial_widget.config(state="normal")
        historial_widget.insert("end", f"\n[{hora}]\n", "hora")
        historial_widget.insert("end", f"EN › {texto_en}\n", "en")
        historial_widget.insert("end", f"ES › {texto_es}\n", "es")
        historial_widget.insert("end", "─" * 55 + "\n", "sep")
        historial_widget.see("end")
        historial_widget.config(state="disabled")

# ══════════════════════════════════════════
#  PROCESO PRINCIPAL
# ══════════════════════════════════════════
def procesar():
    global grabando, boton_grabar

    actualizar_estado("🔴  Grabando... presiona DETENER cuando quieras", COLORES["grabando"])

    try:
        archivo = grabar_audio_manual()
        actualizar_estado("🧠  Transcribiendo con Whisper...", COLORES["amarillo"])

        resultado = modelo_whisper.transcribe(archivo, language="en")
        texto_en = resultado["text"].strip()
        os.unlink(archivo)

        if not texto_en:
            actualizar_estado("⚠️  No se detectó audio claro.", COLORES["rosa"])
            grabando = False
            if boton_grabar:
                boton_grabar.config(text="⬤  GRABAR  (Ctrl+Space)", bg=COLORES["boton"])
            return

        actualizar_estado("🌐  Traduciendo...", COLORES["cyan"])
        texto_es = traductor.translate(texto_en)

        hora = datetime.datetime.now().strftime("%H:%M:%S")
        historial.append({"hora": hora, "en": texto_en, "es": texto_es})
        agregar_al_historial(texto_en, texto_es, hora)

        sugerencias = obtener_sugerencias(texto_en) if es_pregunta(texto_en) else None

        if ventana_principal:
            ventana_principal.after(0, lambda: mostrar_flotante(texto_en, texto_es, sugerencias))

        actualizar_estado("✅  Listo — presiona GRABAR para continuar", COLORES["verde"])

    except Exception as e:
        actualizar_estado(f"❌  Error: {e}", COLORES["rosa"])
        print(f"Error: {e}")

    grabando = False
    if boton_grabar:
        boton_grabar.config(text="⬤  GRABAR  (Ctrl+Space)", bg=COLORES["boton"])

# ══════════════════════════════════════════
#  TOGGLE GRABAR / DETENER
# ══════════════════════════════════════════
def iniciar_proceso():
    global grabando, boton_grabar
    if not grabando:
        grabando = True
        if boton_grabar:
            boton_grabar.config(text="⬛  DETENER", bg="#cc0000")
        hilo = threading.Thread(target=procesar, daemon=True)
        hilo.start()
    else:
        detener_grabacion.set()
        if boton_grabar:
            boton_grabar.config(text="⏳  Procesando...", bg=COLORES["neon"])

# ══════════════════════════════════════════
#  EXPORTAR / LIMPIAR
# ══════════════════════════════════════════
def exportar_historial():
    if not historial:
        messagebox.showinfo("Sin datos", "No hay transcripciones aún.")
        return
    ruta = filedialog.asksaveasfilename(
        defaultextension=".txt",
        filetypes=[("Texto", "*.txt")],
        title="Guardar historial"
    )
    if ruta:
        with open(ruta, "w", encoding="utf-8") as f:
            f.write("HISTORIAL — ADRIANA AI\n")
            f.write("=" * 50 + "\n\n")
            for item in historial:
                f.write(f"[{item['hora']}]\n")
                f.write(f"EN: {item['en']}\n")
                f.write(f"ES: {item['es']}\n")
                f.write("-" * 40 + "\n\n")
        messagebox.showinfo("✅ Guardado", f"Historial exportado en:\n{ruta}")

def limpiar_historial():
    historial.clear()
    if historial_widget:
        historial_widget.config(state="normal")
        historial_widget.delete("1.0", "end")
        historial_widget.config(state="disabled")
    actualizar_estado("🗑  Historial limpiado.", COLORES["texto2"])

# ══════════════════════════════════════════
#  SYSTEM TRAY
# ══════════════════════════════════════════
def crear_icono_tray():
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.ellipse([4, 4, 60, 60], fill="#6c63ff")
    d.ellipse([14, 14, 50, 50], fill="#0d0d1a")
    d.ellipse([24, 24, 40, 40], fill="#7c3aed")
    return img

def mostrar_ventana_desde_tray(icon, item):
    if ventana_principal:
        ventana_principal.deiconify()
        ventana_principal.lift()

def salir_desde_tray(icon, item):
    icon.stop()
    if ventana_principal:
        ventana_principal.destroy()

def iniciar_tray():
    global tray_icon
    menu = pystray.Menu(
        pystray.MenuItem("Mostrar ventana", mostrar_ventana_desde_tray),
        pystray.MenuItem("Salir", salir_desde_tray)
    )
    tray_icon = pystray.Icon("AdrianAI", crear_icono_tray(), "Adriana AI", menu)
    tray_icon.run()

# ══════════════════════════════════════════
#  VENTANA PRINCIPAL
# ══════════════════════════════════════════
def construir_ui():
    global ventana_principal, label_estado, historial_widget, boton_grabar

    ventana_principal = tk.Tk()
    ventana_principal.title("Adriana AI — Asistente de Inglés")
    ventana_principal.configure(bg=COLORES["fondo"])
    ventana_principal.geometry("620x700")
    ventana_principal.resizable(False, True)
    ventana_principal.minsize(620, 500)

    def minimizar_a_tray():
        ventana_principal.withdraw()

    ventana_principal.protocol("WM_DELETE_WINDOW", minimizar_a_tray)

    # ── HEADER ──────────────────────────────
    header = tk.Frame(ventana_principal, bg=COLORES["panel"], pady=14)
    header.pack(fill="x")

    tk.Label(header, text="◈ ADRIANA AI",
             bg=COLORES["panel"], fg=COLORES["borde"],
             font=("Consolas", 18, "bold")).pack(side="left", padx=20)

    tk.Label(header, text="Asistente para clases de inglés",
             bg=COLORES["panel"], fg=COLORES["texto2"],
             font=("Consolas", 9)).pack(side="left")

    tk.Button(header, text="—", command=minimizar_a_tray,
              bg=COLORES["panel"], fg=COLORES["texto2"],
              relief="flat", font=("Consolas", 12), cursor="hand2").pack(side="right", padx=6)

    # ── BOTÓN PRINCIPAL ──────────────────────
    zona_boton = tk.Frame(ventana_principal, bg=COLORES["fondo"], pady=20)
    zona_boton.pack(fill="x")

    boton_grabar = tk.Button(
        zona_boton,
        text="⬤  GRABAR  (Ctrl+Space)",
        command=iniciar_proceso,
        bg=COLORES["boton"],
        fg="white",
        font=("Consolas", 13, "bold"),
        relief="flat",
        padx=30, pady=14,
        cursor="hand2",
        activebackground=COLORES["boton_hover"],
        activeforeground="white"
    )
    boton_grabar.pack()

    def hover_on(e):  boton_grabar.config(bg=COLORES["boton_hover"])
    def hover_off(e): boton_grabar.config(bg=COLORES["boton"])
    boton_grabar.bind("<Enter>", hover_on)
    boton_grabar.bind("<Leave>", hover_off)

    # ── ESTADO ───────────────────────────────
    label_estado = tk.Label(
        ventana_principal,
        text="✅  Listo — presiona GRABAR o Ctrl+Space para comenzar",
        bg=COLORES["fondo"], fg=COLORES["texto2"],
        font=("Consolas", 9)
    )
    label_estado.pack(pady=4)

    # ── SEPARADOR ────────────────────────────
    tk.Frame(ventana_principal, bg=COLORES["borde"], height=1).pack(fill="x", padx=20, pady=8)

    # ── HISTORIAL ────────────────────────────
    zona_hist = tk.Frame(ventana_principal, bg=COLORES["fondo"])
    zona_hist.pack(fill="both", expand=True, padx=20)

    tk.Label(zona_hist, text="▸ HISTORIAL DE TRANSCRIPCIONES",
             bg=COLORES["fondo"], fg=COLORES["borde"],
             font=("Consolas", 9, "bold")).pack(anchor="w", pady=(0, 6))

    historial_widget = scrolledtext.ScrolledText(
        zona_hist,
        bg=COLORES["fondo2"],
        fg=COLORES["texto"],
        font=("Consolas", 9),
        relief="flat",
        bd=0,
        state="disabled",
        insertbackground=COLORES["borde"],
        selectbackground=COLORES["neon"],
        wrap="word"
    )
    historial_widget.pack(fill="both", expand=True)

    historial_widget.tag_config("hora", foreground=COLORES["texto2"])
    historial_widget.tag_config("en",   foreground=COLORES["verde"])
    historial_widget.tag_config("es",   foreground=COLORES["cyan"])
    historial_widget.tag_config("sep",  foreground=COLORES["panel"])

    # ── BOTONES INFERIORES ───────────────────
    zona_bots = tk.Frame(ventana_principal, bg=COLORES["fondo"], pady=12)
    zona_bots.pack(fill="x", padx=20)

    def boton(parent, texto, cmd, color):
        b = tk.Button(parent, text=texto, command=cmd,
                      bg=COLORES["panel"], fg=color,
                      font=("Consolas", 9), relief="flat",
                      padx=14, pady=6, cursor="hand2",
                      activebackground=COLORES["fondo2"])
        b.pack(side="left", padx=4)
        return b

    boton(zona_bots, "🗑  Limpiar historial", limpiar_historial, COLORES["rosa"])
    boton(zona_bots, "💾  Exportar .txt",     exportar_historial, COLORES["verde"])
    boton(zona_bots, "⊟  Minimizar a tray",   minimizar_a_tray,   COLORES["texto2"])

    # ── FOOTER ───────────────────────────────
    tk.Label(ventana_principal,
             text="Whisper · Argos Translate · WASAPI Loopback  —  100% local",
             bg=COLORES["fondo"], fg=COLORES["panel"],
             font=("Consolas", 7)).pack(pady=6)

    return ventana_principal

# ══════════════════════════════════════════
#  ATAJO DE TECLADO
# ══════════════════════════════════════════
keyboard.add_hotkey("ctrl+space", iniciar_proceso, trigger_on_release=True)

# ══════════════════════════════════════════
#  ARRANQUE
# ══════════════════════════════════════════
print("🎯 Iniciando interfaz...")

hilo_tray = threading.Thread(target=iniciar_tray, daemon=True)
hilo_tray.start()

ventana = construir_ui()
print("⌨️  Ctrl+Space para grabar | Minimizar para ir al system tray")
ventana.mainloop()
