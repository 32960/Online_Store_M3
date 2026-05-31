from django.contrib import admin
from django.urls import path

from products.views import ProductListView, ProductDetailView, GuidesView

app_name = 'products'

urlpatterns = [
    path('', ProductListView.as_view(), name= 'product-list'),
    path('<int:product_id>/', ProductDetailView.as_view(), name= 'product-detail'),
    path('guides/', GuidesView.as_view(), name= 'guides')
]

