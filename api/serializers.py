"""
API serializers for the Hop & Barley online store.

This module provides serializers for:
- Products and categories
- Orders and order items
- User registration
- Shopping cart
- Product reviews
"""
from typing import Any

from django.contrib.auth import get_user_model
from django.db import transaction
from rest_framework import serializers

from orders.models import OrderItem, Order
from products.models import Product, Category
from reviews.models import Review


class CategorySerializer(serializers.ModelSerializer):
    """
    Serializer for Category model.

    Provides read-only access to category data including
    parent category relationship and timestamps.

    Attributes:
        model: Category model class.
        fields: List of fields to serialize.
        read_only_fields: List of read-only fields.
    """
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'parent', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class ProductListSerializer(serializers.ModelSerializer):
    """
    Serializer for product list view.

    Contains basic product information for list endpoints.
    Optimized for performance with minimal fields.

    Attributes:
        model: Product model class.
        fields: List of fields to serialize.
        read_only_fields: List of read-only fields.
    """
    class Meta:
        model = Product
        fields = [
            'name', 'description', 'price', 'category',
            'stock', 'created_at', 'updated_at', 'slug',
            'id', 'is_active', 'rating'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'slug', 'is_active']


class ProductDetailSerializer(serializers.ModelSerializer):
    """
    Serializer for product detail view.

    Includes additional fields like image and currency,
    plus nested category serializer for complete product information.

    Attributes:
        category: Nested CategorySerializer for category details.
        model: Product model class.
        fields: List of fields to serialize.
        read_only_fields: List of read-only fields.
    """
    category = CategorySerializer(read_only=True)

    class Meta:
        model = Product
        fields = [
            'image', 'currency'
        ] + ProductListSerializer.Meta.fields
        read_only_fields = ProductListSerializer.Meta.read_only_fields


class OrderItemSerializer(serializers.ModelSerializer):
    """
    Serializer for order items.

    Represents individual items within an order, including
    product reference, quantity, and price at time of purchase.

    Attributes:
        model: OrderItem model class.
        fields: List of fields to serialize.
        read_only_fields: List of read-only fields.
    """
    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'quantity', 'price']
        read_only_fields = ['id', 'price']


