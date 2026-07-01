"""
Tests for the REST API.

Covers:
- Product endpoints
- Order endpoints
- Cart endpoints
- JWT authentication
"""
import pytest

from django.urls import reverse
from django.contrib.auth import get_user_model

from rest_framework import status
from rest_framework.test import APIClient

User = get_user_model()


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def api_client():
    """Return an unauthenticated API client."""
    return APIClient()


@pytest.fixture
def authenticated_api_client(user):
    """Return an API client authenticated with JWT."""
    client = APIClient()
    client.force_authenticate(user=user)
    return client


# =============================================================================
# Product API Tests
# =============================================================================

@pytest.mark.django_db
class TestProductAPI:
    """Tests for product API endpoints."""

    def test_list_products(self, api_client, product):
        """Test listing products."""
        url = reverse('api:products-list')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) >= 1

    def test_retrieve_product(self, api_client, product):
        """Test retrieving product details."""
        url = reverse('api:products-detail', kwargs={'pk': product.pk})  # ✅
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == product.name

    def test_list_products_filter_by_category(self, api_client, product, another_product, another_category):
        """Test filtering products by category."""
        another_product.category = another_category
        another_product.save()
        url = reverse('api:products-list') + f'?category__slug={product.category.slug}'
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        names = [p['name'] for p in response.data['results']]
        assert product.name in names
        assert another_product.name not in names

    def test_list_products_search(self, api_client, product, another_product):
        """Test searching products."""
        url = reverse('api:products-list') + '?search=Citra'
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        names = [p['name'] for p in response.data['results']]
        assert product.name in names
        assert another_product.name not in names


@pytest.mark.django_db
class TestCategoryAPI:
    """Tests for category API endpoints."""

    def test_list_categories(self, api_client, category):
        """Test listing categories."""
        url = reverse('api:categories-list')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) >= 1

    def test_retrieve_category(self, api_client, category):
        """Test retrieving category details."""
        url = reverse('api:categories-detail', kwargs={'pk': category.pk})
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == category.name


# =============================================================================
# Order API Tests
# =============================================================================

@pytest.mark.django_db
class TestOrderAPI:
    """Tests for order API endpoints."""

    def test_list_orders_requires_auth(self, api_client):
        """Test listing orders requires authentication."""
        url = reverse('api:orders-list')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_list_orders(self, authenticated_api_client, order):
        """Test listing user's orders."""
        url = reverse('api:orders-list')
        response = authenticated_api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1

    def test_create_order(self, authenticated_api_client, product):
        """Test creating an order."""
        url = reverse('api:orders-list')
        data = {
            'full_name': 'Test User',
            'phone': '+1234567890',
            'city': 'New York',
            'shipping_address': '123 Main St',
            'payment_method': 'debit',
            'items': [{'product': product.id, 'quantity': 2}],
        }
        response = authenticated_api_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['full_name'] == 'Test User'

    def test_create_order_insufficient_stock(self, authenticated_api_client, product):
        """Test creating order with insufficient stock."""
        url = reverse('api:orders-list')
        data = {
            'full_name': 'Test User',
            'phone': '+1234567890',
            'city': 'New York',
            'shipping_address': '123 Main St',
            'payment_method': 'debit',
            'items': [{'product': product.id, 'quantity': 1000}],  # More than stock
        }
        response = authenticated_api_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_cancel_order(self, authenticated_api_client, order):
        """Test cancelling an order."""
        url = reverse('api:orders-detail', kwargs={'pk': order.pk})
        response = authenticated_api_client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        order.refresh_from_db()
        assert order.status == 'cancelled'


# =============================================================================
# Cart API Tests
# =============================================================================

@pytest.mark.django_db
class TestCartAPI:
    """Tests for cart API endpoints."""

    def test_get_empty_cart(self, api_client):
        """Test getting empty cart."""
        url = reverse('api:cart')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['items'] == []

    def test_add_to_cart(self, api_client, product):
        """Test adding item to cart."""
        url = reverse('api:cart')
        data = {'product': product.id, 'quantity': 2}
        response = api_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert len(response.data['items']) == 1

    def test_add_to_cart_insufficient_stock(self, api_client, product):
        """Test adding more than stock allows."""
        url = reverse('api:cart')
        data = {'product': product.id, 'quantity': 1000}
        response = api_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST


# =============================================================================
# Authentication API Tests
# =============================================================================

@pytest.mark.django_db
class TestAuthenticationAPI:
    """Tests for authentication API endpoints."""

    def test_register_user(self, api_client):
        """Test user registration."""
        url = reverse('api:register')
        data = {
            'username': 'newuser',
            'email': 'new@example.com',
            'password': 'ComplexPass123!',
        }
        response = api_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert User.objects.filter(username='newuser').exists()

    def test_obtain_jwt_tokens(self, api_client, user):
        """Test obtaining JWT tokens."""
        url = reverse('api:login')
        data = {
            'email': user.email,
            'password': 'testpass123',
        }
        response = api_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert 'access' in response.data
        assert 'refresh' in response.data

    def test_refresh_jwt_token(self, api_client, user):
        """Test refreshing JWT token."""
        # First obtain tokens
        obtain_url = reverse('api:login')
        obtain_response = api_client.post(obtain_url, {
            'email': user.email,
            'password': 'testpass123',
        }, format='json')
        refresh_token = obtain_response.data['refresh']

        # Then refresh
        refresh_url = reverse('api:refresh')
        response = api_client.post(refresh_url, {'refresh': refresh_token}, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert 'access' in response.data

    def test_authenticated_endpoint_with_jwt(self, api_client, user, product):
        """Test accessing authenticated endpoint with JWT."""
        # Obtain token
        obtain_url = reverse('api:login')
        obtain_response = api_client.post(obtain_url, {
            'email': user.email,
            'password': 'testpass123',
        }, format='json')
        access_token = obtain_response.data['access']

        # Use token to access orders
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        url = reverse('api:orders-list')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
