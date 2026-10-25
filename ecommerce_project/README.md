# E-Commerce Product Manager

Proyecto de la **Fase 3 del curso Programación (UNAD, código 213023)**: *Ejercicio 4. Sistema de Tienda Virtual*.

## 1. Objetivo

Aplicación de escritorio en Python con Tkinter. Permite gestionar los productos de una tienda virtual, aplicar descuentos según la categoría de cada producto y calcular el total de una compra simulada. Se construyó para demostrar **herencia, polimorfismo, sobrescritura, simulación de sobrecarga, encapsulamiento y composición**.

La interfaz gráfica está completamente en inglés, como exige la guía. El código usa nombres en inglés y los comentarios y esta documentación están en español.

## 2. Funcionalidades principales

- Registro, edición, eliminación y consulta de productos de tres categorías: **Electronics**, **Food** y **Clothing**.
- Formulario que cambia sus campos según la categoría:
  - Electronics: garantía y depreciación.
  - Food: fecha de vencimiento.
  - Clothing: talla y color.
- Tabla de inventario (`ttk.Treeview`) con ID, nombre, categoría, precio, existencias, descuento y precio final.
- Carrito de compras con productos de distintas categorías:
  - agregar, eliminar y modificar cantidades;
  - descuento general, cupón y beneficio prémium;
  - subtotal, descuento total y total final.
- Compra simulada (*Checkout*):
  - pide confirmación;
  - vuelve a verificar las existencias;
  - actualiza el inventario solo si toda la compra es válida;
  - muestra un recibo.
- Validaciones con mensajes en inglés (`messagebox` y barra de estado). La aplicación no se cierra ante errores.
- Datos de ejemplo precargados (9 productos) para facilitar la sustentación.
- Demostración de polimorfismo en consola: `python main.py --demo`.

## 3. Requisitos

- **Python 3.10 o superior.** Se probó con Python 3.14.2 en Windows 11.
- Tkinter, que viene incluido con el instalador oficial de Python.
- **No hay que instalar paquetes externos.** Solo se usa la biblioteca estándar: `tkinter`, `ttk`, `decimal`, `datetime`, `dataclasses`, `unittest` y `argparse`.

## 4. Estructura de carpetas

```
ecommerce_project/
├── main.py                     # Punto de entrada (GUI o demo en consola)
├── models/                     # Dominio: jerarquía de productos (sin Tkinter)
│   ├── __init__.py
│   ├── exceptions.py           # Excepciones propias (mensajes en inglés)
│   ├── product.py              # Clase base Product + utilidades monetarias
│   ├── electronic_product.py   # ElectronicProduct
│   ├── food_product.py         # FoodProduct
│   └── clothing_product.py     # ClothingProduct
├── services/                   # Lógica de negocio (sin Tkinter)
│   ├── __init__.py
│   ├── shopping_cart.py        # ShoppingCart, CartLine, CartSummary
│   ├── inventory_manager.py    # InventoryManager + datos de ejemplo
│   └── product_factory.py      # Convierte los textos del formulario en productos
├── gui/                        # Interfaz gráfica (Tkinter + ttk)
│   ├── __init__.py
│   ├── main_window.py          # Ventana principal / controlador
│   ├── product_form.py         # Panel de registro de productos
│   ├── inventory_view.py       # Tabla de inventario
│   ├── cart_view.py            # Panel del carrito y resumen
│   ├── dialogs.py              # Ventana modal de detalles y recibo
│   └── theme.py                # Paleta de colores y estilos
├── tests/
│   ├── test_products.py
│   └── test_shopping_cart.py
└── README.md
```

Se agregaron cuatro archivos a la estructura sugerida:

- `exceptions.py`: centraliza los errores de negocio.
- `product_factory.py`: permite probar la validación del formulario sin abrir ventanas.
- `theme.py`: reúne los estilos visuales.
- `dialogs.py`: contiene la ventana reutilizable de detalles y recibo.

## 5. Ejecución

Abre una terminal **dentro de la carpeta `ecommerce_project`** y ejecuta:

```bash
python main.py            # abre la aplicación con datos de ejemplo
python main.py --empty    # abre la aplicación con el inventario vacío
python main.py --demo     # demostración de polimorfismo en consola
```

