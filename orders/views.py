from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.mail import send_mail
from django.db import transaction
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.decorators.http import require_POST
from django.views.generic import FormView

from config.settings import DEFAULT_FROM_EMAIL, ADMIN_EMAIL
from orders.cart import get_cart, set_quantity, remove_from_cart, clear_cart, get_cart_items, get_cart_total
from orders.forms import CheckoutForm
from orders.models import OrderItem, Order
from products.models import Product


def get_cart_view(request):
    items = get_cart_items(request)
    total = get_cart_total(request)
    return render(request, 'orders/cart.html', {'items': items, 'total': total})


@require_POST
def add_to_cart_view(request):
    # {1: {'price': price1, 'quantity': quantity1}, ...}
    product_id = request.POST.get('product_id')
    quantity = int(request.POST.get('quantity', 1))

    try:
        product = Product.objects.get(id=product_id)
    except Product.DoesNotExist:
        messages.error(request, 'Product not found')
        return redirect('orders:cart')

    success, message = set_quantity(request, product, quantity)
    if success:
        messages.success(request, message)
    else:
        messages.error(request, message)
    next_url = request.GET.get('next')
    if next_url:
        return redirect(next_url)
    return redirect('products:product-detail', slug=product.slug)


@require_POST
def remove_from_cart_view(request):
    product_id = request.POST.get('product_id')
    try:
        product = Product.objects.get(id=product_id)
    except Product.DoesNotExist:
        messages.error(request, 'Product not found')
        return redirect('orders:cart')

    remove_from_cart(request, product)
    messages.success(request, f'"{product.name}" removed from cart.')
    return redirect('orders:cart')


@require_POST
def clear_cart_view(request):
    clear_cart(request)
    messages.success(request, 'Cart cleared.')
    return redirect('orders:cart')


class CheckoutView(LoginRequiredMixin, FormView):
    template_name = 'orders/checkout.html'
    form_class = CheckoutForm
    success_url = reverse_lazy('orders:cart')

    def get(self, request, *args, **kwargs):
        if not get_cart_items(request):
            messages.warning(request, 'Your cart is empty.')
            return redirect('orders:cart')
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['items'] = get_cart_items(self.request)
        context['total'] = get_cart_total(self.request)
        return context

    def form_valid(self, form: CheckoutForm):
        try:
            order = self.create_order(form)
        except ValueError as exc:
            messages.error(self.request, str(exc))
            return redirect('orders:checkout')

        clear_cart(self.request)
        self.send_emails(order)
        messages.success(self.request, f'Order #{order.id} placed successfully!')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Please correct the errors in the form.')
        return super().form_invalid(form)

    @transaction.atomic
    def create_order(self, form) -> Order:
        order = form.save(commit=False)
        order.user = self.request.user
        order.save()

        cart = get_cart(self.request)
        if not cart:
            raise ValueError('Your cart is empty.')

        products = Product.objects.select_for_update().filter(id__in=cart.keys())
        for product in products:
            quantity = int(cart[str(product.id)]['quantity'])
            if product.stock < quantity:
                raise ValueError(f'Not enough stock for "{product.name}".')

            product.stock -= quantity
            product.save(update_fields=['stock'])

            OrderItem.objects.create(
                order=order, product=product,
                quantity=quantity, price=product.price
            )

        order.status = 'paid'
        order.total_price = get_cart_total(self.request)
        return order

    def send_emails(self, order):
        send_mail(
            'Order Placed',
            f'Thank you for your order! Your order number is {order.id}',
            DEFAULT_FROM_EMAIL,
            [self.request.user.email],
            fail_silently=False,
        )
        send_mail(
            'New Order',
            f'New order placed by {self.request.user.email}. Order number: {order.id}',
            DEFAULT_FROM_EMAIL,
            [ADMIN_EMAIL],
            fail_silently=False,
        )
