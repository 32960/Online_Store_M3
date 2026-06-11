from django.contrib import admin

from products.models import Product, Category


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'currency', 'stock', 'is_active', 'created_at', 'updated_at', 'rating')
    list_filter = ('is_active', 'created_at', 'updated_at')
    search_fields = ('name', 'description', 'slug')
    readonly_fields = ('created_at', 'updated_at')
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'parent', 'created_at', 'updated_at')
    list_filter = ('parent', 'created_at', 'updated_at')
    search_fields = ('name', 'slug')
    readonly_fields = ('created_at', 'updated_at')
    prepopulated_fields = {'slug': ('name',)}

