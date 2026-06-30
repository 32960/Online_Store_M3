"""
Views for user management in the Hop & Barley online store.

This module provides views for:
- User registration, login, and logout
- Personal account with tabbed interface
- Profile and password management
- Address CRUD operations
- Order viewing and cancellation

All account-related views require authentication via LoginRequiredMixin.
"""
from typing import Any

from django.contrib import messages
from django.contrib.auth import get_user_model, login, update_session_auth_hash
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import QuerySet
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import (
    UpdateView, DetailView, CreateView, FormView, ListView, DeleteView,
)

from orders.models import Order
from users.forms import (
    EditProfileForm,
    CustomPasswordChangeForm,
    EmailAuthenticationForm,
    RegisterForm,
    AddressForm,
)
from users.models import Address
from django.contrib.auth.models import AbstractUser

User = get_user_model()


class RegisterView(CreateView):
    """
    View for new user registration.

    Handles user registration with automatic login after successful
    registration. Redirects authenticated users to product list.

    Attributes:
        form_class: RegisterForm for user registration.
        template_name: Path to registration template.
        success_url: URL to redirect after successful registration.

    Note:
        Automatically logs in the user after registration.
    """
    form_class = RegisterForm
    template_name = 'users/register.html'
    success_url = reverse_lazy('products:product-list')

    def form_valid(self, form: RegisterForm) -> HttpResponse:
        """
        Handle valid registration form submission.

        Logs in the user after successful registration and shows
        success message.

        Args:
            form: Valid registration form instance.

        Returns:
            HttpResponse: Redirect to success URL.
        """
        response = super().form_valid(form)
        login(self.request, self.object)
        messages.success(self.request, 'Registration successful! Welcome!')
        return response

    def dispatch(
            self,
            request: HttpRequest,
            *args: Any,
            **kwargs: Any,
    ) -> HttpResponse:
        """
        Handle request dispatch with authentication check.

        Redirects authenticated users to product list.

        Args:
            request: HTTP request object.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.

        Returns:
            HttpResponse: Redirect or dispatched response.
        """
        if request.user.is_authenticated:
            return redirect('products:product-list')
        return super().dispatch(request, *args, **kwargs)


class CustomLoginView(LoginView):
    """
    View for user login with email authentication.

    Uses EmailAuthenticationForm for email-based login.
    Supports 'next' parameter for redirect after login.

    Attributes:
        template_name: Path to login template.
        authentication_form: Form class for authentication.
    """
    template_name = 'users/login.html'
    authentication_form = EmailAuthenticationForm

    def get_success_url(self) -> str:
        """
        Determine redirect URL after successful login.

        Uses 'next' parameter if provided, otherwise redirects
        to product list.

        Returns:
            str: URL to redirect after login.
        """
        next_url = self.request.GET.get('next')
        if next_url:
            return next_url
        return reverse_lazy('products:product-list')

    def form_valid(self, form: EmailAuthenticationForm) -> HttpResponse:
        """
        Handle valid login form submission.

        Shows welcome message with username.

        Args:
            form: Valid authentication form instance.

        Returns:
            HttpResponse: Redirect to success URL.
        """
        messages.success(self.request, f'Welcome back, {form.get_user().username}!')
        return super().form_valid(form)


class CustomLogoutView(LogoutView):
    """
    View for user logout.

    Shows info message after logout and redirects to product list.

    Attributes:
        next_page: URL to redirect after logout.
    """
    next_page = reverse_lazy('products:product-list')

    def dispatch(
            self,
            request: HttpRequest,
            *args: Any,
            **kwargs: Any,
    ) -> HttpResponse:
        """
        Handle logout request with info message.

        Args:
            request: HTTP request object.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.

        Returns:
            HttpResponse: Redirect to next page.
        """
        messages.info(request, 'You have been logged out.')
        return super().dispatch(request, *args, **kwargs)


