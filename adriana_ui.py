import threading
import tempfile
import os
import json
import numpy as np
import pyaudiowpatch as pyaudio
import soundfile as sf
import keyboard
import tkinter as tk
from tkinter import scrolledtext, filedialog, messagebox
import argostranslate.translate
from PIL import Image, ImageDraw
import pystray
import datetime
from faster_whisper import WhisperModel
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Ruta directa a FFmpeg
os.environ["PATH"] = r"C:\ffmpeg\bin" + os.pathsep + os.environ.get("PATH", "")

# ══════════════════════════════════════════
#  CONFIGURACIÓN
# ══════════════════════════════════════════
MODELO_WHISPER     = "small"   # más preciso que base
CHUNK_SEGUNDOS     = 6         # procesa cada 6 segundos en tiempo real
SAMPLE_RATE        = 16000

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

# ══════════════════════════════════════════
#  GLOSARIO FIJO
# ══════════════════════════════════════════
GLOSARIO_FIJO = [
    {
        "pregunta_en_ingles": "How are you?",
        "respuestas_ingles": ["I'm fine, thank you.", "I'm great, thanks!", "I'm okay, and you?"],
        "traducciones_espanol": ["Estoy bien, gracias.", "Estoy genial, ¡gracias!", "Estoy bien, ¿y tú?"]
    },
    {
        "pregunta_en_ingles": "How are you today?",
        "respuestas_ingles": ["I'm doing well, thank you.", "I'm a little tired today.", "I'm very happy today!"],
        "traducciones_espanol": ["Estoy bien hoy, gracias.", "Estoy un poco cansado hoy.", "¡Estoy muy feliz hoy!"]
    },
    {
        "pregunta_en_ingles": "What did you do this weekend?",
        "respuestas_ingles": ["I stayed at home and rested.", "I went out with my family.", "I studied and watched TV."],
        "traducciones_espanol": ["Me quedé en casa y descansé.", "Salí con mi familia.", "Estudié y vi televisión."]
    },
    {
        "pregunta_en_ingles": "How was your weekend?",
        "respuestas_ingles": ["It was great, I relaxed a lot.", "It was okay, nothing special.", "It was busy but fun."],
        "traducciones_espanol": ["Estuvo genial, descansé mucho.", "Estuvo bien, nada especial.", "Estuvo ocupado pero divertido."]
    },
    {
        "pregunta_en_ingles": "How was your week?",
        "respuestas_ingles": ["It was good, thank you.", "It was a bit stressful.", "It was very productive."],
        "traducciones_espanol": ["Estuvo bien, gracias.", "Fue un poco estresante.", "Fue muy productiva."]
    },
    {
        "pregunta_en_ingles": "What did you do yesterday?",
        "respuestas_ingles": ["I worked and then cooked dinner.", "I visited my family.", "I stayed home and rested."],
        "traducciones_espanol": ["Trabajé y luego cociné la cena.", "Visité a mi familia.", "Me quedé en casa y descansé."]
    },
    {
        "pregunta_en_ingles": "Are you ready for class?",
        "respuestas_ingles": ["Yes, I'm ready!", "Almost, give me a second.", "Yes, let's start!"],
        "traducciones_espanol": ["¡Sí, estoy listo!", "Casi, dame un segundo.", "¡Sí, empecemos!"]
    },
    {
        "pregunta_en_ingles": "Can you hear me?",
        "respuestas_ingles": ["Yes, I can hear you clearly.", "Yes, loud and clear!", "No, there is an echo."],
        "traducciones_espanol": ["Sí, te escucho claramente.", "¡Sí, muy claro!", "No, hay un eco."]
    },
    {
        "pregunta_en_ingles": "Do you have any questions?",
        "respuestas_ingles": ["No, I understand.", "Yes, I have one question.", "Can you repeat that please?"],
        "traducciones_espanol": ["No, entiendo.", "Sí, tengo una pregunta.", "¿Puedes repetir eso por favor?"]
    },
    {
        "pregunta_en_ingles": "What is your name?",
        "respuestas_ingles": ["My name is Anthony.", "I'm Anthony, nice to meet you.", "Anthony, but you can call me Tony."],
        "traducciones_espanol": ["Mi nombre es Anthony.", "Soy Anthony, mucho gusto.", "Anthony, pero puedes llamarme Tony."]
    },
    {
        "pregunta_en_ingles": "Where are you from?",
        "respuestas_ingles": ["I'm from Peru.", "I'm from Arequipa, Peru.", "I'm Peruvian."],
        "traducciones_espanol": ["Soy de Perú.", "Soy de Arequipa, Perú.", "Soy peruano."]
    },
    {
        "pregunta_en_ingles": "How do you feel today?",
        "respuestas_ingles": ["I feel good, thank you.", "I feel a little nervous.", "I feel excited to learn!"],
        "traducciones_espanol": ["Me siento bien, gracias.", "Me siento un poco nervioso.", "¡Me siento emocionado de aprender!"]
    },
    {
        "pregunta_en_ingles": "What did you have for breakfast?",
        "respuestas_ingles": ["I had bread and coffee.", "I had eggs and juice.", "I didn't have breakfast today."],
        "traducciones_espanol": ["Comí pan y café.", "Comí huevos y jugo.", "No desayuné hoy."]
    },
    {
        "pregunta_en_ingles": "Can you introduce yourself?",
        "respuestas_ingles": ["Sure! My name is Anthony, I'm from Peru.", "Of course! I'm Anthony and I'm learning English.", "Yes! I'm Anthony, nice to meet everyone."],
        "traducciones_espanol": ["¡Claro! Me llamo Anthony, soy de Perú.", "¡Por supuesto! Soy Anthony y estoy aprendiendo inglés.", "¡Sí! Soy Anthony, mucho gusto a todos."]
    },
]

