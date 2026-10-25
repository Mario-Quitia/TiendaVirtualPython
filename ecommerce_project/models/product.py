"""Clase base ``Product`` y utilidades compartidas para cálculos monetarios.

Todas las operaciones con dinero usan ``decimal.Decimal`` y se redondean a dos
decimales con ``ROUND_HALF_UP`` para evitar los errores de redondeo de ``float``.

Simulación de sobrecarga
------------------------
Python no permite declarar varios métodos con el mismo nombre y distinta
cantidad de parámetros (como en Java). Por eso ``calculate_discount`` es un
único método con parámetros opcionales que admite las tres variantes pedidas:

    product.calculate_discount(10)              # descuento básico
    product.calculate_discount(10, 5)           # descuento + cupón
    product.calculate_discount(10, 5, True)     # descuento + cupón + cliente prémium

Orden de aplicación de las ofertas: 1) descuento promocional, 2) cupón,
3) beneficio prémium. Cada categoría decide si las ofertas se acumulan y cuál
es su tope máximo, pero ninguna puede producir un precio final negativo.
"""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

from models.exceptions import InsufficientStockError, ValidationError

CENT = Decimal("0.01")
HUNDRED = Decimal("100")
ZERO = Decimal("0")


def to_decimal(value: object, field_name: str = "Valor") -> Decimal:
    """Convierte ``value`` en ``Decimal`` o lanza ``ValidationError`` con un mensaje claro."""
    if value is None or isinstance(value, bool):
        raise ValidationError(f"{field_name} debe ser un número.")
    try:
        result = value if isinstance(value, Decimal) else Decimal(str(value).strip())
    except InvalidOperation:
        raise ValidationError(f"{field_name} debe ser un número válido.") from None
    if not result.is_finite():
        raise ValidationError(f"{field_name} debe ser un número finito.")
    return result


def money(value: Decimal) -> Decimal:
    """Redondea un valor monetario a dos decimales."""
    return value.quantize(CENT, rounding=ROUND_HALF_UP)


def format_money(value: Decimal) -> str:
    """Devuelve el valor con formato monetario coherente, por ejemplo ``$1,250.00``."""
    return f"${money(value):,.2f}"


def format_percentage(value: Decimal) -> str:
    """Muestra un porcentaje sin ceros innecesarios: ``Decimal('15.0')`` -> ``'15'``."""
    return f"{value.normalize():f}"


def validate_percentage(value: object, field_name: str = "Descuento") -> Decimal:
    """Valida que el porcentaje sea numérico y esté entre 0 y 100."""
    percentage = to_decimal(value, field_name)
    if percentage < ZERO or percentage > HUNDRED:
        raise ValidationError(f"{field_name} debe estar entre 0 y 100.")
    return percentage


def validate_quantity(value: object, field_name: str = "Cantidad") -> int:
    """Valida que la cantidad sea un entero mayor que cero."""
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValidationError(f"{field_name} debe ser un número entero.")
    if value <= 0:
        raise ValidationError(f"{field_name} debe ser mayor que cero.")
    return value


