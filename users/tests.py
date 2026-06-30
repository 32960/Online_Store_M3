"""
Tests for the users application.

Covers:
- User and Address models
- Registration, login, logout
- Profile and password management
- Address CRUD operations
"""
import pytest

from django.urls import reverse
from django.contrib.auth import get_user_model

from users.models import Address

User = get_user_model()


# =============================================================================
# Model Tests
# =============================================================================

@pytest.mark.django_db
class TestUserModel:
    """Tests for User model."""

    def test_create_user(self, user):
        """Test user creation."""
        assert user.username == 'testuser'
        assert user.email == 'test@example.com'
        assert user.check_password('testpass123')

    def test_user_str(self, user):
        """Test string representation."""
        assert str(user) == 'testuser'

    def test_email_unique(self, user):
        """Test email must be unique."""
        with pytest.raises(Exception):  # IntegrityError
            User.objects.create_user(
                username='another',
                email='test@example.com',
                password='pass123',
            )

    def test_get_last_address(self, user, address, another_address):
        """Test get_last_address returns most recent."""
        last = user.get_last_address()
        assert last == another_address  # Created later


@pytest.mark.django_db
class TestAddressModel:
    """Tests for Address model."""

    def test_create_address(self, address, user):
        """Test address creation."""
        assert address.user == user
        assert address.full_name == 'Test User'
        assert address.city == 'New York'

    def test_address_str(self, address):
        """Test string representation."""
        assert 'Test User' in str(address)
        assert 'New York' in str(address)

    def test_address_unique_constraint(self, user, address):
        """Test unique constraint prevents duplicates."""
        with pytest.raises(Exception):  # IntegrityError
            Address.objects.create(
                user=user,
                full_name=address.full_name,
                phone=address.phone,
                city=address.city,
                shipping_address=address.shipping_address,
            )


# =============================================================================
# View Tests
# =============================================================================

@pytest.mark.django_db
class TestRegistrationView:
    """Tests for user registration."""

    def test_register_page_accessible(self, client):
        """Test registration page loads."""
        response = client.get(reverse('users:register'))
        assert response.status_code == 200

    def test_register_success(self, client):
        """Test successful registration."""
        response = client.post(reverse('users:register'), {
            'username': 'newuser',
            'email': 'new@example.com',
            'password1': 'ComplexPass123!',
            'password2': 'ComplexPass123!',
        })
        assert response.status_code == 302  # Redirect after success
        assert User.objects.filter(username='newuser').exists()

    def test_register_duplicate_email(self, client, user):
        """Test registration with existing email fails."""
        response = client.post(reverse('users:register'), {
            'username': 'newuser',
            'email': user.email,  # Already exists
            'password1': 'ComplexPass123!',
            'password2': 'ComplexPass123!',
        })
        assert response.status_code == 200  # Form error
        assert 'already exists' in response.content.decode()

    def test_register_redirects_authenticated(self, authenticated_client):
        """Test authenticated users are redirected."""
        response = authenticated_client.get(reverse('users:register'))
        assert response.status_code == 302


@pytest.mark.django_db
class TestLoginView:
    """Tests for user login."""

    def test_login_page_accessible(self, client):
        """Test login page loads."""
        response = client.get(reverse('users:login'))
        assert response.status_code == 200

    def test_login_success(self, client, user):
        """Test successful login."""
        response = client.post(reverse('users:login'), {
            'username': user.email,  # Login by email
            'password': 'testpass123',
        })
        assert response.status_code == 302  # Redirect after success

    def test_login_wrong_password(self, client, user):
        """Test login with wrong password fails."""
        response = client.post(reverse('users:login'), {
            'username': user.email,
            'password': 'wrongpassword',
        })
        assert response.status_code == 200  # Form error


@pytest.mark.django_db
class TestLogoutView:
    """Tests for user logout."""

    def test_logout(self, authenticated_client):
        """Test logout works."""
        response = authenticated_client.post(reverse('users:logout'))
        assert response.status_code == 302  # Redirect


@pytest.mark.django_db
class TestAccountView:
    """Tests for account page."""

    def test_account_requires_login(self, client):
        """Test account page requires authentication."""
        response = client.get(reverse('users:account'))
        assert response.status_code == 302  # Redirect to login

    def test_account_accessible(self, authenticated_client, user):
        """Test account page is accessible for authenticated users."""
        response = authenticated_client.get(reverse('users:account'))
        assert response.status_code == 200
        assert response.context['profile_user'] == user

    def test_account_shows_orders(self, authenticated_client, order):
        """Test account page shows user's orders."""
        response = authenticated_client.get(reverse('users:account'))
        assert order in response.context['orders']


@pytest.mark.django_db
class TestAddressViews:
    """Tests for address CRUD views."""

    def test_address_list_requires_login(self, client):
        """Test address list requires authentication."""
        response = client.get(reverse('users:address-list'))
        assert response.status_code == 302

    def test_address_list_accessible(self, authenticated_client, address):
        """Test address list is accessible."""
        response = authenticated_client.get(reverse('users:address-list'))
        assert response.status_code == 200
        assert address in response.context['addresses']

    def test_address_create_requires_login(self, client):
        """Test address creation requires authentication."""
        response = client.get(reverse('users:address-create'))
        assert response.status_code == 302

    def test_address_create_success(self, authenticated_client):
        """Test successful address creation."""
        response = authenticated_client.post(reverse('users:address-create'), {
            'full_name': 'New User',
            'phone': '+987654321',
            'city': 'Boston',
            'shipping_address': '789 Pine St',
        })
        assert response.status_code == 302
        assert Address.objects.filter(city='Boston').exists()

    def test_address_update_own(self, authenticated_client, address):
        """Test user can update own address."""
        response = authenticated_client.post(
            reverse('users:address-update', kwargs={'pk': address.pk}),
            {
                'full_name': 'Updated Name',
                'phone': address.phone,
                'city': address.city,
                'shipping_address': address.shipping_address,
            }
        )
        assert response.status_code == 302
        address.refresh_from_db()
        assert address.full_name == 'Updated Name'

    def test_address_cannot_update_others(self, authenticated_client, another_user):
        """Test user cannot update other's address."""
        other_address = Address.objects.create(
            user=another_user,
            full_name='Other',
            phone='+111',
            city='Other City',
            shipping_address='Other St',
        )
        response = authenticated_client.get(
            reverse('users:address-update', kwargs={'pk': other_address.pk})
        )
        assert response.status_code == 404

    def test_address_delete_own(self, authenticated_client, address):
        """Test user can delete own address."""
        response = authenticated_client.post(
            reverse('users:address-delete', kwargs={'pk': address.pk})
        )
        assert response.status_code == 302
        assert not Address.objects.filter(pk=address.pk).exists()