# ══════════════════════════════════════════
#  ESTADO GLOBAL
# ══════════════════════════════════════════
historial       = []
grabando        = False
ventana_principal = None
label_estado    = None
historial_widget = None
tray_icon       = None
boton_grabar    = None
label_guia      = None
detener_grabacion = threading.Event()
glosario_mes    = []
texto_acumulado = ""
ventana_flotante_actual = None

# ══════════════════════════════════════════
#  CARGAR MODELOS
# ══════════════════════════════════════════
print("⏳ Cargando Faster-Whisper (modelo small)...")
modelo_whisper = WhisperModel(MODELO_WHISPER, device="cpu", compute_type="int8")
print("✅ Faster-Whisper listo")

print("⏳ Cargando traductor...")
traductor = argostranslate.translate.get_translation_from_codes("en", "es")
print("✅ Traductor listo")

# ══════════════════════════════════════════
#  BÚSQUEDA POR SIMILITUD
# ══════════════════════════════════════════
def buscar_pregunta_similar(texto):
    glosario_completo = GLOSARIO_FIJO + glosario_mes
    if not glosario_completo or not texto.strip():
        return None
    preguntas = [item["pregunta_en_ingles"] for item in glosario_completo]
    corpus = preguntas + [texto]
    try:
        vectorizer = TfidfVectorizer().fit_transform(corpus)
        similitudes = cosine_similarity(vectorizer[-1], vectorizer[:-1]).flatten()
        idx = similitudes.argmax()
        score = similitudes[idx]
        if score < 0.15:
            return None
        return {
            "pregunta":     glosario_completo[idx]["pregunta_en_ingles"],
            "respuestas":   glosario_completo[idx]["respuestas_ingles"],
            "traducciones": glosario_completo[idx]["traducciones_espanol"],
            "score":        round(float(score), 2)
        }
    except Exception as e:
        print(f"Error similitud: {e}")
        return None

