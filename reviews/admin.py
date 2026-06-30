"""
Admin interface configuration for reviews in the Hop & Barley online store.

This module provides admin configuration for:
- Review management with bulk delete action
- Filtering and searching reviews
"""
from typing import Any

from django.contrib import admin
from django.db.models import QuerySet
from django.http import HttpRequest

from reviews.models import Review

@admin.action(description='Delete selected reviews')
def delete_reviews(
    modeladmin: admin.ModelAdmin,
    request: HttpRequest,
    queryset: QuerySet[Review],
) -> None:
    """
    Bulk action to delete selected reviews.

    Args:
        modeladmin: Admin model instance.
        request: HTTP request object.
        queryset: Selected reviews to delete.
    """
    count = queryset.count()
    queryset.delete()
    modeladmin.message_user(request, f'Deleted reviews: {count}')


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    """
    Admin interface for Review model.

    Provides comprehensive review management with:
    - List display with key fields
    - Filtering by rating, date, and product
    - Search by product name, username, and comment
    - Bulk delete action
    - Raw ID fields for product and user selection

    Attributes:
        list_display: Fields shown in list view.
        list_display_links: Fields that link to detail view.
        list_filter: Available filters.
        search_fields: Fields searchable in admin.
        readonly_fields: Fields that cannot be edited.
        raw_id_fields: Fields using raw ID widgets.
        actions: Available bulk actions.
    """
    list_display = ('product', 'user', 'rating', 'created_at')
    list_display_links = ('product', 'user')
    list_filter = ('rating', 'created_at', 'product')
    search_fields = ('product__name', 'user__username', 'comment')
    readonly_fields = ('created_at',)
    raw_id_fields = ('product', 'user')
    actions = [delete_reviews]
