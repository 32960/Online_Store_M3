from django.contrib.auth.models import AbstractUser
from django.db import models

from products.models import JournalizedModel


class User(AbstractUser, JournalizedModel):
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True, null=True)