# ══════════════════════════════════════════
#  CARGAR JSON DEL MES
# ══════════════════════════════════════════
def cargar_guia():
    global glosario_mes, label_guia
    ruta = filedialog.askopenfilename(
        filetypes=[("JSON", "*.json")],
        title="Cargar guía del mes"
    )
    if not ruta:
        return
    try:
        with open(ruta, "r", encoding="utf-8") as f:
            datos = json.load(f)
        glosario_mes = datos
        nombre = os.path.basename(ruta)
        if label_guia:
            label_guia.config(
                text=f"📂 {nombre} — {len(datos)} preguntas cargadas",
                fg=COLORES["verde"]
            )
        print(f"✅ Guía cargada: {nombre} ({len(datos)} preguntas)")
    except Exception as e:
        messagebox.showerror("Error", f"No se pudo cargar:\n{e}")

# ══════════════════════════════════════════
#  TRANSCRIPCIÓN EN TIEMPO REAL
# ══════════════════════════════════════════
def transcribir_chunk(audio_np):
    """Transcribe un chunk de audio numpy y retorna el texto."""
    tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    sf.write(tmp.name, audio_np, SAMPLE_RATE)
    try:
        segments, _ = modelo_whisper.transcribe(
            tmp.name,
            language="en",
            beam_size=1,
            vad_filter=True,          # ignora silencio automáticamente
            vad_parameters={"min_silence_duration_ms": 500}
        )
        texto = " ".join(seg.text for seg in segments).strip()
    except Exception as e:
        texto = ""
        print(f"Error transcripción: {e}")
    finally:
        os.unlink(tmp.name)
    return texto

def grabar_y_transcribir():
    """Graba audio en chunks y transcribe cada uno en tiempo real."""
    global texto_acumulado, grabando, boton_grabar

    p = pyaudio.PyAudio()
    wasapi_info = p.get_host_api_info_by_type(pyaudio.paWASAPI)
    default_speakers = p.get_device_info_by_index(wasapi_info["defaultOutputDevice"])

    if not default_speakers.get("isLoopbackDevice", False):
        for loopback in p.get_loopback_device_info_generator():
            if default_speakers["name"] in loopback["name"]:
                default_speakers = loopback
                break

    sample_rate = int(default_speakers["defaultSampleRate"])
    channels    = int(default_speakers["maxInputChannels"])
    chunk       = 1024
    frames_por_chunk = int(sample_rate * CHUNK_SEGUNDOS)

    stream = p.open(
        format=pyaudio.paFloat32,
        channels=channels,
        rate=sample_rate,
        input=True,
        input_device_index=default_speakers["index"],
        frames_per_buffer=chunk
    )

    texto_acumulado = ""
    detener_grabacion.clear()
    frames_actuales = []

    actualizar_estado("🔴  Grabando en tiempo real...", COLORES["grabando"])

    while not detener_grabacion.is_set():
        data = stream.read(chunk, exception_on_overflow=False)
        frames_actuales.append(np.frombuffer(data, dtype=np.float32))

        # Cada CHUNK_SEGUNDOS procesamos
        if len(frames_actuales) >= frames_por_chunk // chunk:
            audio = np.concatenate(frames_actuales)
            if channels > 1:
                audio = audio.reshape(-1, channels).mean(axis=1)

            # Resamplear si es necesario
            if sample_rate != SAMPLE_RATE:
                factor = SAMPLE_RATE / sample_rate
                audio = np.interp(
                    np.arange(0, len(audio) * factor) / factor,
                    np.arange(len(audio)),
                    audio
                )

            frames_actuales = []

            # Transcribir en hilo separado para no bloquear grabación
            chunk_audio = audio.copy()
            def procesar_chunk(a=chunk_audio):
                global texto_acumulado
                texto = transcribir_chunk(a)
                if texto:
                    texto_acumulado = (texto_acumulado + " " + texto).strip()
                    actualizar_historial_tiempo_real(texto)
                    actualizar_estado(f"🔴  Grabando... | Último: \"{texto[:40]}...\"" if len(texto) > 40 else f"🔴  Grabando... | \"{texto}\"", COLORES["grabando"])

            threading.Thread(target=procesar_chunk, daemon=True).start()

    stream.stop_stream()
    stream.close()
    p.terminate()

    # Procesar lo que quedó grabado al presionar DETENER
    if frames_actuales:
        audio = np.concatenate(frames_actuales)
        if channels > 1:
            audio = audio.reshape(-1, channels).mean(axis=1)
        texto_final = transcribir_chunk(audio)
        if texto_final:
            texto_acumulado = (texto_acumulado + " " + texto_final).strip()

    finalizar_sesion()

