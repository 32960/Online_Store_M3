"""
Admin configuration for order management in the Hop & Barley online store.

This module provides:
- Order admin with inline order items
- Custom admin action for cancelling orders with stock restoration
- Filters by status and date ranges
"""

from django.contrib import admin, messages
from django.contrib.admin import TabularInline
from django.db.models import QuerySet
from django.http import HttpRequest
from django.contrib.admin import DateFieldListFilter

from orders.models import Order, OrderItem


class OrderItemInline(TabularInline):
    """
    Inline admin for order items within order admin.

    Displays order items in a tabular format on the order detail page.

    Attributes:
        model: OrderItem model class.
        min_num: Minimum number of items required.
    """
    model = OrderItem
    min_num = 1


@admin.action(description='Cancel selected orders')
def cancel_orders(
    modeladmin: 'OrderAdmin',
    request: HttpRequest,
    queryset: QuerySet[Order]
) -> None:
    """
    Cancel selected orders and restore product stock.

    Args:
        modeladmin: OrderAdmin instance.
        request: HTTP request object.
        queryset: QuerySet of selected orders.

    Note:
        Only cancels orders that are not already shipped, delivered, or cancelled.
        Restores stock for each cancelled order item.
    """
    cancelled_count = 0

    for order in queryset:
        if order.status not in {'shipped', 'delivered', 'cancelled'}:
            for item in order.items.select_related('product'):
                product = item.product
                product.stock += item.quantity
                product.save(update_fields=['stock'])

            order.status = 'cancelled'
            order.save(update_fields=['status'])
            cancelled_count += 1

    modeladmin.message_user(
        request,
        f'Cancelled orders: {cancelled_count}',
        level=messages.SUCCESS
    )


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    """
    Admin interface for Order model.

    Provides:
    - List display with user, status, total price, and creation date
    - Filters by status and date ranges
    - Search by username and email
    - Inline order items
    - Custom action for cancelling orders

    Attributes:
        list_display: Fields to display in list view.
        list_display_links: Fields that link to detail view.
        list_filter: Filters for sidebar.
        search_fields: Fields for search box.
        readonly_fields: Fields that cannot be edited.
        inlines: Inline models to display.
        actions: Custom admin actions.
    """
    list_display = ('user', 'status', 'total_price', 'created_at')
    list_display_links = ('user', 'status')
    list_filter = (
        'status',
        ('created_at', DateFieldListFilter),
        ('updated_at', DateFieldListFilter),
    )
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [OrderItemInline]
    actions = [cancel_orders]

    def has_add_permission(self, request):
        return request.user.is_staff

    def has_change_permission(self, request, obj=None):
        return request.user.is_staff

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

    class Meta:
        model = Order