class AccountView(LoginRequiredMixin, DetailView):
    """
    Personal account view with tabbed interface.

    Provides access to:
    - Profile information
    - Order history with filtering
    - Address management
    - Password change

    Attributes:
        model: User model class.
        template_name: Path to account template.
        context_object_name: Variable name for user in template.

    Note:
        Requires user authentication.
    """
    model = User
    template_name = 'users/account.html'
    context_object_name = 'profile_user'

    def get_object(self, queryset: QuerySet | None = None) -> AbstractUser:
        """
        Return the currently authenticated user.

        Args:
            queryset: Optional queryset (unused).

        Returns:
            User: Current authenticated user instance.
        """
        return self.request.user

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """
        Add account data to template context.

        Includes forms, orders with filtering, addresses, and active tab.

        Args:
            **kwargs: Additional keyword arguments.

        Returns:
            dict[str, Any]: Context with account data:
                - profile_form: Form for editing profile
                - password_form: Form for changing password
                - orders: Paginated order list with filters
                - total_orders: Total number of orders
                - addresses: User's addresses
                - addresses_count: Number of addresses
                - active_tab: Currently active tab
        """
        context = super().get_context_data(**kwargs)
        context['profile_form'] = EditProfileForm(instance=self.request.user)
        context['password_form'] = CustomPasswordChangeForm(user=self.request.user)
        all_orders = Order.objects.filter(user=self.request.user)
        context['total_orders'] = all_orders.count()
        orders_qs = all_orders

        # Apply filters
        status_filter = self.request.GET.get('status')
        if status_filter and status_filter in dict(Order.STATUS_CHOICES):
            orders_qs = orders_qs.filter(status=status_filter)

        date_from = self.request.GET.get('date_from')
        if date_from:
            orders_qs = orders_qs.filter(created_at__date__gte=date_from)

        date_to = self.request.GET.get('date_to')
        if date_to:
            orders_qs = orders_qs.filter(created_at__date__lte=date_to)

        orders_qs = orders_qs.order_by('-created_at')

        # Paginate orders
        paginator = Paginator(orders_qs, 5)
        page_number = self.request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        context['orders'] = page_obj
        context['status_filter'] = status_filter
        context['date_from'] = date_from
        context['date_to'] = date_to
        context['status_choices'] = Order.STATUS_CHOICES
        context['active_tab'] = self.request.GET.get('tab', 'profile')
        context['addresses'] = Address.objects.filter(user=self.request.user)
        context['addresses_count'] = context['addresses'].count()

        return context


class UpdateProfileView(LoginRequiredMixin, UpdateView):
    """
    View for updating user profile information.

    Handles profile updates with email uniqueness validation.
    Only accessible via POST (GET redirects to account page).

    Attributes:
        model: User model class.
        form_class: Form for profile editing.
        template_name: Path to account template.
        success_url: URL to redirect after successful update.
    """
    model = User
    form_class = EditProfileForm
    template_name = 'users/account.html'
    success_url = reverse_lazy('users:account')

    def get_object(self, queryset: QuerySet | None = None) -> AbstractUser:
        """
        Return the currently authenticated user.

        Args:
            queryset: Optional queryset (unused).

        Returns:
            User: Current authenticated user instance.
        """
        return self.request.user

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """
        Add profile form and account data to context.

        Args:
            **kwargs: Additional keyword arguments.

        Returns:
            dict[str, Any]: Context with profile form and account data.
        """
        context = super().get_context_data(**kwargs)
        context['profile_form'] = context['form']
        context['password_form'] = CustomPasswordChangeForm(user=self.request.user)
        context['orders'] = Order.objects.filter(user=self.request.user).order_by('-created_at')
        context['total_orders'] = context['orders'].count()
        context['active_tab'] = 'profile'
        context['addresses'] = Address.objects.filter(user=self.request.user)
        context['addresses_count'] = context['addresses'].count()
        return context

    def form_valid(self, form: EditProfileForm) -> HttpResponse:
        """
        Handle valid profile update.

        Shows success message after update.

        Args:
            form: Valid profile form instance.

        Returns:
            HttpResponse: Redirect to success URL.
        """
        messages.success(self.request, 'Profile updated successfully!')
        return super().form_valid(form)

    def form_invalid(self, form: EditProfileForm) -> HttpResponse:
        """
        Handle invalid profile update.

        Shows error message with validation errors.

        Args:
            form: Invalid profile form instance.

        Returns:
            HttpResponse: Re-rendered form with errors.
        """
        messages.error(self.request, 'Please correct the errors below.')
        return super().form_invalid(form)

    def get(
            self,
            request: HttpRequest,
            *args: Any,
            **kwargs: Any,
    ) -> HttpResponse:
        """
        Redirect GET requests to account page.

        Profile updates are only allowed via POST.

        Args:
            request: HTTP request object.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.

        Returns:
            HttpResponse: Redirect to account page.
        """
        return redirect('users:account')


