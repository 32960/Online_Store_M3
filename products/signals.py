"""
Django signals for automatic product rating updates.

This module connects Review model signals to automatically
recalculate product ratings when reviews are created or updated.
"""
from typing import Any

from django.db.models.signals import post_save
from django.dispatch import receiver

from reviews.models import Review
from products.services import recalculate_product_rating


@receiver(post_save, sender=Review)
def update_product_rating(
    sender: type[Review],
    instance: Review,
    **kwargs: Any,
) -> None:
    """
    Signal handler to update product rating after review save.

    Automatically recalculates the product's average rating
    whenever a review is created or updated.

    Args:
        sender: Model class that sent the signal (Review).
        instance: Review instance that was saved.
        **kwargs: Additional signal arguments.
    """
    recalculate_product_rating(instance.product)
