"""Inventario: registro de productos con identificadores únicos."""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

from models.clothing_product import ClothingProduct
from models.electronic_product import ElectronicProduct
from models.exceptions import DuplicateProductError, ProductNotFoundError, ValidationError
from models.food_product import FoodProduct
from models.product import ZERO, Product, money


class InventoryManager:
    """Almacena los productos por identificador (``P001``, ``P002``...).

    Garantiza identificadores y nombres únicos (sin distinguir mayúsculas).
    """

    def __init__(self, id_prefix: str = "P") -> None:
        self._products: dict[str, Product] = {}
        self._prefix = id_prefix
        self._next_number = 1

    @staticmethod
    def _normalize_id(product_id: str) -> str:
        if not isinstance(product_id, str) or not product_id.strip():
            raise ValidationError("El ID del producto no puede estar vacío.")
        return product_id.strip().upper()

    def generate_id(self) -> str:
        """Genera el siguiente identificador libre."""
        while True:
            candidate = f"{self._prefix}{self._next_number:03d}"
            self._next_number += 1
            if candidate not in self._products:
                return candidate

    def _check_unique_name(self, name: str, ignore_id: str | None = None) -> None:
        for product_id, product in self._products.items():
            if product_id != ignore_id and product.name.lower() == name.lower():
                raise DuplicateProductError(f"Ya existe un producto llamado '{name}' ({product_id}).")

    def add_product(self, product: Product, product_id: str | None = None) -> str:
        """Registra un producto y devuelve su identificador."""
        if not isinstance(product, Product):
            raise ValidationError("Solo se pueden agregar productos al inventario.")
        product_id = self.generate_id() if product_id is None else self._normalize_id(product_id)
        if product_id in self._products:
            raise DuplicateProductError(f"El ID de producto '{product_id}' ya existe.")
        self._check_unique_name(product.name)
        self._products[product_id] = product
        return product_id

    def update_product(self, product_id: str, product: Product) -> None:
        """Reemplaza el producto guardado con ese identificador (puede cambiar de categoría)."""
        product_id = self._normalize_id(product_id)
        self.get_product(product_id)
        if not isinstance(product, Product):
            raise ValidationError("Solo se pueden guardar productos en el inventario.")
        self._check_unique_name(product.name, ignore_id=product_id)
        self._products[product_id] = product

    def remove_product(self, product_id: str) -> Product:
        product_id = self._normalize_id(product_id)
        product = self.get_product(product_id)
        del self._products[product_id]
        return product

    def get_product(self, product_id: str) -> Product:
        product = self._products.get(self._normalize_id(product_id))
        if product is None:
            raise ProductNotFoundError(f"No se encontró el producto '{product_id}'.")
        return product

    def list_products(self) -> list[tuple[str, Product]]:
        return list(self._products.items())

    def total_value(self) -> Decimal:
        """Valor del inventario a precio final."""
        return money(
            sum((p.calculate_final_price() * p.stock for p in self._products.values()), ZERO)
        )

    def __len__(self) -> int:
        return len(self._products)


def load_sample_data(inventory: InventoryManager) -> None:
    """Carga productos de ejemplo para la demostración."""
    today = date.today()
    samples: list[Product] = [
        ElectronicProduct("Laptop Pro 14", "1200.00", 8, warranty_months=24, depreciation_percentage=10),
        ElectronicProduct("Audífonos inalámbricos", "150.00", 25, warranty_months=12,
                          depreciation_percentage=5, discount_percentage=10),
        ElectronicProduct("Teléfono inteligente X", "899.99", 12, warranty_months=12, depreciation_percentage=8),
        FoodProduct("Café orgánico 500g", "18.50", 40, today + timedelta(days=180)),
        FoodProduct("Paquete de yogur griego", "6.75", 30, today + timedelta(days=14), discount_percentage=10),
        FoodProduct("Barra de chocolate oscuro", "3.20", 60, today + timedelta(days=240)),
        ClothingProduct("Chaqueta de jean clásica", "100.00", 15, "M", "Azul", discount_percentage=10),
        ClothingProduct("Camiseta de algodón", "25.00", 50, "L", "Blanco"),
        ClothingProduct("Tenis para correr", "85.00", 20, "XL", "Negro", discount_percentage=15),
    ]
    for product in samples:
        inventory.add_product(product)
