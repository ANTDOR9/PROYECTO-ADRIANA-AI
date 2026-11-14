import threading
import queue
import tempfile
import os
import json
import numpy as np
import pyaudiowpatch as pyaudio
import soundfile as sf
import keyboard
import tkinter as tk
from tkinter import scrolledtext, filedialog, messagebox, ttk

# Modo de dispositivo elegido en Configuración (config.json). Se aplica al reiniciar.
#   mixto = Whisper en la GPU, traducción en el procesador
#   gpu   = Whisper y traducción en la GPU
#   cpu   = todo en el procesador
try:
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json"),
              "r", encoding="utf-8") as _f:
        MODO_DISPOSITIVO = json.load(_f).get("dispositivo", "mixto")
except Exception:
    MODO_DISPOSITIVO = "mixto"
if MODO_DISPOSITIVO not in ("mixto", "gpu", "cpu"):
    MODO_DISPOSITIVO = "mixto"
os.environ["ARGOS_DEVICE_TYPE"] = "cuda" if MODO_DISPOSITIVO == "gpu" else "cpu"

import argostranslate.translate
import argostranslate.settings as _argos_settings
from PIL import Image, ImageDraw
import pystray
import datetime
from faster_whisper import WhisperModel
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import configuracion as _cfg
from estilo import COLORES, instalar_hover
from configuracion import (
    cargar_config, guardar_config, abrir_configuracion,
    calcular_geometria_emergente, calcular_geometria_subtitulos
)

# Ruta directa a FFmpeg
os.environ["PATH"] = r"C:\ffmpeg\bin" + os.pathsep + os.environ.get("PATH", "")

# Librerías CUDA instaladas con pip (nvidia-cublas-cu12, nvidia-cudnn-cu12): que Windows las encuentre
import sys
_nvidia = os.path.join(sys.prefix, "Lib", "site-packages", "nvidia")
if os.path.isdir(_nvidia):
    for _sub in os.listdir(_nvidia):
        _bin = os.path.join(_nvidia, _sub, "bin")
        if os.path.isdir(_bin):
            os.environ["PATH"] = _bin + os.pathsep + os.environ["PATH"]
            try:
                os.add_dll_directory(_bin)
            except Exception:
                pass

# ══════════════════════════════════════════
#  CONFIGURACIÓN
# ══════════════════════════════════════════
MODELO_WHISPER   = "small"
CHUNK_SEGUNDOS   = 4
SAMPLE_RATE      = 16000
ARCHIVO_GLOSARIO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "glosario.json")

# La paleta vive en estilo.py (COLORES)

# ══════════════════════════════════════════
#  GLOSARIO
# ══════════════════════════════════════════
GLOSARIO_GENERAL_DEFAULT = [
    {"pregunta_en_ingles": "How are you?",
     "respuestas_ingles": ["I'm fine, thank you.", "I'm great, thanks!", "I'm okay, and you?"],
     "traducciones_espanol": ["Estoy bien, gracias.", "Estoy genial, ¡gracias!", "Estoy bien, ¿y tú?"]},
    {"pregunta_en_ingles": "How are you today?",
     "respuestas_ingles": ["I'm doing well, thank you.", "I'm a little tired today.", "I'm very happy today!"],
     "traducciones_espanol": ["Estoy bien hoy, gracias.", "Estoy un poco cansado hoy.", "¡Estoy muy feliz hoy!"]},
    {"pregunta_en_ingles": "What did you do this weekend?",
     "respuestas_ingles": ["I stayed at home and rested.", "I went out with my family.", "I studied and watched TV."],
     "traducciones_espanol": ["Me quedé en casa y descansé.", "Salí con mi familia.", "Estudié y vi televisión."]},
    {"pregunta_en_ingles": "How was your weekend?",
     "respuestas_ingles": ["It was great, I relaxed a lot.", "It was okay, nothing special.", "It was busy but fun."],
     "traducciones_espanol": ["Estuvo genial, descansé mucho.", "Estuvo bien, nada especial.", "Estuvo ocupado pero divertido."]},
    {"pregunta_en_ingles": "How was your week?",
     "respuestas_ingles": ["It was good, thank you.", "It was a bit stressful.", "It was very productive."],
     "traducciones_espanol": ["Estuvo bien, gracias.", "Fue un poco estresante.", "Fue muy productiva."]},
    {"pregunta_en_ingles": "What did you do yesterday?",
     "respuestas_ingles": ["I worked and then cooked dinner.", "I visited my family.", "I stayed home and rested."],
     "traducciones_espanol": ["Trabajé y luego cociné la cena.", "Visité a mi familia.", "Me quedé en casa y descansé."]},
    {"pregunta_en_ingles": "Are you ready for class?",
     "respuestas_ingles": ["Yes, I'm ready!", "Almost, give me a second.", "Yes, let's start!"],
     "traducciones_espanol": ["¡Sí, estoy listo!", "Casi, dame un segundo.", "¡Sí, empecemos!"]},
    {"pregunta_en_ingles": "Can you hear me?",
     "respuestas_ingles": ["Yes, I can hear you clearly.", "Yes, loud and clear!", "No, there is an echo."],
     "traducciones_espanol": ["Sí, te escucho claramente.", "¡Sí, muy claro!", "No, hay un eco."]},
    {"pregunta_en_ingles": "Do you have any questions?",
     "respuestas_ingles": ["No, I understand.", "Yes, I have one question.", "Can you repeat that please?"],
     "traducciones_espanol": ["No, entiendo.", "Sí, tengo una pregunta.", "¿Puedes repetir eso por favor?"]},
    {"pregunta_en_ingles": "What is your name?",
     "respuestas_ingles": ["My name is Anthony.", "I'm Anthony, nice to meet you.", "Anthony, but you can call me Tony."],
     "traducciones_espanol": ["Mi nombre es Anthony.", "Soy Anthony, mucho gusto.", "Anthony, pero puedes llamarme Tony."]},
    {"pregunta_en_ingles": "Where are you from?",
     "respuestas_ingles": ["I'm from Peru.", "I'm from Arequipa, Peru.", "I'm Peruvian."],
     "traducciones_espanol": ["Soy de Perú.", "Soy de Arequipa, Perú.", "Soy peruano."]},
    {"pregunta_en_ingles": "How do you feel today?",
     "respuestas_ingles": ["I feel good, thank you.", "I feel a little nervous.", "I feel excited to learn!"],
     "traducciones_espanol": ["Me siento bien, gracias.", "Me siento un poco nervioso.", "¡Me siento emocionado de aprender!"]},
    {"pregunta_en_ingles": "What did you have for breakfast?",
     "respuestas_ingles": ["I had bread and coffee.", "I had eggs and juice.", "I didn't have breakfast today."],
     "traducciones_espanol": ["Comí pan y café.", "Comí huevos y jugo.", "No desayuné hoy."]},
    {"pregunta_en_ingles": "Can you introduce yourself?",
     "respuestas_ingles": ["Sure! My name is Anthony, I'm from Peru.", "Of course! I'm Anthony and I'm learning English.", "Yes! I'm Anthony, nice to meet everyone."],
     "traducciones_espanol": ["¡Claro! Me llamo Anthony, soy de Perú.", "¡Por supuesto! Soy Anthony y estoy aprendiendo inglés.", "¡Sí! Soy Anthony, mucho gusto a todos."]},
]