class Product:
    """Producto general de la tienda.

    Regla de descuento base (no acumulable): de las ofertas recibidas
    (descuento promocional, cupón y beneficio prémium) solo se aplica la mayor.
    El descuento nunca supera ``max_discount`` (50 % por defecto).
    """

    CATEGORY = "General"
    DEFAULT_MAX_DISCOUNT = Decimal("50")
    PREMIUM_BONUS = Decimal("5")
    DISCOUNT_RULE = (
        "No acumulable: solo se aplica la mejor oferta individual (descuento, cupón o "
        "beneficio prémium). Descuento máximo: {max}%."
    )

    def __init__(
        self,
        name: str,
        price: object,
        stock: int,
        discount_percentage: object = 0,
        max_discount: object | None = None,
    ) -> None:
        """Crea un producto validando nombre, precio, existencias y porcentajes."""
        self.name = name
        self.price = price
        self.stock = stock
        self.max_discount = self.DEFAULT_MAX_DISCOUNT if max_discount is None else max_discount
        self.discount_percentage = discount_percentage

    # ------------------------------------------------------------------
    # Encapsulamiento: propiedades con validación
    # ------------------------------------------------------------------
    @property
    def name(self) -> str:
        """Nombre del producto (no vacío)."""
        return self._name

    @name.setter
    def name(self, value: str) -> None:
        if not isinstance(value, str) or not value.strip():
            raise ValidationError("El nombre del producto no puede estar vacío.")
        if len(value.strip()) > 60:
            raise ValidationError("El nombre del producto no puede superar los 60 caracteres.")
        self._name = value.strip()

    @property
    def price(self) -> Decimal:
        """Precio unitario de lista, siempre con dos decimales."""
        return self._price

    @price.setter
    def price(self, value: object) -> None:
        price = to_decimal(value, "Precio")
        if price < ZERO:
            raise ValidationError("El precio no puede ser negativo.")
        self._price = money(price)

    @property
    def stock(self) -> int:
        """Existencias disponibles (entero no negativo)."""
        return self._stock

    @stock.setter
    def stock(self, value: int) -> None:
        if isinstance(value, bool) or not isinstance(value, int):
            raise ValidationError("Las existencias deben ser un número entero.")
        if value < 0:
            raise ValidationError("Las existencias no pueden ser negativas.")
        self._stock = value

    @property
    def discount_percentage(self) -> Decimal:
        """Descuento promocional propio del producto (se usa cuando no se indica otro)."""
        return self._discount_percentage

    @discount_percentage.setter
    def discount_percentage(self, value: object) -> None:
        self._discount_percentage = validate_percentage(value, "Descuento")

    @property
    def max_discount(self) -> Decimal:
        """Tope máximo de descuento configurable para la categoría."""
        return self._max_discount

    @max_discount.setter
    def max_discount(self, value: object) -> None:
        self._max_discount = validate_percentage(value, "Descuento máximo")

    # ------------------------------------------------------------------
    # Inventario
    # ------------------------------------------------------------------
    def is_sellable(self) -> bool:
        """Indica si el producto puede venderse. Las subclases pueden restringirlo."""
        return True

    def reduce_stock(self, quantity: int) -> None:
        """Descuenta existencias tras una compra; nunca deja el inventario negativo."""
        quantity = validate_quantity(quantity)
        if quantity > self._stock:
            raise InsufficientStockError(
                f"Existencias insuficientes para '{self.name}': solicitadas {quantity}, "
                f"disponibles {self._stock}."
            )
        self._stock -= quantity

    # ------------------------------------------------------------------
    # Métodos polimórficos
    # ------------------------------------------------------------------
    def description(self) -> str:
        """Devuelve una descripción textual del producto."""
        return (
            f"{self.name} | Categoría: {self.CATEGORY} | Precio: {format_money(self.price)} "
            f"| Existencias: {self.stock} unidades"
        )

    def discount_rule(self) -> str:
        """Explica en español la regla de descuento de la categoría (se muestra en la GUI)."""
        return self.DISCOUNT_RULE.format(max=format_percentage(self.max_discount))

    def calculate_discount(
        self,
        percentage: object | None = None,
        coupon: object | None = None,
        premium_customer: bool = False,
    ) -> Decimal:
        """Calcula el descuento por unidad (monto en dinero) respecto al precio de lista.

        Args:
            percentage: descuento promocional (0-100). Si es ``None`` se usa
                ``discount_percentage`` del producto.
            coupon: porcentaje de cupón opcional (0-100).
            premium_customer: si es ``True`` se agrega ``PREMIUM_BONUS``.

        Regla base: solo se aplica la mejor oferta individual (no acumulable).
        """
        offers = self._collect_offers(percentage, coupon, premium_customer)
        return self._apply_offers(self.price, [max(offers)])

    def calculate_final_price(
        self,
        percentage: object | None = None,
        coupon: object | None = None,
        premium_customer: bool = False,
    ) -> Decimal:
        """Precio unitario final = precio de lista - ``calculate_discount(...)``.

        Gracias al polimorfismo, este método funciona igual para todas las
        subclases: cada una aporta su propia versión de ``calculate_discount``.
        """
        discount = self.calculate_discount(percentage, coupon, premium_customer)
        return money(max(self.price - discount, ZERO))

    # ------------------------------------------------------------------
    # Ayudantes protegidos reutilizados por las subclases
    # ------------------------------------------------------------------
    def _collect_offers(
        self, percentage: object | None, coupon: object | None, premium_customer: bool
    ) -> list[Decimal]:
        """Valida las ofertas y las devuelve en orden: promoción, cupón, prémium."""
        if not isinstance(premium_customer, bool):
            raise ValidationError("El indicador de cliente prémium debe ser True o False.")
        promo = (
            self.discount_percentage
            if percentage is None
            else validate_percentage(percentage, "Descuento")
        )
        offers = [promo]
        if coupon is not None:
            offers.append(validate_percentage(coupon, "Cupón"))
        if premium_customer:
            offers.append(self.PREMIUM_BONUS)
        return offers

    def _apply_offers(self, base_amount: Decimal, rates: list[Decimal]) -> Decimal:
        """Aplica ``rates`` de forma secuencial sobre ``base_amount`` y devuelve el monto descontado.

        Cada porcentaje se aplica sobre el valor que dejó el anterior (no se suman).
        El resultado respeta ``max_discount`` y nunca deja un precio negativo.
        """
        remaining = base_amount
        for rate in rates:
            remaining -= remaining * rate / HUNDRED
        floor = base_amount * (HUNDRED - self.max_discount) / HUNDRED
        remaining = max(remaining, floor, ZERO)
        return money(base_amount - remaining)

    def __repr__(self) -> str:
        return f"{type(self).__name__}(name={self.name!r}, price={self.price}, stock={self.stock})"
