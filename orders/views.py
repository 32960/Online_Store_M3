from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from orders.cart import get_cart, set_quantity, remove_from_cart, clear_cart, get_cart_items, get_cart_total
from products.models import Product


def get_cart_view(request):
    cart = get_cart(request)
    items = get_cart_items(request)
    total = get_cart_total(request)
    return render(request, 'orders/cart.html', {'items': items, 'total': total})

@require_POST
@csrf_exempt
def add_to_cart_view(request):
    # {1: {'price': price1, 'quantity': quantity1}, ...}
    product_id = request.POST.get('product_id')
    quantity = int(request.POST.get('quantity', 1))

    try:
        product = Product.objects.get(id=product_id)
    except Product.DoesNotExist:
        return HttpResponse('Product not found', status=404)

    success, message = set_quantity(request, product, quantity)
    if success:
        # messages.success(request, message)
        next_url = request.GET.get('next')
        if next_url:
            return redirect(next_url)
        return redirect('products:product-detail', slug=product.slug)
    # messages.error(request, 'message')
    return HttpResponse(message, status=400)


@require_POST
@csrf_exempt
def remove_from_cart_view(request):
    product_id = request.POST.get('product_id')
    try:
        product = Product.objects.get(id=product_id)
    except Product.DoesNotExist:
        return HttpResponse('Product not found', status=404)
    remove_from_cart(request, product)
    return redirect('orders:cart')


@require_POST
@csrf_exempt
def clear_cart_view(request):
    clear_cart(request)
    return redirect('orders:cart')
