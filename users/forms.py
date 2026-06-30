"""
Forms for user management in the Hop & Barley online store.

This module provides forms for:
- User registration with email validation
- Profile editing with email uniqueness check
- Password change with custom styling
- Email-based authentication
- Address creation and editing
"""
from typing import Any

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import (
    PasswordChangeForm,
    UserCreationForm,
    AuthenticationForm,
)

from users.models import Address

User = get_user_model()


class RegisterForm(UserCreationForm):
    """
    Form for new user registration.

    Extends UserCreationForm with email field and custom styling.
    Validates email uniqueness during registration.

    Attributes:
        email: Required email field with custom widget.
        model: User model class.
        fields: List of fields to include in the form.
        widgets: Custom widget configurations.

    Examples:
        >>> form = RegisterForm(data={
        ...     'username': 'john_doe',
        ...     'email': 'john@example.com',
        ...     'password1': 'secure_password',
        ...     'password2': 'secure_password'
        ... })
        >>> form.is_valid()
        True
    """

    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'Input', 'placeholder': 'Email'})
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'Input', 'placeholder': 'Username'}),
        }

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """
        Initialize form with custom widget classes for password fields.

        Args:
            *args: Positional arguments for form initialization.
            **kwargs: Keyword arguments for form initialization.
        """
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs['class'] = 'Input'
        self.fields['password2'].widget.attrs['class'] = 'Input'

    def clean_email(self) -> str:
        """
        Validate email uniqueness during registration.

        Returns:
            str: Validated email address.

        Raises:
            forms.ValidationError: If email already exists.
        """
        email = self.cleaned_data.get('email')
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('A user with this email already exists.')
        return email


class EditProfileForm(forms.ModelForm):
    """
    Form for editing user profile information.

    Allows updating first name, last name, email, and phone.
    Validates email uniqueness while allowing users to keep their current email.

    Attributes:
        model: User model class.
        fields: List of fields to include in the form.
        widgets: Custom widget configurations with placeholders.

    Examples:
        >>> form = EditProfileForm(instance=user, data={
        ...     'first_name': 'John',
        ...     'last_name': 'Doe',
        ...     'email': 'john@example.com',
        ...     'phone': '+1234567890'
        ... })
        >>> form.is_valid()
        True
    """

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'Input', 'placeholder': 'First name'}),
            'last_name': forms.TextInput(attrs={'class': 'Input', 'placeholder': 'Last name'}),
            'email': forms.EmailInput(attrs={'class': 'Input', 'placeholder': 'Email'}),
            'phone': forms.TextInput(attrs={'class': 'Input', 'placeholder': '+1 (234) 567-8900'}),
        }

    def clean_email(self) -> str:
        """
        Validate email uniqueness during profile editing.

        Allows users to keep their current email but prevents
        changing to an email that already exists.

        Returns:
            str: Validated email address.

        Raises:
            forms.ValidationError: If email already exists for another user.
        """
        email = self.cleaned_data.get('email')
        user = self.instance

        if user.email and email.lower() == user.email.lower():
            return email

        if User.objects.filter(email__iexact=email).exclude(pk=user.pk).exists():
            raise forms.ValidationError('A user with this email already exists.')

        return email


class CustomPasswordChangeForm(PasswordChangeForm):
    """
    Form for changing user password with custom styling.

    Extends Django's PasswordChangeForm with custom CSS classes
    for consistent styling across the application.

    Note:
        All fields receive the 'Input' CSS class for styling.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """
        Initialize form with custom widget classes for all fields.

        Args:
            *args: Positional arguments for form initialization.
            **kwargs: Keyword arguments for form initialization.
        """
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'Input'


class EmailAuthenticationForm(AuthenticationForm):
    """
    Email-based authentication form.

    Extends Django's AuthenticationForm to use email instead of username
    for authentication. Customized with placeholder and autocomplete attributes.

    Attributes:
        username: Email field configured for authentication.

    Note:
        Despite the field name 'username', this form uses email for authentication
        due to User.USERNAME_FIELD = 'email'.
    """
    username = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={
            'class': 'Input',
            'placeholder': 'your@email.com',
            'autofocus': True,
            'autocomplete': 'email',
        })
    )


class AddressForm(forms.ModelForm):
    """
    Form for creating and editing user addresses.

    Collects complete shipping information including recipient name,
    phone, city, and street address.

    Attributes:
        model: Address model class.
        fields: List of fields to include in the form.
        widgets: Custom widget configurations with placeholders.

    Examples:
        >>> form = AddressForm(data={
        ...     'full_name': 'John Doe',
        ...     'phone': '+1234567890',
        ...     'city': 'New York',
        ...     'shipping_address': '123 Main St'
        ... })
        >>> form.is_valid()
        True
    """

    class Meta:
        model = Address
        fields = ['full_name', 'phone', 'city', 'shipping_address']
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'Input', 'placeholder': 'John Doe'}),
            'phone': forms.TextInput(attrs={'class': 'Input', 'placeholder': '+1 (234) 567-8900'}),
            'city': forms.TextInput(attrs={'class': 'Input', 'placeholder': 'New York'}),
            'shipping_address': forms.TextInput(attrs={'class': 'Input', 'placeholder': '123 Main Street'}),
        }
