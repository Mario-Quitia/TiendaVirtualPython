"""Pruebas del carrito, el inventario y la fábrica de productos (sin interfaz gráfica)."""

import unittest
from datetime import date, timedelta
from decimal import Decimal

from models import (
    CartError,
    ClothingProduct,
    DuplicateProductError,
    ElectronicProduct,
    FoodProduct,
    InsufficientStockError,
    ProductNotFoundError,
    ValidationError,
)
from services import InventoryManager, ShoppingCart, create_product, load_sample_data

FUTURE = date.today() + timedelta(days=30)


class CartTestCase(unittest.TestCase):
    def setUp(self):
        self.laptop = ElectronicProduct("Laptop", "1000", 5, depreciation_percentage=10)
        self.apples = FoodProduct("Apples", "2.00", 100, FUTURE)
        self.shirt = ClothingProduct("Shirt", "50", 10, "M", "White", discount_percentage=10)
        self.cart = ShoppingCart()


class TestCartTotals(CartTestCase):
    def fill(self):
        self.cart.add_product(self.laptop, 2)
        self.cart.add_product(self.apples, 10)
        self.cart.add_product(self.shirt, 3)

    def test_mixed_categories_totals(self):
        self.fill()
        self.assertEqual(self.cart.calculate_subtotal(), Decimal("2170.00"))
        self.assertEqual(self.cart.calculate_total_discount(), Decimal("215.00"))
        self.assertEqual(self.cart.calculate_total(), Decimal("1955.00"))

    def test_lines_separate_price_discount_quantity(self):
        self.fill()
        lines = {line.product.name: line for line in self.cart.get_items()}
        laptop = lines["Laptop"]
        self.assertEqual(laptop.unit_price, Decimal("1000.00"))
        self.assertEqual(laptop.unit_discount, Decimal("100.00"))
        self.assertEqual(laptop.quantity, 2)
        self.assertEqual(laptop.line_subtotal, Decimal("2000.00"))
        self.assertEqual(laptop.line_total, Decimal("1800.00"))

    def test_discount_coupon_and_premium(self):
        self.fill()
        self.cart.apply_discount(20)
        self.cart.apply_coupon(10)
        self.cart.set_premium_customer(True)
        self.assertEqual(self.cart.calculate_subtotal(), Decimal("2170.00"))
        # Laptop 2 x 280, manzanas 10 x 0.30, camisa 3 x 15.80
        self.assertEqual(self.cart.calculate_total_discount(), Decimal("610.40"))
        self.assertEqual(self.cart.calculate_total(), Decimal("1559.60"))

    def test_invalid_coupon_and_discount(self):
        for coupon in (0, -1, 120, "abc"):
            with self.subTest(coupon=coupon), self.assertRaises(ValidationError):
                self.cart.apply_coupon(coupon)
        with self.assertRaises(ValidationError):
            self.cart.apply_discount(101)

    def test_summary_uses_polymorphic_descriptions(self):
        self.fill()
        text = self.cart.get_cart_summary().as_text()
        self.assertIn("Garantía", text)
        self.assertIn("Vence", text)
        self.assertIn("Talla: M", text)


class TestCartQuantities(CartTestCase):
    def test_duplicate_add_updates_quantity(self):
        self.cart.add_product(self.shirt, 2)
        self.cart.add_product(self.shirt, 3)
        self.assertEqual(len(self.cart), 1)
        self.assertEqual(self.cart.get_items()[0].quantity, 5)

    def test_invalid_quantities(self):
        for quantity in (0, -2, 1.5, "3"):
            with self.subTest(quantity=quantity), self.assertRaises(ValidationError):
                self.cart.add_product(self.shirt, quantity)

    def test_insufficient_stock(self):
        with self.assertRaises(InsufficientStockError):
            self.cart.add_product(self.laptop, 6)
        self.cart.add_product(self.laptop, 4)
        with self.assertRaises(InsufficientStockError):
            self.cart.add_product(self.laptop, 2)  # 4 + 2 > 5
        with self.assertRaises(InsufficientStockError):
            self.cart.update_quantity("Laptop", 9)

    def test_adding_does_not_reduce_stock(self):
        self.cart.add_product(self.laptop, 3)
        self.assertEqual(self.laptop.stock, 5)

    def test_update_and_remove(self):
        self.cart.add_product(self.laptop, 1)
        self.cart.add_product(self.shirt, 1)
        self.cart.update_quantity("laptop", 4)
        self.assertEqual(self.cart.calculate_subtotal(), Decimal("4050.00"))
        self.cart.remove_product("Shirt")
        self.assertEqual(len(self.cart), 1)
        with self.assertRaises(ProductNotFoundError):
            self.cart.remove_product("Shirt")
        with self.assertRaises(ValidationError):
            self.cart.update_quantity("Laptop", 0)


