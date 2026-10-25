"""Productos alimenticios: fecha de vencimiento y descuento máximo."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from models.exceptions import ValidationError
from models.product import Product

DATE_FORMAT = "%Y-%m-%d"


class FoodProduct(Product):
    """Producto alimenticio con fecha de vencimiento.

    Regla de negocio: la promoción, el cupón y el beneficio prémium se acumulan
    de forma secuencial, pero el descuento total NUNCA supera ``max_discount``
    (15 % por defecto, configurable). El tope se aplica por igual a promociones
    y cupones. Un alimento vencido no puede venderse.
    """

    CATEGORY = "Alimentos"
    DEFAULT_MAX_DISCOUNT = Decimal("15")
    DISCOUNT_RULE = (
        "El descuento, el cupón y el beneficio prémium se combinan en secuencia, pero el "
        "descuento total nunca puede superar {max}%."
    )

    def __init__(
        self,
        name: str,
        price: object,
        stock: int,
        expiration_date: date | str,
        discount_percentage: object = 0,
        max_discount: object | None = None,
    ) -> None:
        super().__init__(name, price, stock, discount_percentage, max_discount)
        self.expiration_date = expiration_date

    @property
    def expiration_date(self) -> date:
        """Fecha de vencimiento validada con ``datetime``."""
        return self._expiration_date

    @expiration_date.setter
    def expiration_date(self, value: date | str) -> None:
        self._expiration_date = self.parse_date(value)
        if self._expiration_date < date.today():
            raise ValidationError("La fecha de vencimiento no puede ser una fecha pasada.")

    @staticmethod
    def parse_date(value: date | str) -> date:
        """Convierte ``YYYY-MM-DD`` (o un objeto ``date``) en ``date``."""
        if isinstance(value, datetime):
            return value.date()
        if isinstance(value, date):
            return value
        if isinstance(value, str) and value.strip():
            try:
                return datetime.strptime(value.strip(), DATE_FORMAT).date()
            except ValueError:
                pass
        raise ValidationError("La fecha de vencimiento debe ser una fecha válida con formato AAAA-MM-DD.")

    def is_expired(self, reference: date | None = None) -> bool:
        """``True`` si la fecha de vencimiento ya pasó."""
        return self._expiration_date < (reference or date.today())

    def is_sellable(self) -> bool:
        """Sobrescritura: un alimento vencido no se puede vender."""
        return not self.is_expired()

    def description(self) -> str:
        """Sobrescritura: agrega la fecha de vencimiento."""
        status = " (VENCIDO)" if self.is_expired() else ""
        return f"{super().description()} | Vence: {self.expiration_date.isoformat()}{status}"

    def calculate_discount(
        self,
        percentage: object | None = None,
        coupon: object | None = None,
        premium_customer: bool = False,
    ) -> Decimal:
        """Sobrescritura: ofertas acumuladas, limitadas a ``max_discount``."""
        offers = self._collect_offers(percentage, coupon, premium_customer)
        return self._apply_offers(self.price, offers)
