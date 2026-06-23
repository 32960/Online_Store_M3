from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db import models
from django.db.models import Sum, ExpressionWrapper, F, DecimalField

from products.models import JournalizedModel


class Order(JournalizedModel):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]

    PAYMENT_CHOICES = [
        ('debit', 'Debit Card'),
        ('wallet', 'Digital Wallet'),
        ('cod', 'Cash On Delivery'),
    ]

    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    status = models.CharField(max_length=20,
                              choices=STATUS_CHOICES,
                              default='pending')
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    full_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15)
    city = models.CharField(max_length=100)
    shipping_address = models.TextField()
    payment_method = models.CharField(max_length=20, choices=PAYMENT_CHOICES)

    # payment_id = models.CharField(max_length=100, null=True, blank=True)
    # payment_status = models.CharField(max_length=20, null=True, blank=True)

    def __str__(self):
        return f'Order {self.id} by {self.user}'

    def update_total_price(self) -> None:
        """Recalculate and persist the order total price."""
        total_price = self.items.aggregate(
            total_price=Sum(
                ExpressionWrapper(
                    F('price') * F('quantity'),
                    output_field=DecimalField(
                        max_digits=10,
                        decimal_places=2,
                    ),
                ),
            ),
        )['total_price'] or Decimal('0.00')
        self.total_price = total_price
        self.save(update_fields=['total_price', 'updated_at'])


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.order.update_total_price()

    def delete(self, *args, **kwargs):
        order = self.order
        result = super().delete(*args, **kwargs)
        order.update_total_price()
        return result
