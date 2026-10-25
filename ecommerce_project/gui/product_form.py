"""Formulario de registro de productos con campos dinámicos según la categoría."""

from __future__ import annotations

import tkinter as tk
from collections.abc import Callable
from datetime import date, timedelta
from tkinter import ttk

from models import (
    VALID_SIZES,
    ClothingProduct,
    ElectronicProduct,
    FoodProduct,
    Product,
    format_percentage,
)
from gui.tooltip import add_tooltip
from services import CATEGORIES

CATEGORY_HINTS = {
    "Electrónica": "La depreciación se aplica una sola vez, antes de cualquier promoción.",
    "Alimentos": "El descuento total tiene un tope de 15%. Formato: AAAA-MM-DD.",
    "Ropa": "Los descuentos se acumulan en secuencia (máx. 40%).",
}

FIELD_TIPS = {
    "Nombre del producto": "Nombre que se muestra en el inventario y el carrito. Debe ser único.",
    "Precio ($)": "Precio de lista antes de descuentos, p. ej. 1200 o 18.50.",
    "Existencias": "Unidades disponibles para la venta. El carrito no puede superar esta cantidad.",
    "Descuento promocional (%)": "Promoción propia del producto (0-100). Use 0 si no tiene promoción.",
    "Categoría del producto": "Cada categoría tiene campos adicionales y su propia regla de descuento.",
    "Garantía (meses)": "Duración de la garantía, de 0 a 120 meses.",
    "Depreciación (%)": "Pérdida de valor aplicada al precio de lista antes de cualquier promoción.",
    "Fecha de vencimiento": "Formato AAAA-MM-DD, p. ej. 2026-12-31. No puede ser una fecha pasada.",
    "Talla": "Talla de la prenda: XS, S, M, L, XL o XXL.",
    "Color": "Color de la prenda, p. ej. Azul.",
}

BUTTON_TIPS = {
    "Agregar producto": "Registra los datos del formulario como un producto nuevo.",
    "Actualizar producto": "Guarda los cambios del producto seleccionado en el inventario.",
    "Eliminar producto": "Elimina el producto seleccionado (pide confirmación).",
    "Limpiar formulario": "Vacía el formulario para registrar un producto nuevo.",
    "Ver detalles": "Muestra el desglose de precios y la regla de descuento del producto seleccionado.",
}


