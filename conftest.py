"""
Common pytest fixtures for the Hop & Barley project.

Provides reusable test data: users, products, categories, orders, etc.
"""
import io
import pytest
from decimal import Decimal
from PIL import Image
from django.core.files.uploadedfile import SimpleUploadedFile

from django.contrib.auth import get_user_model
from django.test import Client

from products.models import Product, Category
from orders.models import Order, OrderItem
from users.models import Address
from reviews.models import Review


User = get_user_model()


# =============================================================================
# Helper Functions
# =============================================================================

def create_test_image():
    """Create a test image file for product fixtures."""
    image = Image.new('RGB', (100, 100), color='red')
    image_file = io.BytesIO()
    image.save(image_file, 'jpeg')
    image_file.seek(0)
    return SimpleUploadedFile(
        name='test.jpg',
        content=image_file.read(),
        content_type='image/jpeg'
    )


# =============================================================================
# User Fixtures
# =============================================================================

@pytest.fixture
def user(db):
    """Create a regular test user."""
    return User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123',
        first_name='Test',
        last_name='User',
    )


@pytest.fixture
def another_user(db):
    """Create another regular test user."""
    return User.objects.create_user(
        username='anotheruser',
        email='another@example.com',
        password='testpass123',
    )


@pytest.fixture
def admin_user(db):
    """Create an admin/staff user."""
    return User.objects.create_superuser(
        username='admin',
        email='admin@example.com',
        password='adminpass123',
    )


@pytest.fixture
def authenticated_client(client, user):
    """Return a client authenticated as the regular user."""
    client.login(username='test@example.com', password='testpass123')
    return client

@pytest.fixture
def admin_client(client, admin_user):
    """Return a client authenticated as admin."""
    client.login(username='admin@example.com', password='adminpass123')
    return client


# =============================================================================
# Product Fixtures
# =============================================================================

@pytest.fixture
def category(db):
    """Create a test category."""
    return Category.objects.create(
        name='Hops',
        slug='hops',
    )


@pytest.fixture
def another_category(db):
    """Create another test category."""
    return Category.objects.create(
        name='Malt',
        slug='malt',
    )

def create_test_image():
    """Create a test image file."""
    image = Image.new('RGB', (100, 100), color='red')
    image_file = io.BytesIO()
    image.save(image_file, 'jpeg')
    image_file.seek(0)
    return SimpleUploadedFile(
        name='test.jpg',
        content=image_file.read(),
        content_type='image/jpeg'
    )

@pytest.fixture
def product(db, category):
    """Create a test product with image."""
    return Product.objects.create(
        name='Citra Hops',
        slug='citra-hops',
        description='Dual-purpose hops with citrus aroma',
        price=Decimal('14.99'),
        category=category,
        stock=100,
        is_active=True,
        image=create_test_image(),
    )

@pytest.fixture
def another_product(db, category):
    """Create another test product with image."""
    return Product.objects.create(
        name='Simcoe Hops',
        slug='simcoe-hops',
        description='Dual-purpose hops with pine aroma',
        price=Decimal('12.99'),
        category=category,
        stock=50,
        is_active=True,
        image=create_test_image(),
    )

@pytest.fixture
def inactive_product(db, category):
    """Create an inactive product with image."""
    return Product.objects.create(
        name='Inactive Product',
        slug='inactive-product',
        description='This product is not active',
        price=Decimal('9.99'),
        category=category,
        stock=10,
        is_active=False,
        image=create_test_image(),
    )

@pytest.fixture
def low_stock_product(db, category):
    """Create a product with low stock and image."""
    return Product.objects.create(
        name='Low Stock Product',
        slug='low-stock-product',
        description='Only 2 items left',
        price=Decimal('19.99'),
        category=category,
        stock=2,
        is_active=True,
        image=create_test_image(),
    )


# =============================================================================
# Order Fixtures
# =============================================================================

@pytest.fixture
def order(db, user, product):
    """Create a test order with one item."""
    order = Order.objects.create(
        user=user,
        full_name='Test User',
        phone='+1234567890',
        city='New York',
        shipping_address='123 Main St',
        payment_method='debit',
        status='pending',
    )
    OrderItem.objects.create(
        order=order,
        product=product,
        quantity=2,
        price=product.price,
    )
    return order


@pytest.fixture
def paid_order(db, user, product):
    """Create a paid order."""
    order = Order.objects.create(
        user=user,
        full_name='Test User',
        phone='+1234567890',
        city='New York',
        shipping_address='123 Main St',
        payment_method='debit',
        status='paid',
    )
    OrderItem.objects.create(
        order=order,
        product=product,
        quantity=2,
        price=product.price,
    )
    return order


# =============================================================================
# Address Fixtures
# =============================================================================

@pytest.fixture
def address(db, user):
    """Create a test address."""
    return Address.objects.create(
        user=user,
        full_name='Test User',
        phone='+1234567890',
        city='New York',
        shipping_address='123 Main St',
    )


@pytest.fixture
def another_address(db, user):
    """Create another test address for the same user."""
    return Address.objects.create(
        user=user,
        full_name='Test User',
        phone='+1234567890',
        city='Boston',
        shipping_address='456 Oak Ave',
    )


# =============================================================================
# Review Fixtures
# =============================================================================

@pytest.fixture
def review(db, user, product):
    """Create a test review."""
    return Review.objects.create(
        product=product,
        user=user,
        rating=5,
        comment='Excellent product!',
    )
