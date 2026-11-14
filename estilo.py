"""Paleta y utilidades de estilo de Adriana AI.

Estilo minimalista: negros suaves + acento morado. Las animaciones son solo
una transición corta de color en los botones (5 pasos, ~80 ms), casi sin costo.
"""
import tkinter as tk

COLORES = {
    "fondo":        "#0a0a0f",   # negro de fondo
    "fondo2":       "#101017",   # superficies (transcripción)
    "panel":        "#17171f",   # tarjetas y botones
    "linea":        "#262633",   # divisores y bordes sutiles
    "borde":        "#8b5cf6",   # acento morado
    "borde2":       "#a78bfa",   # acento morado claro
    "neon":         "#7c3aed",   # morado intenso (selección)
    "texto":        "#ececf4",
    "texto2":       "#8e8ea3",
    "verde":        "#4ade80",
    "cyan":         "#7dd3fc",
    "rosa":         "#f472b6",
    "amarillo":     "#fbbf24",
    "boton":        "#7c3aed",
    "boton_hover":  "#8b5cf6",
    "grabando":     "#ef4444",
}

PASOS_ANIMACION = 5
INTERVALO_MS    = 16


def _a_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def mezclar(c1, c2, t):
    a, b = _a_rgb(c1), _a_rgb(c2)
    return "#%02x%02x%02x" % tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))


def aclarar(c, t=0.12):
    return mezclar(c, "#ffffff", t)


def oscurecer(c, t=0.18):
    return mezclar(c, "#000000", t)


def _color_valido(c):
    return isinstance(c, str) and c.startswith("#") and len(c) == 7


def _fijar(w, color):
    try:
        w.config(bg=color, activebackground=color)
        w._ultimo = color
    except tk.TclError:
        pass


def _cancelar(w):
    ident = getattr(w, "_anim", None)
    if ident:
        try:
            w.after_cancel(ident)
        except Exception:
            pass
    w._anim = None


def _transicion(w, destino):
    _cancelar(w)
    try:
        origen = w.cget("bg")
    except tk.TclError:
        return
    if not (_color_valido(origen) and _color_valido(destino)) or origen == destino:
        return

    def paso(i):
        try:
            if not w.winfo_exists():
                return
            _fijar(w, mezclar(origen, destino, i / PASOS_ANIMACION))
            if i < PASOS_ANIMACION:
                w._anim = w.after(INTERVALO_MS, paso, i + 1)
        except tk.TclError:
            pass

    paso(1)


def _sin_cambios_externos(w):
    """True si nadie más cambió el color del botón mientras lo animábamos."""
    try:
        return w.cget("bg") == getattr(w, "_ultimo", None)
    except tk.TclError:
        return False


def _al_entrar(e):
    w = e.widget
    try:
        if str(w.cget("state")) == "disabled" or not _color_valido(w.cget("bg")):
            return
        base = w.cget("bg")
        w._base = base
        w._ultimo = base
        w.config(activebackground=base, activeforeground=w.cget("fg"))
    except tk.TclError:
        return
    _transicion(w, aclarar(base))


def _al_salir(e):
    w = e.widget
    base = getattr(w, "_base", None)
    if base is None:
        return
    if _sin_cambios_externos(w):
        _transicion(w, base)
    w._base = None


def _al_presionar(e):
    w = e.widget
    base = getattr(w, "_base", None)
    if base and _sin_cambios_externos(w):
        _cancelar(w)
        _fijar(w, oscurecer(base))


def _al_soltar(e):
    w = e.widget
    base = getattr(w, "_base", None)
    if base and _sin_cambios_externos(w):
        _transicion(w, aclarar(base))


def instalar_hover(root):
    """Activa la transición suave de color en TODOS los tk.Button de la app."""
    root.bind_class("Button", "<Enter>", _al_entrar, add="+")
    root.bind_class("Button", "<Leave>", _al_salir, add="+")
    root.bind_class("Button", "<ButtonPress-1>", _al_presionar, add="+")
    root.bind_class("Button", "<ButtonRelease-1>", _al_soltar, add="+")
