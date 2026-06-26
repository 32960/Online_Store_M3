from django.contrib import admin
from reviews.models import Review

@admin.action(description='Delete selected reviews')
def delete_reviews(modeladmin, request, queryset):
    count = queryset.count()
    queryset.delete()
    modeladmin.message_user(request, f'Deleted reviews: {count}')


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('product', 'user', 'rating', 'created_at')
    list_display_links = ('product', 'user')
    list_filter = ('rating', 'created_at', 'product')
    search_fields = ('product__name', 'user__username', 'comment')
    readonly_fields = ('created_at',)
    raw_id_fields = ('product', 'user')
    actions = [delete_reviews]
