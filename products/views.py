"""
Views for product catalog and admin dashboard in the Hop & Barley online store.

This module provides views for:
- Admin dashboard with sales statistics
- Product listing with filtering, sorting, and search
- Product detail pages with reviews
- Guides and recipes pages

All views support both authenticated and anonymous users where appropriate.
"""
from decimal import Decimal
from typing import Any

from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import get_user_model
from django.db.models import Q, F, Sum, Count, ExpressionWrapper, DecimalField, QuerySet
from django.http import HttpRequest
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView, ListView, DetailView

from config.settings import PRODUCT_ALLOWED_SORTING
from orders.cart import get_cart
from orders.models import Order, OrderItem
from products.models import Product, Category
from reviews.services import user_bought_product, user_already_reviewed

@method_decorator(staff_member_required, name='dispatch')
class AdminDashboardView(TemplateView):
    """
    Admin dashboard view with sales statistics and analytics.

    Displays key metrics:
    - Total revenue from paid orders
    - Order counts by status
    - Top 5 products by revenue
    - Total user count

    Note:
        Requires staff member authentication.
        Only shows data from paid, shipped, and delivered orders.

    Attributes:
        template_name: Path to dashboard template.
    """
    template_name = 'products/admin/dashboard.html'

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """
        Add dashboard statistics to template context.

        Args:
            **kwargs: Additional keyword arguments.

        Returns:
            dict[str, Any]: Context with dashboard statistics:
                - total_revenue: Total revenue from paid orders
                - orders_count: Order counts grouped by status
                - total_orders: Total number of orders
                - pending_orders: Number of pending orders
                - top_products: Top 5 products by revenue
                - total_users: Total number of registered users
        """
        context = super().get_context_data(**kwargs)

        # Total revenue (paid orders only)
        total_revenue = OrderItem.objects.filter(
            order__status__in=['paid', 'shipped', 'delivered']
        ).aggregate(
            total=Sum(
                ExpressionWrapper(
                    F('price') * F('quantity'),
                    output_field=DecimalField(max_digits=12, decimal_places=2)
                )
            )
        )['total'] or Decimal('0.00')


        # Number of orders by status
        orders_count = Order.objects.values('status').annotate(
            count=Count('id')
        ).order_by('status')

        total_orders = Order.objects.count()
        pending_orders = Order.objects.filter(status='pending').count()

        # Top 5 products by revenue
        top_products = OrderItem.objects.filter(
            order__status__in=['paid', 'shipped', 'delivered']
        ).values(
            'product__name'
        ).annotate(
            revenue=Sum(
                ExpressionWrapper(
                    F('price') * F('quantity'),
                    output_field=DecimalField(max_digits=12, decimal_places=2)
                )
            ),
            quantity_sold=Sum('quantity')
        ).order_by('-revenue')[:5]

        User = get_user_model()
        total_users = User.objects.count()

        context['total_revenue'] = total_revenue
        context['orders_count'] = orders_count
        context['total_orders'] = total_orders
        context['pending_orders'] = pending_orders
        context['top_products'] = top_products
        context['total_users'] = total_users

        return context


class GuidesView(TemplateView):
    """
    Static page view for brewing guides and recipes.

    Displays educational content about beer brewing techniques,
    recipes, and best practices.

    Attributes:
        template_name: Path to guides template.
    """
    template_name = 'products/guides-recipes.html'


class ProductListView(ListView):
    """
    Product listing view with filtering, sorting, and search.

    Displays paginated list of active products with support for:
    - Category filtering (multiple categories)
    - Price and rating sorting
    - Full-text search in name and description

    Attributes:
        model: Product model class.
        template_name: Path to product list template.
        context_object_name: Variable name for products in template.
        paginate_by: Number of products per page.

    Examples:
        GET /products/?categories=malt,hops&sorting=-price&q=citra
    """
    model = Product
    template_name = 'products/product-list.html'
    context_object_name = 'products'
    paginate_by = 6

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """
        Add categories and sorting options to template context.

        Args:
            **kwargs: Additional keyword arguments.

        Returns:
            dict[str, Any]: Context with:
                - categories: List of all categories
                - sorting_data: Available sorting options
                - checked_categories: Currently selected categories
        """
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all().values('name', 'slug')
        sorting_data = [
            ('-created_at', 'New'),
            ('price', 'Price ascending'),
            ('-price', 'Price descending'),
            ('-rating', 'Rating'),
        ]
        checked_categories = self.request.GET.get('categories', '')
        context['checked_categories'] = checked_categories.split(',') if checked_categories else []
        context['sorting_data'] = sorting_data
        return context

    def get_queryset(self) -> QuerySet[Product]:
        """
        Return filtered, sorted, and searched product queryset.

        Applies filters in order:
        1. Only active products
        2. Category filter (if specified)
        3. Sorting (if valid)
        4. Search query (if specified)

        Returns:
            QuerySet[Product]: Filtered product queryset.
        """
        queryset = Product.objects.filter(is_active= True)

        # Category filter
        categories = self.request.GET.get('categories')
        categories = categories.split(',') if categories else []
        if categories:
            queryset = queryset.filter(category__slug__in= categories)

        # Sorting
        sorting = self.request.GET.get('sorting', '-created_at')
        if sorting and sorting in PRODUCT_ALLOWED_SORTING:
            queryset = queryset.order_by(sorting)

        # Search
        q = self.request.GET.get('q')
        if q:
            queryset = queryset.filter(Q(name__icontains= q) | Q(description__icontains= q))

        return queryset


class ProductDetailView(DetailView):
    """
    Product detail view with reviews and cart integration.

    Displays complete product information including:
    - Product details and specifications
    - Current cart quantity
    - Recent reviews
    - Review permissions (based on purchase history)

    Attributes:
        model: Product model class.
        template_name: Path to product detail template.
        slug_url_kwarg: URL parameter name for product slug.

    Note:
        Review permissions require user authentication and purchase history.
    """
    model = Product
    template_name = 'products/product-detail.html'
    slug_url_kwarg = 'slug'

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """
        Add cart data, reviews, and review permissions to context.

        Args:
            **kwargs: Additional keyword arguments.

        Returns:
            dict[str, Any]: Context with:
                - cart: Current cart data
                - quantity: Product quantity in cart
                - recent_reviews: Last 3 reviews
                - can_review: Whether user can write a review
                - user_reviewed: Whether user already reviewed
                - user_bought: Whether user purchased the product
        """
        context = super().get_context_data(**kwargs)
        cart = get_cart(self.request)
        context['cart'] = cart
        context['quantity'] = cart.get(str(self.object.id), {'quantity': 0})['quantity']
        context['recent_reviews'] = self.object.reviews.select_related('user').order_by('-created_at')[:3]

        if self.request.user.is_authenticated:
            user_bought = user_bought_product(self.request.user, self.object)
            user_reviewed = user_already_reviewed(self.request.user, self.object)
            context['can_review'] = user_bought and not user_reviewed
            context['user_reviewed'] = user_reviewed
            context['user_bought'] = user_bought
        else:
            context['can_review'] = False
            context['user_reviewed'] = False
            context['user_bought'] = False

        return context
