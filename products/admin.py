from django.contrib import admin

from products.models import Product, Category


@admin.action(description='Make selected products inactive')
def deactivate_products(modeladmin, request, queryset):
    queryset.update(is_active=False)
    modeladmin.message_user(request, f'Products deactivated: {queryset.count()}')

@admin.action(description='Make selected products active')
def activate_products(modeladmin, request, queryset):
    queryset.update(is_active=True)
    modeladmin.message_user(request, f'Activated products: {queryset.count()}')

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
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
    list_display = ('name', 'slug', 'parent', 'created_at', 'updated_at')
    list_filter = ('parent', 'created_at', 'updated_at')
    search_fields = ('name', 'slug')
    readonly_fields = ('created_at', 'updated_at')
    prepopulated_fields = {'slug': ('name',)}
