from django.contrib import admin
from django.contrib.admin import TabularInline

from orders.models import Order, OrderItem


class OrderItemInline(TabularInline):
    model = OrderItem
    min_num = 1


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('user', 'status', 'total_price', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [OrderItemInline]

    class Meta:
        model = Order

