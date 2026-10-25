"""Pruebas de la jerarquía de productos (sin interfaz gráfica)."""

import unittest
from datetime import date, timedelta
from decimal import Decimal

from models import (
    ClothingProduct,
    ElectronicProduct,
    FoodProduct,
    Product,
    ValidationError,
)

FUTURE = date.today() + timedelta(days=30)


class TestBaseProduct(unittest.TestCase):
    def setUp(self):
        self.product = Product("Notebook", "200", 10)

    def test_description_and_price(self):
        text = self.product.description()
        self.assertIn("Notebook", text)
        self.assertIn("$200.00", text)
        self.assertIn("Existencias: 10", text)
        self.assertEqual(self.product.calculate_final_price(), Decimal("200.00"))
        self.assertEqual(self.product.calculate_final_price(10), Decimal("180.00"))

    def test_base_offers_are_not_cumulative(self):
        # Solo la mejor oferta: max(10, 15, 5) = 15 % -> $170
        self.assertEqual(self.product.calculate_final_price(10, 15, True), Decimal("170.00"))

    def test_base_maximum_discount(self):
        self.assertEqual(self.product.calculate_final_price(80), Decimal("100.00"))

    def test_uses_own_discount_when_none_given(self):
        product = Product("Pen", "10", 5, discount_percentage=20)
        self.assertEqual(product.calculate_discount(), Decimal("2.00"))
        self.assertEqual(product.calculate_final_price(), Decimal("8.00"))

    def test_invalid_data_raises(self):
        with self.assertRaises(ValidationError):
            Product("   ", "10", 1)
        with self.assertRaises(ValidationError):
            Product("Item", "-1", 1)
        with self.assertRaises(ValidationError):
            Product("Item", "abc", 1)
        with self.assertRaises(ValidationError):
            Product("Item", "10", -3)
        with self.assertRaises(ValidationError):
            Product("Item", "10", 2.5)

    def test_invalid_discounts(self):
        for value in (-5, 101, "abc", "", True):
            with self.subTest(value=value), self.assertRaises(ValidationError):
                self.product.calculate_discount(value)
        with self.assertRaises(ValidationError):
            self.product.calculate_discount(10, 150)  # cupón inválido
        with self.assertRaises(ValidationError):
            self.product.calculate_discount(10, 5, "yes")  # bandera prémium inválida


class TestElectronicProduct(unittest.TestCase):
    def setUp(self):
        self.laptop = ElectronicProduct("Laptop", "1000", 5, warranty_months=24,
                                        depreciation_percentage=10)

    def test_depreciation_applied_before_discount(self):
        self.assertEqual(self.laptop.depreciated_price(), Decimal("900.00"))
        self.assertEqual(self.laptop.calculate_final_price(0), Decimal("900.00"))
        self.assertEqual(self.laptop.calculate_final_price(10), Decimal("810.00"))
        self.assertEqual(self.laptop.calculate_discount(10), Decimal("190.00"))

    def test_depreciation_is_not_applied_twice(self):
        first = self.laptop.calculate_final_price(10)
        second = self.laptop.calculate_final_price(10)
        self.assertEqual(first, second)
        self.assertEqual(self.laptop.price, Decimal("1000.00"))

    def test_promotional_cap(self):
        # 900 con tope del 30 % -> 630
        self.assertEqual(self.laptop.calculate_final_price(50), Decimal("630.00"))

    def test_description_overridden(self):
        text = self.laptop.description()
        self.assertIn("Categoría: Electrónica", text)
        self.assertIn("Garantía: 24 meses", text)
        self.assertIn("Depreciación: 10%", text)

    def test_invalid_depreciation_and_warranty(self):
        with self.assertRaises(ValidationError):
            ElectronicProduct("TV", "500", 1, depreciation_percentage=95)
        with self.assertRaises(ValidationError):
            ElectronicProduct("TV", "500", 1, warranty_months=-1)


