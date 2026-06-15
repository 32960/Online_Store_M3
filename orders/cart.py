from django.http import HttpRequest

from config.settings import CART_SESSION_KEY
from products.models import Product


def get_cart(request: HttpRequest):
    return request.session.setdefault(CART_SESSION_KEY, {})


def set_quantity(request: HttpRequest, product: Product, quantity: int =1) -> tuple[bool, str]:
    cart = get_cart(request)

    if product.stock < quantity:
        return False, 'Not enough stock'
    if quantity < 1:
        return False, 'Quantity must be positive'
    cart[str(product.id)] = {'price': float(product.price), 'quantity': quantity}
    request.session.modified = True
    return True, 'Product added to cart'


def remove_from_cart(request: HttpRequest, product: Product):
    cart = get_cart(request)
    if str(product.id) not in cart:
        return
    cart.pop(str(product.id), None)
    request.session.modified = True


def clear_cart(request: HttpRequest):
    request.session.pop(CART_SESSION_KEY, None)
    request.session.modified = True


def get_cart_total(request: HttpRequest):
    cart = get_cart(request)
    return round(sum(item['price'] * item['quantity'] for item in cart.values()), 2)


def get_cart_items(request: HttpRequest) -> list[tuple[Product, int]]:
    cart = get_cart(request)
    products = Product.objects.filter(id__in=cart)
    return [(p, cart[str(p.id)]['quantity']) for p in products]