class OrderSerializer(serializers.ModelSerializer):
    """
    Serializer for Order model.

    Includes nested order items and user info.
    Validates stock availability and order status transitions.
    Handles complex business logic for order creation and updates.

    Attributes:
        items: Nested OrderItemSerializer for order items.
        user: String representation of the user.
        model: Order model class.
        fields: List of fields to serialize.
        read_only_fields: List of read-only fields.
    """
    items = OrderItemSerializer(many=True)
    user = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Order
        fields = [
            'id', 'user', 'status', 'total_price', 'items',
            'created_at', 'updated_at', 'full_name', 'phone',
            'city', 'shipping_address', 'payment_method'
        ]
        read_only_fields = ['id', 'user', 'total_price', 'created_at', 'updated_at']

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        """
        Validate order data with complex business rules.

        Validates:
        - Locked fields cannot be changed after certain statuses
        - Payment method cannot be changed after payment
        - At least one item required for new orders
        - Items cannot be changed after creation
        - Status transitions are valid
        - Sufficient stock for all items

        Args:
            attrs: Validated attributes dictionary.

        Returns:
            dict[str, Any]: Validated attributes.

        Raises:
            serializers.ValidationError: If validation fails.
        """
        request = self.context.get('request')
        items = attrs.get('items')

        if self.instance is not None:
            current_status = self.instance.status
            locked_fields = {'shipping_address', 'city', 'payment_method'}
            if current_status in {'shipped', 'delivered', 'cancelled'}:
                for field in locked_fields:
                    if field in attrs and attrs[field] != getattr(self.instance, field):
                        raise serializers.ValidationError({
                            field: f'Cannot change {field} after order is {current_status}.'
                        })

            if current_status in {'paid', 'shipped', 'delivered'}:
                if 'payment_method' in attrs and attrs['payment_method'] != self.instance.payment_method:
                    raise serializers.ValidationError({
                        'payment_method': 'Cannot change payment method after payment.'
                    })

        if self.instance is None and not items:
            raise serializers.ValidationError({
                'items': 'At least one order item is required.',
            })

        if self.instance is not None and 'items' in attrs:
            raise serializers.ValidationError({
                'items': 'Order items cannot be changed after creation.',
            })

        if self.instance is not None and 'status' in attrs:
            next_status = attrs['status']
            user_can_only_cancel = (
                request
                and not request.user.is_staff
                and next_status != 'cancelled'
            )
            if user_can_only_cancel:
                raise serializers.ValidationError({
                    'status': 'Customers can only cancel orders.',
                })
            if (
                next_status == 'cancelled'
                and self.instance.status in {
                    'cancelled', 'shipped', 'delivered',
                }
            ):
                raise serializers.ValidationError({
                    'status': 'This order cannot be cancelled.',
                })

        if items:
            quantities_by_product: dict[int, int] = {}
            for item in items:
                product = item['product']
                quantities_by_product[product.id] = (
                    quantities_by_product.get(product.id, 0) + item['quantity']
                )
            product_ids = list(quantities_by_product.keys())
            products = Product.objects.in_bulk(product_ids)
            for product_id, quantity in quantities_by_product.items():
                product = products[product_id]
                if product.stock < quantity:
                    raise serializers.ValidationError({
                        'items': (
                            f'Not enough stock for product: {product.name}.'
                        ),
                    })

        return attrs

    def create(self, validated_data: dict[str, Any]) -> Order:
        """
        Create a new order with items and update product stock.

        Performs atomic operation to ensure data consistency:
        - Creates order
        - Creates order items
        - Updates product stock
        - Calculates total price

        Args:
            validated_data: Validated order data including items.

        Returns:
            Order: Created order instance with calculated total price.

        Raises:
            serializers.ValidationError: If stock is insufficient.
        """
        request = self.context['request']
        items_data = validated_data.pop('items')

        with transaction.atomic():
            product_ids = [item['product'].id for item in items_data]
            products = Product.objects.select_for_update().in_bulk(product_ids)

            order = Order.objects.create(user=request.user, **validated_data)
            for item in items_data:
                product = products[item['product'].id]
                quantity = item['quantity']
                if product.stock < quantity:
                    raise serializers.ValidationError({
                        'items': (
                            f'Not enough stock for product: {product.name}.'
                        ),
                    })

                product.stock -= quantity
                product.save(update_fields=['stock'])
                OrderItem.objects.create(
                    order=order,
                    product=product,
                    quantity=quantity,
                    price=product.price,
                )

            order.update_total_price()
            order.refresh_from_db(fields=['total_price'])
            return order


class RegisterSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration.

    Password is write-only and hashed automatically via create_user().

    Attributes:
        model: User model class.
        fields: List of fields to serialize.
        read_only_fields: List of read-only fields.
        extra_kwargs: Additional field configurations.
    """
    class Meta:
        model = get_user_model()
        fields = ['id', 'username', 'email', 'password']
        read_only_fields = ['id']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data: dict[str, Any]) -> Any:
        """
        Create a new user with hashed password.

        Args:
            validated_data: Validated user data.

        Returns:
            Any: Created user instance.
        """
        return get_user_model().objects.create_user(**validated_data)


class CartItemSerializer(serializers.Serializer):
    """
    Serializer for cart item operations (add/update).

    Validates product availability and stock before adding to cart.

    Attributes:
        product: Primary key related field for active products.
        quantity: Integer field with minimum value of 1.
    """
    product = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.filter(is_active=True)
    )
    quantity = serializers.IntegerField(min_value=1)

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        """
        Validate cart item data.

        Checks if sufficient stock is available for the requested quantity.

        Args:
            attrs: Validated attributes dictionary.

        Returns:
            dict[str, Any]: Validated attributes.

        Raises:
            serializers.ValidationError: If stock is insufficient.
        """
        product = attrs['product']
        quantity = attrs['quantity']
        if product.stock < quantity:
            raise serializers.ValidationError('Not enough stock available')
        return attrs


class CartSerializer(serializers.Serializer):
    """
    Serializer for cart response.

    Contains list of cart items with their details.

    Attributes:
        items: List of CartItemSerializer instances.
    """
    items = CartItemSerializer(many=True)


class ReviewSerializer(serializers.ModelSerializer):
    """
    Serializer for product reviews.

    User and product are set automatically from request context.
    Provides read-only access to user information.

    Attributes:
        user: String representation of the reviewer.
        model: Review model class.
        fields: List of fields to serialize.
        read_only_fields: List of read-only fields.
    """
    user = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Review
        fields = ['id', 'product', 'user', 'rating', 'comment', 'created_at']
        read_only_fields = ['id', 'product', 'user', 'created_at']
