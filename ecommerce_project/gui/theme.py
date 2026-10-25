"""Paleta de colores (azul oscuro, blanco y gris claro) y estilos ttk."""

import tkinter as tk
from tkinter import ttk

COLORS = {
    "navy": "#0B2545",
    "blue": "#134074",
    "blue_hover": "#1D5193",
    "accent": "#8DA9C4",
    "bg": "#EEF2F6",
    "card": "#FFFFFF",
    "border": "#D5DCE4",
    "text": "#1F2933",
    "muted": "#5F6B7A",
    "light": "#E4E9F0",
    "light_hover": "#D3DBE6",
    "danger": "#B42318",
    "danger_hover": "#8F1B13",
    "success": "#1E7B4F",
    "success_hover": "#17633F",
    "row_alt": "#F5F7FA",
    "select": "#CFE0F5",
}

FAMILY = "Segoe UI"
FONTS = {
    "title": (FAMILY, 18, "bold"),
    "subtitle": (FAMILY, 10),
    "section": (FAMILY, 11, "bold"),
    "body": (FAMILY, 10),
    "bold": (FAMILY, 10, "bold"),
    "small": (FAMILY, 9),
    "total": (FAMILY, 15, "bold"),
    "mono": ("Consolas", 10),
}


def _button(style: ttk.Style, name: str, bg: str, hover: str, fg: str = "white") -> None:
    style.configure(name, background=bg, foreground=fg, borderwidth=0, focusthickness=0,
                    padding=(9, 6), font=FONTS["bold"], anchor="center")
    style.map(name,
              background=[("disabled", "#A0AEC0"), ("pressed", hover), ("active", hover)],
              foreground=[("disabled", "#F1F5F9")])


def configure_styles(root: tk.Tk) -> None:
    """Configura todos los estilos de la aplicación sobre el tema ``clam``."""
    style = ttk.Style(root)
    style.theme_use("clam")
    root.configure(background=COLORS["bg"])
    root.option_add("*TCombobox*Listbox.font", FONTS["body"])

    style.configure(".", font=FONTS["body"], background=COLORS["bg"], foreground=COLORS["text"])
    style.configure("TFrame", background=COLORS["bg"])
    style.configure("Card.TFrame", background=COLORS["card"])
    style.configure("Card.TLabelframe", background=COLORS["card"], bordercolor=COLORS["border"],
                    relief="solid", borderwidth=1, padding=12)
    style.configure("Card.TLabelframe.Label", background=COLORS["card"],
                    foreground=COLORS["navy"], font=FONTS["section"])
    style.configure("Card.TLabel", background=COLORS["card"])
    style.configure("Field.TLabel", background=COLORS["card"], foreground=COLORS["text"])
    style.configure("Muted.TLabel", background=COLORS["card"], foreground=COLORS["muted"],
                    font=FONTS["small"])
    style.configure("Section.TLabel", background=COLORS["card"], foreground=COLORS["navy"],
                    font=FONTS["bold"])

    style.configure("Header.TFrame", background=COLORS["navy"])
    style.configure("HeaderTitle.TLabel", background=COLORS["navy"], foreground="white",
                    font=FONTS["title"])
    style.configure("HeaderSub.TLabel", background=COLORS["navy"], foreground=COLORS["accent"],
                    font=FONTS["subtitle"])

    style.configure("Status.TFrame", background=COLORS["light"])
    for kind, color in (("info", COLORS["muted"]), ("success", COLORS["success"]),
                        ("error", COLORS["danger"])):
        style.configure(f"Status.{kind}.TLabel", background=COLORS["light"], foreground=color,
                        font=FONTS["small"])

    style.configure("SummaryKey.TLabel", background=COLORS["card"], foreground=COLORS["muted"])
    style.configure("SummaryValue.TLabel", background=COLORS["card"], font=FONTS["bold"])
    style.configure("Total.TLabel", background=COLORS["card"], foreground=COLORS["navy"],
                    font=FONTS["total"])

    _button(style, "Primary.TButton", COLORS["blue"], COLORS["blue_hover"])
    _button(style, "Secondary.TButton", COLORS["light"], COLORS["light_hover"], COLORS["navy"])
    _button(style, "Danger.TButton", COLORS["danger"], COLORS["danger_hover"])
    _button(style, "Success.TButton", COLORS["success"], COLORS["success_hover"])

    style.configure("TEntry", fieldbackground="white", bordercolor=COLORS["border"],
                    lightcolor=COLORS["border"], padding=4)
    style.map("TEntry", bordercolor=[("focus", COLORS["blue"])])
    style.configure("TSpinbox", fieldbackground="white", bordercolor=COLORS["border"],
                    padding=3, arrowsize=12)
    style.configure("TCombobox", fieldbackground="white", bordercolor=COLORS["border"], padding=3)
    style.map("TCombobox", fieldbackground=[("readonly", "white")],
              selectbackground=[("readonly", "white")], selectforeground=[("readonly", COLORS["text"])])
    style.configure("Card.TCheckbutton", background=COLORS["card"])
    style.map("Card.TCheckbutton", background=[("active", COLORS["card"])])
    style.configure("Card.TSeparator", background=COLORS["border"])

    style.configure("Treeview", background="white", fieldbackground="white",
                    foreground=COLORS["text"], rowheight=26, bordercolor=COLORS["border"],
                    borderwidth=0)
    style.configure("Treeview.Heading", background=COLORS["navy"], foreground="white",
                    font=FONTS["bold"], relief="flat", padding=(4, 6))
    style.map("Treeview.Heading", background=[("active", COLORS["blue"])])
    style.map("Treeview", background=[("selected", COLORS["select"])],
              foreground=[("selected", COLORS["text"])])
