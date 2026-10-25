"""Convierte los textos del formulario en objetos ``Product``.

Separa la interpretación de datos de la interfaz gráfica, de modo que la
validación pueda probarse sin abrir ventanas. Nunca usa ``eval()``.
"""

from __future__ import annotations

from models.clothing_product import ClothingProduct
from models.electronic_product import ElectronicProduct
from models.exceptions import ValidationError
from models.food_product import FoodProduct
from models.product import Product

CATEGORIES = ("Electrónica", "Alimentos", "Ropa")


def require(value: str, field_name: str) -> str:
    """Comprueba que un campo obligatorio no esté vacío."""
    text = (value or "").strip()
    if not text:
        raise ValidationError(f"{field_name} es obligatorio.")
    return text


def parse_int(value: str, field_name: str) -> int:
    """Convierte texto en entero con un mensaje claro si no es válido."""
    text = require(value, field_name)
    try:
        return int(text)
    except ValueError:
        raise ValidationError(f"{field_name} debe ser un número entero.") from None


def optional_percentage(value: str, default: str = "0") -> str:
    """Devuelve el porcentaje escrito o el valor por defecto si el campo está vacío."""
    text = (value or "").strip().rstrip("%").strip()
    return text or default


def create_product(
    category: str,
    name: str,
    price: str,
    stock: str,
    discount: str = "",
    warranty: str = "",
    depreciation: str = "",
    expiration: str = "",
    size: str = "",
    color: str = "",
) -> Product:
    """Crea la subclase correspondiente a ``category`` con los datos del formulario."""
    if category not in CATEGORIES:
        raise ValidationError("Seleccione una categoría de producto válida.")
    name = require(name, "Nombre del producto")
    price = require(price, "Precio").lstrip("$")
    stock_value = parse_int(stock, "Existencias")
    discount = optional_percentage(discount)

    if category == "Electrónica":
        return ElectronicProduct(
            name,
            price,
            stock_value,
            warranty_months=parse_int(warranty, "Garantía (meses)"),
            depreciation_percentage=optional_percentage(depreciation),
            discount_percentage=discount,
        )
    if category == "Alimentos":
        return FoodProduct(
            name, price, stock_value, require(expiration, "Fecha de vencimiento"),
            discount_percentage=discount,
        )
    return ClothingProduct(
        name, price, stock_value, require(size, "Talla"), require(color, "Color"),
        discount_percentage=discount,
    )
