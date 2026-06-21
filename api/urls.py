from django.contrib import admin
from django.urls import path
from rest_framework import routers
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from api.views import ProductViewSet, CategoryViewSet, OrderViewSet, RegisterView, CartAPIView, ProductReviewView

app_name = 'api'

router = routers.DefaultRouter()


router.register('products', ProductViewSet, basename='products')
router.register('categories', CategoryViewSet, basename='categories')
router.register('orders', OrderViewSet, basename='orders')

urlpatterns = router.urls + [
    path('schema/', SpectacularAPIView.as_view(), name='schema'),
    path(
        'docs/',
        SpectacularSwaggerView.as_view(url_name='api:schema'),
        name='docs',
    ),
    path('users/login/', TokenObtainPairView.as_view(), name='login'),
    path('users/refresh/', TokenRefreshView.as_view(), name='refresh'),
    path('users/register/', RegisterView.as_view(), name='register'),
    path('cart/', CartAPIView.as_view(), name='cart'),
    path(
        'products/<int:product_id>/reviews/',
        ProductReviewView.as_view(),
        name='product-reviews',
    ),
]