def finalizar_sesion():
    """Procesa el texto acumulado al terminar la grabación."""
    global grabando, boton_grabar, texto_acumulado

    if not texto_acumulado.strip():
        actualizar_estado("⚠️  No se detectó audio claro.", COLORES["rosa"])
        grabando = False
        if boton_grabar:
            boton_grabar.config(text="⬤  GRABAR  (Ctrl+Space)", bg=COLORES["boton"])
        return

    actualizar_estado("🌐  Traduciendo texto completo...", COLORES["cyan"])
    texto_es = traductor.translate(texto_acumulado)

    actualizar_estado("🔍  Buscando en glosario...", COLORES["borde"])
    coincidencia = buscar_pregunta_similar(texto_acumulado)

    hora = datetime.datetime.now().strftime("%H:%M:%S")
    historial.append({"hora": hora, "en": texto_acumulado, "es": texto_es})
    agregar_al_historial(texto_acumulado, texto_es, hora,
                         coincidencia["pregunta"] if coincidencia else None)

    if ventana_principal:
        txt = texto_acumulado
        es  = texto_es
        c   = coincidencia
        ventana_principal.after(0, lambda: mostrar_flotante(txt, es, c))

    if coincidencia:
        actualizar_estado(f"✅  Pregunta detectada ({int(coincidencia['score']*100)}% similitud)", COLORES["verde"])
    else:
        actualizar_estado("✅  Listo — presiona GRABAR para continuar", COLORES["texto2"])

    grabando = False
    if boton_grabar:
        boton_grabar.config(text="⬤  GRABAR  (Ctrl+Space)", bg=COLORES["boton"])

# ══════════════════════════════════════════
#  ACTUALIZAR HISTORIAL EN TIEMPO REAL
# ══════════════════════════════════════════
_ultima_linea_en = ""

def actualizar_historial_tiempo_real(texto_nuevo):
    global _ultima_linea_en
    if not historial_widget:
        return
    if ventana_principal:
        ventana_principal.after(0, lambda: _insertar_chunk(texto_nuevo))

def _insertar_chunk(texto):
    global _ultima_linea_en
    historial_widget.config(state="normal")
    if not _ultima_linea_en:
        historial_widget.insert("end", f"\n[{datetime.datetime.now().strftime('%H:%M:%S')}] 🔴 EN VIVO\n", "hora")
    historial_widget.insert("end", texto + " ", "en")
    historial_widget.see("end")
    historial_widget.config(state="disabled")
    _ultima_linea_en += texto + " "

