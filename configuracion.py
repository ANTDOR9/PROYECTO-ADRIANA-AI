import json
import os
import tkinter as tk
from tkinter import ttk

# ══════════════════════════════════════════
#  ARCHIVO DE CONFIGURACIÓN
# ══════════════════════════════════════════
ARCHIVO_CONFIG = os.path.join(os.path.dirname(__file__), "config.json")

CONFIG_DEFAULT = {
    "emergente_activa":     True,
    "emergente_tamano":     "mediano",   # pequeño, mediano, grande
    "emergente_posicion":   "inferior_derecha",  # inferior_derecha, superior_derecha, superior_izquierda, centro
    "emergente_opacidad":   0.95,        # 0.5 a 1.0
}

COLORES = {
    "fondo":        "#0d0d1a",
    "fondo2":       "#13132b",
    "panel":        "#1a1a35",
    "borde":        "#6c63ff",
    "borde2":       "#9d4edd",
    "texto":        "#e0e0ff",
    "texto2":       "#a0a0cc",
    "verde":        "#00ff9d",
    "cyan":         "#00d4ff",
    "rosa":         "#ff6b9d",
    "amarillo":     "#ffd93d",
    "boton":        "#6c63ff",
    "boton_hover":  "#7c3aed",
}

# ══════════════════════════════════════════
#  CARGAR / GUARDAR CONFIG
# ══════════════════════════════════════════
def cargar_config():
    if os.path.exists(ARCHIVO_CONFIG):
        try:
            with open(ARCHIVO_CONFIG, "r", encoding="utf-8") as f:
                data = json.load(f)
            # Merge con defaults por si faltan claves nuevas
            for k, v in CONFIG_DEFAULT.items():
                if k not in data:
                    data[k] = v
            return data
        except:
            pass
    return CONFIG_DEFAULT.copy()

