"""
Views for order management in the Hop & Barley online store.

This module provides views for:
- Shopping cart display and management
- Checkout process with order creation
- Email notifications for orders

All cart operations use session-based storage, while checkout
requires user authentication.
"""
from typing import Any

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.mail import send_mail
from django.db import transaction
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.decorators.http import require_POST
from django.views.generic import FormView

from config.settings import DEFAULT_FROM_EMAIL, ADMIN_EMAIL
from orders.cart import (
    get_cart,
    set_quantity,
    remove_from_cart,
    clear_cart,
    get_cart_items,
    get_cart_total,
)
from orders.forms import CheckoutForm
from orders.models import OrderItem, Order
from products.models import Product
from users.models import Address


def get_cart_view(request: HttpRequest) -> HttpResponse:
    """
    Display shopping cart contents.

    Args:
        request: HTTP request object.

    Returns:
        HttpResponse: Rendered cart template with items and total.
    """
    items = get_cart_items(request)
    total = get_cart_total(request)
    return render(request, 'orders/cart.html', {'items': items, 'total': total})


@require_POST
def add_to_cart_view(request: HttpRequest) -> HttpResponse:
    """
    Add product to shopping cart or update quantity.

    Args:
        request: HTTP request object with product_id and quantity in POST data.

    Returns:
        HttpResponse: Redirect to cart or product page.

    Note:
        If product not found, shows error message.
        If quantity < 1, removes product from cart.
    """
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
def remove_from_cart_view(request: HttpRequest) -> HttpResponse:
    """
    Remove product from shopping cart.

    Args:
        request: HTTP request object with product_id in POST data.

    Returns:
        HttpResponse: Redirect to cart page.

    Note:
        If product not found, shows error message.
    """
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
def clear_cart_view(request: HttpRequest) -> HttpResponse:
    """
    Clear all items from shopping cart.

    Args:
        request: HTTP request object.

    Returns:
        HttpResponse: Redirect to cart page.
    """
    clear_cart(request)
    messages.success(request, 'Cart cleared.')
    return redirect('orders:cart')


class CheckoutView(LoginRequiredMixin, FormView):
    """
    Checkout view for creating orders.

    Handles the complete checkout process:
    - Displays checkout form with autofilled data from user's last address
    - Validates form and creates order
    - Saves address for future orders
    - Clears cart and sends email notifications

    Attributes:
        template_name: Path to checkout template.
        form_class: CheckoutForm for order data.
        success_url: URL to redirect after successful checkout.

    Note:
        Requires user authentication.
        Cart must not be empty.
    """
    template_name = 'orders/checkout.html'
    form_class = CheckoutForm
    success_url = reverse_lazy('orders:cart')

    def get_initial(self) -> dict[str, Any]:
        """
        Autofill form from user's last address.

        Returns:
            dict[str, Any]: Initial form data with address fields.
        """
        initial = super().get_initial()
        last_address = self.request.user.get_last_address()
        if last_address:
            initial['full_name'] = last_address.full_name
            initial['phone'] = last_address.phone
            initial['city'] = last_address.city
            initial['shipping_address'] = last_address.shipping_address
        return initial

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        """
        Handle GET request for checkout page.

        Args:
            request: HTTP request object.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.

        Returns:
            HttpResponse: Rendered checkout page or redirect to cart if empty.
        """
        if not get_cart_items(request):
            messages.warning(request, 'Your cart is empty.')
            return redirect('orders:cart')
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """
        Add cart items and total to template context.

        Args:
            **kwargs: Additional keyword arguments.

        Returns:
            dict[str, Any]: Context with items and total.
        """
        context = super().get_context_data(**kwargs)
        context['items'] = get_cart_items(self.request)
        context['total'] = get_cart_total(self.request)
        return context

    def form_valid(self, form: CheckoutForm) -> HttpResponse:
        """
        Handle valid form submission.

        Creates order, saves address, clears cart, and sends emails.

        Args:
            form: Valid checkout form instance.

        Returns:
            HttpResponse: Redirect to success URL.
        """
        try:
            order = self.create_order(form)
        except ValueError as exc:
            messages.error(self.request, str(exc))
            return redirect('orders:checkout')

        Address.objects.get_or_create(
            user=self.request.user,
            full_name=order.full_name,
            phone=order.phone,
            city=order.city,
            shipping_address=order.shipping_address,
        )

        clear_cart(self.request)
        self.send_emails(order)
        messages.success(self.request, f'Order #{order.id} placed successfully!')
        return super().form_valid(form)

    def form_invalid(self, form: CheckoutForm) -> HttpResponse:
        """
        Handle invalid form submission.

        Args:
            form: Invalid checkout form instance.

        Returns:
            HttpResponse: Re-rendered form with errors.
        """
        messages.error(self.request, 'Please correct the errors in the form.')
        return super().form_invalid(form)

    @transaction.atomic
    def create_order(self, form: CheckoutForm) -> Order:
        """
        Create order from form data and cart contents.

        Performs atomic operation:
        - Creates order with shipping info
        - Creates order items from cart
        - Updates product stock
        - Calculates total price

        Args:
            form: Valid checkout form instance.

        Returns:
            Order: Created order instance.

        Raises:
            ValueError: If cart is empty or stock is insufficient.
        """
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
        order.save(update_fields=['status', 'total_price'])
        return order

    def send_emails(self, order: Order) -> None:
        """
        Send email notifications for order.

        Sends two emails:
        - Confirmation to customer
        - Notification to admin

        Args:
            order: Created order instance.
        """
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
