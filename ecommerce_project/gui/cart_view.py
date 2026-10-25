"""Panel del carrito: tabla de líneas, controles de compra y resumen."""

from __future__ import annotations

import tkinter as tk
from decimal import Decimal
from collections.abc import Callable
from tkinter import ttk

from gui.theme import COLORS
from gui.tooltip import add_tooltip
from models import format_money
from services import CartSummary

CART_COLUMNS = (
    ("product", "Producto", 100, "w"),
    ("unit", "Precio unit.", 80, "e"),
    ("quantity", "Cant.", 42, "center"),
    ("discount", "Descuento", 75, "e"),
    ("total", "Total", 75, "e"),
)


class CartView(ttk.LabelFrame):
    """Interfaz del carrito. Delega todas las operaciones en los callbacks recibidos."""

    def __init__(
        self,
        master: tk.Misc,
        *,
        on_add: Callable[[], None],
        on_update_quantity: Callable[[], None],
        on_remove: Callable[[], None],
        on_apply_discount: Callable[[], None],
        on_apply_coupon: Callable[[], None],
        on_premium_toggle: Callable[[], None],
        on_checkout: Callable[[], None],
        on_clear: Callable[[], None],
    ) -> None:
        super().__init__(master, text="Carrito de compras", style="Card.TLabelframe")
        self.product_var = tk.StringVar()
        self.quantity_var = tk.StringVar(value="1")
        self.discount_var = tk.StringVar()
        self.coupon_var = tk.StringVar()
        self.premium_var = tk.BooleanVar(value=False)
        self._subtotal = tk.StringVar(value=format_money(Decimal(0)))
        self._discount_total = tk.StringVar(value=format_money(Decimal(0)))
        self._total = tk.StringVar(value=format_money(Decimal(0)))
        self._promotions = tk.StringVar()
        self._choices: dict[str, str] = {}  # etiqueta del combobox -> id del producto
        self._labels_by_name: dict[str, str] = {}  # nombre del producto -> etiqueta

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self._build_table()
        self._build_controls(on_add, on_update_quantity, on_remove, on_apply_discount,
                             on_apply_coupon, on_premium_toggle)
        self._build_summary(on_checkout, on_clear)

    # ------------------------------------------------------------------
    # Construcción
    # ------------------------------------------------------------------
    def _build_table(self) -> None:
        frame = ttk.Frame(self, style="Card.TFrame")
        frame.grid(row=0, column=0, sticky="nsew")
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)
        self.tree = ttk.Treeview(frame, columns=[c[0] for c in CART_COLUMNS], show="headings",
                                 selectmode="browse", height=5)
        for key, heading, width, anchor in CART_COLUMNS:
            self.tree.heading(key, text=heading, anchor=anchor)
            self.tree.column(key, width=width, minwidth=40, anchor=anchor, stretch=True)
        self.tree.tag_configure("odd", background=COLORS["row_alt"])
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.tree.bind("<<TreeviewSelect>>", self._cart_row_selected)
        add_tooltip(self.tree, "Haga clic en una línea para seleccionarla y luego use Actualizar o Quitar.")

    def _build_controls(self, on_add, on_update, on_remove, on_discount, on_coupon,
                        on_premium) -> None:
        panel = ttk.Frame(self, style="Card.TFrame")
        panel.grid(row=0, column=1, sticky="ns", padx=(10, 0))
        panel.columnconfigure(1, weight=1)

        ttk.Label(panel, text="Agregar artículos", style="Section.TLabel").grid(
            row=0, column=0, columnspan=3, sticky="w")
        ttk.Label(panel, text="Producto", style="Field.TLabel").grid(row=1, column=0, sticky="w",
                                                                    pady=3)
        self.product_box = ttk.Combobox(panel, textvariable=self.product_var, state="readonly",
                                        width=17)
        self.product_box.grid(row=1, column=1, columnspan=2, sticky="ew", pady=3)
        add_tooltip(self.product_box, "Producto a agregar. El número entre [ ] son las existencias restantes.")
        ttk.Label(panel, text="Cantidad", style="Field.TLabel").grid(row=2, column=0, sticky="w",
                                                                     pady=3)
        add_tooltip(ttk.Spinbox(panel, from_=1, to=9999, textvariable=self.quantity_var, width=8),
                    "Unidades a agregar, o la nueva cantidad para Actualizar.").grid(
            row=2, column=1, sticky="w", pady=3)

        actions = ttk.Frame(panel, style="Card.TFrame")
        actions.grid(row=3, column=0, columnspan=3, sticky="ew", pady=(4, 0))
        actions.columnconfigure((0, 1, 2), weight=1, uniform="cart")
        add_tooltip(ttk.Button(actions, text="Agregar", style="Primary.TButton",
                               command=on_add),
                    "Agrega al carrito el producto y la cantidad elegidos.").grid(
            row=0, column=0, sticky="ew", padx=(0, 3))
        add_tooltip(ttk.Button(actions, text="Actualizar", style="Secondary.TButton",
                               command=on_update),
                    "Cambia la línea seleccionada del carrito a la Cantidad indicada arriba.").grid(
            row=0, column=1, sticky="ew", padx=3)
        add_tooltip(ttk.Button(actions, text="Quitar", style="Danger.TButton",
                               command=on_remove),
                    "Quita la línea seleccionada del carrito.").grid(
            row=0, column=2, sticky="ew", padx=(3, 0))

        ttk.Separator(panel).grid(row=4, column=0, columnspan=3, sticky="ew", pady=10)
        ttk.Label(panel, text="Promociones", style="Section.TLabel").grid(
            row=5, column=0, columnspan=3, sticky="w")
        ttk.Label(panel, text="Descuento (%)", style="Field.TLabel").grid(
            row=6, column=0, sticky="w", pady=3)
        add_tooltip(ttk.Entry(panel, textvariable=self.discount_var, width=10),
                    "Descuento general del pedido (0-100). Cada producto usa el mayor entre este "
                    "y su propio descuento promocional.").grid(
            row=6, column=1, sticky="ew", pady=3, padx=(0, 6))
        ttk.Button(panel, text="Aplicar", style="Secondary.TButton",
                   command=on_discount).grid(row=6, column=2, sticky="ew", pady=3)
        ttk.Label(panel, text="Cupón (%)", style="Field.TLabel").grid(
            row=7, column=0, sticky="w", pady=3)
        add_tooltip(ttk.Entry(panel, textvariable=self.coupon_var, width=10),
                    "Porcentaje del cupón (1-100). Déjelo vacío y pulse Aplicar para "
                    "quitarlo.").grid(
            row=7, column=1, sticky="ew", pady=3, padx=(0, 6))
        ttk.Button(panel, text="Aplicar", style="Secondary.TButton",
                   command=on_coupon).grid(row=7, column=2, sticky="ew", pady=3)
        add_tooltip(ttk.Checkbutton(panel, text="Cliente prémium (+5% de beneficio)",
                                    variable=self.premium_var, style="Card.TCheckbutton",
                                    command=on_premium),
                    "Agrega un beneficio del 5%. Cómo se combina depende de la categoría "
                    "de cada producto (ver Ayuda).").grid(
            row=8, column=0, columnspan=3, sticky="w", pady=(6, 0))

    def _build_summary(self, on_checkout, on_clear) -> None:
        panel = ttk.Frame(self, style="Card.TFrame")
        panel.grid(row=0, column=2, sticky="nsew", padx=(10, 0))
        panel.columnconfigure(1, weight=1)
        ttk.Label(panel, text="Resumen del pedido", style="Section.TLabel").grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(0, 6))
        rows = (("Subtotal", self._subtotal, "SummaryValue.TLabel"),
                ("Descuento total", self._discount_total, "SummaryValue.TLabel"))
        for index, (label, variable, style) in enumerate(rows, start=1):
            ttk.Label(panel, text=label, style="SummaryKey.TLabel").grid(
                row=index, column=0, sticky="w", pady=3)
            ttk.Label(panel, textvariable=variable, style=style).grid(
                row=index, column=1, sticky="e", pady=3)
        ttk.Separator(panel).grid(row=3, column=0, columnspan=2, sticky="ew", pady=8)
        ttk.Label(panel, text="Total final", style="SummaryKey.TLabel").grid(
            row=4, column=0, sticky="w")
        ttk.Label(panel, textvariable=self._total, style="Total.TLabel").grid(
            row=4, column=1, sticky="e")
        ttk.Label(panel, textvariable=self._promotions, style="Muted.TLabel",
                  wraplength=200).grid(row=5, column=0, columnspan=2, sticky="w", pady=(6, 10))
        add_tooltip(ttk.Button(panel, text="Finalizar compra", style="Success.TButton",
                               command=on_checkout),
                    "Completa la compra simulada, muestra el recibo y actualiza "
                    "las existencias.").grid(row=6, column=0, columnspan=2, sticky="ew", pady=3)
        add_tooltip(ttk.Button(panel, text="Vaciar carrito", style="Danger.TButton",
                               command=on_clear),
                    "Quita todos los artículos y restablece las promociones.").grid(
            row=7, column=0, columnspan=2, sticky="ew", pady=3)

    # ------------------------------------------------------------------
    # Comportamiento
    # ------------------------------------------------------------------
    def _cart_row_selected(self, _event: tk.Event) -> None:
        item = self.selected_cart_item()
        if not item:
            return
        values = self.tree.item(item, "values")
        self.quantity_var.set(str(values[2]))
        label = self._labels_by_name.get(str(values[0]))
        if label:
            self.product_var.set(label)

    def set_product_choices(self, products: list[tuple[str, str, int]]) -> None:
        """Actualiza el combobox con tuplas (id, nombre, existencias)."""
        current_id = self.selected_product_id()
        self._choices = {f"{pid} · {name} [{stock}]": pid for pid, name, stock in products}
        self._labels_by_name = {name: f"{pid} · {name} [{stock}]"
                                for pid, name, stock in products}
        self.product_box.configure(values=list(self._choices))
        self.select_product(current_id)

    def select_product(self, product_id: str | None) -> None:
        for label, pid in self._choices.items():
            if pid == product_id:
                self.product_var.set(label)
                return
        self.product_var.set("")

    def selected_product_id(self) -> str | None:
        return self._choices.get(self.product_var.get())

    def selected_cart_item(self) -> str | None:
        selection = self.tree.selection()
        return selection[0] if selection else None

    def refresh(self, summary: CartSummary, promotions: str) -> None:
        """Dibuja las líneas del carrito y el resumen de la compra."""
        selected = self.selected_cart_item()
        self.tree.delete(*self.tree.get_children())
        for index, line in enumerate(summary.lines):
            self.tree.insert("", "end", iid=line.product.name, tags=("odd",) if index % 2 else (),
                             values=(line.product.name, format_money(line.unit_price),
                                     line.quantity, f"-{format_money(line.line_discount)}",
                                     format_money(line.line_total)))
        if selected and self.tree.exists(selected):
            self.tree.selection_set(selected)
        self._subtotal.set(format_money(summary.subtotal))
        self._discount_total.set(f"-{format_money(summary.total_discount)}")
        self._total.set(format_money(summary.total))
        items = f"{summary.total_units} unidad(es) en el carrito" if not summary.is_empty else "El carrito está vacío"
        self._promotions.set(f"{items}\n{promotions}")
