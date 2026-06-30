"""
Service functions for product management in the Hop & Barley online store.

This module provides utility functions for:
- Product rating calculation based on reviews
"""
from decimal import Decimal

from django.db.models import Avg

from products.models import Product
from reviews.models import Review


def recalculate_product_rating(product: Product) -> None:
    """
    Update product rating based on all reviews.

    Calculates average rating from all reviews for the product
    and updates the product's rating field. Rating is rounded
    to 1 decimal place.

    Args:
        product: Product instance to update.

    Note:
        This function is automatically called when a review
        is created or updated via Django signals.

    Examples:
        >>> recalculate_product_rating(product)
        >>> product.rating
        Decimal('4.5')
    """
    rating = Review.objects.filter(product=product).aggregate(
        value=Avg('rating'),
    )['value']

    product.rating = Decimal(str(rating or 0)).quantize(Decimal('0.1'))
    product.save(update_fields=['rating'])
