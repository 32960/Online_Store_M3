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

from orders.models import Order
from products.models import Product, Category
from products.services import recalculate_product_rating
from reviews.models import Review
from conftest import create_test_image
from django.contrib.auth import get_user_model

User = get_user_model()

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
                image=create_test_image(),
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

# =============================================================================
# Checkout Success View Tests
# =============================================================================


@pytest.mark.django_db
class TestCheckoutSuccessView:
    """Tests for checkout success view."""

    def test_checkout_success_requires_login(self, client, order):
        """Test checkout success page requires authentication."""
        response = client.get(
            reverse('orders:checkout-success', kwargs={'pk': order.pk})
        )
        assert response.status_code == 302
        assert 'login' in response.url.lower()

    def test_checkout_success_accessible(self, authenticated_client, order):
        """Test checkout success page is accessible for authenticated users."""
        response = authenticated_client.get(
            reverse('orders:checkout-success', kwargs={'pk': order.pk})
        )
        assert response.status_code == 200
        assert 'orders/checkout-success.html' in [t.name for t in response.templates]

    def test_checkout_success_shows_order(self, authenticated_client, order):
        """Test checkout success page shows order details."""
        response = authenticated_client.get(
            reverse('orders:checkout-success', kwargs={'pk': order.pk})
        )
        assert response.context['order'] == order
        assert response.context['order'].total_price == order.total_price

    def test_checkout_success_404_for_others_order(
        self, authenticated_client, another_user, product
    ):
        """Test checkout success returns 404 for other user's order."""
        other_order = Order.objects.create(
            user=another_user,
            full_name='Other User',
            phone='+987654321',
            city='Boston',
            shipping_address='456 Oak Ave',
            payment_method='debit',
            status='paid',
        )
        response = authenticated_client.get(
            reverse('orders:checkout-success', kwargs={'pk': other_order.pk})
        )
        assert response.status_code == 404

# =============================================================================
# Cart Views Tests
# =============================================================================


@pytest.mark.django_db
class TestCartViews:
    """Tests for cart views (add, remove, clear)."""

    def test_cart_page_status_code(self, client):
        """Test cart page returns 200."""
        response = client.get(reverse('orders:cart'))
        assert response.status_code == 200

    def test_cart_page_template(self, client):
        """Test correct template is used."""
        response = client.get(reverse('orders:cart'))
        assert 'orders/cart.html' in [t.name for t in response.templates]

    def test_add_to_cart(self, client, product):
        """Test adding product to cart."""
        response = client.post(
            reverse('orders:add_to_cart'),
            {'product_id': product.id, 'quantity': 2}
        )
        assert response.status_code == 302
        cart = client.session.get('cart', {})
        assert str(product.id) in cart
        assert cart[str(product.id)]['quantity'] == 2

    def test_remove_from_cart(self, client, product):
        """Test removing product from cart."""
        # First add
        client.post(
            reverse('orders:add_to_cart'),
            {'product_id': product.id, 'quantity': 2}
        )
        # Then remove
        response = client.post(
            reverse('orders:remove_from_cart'),
            {'product_id': product.id}
        )
        assert response.status_code == 302
        cart = client.session.get('cart', {})
        assert str(product.id) not in cart

    def test_clear_cart(self, client, product, another_product):
        """Test clearing cart."""
        # Add two products
        client.post(
            reverse('orders:add_to_cart'),
            {'product_id': product.id, 'quantity': 2}
        )
        client.post(
            reverse('orders:add_to_cart'),
            {'product_id': another_product.id, 'quantity': 1}
        )
        # Clear cart
        response = client.post(reverse('orders:clear_cart'))
        assert response.status_code == 302
        cart = client.session.get('cart', {})
        assert cart == {}

    def test_add_to_cart_nonexistent_product(self, client):
        """Test adding nonexistent product returns 404."""
        response = client.post(
            reverse('orders:add_to_cart'),
            {'product_id': 99999, 'quantity': 1}
        )
        assert response.status_code == 404

    def test_remove_from_cart_nonexistent_product(self, client):
        """Test removing nonexistent product returns 404."""
        response = client.post(
            reverse('orders:remove_from_cart'),
            {'product_id': 99999}
        )
        assert response.status_code == 404