def glosario_vacio():
    return {"general": GLOSARIO_GENERAL_DEFAULT.copy(), "semanas": {}, "semanas_activas": []}

def cargar_glosario_json():
    if os.path.exists(ARCHIVO_GLOSARIO):
        try:
            with open(ARCHIVO_GLOSARIO, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return glosario_vacio()

def guardar_glosario_json(data):
    with open(ARCHIVO_GLOSARIO, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

glosario_data = cargar_glosario_json()

def obtener_preguntas_activas():
    resultado = list(glosario_data["general"])
    for semana in glosario_data.get("semanas_activas", []):
        resultado += glosario_data["semanas"].get(semana, [])
    return resultado

# ══════════════════════════════════════════
#  ESTADO GLOBAL
# ══════════════════════════════════════════
historial               = []
grabando                = False
ventana_principal       = None
label_estado            = None
historial_widget        = None
tray_icon               = None
boton_grabar            = None
label_punto             = None
detener_grabacion       = threading.Event()
texto_acumulado         = ""
ventana_emergente_actual = None
ventana_subtitulos      = None
_ultima_linea_en        = ""
_lock_emergente         = threading.Lock()
_ultima_pregunta        = ""

# ══════════════════════════════════════════
#  CARGAR MODELOS
# ══════════════════════════════════════════
print("⏳ Cargando Faster-Whisper (modelo small)...")
INFO_WHISPER = "CPU"

def _cargar_whisper():
    global INFO_WHISPER
    if MODO_DISPOSITIVO != "cpu":
        # Usa la GPU NVIDIA con el tipo de cálculo que ella soporte.
        # Las GTX 10xx (Pascal) no soportan float16 bien: usan int8.
        try:
            import ctranslate2
            soportados = ctranslate2.get_supported_compute_types("cuda")
        except Exception as e:
            print(f"Whisper: no se detecta CUDA ({e}).")
            soportados = set()
        for tipo in ("float16", "int8_float16", "int8_float32", "int8"):
            if tipo not in soportados:
                continue
            try:
                m = WhisperModel(MODELO_WHISPER, device="cuda", compute_type=tipo)
                list(m.transcribe(np.zeros(SAMPLE_RATE, dtype=np.float32), language="en")[0])
                print(f"Whisper: usando GPU (CUDA, {tipo})")
                INFO_WHISPER = f"GPU ({tipo})"
                return m
            except Exception as e:
                print(f"Whisper: GPU con {tipo} falló ({e})")
        print("Whisper: no se pudo usar la GPU, usando CPU.")
    else:
        print("Whisper: usando CPU (modo solo procesador).")
    INFO_WHISPER = "CPU"
    return WhisperModel(MODELO_WHISPER, device="cpu", compute_type="int8")

modelo_whisper = _cargar_whisper()
print("✅ Faster-Whisper listo")

print("⏳ Cargando traductor...")
traductor = argostranslate.translate.get_translation_from_codes("en", "es")
INFO_ARGOS = "CPU"
if MODO_DISPOSITIVO == "gpu":
    try:
        traductor.translate("hello")
        INFO_ARGOS = "GPU"
    except Exception as e:
        print(f"Traductor: la GPU falló ({e}); usando CPU.")
        _argos_settings.device = "cpu"
print(f"✅ Traductor listo ({INFO_ARGOS})")
_cfg.INFO_DISPOSITIVO = f"Whisper en {INFO_WHISPER} · Traducción en {INFO_ARGOS}"

# ══════════════════════════════════════════
#  BÚSQUEDA POR SIMILITUD
# ══════════════════════════════════════════
_cache_tfidf = {"clave": None, "vec": None, "mat": None}

def buscar_pregunta_similar(texto):
    preguntas_activas = obtener_preguntas_activas()
    if not preguntas_activas or not texto.strip():
        return None
    preguntas = [item["pregunta_en_ingles"] for item in preguntas_activas]
    try:
        clave = tuple(preguntas)
        if _cache_tfidf["clave"] != clave:
            vec = TfidfVectorizer()
            mat = vec.fit_transform(preguntas)
            _cache_tfidf.update(clave=clave, vec=vec, mat=mat)
        v = _cache_tfidf["vec"].transform([texto])
        similitudes = cosine_similarity(v, _cache_tfidf["mat"]).flatten()
        idx   = similitudes.argmax()
        score = similitudes[idx]
        if score < 0.15:
            return None
        return {
            "pregunta":     preguntas_activas[idx]["pregunta_en_ingles"],
            "respuestas":   preguntas_activas[idx]["respuestas_ingles"],
            "traducciones": preguntas_activas[idx]["traducciones_espanol"],
            "score":        round(float(score), 2)
        }
    except Exception as e:
        print(f"Error similitud: {e}")
        return None

# ══════════════════════════════════════════
#  TRANSCRIPCIÓN
# ══════════════════════════════════════════
PAUSA_SALTO   = 1.2   # segundos de silencio -> salto de línea
PAUSA_PARRAFO = 3.0   # segundos de silencio -> párrafo aparte (línea en blanco)
_silencio_acum = 0.0  # silencio acumulado desde la última voz

def _separador_pausa(pausa, previo):
    """Separador entre dos trozos de texto según la pausa (en segundos) que hubo."""
    if pausa < PAUSA_SALTO:
        return " "
    punto = "" if previo.rstrip().endswith((".", "?", "!", "…")) else "."
    return punto + ("\n\n" if pausa >= PAUSA_PARRAFO else "\n")

def transcribir_chunk_detallado(audio_np):
    """Devuelve [(texto, inicio_seg, fin_seg), ...] del chunk."""
    try:
        segments, _ = modelo_whisper.transcribe(
            np.ascontiguousarray(audio_np, dtype=np.float32),
            language="en", beam_size=1,
            vad_filter=True,
            vad_parameters={"min_silence_duration_ms": 500},
            condition_on_previous_text=False
        )
        return [(sg.text.strip(), sg.start, sg.end) for sg in segments if sg.text.strip()]
    except Exception as e:
        print(f"Error transcripción: {e}")
        return []

def transcribir_chunk(audio_np):
    return " ".join(t for t, _, _ in transcribir_chunk_detallado(audio_np)).strip()

# Cola con un solo trabajador: procesa los chunks en orden
_cola_chunks = queue.Queue()
def _trabajador_chunks():
    while True:
        tarea = _cola_chunks.get()
        try:
            tarea()
        except Exception as e:
            print(f"Error procesando chunk: {e}")
threading.Thread(target=_trabajador_chunks, daemon=True).start()

# ══════════════════════════════════════════
#  SUBTÍTULOS EN TIEMPO REAL
# ══════════════════════════════════════════
def crear_ventana_subtitulos():
    global ventana_subtitulos
    config = cargar_config()
    if not config["subtitulos_activos"]:
        return

    if ventana_subtitulos:
        try:
            if ventana_subtitulos.winfo_exists():
                return
        except:
            pass

    sub = tk.Toplevel()
    ventana_subtitulos = sub
    sub.overrideredirect(True)
    sub.attributes("-topmost", True)
    sub.configure(bg="#000000")

    sw = sub.winfo_screenwidth()
    sh = sub.winfo_screenheight()
    ancho, alto, x, y = calcular_geometria_subtitulos(config, sw, sh)
    sub.geometry(f"{ancho}x{alto}+{x}+{y}")
    sub.attributes("-alpha", config["subtitulos_opacidad"])

    # Contenido
    frame = tk.Frame(sub, bg="#000000", padx=10, pady=6)
    frame.pack(fill="both", expand=True)

    # Botón cerrar sutil en esquina superior derecha
    btn_cerrar = tk.Label(frame, text="✕",
                          bg="#000000", fg="#888899",
                          font=("Segoe UI", 10, "bold"), cursor="hand2")
    btn_cerrar.place(relx=1.0, rely=0.0, anchor="ne", x=-2, y=2)
    btn_cerrar.bind("<Button-1>", lambda e: cerrar_subtitulos())
    btn_cerrar.bind("<Enter>", lambda e: btn_cerrar.config(fg=COLORES["rosa"]))
    btn_cerrar.bind("<Leave>", lambda e: btn_cerrar.config(fg="#444466"))

    sub.lbl_en = tk.Label(frame, text="",
                           bg="#000000", fg=COLORES["verde"],
                           font=("Segoe UI", 11, "bold"),
                           wraplength=ancho - 30, justify="center")
    sub.lbl_en.pack(fill="x")

    sub.lbl_es = tk.Label(frame, text="",
                           bg="#000000", fg="white",
                           font=("Segoe UI", 11),
                           wraplength=ancho - 30, justify="center")
    sub.lbl_es.pack(fill="x")

    # Arrastrable
    def iniciar_arrastre(e):
        sub._drag_x = e.x
        sub._drag_y = e.y
    def arrastrar(e):
        x = sub.winfo_x() + e.x - sub._drag_x
        y = sub.winfo_y() + e.y - sub._drag_y
        sub.geometry(f"+{x}+{y}")
    frame.bind("<Button-1>", iniciar_arrastre)
    frame.bind("<B1-Motion>", arrastrar)
    sub.lbl_en.bind("<Button-1>", iniciar_arrastre)
    sub.lbl_en.bind("<B1-Motion>", arrastrar)
    sub.lbl_es.bind("<Button-1>", iniciar_arrastre)
    sub.lbl_es.bind("<B1-Motion>", arrastrar)

def actualizar_subtitulos(texto_en, texto_es):
    global ventana_subtitulos
    if not ventana_subtitulos:
        return
    try:
        if ventana_subtitulos.winfo_exists():
            ventana_subtitulos.lbl_en.config(text=texto_en)
            ventana_subtitulos.lbl_es.config(text=texto_es)
    except:
        pass

def cerrar_subtitulos():
    global ventana_subtitulos
    try:
        if ventana_subtitulos and ventana_subtitulos.winfo_exists():
            ventana_subtitulos.destroy()
    except:
        pass
    ventana_subtitulos = None

# ══════════════════════════════════════════
#  VENTANA EMERGENTE DE PREGUNTAS
# ══════════════════════════════════════════
def mostrar_emergente(texto_en, texto_es, coincidencia):
    global ventana_emergente_actual, _ultima_pregunta

    config = cargar_config()
    if not config["emergente_activa"]:
        return
    if coincidencia["pregunta"] == _ultima_pregunta:
        return
    _ultima_pregunta = coincidencia["pregunta"]

    with _lock_emergente:
        try:
            if ventana_emergente_actual and ventana_emergente_actual.winfo_exists():
                ventana_emergente_actual.destroy()
        except:
            pass

    flotante = tk.Toplevel()
    ventana_emergente_actual = flotante
    flotante.overrideredirect(True)
    flotante.attributes("-topmost", True)
    flotante.configure(bg=COLORES["fondo"])
    flotante.resizable(False, False)
    flotante.attributes("-alpha", config["emergente_opacidad"])

    sw = flotante.winfo_screenwidth()
    sh = flotante.winfo_screenheight()
    ancho, alto, x, y = calcular_geometria_emergente(config, sw, sh)
    flotante.geometry(f"{ancho}x{alto}+{x}+{y}")
    flotante.minsize(300, 200)

    marco = tk.Frame(flotante, bg=COLORES["borde"], padx=2, pady=2)
    marco.pack(fill="both", expand=True)
    interior = tk.Frame(marco, bg=COLORES["fondo"])
    interior.pack(fill="both", expand=True)

    header = tk.Frame(interior, bg=COLORES["panel"], pady=5)
    header.pack(fill="x")
    tk.Label(header, text="💬 PREGUNTA DETECTADA",
             bg=COLORES["panel"], fg=COLORES["amarillo"],
             font=("Segoe UI", 9, "bold")).pack(side="left", padx=8)
    tk.Button(header, text="⚙", command=lambda: abrir_configuracion(flotante, _aplicar_config),
              bg=COLORES["panel"], fg=COLORES["texto2"],
              relief="flat", font=("Segoe UI", 10),
              cursor="hand2", bd=0).pack(side="right", padx=2)
    tk.Button(header, text="✕", command=flotante.destroy,
              bg=COLORES["panel"], fg=COLORES["rosa"],
              relief="flat", font=("Segoe UI", 10, "bold"),
              cursor="hand2", bd=0).pack(side="right", padx=6)

    contenido = scrolledtext.ScrolledText(
        interior, bg=COLORES["fondo"], fg=COLORES["texto"],
        font=("Segoe UI", 10), relief="flat", bd=0,
        wrap="word", state="normal"
    )
    contenido.pack(fill="both", expand=True, padx=8, pady=6)

    contenido.tag_config("match",   foreground=COLORES["amarillo"], font=("Segoe UI", 9, "bold"))
    contenido.tag_config("sep",     foreground=COLORES["panel"])
    contenido.tag_config("resp_en", foreground=COLORES["verde"],    font=("Segoe UI", 10))
    contenido.tag_config("resp_es", foreground=COLORES["rosa"],     font=("Segoe UI", 9))
    contenido.tag_config("score",   foreground=COLORES["cyan"],     font=("Segoe UI", 8))

    contenido.insert("end", f"🔍 {coincidencia['pregunta']}\n", "match")
    contenido.insert("end", f"   Similitud: {int(coincidencia['score']*100)}%\n\n", "score")
    contenido.insert("end", "💬 Respuestas sugeridas:\n", "match")
    contenido.insert("end", "─" * 38 + "\n", "sep")

    for i, (r, t) in enumerate(zip(coincidencia["respuestas"], coincidencia["traducciones"])):
        contenido.insert("end", f"  {i+1}. {r}\n", "resp_en")
        contenido.insert("end", f"     {t}\n\n", "resp_es")

    contenido.config(state="disabled")

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
#  APLICAR CONFIG EN TIEMPO REAL
# ══════════════════════════════════════════
def _aplicar_config(config):
    global ventana_subtitulos
    # Actualizar subtítulos si están activos
    if config["subtitulos_activos"]:
        cerrar_subtitulos()
        if grabando and ventana_principal:
            ventana_principal.after(100, crear_ventana_subtitulos)
    else:
        cerrar_subtitulos()
    actualizar_info()

# ══════════════════════════════════════════
#  GRABACIÓN EN TIEMPO REAL
# ══════════════════════════════════════════
def grabar_y_transcribir():
    global texto_acumulado, grabando, boton_grabar, _silencio_acum

    p = pyaudio.PyAudio()
    wasapi_info = p.get_host_api_info_by_type(pyaudio.paWASAPI)
    default_spk = p.get_device_info_by_index(wasapi_info["defaultOutputDevice"])

    if not default_spk.get("isLoopbackDevice", False):
        for loopback in p.get_loopback_device_info_generator():
            if default_spk["name"] in loopback["name"]:
                default_spk = loopback
                break

    sample_rate      = int(default_spk["defaultSampleRate"])
    channels         = int(default_spk["maxInputChannels"])
    chunk            = 1024
    frames_por_chunk = int(sample_rate * CHUNK_SEGUNDOS)

    stream = p.open(
        format=pyaudio.paFloat32, channels=channels,
        rate=sample_rate, input=True,
        input_device_index=default_spk["index"],
        frames_per_buffer=chunk
    )

    texto_acumulado = ""
    _silencio_acum = 0.0
    detener_grabacion.clear()
    frames_actuales = []
    actualizar_estado("🔴  Grabando en tiempo real...", COLORES["grabando"])

    # Abrir subtítulos
    if ventana_principal:
        ventana_principal.after(0, crear_ventana_subtitulos)

    while not detener_grabacion.is_set():
        data = stream.read(chunk, exception_on_overflow=False)
        frames_actuales.append(np.frombuffer(data, dtype=np.float32))

        if len(frames_actuales) >= frames_por_chunk // chunk:
            audio = np.concatenate(frames_actuales)
            if channels > 1:
                audio = audio.reshape(-1, channels).mean(axis=1)
            if sample_rate != SAMPLE_RATE:
                factor = SAMPLE_RATE / sample_rate
                audio = np.interp(
                    np.arange(0, len(audio) * factor) / factor,
                    np.arange(len(audio)), audio
                )
            frames_actuales = []
            chunk_audio = audio.copy()

            def procesar_chunk(a=chunk_audio):
                global texto_acumulado, _silencio_acum
                dur  = len(a) / SAMPLE_RATE
                segs = transcribir_chunk_detallado(a)
                if not segs:
                    _silencio_acum += dur
                    return
                # Pausa antes de este chunk = silencio previo + silencio inicial
                pausa_inicial = _silencio_acum + segs[0][1]
                _silencio_acum = max(0.0, dur - segs[-1][2])
                # Texto con saltos de línea donde hubo pausas dentro del chunk
                texto_fmt = segs[0][0]
                for i in range(1, len(segs)):
                    texto_fmt += _separador_pausa(segs[i][1] - segs[i-1][2], texto_fmt) + segs[i][0]
                texto = " ".join(t for t, _, _ in segs)
                texto_acumulado = (texto_acumulado + " " + texto).strip()
                insertar_chunk_en_historial(texto_fmt, pausa_inicial)

                # Mostrar ya el inglés, sin esperar la traducción
                if ventana_principal:
                    ventana_principal.after(0, lambda t=texto:
                                            actualizar_subtitulos(t, ""))

                # Traducir y completar los subtítulos
                try:
                    texto_es = traductor.translate(texto)
                except:
                    texto_es = ""

                if ventana_principal:
                    ventana_principal.after(0, lambda t=texto, e=texto_es:
                                            actualizar_subtitulos(t, e))

                # Buscar pregunta para emergente
                coincidencia = buscar_pregunta_similar(texto)
                etiqueta = f"🔴 \"{texto[:45]}...\"" if len(texto) > 45 else f"🔴 \"{texto}\""
                actualizar_estado(etiqueta, COLORES["grabando"])

                # Mostrar emergente SOLO si hay pregunta con respuestas
                if coincidencia and ventana_principal:
                    ventana_principal.after(0, lambda t=texto, e=texto_es, c=coincidencia:
                                            mostrar_emergente(t, e, c))

            _cola_chunks.put(procesar_chunk)

    stream.stop_stream()
    stream.close()
    p.terminate()

    if frames_actuales:
        audio = np.concatenate(frames_actuales)
        if channels > 1:
            audio = audio.reshape(-1, channels).mean(axis=1)
        texto_final = transcribir_chunk(audio)
        if texto_final:
            texto_acumulado = (texto_acumulado + " " + texto_final).strip()
            insertar_chunk_en_historial(texto_final)

    finalizar_sesion()

def finalizar_sesion():
    global grabando, boton_grabar, texto_acumulado, _ultima_pregunta

    # Cerrar subtítulos al terminar
    if ventana_principal:
        ventana_principal.after(0, cerrar_subtitulos)

    if not texto_acumulado.strip():
        actualizar_estado("⚠️  No se detectó audio claro.", COLORES["rosa"])
        grabando = False
        if boton_grabar:
            boton_grabar.config(text="●  Grabar", bg=COLORES["boton"])
        return

    try:
        texto_es = traductor.translate(texto_acumulado)
    except:
        texto_es = ""

    coincidencia = buscar_pregunta_similar(texto_acumulado)
    hora = datetime.datetime.now().strftime("%H:%M:%S")
    historial.append({"hora": hora, "en": texto_acumulado, "es": texto_es})
    agregar_separador_historial(texto_es, hora, coincidencia["pregunta"] if coincidencia else None)
    _ultima_pregunta = ""

    if coincidencia:
        actualizar_estado(f"✅  Sesión finalizada — {int(coincidencia['score']*100)}% similitud", COLORES["verde"])
    else:
        actualizar_estado("✅  Sesión finalizada — presiona GRABAR para continuar", COLORES["texto2"])

    grabando = False
    if boton_grabar:
        boton_grabar.config(text="●  Grabar", bg=COLORES["boton"])

# ══════════════════════════════════════════
#  HISTORIAL
# ══════════════════════════════════════════
def insertar_chunk_en_historial(texto, pausa=0.0):
    global _ultima_linea_en
    if not historial_widget or not ventana_principal:
        return
    def _hacer():
        global _ultima_linea_en
        historial_widget.config(state="normal")
        if not _ultima_linea_en:
            hora = datetime.datetime.now().strftime("%H:%M:%S")
            historial_widget.insert("end", f"\n[{hora}] 🔴 EN VIVO\n", "hora")
            sep = ""
        else:
            sep = _separador_pausa(pausa, _ultima_linea_en)
            historial_widget.insert("end", sep, "en")
        historial_widget.insert("end", texto, "en")
        historial_widget.see("end")
        historial_widget.config(state="disabled")
        _ultima_linea_en += sep + texto
    ventana_principal.after(0, _hacer)

def agregar_separador_historial(texto_es, hora, pregunta=None):
    global _ultima_linea_en
    if not historial_widget or not ventana_principal:
        return
    def _hacer():
        global _ultima_linea_en
        historial_widget.config(state="normal")
        historial_widget.insert("end", f"\nES › {texto_es}\n", "es")
        if pregunta:
            historial_widget.insert("end", f"🔍 {pregunta}\n", "match")
        historial_widget.insert("end", "─" * 55 + "\n", "sep")
        historial_widget.see("end")
        historial_widget.config(state="disabled")
        _ultima_linea_en = ""
    ventana_principal.after(0, _hacer)

def actualizar_estado(texto, color=None):
    if label_estado and ventana_principal:
        def _a():
            label_estado.config(text=texto, fg=COLORES["texto"])
            if label_punto:
                label_punto.config(fg=color or COLORES["verde"])
        ventana_principal.after(0, _a)

def actualizar_info():
    pass  # se llama desde el loop de refresco

# ══════════════════════════════════════════
#  TOGGLE GRABAR
# ══════════════════════════════════════════
def iniciar_proceso():
    global grabando, boton_grabar, _ultima_linea_en, _ultima_pregunta
    if not grabando:
        grabando = True
        _ultima_linea_en = ""
        _ultima_pregunta = ""
        if boton_grabar:
            boton_grabar.config(text="■  Detener", bg=COLORES["grabando"])
        threading.Thread(target=grabar_y_transcribir, daemon=True).start()
    else:
        detener_grabacion.set()
        if boton_grabar:
            boton_grabar.config(text="Procesando…", bg=COLORES["panel"])

# ══════════════════════════════════════════
#  EDITOR DE GLOSARIO
# ══════════════════════════════════════════
def abrir_editor_glosario():
    editor = tk.Toplevel()
    editor.title("📚 Editor de Glosario")
    editor.configure(bg=COLORES["fondo"])
    editor.geometry("700x600")
    editor.minsize(600, 500)
    editor.resizable(True, True)

    style = ttk.Style()
    style.theme_use("default")
    style.configure("TNotebook",      background=COLORES["fondo"], borderwidth=0)
    style.configure("TNotebook.Tab",  background=COLORES["panel"], foreground=COLORES["texto2"],
                    padding=[10, 4],  font=("Segoe UI", 9))
    style.map("TNotebook.Tab",
              background=[("selected", COLORES["borde"])],
              foreground=[("selected", "white")])

    notebook = ttk.Notebook(editor)
    notebook.pack(fill="both", expand=True, padx=10, pady=10)

    def crear_pestaña(nombre_seccion, es_general=False):
        frame = tk.Frame(notebook, bg=COLORES["fondo"])
        notebook.add(frame, text=f"{'🌐' if es_general else '📅'} {nombre_seccion}")

        frame_lista = tk.Frame(frame, bg=COLORES["fondo2"], width=220)
        frame_lista.pack(side="left", fill="y", padx=(0, 4), pady=4)
        frame_lista.pack_propagate(False)

        tk.Label(frame_lista, text="Preguntas guardadas:",
                 bg=COLORES["fondo2"], fg=COLORES["borde"],
                 font=("Segoe UI", 8, "bold")).pack(anchor="w", padx=8, pady=(8, 2))

        lista_box = tk.Listbox(
            frame_lista, bg=COLORES["fondo"], fg=COLORES["verde"],
            font=("Segoe UI", 8), relief="flat", bd=0,
            selectbackground=COLORES["neon"], selectforeground=COLORES["fondo"],
            activestyle="none"
        )
        lista_box.pack(fill="both", expand=True, padx=4, pady=4)

        frame_form = tk.Frame(frame, bg=COLORES["fondo"])
        frame_form.pack(side="left", fill="both", expand=True, pady=4)

        def campo(label, color=None):
            tk.Label(frame_form, text=label, bg=COLORES["fondo"],
                     fg=color or COLORES["texto2"], font=("Segoe UI", 8)).pack(anchor="w", padx=8, pady=(6, 0))
            e = tk.Entry(frame_form, bg=COLORES["fondo2"], fg=color or COLORES["texto"],
                         font=("Segoe UI", 9), relief="flat", bd=4,
                         insertbackground=COLORES["borde"])
            e.pack(fill="x", padx=8)
            return e

        e_pregunta = campo("Pregunta en inglés:")
        tk.Frame(frame_form, bg=COLORES["panel"], height=1).pack(fill="x", padx=8, pady=6)

        pares = []
        for i in range(1, 4):
            e_r = campo(f"Respuesta {i}:", COLORES["verde"])
            e_t = campo(f"  Traducción {i}:", COLORES["rosa"])
            pares.append((e_r, e_t))

        def obtener_lista_seccion():
            if es_general:
                return glosario_data["general"]
            return glosario_data["semanas"].setdefault(nombre_seccion, [])

        def refrescar_lista():
            lista_box.delete(0, "end")
            for item in obtener_lista_seccion():
                lista_box.insert("end", item["pregunta_en_ingles"][:35])

        def limpiar_form():
            e_pregunta.delete(0, "end")
            for e_r, e_t in pares:
                e_r.delete(0, "end")
                e_t.delete(0, "end")

        def al_seleccionar(event):
            sel = lista_box.curselection()
            if not sel:
                return
            item = obtener_lista_seccion()[sel[0]]
            limpiar_form()
            e_pregunta.insert(0, item["pregunta_en_ingles"])
            for i, (e_r, e_t) in enumerate(pares):
                if i < len(item["respuestas_ingles"]):
                    e_r.insert(0, item["respuestas_ingles"][i])
                if i < len(item["traducciones_espanol"]):
                    e_t.insert(0, item["traducciones_espanol"][i])

        lista_box.bind("<<ListboxSelect>>", al_seleccionar)

        def agregar():
            pregunta = e_pregunta.get().strip()
            if not pregunta:
                messagebox.showwarning("Campo vacío", "Escribe la pregunta en inglés.", parent=editor)
                return
            respuestas   = [e_r.get().strip() for e_r, _ in pares if e_r.get().strip()]
            traducciones = [e_t.get().strip() for _, e_t in pares if e_t.get().strip()]
            if not respuestas:
                messagebox.showwarning("Sin respuestas", "Agrega al menos una respuesta.", parent=editor)
                return
            nuevo = {"pregunta_en_ingles": pregunta, "respuestas_ingles": respuestas, "traducciones_espanol": traducciones}
            lista = obtener_lista_seccion()
            for i, item in enumerate(lista):
                if item["pregunta_en_ingles"].lower() == pregunta.lower():
                    lista[i] = nuevo
                    guardar_glosario_json(glosario_data)
                    refrescar_lista()
                    limpiar_form()
                    actualizar_estado("✅  Pregunta actualizada", COLORES["verde"])
                    return
            lista.append(nuevo)
            guardar_glosario_json(glosario_data)
            refrescar_lista()
            limpiar_form()
            actualizar_estado("✅  Pregunta agregada", COLORES["verde"])

        def eliminar():
            sel = lista_box.curselection()
            if not sel:
                return
            lista = obtener_lista_seccion()
            item  = lista[sel[0]]
            if messagebox.askyesno("Eliminar", f"¿Eliminar:\n{item['pregunta_en_ingles']}?", parent=editor):
                lista.pop(sel[0])
                guardar_glosario_json(glosario_data)
                refrescar_lista()
                limpiar_form()

        frame_bots = tk.Frame(frame_form, bg=COLORES["fondo"])
        frame_bots.pack(fill="x", padx=8, pady=8)
        tk.Button(frame_bots, text="➕  Agregar / Actualizar", command=agregar,
                  bg=COLORES["boton"], fg="white", font=("Segoe UI", 9, "bold"),
                  relief="flat", padx=10, pady=6, cursor="hand2").pack(side="left", padx=(0, 6))
        tk.Button(frame_bots, text="🗑  Eliminar", command=eliminar,
                  bg=COLORES["panel"], fg=COLORES["rosa"], font=("Segoe UI", 9),
                  relief="flat", padx=10, pady=6, cursor="hand2").pack(side="left")
        tk.Button(frame_bots, text="🔄  Limpiar", command=limpiar_form,
                  bg=COLORES["panel"], fg=COLORES["texto2"], font=("Segoe UI", 9),
                  relief="flat", padx=10, pady=6, cursor="hand2").pack(side="left", padx=6)
        refrescar_lista()

    crear_pestaña("General", es_general=True)
    for semana in glosario_data["semanas"]:
        crear_pestaña(semana)

    frame_sem = tk.Frame(notebook, bg=COLORES["fondo"])
    notebook.add(frame_sem, text="⚙️ Semanas")

    tk.Label(frame_sem, text="Gestionar semanas de clase",
             bg=COLORES["fondo"], fg=COLORES["borde"],
             font=("Segoe UI", 11, "bold")).pack(pady=(20, 4))
    tk.Frame(frame_sem, bg=COLORES["panel"], height=1).pack(fill="x", padx=20, pady=12)

    frame_nueva = tk.Frame(frame_sem, bg=COLORES["fondo"])
    frame_nueva.pack(pady=6)
    tk.Label(frame_nueva, text="Nueva semana:", bg=COLORES["fondo"],
             fg=COLORES["texto2"], font=("Segoe UI", 9)).pack(side="left", padx=6)
    e_nueva_sem = tk.Entry(frame_nueva, bg=COLORES["fondo2"], fg=COLORES["texto"],
                           font=("Segoe UI", 9), relief="flat", bd=4, width=20,
                           insertbackground=COLORES["borde"])
    e_nueva_sem.pack(side="left", padx=6)
    e_nueva_sem.insert(0, "Semana 1")

    frame_checks = tk.Frame(frame_sem, bg=COLORES["fondo"])
    frame_checks.pack(pady=8)
    checks_vars = {}

    def refrescar_semanas():
        for w in frame_checks.winfo_children():
            w.destroy()
        checks_vars.clear()
        for semana in glosario_data["semanas"]:
            var = tk.BooleanVar(value=(semana in glosario_data.get("semanas_activas", [])))
            checks_vars[semana] = var
            fila = tk.Frame(frame_checks, bg=COLORES["fondo"])
            fila.pack(anchor="w", pady=2)
            tk.Checkbutton(fila, text=semana, variable=var,
                           bg=COLORES["fondo"], fg=COLORES["cyan"],
                           selectcolor=COLORES["panel"],
                           activebackground=COLORES["fondo"],
                           font=("Segoe UI", 10), command=guardar_activas).pack(side="left")
            tk.Label(fila, text=f"  ({len(glosario_data['semanas'].get(semana, []))} preguntas)",
                     bg=COLORES["fondo"], fg=COLORES["texto2"],
                     font=("Segoe UI", 8)).pack(side="left")
        if not glosario_data["semanas"]:
            tk.Label(frame_checks, text="No hay semanas creadas aún.",
                     bg=COLORES["fondo"], fg=COLORES["texto2"],
                     font=("Segoe UI", 9)).pack()

    def guardar_activas():
        activas = [s for s, v in checks_vars.items() if v.get()]
        glosario_data["semanas_activas"] = activas
        guardar_glosario_json(glosario_data)
        actualizar_estado(f"✅  {len(obtener_preguntas_activas())} preguntas activas", COLORES["verde"])

    def crear_semana():
        nombre = e_nueva_sem.get().strip()
        if not nombre:
            return
        if nombre in glosario_data["semanas"]:
            messagebox.showinfo("Ya existe", f"'{nombre}' ya existe.", parent=editor)
            return
        glosario_data["semanas"][nombre] = []
        guardar_glosario_json(glosario_data)
        refrescar_semanas()
        crear_pestaña(nombre)
        messagebox.showinfo("✅", f"Semana '{nombre}' creada.", parent=editor)

    tk.Button(frame_nueva, text="➕ Crear", command=crear_semana,
              bg=COLORES["boton"], fg="white", font=("Segoe UI", 9),
              relief="flat", padx=10, pady=4, cursor="hand2").pack(side="left")

    tk.Label(frame_sem, text="Semanas activas:", bg=COLORES["fondo"],
             fg=COLORES["amarillo"], font=("Segoe UI", 9, "bold")).pack(pady=(12, 4))
    refrescar_semanas()

    tk.Frame(frame_sem, bg=COLORES["panel"], height=1).pack(fill="x", padx=20, pady=12)
    tk.Label(frame_sem, text="Importar JSON a una semana:",
             bg=COLORES["fondo"], fg=COLORES["texto2"],
             font=("Segoe UI", 8, "bold")).pack()

    frame_imp = tk.Frame(frame_sem, bg=COLORES["fondo"])
    frame_imp.pack(pady=6)
    tk.Label(frame_imp, text="Semana destino:", bg=COLORES["fondo"],
             fg=COLORES["texto2"], font=("Segoe UI", 8)).pack(side="left", padx=6)
    e_sem_imp = tk.Entry(frame_imp, bg=COLORES["fondo2"], fg=COLORES["texto"],
                         font=("Segoe UI", 9), relief="flat", bd=4, width=14,
                         insertbackground=COLORES["borde"])
    e_sem_imp.pack(side="left", padx=4)
    e_sem_imp.insert(0, "Semana 1")

    def importar_json():
        nombre = e_sem_imp.get().strip()
        if not nombre:
            return
        ruta = filedialog.askopenfilename(
            filetypes=[("JSON", "*.json")], title="Seleccionar JSON", parent=editor)
        if not ruta:
            return
        try:
            with open(ruta, "r", encoding="utf-8") as f:
                datos = json.load(f)
            if nombre not in glosario_data["semanas"]:
                glosario_data["semanas"][nombre] = []
            glosario_data["semanas"][nombre] += datos
            guardar_glosario_json(glosario_data)
            messagebox.showinfo("✅", f"{len(datos)} preguntas importadas a '{nombre}'.", parent=editor)
        except Exception as e:
            messagebox.showerror("Error", str(e), parent=editor)

    tk.Button(frame_imp, text="📂 Importar JSON", command=importar_json,
              bg=COLORES["panel"], fg=COLORES["amarillo"], font=("Segoe UI", 9),
              relief="flat", padx=10, pady=4, cursor="hand2").pack(side="left", padx=6)

# ══════════════════════════════════════════
#  EXPORTAR / LIMPIAR
# ══════════════════════════════════════════
def exportar_historial():
    if not historial:
        messagebox.showinfo("Sin datos", "No hay transcripciones aún.")
        return
    ruta = filedialog.asksaveasfilename(
        defaultextension=".txt", filetypes=[("Texto", "*.txt")], title="Guardar historial")
    if ruta:
        with open(ruta, "w", encoding="utf-8") as f:
            f.write("HISTORIAL — ADRIANA AI\n" + "=" * 50 + "\n\n")
            for item in historial:
                f.write(f"[{item['hora']}]\nEN: {item['en']}\nES: {item['es']}\n" + "-" * 40 + "\n\n")
        messagebox.showinfo("✅ Guardado", f"Historial exportado:\n{ruta}")

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
    try:
        img = Image.open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "icono.ico"))
        img = img.resize((64, 64))
        return img
    except:
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
    global ventana_principal, label_estado, label_punto, historial_widget, boton_grabar

    F = "Segoe UI"
    ventana_principal = tk.Tk()
    ventana_principal.title("Adriana AI — Traductor en Tiempo Real")
    ventana_principal.configure(bg=COLORES["fondo"])
    instalar_hover(ventana_principal)   # transición suave de color en todos los botones

    try:
        ventana_principal.iconbitmap(
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "icono.ico"))
    except:
        pass

    sw = ventana_principal.winfo_screenwidth()
    sh = ventana_principal.winfo_screenheight()
    ancho = min(660, sw - 20)
    alto  = min(720, sh - 60)
    ventana_principal.geometry(f"{ancho}x{alto}+{(sw-ancho)//2}+{(sh-alto)//2}")
    ventana_principal.minsize(480, 520)
    ventana_principal.resizable(True, True)

    def minimizar_a_tray():
        ventana_principal.withdraw()

    ventana_principal.protocol("WM_DELETE_WINDOW", minimizar_a_tray)

    def boton_sutil(parent, texto, cmd, fg=None):
        return tk.Button(parent, text=texto, command=cmd,
                         bg=COLORES["panel"], fg=fg or COLORES["texto2"],
                         font=(F, 9), relief="flat", bd=0, highlightthickness=0,
                         padx=12, pady=6, cursor="hand2",
                         activeforeground=fg or COLORES["texto2"])

    # ── BARRA SUPERIOR ──────────────────────
    barra = tk.Frame(ventana_principal, bg=COLORES["fondo"])
    barra.pack(fill="x", padx=20, pady=(16, 0))
    tk.Label(barra, text="Adriana", bg=COLORES["fondo"], fg=COLORES["texto"],
             font=(F, 18, "bold")).pack(side="left")
    tk.Label(barra, text="AI", bg=COLORES["fondo"], fg=COLORES["borde"],
             font=(F, 18, "bold")).pack(side="left", padx=(5, 0))

    acciones = tk.Frame(barra, bg=COLORES["fondo"])
    acciones.pack(side="right")
    boton_sutil(acciones, "Glosario", abrir_editor_glosario).pack(side="left")
    boton_sutil(acciones, "Configuración",
                lambda: abrir_configuracion(ventana_principal, _aplicar_config)
                ).pack(side="left", padx=6)
    boton_sutil(acciones, "—", minimizar_a_tray).pack(side="left")

    # ── TARJETA DE ESTADO ───────────────────
    tarjeta = tk.Frame(ventana_principal, bg=COLORES["panel"])
    tarjeta.pack(fill="x", padx=20, pady=(14, 0))

    fila_estado = tk.Frame(tarjeta, bg=COLORES["panel"])
    fila_estado.pack(fill="x", padx=16, pady=(12, 4))
    label_punto = tk.Label(fila_estado, text="●", bg=COLORES["panel"],
                           fg=COLORES["verde"], font=(F, 10))
    label_punto.pack(side="left")
    label_estado = tk.Label(fila_estado, text="Listo para grabar",
                            bg=COLORES["panel"], fg=COLORES["texto"],
                            font=(F, 10), anchor="w")
    label_estado.pack(side="left", padx=(8, 0), fill="x", expand=True)

    fila_chips = tk.Frame(tarjeta, bg=COLORES["panel"])
    fila_chips.pack(fill="x", padx=16, pady=(0, 12))

    def chip():
        l = tk.Label(fila_chips, bg=COLORES["panel"], fg=COLORES["texto2"], font=(F, 8))
        l.pack(side="left", padx=(0, 14))
        return l

    chip_sub  = chip()
    chip_emg  = chip()
    chip_preg = chip()

    def refrescar_info():
        cfg     = cargar_config()
        activas = glosario_data.get("semanas_activas", [])
        total   = len(obtener_preguntas_activas())
        chip_sub.config(text=("●" if cfg["subtitulos_activos"] else "○") + " Subtítulos",
                        fg=COLORES["verde"] if cfg["subtitulos_activos"] else COLORES["texto2"])
        chip_emg.config(text=("●" if cfg["emergente_activa"] else "○") + " Emergente",
                        fg=COLORES["verde"] if cfg["emergente_activa"] else COLORES["texto2"])
        sem = f" · {', '.join(activas)}" if activas else ""
        chip_preg.config(text=f"{total} preguntas{sem}")
        ventana_principal.after(2000, refrescar_info)
    refrescar_info()

    # ── BOTÓN PRINCIPAL ─────────────────────
    zona_boton = tk.Frame(ventana_principal, bg=COLORES["fondo"])
    zona_boton.pack(fill="x", pady=(22, 4))
    boton_grabar = tk.Button(
        zona_boton, text="●  Grabar", command=iniciar_proceso,
        bg=COLORES["boton"], fg="white", font=(F, 13, "bold"),
        relief="flat", bd=0, highlightthickness=0,
        padx=46, pady=12, cursor="hand2", activeforeground="white"
    )
    boton_grabar.pack()
    tk.Label(zona_boton, text="Ctrl + Espacio", bg=COLORES["fondo"],
             fg=COLORES["texto2"], font=(F, 8)).pack(pady=(6, 0))

    # ── TRANSCRIPCIÓN ───────────────────────
    zona_hist = tk.Frame(ventana_principal, bg=COLORES["fondo"])
    zona_hist.pack(fill="both", expand=True, padx=20, pady=(16, 0))

    cab = tk.Frame(zona_hist, bg=COLORES["fondo"])
    cab.pack(fill="x", pady=(0, 6))
    tk.Label(cab, text="TRANSCRIPCIÓN", bg=COLORES["fondo"], fg=COLORES["borde"],
             font=(F, 8, "bold")).pack(side="left")
    boton_sutil(cab, "Exportar", exportar_historial, COLORES["verde"]).pack(side="right")
    boton_sutil(cab, "Limpiar", limpiar_historial, COLORES["rosa"]).pack(side="right", padx=6)

    marco = tk.Frame(zona_hist, bg=COLORES["linea"])
    marco.pack(fill="both", expand=True)
    historial_widget = scrolledtext.ScrolledText(
        marco, bg=COLORES["fondo2"], fg=COLORES["texto"],
        font=("Consolas", 10), relief="flat", bd=0, highlightthickness=0,
        padx=14, pady=12, spacing1=2, spacing3=2,
        state="disabled", insertbackground=COLORES["borde"],
        selectbackground=COLORES["neon"], wrap="word"
    )
    historial_widget.pack(fill="both", expand=True, padx=1, pady=1)

    historial_widget.tag_config("hora",  foreground=COLORES["texto2"], font=(F, 8, "bold"))
    historial_widget.tag_config("en",    foreground=COLORES["texto"])
    historial_widget.tag_config("es",    foreground=COLORES["borde2"])
    historial_widget.tag_config("match", foreground=COLORES["amarillo"])
    historial_widget.tag_config("sep",   foreground=COLORES["linea"])

    # ── PIE ─────────────────────────────────
    info = getattr(_cfg, "INFO_DISPOSITIVO", "")
    tk.Label(ventana_principal,
             text=(info + "   ·   " if info else "") + "100% local",
             bg=COLORES["fondo"], fg=COLORES["texto2"],
             font=(F, 7)).pack(pady=(8, 10))

    return ventana_principal

# ══════════════════════════════════════════
#  ATAJO DE TECLADO
# ══════════════════════════════════════════
keyboard.add_hotkey("ctrl+space", iniciar_proceso, trigger_on_release=True)

def _antes_de_reiniciar():
    try:
        if tray_icon:
            tray_icon.stop()
    except Exception:
        pass
    try:
        keyboard.unhook_all()
    except Exception:
        pass
_cfg.ANTES_DE_REINICIAR = _antes_de_reiniciar

# ══════════════════════════════════════════
#  ARRANQUE
# ══════════════════════════════════════════
print("🎯 Iniciando Adriana AI...")
threading.Thread(target=iniciar_tray, daemon=True).start()
ventana = construir_ui()
print("⌨️  Ctrl+Space para grabar | Minimizar para ir al system tray")
ventana.mainloop()
