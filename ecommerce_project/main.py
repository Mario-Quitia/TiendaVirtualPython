"""Punto de entrada del Gestor de Productos de Tienda Virtual.

Uso:
    python main.py            # abre la interfaz gráfica con datos de ejemplo
    python main.py --empty    # abre la interfaz con el inventario vacío
    python main.py --demo     # demostración de polimorfismo en consola (sin ventanas)
"""

import argparse
from datetime import date, timedelta

from models import ClothingProduct, ElectronicProduct, FoodProduct, Product, format_money
from services import ShoppingCart


def run_console_demo() -> None:
    """Muestra herencia, polimorfismo y la simulación de sobrecarga en consola."""
    products: list[Product] = [  # referencias del tipo base Product
        ElectronicProduct("Laptop Pro 14", "1000", 5, warranty_months=24, depreciation_percentage=10),
        FoodProduct("Organic Coffee", "100", 20, date.today() + timedelta(days=90)),
        ClothingProduct("Denim Jacket", "100", 10, "M", "Blue"),
    ]
    print("=== Polimorfismo: mismas llamadas, distinto comportamiento ===")
    for product in products:
        print(product.description())
        print(f"  calculate_discount(10)           -> {format_money(product.calculate_discount(10))}")
        print(f"  calculate_discount(10, 20)       -> {format_money(product.calculate_discount(10, 20))}")
        print(f"  calculate_discount(10, 20, True) -> "
              f"{format_money(product.calculate_discount(10, 20, True))}")
        print(f"  Precio final con 10% + cupón 20%: {format_money(product.calculate_final_price(10, 20))}")
        print()

    cart = ShoppingCart()
    for product in products:
        cart.add_product(product, 2)
    cart.apply_coupon(20)
    print("=== Carrito de compras (cupón 20%) ===")
    print(cart.get_cart_summary().as_text())


def main() -> None:
    parser = argparse.ArgumentParser(description="Gestor de Productos de Tienda Virtual")
    parser.add_argument("--demo", action="store_true", help="ejecuta la demostración de polimorfismo en consola")
    parser.add_argument("--empty", action="store_true", help="inicia sin productos de ejemplo")
    args = parser.parse_args()
    if args.demo:
        run_console_demo()
        return
    from gui.main_window import run_app  # se importa aquí para que --demo no requiera Tkinter

    run_app(with_sample_data=not args.empty)


if __name__ == "__main__":
    main()
