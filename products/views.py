from decimal import Decimal

from django.db.models import Q, F, Sum, Count, ExpressionWrapper, DecimalField
from django.views.generic import TemplateView, ListView, DetailView

from config.settings import PRODUCT_ALLOWED_SORTING
from orders.cart import get_cart
from products.models import Product, Category

from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import get_user_model
from django.utils.decorators import method_decorator
from orders.models import Order, OrderItem
from reviews.services import user_bought_product, user_already_reviewed

@method_decorator(staff_member_required, name='dispatch')
class AdminDashboardView(TemplateView):
    template_name = 'products/admin/dashboard.html'

    def get_context_data(self, **kwargs):
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
    template_name = 'products/guides-recipes.html'


class ProductListView(ListView):
    model = Product
    template_name = 'products/product-list.html'
    context_object_name = 'products'
    paginate_by = 6

    def get_context_data(self, **kwargs):
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

    def get_queryset(self):
        queryset = Product.objects.filter(is_active= True)
        categories = self.request.GET.get('categories')
        categories = categories.split(',') if categories else []
        if categories:
            queryset = queryset.filter(category__slug__in= categories)

        sorting = self.request.GET.get('sorting', '-created_at')
        if sorting and sorting in PRODUCT_ALLOWED_SORTING:
            queryset = queryset.order_by(sorting)

        q = self.request.GET.get('q')
        if q:
            queryset = queryset.filter(Q(name__icontains= q) | Q(description__icontains= q))

        return queryset


class ProductDetailView(DetailView):
    model = Product
    template_name = 'products/product-detail.html'
    slug_url_kwarg = 'slug'

    def get_context_data(self, **kwargs):
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
