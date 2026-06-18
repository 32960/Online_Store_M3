from decimal import Decimal

from django.http import HttpRequest

from config.settings import CART_SESSION_KEY
from products.models import Product


def get_cart(request: HttpRequest) -> dict[str, dict[str, str | int]]:
    return request.session.setdefault(CART_SESSION_KEY, {})


def set_quantity(request: HttpRequest, product: Product, quantity: int =1) -> tuple[bool, str]:
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
    cart = get_cart(request)
    if str(product.id) not in cart:
        return
    cart.pop(str(product.id), None)
    request.session.modified = True


def clear_cart(request: HttpRequest) -> None:
    request.session.pop(CART_SESSION_KEY, None)
    request.session.modified = True


def get_cart_total(request: HttpRequest) -> None:
    cart = get_cart(request)
    total = sum(
        (
            Decimal(str(item['price'])) * int(item['quantity'])
            for item in cart.values()
        ),
        Decimal('0.00'),
    )
    return total.quantize(Decimal('0.01'))


def get_cart_items(request: HttpRequest) -> list[tuple[Product, int]]:
    cart = get_cart(request)
    products = Product.objects.filter(id__in=cart.keys())
    return [(p, int(cart[str(p.id)]['quantity'])) for p in products]
