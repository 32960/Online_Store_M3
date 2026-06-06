from django.contrib import admin
from django.urls import path

from orders.views import cart_mock

app_name = 'orders'

urlpatterns = [
    path('cart/', cart_mock,  name= 'cart')
]

