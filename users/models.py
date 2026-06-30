"""
Models for user management in the Hop & Barley online store.

This module defines:
- User: Custom user model with email-based authentication
- Address: User delivery addresses with unique constraints

The User model extends Django's AbstractUser to use email as the primary
authentication field while maintaining username for display purposes.
"""
from typing import Optional

from django.contrib.auth.models import AbstractUser
from django.db import models

from products.models import JournalizedModel


class User(AbstractUser, JournalizedModel):
    """
    Custom user model with email-based authentication.

    Extends Django's AbstractUser to use email as the primary
    authentication field. Inherits timestamp tracking from JournalizedModel.

    Attributes:
        USERNAME_FIELD: Field used for authentication ('email').
        REQUIRED_FIELDS: Fields required when creating superuser.
        email: Unique email address used for authentication.
        phone: Optional phone number for contact.

    Examples:
        >>> user = User.objects.create_user(
        ...     username='john_doe',
        ...     email='john@example.com',
        ...     password='secure_password'
        ... )
        >>> user.get_last_address()
        <Address: John Doe, New York, 123 Main St>
    """
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self) -> str:
        """
        Return string representation of the user.

        Returns:
            str: Username of the user.
        """
        return self.username

    def get_last_address(self) -> Optional['Address']:
        """
        Return the user's most recently created address.

        Returns:
            Optional[Address]: Most recent address or None if no addresses exist.

        Examples:
            >>> user.get_last_address()
            <Address: John Doe, New York, 123 Main St>
        """
        return self.addresses.order_by('-created_at').first()


class Address(JournalizedModel):
    """
    Model representing a user's delivery address.

    Stores complete shipping information for order fulfillment.
    Enforces uniqueness constraint per user to prevent duplicate addresses.

    Attributes:
        user: Foreign key to the user who owns this address.
        full_name: Recipient's full name.
        phone: Contact phone number.
        city: Delivery city.
        shipping_address: Full street address.

    Note:
        UniqueConstraint ensures a user cannot have duplicate addresses
        with the same combination of fields.

    Examples:
        >>> address = Address.objects.create(
        ...     user=user,
        ...     full_name='John Doe',
        ...     phone='+1234567890',
        ...     city='New York',
        ...     shipping_address='123 Main St'
        ... )
    """

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

    def __str__(self) -> str:
        """
        Return string representation of the address.

        Returns:
            str: Formatted address string with name, city, and street.
        """
        return f'{self.full_name}, {self.city}, {self.shipping_address}'