class TestCheckout(CartTestCase):
    def test_successful_checkout_reduces_stock(self):
        self.cart.add_product(self.laptop, 2)
        self.cart.add_product(self.apples, 10)
        receipt = self.cart.checkout()
        self.assertEqual(self.laptop.stock, 3)
        self.assertEqual(self.apples.stock, 90)
        self.assertEqual(receipt.total, Decimal("1820.00"))
        self.assertTrue(self.cart.is_empty())

    def test_checkout_is_all_or_nothing(self):
        self.cart.add_product(self.laptop, 2)
        self.cart.add_product(self.shirt, 5)
        self.shirt.stock = 3  # el inventario cambió después de agregar al carrito
        with self.assertRaises(InsufficientStockError):
            self.cart.checkout()
        self.assertEqual(self.laptop.stock, 5)
        self.assertEqual(self.shirt.stock, 3)
        self.assertEqual(len(self.cart), 2)

    def test_stock_never_negative(self):
        with self.assertRaises(InsufficientStockError):
            self.laptop.reduce_stock(6)
        self.assertEqual(self.laptop.stock, 5)


class TestEmptyCart(unittest.TestCase):
    def test_empty_cart(self):
        cart = ShoppingCart()
        self.assertTrue(cart.is_empty())
        self.assertEqual(cart.get_items(), [])
        self.assertEqual(cart.calculate_subtotal(), Decimal("0.00"))
        self.assertEqual(cart.calculate_total_discount(), Decimal("0.00"))
        self.assertEqual(cart.calculate_total(), Decimal("0.00"))
        self.assertTrue(cart.get_cart_summary().is_empty)
        with self.assertRaises(CartError):
            cart.checkout()

    def test_clear_resets_cart(self):
        cart = ShoppingCart()
        cart.add_product(ClothingProduct("Cap", "10", 3, "S", "Red"))
        cart.apply_coupon(10)
        cart.clear()
        self.assertTrue(cart.is_empty())
        self.assertIsNone(cart.coupon)


class TestInventoryAndFactory(unittest.TestCase):
    def test_ids_and_duplicates(self):
        inventory = InventoryManager()
        first = inventory.add_product(ClothingProduct("Cap", "10", 3, "S", "Red"))
        self.assertEqual(first, "P001")
        with self.assertRaises(DuplicateProductError):
            inventory.add_product(ClothingProduct("Hat", "10", 3, "S", "Red"), "p001")
        with self.assertRaises(DuplicateProductError):
            inventory.add_product(ClothingProduct("cap", "12", 1, "M", "Blue"))
        with self.assertRaises(ProductNotFoundError):
            inventory.get_product("P999")

    def test_sample_data_loads(self):
        inventory = InventoryManager()
        load_sample_data(inventory)
        self.assertEqual(len(inventory), 9)

    def test_factory_builds_each_category(self):
        tv = create_product("Electrónica", "TV", "500", "3", warranty="12", depreciation="10")
        food = create_product("Alimentos", "Tea", "4.5", "10", expiration="2099-01-01")
        sock = create_product("Ropa", "Socks", "5", "8", size="S", color="black")
        self.assertIsInstance(tv, ElectronicProduct)
        self.assertIsInstance(food, FoodProduct)
        self.assertIsInstance(sock, ClothingProduct)

    def test_factory_reports_missing_fields(self):
        cases = [
            dict(category="Alimentos", name="", price="1", stock="1", expiration="2099-01-01"),
            dict(category="Alimentos", name="Tea", price="", stock="1", expiration="2099-01-01"),
            dict(category="Alimentos", name="Tea", price="1", stock="1.5", expiration="2099-01-01"),
            dict(category="Alimentos", name="Tea", price="1", stock="1", expiration=""),
            dict(category="Toys", name="Ball", price="1", stock="1"),
            dict(category="Electrónica", name="TV", price="1", stock="1", warranty="abc"),
        ]
        for case in cases:
            with self.subTest(case=case), self.assertRaises(ValidationError):
                create_product(**case)


if __name__ == "__main__":
    unittest.main()