class ChangePasswordView(LoginRequiredMixin, FormView):
    """
    View for changing user password.

    Handles password changes with session hash update to prevent
    logout after password change. Only accessible via POST.

    Attributes:
        form_class: Form for password change.
        template_name: Path to account template.
        success_url: URL to redirect after successful change.
    """
    form_class = CustomPasswordChangeForm
    template_name = 'users/account.html'
    success_url = reverse_lazy('users:account')

    def get_form_kwargs(self) -> dict[str, Any]:
        """
        Add user to form kwargs for password validation.

        Returns:
            dict[str, Any]: Form kwargs with user instance.
        """
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """
        Add password form and account data to context.

        Args:
            **kwargs: Additional keyword arguments.

        Returns:
            dict[str, Any]: Context with password form and account data.
        """
        context = super().get_context_data(**kwargs)
        context['profile_form'] = EditProfileForm(instance=self.request.user)
        context['password_form'] = context['form']
        context['orders'] = Order.objects.filter(user=self.request.user).order_by('-created_at')
        context['total_orders'] = context['orders'].count()
        context['active_tab'] = 'password'
        context['addresses'] = Address.objects.filter(user=self.request.user)
        context['addresses_count'] = context['addresses'].count()
        return context

    def form_valid(self, form: CustomPasswordChangeForm) -> HttpResponse:
        """
        Handle valid password change.

        Updates session hash to prevent logout and shows success message.

        Args:
            form: Valid password change form instance.

        Returns:
            HttpResponse: Redirect to success URL.
        """
        user = form.save()
        update_session_auth_hash(self.request, user)
        messages.success(self.request, 'Password changed successfully!')
        return super().form_valid(form)

    def form_invalid(self, form: CustomPasswordChangeForm) -> HttpResponse:
        """
        Handle invalid password change.

        Shows error message with validation errors.

        Args:
            form: Invalid password change form instance.

        Returns:
            HttpResponse: Re-rendered form with errors.
        """
        messages.error(self.request, 'Please correct the errors below.')
        return super().form_invalid(form)

    def get(
            self,
            request: HttpRequest,
            *args: Any,
            **kwargs: Any,
    ) -> HttpResponse:
        """
        Redirect GET requests to account page.

        Password changes are only allowed via POST.

        Args:
            request: HTTP request object.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.

        Returns:
            HttpResponse: Redirect to account page.
        """
        return redirect('users:account')


class AddressListView(LoginRequiredMixin, ListView):
    """
    View for displaying user's address list.

    Shows all addresses belonging to the authenticated user.

    Attributes:
        model: Address model class.
        template_name: Path to address list template.
        context_object_name: Variable name for addresses in template.
    """
    model = Address
    template_name = 'users/address_list.html'
    context_object_name = 'addresses'

    def get_queryset(self) -> QuerySet[Address]:
        """
        Return addresses for the authenticated user.

        Returns:
            QuerySet[Address]: User's addresses ordered by creation date.
        """
        return Address.objects.filter(user=self.request.user)


class AddressCreateView(LoginRequiredMixin, CreateView):
    """
    View for creating a new address.

    Automatically assigns the authenticated user to the new address.

    Attributes:
        model: Address model class.
        form_class: Form for address creation.
        template_name: Path to address form template.
        success_url: URL to redirect after successful creation.
    """
    model = Address
    form_class = AddressForm
    template_name = 'users/address_form.html'
    success_url = reverse_lazy('users:address-list')

    def form_valid(self, form: AddressForm) -> HttpResponse:
        """
        Handle valid address creation.

        Assigns user to address and shows success message.

        Args:
            form: Valid address form instance.

        Returns:
            HttpResponse: Redirect to address list.
        """
        form.instance.user = self.request.user
        messages.success(self.request, 'Address added successfully!')
        return super().form_valid(form)


