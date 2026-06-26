from django.contrib import admin, messages
from django.contrib.admin import TabularInline

from orders.models import Order, OrderItem


class OrderItemInline(TabularInline):
    model = OrderItem
    min_num = 1


@admin.action(description='Cancel selected orders')
def cancel_orders(modeladmin, request, queryset):
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
    list_display = ('user', 'status', 'total_price', 'created_at')
    list_display_links = ('user', 'status')
    list_filter = ('status', 'created_at')
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [OrderItemInline]
    actions = [cancel_orders]

    class Meta:
        model = Order
