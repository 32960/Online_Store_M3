"""
Shopping cart management for the Hop & Barley online store.

This module provides functions for managing shopping cart stored in session:
- Add/update items
- Remove items
- Clear cart
- Calculate totals
- Retrieve cart items with product data

Cart data structure in session:
{
    'cart': {
        '1': {'price': '14.99', 'quantity': 2},
        '3': {'price': '29.99', 'quantity': 1},
    }
}
"""
from decimal import Decimal
from typing import cast

from django.http import HttpRequest

from config.settings import CART_SESSION_KEY
from products.models import Product


def get_cart(request: HttpRequest) -> dict[str, dict[str, str | int]]:
    """
    Get shopping cart from session.

    Args:
        request: HTTP request object.

    Returns:
        dict[str, dict[str, str | int]]: Cart data with product IDs as keys.
            Each item contains 'price' (str) and 'quantity' (int).

    Examples:
        >>> cart = get_cart(request)
        >>> cart
        {'1': {'price': '14.99', 'quantity': 2}}
    """
    cart = request.session.setdefault(CART_SESSION_KEY, {})
    return cast(dict[str, dict[str, str | int]], cart)

def set_quantity(request: HttpRequest, product: Product, quantity: int = 1) -> tuple[bool, str]:
    """
    Set product quantity in cart.

    If quantity < 1, removes product from cart.
    If quantity >= 1, adds or updates product in cart.

    Args:
        request: HTTP request object.
        product: Product instance to add/update.
        quantity: Desired quantity (default: 1).

    Returns:
        tuple[bool, str]: Success flag and message.

    Examples:
        >>> success, message = set_quantity(request, product, 2)
        >>> success
        True
        >>> message
        '"Product Name" added to cart.'
    """
    cart = get_cart(request)

    if product.stock < quantity:
        return False, f'Not enough stock for "{product.name}".'
    if quantity < 1:
        remove_from_cart(request, product)
        return True, f'"{product.name}" removed from cart.'
    cart[str(product.id)] = {'price': str(product.price), 'quantity': quantity,}

    request.session.modified = True
    return True, f'"{product.name}" added to cart.'


def remove_from_cart(request: HttpRequest, product: Product) -> None:
    """
    Remove product from shopping cart.

    Args:
        request: HTTP request object.
        product: Product instance to remove.

    Note:
        If product not in cart, does nothing.
    """
    cart = get_cart(request)
    if str(product.id) not in cart:
        return
    cart.pop(str(product.id), None)
    request.session.modified = True


def clear_cart(request: HttpRequest) -> None:
    """
    Clear all items from shopping cart.

    Args:
        request: HTTP request object.
    """
    request.session.pop(CART_SESSION_KEY, None)
    request.session.modified = True


def get_cart_total(request: HttpRequest) -> Decimal:
    """
    Calculate cart total using actual prices from database.

    Args:
        request: HTTP request object.

    Returns:
        Decimal: Total price rounded to 2 decimal places.

    Examples:
        >>> total = get_cart_total(request)
        >>> total
        Decimal('59.97')
    """
    total = Decimal('0.00')
    for product, quantity in get_cart_items(request):
        total += product.price * quantity
    return total.quantize(Decimal('0.01'))


def get_cart_items(request: HttpRequest) -> list[tuple[Product, int]]:
    """
    Get cart items with product data.

    Args:
        request: HTTP request object.

    Returns:
        list[tuple[Product, int]]: List of (product, quantity) tuples.

    Examples:
        >>> items = get_cart_items(request)
        >>> items
        [(<Product: Product Name>, 2)]
    """
    cart = get_cart(request)
    if not cart:
        return []
    products = Product.objects.filter(id__in=cart.keys()).select_related('category')
    return [(p, int(cart[str(p.id)]['quantity'])) for p in products]
