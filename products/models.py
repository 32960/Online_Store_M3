"""
Models for product catalog in the Hop & Barley online store.

This module defines:
- JournalizedModel: Abstract base model with timestamps
- Product: Main product model with pricing, stock, and specifications
- Category: Hierarchical product categories

Products support dynamic pricing units and JSON-based technical specifications
for flexible product information storage.
"""
from typing import Any

from django.db import models
from django.urls import reverse

class JournalizedModel(models.Model):
    """
    Abstract base model with automatic timestamp tracking.

    Provides created_at and updated_at fields that are automatically
    managed by Django. All models in the project inherit from this base.

    Attributes:
        created_at: Timestamp when the object was created (auto-set).
        updated_at: Timestamp when the object was last updated (auto-set).

    Note:
        This is an abstract model and does not create a database table.
    """
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Product(JournalizedModel):
    """
    Model representing a product in the catalog.

    Tracks product details, pricing, stock, ratings, and technical specifications.
    Supports multiple currencies and dynamic price units.

    Attributes:
        CURRENCY: Available currency choices (USD, EUR, RUB).
        name: Product name (max 100 characters).
        description: Detailed product description.
        price: Product price with 2 decimal places.
        image: Product image file.
        slug: URL-friendly unique identifier.
        currency: Selected currency for pricing.
        category: Foreign key to product category (nullable).
        is_active: Flag to show/hide product from catalog.
        stock: Available quantity in stock.
        rating: Average product rating (0.0-5.0).
        price_unit: Unit of measurement for price (e.g., "per 1 lb").
        specifications: JSON field for technical specifications.

    Examples:
        >>> product = Product.objects.create(
        ...     name='Citra Hops',
        ...     description='Dual-purpose hops with citrus aroma',
        ...     price=14.99,
        ...     slug='citra-hops',
        ...     category=category,
        ...     stock=100
        ... )
        >>> product.get_absolute_url()
        '/products/citra-hops/'
    """
    CURRENCY = [
        ('$', 'USD'),
        ('€', 'EUR'),
        ('₽', 'RUB'),
    ]
    name = models.CharField(max_length=100)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to='product_images/')
    slug = models.SlugField(unique=True)
    currency = models.CharField(max_length=3, choices=CURRENCY, default='USD')
    category = models.ForeignKey('Category', on_delete=models.SET_NULL, null=True, related_name='products')
    is_active = models.BooleanField(default=True)
    stock = models.PositiveIntegerField(default=0)
    rating = models.DecimalField(max_digits=3, decimal_places=1, default=0.0)
    price_unit = models.CharField(
        max_length=50,
        default='per 1 lb',
        blank=True,
        verbose_name='Price unit of measurement',
        help_text='For example: per 1 lb, per 100g, per pouch'
    )

    specifications = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='Technical specifications',
        help_text='Format JSON: {"Origin": "USA", "Type": "Dual-Purpose", ...}'
    )

    def __str__(self) -> str:
        """
        Return string representation of the product.

        Returns:
            str: Product name.
        """
        return self.name

    def get_absolute_url(self) -> str:
        """
        Return the URL for the product detail page.

        Returns:
            str: URL path to the product detail page.
        """
        return reverse('products:product-detail', kwargs={'slug': self.slug})

    class Meta:
        verbose_name = 'Product'
        verbose_name_plural = 'Products'
        ordering = ['-created_at']


class Category(JournalizedModel):
    """
    Model representing a product category.

    Supports hierarchical structure with parent-child relationships.
    Categories are used to organize products in the catalog.

    Attributes:
        name: Category name (max 50 characters).
        slug: URL-friendly unique identifier.
        parent: Foreign key to parent category (nullable for root categories).

    Examples:
        >>> category = Category.objects.create(
        ...     name='Hops',
        ...     slug='hops'
        ... )
        >>> subcategory = Category.objects.create(
        ...     name='Aroma Hops',
        ...     slug='aroma-hops',
        ...     parent=category
        ... )
    """
    name = models.CharField(max_length=50)
    slug = models.SlugField(unique=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='subcategories')

    class Meta:
        verbose_name = 'Category'
        verbose_name_plural = 'Categories'
        ordering = ['name']

    def __str__(self) -> str:
        """
        Return string representation of the category.

        Returns:
            str: Category name.
        """
        return self.name
