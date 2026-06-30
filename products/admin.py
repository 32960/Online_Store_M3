"""
Admin interface configuration for product catalog in the Hop & Barley online store.

This module provides admin configurations for:
- Product management with bulk actions
- Category management with hierarchical structure

Custom actions allow bulk activation/deactivation of products.
"""
from django.contrib import admin
from django.db.models import QuerySet
from django.http import HttpRequest

from products.models import Product, Category


@admin.action(description='Make selected products inactive')
def deactivate_products(
    modeladmin: admin.ModelAdmin,
    request: HttpRequest,
    queryset: QuerySet[Product],
) -> None:
    """
    Bulk action to deactivate selected products.

    Args:
        modeladmin: Admin model instance.
        request: HTTP request object.
        queryset: Selected products to deactivate.
    """
    queryset.update(is_active=False)
    modeladmin.message_user(request, f'Products deactivated: {queryset.count()}')

@admin.action(description='Make selected products active')
def activate_products(
    modeladmin: admin.ModelAdmin,
    request: HttpRequest,
    queryset: QuerySet[Product],
) -> None:
    """
    Bulk action to activate selected products.

    Args:
        modeladmin: Admin model instance.
        request: HTTP request object.
        queryset: Selected products to activate.
    """
    queryset.update(is_active=True)
    modeladmin.message_user(request, f'Activated products: {queryset.count()}')

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """
    Admin interface for Product model.

    Provides comprehensive product management with:
    - List display with key fields
    - Filtering by status and dates
    - Search by name, description, slug
    - Auto-generated slug from name
    - Bulk activation/deactivation actions
    - Collapsible fieldsets for additional info

    Attributes:
        list_display: Fields shown in list view.
        list_filter: Available filters.
        search_fields: Fields searchable in admin.
        readonly_fields: Fields that cannot be edited.
        prepopulated_fields: Auto-populated fields.
        actions: Available bulk actions.
        fieldsets: Organized field groups.
    """
    list_display = ('id', 'name', 'price', 'currency', 'stock', 'is_active', 'created_at', 'updated_at', 'rating')
    list_filter = ('is_active', 'created_at', 'updated_at')
    search_fields = ('name', 'description', 'slug')
    readonly_fields = ('created_at', 'updated_at')
    prepopulated_fields = {'slug': ('name',)}
    actions = [deactivate_products, activate_products]

    fieldsets = (
        ('Basic information', {
            'fields': ('name', 'slug', 'category', 'description', 'price', 'stock', 'image', 'is_active')
        }),
        ('Additional information', {
            'fields': ('price_unit', 'specifications'),
            'classes': ('collapse',),
        }),
    )

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """
    Admin interface for Category model.

    Provides category management with:
    - List display with hierarchy
    - Filtering by parent and dates
    - Search by name and slug
    - Auto-generated slug from name

    Attributes:
        list_display: Fields shown in list view.
        list_filter: Available filters.
        search_fields: Fields searchable in admin.
        readonly_fields: Fields that cannot be edited.
        prepopulated_fields: Auto-populated fields.
    """
    list_display = ('name', 'slug', 'parent', 'created_at', 'updated_at')
    list_filter = ('parent', 'created_at', 'updated_at')
    search_fields = ('name', 'slug')
    readonly_fields = ('created_at', 'updated_at')
    prepopulated_fields = {'slug': ('name',)}
