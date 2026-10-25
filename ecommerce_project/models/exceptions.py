"""Excepciones propias del dominio de la tienda.

Los mensajes de las excepciones están en español porque la interfaz gráfica
los muestra directamente al usuario.
"""


class ECommerceError(Exception):
    """Error base de la aplicación. La GUI captura esta clase para mostrar mensajes."""


class ValidationError(ECommerceError, ValueError):
    """Datos inválidos: nombres vacíos, precios negativos, porcentajes fuera de rango, etc."""


class InsufficientStockError(ECommerceError):
    """La cantidad solicitada supera las existencias disponibles."""


class DuplicateProductError(ECommerceError):
    """Ya existe un producto con el mismo identificador o nombre."""


class ProductNotFoundError(ECommerceError):
    """El producto solicitado no existe en el inventario o en el carrito."""


class CartError(ECommerceError):
    """Operación inválida sobre el carrito (por ejemplo, pagar un carrito vacío)."""
