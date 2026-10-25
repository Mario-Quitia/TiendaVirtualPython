"""Lógica de negocio independiente de la interfaz gráfica."""

from services.inventory_manager import InventoryManager, load_sample_data
from services.product_factory import CATEGORIES, create_product, parse_int
from services.shopping_cart import CartLine, CartSummary, ShoppingCart

__all__ = [
    "CATEGORIES",
    "CartLine",
    "CartSummary",
    "InventoryManager",
    "ShoppingCart",
    "create_product",
    "load_sample_data",
    "parse_int",
]
