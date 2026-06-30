"""
Tests for the products application.

Covers:
- Product and Category models
- Product list and detail views
- Product filtering, searching, and sorting
- Product rating recalculation
"""
import pytest
from decimal import Decimal

from django.urls import reverse

from products.models import Product, Category
from products.services import recalculate_product_rating
from reviews.models import Review
from conftest import create_test_image


# =============================================================================
# Model Tests
# =============================================================================

@pytest.mark.django_db
class TestCategoryModel:
    """Tests for Category model."""

    def test_create_category(self, category):
        """Test category creation."""
        assert category.name == 'Hops'
        assert category.slug == 'hops'
        assert str(category) == 'Hops'

    def test_category_hierarchy(self, category):
        """Test parent-child relationship."""
        subcategory = Category.objects.create(
            name='Aroma Hops',
            slug='aroma-hops',
            parent=category,
        )
        assert subcategory.parent == category
        assert category.subcategories.count() == 1
        assert category.subcategories.first() == subcategory

    def test_category_slug_unique(self, category):
        """Test that slug must be unique."""
        with pytest.raises(Exception):  # IntegrityError
            Category.objects.create(name='Another Hops', slug='hops')


@pytest.mark.django_db
class TestProductModel:
    """Tests for Product model."""

    def test_create_product(self, product, category):
        """Test product creation."""
        assert product.name == 'Citra Hops'
        assert product.slug == 'citra-hops'
        assert product.price == Decimal('14.99')
        assert product.category == category
        assert product.stock == 100
        assert product.is_active is True

    def test_product_str(self, product):
        """Test string representation."""
        assert str(product) == 'Citra Hops'

    def test_product_absolute_url(self, product):
        """Test get_absolute_url method."""
        assert product.get_absolute_url() == '/products/citra-hops/'

    def test_product_default_values(self, db, category):
        """Test default field values."""
        product = Product.objects.create(
            name='Test',
            slug='test',
            description='Test',
            price=Decimal('10.00'),
            category=category,
        )
        assert product.stock == 0
        assert product.is_active is True
        assert product.rating == Decimal('0.0')
        assert product.price_unit == 'per 1 lb'
        assert product.specifications == {}


# =============================================================================
# Service Tests
# =============================================================================

@pytest.mark.django_db
class TestProductRatingService:
    """Tests for product rating recalculation."""

    def test_recalculate_rating_no_reviews(self, product):
        """Test rating with no reviews."""
        recalculate_product_rating(product)
        product.refresh_from_db()
        assert product.rating == Decimal('0.0')

    def test_recalculate_rating_single_review(self, product, user):
        """Test rating with single review."""
        Review.objects.create(
            product=product, user=user, rating=5, comment='Great!'
        )
        recalculate_product_rating(product)
        product.refresh_from_db()
        assert product.rating == Decimal('5.0')

    def test_recalculate_rating_multiple_reviews(self, product, user, another_user):
        """Test rating with multiple reviews."""
        Review.objects.create(product=product, user=user, rating=5, comment='Great!')
        Review.objects.create(product=product, user=another_user, rating=3, comment='OK')
        recalculate_product_rating(product)
        product.refresh_from_db()
        assert product.rating == Decimal('4.0')  # (5+3)/2

    def test_recalculate_rating_rounding(self, product, user, another_user):
        """Test rating is rounded to 1 decimal place."""
        Review.objects.create(product=product, user=user, rating=5, comment='Great!')
        Review.objects.create(product=product, user=another_user, rating=4, comment='Good')
        Review.objects.create(
            product=product,
            user=User.objects.create_user('third', 'third@test.com', 'pass'),
            rating=4,
            comment='Good'
        )
        recalculate_product_rating(product)
        product.refresh_from_db()
        # (5+4+4)/3 = 4.333... → 4.3
        assert product.rating == Decimal('4.3')


# =============================================================================
# View Tests
# =============================================================================

@pytest.mark.django_db
class TestProductListView:
    """Tests for product list view."""

    def test_product_list_status_code(self, client):
        """Test list view returns 200."""
        response = client.get(reverse('products:product-list'))
        assert response.status_code == 200

    def test_product_list_template(self, client):
        """Test correct template is used."""
        response = client.get(reverse('products:product-list'))
        assert 'products/product-list.html' in [t.name for t in response.templates]

    def test_product_list_shows_active_products(self, client, product, inactive_product):
        """Test only active products are shown."""
        response = client.get(reverse('products:product-list'))
        products = list(response.context['products'])
        assert product in products
        assert inactive_product not in products

    def test_product_list_pagination(self, client, category):
        """Test pagination (6 per page)."""
        for i in range(10):
            Product.objects.create(
                name=f'Product {i}',
                slug=f'product-{i}',
                description='Test',
                price=Decimal('10.00'),
                category=category,
                stock=10,
                image=create_test_image(),  # ← ДОБАВЬ ЭТО
            )
        response = client.get(reverse('products:product-list'))
        assert len(response.context['products']) == 6

        response = client.get(reverse('products:product-list') + '?page=2')
        assert len(response.context['products']) == 4

    def test_product_list_filter_by_category(self, client, product, another_product, another_category):
        """Test filtering by category."""
        another_product.category = another_category
        another_product.save()

        response = client.get(
            reverse('products:product-list') + f'?categories={product.category.slug}'
        )
        products = list(response.context['products'])
        assert product in products
        assert another_product not in products

    def test_product_list_search(self, client, product, another_product):
        """Test search functionality."""
        response = client.get(reverse('products:product-list') + '?q=Citra')
        products = list(response.context['products'])
        assert product in products
        assert another_product not in products

    def test_product_list_sorting_price_asc(self, client, product, another_product):
        """Test sorting by price ascending."""
        response = client.get(reverse('products:product-list') + '?sorting=price')
        products = list(response.context['products'])
        assert products[0].price <= products[1].price


@pytest.mark.django_db
class TestProductDetailView:
    """Tests for product detail view."""

    def test_product_detail_status_code(self, client, product):
        """Test detail view returns 200."""
        response = client.get(
            reverse('products:product-detail', kwargs={'slug': product.slug})
        )
        assert response.status_code == 200

    def test_product_detail_template(self, client, product):
        """Test correct template is used."""
        response = client.get(
            reverse('products:product-detail', kwargs={'slug': product.slug})
        )
        assert 'products/product-detail.html' in [t.name for t in response.templates]

    def test_product_detail_context(self, client, product):
        """Test context contains product."""
        response = client.get(
            reverse('products:product-detail', kwargs={'slug': product.slug})
        )
        assert response.context['product'] == product

    def test_product_detail_404_for_nonexistent(self, client):
        """Test 404 for nonexistent product."""
        response = client.get(
            reverse('products:product-detail', kwargs={'slug': 'nonexistent'})
        )
        assert response.status_code == 404

    def test_product_detail_shows_reviews(self, client, product, review):
        """Test reviews are shown in context."""
        response = client.get(
            reverse('products:product-detail', kwargs={'slug': product.slug})
        )
        assert review in response.context['recent_reviews']


# Import User for test_recalculate_rating_rounding
from django.contrib.auth import get_user_model
User = get_user_model()
