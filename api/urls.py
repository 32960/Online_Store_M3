"""
URL configuration for the Hop & Barley API.

This module defines all API endpoints using Django REST Framework routers
and includes JWT authentication, Swagger documentation, and custom views.

Endpoints:
    Products:
        - GET /api/products/ - List all products
        - GET /api/products/{slug}/ - Retrieve product details

    Categories:
        - GET /api/categories/ - List all categories
        - GET /api/categories/{id}/ - Retrieve category details

    Orders (JWT required):
        - GET /api/orders/ - List user's orders
        - POST /api/orders/ - Create new order
        - GET /api/orders/{id}/ - Retrieve order details
        - PUT /api/orders/{id}/ - Update order
        - DELETE /api/orders/{id}/ - Cancel order

    Authentication:
        - POST /api/users/login/ - Obtain JWT tokens
        - POST /api/users/refresh/ - Refresh access token
        - POST /api/users/register/ - Register new user

    Cart:
        - GET /api/cart/ - Retrieve cart contents
        - POST /api/cart/ - Add item to cart
        - PATCH /api/cart/ - Update item quantity
        - DELETE /api/cart/ - Remove item or clear cart

    Reviews:
        - GET /api/products/{id}/reviews/ - List product reviews
        - POST /api/products/{id}/reviews/ - Create review

    Documentation:
        - GET /api/schema/ - OpenAPI schema (YAML/JSON)
        - GET /api/docs/ - Swagger UI
        - GET /api/redoc/ - ReDoc UI
"""
from django.urls import path
from rest_framework import routers
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

from api.views import ProductViewSet, CategoryViewSet, OrderViewSet, RegisterView, CartAPIView, ProductReviewView

app_name = 'api'

# Initialize DRF router for viewsets
router = routers.DefaultRouter()

# Register viewsets
router.register('products', ProductViewSet, basename='products')
router.register('categories', CategoryViewSet, basename='categories')
router.register('orders', OrderViewSet, basename='orders')

# URL patterns
urlpatterns = router.urls + [
    # API Documentation
    path('schema/', SpectacularAPIView.as_view(), name='schema'),
    path('docs/', SpectacularSwaggerView.as_view(url_name='api:schema'), name='docs'),
    path('redoc/', SpectacularRedocView.as_view(url_name='api:schema'), name='redoc'),

    # Authentication
    path('users/login/', TokenObtainPairView.as_view(), name='login'),
    path('users/refresh/', TokenRefreshView.as_view(), name='refresh'),
    path('users/register/', RegisterView.as_view(), name='register'),

    # Cart
    path('cart/', CartAPIView.as_view(), name='cart'),

    # Reviews
    path(
        'products/<int:product_id>/reviews/',
        ProductReviewView.as_view(),
        name='product-reviews',
    ),
]
