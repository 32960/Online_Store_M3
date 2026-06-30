"""
Service functions for review management in the Hop & Barley online store.

This module provides utility functions for:
- Checking if user has purchased a product
- Checking if user has already reviewed a product
- Validating if user can review a product

These functions are used by views to enforce review permissions.
"""
from typing import Any

from django.contrib.auth.models import AbstractUser

from orders.models import OrderItem
from products.models import Product
from reviews.models import Review


def user_bought_product(user: AbstractUser, product: Product) -> bool:
    """
    Check if user has purchased the product.

    Args:
        user: User instance to check.
        product: Product instance to check.

    Returns:
        bool: True if user has purchased the product with
            paid/shipped/delivered status, False otherwise.

    Examples:
        >>> user_bought_product(user, product)
        True
    """
    return OrderItem.objects.filter(
        order__user=user,
        order__status__in=['paid', 'shipped', 'delivered'],
        product=product,
    ).exists()

def user_already_reviewed(user: AbstractUser, product: Product) -> bool:
    """
    Check if user has already reviewed the product.

    Args:
        user: User instance to check.
        product: Product instance to check.

    Returns:
        bool: True if user has already reviewed the product, False otherwise.

    Examples:
        >>> user_already_reviewed(user, product)
        False
    """
    return Review.objects.filter(
        product=product,
        user=user,
    ).exists()

def user_can_review(
    user: AbstractUser,
    product: Product,
) -> tuple[bool, str | None]:
    """
    Check if user can review the product.

    Validates two conditions:
    1. User has purchased the product
    2. User has not already reviewed the product

    Args:
        user: User instance to check.
        product: Product instance to check.

    Returns:
        tuple[bool, str | None]: Tuple containing:
            - can_review: True if user can review, False otherwise
            - error_message: Error message if user cannot review, None otherwise

    Examples:
        >>> can_review, error = user_can_review(user, product)
        >>> can_review
        True
        >>> error
        None
    """
    if not user_bought_product(user, product):
        return False, 'You can only review products you have purchased.'

    if user_already_reviewed(user, product):
        return False, 'You have already reviewed this product.'

    return True, None
