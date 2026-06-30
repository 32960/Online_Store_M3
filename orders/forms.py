"""
Forms for order management in the Hop & Barley online store.

This module provides forms for:
- Checkout process with shipping and payment information
"""
from django import forms

from orders.models import Order


class CheckoutForm(forms.ModelForm):
    """
    Form for checkout process.

    Collects shipping information and payment method from the user.
    Uses custom widgets with placeholders and styling classes.

    Attributes:
        model: Order model class.
        fields: List of fields to include in the form.
        widgets: Custom widget configurations for each field.

    Examples:
        >>> form = CheckoutForm(data={
        ...     'full_name': 'John Doe',
        ...     'phone': '+1234567890',
        ...     'city': 'New York',
        ...     'shipping_address': '123 Main St',
        ...     'payment_method': 'debit'
        ... })
        >>> form.is_valid()
        True
    """
    class Meta:
        model = Order
        fields = ['full_name', 'phone', 'city', 'shipping_address', 'payment_method']
        widgets = {
            'shipping_address': forms.Textarea(attrs={'rows': 3, 'class': 'Textarea', 'placeholder': 'Lenina st., 18, apt. 9'}),
            'payment_method': forms.RadioSelect(attrs={'class': 'Input'}),
            'full_name': forms.TextInput(attrs={'class': 'Input', 'placeholder': 'Ivanov Ivan'}),
            'phone': forms.TextInput(attrs={'class': 'Input', 'placeholder': '+7 123 456 7890'}),
            'city': forms.TextInput(attrs={'class': 'Input', 'placeholder': 'Moscow'}),
        }
