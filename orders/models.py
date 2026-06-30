"""
Models for order management in the Hop & Barley online store.

This module defines:
- Order: Main order model with shipping info and payment details
- OrderItem: Individual items within an order

Orders track the complete lifecycle from creation to delivery,
including automatic stock management and price calculations.
"""
from decimal import Decimal
from typing import Any

from django.contrib.auth import get_user_model
from django.db import models
from django.db.models import Sum, ExpressionWrapper, F, DecimalField

from products.models import JournalizedModel


class Order(JournalizedModel):
    """
    Model representing a customer order.

    Tracks order status, shipping information, payment method,
    and automatically calculates total price from order items.

    Attributes:
        STATUS_CHOICES: Available order statuses.
        PAYMENT_CHOICES: Available payment methods.
        user: Foreign key to the user who placed the order.
        status: Current order status (pending, paid, shipped, delivered, cancelled).
        total_price: Total price calculated from order items.
        full_name: Recipient's full name.
        phone: Recipient's phone number.
        city: Delivery city.
        shipping_address: Full shipping address.
        payment_method: Selected payment method.

    Examples:
        >>> order = Order.objects.create(
        ...     user=user,
        ...     full_name='John Doe',
        ...     phone='+1234567890',
        ...     city='New York',
        ...     shipping_address='123 Main St',
        ...     payment_method='debit'
        ... )
        >>> order.update_total_price()
    """
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

    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name='orders',)
    status = models.CharField(max_length=20,
                              choices=STATUS_CHOICES,
                              default='pending')
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    full_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)
    city = models.CharField(max_length=100)
    shipping_address = models.CharField(max_length=255)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_CHOICES)

    def __str__(self) -> str:
        """
        Return string representation of the order.

        Returns:
            str: Order ID and associated user.
        """
        return f'Order {self.id} by {self.user}'

    def update_total_price(self) -> None:
        """
        Recalculate and persist the order total price.

        Aggregates all order items (price * quantity) and updates
        the total_price field. Uses database-level aggregation
        for efficiency.

        Note:
            This method is automatically called when order items
            are created, updated, or deleted.
        """
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
    """
    Model representing an individual item within an order.

    Tracks product reference, quantity, and price at time of purchase.
    Automatically updates order total price when saved or deleted.

    Attributes:
        order: Foreign key to the parent order.
        product: Foreign key to the purchased product.
        quantity: Number of units purchased.
        price: Price per unit at time of purchase.

    Examples:
        >>> item = OrderItem.objects.create(
        ...     order=order,
        ...     product=product,
        ...     quantity=2,
        ...     price=product.price
        ... )
        >>> item.total
        Decimal('29.98')
    """
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

    @property
    def total(self) -> Decimal:
        """
        Calculate total cost of this item.

        Returns:
            Decimal: Total cost (quantity * price).
        """
        return self.quantity * self.price

    def save(self, *args: Any, **kwargs: Any) -> None:
        """
        Save the order item and update order total price.

        Args:
            *args: Positional arguments for Model.save().
            **kwargs: Keyword arguments for Model.save().
        """
        super().save(*args, **kwargs)
        self.order.update_total_price()

    def delete(self, *args: Any, **kwargs: Any) -> tuple[int, dict[str, int]]:
        """
        Delete the order item and update order total price.

        Args:
            *args: Positional arguments for Model.delete().
            **kwargs: Keyword arguments for Model.delete().

        Returns:
            tuple[int, dict[str, int]]: Number of objects deleted and breakdown.
        """
        order = self.order
        result = super().delete(*args, **kwargs)
        order.update_total_price()
        return result
