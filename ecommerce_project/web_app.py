"""Versión web (Flask) del Gestor de Productos de Tienda Virtual.

Reutiliza sin cambios la lógica de ``models`` y ``services``: solo reemplaza la
interfaz de Tkinter por páginas HTML. Cada visitante recibe su propio
inventario y carrito (guardados en memoria del servidor e identificados por una
cookie), de modo que lo que haga una persona no afecta a las demás.

Uso local:
    pip install -r requirements.txt
    python web_app.py          # abre http://127.0.0.1:5000

En producción (Render) se ejecuta con: gunicorn web_app:app
"""

from __future__ import annotations

import os
import secrets
import threading
from collections import OrderedDict
from dataclasses import dataclass, field
from functools import wraps
from typing import Callable

from flask import Flask, flash, redirect, render_template, request, session, url_for

from models import (
    ClothingProduct,
    ECommerceError,
    ElectronicProduct,
    FoodProduct,
    Product,
    VALID_SIZES,
    format_money,
    format_percentage,
)
from models.product import ZERO
from services import (
    CATEGORIES,
    CartSummary,
    InventoryManager,
    ShoppingCart,
    create_product,
    load_sample_data,
    parse_int,
)
from services.product_factory import optional_percentage

MAX_SESSIONS = 300  # límite de visitantes simultáneos guardados en memoria

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY") or secrets.token_hex(32)
app.jinja_env.filters["money"] = format_money
app.jinja_env.filters["pct"] = format_percentage


@dataclass
class Store:
    """Estado de un visitante: su inventario, su carrito y el último recibo."""

    inventory: InventoryManager = field(default_factory=InventoryManager)
    cart: ShoppingCart = field(default_factory=ShoppingCart)
    receipt: CartSummary | None = None

    @classmethod
    def with_sample_data(cls) -> Store:
        store = cls()
        load_sample_data(store.inventory)
        return store


_stores: OrderedDict[str, Store] = OrderedDict()
_lock = threading.Lock()


def get_store() -> Store:
    """Devuelve la tienda del visitante actual (la crea si no existe)."""
    sid = session.get("sid")
    with _lock:
        if sid and sid in _stores:
            _stores.move_to_end(sid)
            return _stores[sid]
        sid = secrets.token_urlsafe(16)
        session["sid"] = sid
        _stores[sid] = Store.with_sample_data()
        while len(_stores) > MAX_SESSIONS:
            _stores.popitem(last=False)  # descarta al visitante más antiguo
        return _stores[sid]


def handles_errors(view: Callable) -> Callable:
    """Muestra los errores del dominio como mensajes en la página en vez de fallar."""

    @wraps(view)
    def wrapper(*args, **kwargs):
        try:
            return view(*args, **kwargs)
        except ECommerceError as exc:
            flash(str(exc), "error")
            if "category" in request.form:  # conserva lo escrito en el formulario de producto
                session["draft"] = form_values()
            return redirect(request.form.get("next") or url_for("index"))

    return wrapper


def form_values() -> dict[str, str]:
    """Lee los campos del formulario de producto con los nombres de ``create_product``."""
    keys = ("category", "name", "price", "stock", "discount", "warranty",
            "depreciation", "expiration", "size", "color")
    return {key: request.form.get(key, "") for key in keys}


def product_to_form(product: Product) -> dict[str, str]:
    """Convierte un producto en los valores que se muestran en el formulario."""
    values = {
        "category": product.CATEGORY,
        "name": product.name,
        "price": f"{product.price}",
        "stock": str(product.stock),
        "discount": format_percentage(product.discount_percentage),
    }
    if isinstance(product, ElectronicProduct):
        values["warranty"] = str(product.warranty_months)
        values["depreciation"] = format_percentage(product.depreciation_percentage)
    elif isinstance(product, FoodProduct):
        values["expiration"] = product.expiration_date.isoformat()
    elif isinstance(product, ClothingProduct):
        values["size"] = product.size
        values["color"] = product.color
    return values


def ensure_not_in_cart(store: Store, product_id: str, action: str) -> None:
    product = store.inventory.get_product(product_id)
    if store.cart.contains(product):
        raise ECommerceError(f"'{product.name}' está en el carrito de compras. "
                             f"Quítelo del carrito antes de {action}lo.")


