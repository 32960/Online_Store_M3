from django.contrib.auth import get_user_model
from django.db import models

from products.models import JournalizedModel


class Order(JournalizedModel):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]

    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    status = models.CharField(max_length=20,
                              choices=STATUS_CHOICES,
                              default='pending')
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    shipping_address = models.TextField()
    # payment_id = models.CharField(max_length=100, null=True, blank=True)
    # payment_status = models.CharField(max_length=20, null=True, blank=True)

    def __str__(self):
        return f'Order {self.id} by {self.user}'

    def save(self, *args, **kwargs):
        self.total_price = self.items.aggregate(
            total_price=models.Sum('price')
        )['total_price'] or 0
        super().save(*args, **kwargs)



class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)