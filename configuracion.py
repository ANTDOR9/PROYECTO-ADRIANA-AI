import json
import os
import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import sys

# ══════════════════════════════════════════
#  ARCHIVO DE CONFIGURACIÓN
# ══════════════════════════════════════════
ARCHIVO_CONFIG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")

CONFIG_DEFAULT = {
    # Ventana emergente de preguntas
    "emergente_activa":     True,
    "emergente_tamano":     "mediano",
    "emergente_posicion":   "inferior_derecha",
    "emergente_opacidad":   0.95,

    # Subtítulos en tiempo real
    "subtitulos_activos":   True,
    "subtitulos_posicion":  "inferior_centro",
    "subtitulos_opacidad":  0.75,
    "subtitulos_tamano":    "mediano",

    # Rendimiento (requiere reiniciar): mixto | gpu | cpu
    "dispositivo":          "mixto",
}

from estilo import COLORES, instalar_hover

# ══════════════════════════════════════════
#  CARGAR / GUARDAR CONFIG
# ══════════════════════════════════════════
def cargar_config():
    if os.path.exists(ARCHIVO_CONFIG):
        try:
            with open(ARCHIVO_CONFIG, "r", encoding="utf-8") as f:
                data = json.load(f)
            for k, v in CONFIG_DEFAULT.items():
                if k not in data:
                    data[k] = v
            return data
        except:
            pass
    return CONFIG_DEFAULT.copy()

# Los rellena adriana_ui.py
INFO_DISPOSITIVO   = ""
ANTES_DE_REINICIAR = None

def reiniciar_aplicacion():
    """Abre una instancia nueva de la app y cierra la actual."""
    try:
        if ANTES_DE_REINICIAR:
            ANTES_DE_REINICIAR()
    except Exception:
        pass
    carpeta = os.path.dirname(os.path.abspath(__file__))
    script  = os.path.join(carpeta, "adriana_ui.py")
    flags   = getattr(subprocess, "CREATE_NEW_CONSOLE", 0)
    subprocess.Popen([sys.executable, script], cwd=carpeta, creationflags=flags)
    os._exit(0)

