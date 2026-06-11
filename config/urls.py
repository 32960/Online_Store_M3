from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static

from config import settings
from products.views import ProductListView

urlpatterns = [
    path('', ProductListView.as_view()),
    path('admin/', admin.site.urls),
    # path('api/', include('api.urls', namespace='api')),
    path('orders/', include('orders.urls', namespace='orders')),
    path('products/', include('products.urls', namespace='products')),
    path('reviews/', include('reviews.urls', namespace='reviews')),
    path('users/', include('users.urls', namespace='users')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