class TestFoodProduct(unittest.TestCase):
    def setUp(self):
        self.milk = FoodProduct("Milk", "100", 20, FUTURE)

    def test_maximum_discount_15_percent(self):
        self.assertEqual(self.milk.calculate_final_price(20), Decimal("85.00"))
        self.assertEqual(self.milk.calculate_final_price(10), Decimal("90.00"))

    def test_cap_applies_to_coupons(self):
        # 10 % + 10 % = 19 % acumulado -> limitado a 15 %
        self.assertEqual(self.milk.calculate_final_price(10, 10), Decimal("85.00"))
        self.assertEqual(self.milk.calculate_final_price(5, 5), Decimal("90.25"))

    def test_configurable_cap(self):
        food = FoodProduct("Rice", "100", 5, FUTURE, max_discount=25)
        self.assertEqual(food.calculate_final_price(20), Decimal("80.00"))

    def test_expiration_date_validation(self):
        self.assertEqual(FoodProduct("Bread", "2", 1, "2099-12-31").expiration_date,
                         date(2099, 12, 31))
        for bad in ("2024-13-40", "31/12/2099", "", "tomorrow"):
            with self.subTest(bad=bad), self.assertRaises(ValidationError):
                FoodProduct("Bread", "2", 1, bad)
        with self.assertRaises(ValidationError):
            FoodProduct("Bread", "2", 1, date.today() - timedelta(days=1))

    def test_description_shows_expiration(self):
        self.assertIn(f"Vence: {FUTURE.isoformat()}", self.milk.description())


class TestClothingProduct(unittest.TestCase):
    def setUp(self):
        self.jacket = ClothingProduct("Jacket", "100", 10, "m", "blue")

    def test_mandatory_cumulative_example(self):
        # $100 -> 10 % -> $90 -> 20 % -> $72
        self.assertEqual(self.jacket.calculate_final_price(10, 20), Decimal("72.00"))

    def test_cumulative_with_premium(self):
        self.assertEqual(self.jacket.calculate_final_price(10, 20, True), Decimal("68.40"))

    def test_cumulative_cap_40_percent(self):
        self.assertEqual(self.jacket.calculate_final_price(30, 30), Decimal("60.00"))

    def test_attributes_and_description(self):
        self.assertEqual(self.jacket.size, "M")
        self.assertIn("Talla: M | Color: Blue", self.jacket.description())
        with self.assertRaises(ValidationError):
            ClothingProduct("Shirt", "10", 1, "XXXL", "Red")
        with self.assertRaises(ValidationError):
            ClothingProduct("Shirt", "10", 1, "M", "  ")


class TestOverloadAndPolymorphism(unittest.TestCase):
    def test_three_overload_variants(self):
        product = Product("Bag", "200", 3)
        self.assertEqual(product.calculate_discount(10), Decimal("20.00"))
        self.assertEqual(product.calculate_discount(10, 15), Decimal("30.00"))
        self.assertEqual(product.calculate_discount(0, 0, True), Decimal("10.00"))

    def test_coupon_and_premium_per_category(self):
        laptop = ElectronicProduct("Laptop", "1000", 1, depreciation_percentage=10)
        food = FoodProduct("Cheese", "100", 1, FUTURE)
        shirt = ClothingProduct("Shirt", "100", 1, "S", "Red")
        # Electrónico: 900 y mejor oferta 15 % -> 765
        self.assertEqual(laptop.calculate_final_price(10, 15, True), Decimal("765.00"))
        # Alimento: 10 %, 15 %, 5 % acumulados superan el 15 % -> 85
        self.assertEqual(food.calculate_final_price(10, 15, True), Decimal("85.00"))
        # Ropa: 100 * .9 * .85 * .95 = 72.675; el descuento 27.325 se redondea a 27.33
        self.assertEqual(shirt.calculate_discount(10, 15, True), Decimal("27.33"))
        self.assertEqual(shirt.calculate_final_price(10, 15, True), Decimal("72.67"))

    def test_polymorphism_through_base_reference(self):
        products: list[Product] = [
            ElectronicProduct("Tablet", "100", 1, depreciation_percentage=10),
            FoodProduct("Honey", "100", 1, FUTURE),
            ClothingProduct("Scarf", "100", 1, "S", "Green"),
        ]
        prices = [p.calculate_final_price(20, 10) for p in products]
        self.assertEqual(prices, [Decimal("72.00"), Decimal("85.00"), Decimal("72.00")])
        categories = [p.description().split("|")[1].strip() for p in products]
        self.assertEqual(categories, ["Categoría: Electrónica", "Categoría: Alimentos",
                                      "Categoría: Ropa"])


if __name__ == "__main__":
    unittest.main()
