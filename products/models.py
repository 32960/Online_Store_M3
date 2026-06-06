from django.db import models
from django.urls import reverse

class JournalizedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

class Product(JournalizedModel):
    CURRENCY = [
        ('$', 'USD'),
        ('$', 'EUR'),
        ('$', 'RUB'),
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

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('products:product-detail', kwargs={'slug':self.slug})


class Category(JournalizedModel):
    name = models.CharField(max_length=50)
    slug = models.SlugField(unique=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='subcategories')

    class Meta:
        verbose_name = 'Category'
        verbose_name_plural = 'Categories'

    def __str__(self):
        return self.name