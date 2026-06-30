"""
Models for product reviews in the Hop & Barley online store.

This module defines:
- Review: User reviews for products with ratings and comments

Reviews are tied to both products and users, with a unique constraint
ensuring each user can only review a product once.
"""
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models


class Review(models.Model):
    """
    Model representing a user's review of a product.

    Stores rating (1-5), comment, and relationships to product and user.
    Enforces uniqueness constraint to prevent duplicate reviews.

    Attributes:
        product: Foreign key to the reviewed product.
        user: Foreign key to the user who wrote the review.
        rating: Integer rating from 1 to 5.
        comment: Text content of the review.
        created_at: Timestamp when the review was created (auto-set).

    Note:
        UniqueConstraint ensures a user cannot review the same product twice.
        Rating is validated to be between 1 and 5.

    Examples:
        >>> review = Review.objects.create(
        ...     product=product,
        ...     user=user,
        ...     rating=5,
        ...     comment='Excellent product!'
        ... )
        >>> str(review)
        'john_doe - Citra Hops (5/5)'
    """
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name='reviews')
    rating = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        """
        Return string representation of the review.

        Returns:
            str: Formatted string with username, product name, and rating.
        """
        return f'{self.user.username} - {self.product.name} ({self.rating}/5)'

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['product', 'user'],
                name='unique_product_user_review',
            )
        ]
