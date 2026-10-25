"""Ventana modal reutilizable para mostrar detalles y recibos."""

import tkinter as tk
from tkinter import ttk

from gui.theme import COLORS, FONTS


def show_text_dialog(parent: tk.Misc, title: str, heading: str, body: str) -> tk.Toplevel:
    """Muestra un texto de solo lectura en una ventana modal con botón Cerrar."""
    dialog = tk.Toplevel(parent)
    dialog.title(title)
    dialog.configure(background=COLORS["card"])
    dialog.transient(parent.winfo_toplevel())
    dialog.minsize(520, 320)

    frame = ttk.Frame(dialog, style="Card.TFrame", padding=16)
    frame.pack(fill="both", expand=True)
    frame.columnconfigure(0, weight=1)
    frame.rowconfigure(1, weight=1)

    ttk.Label(frame, text=heading, style="Section.TLabel", font=FONTS["section"]).grid(
        row=0, column=0, sticky="w", pady=(0, 8))
    text = tk.Text(frame, wrap="word", font=FONTS["mono"], relief="flat", padx=10, pady=10,
                   background=COLORS["row_alt"], foreground=COLORS["text"],
                   width=78, height=min(max(body.count("\n") + 2, 8), 24))
    scrollbar = ttk.Scrollbar(frame, orient="vertical", command=text.yview)
    text.configure(yscrollcommand=scrollbar.set)
    text.insert("1.0", body)
    text.configure(state="disabled")
    text.grid(row=1, column=0, sticky="nsew")
    scrollbar.grid(row=1, column=1, sticky="ns")
    ttk.Button(frame, text="Cerrar", style="Primary.TButton", command=dialog.destroy).grid(
        row=2, column=0, columnspan=2, sticky="e", pady=(12, 0))

    dialog.bind("<Escape>", lambda _event: dialog.destroy())
    dialog.update_idletasks()
    dialog.grab_set()
    return dialog