def guardar_config(data):
    with open(ARCHIVO_CONFIG, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ══════════════════════════════════════════
#  TAMAÑOS
# ══════════════════════════════════════════
TAMANOS_EMERGENTE = {
    "pequeño":  (380, 220),
    "mediano":  (500, 320),
    "grande":   (620, 420),
}

TAMANOS_SUBTITULOS = {
    "pequeño":  (700,  70),
    "mediano":  (900,  90),
    "grande":   (1100, 110),
}

def calcular_geometria_emergente(config, sw, sh):
    ancho, alto = TAMANOS_EMERGENTE[config["emergente_tamano"]]
    ancho = min(ancho, sw - 20)
    alto  = min(alto,  sh - 60)
    pos   = config["emergente_posicion"]
    m     = 12
    if pos == "inferior_derecha":
        x, y = sw - ancho - m, sh - alto - 60
    elif pos == "superior_derecha":
        x, y = sw - ancho - m, m + 40
    elif pos == "superior_izquierda":
        x, y = m, m + 40
    elif pos == "centro":
        x, y = (sw - ancho) // 2, (sh - alto) // 2
    else:
        x, y = sw - ancho - m, sh - alto - 60
    return ancho, alto, x, y

def calcular_geometria_subtitulos(config, sw, sh):
    ancho, alto = TAMANOS_SUBTITULOS[config["subtitulos_tamano"]]
    ancho = min(ancho, sw - 20)
    pos   = config["subtitulos_posicion"]
    m     = 10
    if pos == "inferior_centro":
        x, y = (sw - ancho) // 2, sh - alto - 60
    elif pos == "inferior_izquierda":
        x, y = m, sh - alto - 60
    elif pos == "inferior_derecha":
        x, y = sw - ancho - m, sh - alto - 60
    elif pos == "superior_centro":
        x, y = (sw - ancho) // 2, m + 40
    else:
        x, y = (sw - ancho) // 2, sh - alto - 60
    return ancho, alto, x, y

# ══════════════════════════════════════════
#  VENTANA DE CONFIGURACIÓN
# ══════════════════════════════════════════
def abrir_configuracion(parent=None, callback_aplicar=None):
    config_actual  = cargar_config()
    config_backup  = config_actual.copy()

    ventana = tk.Toplevel(parent) if parent else tk.Tk()
    ventana.title("⚙️ Configuración — Adriana AI")
    ventana.configure(bg=COLORES["fondo"])
    ventana.geometry("780x680")
    ventana.resizable(False, True)
    ventana.attributes("-topmost", True)
    if parent:
        ventana.grab_set()

    # Variables
    var_emergente_activa   = tk.BooleanVar(value=config_actual["emergente_activa"])
    var_emergente_tamano   = tk.StringVar(value=config_actual["emergente_tamano"])
    var_emergente_posicion = tk.StringVar(value=config_actual["emergente_posicion"])
    var_emergente_opacidad = tk.DoubleVar(value=config_actual["emergente_opacidad"])

    var_subtitulos_activos  = tk.BooleanVar(value=config_actual["subtitulos_activos"])
    var_subtitulos_tamano   = tk.StringVar(value=config_actual["subtitulos_tamano"])
    var_subtitulos_posicion = tk.StringVar(value=config_actual["subtitulos_posicion"])
    var_subtitulos_opacidad = tk.DoubleVar(value=config_actual["subtitulos_opacidad"])
    var_dispositivo         = tk.StringVar(value=config_actual["dispositivo"])

    # ── HEADER ──────────────────────────────
    tk.Frame(ventana, bg=COLORES["panel"], pady=10).pack(fill="x")
    header = ventana.winfo_children()[-1]
    tk.Label(header, text="⚙️  Configuración — Adriana AI",
             bg=COLORES["panel"], fg=COLORES["borde"],
             font=("Segoe UI", 13, "bold")).pack(side="left", padx=16)

    # Scroll
    canvas = tk.Canvas(ventana, bg=COLORES["fondo"], highlightthickness=0)
    scrollbar = ttk.Scrollbar(ventana, orient="vertical", command=canvas.yview)
    frame_scroll = tk.Frame(canvas, bg=COLORES["fondo"])
    frame_scroll.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.create_window((0, 0), window=frame_scroll, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)
    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    def seccion(texto):
        tk.Frame(frame_scroll, bg=COLORES["linea"], height=1).pack(fill="x", padx=16, pady=(14, 0))
        tk.Label(frame_scroll, text=texto,
                 bg=COLORES["fondo"], fg=COLORES["amarillo"],
                 font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=16, pady=(6, 4))

    def toggle_label(var, lbl):
        lbl.config(
            text="✅ Activado" if var.get() else "❌ Desactivado",
            fg=COLORES["verde"] if var.get() else COLORES["rosa"]
        )

    def slider_row(parent, var, lbl_ref):
        f = tk.Frame(parent, bg=COLORES["fondo"])
        f.pack(fill="x", padx=24, pady=4)
        tk.Label(f, text="Transparencia:", bg=COLORES["fondo"],
                 fg=COLORES["texto2"], font=("Segoe UI", 8)).pack(side="left")
        lbl = tk.Label(f, text=f"{int(var.get()*100)}%",
                       bg=COLORES["fondo"], fg=COLORES["verde"],
                       font=("Segoe UI", 9, "bold"), width=5)
        lbl.pack(side="right", padx=8)
        lbl_ref.append(lbl)
        style = ttk.Style()
        style.theme_use("default")
        style.configure("C.Horizontal.TScale", background=COLORES["fondo"],
                        troughcolor=COLORES["panel"])
        ttk.Scale(f, from_=0.3, to=1.0, variable=var, orient="horizontal",
                  length=240, style="C.Horizontal.TScale",
                  command=lambda v, l=lbl: l.config(text=f"{int(float(v)*100)}%")
                  ).pack(side="left", padx=8)

    def radio_row(parent, var, opciones):
        f = tk.Frame(parent, bg=COLORES["fondo"])
        f.pack(fill="x", padx=24)
        for valor, label in opciones:
            tk.Radiobutton(f, text=label, variable=var, value=valor,
                           bg=COLORES["fondo"], fg=COLORES["cyan"],
                           selectcolor=COLORES["panel"],
                           activebackground=COLORES["fondo"],
                           font=("Segoe UI", 9), cursor="hand2",
                           wraplength=440, justify="left").pack(anchor="w", pady=1)

    # ══ SECCIÓN: VENTANA EMERGENTE ══════════
    seccion("▸ Ventana emergente de preguntas")

    f_toggle1 = tk.Frame(frame_scroll, bg=COLORES["fondo"])
    f_toggle1.pack(fill="x", padx=24, pady=4)
    tk.Label(f_toggle1, text="Mostrar ventana al detectar pregunta:",
             bg=COLORES["fondo"], fg=COLORES["texto2"],
             font=("Segoe UI", 8)).pack(side="left")
    lbl_emergente = tk.Label(f_toggle1,
                              text="✅ Activado" if var_emergente_activa.get() else "❌ Desactivado",
                              bg=COLORES["fondo"],
                              fg=COLORES["verde"] if var_emergente_activa.get() else COLORES["rosa"],
                              font=("Segoe UI", 8, "bold"))
    lbl_emergente.pack(side="right")
    tk.Checkbutton(f_toggle1, variable=var_emergente_activa,
                   bg=COLORES["fondo"], selectcolor=COLORES["panel"],
                   activebackground=COLORES["fondo"],
                   command=lambda: toggle_label(var_emergente_activa, lbl_emergente),
                   cursor="hand2").pack(side="right")

    tk.Label(frame_scroll, text="Tamaño:", bg=COLORES["fondo"],
             fg=COLORES["texto2"], font=("Segoe UI", 8)).pack(anchor="w", padx=24)
    radio_row(frame_scroll, var_emergente_tamano, [
        ("pequeño", "🔹 Pequeño  (380×220)"),
        ("mediano", "🔷 Mediano  (500×320)"),
        ("grande",  "🔶 Grande   (620×420)"),
    ])

    tk.Label(frame_scroll, text="Posición:", bg=COLORES["fondo"],
             fg=COLORES["texto2"], font=("Segoe UI", 8)).pack(anchor="w", padx=24, pady=(8,0))
    radio_row(frame_scroll, var_emergente_posicion, [
        ("inferior_derecha",   "↘ Inferior derecha  (recomendado)"),
        ("superior_derecha",   "↗ Superior derecha"),
        ("superior_izquierda", "↖ Superior izquierda"),
        ("centro",             "⊙ Centro"),
    ])

    lbl_op1 = []
    slider_row(frame_scroll, var_emergente_opacidad, lbl_op1)

    # ══ SECCIÓN: SUBTÍTULOS ═════════════════
    seccion("▸ Subtítulos en tiempo real")

    f_toggle2 = tk.Frame(frame_scroll, bg=COLORES["fondo"])
    f_toggle2.pack(fill="x", padx=24, pady=4)
    tk.Label(f_toggle2, text="Mostrar subtítulos al grabar:",
             bg=COLORES["fondo"], fg=COLORES["texto2"],
             font=("Segoe UI", 8)).pack(side="left")
    lbl_subtitulos = tk.Label(f_toggle2,
                               text="✅ Activado" if var_subtitulos_activos.get() else "❌ Desactivado",
                               bg=COLORES["fondo"],
                               fg=COLORES["verde"] if var_subtitulos_activos.get() else COLORES["rosa"],
                               font=("Segoe UI", 8, "bold"))
    lbl_subtitulos.pack(side="right")
    tk.Checkbutton(f_toggle2, variable=var_subtitulos_activos,
                   bg=COLORES["fondo"], selectcolor=COLORES["panel"],
                   activebackground=COLORES["fondo"],
                   command=lambda: toggle_label(var_subtitulos_activos, lbl_subtitulos),
                   cursor="hand2").pack(side="right")

    tk.Label(frame_scroll, text="Tamaño:", bg=COLORES["fondo"],
             fg=COLORES["texto2"], font=("Segoe UI", 8)).pack(anchor="w", padx=24)
    radio_row(frame_scroll, var_subtitulos_tamano, [
        ("pequeño", "🔹 Pequeño  (700×70)"),
        ("mediano", "🔷 Mediano  (900×90)"),
        ("grande",  "🔶 Grande   (1100×110)"),
    ])

    tk.Label(frame_scroll, text="Posición:", bg=COLORES["fondo"],
             fg=COLORES["texto2"], font=("Segoe UI", 8)).pack(anchor="w", padx=24, pady=(8,0))
    radio_row(frame_scroll, var_subtitulos_posicion, [
        ("inferior_centro",    "⬇ Inferior centro  (recomendado)"),
        ("inferior_izquierda", "↙ Inferior izquierda"),
        ("inferior_derecha",   "↘ Inferior derecha"),
        ("superior_centro",    "⬆ Superior centro"),
    ])

    lbl_op2 = []
    slider_row(frame_scroll, var_subtitulos_opacidad, lbl_op2)

    # ══ SECCIÓN: RENDIMIENTO ════════════════
    seccion("▸ Rendimiento (requiere reiniciar)")
    if INFO_DISPOSITIVO:
        tk.Label(frame_scroll, text=f"En uso ahora: {INFO_DISPOSITIVO}",
                 bg=COLORES["fondo"], fg=COLORES["verde"],
                 font=("Segoe UI", 8)).pack(anchor="w", padx=24, pady=(0, 4))
    radio_row(frame_scroll, var_dispositivo, [
        ("mixto", "⚖ Mixto: Whisper en la gráfica, traducción en el procesador (recomendado)"),
        ("gpu",   "🎮 Solo gráfica: Whisper y traducción en la GPU (usa más memoria de video)"),
        ("cpu",   "🧠 Solo procesador: no usa la gráfica (más lento, deja la GPU libre)"),
    ])

    # ══ BOTONES ═════════════════════════════
    tk.Frame(frame_scroll, bg=COLORES["linea"], height=1).pack(fill="x", padx=16, pady=14)

    frame_bots = tk.Frame(frame_scroll, bg=COLORES["fondo"])
    frame_bots.pack(pady=8)

    def _guardar():
        config_actual["dispositivo"]         = var_dispositivo.get()
        config_actual["emergente_activa"]    = var_emergente_activa.get()
        config_actual["emergente_tamano"]    = var_emergente_tamano.get()
        config_actual["emergente_posicion"]  = var_emergente_posicion.get()
        config_actual["emergente_opacidad"]  = round(var_emergente_opacidad.get(), 2)
        config_actual["subtitulos_activos"]  = var_subtitulos_activos.get()
        config_actual["subtitulos_tamano"]   = var_subtitulos_tamano.get()
        config_actual["subtitulos_posicion"] = var_subtitulos_posicion.get()
        config_actual["subtitulos_opacidad"] = round(var_subtitulos_opacidad.get(), 2)
        guardar_config(config_actual)
        if callback_aplicar:
            callback_aplicar(config_actual)

    def guardar_y_cerrar():
        cambio = var_dispositivo.get() != config_backup["dispositivo"]
        _guardar()
        reiniciar = cambio and messagebox.askyesno(
            "Reiniciar",
            "Cambiaste el dispositivo de procesamiento.\n¿Reiniciar Adriana AI ahora para aplicarlo?",
            parent=ventana)
        ventana.destroy()
        if reiniciar:
            reiniciar_aplicacion()

    def guardar_y_reiniciar():
        _guardar()
        ventana.destroy()
        reiniciar_aplicacion()

    def revertir():
        var_emergente_activa.set(config_backup["emergente_activa"])
        var_emergente_tamano.set(config_backup["emergente_tamano"])
        var_emergente_posicion.set(config_backup["emergente_posicion"])
        var_emergente_opacidad.set(config_backup["emergente_opacidad"])
        var_subtitulos_activos.set(config_backup["subtitulos_activos"])
        var_subtitulos_tamano.set(config_backup["subtitulos_tamano"])
        var_subtitulos_posicion.set(config_backup["subtitulos_posicion"])
        var_subtitulos_opacidad.set(config_backup["subtitulos_opacidad"])
        var_dispositivo.set(config_backup["dispositivo"])
        toggle_label(var_emergente_activa, lbl_emergente)
        toggle_label(var_subtitulos_activos, lbl_subtitulos)

    tk.Button(frame_bots, text="💾  Guardar cambios",
              command=guardar_y_cerrar,
              bg=COLORES["boton"], fg="white",
              font=("Segoe UI", 10, "bold"), relief="flat",
              padx=16, pady=8, cursor="hand2").pack(side="left", padx=6)

    tk.Button(frame_bots, text="🔄  Guardar y reiniciar",
              command=guardar_y_reiniciar,
              bg=COLORES["borde2"], fg="white",
              font=("Segoe UI", 10, "bold"), relief="flat",
              padx=16, pady=8, cursor="hand2").pack(side="left", padx=6)

    tk.Button(frame_bots, text="↩  Revertir",
              command=revertir,
              bg=COLORES["panel"], fg=COLORES["amarillo"],
              font=("Segoe UI", 10), relief="flat",
              padx=16, pady=8, cursor="hand2").pack(side="left", padx=6)

    tk.Button(frame_bots, text="✕  Cancelar",
              command=ventana.destroy,
              bg=COLORES["panel"], fg=COLORES["rosa"],
              font=("Segoe UI", 10), relief="flat",
              padx=16, pady=8, cursor="hand2").pack(side="left", padx=6)

    tk.Frame(frame_scroll, bg=COLORES["fondo"], height=20).pack()

    if not parent:
        ventana.mainloop()

if __name__ == "__main__":
    _r = tk.Tk(); _r.withdraw(); instalar_hover(_r)
    abrir_configuracion(_r)
    _r.mainloop()