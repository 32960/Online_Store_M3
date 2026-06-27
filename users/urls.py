from django.contrib import admin
from django.urls import path

from users.views import profile_mock, login_mock

app_name = 'users'

urlpatterns = [
    path('profile/', profile_mock, name= 'profile'),
    path('login/', login_mock, name='login'),
]
