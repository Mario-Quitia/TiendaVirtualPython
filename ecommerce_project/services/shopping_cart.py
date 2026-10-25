"""Carrito de compras: almacena productos de cualquier categoría y calcula totales.

El carrito no conoce las reglas de cada categoría: solo llama a
``product.calculate_discount(...)`` y ``product.description()``. Cada objeto
responde con su propia implementación (polimorfismo).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal

from models.exceptions import (
    CartError,
    InsufficientStockError,
    ProductNotFoundError,
    ValidationError,
)
from models.product import (
    ZERO,
    Product,
    format_money,
    format_percentage,
    money,
    validate_percentage,
    validate_quantity,
)


@dataclass(frozen=True)
class CartLine:
    """Línea del carrito: diferencia precio unitario, descuento, cantidad y subtotal."""

    product: Product
    quantity: int
    unit_price: Decimal
    unit_discount: Decimal

    @property
    def final_unit_price(self) -> Decimal:
        return money(self.unit_price - self.unit_discount)

    @property
    def line_subtotal(self) -> Decimal:
        return money(self.unit_price * self.quantity)

    @property
    def line_discount(self) -> Decimal:
        return money(self.unit_discount * self.quantity)

    @property
    def line_total(self) -> Decimal:
        return money(self.line_subtotal - self.line_discount)


@dataclass(frozen=True)
class CartSummary:
    """Resumen del carrito (también se usa como recibo de la compra simulada)."""

    lines: list[CartLine] = field(default_factory=list)
    subtotal: Decimal = ZERO
    total_discount: Decimal = ZERO
    total: Decimal = ZERO

    @property
    def is_empty(self) -> bool:
        return not self.lines

    @property
    def total_units(self) -> int:
        return sum(line.quantity for line in self.lines)

    def as_text(self) -> str:
        """Recibo en texto plano (en español, porque se muestra en la GUI)."""
        if self.is_empty:
            return "El carrito está vacío."
        rows = [f"{'Producto':<24}{'Cant.':>5}{'Unitario':>12}{'Descuento':>12}{'Total':>13}", "-" * 66]
        for line in self.lines:
            rows.append(
                f"{line.product.name[:23]:<24}{line.quantity:>5}"
                f"{format_money(line.unit_price):>12}{format_money(line.line_discount):>12}"
                f"{format_money(line.line_total):>13}"
            )
        rows += [
            "-" * 66,
            f"{'Subtotal:':<45}{format_money(self.subtotal):>21}",
            f"{'Descuento total:':<45}{'-' + format_money(self.total_discount):>21}",
            f"{'Total final:':<45}{format_money(self.total):>21}",
            "",
            "Artículos:",
        ]
        rows += [f"  - {line.product.description()}" for line in self.lines]
        return "\n".join(rows)


class ShoppingCart:
    """Carrito que mantiene productos (composición) y opciones de descuento de la compra.

    Las existencias NO se descuentan al agregar productos; solo ``checkout()``
    las actualiza, y únicamente si toda la compra es válida.
    """

    def __init__(self) -> None:
        self._items: dict[str, tuple[Product, int]] = {}
        self._discount_percentage = ZERO
        self._coupon: Decimal | None = None
        self._premium_customer = False

    # ------------------------------------------------------------------
    # Opciones de descuento de la compra
    # ------------------------------------------------------------------
    @property
    def discount_percentage(self) -> Decimal:
        return self._discount_percentage

    @property
    def coupon(self) -> Decimal | None:
        return self._coupon

    @property
    def premium_customer(self) -> bool:
        return self._premium_customer

    def apply_discount(self, percentage: object) -> None:
        """Descuento general de la compra. En cada línea se usa el mayor entre
        este valor y el descuento promocional propio del producto."""
        self._discount_percentage = validate_percentage(percentage, "Descuento")

    def apply_coupon(self, coupon: object | None) -> None:
        """Aplica un cupón porcentual (1-100). ``None`` elimina el cupón."""
        if coupon is None:
            self._coupon = None
            return
        value = validate_percentage(coupon, "Cupón")
        if value == ZERO:
            raise ValidationError("El cupón debe ser mayor que 0.")
        self._coupon = value

    def set_premium_customer(self, enabled: bool) -> None:
        if not isinstance(enabled, bool):
            raise ValidationError("El indicador de cliente prémium debe ser True o False.")
        self._premium_customer = enabled

    # ------------------------------------------------------------------
    # Gestión de productos
    # ------------------------------------------------------------------
    @staticmethod
    def _key(product_name: str) -> str:
        return product_name.strip().lower()

    def _get_entry(self, product_name: str) -> tuple[Product, int]:
        entry = self._items.get(self._key(product_name or ""))
        if entry is None:
            raise ProductNotFoundError(f"'{product_name}' no está en el carrito.")
        return entry

    @staticmethod
    def _check_availability(product: Product, quantity: int) -> None:
        if not product.is_sellable():
            raise CartError(f"'{product.name}' no se puede vender (ya no está disponible).")
        if quantity > product.stock:
            raise InsufficientStockError(
                f"Existencias insuficientes para '{product.name}': solicitadas {quantity}, "
                f"disponibles {product.stock}."
            )

    def add_product(self, product: Product, quantity: int = 1) -> None:
        """Agrega un producto o, si ya existe, incrementa su cantidad (sin duplicar líneas)."""
        if not isinstance(product, Product):
            raise ValidationError("Solo se pueden agregar productos al carrito.")
        quantity = validate_quantity(quantity)
        key = self._key(product.name)
        current = 0
        if key in self._items:
            existing, current = self._items[key]
            if existing is not product:
                raise CartError(f"Ya hay en el carrito otro producto llamado '{product.name}'.")
        self._check_availability(product, current + quantity)
        self._items[key] = (product, current + quantity)

    def remove_product(self, product_name: str) -> Product:
        """Elimina un producto del carrito y lo devuelve."""
        product, _ = self._get_entry(product_name)
        del self._items[self._key(product_name)]
        return product

    def update_quantity(self, product_name: str, quantity: int) -> None:
        """Cambia la cantidad de un producto que ya está en el carrito."""
        product, _ = self._get_entry(product_name)
        quantity = validate_quantity(quantity)
        self._check_availability(product, quantity)
        self._items[self._key(product_name)] = (product, quantity)

    def contains(self, product: Product) -> bool:
        entry = self._items.get(self._key(product.name))
        return entry is not None and entry[0] is product

    def clear(self) -> None:
        """Vacía el carrito y restablece las opciones de descuento."""
        self._items.clear()
        self._discount_percentage = ZERO
        self._coupon = None
        self._premium_customer = False

    def is_empty(self) -> bool:
        return not self._items

    def __len__(self) -> int:
        return len(self._items)

    # ------------------------------------------------------------------
    # Cálculos (polimorfismo)
    # ------------------------------------------------------------------
    def get_items(self) -> list[CartLine]:
        """Devuelve las líneas del carrito con sus precios y descuentos calculados."""
        lines = []
        for product, quantity in self._items.values():
            promo = max(product.discount_percentage, self._discount_percentage)
            # Llamada polimórfica: cada categoría aplica su propia regla.
            unit_discount = product.calculate_discount(
                promo, self._coupon, self._premium_customer
            )
            lines.append(CartLine(product, quantity, product.price, unit_discount))
        return lines

    def calculate_subtotal(self) -> Decimal:
        return money(sum((line.line_subtotal for line in self.get_items()), ZERO))

    def calculate_total_discount(self) -> Decimal:
        return money(sum((line.line_discount for line in self.get_items()), ZERO))

    def calculate_total(self) -> Decimal:
        return money(self.calculate_subtotal() - self.calculate_total_discount())

    def get_cart_summary(self) -> CartSummary:
        lines = self.get_items()
        subtotal = money(sum((line.line_subtotal for line in lines), ZERO))
        discount = money(sum((line.line_discount for line in lines), ZERO))
        return CartSummary(lines, subtotal, discount, money(subtotal - discount))

    def describe_promotions(self) -> str:
        """Texto corto con las opciones activas (para la GUI)."""
        parts = []
        if self._discount_percentage > ZERO:
            parts.append(f"Descuento {format_percentage(self._discount_percentage)}%")
        if self._coupon is not None:
            parts.append(f"Cupón {format_percentage(self._coupon)}%")
        if self._premium_customer:
            parts.append(f"Prémium +{format_percentage(Product.PREMIUM_BONUS)}%")
        return " | ".join(parts) if parts else "Sin promociones aplicadas"

    # ------------------------------------------------------------------
    # Compra simulada
    # ------------------------------------------------------------------
    def checkout(self) -> CartSummary:
        """Completa la compra simulada.

        1. Verifica de nuevo TODAS las existencias antes de modificar nada.
        2. Solo si todo es válido descuenta el inventario.
        3. Devuelve el recibo y vacía el carrito.
        """
        if self.is_empty():
            raise CartError("No se puede finalizar la compra: el carrito está vacío.")
        for product, quantity in self._items.values():
            self._check_availability(product, quantity)
        receipt = self.get_cart_summary()
        for product, quantity in self._items.values():
            product.reduce_stock(quantity)
        self.clear()
        return receipt