def guardar_config(data):
    with open(ARCHIVO_CONFIG, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ══════════════════════════════════════════
#  CALCULAR POSICIÓN DE VENTANA EMERGENTE
# ══════════════════════════════════════════
TAMANOS = {
    "pequeño":  (380, 220),
    "mediano":  (500, 320),
    "grande":   (620, 420),
}

def calcular_geometria(config, sw, sh):
    ancho, alto = TAMANOS[config["emergente_tamano"]]
    ancho = min(ancho, sw - 20)
    alto  = min(alto,  sh - 60)
    pos   = config["emergente_posicion"]
    margen = 12

    if pos == "inferior_derecha":
        x = sw - ancho - margen
        y = sh - alto - 60
    elif pos == "superior_derecha":
        x = sw - ancho - margen
        y = margen + 40
    elif pos == "superior_izquierda":
        x = margen
        y = margen + 40
    elif pos == "centro":
        x = (sw - ancho) // 2
        y = (sh - alto) // 2
    else:
        x = sw - ancho - margen
        y = sh - alto - 60

    return ancho, alto, x, y

# ══════════════════════════════════════════
#  VENTANA DE CONFIGURACIÓN
# ══════════════════════════════════════════
def abrir_configuracion(parent=None):
    config = cargar_config()

    ventana = tk.Toplevel(parent) if parent else tk.Tk()
    ventana.title("⚙️ Configuración — Adriana AI")
    ventana.configure(bg=COLORES["fondo"])
    ventana.geometry("480x480")
    ventana.resizable(False, False)
    ventana.attributes("-topmost", True)
    if parent:
        ventana.grab_set()

    # ── HEADER ──────────────────────────────
    header = tk.Frame(ventana, bg=COLORES["panel"], pady=10)
    header.pack(fill="x")
    tk.Label(header, text="⚙️  Configuración",
             bg=COLORES["panel"], fg=COLORES["borde"],
             font=("Consolas", 14, "bold")).pack(side="left", padx=16)

    # ── SECCIÓN: VENTANA EMERGENTE ───────────
    def seccion(texto):
        tk.Frame(ventana, bg=COLORES["borde"], height=1).pack(fill="x", padx=16, pady=(14, 0))
        tk.Label(ventana, text=texto,
                 bg=COLORES["fondo"], fg=COLORES["amarillo"],
                 font=("Consolas", 9, "bold")).pack(anchor="w", padx=16, pady=(4, 8))

    # 1 — ACTIVAR/DESACTIVAR EMERGENTE
    seccion("▸ Ventana emergente de ayuda")

    frame_toggle = tk.Frame(ventana, bg=COLORES["fondo"])
    frame_toggle.pack(fill="x", padx=24)

    var_activa = tk.BooleanVar(value=config["emergente_activa"])

    tk.Label(frame_toggle, text="Mostrar ventana emergente al detectar pregunta:",
             bg=COLORES["fondo"], fg=COLORES["texto2"],
             font=("Consolas", 8)).pack(side="left")

    def toggle_emergente():
        config["emergente_activa"] = var_activa.get()
        lbl_estado_toggle.config(
            text="✅ Activada" if var_activa.get() else "❌ Desactivada",
            fg=COLORES["verde"] if var_activa.get() else COLORES["rosa"]
        )

    cb = tk.Checkbutton(frame_toggle, variable=var_activa,
                        bg=COLORES["fondo"], activebackground=COLORES["fondo"],
                        selectcolor=COLORES["panel"], command=toggle_emergente,
                        cursor="hand2")
    cb.pack(side="left", padx=6)

    lbl_estado_toggle = tk.Label(frame_toggle,
                                  text="✅ Activada" if var_activa.get() else "❌ Desactivada",
                                  bg=COLORES["fondo"],
                                  fg=COLORES["verde"] if var_activa.get() else COLORES["rosa"],
                                  font=("Consolas", 8, "bold"))
    lbl_estado_toggle.pack(side="left")

    # 2 — TAMAÑO
    seccion("▸ Tamaño de la ventana emergente")

    frame_tam = tk.Frame(ventana, bg=COLORES["fondo"])
    frame_tam.pack(fill="x", padx=24)

    var_tamano = tk.StringVar(value=config["emergente_tamano"])

    for valor, label, desc in [
        ("pequeño",  "🔹 Pequeño",  "380 × 220 px"),
        ("mediano",  "🔷 Mediano",  "500 × 320 px"),
        ("grande",   "🔶 Grande",   "620 × 420 px"),
    ]:
        fila = tk.Frame(frame_tam, bg=COLORES["fondo"])
        fila.pack(anchor="w", pady=1)
        tk.Radiobutton(fila, text=label, variable=var_tamano, value=valor,
                       bg=COLORES["fondo"], fg=COLORES["cyan"],
                       selectcolor=COLORES["panel"],
                       activebackground=COLORES["fondo"],
                       font=("Consolas", 9), cursor="hand2").pack(side="left")
        tk.Label(fila, text=f"  {desc}",
                 bg=COLORES["fondo"], fg=COLORES["texto2"],
                 font=("Consolas", 7)).pack(side="left")

    # 3 — POSICIÓN
    seccion("▸ Posición de la ventana emergente")

    frame_pos = tk.Frame(ventana, bg=COLORES["fondo"])
    frame_pos.pack(fill="x", padx=24)

    var_posicion = tk.StringVar(value=config["emergente_posicion"])

    posiciones = [
        ("inferior_derecha",  "↘ Inferior derecha  (recomendado)"),
        ("superior_derecha",  "↗ Superior derecha"),
        ("superior_izquierda","↖ Superior izquierda"),
        ("centro",            "⊙ Centro de pantalla"),
    ]

    for valor, label in posiciones:
        tk.Radiobutton(frame_pos, text=label, variable=var_posicion, value=valor,
                       bg=COLORES["fondo"], fg=COLORES["cyan"],
                       selectcolor=COLORES["panel"],
                       activebackground=COLORES["fondo"],
                       font=("Consolas", 9), cursor="hand2").pack(anchor="w", pady=1)

    # 4 — TRANSPARENCIA
    seccion("▸ Transparencia de la ventana emergente")

    frame_op = tk.Frame(ventana, bg=COLORES["fondo"])
    frame_op.pack(fill="x", padx=24)

    tk.Label(frame_op, text="Opacidad:",
             bg=COLORES["fondo"], fg=COLORES["texto2"],
             font=("Consolas", 8)).pack(side="left")

    lbl_opacidad = tk.Label(frame_op,
                             text=f"{int(config['emergente_opacidad']*100)}%",
                             bg=COLORES["fondo"], fg=COLORES["verde"],
                             font=("Consolas", 9, "bold"), width=5)
    lbl_opacidad.pack(side="right", padx=8)

    var_opacidad = tk.DoubleVar(value=config["emergente_opacidad"])

    style = ttk.Style()
    style.theme_use("default")
    style.configure("Custom.Horizontal.TScale",
                    background=COLORES["fondo"],
                    troughcolor=COLORES["panel"],
                    sliderthickness=16)

    slider = ttk.Scale(frame_op, from_=0.5, to=1.0,
                       variable=var_opacidad,
                       orient="horizontal", length=260,
                       style="Custom.Horizontal.TScale",
                       command=lambda v: lbl_opacidad.config(
                           text=f"{int(float(v)*100)}%"))
    slider.pack(side="left", padx=8)

    # ── BOTONES ──────────────────────────────
    tk.Frame(ventana, bg=COLORES["borde"], height=1).pack(fill="x", padx=16, pady=14)

    frame_bots = tk.Frame(ventana, bg=COLORES["fondo"])
    frame_bots.pack(pady=4)

    def guardar_y_cerrar():
        config["emergente_activa"]   = var_activa.get()
        config["emergente_tamano"]   = var_tamano.get()
        config["emergente_posicion"] = var_posicion.get()
        config["emergente_opacidad"] = round(var_opacidad.get(), 2)
        guardar_config(config)
        ventana.destroy()

    def cancelar():
        ventana.destroy()

    tk.Button(frame_bots, text="💾  Guardar",
              command=guardar_y_cerrar,
              bg=COLORES["boton"], fg="white",
              font=("Consolas", 10, "bold"), relief="flat",
              padx=20, pady=8, cursor="hand2").pack(side="left", padx=6)

    tk.Button(frame_bots, text="✕  Cancelar",
              command=cancelar,
              bg=COLORES["panel"], fg=COLORES["rosa"],
              font=("Consolas", 10), relief="flat",
              padx=20, pady=8, cursor="hand2").pack(side="left", padx=6)

    if not parent:
        ventana.mainloop()

if __name__ == "__main__":
    abrir_configuracion()