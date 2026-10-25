"""Productos electrónicos: garantía y depreciación."""

from __future__ import annotations

from decimal import Decimal

from models.exceptions import ValidationError
from models.product import (
    HUNDRED,
    Product,
    format_money,
    format_percentage,
    money,
    validate_percentage,
)


class ElectronicProduct(Product):
    """Producto electrónico con garantía y depreciación configurable.

    Regla de negocio (orden de aplicación):
      1. La depreciación se aplica UNA sola vez sobre el precio de lista y produce
         el "precio depreciado". El precio de lista guardado nunca se modifica,
         por eso llamar varias veces al cálculo no deprecia dos veces.
      2. Sobre el precio depreciado se aplica la mejor oferta individual
         (promoción, cupón o prémium), igual que en ``Product``.
      3. Esa oferta promocional no supera ``max_discount`` (30 % por defecto),
         medido sobre el precio depreciado. La depreciación no cuenta en el tope.

    Ejemplo: precio $1,000, depreciación 10 %, descuento 10 %
    -> depreciado $900 -> final $810 -> descuento total $190.
    """

    CATEGORY = "Electrónica"
    DEFAULT_MAX_DISCOUNT = Decimal("30")
    DEFAULT_DEPRECIATION = Decimal("10")
    MAX_DEPRECIATION = Decimal("90")
    MAX_WARRANTY_MONTHS = 120
    DISCOUNT_RULE = (
        "La depreciación se aplica una sola vez al precio de lista; luego se aplica la mejor "
        "oferta individual (descuento, cupón o beneficio prémium) al precio depreciado. "
        "Descuento promocional máximo: {max}%."
    )

    def __init__(
        self,
        name: str,
        price: object,
        stock: int,
        warranty_months: int = 12,
        depreciation_percentage: object = DEFAULT_DEPRECIATION,
        discount_percentage: object = 0,
        max_discount: object | None = None,
    ) -> None:
        super().__init__(name, price, stock, discount_percentage, max_discount)
        self.warranty_months = warranty_months
        self.depreciation_percentage = depreciation_percentage

    @property
    def warranty_months(self) -> int:
        """Meses de garantía (0 a 120)."""
        return self._warranty_months

    @warranty_months.setter
    def warranty_months(self, value: int) -> None:
        if isinstance(value, bool) or not isinstance(value, int):
            raise ValidationError("La garantía debe ser un número entero de meses.")
        if not 0 <= value <= self.MAX_WARRANTY_MONTHS:
            raise ValidationError(
                f"La garantía debe estar entre 0 y {self.MAX_WARRANTY_MONTHS} meses."
            )
        self._warranty_months = value

    @property
    def depreciation_percentage(self) -> Decimal:
        """Porcentaje de depreciación (0 a 90)."""
        return self._depreciation_percentage

    @depreciation_percentage.setter
    def depreciation_percentage(self, value: object) -> None:
        depreciation = validate_percentage(value, "Depreciación")
        if depreciation > self.MAX_DEPRECIATION:
            raise ValidationError(
                f"La depreciación no puede superar {format_percentage(self.MAX_DEPRECIATION)}%."
            )
        self._depreciation_percentage = depreciation

    def depreciated_price(self) -> Decimal:
        """Precio de lista menos la depreciación (se calcula, no se guarda)."""
        return money(self.price * (HUNDRED - self.depreciation_percentage) / HUNDRED)

    def description(self) -> str:
        """Sobrescritura: agrega garantía, depreciación y precio depreciado."""
        return (
            f"{super().description()} | Garantía: {self.warranty_months} meses "
            f"| Depreciación: {format_percentage(self.depreciation_percentage)}% "
            f"| Precio depreciado: {format_money(self.depreciated_price())}"
        )

    def calculate_discount(
        self,
        percentage: object | None = None,
        coupon: object | None = None,
        premium_customer: bool = False,
    ) -> Decimal:
        """Sobrescritura: depreciación + mejor oferta, devuelto como descuento total por unidad."""
        offers = self._collect_offers(percentage, coupon, premium_customer)
        depreciated = self.depreciated_price()
        promotional = self._apply_offers(depreciated, [max(offers)])
        return money(self.price - depreciated + promotional)