# ══════════════════════════════════════════
#  VENTANA FLOTANTE
# ══════════════════════════════════════════
def mostrar_flotante(texto_en, texto_es, coincidencia=None):
    global ventana_flotante_actual

    # Cerrar flotante anterior si existe
    try:
        if ventana_flotante_actual and ventana_flotante_actual.winfo_exists():
            ventana_flotante_actual.destroy()
    except:
        pass

    flotante = tk.Toplevel()
    ventana_flotante_actual = flotante
    flotante.title("")
    flotante.attributes("-topmost", True)
    flotante.attributes("-alpha", 0.96)
    flotante.overrideredirect(True)
    flotante.configure(bg=COLORES["fondo"])

    alto = 300 if coincidencia else 180
    ancho = 520
    sw = flotante.winfo_screenwidth()
    sh = flotante.winfo_screenheight()
    flotante.geometry(f"{ancho}x{alto}+{sw - ancho - 20}+{sh - alto - 70}")

    marco = tk.Frame(flotante, bg=COLORES["borde"], padx=2, pady=2)
    marco.pack(fill="both", expand=True)
    interior = tk.Frame(marco, bg=COLORES["fondo"])
    interior.pack(fill="both", expand=True)

    header = tk.Frame(interior, bg=COLORES["panel"], pady=6)
    header.pack(fill="x")
    tk.Label(header, text="◈ ADRIANA AI",
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
             wraplength=440, justify="left").pack(side="left", padx=6)

    tk.Frame(interior, bg=COLORES["borde2"], height=1).pack(fill="x", padx=10)

    fila_es = tk.Frame(interior, bg=COLORES["fondo"], pady=4)
    fila_es.pack(fill="x", padx=10)
    tk.Label(fila_es, text="ES›", bg=COLORES["fondo"],
             fg=COLORES["borde2"], font=("Consolas", 9, "bold")).pack(side="left")
    tk.Label(fila_es, text=texto_es, bg=COLORES["fondo"],
             fg=COLORES["cyan"], font=("Consolas", 10),
             wraplength=440, justify="left").pack(side="left", padx=6)

    if coincidencia:
        tk.Frame(interior, bg=COLORES["neon"], height=1).pack(fill="x", padx=10, pady=4)
        tk.Label(interior,
                 text=f"🔍 Pregunta detectada  ({int(coincidencia['score']*100)}% similitud)",
                 bg=COLORES["fondo"], fg=COLORES["amarillo"],
                 font=("Consolas", 8, "bold")).pack(anchor="w", padx=10)
        tk.Label(interior, text=f"  {coincidencia['pregunta']}",
                 bg=COLORES["fondo"], fg=COLORES["amarillo"],
                 font=("Consolas", 9, "italic"),
                 wraplength=490, justify="left").pack(anchor="w", padx=10)
        tk.Label(interior, text="💬 Respuestas sugeridas:",
                 bg=COLORES["fondo"], fg=COLORES["texto2"],
                 font=("Consolas", 8, "bold")).pack(anchor="w", padx=12, pady=(4, 0))
        for i, (r, t) in enumerate(zip(coincidencia["respuestas"], coincidencia["traducciones"])):
            tk.Label(interior, text=f"  {i+1}. {r}",
                     bg=COLORES["fondo"], fg=COLORES["verde"],
                     font=("Consolas", 9),
                     wraplength=490, justify="left").pack(anchor="w", padx=14)
            tk.Label(interior, text=f"     {t}",
                     bg=COLORES["fondo"], fg=COLORES["rosa"],
                     font=("Consolas", 8),
                     wraplength=490, justify="left").pack(anchor="w", padx=14)

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
    if label_estado and ventana_principal:
        ventana_principal.after(0, lambda: label_estado.config(
            text=texto, fg=color or COLORES["texto2"]))

def agregar_al_historial(texto_en, texto_es, hora, pregunta_detectada=None):
    global _ultima_linea_en
    if not historial_widget:
        return
    def _insertar():
        global _ultima_linea_en
        historial_widget.config(state="normal")
        historial_widget.insert("end", "\n", "sep")
        historial_widget.insert("end", f"ES › {texto_es}\n", "es")
        if pregunta_detectada:
            historial_widget.insert("end", f"🔍 {pregunta_detectada}\n", "match")
        historial_widget.insert("end", "─" * 55 + "\n", "sep")
        historial_widget.see("end")
        historial_widget.config(state="disabled")
        _ultima_linea_en = ""
    if ventana_principal:
        ventana_principal.after(0, _insertar)