class ProductForm(ttk.LabelFrame):
    """Panel izquierdo: captura los datos del producto. No contiene lógica de negocio."""

    def __init__(
        self,
        master: tk.Misc,
        *,
        on_add: Callable[[], None],
        on_update: Callable[[], None],
        on_delete: Callable[[], None],
        on_details: Callable[[], None],
        on_clear: Callable[[], None],
    ) -> None:
        super().__init__(master, text="Registro de productos", style="Card.TLabelframe")
        self._on_clear = on_clear
        self.selected_id: str | None = None
        self.vars = {key: tk.StringVar() for key in (
            "name", "price", "stock", "discount", "category",
            "warranty", "depreciation", "expiration", "size", "color")}
        self._id_text = tk.StringVar()
        self._hint_text = tk.StringVar()
        self._category_frames: dict[str, ttk.Frame] = {}

        self.columnconfigure(1, weight=1)
        self._build_common_fields()
        self._build_category_fields()
        self._build_buttons(on_add, on_update, on_delete, on_details)
        self.vars["category"].trace_add("write", lambda *_: self._show_category_fields())
        self.clear()

    # ------------------------------------------------------------------
    # Construcción
    # ------------------------------------------------------------------
    @staticmethod
    def _field(parent: tk.Misc, row: int, label: str, widget: tk.Widget) -> None:
        ttk.Label(parent, text=label, style="Field.TLabel").grid(
            row=row, column=0, sticky="w", padx=(0, 10), pady=4)
        widget.grid(row=row, column=1, sticky="ew", pady=4)
        if label in FIELD_TIPS:
            add_tooltip(widget, FIELD_TIPS[label])

    def _build_common_fields(self) -> None:
        ttk.Label(self, textvariable=self._id_text, style="Muted.TLabel").grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(0, 6))
        self._name_entry = ttk.Entry(self, textvariable=self.vars["name"])
        self._field(self, 1, "Nombre del producto", self._name_entry)
        self._field(self, 2, "Precio ($)", ttk.Entry(self, textvariable=self.vars["price"]))
        self._field(self, 3, "Existencias", ttk.Spinbox(self, from_=0, to=100000,
                                                  textvariable=self.vars["stock"]))
        self._field(self, 4, "Descuento promocional (%)",
                    ttk.Entry(self, textvariable=self.vars["discount"]))
        self._field(self, 5, "Categoría del producto", ttk.Combobox(
            self, textvariable=self.vars["category"], values=CATEGORIES, state="readonly"))
        ttk.Separator(self).grid(row=6, column=0, columnspan=2, sticky="ew", pady=10)

    def _build_category_fields(self) -> None:
        container = ttk.Frame(self, style="Card.TFrame")
        container.grid(row=7, column=0, columnspan=2, sticky="ew")
        container.columnconfigure(0, weight=1)

        def make_frame(category: str) -> ttk.Frame:
            frame = ttk.Frame(container, style="Card.TFrame")
            frame.grid(row=0, column=0, sticky="ew")
            frame.columnconfigure(1, weight=1)
            ttk.Label(frame, text=f"Detalles de {category}", style="Section.TLabel").grid(
                row=0, column=0, columnspan=2, sticky="w", pady=(0, 4))
            self._category_frames[category] = frame
            return frame

        electronics = make_frame("Electrónica")
        self._field(electronics, 1, "Garantía (meses)", ttk.Spinbox(
            electronics, from_=0, to=120, textvariable=self.vars["warranty"]))
        self._field(electronics, 2, "Depreciación (%)",
                    ttk.Entry(electronics, textvariable=self.vars["depreciation"]))

        food = make_frame("Alimentos")
        self._field(food, 1, "Fecha de vencimiento",
                    ttk.Entry(food, textvariable=self.vars["expiration"]))

        clothing = make_frame("Ropa")
        self._field(clothing, 1, "Talla", ttk.Combobox(
            clothing, textvariable=self.vars["size"], values=VALID_SIZES, state="readonly"))
        self._field(clothing, 2, "Color", ttk.Entry(clothing, textvariable=self.vars["color"]))

        ttk.Label(self, textvariable=self._hint_text, style="Muted.TLabel", wraplength=280).grid(
            row=8, column=0, columnspan=2, sticky="w", pady=(6, 0))

    def _build_buttons(self, on_add, on_update, on_delete, on_details) -> None:
        buttons = ttk.Frame(self, style="Card.TFrame")
        buttons.grid(row=9, column=0, columnspan=2, sticky="ew", pady=(14, 0))
        buttons.columnconfigure((0, 1), weight=1, uniform="buttons")
        specs = [
            ("Agregar producto", "Primary.TButton", on_add, 0, 0),
            ("Actualizar producto", "Secondary.TButton", on_update, 0, 1),
            ("Eliminar producto", "Danger.TButton", on_delete, 1, 0),
            ("Limpiar formulario", "Secondary.TButton", self._clear_clicked, 1, 1),
        ]
        for text, style, command, row, column in specs:
            add_tooltip(ttk.Button(buttons, text=text, style=style, command=command),
                        BUTTON_TIPS[text]).grid(row=row, column=column, sticky="ew", padx=3, pady=3)
        add_tooltip(ttk.Button(buttons, text="Ver detalles", style="Secondary.TButton",
                               command=on_details), BUTTON_TIPS["Ver detalles"]).grid(row=2, column=0, columnspan=2, sticky="ew",
                                            padx=3, pady=3)

    # ------------------------------------------------------------------
    # Comportamiento
    # ------------------------------------------------------------------
    def _show_category_fields(self) -> None:
        category = self.vars["category"].get()
        for name, frame in self._category_frames.items():
            if name == category:
                frame.grid()
            else:
                frame.grid_remove()
        self._hint_text.set(CATEGORY_HINTS.get(category, ""))

    def _clear_clicked(self) -> None:
        self.clear()
        self._on_clear()

    def get_values(self) -> dict[str, str]:
        """Valores del formulario como texto (la validación se hace en la capa de servicios)."""
        return {key: var.get().strip() for key, var in self.vars.items()}

    def clear(self) -> None:
        """Restablece el formulario con valores por defecto."""
        defaults = {
            "name": "", "price": "", "stock": "0", "discount": "0", "category": "Electrónica",
            "warranty": "12", "depreciation": "10",
            "expiration": (date.today() + timedelta(days=30)).isoformat(),
            "size": "M", "color": "",
        }
        for key, value in defaults.items():
            self.vars[key].set(value)
        self.selected_id = None
        self._id_text.set("Producto nuevo (el ID se generará automáticamente)")
        self._name_entry.focus_set()

    def load_product(self, product_id: str, product: Product) -> None:
        """Carga un producto del inventario en el formulario para editarlo."""
        self.selected_id = product_id
        self._id_text.set(f"Editando el producto {product_id}")
        self.vars["name"].set(product.name)
        self.vars["price"].set(f"{product.price:.2f}")
        self.vars["stock"].set(str(product.stock))
        self.vars["discount"].set(format_percentage(product.discount_percentage))
        if isinstance(product, ElectronicProduct):
            self.vars["warranty"].set(str(product.warranty_months))
            self.vars["depreciation"].set(format_percentage(product.depreciation_percentage))
        elif isinstance(product, FoodProduct):
            self.vars["expiration"].set(product.expiration_date.isoformat())
        elif isinstance(product, ClothingProduct):
            self.vars["size"].set(product.size)
            self.vars["color"].set(product.color)
        self.vars["category"].set(product.CATEGORY)
