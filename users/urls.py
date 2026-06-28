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
)
from django.contrib.auth import views as auth_views
from django.urls import reverse_lazy

app_name = 'users'

urlpatterns = [
    # Аутентификация
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', CustomLogoutView.as_view(), name='logout'),

    # Password Reset
    path('forgot-password/',
         auth_views.PasswordResetView.as_view(
             template_name='users/forgot_password.html',
             email_template_name='users/password_reset_email.html',
             subject_template_name='users/password_reset_subject.txt',
             success_url=reverse_lazy('users:password_reset_done'),
         ),
         name='forgot-password'),

    path('forgot-password/done/',
         auth_views.PasswordResetDoneView.as_view(
             template_name='users/password_reset_done.html',
         ),
         name='password_reset_done'),

    path('reset-password/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(
             template_name='users/reset_password.html',
             success_url=reverse_lazy('users:password_reset_complete'),
         ),
         name='password_reset_confirm'),

    path('reset-password/done/',
         auth_views.PasswordResetCompleteView.as_view(
             template_name='users/reset_password_complete.html',
         ),
         name='password_reset_complete'),

    # Личный кабинет
    path('account/', AccountView.as_view(), name='account'),
    path('account/update/', UpdateProfileView.as_view(), name='update-profile'),
    path('account/password/', ChangePasswordView.as_view(), name='change-password'),

    # Адреса
    path('account/addresses/', AddressListView.as_view(), name='address-list'),
    path('account/addresses/add/', AddressCreateView.as_view(), name='address-create'),
    path('account/addresses/<int:pk>/edit/', AddressUpdateView.as_view(), name='address-update'),
    path('account/addresses/<int:pk>/delete/', AddressDeleteView.as_view(), name='address-delete'),
]
