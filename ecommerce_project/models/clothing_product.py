"""Prendas de vestir: talla, color y descuentos acumulables."""

from __future__ import annotations

from decimal import Decimal

from models.exceptions import ValidationError
from models.product import Product

VALID_SIZES = ("XS", "S", "M", "L", "XL", "XXL")


class ClothingProduct(Product):
    """Prenda de vestir con descuentos acumulables.

    Regla de negocio: los descuentos se aplican uno después del otro sobre el
    precio que dejó el anterior (no se suman). Ejemplo obligatorio:
    $100 con 10 % y luego 20 % -> $100 * 0.90 * 0.80 = $72.
    El descuento acumulado no supera ``max_discount`` (40 % por defecto).
    """

    CATEGORY = "Ropa"
    DEFAULT_MAX_DISCOUNT = Decimal("40")
    DISCOUNT_RULE = (
        "Acumulable: el descuento, el cupón y el beneficio prémium se aplican uno tras otro "
        "(p. ej. $100 - 10% - 20% = $72). Descuento acumulado máximo: {max}%."
    )

    def __init__(
        self,
        name: str,
        price: object,
        stock: int,
        size: str,
        color: str,
        discount_percentage: object = 0,
        max_discount: object | None = None,
    ) -> None:
        super().__init__(name, price, stock, discount_percentage, max_discount)
        self.size = size
        self.color = color

    @property
    def size(self) -> str:
        """Talla (XS, S, M, L, XL o XXL)."""
        return self._size

    @size.setter
    def size(self, value: str) -> None:
        size = value.strip().upper() if isinstance(value, str) else ""
        if size not in VALID_SIZES:
            raise ValidationError(f"La talla debe ser una de: {', '.join(VALID_SIZES)}.")
        self._size = size

    @property
    def color(self) -> str:
        """Color de la prenda (no vacío)."""
        return self._color

    @color.setter
    def color(self, value: str) -> None:
        if not isinstance(value, str) or not value.strip():
            raise ValidationError("El color no puede estar vacío.")
        self._color = value.strip().capitalize()

    def description(self) -> str:
        """Sobrescritura: agrega talla y color."""
        return f"{super().description()} | Talla: {self.size} | Color: {self.color}"

    def calculate_discount(
        self,
        percentage: object | None = None,
        coupon: object | None = None,
        premium_customer: bool = False,
    ) -> Decimal:
        """Sobrescritura: todas las ofertas se acumulan de forma secuencial."""
        offers = self._collect_offers(percentage, coupon, premium_customer)
        return self._apply_offers(self.price, offers)
