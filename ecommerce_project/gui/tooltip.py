"""Ayuda emergente (tooltip) que aparece al dejar el mouse sobre un widget."""

from __future__ import annotations

import tkinter as tk

from gui.theme import COLORS, FONTS

DELAY_MS = 500


class ToolTip:
    """Muestra un texto breve junto al widget tras ``DELAY_MS`` milisegundos."""

    def __init__(self, widget: tk.Widget, text: str) -> None:
        self.widget = widget
        self.text = text
        self._after_id: str | None = None
        self._window: tk.Toplevel | None = None
        widget.bind("<Enter>", self._schedule, add="+")
        widget.bind("<Leave>", self._hide, add="+")
        widget.bind("<ButtonPress>", self._hide, add="+")

    def _schedule(self, _event: tk.Event) -> None:
        self._cancel()
        self._after_id = self.widget.after(DELAY_MS, self._show)

    def _cancel(self) -> None:
        if self._after_id:
            self.widget.after_cancel(self._after_id)
            self._after_id = None

    def _show(self) -> None:
        if self._window or not self.widget.winfo_viewable():
            return
        x = self.widget.winfo_rootx() + 12
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 4
        self._window = window = tk.Toplevel(self.widget)
        window.wm_overrideredirect(True)
        window.attributes("-topmost", True)
        tk.Label(window, text=self.text, justify="left", wraplength=300, padx=8, pady=5,
                 background=COLORS["navy"], foreground="white", font=FONTS["small"]).pack()
        # Evita que el tooltip se salga por el borde derecho o inferior de la pantalla.
        window.update_idletasks()
        x = min(x, window.winfo_screenwidth() - window.winfo_width() - 8)
        if y + window.winfo_height() > window.winfo_screenheight() - 40:
            y = self.widget.winfo_rooty() - window.winfo_height() - 4
        window.wm_geometry(f"+{x}+{y}")

    def _hide(self, _event: tk.Event | None = None) -> None:
        self._cancel()
        if self._window:
            self._window.destroy()
            self._window = None


def add_tooltip(widget: tk.Widget, text: str) -> tk.Widget:
    """Asocia un tooltip al widget y lo devuelve (permite encadenar con ``grid``)."""
    ToolTip(widget, text)
    return widget
