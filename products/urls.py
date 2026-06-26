from django.contrib import admin
from django.urls import path

from products.views import ProductListView, ProductDetailView, GuidesView

app_name = 'products'

urlpatterns = [
    path('', ProductListView.as_view(), name= 'product-list'),
    path('guides/', GuidesView.as_view(), name= 'guides'),
    path('<slug:slug>/', ProductDetailView.as_view(), name= 'product-detail'),
]
