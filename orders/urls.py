from django.contrib import admin
from django.urls import path

from orders.views import get_cart_view, add_to_cart_view, remove_from_cart_view, clear_cart_view

app_name = 'orders'

urlpatterns = [
    path('cart/', get_cart_view,  name= 'cart'),
    path('cart/add/', add_to_cart_view, name='add_to_cart'),
    path('cart/remove/', remove_from_cart_view, name='remove_from_cart'),
    path('cart/clear/', clear_cart_view, name='clear_cart'),
    # path('cart/total', get_cart_total, name='get_cart_total'),
]

