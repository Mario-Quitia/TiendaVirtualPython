"""Ventana principal: integra el formulario, el inventario y el carrito.

Esta clase actúa como controlador. Lee los datos de los paneles, llama a la
lógica de negocio (``InventoryManager``, ``ShoppingCart``, ``create_product``)
y muestra los resultados. Toda regla de descuento vive en ``models``.
"""

from __future__ import annotations

import tkinter as tk
from collections.abc import Callable
from functools import wraps
from tkinter import messagebox, ttk

from gui.cart_view import CartView
from gui.dialogs import show_text_dialog
from gui.help_guide import USER_GUIDE
from gui.inventory_view import InventoryView
from gui.product_form import ProductForm
from gui.theme import configure_styles
from gui.tooltip import add_tooltip
from models import ECommerceError, ElectronicProduct, format_money, format_percentage
from services import (
    InventoryManager,
    ShoppingCart,
    create_product,
    load_sample_data,
    parse_int,
)
from services.product_factory import optional_percentage

APP_TITLE = "Gestor de Productos de Tienda Virtual"


def handles_errors(title: str) -> Callable:
    """Decorador: convierte los errores de negocio en mensajes de error en español."""

    def decorator(method: Callable) -> Callable:
        @wraps(method)
        def wrapper(self: MainWindow, *args, **kwargs):
            try:
                return method(self, *args, **kwargs)
            except ECommerceError as error:
                self.set_status(str(error), "error")
                messagebox.showerror(title, str(error), parent=self.root)
            return None

        return wrapper

    return decorator