class AddressUpdateView(LoginRequiredMixin, UpdateView):
    """
    View for editing an existing address.

    Only allows editing user's own addresses.

    Attributes:
        model: Address model class.
        form_class: Form for address editing.
        template_name: Path to address form template.
        success_url: URL to redirect after successful update.
    """
    model = Address
    form_class = AddressForm
    template_name = 'users/address_form.html'
    success_url = reverse_lazy('users:address-list')

    def get_queryset(self) -> QuerySet[Address]:
        """
        Return addresses for the authenticated user.

        Returns:
            QuerySet[Address]: User's addresses.
        """
        return Address.objects.filter(user=self.request.user)

    def form_valid(self, form: AddressForm) -> HttpResponse:
        """
        Handle valid address update.

        Shows success message after update.

        Args:
            form: Valid address form instance.

        Returns:
            HttpResponse: Redirect to address list.
        """
        messages.success(self.request, 'Address updated successfully!')
        return super().form_valid(form)


class AddressDeleteView(LoginRequiredMixin, DeleteView):
    """
    View for deleting an address.

    Only allows deleting user's own addresses.

    Attributes:
        model: Address model class.
        success_url: URL to redirect after successful deletion.
    """
    model = Address
    success_url = reverse_lazy('users:address-list')

    def get_queryset(self) -> QuerySet[Address]:
        """
        Return addresses for the authenticated user.

        Returns:
            QuerySet[Address]: User's addresses.
        """
        return Address.objects.filter(user=self.request.user)

    def delete(
            self,
            request: HttpRequest,
            *args: Any,
            **kwargs: Any,
    ) -> HttpResponse:
        """
        Handle address deletion.

        Shows success message after deletion.

        Args:
            request: HTTP request object.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.

        Returns:
            HttpResponse: Redirect to address list.
        """
        messages.success(request, 'Address deleted successfully!')
        return super().delete(request, *args, **kwargs)


class OrderDetailView(LoginRequiredMixin, DetailView):
    """
    View for displaying detailed order information.

    Shows complete order details including items, shipping info,
    and cancellation option. Only accessible for user's own orders.

    Attributes:
        model: Order model class.
        template_name: Path to order detail template.
        context_object_name: Variable name for order in template.
    """
    model = Order
    template_name = 'users/order_detail.html'
    context_object_name = 'order'

    def get_queryset(self) -> QuerySet[Order]:
        """
        Return orders for the authenticated user.

        Returns:
            QuerySet[Order]: User's orders.
        """
        return Order.objects.filter(user=self.request.user)

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """
        Add order items and cancellation flag to context.

        Args:
            **kwargs: Additional keyword arguments.

        Returns:
            dict[str, Any]: Context with:
                - items: Order items with product data
                - can_cancel: Whether order can be cancelled
        """
        context = super().get_context_data(**kwargs)
        context['items'] = self.object.items.select_related('product')
        context['can_cancel'] = self.object.status == 'pending'
        return context


class OrderCancelView(LoginRequiredMixin, View):
    """
    View for cancelling an order.

    Only allows cancellation of orders with 'pending' status.
    Restores product stock when order is cancelled.

    Note:
        Uses database transactions and row-level locking to ensure
        data consistency during cancellation.
    """

    @transaction.atomic
    def post(
            self,
            request: HttpRequest,
            pk: int,
    ) -> HttpResponse:
        """
        Handle order cancellation.

        Restores product stock and updates order status to 'cancelled'.

        Args:
            request: HTTP request object.
            pk: Primary key of the order to cancel.

        Returns:
            HttpResponse: Redirect to order detail page.

        Raises:
            Http404: If order doesn't exist or doesn't belong to user.
        """
        order = get_object_or_404(
            Order.objects.select_for_update(),
            pk=pk,
            user=request.user,
        )

        if order.status != 'pending':
            messages.error(request, 'Only pending orders can be cancelled.')
            return redirect('users:order-detail', pk=order.pk)

        # Restore stock for each item
        for item in order.items.select_related('product'):
            product = item.product
            product.stock += item.quantity
            product.save(update_fields=['stock'])

        order.status = 'cancelled'
        order.save(update_fields=['status', 'updated_at'])

        messages.success(request, f'Order #{order.id} has been cancelled.')
        return redirect('users:order-detail', pk=order.pk)