# ----------------------------------------------------------------------
# Página principal
# ----------------------------------------------------------------------
@app.get("/")
def index():
    store = get_store()
    edit_id = request.args.get("edit", "").upper()
    view_id = request.args.get("view", "").upper()
    form = {"category": CATEGORIES[0]}
    details = None
    try:
        if edit_id:
            form = product_to_form(store.inventory.get_product(edit_id))
        if view_id:
            details = (view_id, store.inventory.get_product(view_id))
    except ECommerceError as exc:
        flash(str(exc), "error")
        edit_id = ""
    form = session.pop("draft", None) or form
    receipt, store.receipt = store.receipt, None
    return render_template(
        "index.html",
        products=store.inventory.list_products(),
        inventory_value=store.inventory.total_value(),
        summary=store.cart.get_cart_summary(),
        cart=store.cart,
        promotions=store.cart.describe_promotions(),
        categories=CATEGORIES,
        sizes=VALID_SIZES,
        form=form,
        edit_id=edit_id,
        details=details,
        receipt=receipt,
        zero=ZERO,
    )


# ----------------------------------------------------------------------
# Productos
# ----------------------------------------------------------------------
@app.post("/products")
@handles_errors
def add_product():
    store = get_store()
    product = create_product(**form_values())
    product_id = store.inventory.add_product(product)
    flash(f"Producto {product_id} '{product.name}' agregado correctamente.", "success")
    return redirect(url_for("index"))


@app.post("/products/<product_id>/update")
@handles_errors
def update_product(product_id: str):
    store = get_store()
    ensure_not_in_cart(store, product_id, "actualizar")
    store.inventory.update_product(product_id, create_product(**form_values()))
    flash(f"Producto {product_id} actualizado correctamente.", "success")
    return redirect(url_for("index"))


@app.post("/products/<product_id>/delete")
@handles_errors
def delete_product(product_id: str):
    store = get_store()
    ensure_not_in_cart(store, product_id, "eliminar")
    store.inventory.remove_product(product_id)
    flash(f"Producto {product_id} eliminado.", "success")
    return redirect(url_for("index"))


@app.post("/reset")
def reset_store():
    store = get_store()
    store.inventory = InventoryManager()
    load_sample_data(store.inventory)
    store.cart.clear()
    flash("Se restauraron los productos de ejemplo.", "success")
    return redirect(url_for("index"))


# ----------------------------------------------------------------------
# Carrito
# ----------------------------------------------------------------------
@app.post("/cart/add")
@handles_errors
def add_to_cart():
    store = get_store()
    product = store.inventory.get_product(request.form.get("product_id", ""))
    quantity = parse_int(request.form.get("quantity", ""), "Cantidad")
    store.cart.add_product(product, quantity)
    flash(f"Se agregaron {quantity} x '{product.name}' al carrito.", "success")
    return redirect(url_for("index") + "#carrito")


@app.post("/cart/update")
@handles_errors
def update_cart_quantity():
    store = get_store()
    name = request.form.get("name", "")
    quantity = parse_int(request.form.get("quantity", ""), "Cantidad")
    store.cart.update_quantity(name, quantity)
    flash(f"Cantidad de '{name}' actualizada a {quantity}.", "success")
    return redirect(url_for("index") + "#carrito")


@app.post("/cart/remove")
@handles_errors
def remove_from_cart():
    store = get_store()
    name = request.form.get("name", "")
    store.cart.remove_product(name)
    flash(f"'{name}' se quitó del carrito.", "success")
    return redirect(url_for("index") + "#carrito")


@app.post("/cart/promotions")
@handles_errors
def apply_promotions():
    store = get_store()
    store.cart.apply_discount(optional_percentage(request.form.get("discount", "")))
    coupon = optional_percentage(request.form.get("coupon", ""), default="")
    store.cart.apply_coupon(coupon or None)
    store.cart.set_premium_customer(request.form.get("premium") == "on")
    flash(f"Promociones actualizadas: {store.cart.describe_promotions()}.", "success")
    return redirect(url_for("index") + "#carrito")


@app.post("/cart/clear")
def clear_cart():
    get_store().cart.clear()
    flash("Carrito vaciado.", "success")
    return redirect(url_for("index") + "#carrito")


@app.post("/checkout")
@handles_errors
def checkout():
    store = get_store()
    store.receipt = store.cart.checkout()
    flash(f"Compra completada. Total cobrado: {format_money(store.receipt.total)}. "
          "Inventario actualizado.", "success")
    return redirect(url_for("index") + "#carrito")


if __name__ == "__main__":
    app.run(debug=True)