# ══════════════════════════════════════════
#  TOGGLE GRABAR / DETENER
# ══════════════════════════════════════════
def iniciar_proceso():
    global grabando, boton_grabar, _ultima_linea_en
    if not grabando:
        grabando = True
        _ultima_linea_en = ""
        if boton_grabar:
            boton_grabar.config(text="⬛  DETENER", bg="#cc0000")
        hilo = threading.Thread(target=grabar_y_transcribir, daemon=True)
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
    global ventana_principal, label_estado, historial_widget, boton_grabar, label_guia

    ventana_principal = tk.Tk()
    ventana_principal.title("Adriana AI — Asistente de Inglés")
    ventana_principal.configure(bg=COLORES["fondo"])
    ventana_principal.geometry("620x750")
    ventana_principal.resizable(False, True)
    ventana_principal.minsize(620, 550)

    def minimizar_a_tray():
        ventana_principal.withdraw()

    ventana_principal.protocol("WM_DELETE_WINDOW", minimizar_a_tray)

    # HEADER
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

    # ZONA GUÍA
    zona_guia = tk.Frame(ventana_principal, bg=COLORES["fondo2"], pady=8)
    zona_guia.pack(fill="x", padx=20, pady=(12, 0))
    tk.Button(zona_guia, text="📂  Cargar guía del mes (.json)",
              command=cargar_guia,
              bg=COLORES["panel"], fg=COLORES["amarillo"],
              font=("Consolas", 9, "bold"), relief="flat",
              padx=12, pady=6, cursor="hand2").pack(side="left")
    label_guia = tk.Label(zona_guia,
                          text=f"📌 Glosario fijo: {len(GLOSARIO_FIJO)} preguntas",
                          bg=COLORES["fondo2"], fg=COLORES["texto2"],
                          font=("Consolas", 8))
    label_guia.pack(side="left", padx=12)

    # BOTÓN PRINCIPAL
    zona_boton = tk.Frame(ventana_principal, bg=COLORES["fondo"], pady=16)
    zona_boton.pack(fill="x")
    boton_grabar = tk.Button(
        zona_boton,
        text="⬤  GRABAR  (Ctrl+Space)",
        command=iniciar_proceso,
        bg=COLORES["boton"], fg="white",
        font=("Consolas", 13, "bold"),
        relief="flat", padx=30, pady=14,
        cursor="hand2",
        activebackground=COLORES["boton_hover"],
        activeforeground="white"
    )
    boton_grabar.pack()

    def hover_on(e):  boton_grabar.config(bg=COLORES["boton_hover"])
    def hover_off(e): boton_grabar.config(bg=COLORES["boton"])
    boton_grabar.bind("<Enter>", hover_on)
    boton_grabar.bind("<Leave>", hover_off)

    # ESTADO
    label_estado = tk.Label(
        ventana_principal,
        text="✅  Listo — presiona GRABAR o Ctrl+Space para comenzar",
        bg=COLORES["fondo"], fg=COLORES["texto2"],
        font=("Consolas", 9)
    )
    label_estado.pack(pady=4)

    # INFO TIEMPO REAL
    tk.Label(ventana_principal,
             text="⚡ Transcripción en tiempo real cada 6 segundos",
             bg=COLORES["fondo"], fg=COLORES["borde"],
             font=("Consolas", 8)).pack()

    tk.Frame(ventana_principal, bg=COLORES["borde"], height=1).pack(fill="x", padx=20, pady=8)

    # HISTORIAL
    zona_hist = tk.Frame(ventana_principal, bg=COLORES["fondo"])
    zona_hist.pack(fill="both", expand=True, padx=20)
    tk.Label(zona_hist, text="▸ TRANSCRIPCIÓN EN VIVO / HISTORIAL",
             bg=COLORES["fondo"], fg=COLORES["borde"],
             font=("Consolas", 9, "bold")).pack(anchor="w", pady=(0, 6))

    historial_widget = scrolledtext.ScrolledText(
        zona_hist,
        bg=COLORES["fondo2"], fg=COLORES["texto"],
        font=("Consolas", 9), relief="flat", bd=0,
        state="disabled",
        insertbackground=COLORES["borde"],
        selectbackground=COLORES["neon"],
        wrap="word"
    )
    historial_widget.pack(fill="both", expand=True)

    historial_widget.tag_config("hora",  foreground=COLORES["texto2"])
    historial_widget.tag_config("en",    foreground=COLORES["verde"])
    historial_widget.tag_config("es",    foreground=COLORES["cyan"])
    historial_widget.tag_config("match", foreground=COLORES["amarillo"])
    historial_widget.tag_config("sep",   foreground=COLORES["panel"])

    # BOTONES INFERIORES
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

    # FOOTER
    tk.Label(ventana_principal,
             text="Faster-Whisper · Argos Translate · WASAPI Loopback  —  100% local",
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