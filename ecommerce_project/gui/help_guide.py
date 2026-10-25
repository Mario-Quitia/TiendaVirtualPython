"""Texto de la guía de uso que se muestra con el botón Ayuda (F1)."""

USER_GUIDE = """\
INICIO RÁPIDO
-------------
1. Registre o elija un producto en el panel izquierdo / tabla de Inventario.
2. Elíjalo en "Agregar artículos", indique la cantidad y pulse "Agregar".
3. Si lo desea, aplique un descuento, un cupón o el beneficio prémium.
4. Pulse "Finalizar compra" para completar la compra (simulada).
Consejo: deje el mouse sobre cualquier campo o botón para ver una ayuda breve.

1. REGISTRAR UN PRODUCTO (panel izquierdo)
------------------------------------------
- Complete Nombre del producto, Precio ($), Existencias y Descuento promocional (%).
- Elija la Categoría del producto. Cada categoría muestra campos adicionales:
    Electrónica -> Garantía (meses) y Depreciación (%)
    Alimentos   -> Fecha de vencimiento (formato AAAA-MM-DD, p. ej. 2026-12-31)
    Ropa        -> Talla (XS..XXL) y Color
- Pulse "Agregar producto". El ID (P001, P002...) se crea automáticamente.

2. EDITAR, ELIMINAR O CONSULTAR UN PRODUCTO
-------------------------------------------
- Haga clic en una fila de la tabla de Inventario: sus datos se cargan en el formulario.
- Cambie los valores y pulse "Actualizar producto" para guardarlos.
- "Eliminar producto" lo borra (se le pedirá confirmación).
- "Ver detalles" muestra el desglose de precios y la regla de descuento.
- "Limpiar formulario" quita la selección para registrar un producto nuevo.
- Un producto que está en el carrito no se puede actualizar ni eliminar;
  primero quítelo del carrito. Las filas en rojo no tienen existencias.

3. USAR EL CARRITO DE COMPRAS
-----------------------------
- Agregar artículos: elija un producto (el número entre [ ] son las
  existencias restantes), escriba la Cantidad y pulse "Agregar".
- Para cambiar o quitar una línea, primero haga clic en ella en la tabla
  del carrito y luego use "Actualizar" o "Quitar".
- El carrito nunca acepta más unidades que las existencias disponibles.

4. PROMOCIONES
--------------
- Descuento (%): descuento general del pedido. Cada producto usa el mayor
  entre este valor y su propio descuento promocional.
- Cupón (%): porcentaje adicional de cupón. Déjelo vacío y pulse
  "Aplicar" para quitarlo.
- Cliente prémium: agrega un beneficio del 5%.
- Cada categoría combina las ofertas a su manera:
    Electrónica: primero la depreciación y luego solo la mejor oferta.
    Alimentos:   las ofertas se combinan, pero el total tiene un tope de 15%.
    Ropa:        las ofertas se acumulan una tras otra, máximo 40%.

5. FINALIZAR LA COMPRA
----------------------
- El Resumen del pedido muestra el Subtotal, el Descuento total y el Total final.
- "Finalizar compra" pide confirmación, muestra un recibo y descuenta las
  unidades vendidas del inventario. No se procesa ningún pago real.
- "Vaciar carrito" vacía el carrito y restablece las promociones.

MENSAJES
--------
La barra inferior de la ventana confirma cada acción (verde) o explica
qué salió mal (rojo). Las ventanas de error indican qué campo corregir.

Teclado: F1 abre esta guía y Esc la cierra.
"""
