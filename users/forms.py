from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import PasswordChangeForm, UserCreationForm
from django.contrib.auth.forms import AuthenticationForm
from users.models import Address

User = get_user_model()


class RegisterForm(UserCreationForm):
    """New user registration form."""

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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs['class'] = 'Input'
        self.fields['password2'].widget.attrs['class'] = 'Input'

    def clean_email(self):
        """Email uniqueness check during registration."""
        email = self.cleaned_data.get('email')
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('A user with this email already exists.')
        return email


class EditProfileForm(forms.ModelForm):
    """User profile editing form."""

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'Input', 'placeholder': 'First name'}),
            'last_name': forms.TextInput(attrs={'class': 'Input', 'placeholder': 'Last name'}),
            'email': forms.EmailInput(attrs={'class': 'Input', 'placeholder': 'Email'}),
            'phone': forms.TextInput(attrs={'class': 'Input', 'placeholder': '+1 (234) 567-8900'}),
        }

    def clean_email(self):
        """Email uniqueness check during editing."""
        email = self.cleaned_data.get('email')
        user = self.instance

        if user.email and email.lower() == user.email.lower():
            return email

        if User.objects.filter(email__iexact=email).exclude(pk=user.pk).exists():
            raise forms.ValidationError('A user with this email already exists.')

        return email


class CustomPasswordChangeForm(PasswordChangeForm):
    """Password change form with custom styles."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'Input'


class EmailAuthenticationForm(AuthenticationForm):
    """
    Email-based login form.
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
    """Form for creating/editing an address."""

    class Meta:
        model = Address
        fields = ['full_name', 'phone', 'city', 'shipping_address']
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'Input', 'placeholder': 'John Doe'}),
            'phone': forms.TextInput(attrs={'class': 'Input', 'placeholder': '+1 (234) 567-8900'}),
            'city': forms.TextInput(attrs={'class': 'Input', 'placeholder': 'New York'}),
            'shipping_address': forms.TextInput(attrs={'class': 'Input', 'placeholder': '123 Main Street'}),
        }