## 6. Pruebas

Desde la carpeta `ecommerce_project`:

```bash
python -m unittest discover -s tests -v
```

Son 42 pruebas con `unittest` y ninguna abre ventanas. Cubren:

- el producto base;
- la depreciación;
- el tope de descuento de los alimentos;
- los descuentos acumulados de la ropa (incluido el ejemplo de $100 → $72);
- los cupones y el beneficio prémium;
- los descuentos inválidos;
- un carrito con varias categorías;
- subtotales y totales;
- el inventario insuficiente;
- la reducción de existencias después de la compra;
- la modificación y eliminación de productos del carrito;
- el carrito vacío;
- los IDs duplicados;
- la fábrica de productos.

## 7. Jerarquía de clases

```
Product                      (clase base: name, price, stock)
├── ElectronicProduct        (+ warranty_months, depreciation_percentage)
├── FoodProduct              (+ expiration_date)
└── ClothingProduct          (+ size, color)

ShoppingCart ──contiene──> Product (cualquier subclase)      [composición]
InventoryManager ──contiene──> Product (por ID: P001, P002…)
```

## 8. Conceptos de POO y dónde se demuestran

| Concepto | Dónde |
|---|---|
| **Herencia** | `ElectronicProduct`, `FoodProduct` y `ClothingProduct` heredan de `Product` y llaman a `super().__init__(...)`. |
| **Sobrescritura** | Cada subclase redefine `description()` (reutilizando `super().description()`) y `calculate_discount()`. `FoodProduct` también redefine `is_sellable()`. |
| **Polimorfismo** | `ShoppingCart.get_items()` llama a `product.calculate_discount(...)` sin saber la categoría. `Product.calculate_final_price()` llama a `self.calculate_discount(...)`, que se resuelve en la subclase. También lo usan `InventoryView.refresh()` y `CartSummary.as_text()`, que llama a `description()`. |
| **Simulación de sobrecarga** | `calculate_discount(percentage=None, coupon=None, premium_customer=False)` en `models/product.py`. |
| **Encapsulamiento** | Atributos protegidos (`_price`, `_stock`, …) expuestos mediante `@property` con validación. El stock solo baja con `reduce_stock()`. |
| **Composición** | `ShoppingCart` mantiene los productos seleccionados con su cantidad. `InventoryManager` guarda los productos registrados y ambos comparten los mismos objetos. |

### Ejemplo de herencia y polimorfismo

```python
products: list[Product] = [
    ElectronicProduct("Laptop", "1000", 5, warranty_months=24, depreciation_percentage=10),
    FoodProduct("Coffee", "100", 20, "2099-01-01"),
    ClothingProduct("Jacket", "100", 10, "M", "Blue"),
]
for product in products:                        # misma llamada…
    print(product.description())
    print(product.calculate_final_price(10, 20)) # …resultados distintos: 720.00, 85.00, 72.00
```

## 9. Simulación de sobrecarga

Python no admite varios métodos con el mismo nombre y distinta cantidad de parámetros, como en Java. Si se definen varios, el último reemplaza a los anteriores. Por eso se usa **un único método con parámetros opcionales**:

```python
product.calculate_discount(10)            # calculate_discount(discount)
product.calculate_discount(10, 5)         # calculate_discount(discount, coupon)
product.calculate_discount(10, 5, True)   # calculate_discount(discount, coupon, premium_customer)
```

- Si no se indica el descuento (`None`), se usa el descuento promocional propio del producto.
- **Orden fijo de las ofertas:** 1) descuento promocional, 2) cupón y 3) beneficio prémium (+5 %).
- Cada porcentaje debe estar entre 0 y 100. Si no, se lanza `ValidationError`.
- El método devuelve el **monto descontado por unidad** como `Decimal`. `calculate_final_price(...)` acepta los mismos parámetros y devuelve el precio unitario final.

## 10. Reglas de descuento y depreciación

Todos los cálculos usan `decimal.Decimal` y redondean a 2 decimales con `ROUND_HALF_UP`. **Ningún precio final puede ser negativo.**

