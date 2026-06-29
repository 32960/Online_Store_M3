from django.contrib.auth.models import AbstractUser
from django.db import models

from products.models import JournalizedModel


class User(AbstractUser, JournalizedModel):
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return self.username

    def get_last_address(self):
        """Returns the user's last address.."""
        return self.addresses.order_by('-created_at').first()


class Address(JournalizedModel):
    """User's delivery address."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='addresses',
    )
    full_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)
    city = models.CharField(max_length=100)
    shipping_address = models.CharField(max_length=255)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Address'
        verbose_name_plural = 'Addresses'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'full_name', 'phone', 'city', 'shipping_address'],
                name='unique_user_address',
            )
        ]

    def __str__(self):
        return f'{self.full_name}, {self.city}, {self.shipping_address}'
