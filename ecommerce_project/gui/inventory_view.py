"""Tabla de inventario basada en ``ttk.Treeview``."""

from __future__ import annotations

import tkinter as tk
from collections.abc import Callable
from tkinter import ttk

from gui.theme import COLORS
from models import Product, format_money

COLUMNS = (
    # (id, encabezado, ancho, alineación)
    ("id", "ID producto", 90, "center"),
    ("name", "Nombre", 190, "w"),
    ("category", "Categoría", 100, "center"),
    ("price", "Precio", 95, "e"),
    ("stock", "Existencias", 80, "center"),
    ("discount", "Descuento", 130, "e"),
    ("final", "Precio final", 100, "e"),
)


class InventoryView(ttk.LabelFrame):
    """Muestra los productos registrados y notifica la selección."""

    def __init__(self, master: tk.Misc, on_select: Callable[[str], None]) -> None:
        super().__init__(master, text="Inventario", style="Card.TLabelframe")
        self._on_select = on_select
        self._summary = tk.StringVar()
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        self.tree = ttk.Treeview(self, columns=[c[0] for c in COLUMNS], show="headings",
                                 selectmode="browse", height=5)
        for key, heading, width, anchor in COLUMNS:
            self.tree.heading(key, text=heading, anchor=anchor)
            self.tree.column(key, width=width, minwidth=60, anchor=anchor, stretch=True)
        self.tree.tag_configure("odd", background=COLORS["row_alt"])
        self.tree.tag_configure("empty", foreground=COLORS["danger"])
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")
        ttk.Label(self, textvariable=self._summary, style="Muted.TLabel").grid(
            row=1, column=0, columnspan=2, sticky="w", pady=(8, 0))

        self.tree.bind("<<TreeviewSelect>>", self._selection_changed)

    def _selection_changed(self, _event: tk.Event) -> None:
        product_id = self.selected_id()
        if product_id:
            self._on_select(product_id)

    def refresh(self, products: list[tuple[str, Product]], inventory_value: str = "",
                select_id: str | None = None) -> None:
        """Vuelve a dibujar la tabla. Usa métodos polimórficos para descuentos y precios."""
        self.tree.delete(*self.tree.get_children())
        for index, (product_id, product) in enumerate(products):
            discount = product.calculate_discount()
            percent = discount / product.price * 100 if product.price else 0
            tags = ["odd"] if index % 2 else []
            if product.stock == 0:
                tags.append("empty")
            self.tree.insert("", "end", iid=product_id, tags=tags, values=(
                product_id, product.name, product.CATEGORY, format_money(product.price),
                product.stock, f"{format_money(discount)} ({percent:.1f}%)",
                format_money(product.calculate_final_price()),
            ))
        self._summary.set(f"{len(products)} productos registrados  ·  Valor del inventario a precio "
                          f"final: {inventory_value}  ·  Seleccione una fila para editar o ver detalles.")
        if select_id and self.tree.exists(select_id):
            self.tree.selection_set(select_id)
            self.tree.see(select_id)

    def selected_id(self) -> str | None:
        selection = self.tree.selection()
        return selection[0] if selection else None

    def clear_selection(self) -> None:
        self.tree.selection_remove(*self.tree.selection())