| Categoría | Regla | Tope por defecto (configurable con `max_discount`) |
|---|---|---|
| `Product` (base) | **No acumulable:** solo se aplica la mejor oferta entre descuento, cupón y prémium. | 50 % |
| `ElectronicProduct` | 1) La **depreciación** se aplica una sola vez al precio de lista. 2) Sobre el precio depreciado se aplica la mejor oferta, igual que en la base. | 30 % sobre el precio depreciado (la depreciación no cuenta en el tope) |
| `FoodProduct` | Las ofertas **se acumulan** en secuencia, pero el total nunca supera el tope. El tope rige igual para promociones y cupones. Un alimento vencido no puede venderse. | 15 % |
| `ClothingProduct` | **Descuentos acumulables** aplicados uno tras otro, sin sumar porcentajes: $100 − 10 % = $90; $90 − 20 % = **$72**. | 40 % |

### La depreciación no se aplica dos veces

El precio de lista (`price`) **nunca se modifica**. El precio depreciado se *calcula* cada vez con `depreciated_price()`. Por eso llamar varias veces a `calculate_discount` siempre da el mismo resultado.

Ejemplo: Laptop de $1,000 con depreciación del 10 % y descuento del 10 %:

- precio depreciado: $900;
- precio final: $810;
- descuento total: $190.

### Descuentos en el carrito

En cada línea del carrito se usa el **mayor** entre el descuento promocional del producto y el descuento general aplicado con *Apply Discount*. Luego se agregan el cupón y el beneficio prémium, si están activos, y cada categoría aplica su propia regla.

Validaciones del carrito:

- El cupón debe estar entre 1 y 100 %. Si el campo se deja vacío y se pulsa *Apply Coupon*, se quita el cupón.
- **Agregar al carrito no descuenta existencias.**
- *Checkout* revisa primero todas las líneas. Si alguna no tiene existencias suficientes, no se modifica nada (todo o nada).

## 11. Validaciones implementadas

- Nombre vacío.
- Precio negativo o no numérico.
- Stock no entero o negativo.
- Cantidades ≤ 0 o no enteras.
- Descuentos, cupones o depreciación fuera de rango.
- Fechas con formato distinto de `YYYY-MM-DD`, inexistentes o vencidas.
- Campos obligatorios vacíos.
- IDs o nombres de producto duplicados.
- Inventario insuficiente.
- Pago con el carrito vacío.
- Acciones sin selección.
- No se puede editar ni eliminar un producto que está en el carrito.

No se usa `eval()`: los textos se convierten con `int()`, `Decimal()` y `datetime.strptime()`.

## 12. Relación entre la interfaz y la lógica de negocio

```
gui/ (Tkinter)  ──usa──>  services/  ──usa──>  models/
   ProductForm  ──> create_product() ──> ElectronicProduct / FoodProduct / ClothingProduct
   InventoryView ─> InventoryManager
   CartView     ──> ShoppingCart  ──> product.calculate_discount(...)  (polimorfismo)
```

- `models` y `services` **no importan Tkinter**, así que se prueban sin abrir ventanas.
- `MainWindow` actúa como controlador: lee los paneles, llama a los servicios y captura las excepciones `ECommerceError`, que muestra como mensajes de error.
- No hay dependencias circulares: `models` no conoce a `services` y `services` no conoce a `gui`.

## 13. Decisiones tomadas y limitaciones conocidas

- **Los datos se guardan solo en memoria.** Al cerrar la aplicación se pierden los cambios y al abrirla se cargan de nuevo los datos de ejemplo.
- Los IDs de producto se generan automáticamente (`P001`, `P002`…). Los nombres también deben ser únicos porque el carrito identifica los productos por nombre (`remove_product(product_name)`).
- El beneficio prémium es fijo: +5 % (`Product.PREMIUM_BONUS`).
- El formulario incluye un campo adicional, *Promo Discount (%)*, para definir el descuento promocional propio de cada producto. Es el que se muestra en la columna *Discount* del inventario.
- Los cupones son porcentajes; no hay códigos de cupón.
- El pago es una simulación local: no se procesan pagos ni se solicitan datos bancarios.
- No se puede crear un alimento con fecha de vencimiento pasada. Si un alimento vence mientras la aplicación está abierta, ya no se puede agregar al carrito.
- La interfaz está diseñada para pantallas de 1366×768 o mayores.
