from django.urls import path
from users.views import (
    RegisterView,
    CustomLoginView,
    CustomLogoutView,
    AccountView,
    UpdateProfileView,
    ChangePasswordView,
    AddressListView,
    AddressCreateView,
    AddressUpdateView,
    AddressDeleteView,
    OrderDetailView,
    OrderCancelView,
)

app_name = 'users'

urlpatterns = [
    # Authentication
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', CustomLogoutView.as_view(), name='logout'),

    # Personal Account
    path('account/', AccountView.as_view(), name='account'),
    path('account/update/', UpdateProfileView.as_view(), name='update-profile'),
    path('account/password/', ChangePasswordView.as_view(), name='change-password'),

    # Addresses
    path('account/addresses/', AddressListView.as_view(), name='address-list'),
    path('account/addresses/add/', AddressCreateView.as_view(), name='address-create'),
    path('account/addresses/<int:pk>/edit/', AddressUpdateView.as_view(), name='address-update'),
    path('account/addresses/<int:pk>/delete/', AddressDeleteView.as_view(), name='address-delete'),

    # Orders
    path('account/orders/<int:pk>/', OrderDetailView.as_view(), name='order-detail'),
    path('account/orders/<int:pk>/cancel/', OrderCancelView.as_view(), name='order-cancel'),
]
