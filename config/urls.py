from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    # path('api/', include('api.urls', namespace='api')),
    # path('orders/', include('orders.urls', namespace='orders')),
    path('products/', include('products.urls', namespace='products')),
    # path('reviews/', include('reviews.urls', namespace='reviews')),
    # path('users/', include('users.urls', namespace='users')),
]

