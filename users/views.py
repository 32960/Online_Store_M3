from django.contrib.auth import login, update_session_auth_hash
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib import messages
from django.core.paginator import Paginator
from django.shortcuts import redirect, get_object_or_404
from django.views.generic import UpdateView, DetailView, CreateView, FormView, ListView, DeleteView
from django.urls import reverse_lazy

from django.contrib.auth import get_user_model
from orders.models import Order
from users.models import Address
from users.forms import EditProfileForm, CustomPasswordChangeForm, EmailAuthenticationForm, RegisterForm, AddressForm

from django.db import transaction
from django.views import View

User = get_user_model()


class RegisterView(CreateView):
    """New user registration."""
    form_class = RegisterForm
    template_name = 'users/register.html'
    success_url = reverse_lazy('products:product-list')

    def form_valid(self, form):
        response = super().form_valid(form)
        login(self.request, self.object)
        messages.success(self.request, 'Registration successful! Welcome!')
        return response

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('products:product-list')
        return super().dispatch(request, *args, **kwargs)


class CustomLoginView(LoginView):
    """Log in."""
    template_name = 'users/login.html'
    authentication_form = EmailAuthenticationForm

    def get_success_url(self):
        next_url = self.request.GET.get('next')
        if next_url:
            return next_url
        return reverse_lazy('products:product-list')

    def form_valid(self, form):
        messages.success(self.request, f'Welcome back, {form.get_user().username}!')
        return super().form_valid(form)


class CustomLogoutView(LogoutView):
    """Log out."""
    next_page = reverse_lazy('products:product-list')

    def dispatch(self, request, *args, **kwargs):
        messages.info(request, 'You have been logged out.')
        return super().dispatch(request, *args, **kwargs)


class AccountView(LoginRequiredMixin, DetailView):
    """Personal account with tabs."""
    model = User
    template_name = 'users/account.html'
    context_object_name = 'profile_user'

    def get_object(self, queryset=None):
        return self.request.user

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['profile_form'] = EditProfileForm(instance=self.request.user)
        context['password_form'] = CustomPasswordChangeForm(user=self.request.user)
        all_orders = Order.objects.filter(user=self.request.user)
        context['total_orders'] = all_orders.count()
        orders_qs = all_orders

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
    """Profile update."""
    model = User
    form_class = EditProfileForm
    template_name = 'users/account.html'
    success_url = reverse_lazy('users:account')

    def get_object(self, queryset=None):
        return self.request.user

    def get_context_data(self, **kwargs):
        """Adding the necessary data to the context."""
        context = super().get_context_data(**kwargs)
        context['profile_form'] = context['form']
        context['password_form'] = CustomPasswordChangeForm(user=self.request.user)
        context['orders'] = Order.objects.filter(user=self.request.user).order_by('-created_at')
        context['total_orders'] = context['orders'].count()
        context['active_tab'] = 'profile'
        context['addresses'] = Address.objects.filter(user=self.request.user)
        context['addresses_count'] = context['addresses'].count()
        return context

    def form_valid(self, form):
        messages.success(self.request, 'Profile updated successfully!')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Please correct the errors below.')
        return super().form_invalid(form)

    def get(self, request, *args, **kwargs):
        return redirect('users:account')


class ChangePasswordView(LoginRequiredMixin, FormView):
    """Change password."""
    form_class = CustomPasswordChangeForm
    template_name = 'users/account.html'
    success_url = reverse_lazy('users:account')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        """Adding the necessary data to the context."""
        context = super().get_context_data(**kwargs)
        context['profile_form'] = EditProfileForm(instance=self.request.user)
        context['password_form'] = context['form']
        context['orders'] = Order.objects.filter(user=self.request.user).order_by('-created_at')
        context['total_orders'] = context['orders'].count()
        context['active_tab'] = 'password'
        context['addresses'] = Address.objects.filter(user=self.request.user)
        context['addresses_count'] = context['addresses'].count()
        return context

    def form_valid(self, form):
        user = form.save()
        update_session_auth_hash(self.request, user)
        messages.success(self.request, 'Password changed successfully!')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Please correct the errors below.')
        return super().form_invalid(form)

    def get(self, request, *args, **kwargs):
        return redirect('users:account')


class AddressListView(LoginRequiredMixin, ListView):
    """User address list."""
    model = Address
    template_name = 'users/address_list.html'
    context_object_name = 'addresses'

    def get_queryset(self):
        return Address.objects.filter(user=self.request.user)


class AddressCreateView(LoginRequiredMixin, CreateView):
    """Creating a new address."""
    model = Address
    form_class = AddressForm
    template_name = 'users/address_form.html'
    success_url = reverse_lazy('users:address-list')

    def form_valid(self, form):
        form.instance.user = self.request.user
        messages.success(self.request, 'Address added successfully!')
        return super().form_valid(form)


class AddressUpdateView(LoginRequiredMixin, UpdateView):
    """Editing the address."""
    model = Address
    form_class = AddressForm
    template_name = 'users/address_form.html'
    success_url = reverse_lazy('users:address-list')

    def get_queryset(self):
        return Address.objects.filter(user=self.request.user)

    def form_valid(self, form):
        messages.success(self.request, 'Address updated successfully!')
        return super().form_valid(form)


class AddressDeleteView(LoginRequiredMixin, DeleteView):
    """Deleting the address."""
    model = Address
    success_url = reverse_lazy('users:address-list')

    def get_queryset(self):
        return Address.objects.filter(user=self.request.user)

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Address deleted successfully!')
        return super().delete(request, *args, **kwargs)


class OrderDetailView(LoginRequiredMixin, DetailView):
    """Detailed order view."""
    model = Order
    template_name = 'users/order_detail.html'
    context_object_name = 'order'

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['items'] = self.object.items.select_related('product')
        context['can_cancel'] = self.object.status == 'pending'
        return context


class OrderCancelView(LoginRequiredMixin, View):
    """Order cancellation (only if status is "pending")."""

    @transaction.atomic
    def post(self, request, pk):
        order = get_object_or_404(
            Order.objects.select_for_update(),
            pk=pk,
            user=request.user,
        )

        if order.status != 'pending':
            messages.error(request, 'Only pending orders can be cancelled.')
            return redirect('users:order-detail', pk=order.pk)

        for item in order.items.select_related('product'):
            product = item.product
            product.stock += item.quantity
            product.save(update_fields=['stock'])

        order.status = 'cancelled'
        order.save(update_fields=['status', 'updated_at'])

        messages.success(request, f'Order #{order.id} has been cancelled.')
        return redirect('users:order-detail', pk=order.pk)