class MainWindow:
    """Construye la interfaz y coordina las operaciones del usuario."""

    def __init__(self, root: tk.Tk, inventory: InventoryManager | None = None,
                 cart: ShoppingCart | None = None) -> None:
        self.root = root
        self.inventory = inventory if inventory is not None else InventoryManager()
        self.cart = cart if cart is not None else ShoppingCart()
        self._status = tk.StringVar()

        root.title(APP_TITLE)
        # Se adapta a pantallas pequeñas (por ejemplo 1366x768).
        width = min(1360, root.winfo_screenwidth() - 40)
        height = min(800, root.winfo_screenheight() - 90)
        root.geometry(f"{width}x{height}+10+10")
        root.minsize(1100, 640)
        root.report_callback_exception = self._unexpected_error
        configure_styles(root)
        self._build_layout()
        self.refresh_all()
        self.set_status("Listo. Registre productos o seleccione uno del inventario. "
                        "Pulse F1 para ver la ayuda.")

    # ------------------------------------------------------------------
    # Diseño
    # ------------------------------------------------------------------
    def _build_layout(self) -> None:
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=1)

        header = ttk.Frame(self.root, style="Header.TFrame", padding=(20, 12))
        header.grid(row=0, column=0, sticky="ew")
        ttk.Label(header, text=APP_TITLE, style="HeaderTitle.TLabel").pack(side="left")
        ttk.Label(header, text="Inventario · Descuentos por categoría · Carrito de compras",
                  style="HeaderSub.TLabel").pack(side="left", padx=(16, 0), pady=(6, 0))
        add_tooltip(ttk.Button(header, text="?  Ayuda (F1)", style="Secondary.TButton",
                               command=self.show_help),
                    "Guía paso a paso: productos, carrito, promociones y pago."
                    ).pack(side="right")
        self.root.bind("<F1>", lambda _event: self.show_help())

        body = ttk.Frame(self.root, padding=12)
        body.grid(row=1, column=0, sticky="nsew")
        body.columnconfigure(1, weight=1)
        body.rowconfigure(0, weight=1)

        self.form = ProductForm(
            body,
            on_add=self.add_product,
            on_update=self.update_product,
            on_delete=self.delete_product,
            on_details=self.view_details,
            on_clear=self.clear_form,
        )
        self.form.grid(row=0, column=0, sticky="nsew", padx=(0, 12))

        right = ttk.Frame(body)
        right.grid(row=0, column=1, sticky="nsew")
        right.columnconfigure(0, weight=1)
        right.rowconfigure(0, weight=1)  # el inventario usa el espacio sobrante
        right.rowconfigure(1, weight=0)  # el carrito conserva su alto natural

        self.inventory_view = InventoryView(right, on_select=self.product_selected)
        self.inventory_view.grid(row=0, column=0, sticky="nsew", pady=(0, 12))
        self.cart_view = CartView(
            right,
            on_add=self.add_to_cart,
            on_update_quantity=self.update_cart_quantity,
            on_remove=self.remove_from_cart,
            on_apply_discount=self.apply_discount,
            on_apply_coupon=self.apply_coupon,
            on_premium_toggle=self.toggle_premium,
            on_checkout=self.checkout,
            on_clear=self.clear_cart,
        )
        self.cart_view.grid(row=1, column=0, sticky="nsew")

        status = ttk.Frame(self.root, style="Status.TFrame", padding=(16, 5))
        status.grid(row=2, column=0, sticky="ew")
        self._status_label = ttk.Label(status, textvariable=self._status, style="Status.info.TLabel")
        self._status_label.pack(side="left")

    # ------------------------------------------------------------------
    # Utilidades
    # ------------------------------------------------------------------
    def set_status(self, message: str, kind: str = "info") -> None:
        self._status.set(message)
        self._status_label.configure(style=f"Status.{kind}.TLabel")

    def show_help(self) -> None:
        show_text_dialog(self.root, "Guía de usuario", "Cómo usar el Gestor de Productos de Tienda Virtual",
                         USER_GUIDE)

    def _unexpected_error(self, exc_type, exc_value, _traceback) -> None:
        """Evita que un error inesperado cierre la aplicación."""
        self.set_status(f"Error inesperado: {exc_value}", "error")
        messagebox.showerror("Error inesperado",
                             f"Ocurrió un error inesperado:\n{exc_type.__name__}: {exc_value}",
                             parent=self.root)

    def refresh_all(self, select_id: str | None = None) -> None:
        products = self.inventory.list_products()
        self.inventory_view.refresh(products, format_money(self.inventory.total_value()), select_id)
        self.cart_view.set_product_choices([(pid, p.name, p.stock) for pid, p in products])
        self.refresh_cart()

    def refresh_cart(self) -> None:
        self.cart_view.refresh(self.cart.get_cart_summary(), self.cart.describe_promotions())

    def _require_selected_product(self) -> str:
        product_id = self.form.selected_id or self.inventory_view.selected_id()
        if not product_id:
            raise ECommerceError("Primero seleccione un producto de la tabla de inventario.")
        return product_id

    def _ensure_not_in_cart(self, product_id: str, action: str) -> None:
        product = self.inventory.get_product(product_id)
        if self.cart.contains(product):
            raise ECommerceError(f"'{product.name}' está en el carrito de compras. "
                                 f"Quítelo del carrito antes de {action}lo.")

    # ------------------------------------------------------------------
    # Productos
    # ------------------------------------------------------------------
    def product_selected(self, product_id: str) -> None:
        product = self.inventory.get_product(product_id)
        self.form.load_product(product_id, product)
        self.cart_view.select_product(product_id)
        self.set_status(f"Seleccionado {product_id}: {product.name}.")

    def clear_form(self) -> None:
        self.inventory_view.clear_selection()
        self.form.selected_id = None
        self.set_status("Formulario limpio. Listo para registrar un producto nuevo.")

    @handles_errors("Producto inválido")
    def add_product(self) -> None:
        product = create_product(**self.form.get_values())
        product_id = self.inventory.add_product(product)
        self.form.clear()
        self.refresh_all(select_id=product_id)
        self.set_status(f"Producto {product_id} '{product.name}' agregado correctamente.", "success")

    @handles_errors("Error al actualizar")
    def update_product(self) -> None:
        product_id = self._require_selected_product()
        self._ensure_not_in_cart(product_id, "actualizar")
        product = create_product(**self.form.get_values())
        self.inventory.update_product(product_id, product)
        self.refresh_all(select_id=product_id)
        self.set_status(f"Producto {product_id} actualizado correctamente.", "success")

    @handles_errors("Error al eliminar")
    def delete_product(self) -> None:
        product_id = self._require_selected_product()
        self._ensure_not_in_cart(product_id, "eliminar")
        product = self.inventory.get_product(product_id)
        if not messagebox.askyesno("Confirmar eliminación",
                                   f"¿Eliminar el producto {product_id} '{product.name}'?\n"
                                   "Esta acción no se puede deshacer.", parent=self.root):
            self.set_status("Eliminación cancelada.")
            return
        self.inventory.remove_product(product_id)
        self.form.clear()
        self.refresh_all()
        self.set_status(f"Producto {product_id} eliminado.", "success")

    @handles_errors("Detalles del producto")
    def view_details(self) -> None:
        product_id = self._require_selected_product()
        product = self.inventory.get_product(product_id)
        lines = [f"ID del producto: {product_id}", *product.description().split(" | "), "",
                 "Precios", "-------",
                 f"Precio de lista:       {format_money(product.price)}",
                 f"Descuento promocional: {format_percentage(product.discount_percentage)}%"]
        if isinstance(product, ElectronicProduct):
            lines.append(f"Precio depreciado:     {format_money(product.depreciated_price())}")
        lines += [f"Descuento unitario:    {format_money(product.calculate_discount())}",
                  f"Precio final:          {format_money(product.calculate_final_price())}",
                  "", "Regla de descuento", "------------------", product.discount_rule()]
        show_text_dialog(self.root, "Detalles del producto", f"{product.CATEGORY}: {product.name}",
                         "\n".join(lines))

    # ------------------------------------------------------------------
    # Carrito
    # ------------------------------------------------------------------
    def _cart_item_name(self) -> str:
        name = self.cart_view.selected_cart_item()
        if not name:
            raise ECommerceError("Primero seleccione un artículo del carrito.")
        return name

    @handles_errors("Error del carrito")
    def add_to_cart(self) -> None:
        product_id = self.cart_view.selected_product_id()
        if not product_id:
            raise ECommerceError("Seleccione un producto para agregar al carrito.")
        quantity = parse_int(self.cart_view.quantity_var.get(), "Cantidad")
        product = self.inventory.get_product(product_id)
        self.cart.add_product(product, quantity)
        self.refresh_cart()
        self.set_status(f"Se agregaron {quantity} x '{product.name}' al carrito.", "success")

    @handles_errors("Error del carrito")
    def update_cart_quantity(self) -> None:
        name = self._cart_item_name()
        quantity = parse_int(self.cart_view.quantity_var.get(), "Cantidad")
        self.cart.update_quantity(name, quantity)
        self.refresh_cart()
        self.set_status(f"Cantidad de '{name}' actualizada a {quantity}.", "success")

    @handles_errors("Error del carrito")
    def remove_from_cart(self) -> None:
        name = self._cart_item_name()
        self.cart.remove_product(name)
        self.refresh_cart()
        self.set_status(f"'{name}' se quitó del carrito.", "success")

    @handles_errors("Descuento inválido")
    def apply_discount(self) -> None:
        self.cart.apply_discount(optional_percentage(self.cart_view.discount_var.get()))
        self.refresh_cart()
        self.set_status(f"Descuento aplicado: {self.cart.describe_promotions()}.", "success")

    @handles_errors("Cupón inválido")
    def apply_coupon(self) -> None:
        text = optional_percentage(self.cart_view.coupon_var.get(), default="")
        self.cart.apply_coupon(text or None)
        self.refresh_cart()
        self.set_status("Cupón eliminado." if not text else "Cupón aplicado.", "success")

    @handles_errors("Error del carrito")
    def toggle_premium(self) -> None:
        enabled = bool(self.cart_view.premium_var.get())
        self.cart.set_premium_customer(enabled)
        self.refresh_cart()
        self.set_status(f"Beneficio de cliente prémium {'activado' if enabled else 'desactivado'}.")

    def _reset_promotion_fields(self) -> None:
        self.cart_view.discount_var.set("")
        self.cart_view.coupon_var.set("")
        self.cart_view.premium_var.set(False)

    @handles_errors("Error en el pago")
    def checkout(self) -> None:
        if self.cart.is_empty():
            raise ECommerceError("No se puede finalizar la compra: el carrito está vacío.")
        total = format_money(self.cart.calculate_total())
        if not messagebox.askyesno("Confirmar compra",
                                   f"¿Completar esta compra simulada por {total}?\n"
                                   "No se procesará ningún pago real.", parent=self.root):
            self.set_status("Compra cancelada.")
            return
        receipt = self.cart.checkout()
        self._reset_promotion_fields()
        self.refresh_all(select_id=self.inventory_view.selected_id())
        self.set_status(f"Compra completada. Total cobrado: {format_money(receipt.total)}. "
                        "Inventario actualizado.", "success")
        show_text_dialog(self.root, "Recibo de compra", "Compra completada con éxito",
                         receipt.as_text())

    def clear_cart(self) -> None:
        if self.cart.is_empty():
            self.set_status("El carrito ya está vacío.")
            return
        if messagebox.askyesno("Vaciar carrito", "¿Quitar todos los artículos del carrito?", parent=self.root):
            self.cart.clear()
            self._reset_promotion_fields()
            self.refresh_cart()
            self.set_status("Carrito vaciado.", "success")


def run_app(with_sample_data: bool = True) -> None:
    """Crea la ventana principal e inicia el ciclo de eventos de Tkinter."""
    root = tk.Tk()
    inventory = InventoryManager()
    if with_sample_data:
        load_sample_data(inventory)
    MainWindow(root, inventory)
    root.mainloop()
