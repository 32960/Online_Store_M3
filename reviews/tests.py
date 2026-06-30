"""
Tests for the reviews application.

Covers:
- Review model
- Review services (permission checks)
- Review creation view
"""
import pytest

from django.urls import reverse
from django.contrib.auth import get_user_model

from reviews.models import Review
from reviews.services import (
    user_bought_product,
    user_already_reviewed,
    user_can_review,
)
from orders.models import Order, OrderItem

User = get_user_model()


# =============================================================================
# Model Tests
# =============================================================================

@pytest.mark.django_db
class TestReviewModel:
    """Tests for Review model."""

    def test_create_review(self, review, user, product):
        """Test review creation."""
        assert review.user == user
        assert review.product == product
        assert review.rating == 5
        assert review.comment == 'Excellent product!'

    def test_review_str(self, review, user, product):
        """Test string representation."""
        expected = f'{user.username} - {product.name} (5/5)'
        assert str(review) == expected

    def test_review_unique_constraint(self, review, another_user, product):
        """Test unique constraint prevents duplicate reviews."""
        # First user already reviewed, second user can review
        Review.objects.create(
            product=product,
            user=another_user,
            rating=4,
            comment='Good',
        )
        assert Review.objects.filter(product=product).count() == 2

    def test_review_same_user_duplicate(self, review, user, product):
        """Test same user cannot review same product twice."""
        with pytest.raises(Exception):  # IntegrityError
            Review.objects.create(
                product=product,
                user=user,
                rating=3,
                comment='Again',
            )


# =============================================================================
# Service Tests
# =============================================================================

@pytest.mark.django_db
class TestReviewServices:
    """Tests for review service functions."""

    def test_user_bought_product_true(self, user, product, order):
        """Test user_bought_product returns True for paid order."""
        order.status = 'paid'
        order.save()
        assert user_bought_product(user, product) is True

    def test_user_bought_product_false_no_order(self, user, product):
        """Test user_bought_product returns False without order."""
        assert user_bought_product(user, product) is False

    def test_user_bought_product_false_pending(self, user, product, order):
        """Test user_bought_product returns False for pending order."""
        assert order.status == 'pending'
        assert user_bought_product(user, product) is False

    def test_user_already_reviewed_true(self, user, product, review):
        """Test user_already_reviewed returns True after review."""
        assert user_already_reviewed(user, product) is True

    def test_user_already_reviewed_false(self, user, product):
        """Test user_already_reviewed returns False without review."""
        assert user_already_reviewed(user, product) is False

    def test_user_can_review_true(self, user, product, order):
        """Test user_can_review returns True when bought and not reviewed."""
        order.status = 'paid'
        order.save()
        can_review, error = user_can_review(user, product)
        assert can_review is True
        assert error is None

    def test_user_can_review_false_not_bought(self, user, product):
        """Test user_can_review returns False when not bought."""
        can_review, error = user_can_review(user, product)
        assert can_review is False
        assert 'purchased' in error.lower()

    def test_user_can_review_false_already_reviewed(self, user, product, order, review):
        """Test user_can_review returns False when already reviewed."""
        order.status = 'paid'
        order.save()
        can_review, error = user_can_review(user, product)
        assert can_review is False
        assert 'already reviewed' in error.lower()


# =============================================================================
# View Tests
# =============================================================================

@pytest.mark.django_db
class TestReviewCreateView:
    """Tests for review creation view."""

    def test_review_requires_login(self, client, product):
        """Test review creation requires authentication."""
        response = client.get(
            reverse('reviews:review-create', kwargs={'slug': product.slug})
        )
        assert response.status_code == 302

    def test_review_requires_purchase(self, authenticated_client, product):
        """Test review creation requires purchase."""
        response = authenticated_client.get(
            reverse('reviews:review-create', kwargs={'slug': product.slug})
        )
        assert response.status_code == 302  # Redirect with error

    def test_review_creation_success(self, authenticated_client, product, order):
        """Test successful review creation."""
        order.status = 'paid'
        order.save()
        response = authenticated_client.post(
            reverse('reviews:review-create', kwargs={'slug': product.slug}),
            {'rating': 5, 'comment': 'Great!'}
        )
        assert response.status_code == 302
        assert Review.objects.filter(product=product, user=order.user).exists()

    def test_review_prevents_duplicate(self, authenticated_client, product, order, review):
        """Test duplicate review is prevented."""
        order.status = 'paid'
        order.save()
        response = authenticated_client.post(
            reverse('reviews:review-create', kwargs={'slug': product.slug}),
            {'rating': 4, 'comment': 'Again'}
        )
        assert response.status_code == 302
        # Still only one review
        assert Review.objects.filter(product=product, user=order.user).count() == 1
