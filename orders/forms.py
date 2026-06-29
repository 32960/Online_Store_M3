from django import forms

from orders.models import Order


class CheckoutForm(forms.ModelForm):

    class Meta:
        model = Order
        fields = ['full_name', 'phone', 'city', 'shipping_address', 'payment_method']
        # required = ['full_name', 'phone', 'city', 'shipping_address', 'payment_method']
        widgets = {
            'shipping_address': forms.Textarea(attrs={'rows': 3, 'class': 'Textarea', 'placeholder': 'Lenina st., 18, apt. 9'}),
            'payment_method': forms.RadioSelect(attrs={'class': 'Input'}),
            'full_name': forms.TextInput(attrs={'class': 'Input', 'placeholder': 'Ivanov Ivan'}),
            'phone': forms.TextInput(attrs={'class': 'Input', 'placeholder': '+7 123 456 7890'}),
            'city': forms.TextInput(attrs={'class': 'Input', 'placeholder': 'Moscow'}),
        }
