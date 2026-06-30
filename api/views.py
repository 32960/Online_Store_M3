"""
API views for the Hop & Barley online store.

This module provides REST API endpoints for:
- Products catalog (read-only)
- Categories (read-only)
- Orders management (CRUD with JWT authentication)
- Shopping cart operations
- Product reviews
- User registration and JWT authentication
"""
from api.serializers import ProductListSerializer, ProductDetailSerializer, CategorySerializer, OrderSerializer, \
    RegisterSerializer, CartItemSerializer, CartSerializer, ReviewSerializer

from decimal import Decimal
from django.db import transaction, IntegrityError
from django.db.models import QuerySet
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend

from orders.cart import (
    clear_cart,
    get_cart_items,
    get_cart_total,
    remove_from_cart,
    set_quantity, get_cart,
)
from orders.models import Order

from products.models import Product, Category

from rest_framework import filters, permissions, status, viewsets
from rest_framework.authentication import SessionAuthentication
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.generics import CreateAPIView
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication

from reviews.models import Review
from reviews.services import user_can_review

from typing import Any

from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample, OpenApiResponse
from drf_spectacular.types import OpenApiTypes

@extend_schema(tags=['Products'])
class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing products.

    Provides read-only access to the product catalog with filtering,
    searching, and ordering capabilities.

    Attributes:
        queryset: Base queryset for all products.
        serializer_class: Default serializer for list view.
        filter_backends: List of filter backends (Django filters, search, ordering).
        filterset_fields: Fields available for filtering.
        search_fields: Fields available for search.
        ordering_fields: Fields available for ordering.
        permission_classes: Permission classes (AllowAny for public access).

    Examples:
        GET /api/products/ - List all active products
        GET /api/products/?category__slug=malt - Filter by category
        GET /api/products/?search=citra - Search in name/description
        GET /api/products/?ordering=-price - Order by price descending
        GET /api/products/{slug}/ - Retrieve product details
    """
    queryset = Product.objects.all()
    serializer_class = ProductListSerializer
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = {
        'category': ['exact'],
        'category__slug': ['exact'],
        'price': ['gte', 'lte'],
    }
    search_fields = ['name', 'description', 'slug']
    ordering_fields = ['price', 'created_at', 'updated_at', 'rating']
    ordering = ['-created_at']
    permission_classes = [permissions.AllowAny]

    def get_queryset(self) -> QuerySet[Product]:
        """
        Return active products with related category.

        Returns:
            QuerySet[Product]: Filtered queryset of active products
                with prefetched category data.
        """
        queryset = super().get_queryset()
        return queryset.filter(is_active=True).select_related('category')

    def get_serializer_class(self) -> type[ProductListSerializer | ProductDetailSerializer]:
        """
        Return appropriate serializer class based on action.

        Returns:
            type[ProductListSerializer | ProductDetailSerializer]:
                ProductListSerializer for list action,
                ProductDetailSerializer for retrieve action.
        """
        if self.action == 'list':
            return ProductListSerializer
        return ProductDetailSerializer

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name='category__slug',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Filter by category slug',
                examples=[
                    OpenApiExample('Malt', value='malt'),
                    OpenApiExample('Hops', value='hops'),
                ]
            ),
            OpenApiParameter(
                name='price__gte',
                type=OpenApiTypes.FLOAT,
                location=OpenApiParameter.QUERY,
                description='Minimum price',
            ),
            OpenApiParameter(
                name='price__lte',
                type=OpenApiTypes.FLOAT,
                location=OpenApiParameter.QUERY,
                description='Maximum price',
            ),
            OpenApiParameter(
                name='search',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Search in name, description, slug',
            ),
            OpenApiParameter(
                name='ordering',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Order by field (prefix with - for descending)',
                examples=[
                    OpenApiExample('Price ascending', value='price'),
                    OpenApiExample('Price descending', value='-price'),
                    OpenApiExample('Rating', value='-rating'),
                ]
            ),
        ]
    )

    def list(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        List all active products with filtering, searching, and ordering.

        Args:
            request: HTTP request object.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.

        Returns:
            Response: Paginated list of products with metadata.
        """
        return super().list(request, *args, **kwargs)


@extend_schema(tags=['Categories'])
class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing product categories.

    Provides read-only access to the category hierarchy.

    Attributes:
        queryset: Base queryset for all categories.
        serializer_class: Serializer for category data.
        permission_classes: Permission classes (AllowAny for public access).

    Examples:
        GET /api/categories/ - List all categories
        GET /api/categories/{id}/ - Retrieve category details
    """
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.AllowAny]
    ordering = ['name']


@extend_schema(tags=['Orders'])
class OrderViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing orders.

    Provides full CRUD operations for orders with JWT authentication.
    Users can only see and manage their own orders.
    Staff users can see all orders.

    Attributes:
        queryset: Base queryset for all orders.
        serializer_class: Serializer for order data.
        filter_backends: List of filter backends.
        filterset_fields: Fields available for filtering.
        search_fields: Fields available for search.
        ordering_fields: Fields available for ordering.
        authentication_classes: Authentication classes (JWT and Session).
        permission_classes: Permission classes (IsAuthenticated).

    Examples:
        GET /api/orders/ - List user's orders
        POST /api/orders/ - Create new order
        GET /api/orders/{id}/ - Retrieve order details
        PUT /api/orders/{id}/ - Update order
        DELETE /api/orders/{id}/ - Cancel order
    """
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status']
    search_fields = ['user__username', 'user__email']
    ordering_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self) -> QuerySet[Order]:
        """
        Return orders with prefetched items and products.

        For staff users, returns all orders.
        For regular users, returns only their own orders.

        Returns:
            QuerySet[Order]: Filtered queryset with prefetched related data.
        """

        user = self.request.user
        queryset = Order.objects.prefetch_related('items__product')
        if user.is_staff:
            return queryset
        return queryset.filter(user=user)

    def perform_destroy(self, instance: Order) -> None:
        """
        Cancel order and restore product stock.

        Args:
            instance: Order instance to cancel.

        Raises:
            ValidationError: If order status is 'shipped', 'delivered', or 'cancelled'.
        """
        if instance.status in {'shipped', 'delivered', 'cancelled'}:
            raise ValidationError('This order cannot be cancelled.')

        with transaction.atomic():
            # Restore stock for each item
            for item in instance.items.select_related('product'):
                product = item.product
                product.stock += item.quantity
                product.save(update_fields=['stock'])

            instance.status = 'cancelled'
            instance.save(update_fields=['status', 'updated_at'])

    @extend_schema(
        request=OrderSerializer,
        responses={
            201: OrderSerializer,
            400: OpenApiResponse(description='Validation error'),
        },
        tags=['Orders'],
        examples=[
            OpenApiExample(
                'Create Order',
                value={
                    'full_name': 'John Doe',
                    'phone': '+1234567890',
                    'city': 'New York',
                    'shipping_address': '123 Main St',
                    'payment_method': 'debit',
                    'items': [
                        {'product': 1, 'quantity': 2},
                        {'product': 3, 'quantity': 1},
                    ]
                },
                request_only=True,
            ),
        ]
    )
    def create(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        Create a new order.

        Args:
            request: HTTP request object with order data.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.

        Returns:
            Response: Created order data with status 201.

        Raises:
            ValidationError: If order data is invalid or stock is insufficient.
        """
        return super().create(request, *args, **kwargs)


@extend_schema(tags=['Authentication'])
class RegisterView(CreateAPIView):
    """
    Register a new user.

    Provides user registration endpoint with automatic password hashing.

    Attributes:
        serializer_class: Serializer for registration data.
        permission_classes: Permission classes (AllowAny for public access).

    Examples:
        POST /api/users/register/ - Register new user
        {
            "username": "john_doe",
            "email": "john@example.com",
            "password": "secure_password"
        }
    """
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]


@extend_schema(
    tags=['Cart'],
    description='Shopping cart operations. Supports both JWT and session authentication.',
)
class CartAPIView(APIView):
    """
    Shopping cart endpoint.

    Provides cart management operations with support for both JWT
    and session authentication. Cart data is stored in session.

    Attributes:
        serializer_class: Serializer for cart response.
        authentication_classes: Authentication classes (JWT and Session).
        permission_classes: Permission classes (AllowAny for guest access).

    Examples:
        GET /api/cart/ - Retrieve cart contents
        POST /api/cart/ - Add item to cart
        PATCH /api/cart/ - Update item quantity
        DELETE /api/cart/ - Remove item or clear cart
    """

    serializer_class = CartSerializer
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    permission_classes = [permissions.AllowAny]

    def get(self, request: Request) -> Response:
        """
        Retrieve cart contents.

        Args:
            request: HTTP request object.

        Returns:
            Response: Cart data with items and total price.
        """
        return Response(self.get_cart_payload(request))

    @extend_schema(
        request=CartItemSerializer,
        responses=CartSerializer,
        examples=[
            OpenApiExample(
                'Add to Cart',
                value={'product': 1, 'quantity': 2},
                request_only=True,
            ),
        ]
    )
    def post(self, request: Request) -> Response:
        """
        Add item to cart or update quantity if already exists.

        Args:
            request: HTTP request object with product ID and quantity.

        Returns:
            Response: Updated cart data with status 201.

        Raises:
            ValidationError: If product doesn't exist or stock is insufficient.
        """
        serializer = CartItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        product = serializer.validated_data['product']
        quantity = serializer.validated_data['quantity']
        success, message = set_quantity(request, product, quantity)
        if not success:
            raise ValidationError(message)
        return Response(
            self.get_cart_payload(request),
            status=status.HTTP_201_CREATED,
        )

    @extend_schema(
        request=CartItemSerializer,
        responses=CartSerializer,
        examples=[
            OpenApiExample(
                'Update Quantity',
                value={'product': 1, 'quantity': 5},
                request_only=True,
            ),
        ]
    )
    def patch(self, request: Request) -> Response:
        """
        Update item quantity in cart.

        Args:
            request: HTTP request object with product ID and new quantity.

        Returns:
            Response: Updated cart data.

        Raises:
            ValidationError: If product doesn't exist or stock is insufficient.
        """
        serializer = CartItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        product = serializer.validated_data['product']
        quantity = serializer.validated_data['quantity']
        success, message = set_quantity(request, product, quantity)
        if not success:
            raise ValidationError(message)
        return Response(self.get_cart_payload(request))

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name='product',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description='Product ID to remove. If omitted, clears entire cart.',
            ),
        ],
        responses=CartSerializer,
    )
    def delete(self, request: Request) -> Response:
        """
        Remove item from cart or clear entire cart.

        Args:
            request: HTTP request object with optional product ID.

        Returns:
            Response: Updated cart data.
        """
        product_id = (
            request.data.get('product')
            or request.query_params.get('product')
        )
        if product_id:
            product = get_object_or_404(Product, id=product_id)
            remove_from_cart(request, product)
        else:
            clear_cart(request)
        return Response(self.get_cart_payload(request))

    @staticmethod
    def get_cart_payload(request: Request) -> dict[str, Any]:
        """
        Return cart payload with price change warnings.

        Compares current product prices with session-stored prices
        and includes warnings if prices have changed.

        Args:
            request: HTTP request object.

        Returns:
            dict[str, Any]: Cart data with items and total price.
                Each item includes:
                - product: Product ID
                - name: Product name
                - price: Current price
                - quantity: Quantity in cart
                - subtotal: Total for this item
                - stock: Available stock
                - price_changed: Boolean flag if price changed
                - old_price: Previous price (if changed)
        """
        cart = get_cart(request)
        items = []

        for product, quantity in get_cart_items(request):
            actual_price = product.price
            subtotal = actual_price * quantity

            session_price_str = cart.get(str(product.id), {}).get('price')
            session_price = Decimal(session_price_str) if session_price_str else actual_price
            price_changed = session_price != actual_price

            items.append({
                'product': product.id,
                'name': product.name,
                'price': str(actual_price),
                'quantity': quantity,
                'subtotal': str(subtotal.quantize(Decimal('0.01'))),
                'stock': product.stock,
                'price_changed': price_changed,
                'old_price': str(session_price) if price_changed else None,
            })

        return {
            'items': items,
            'total': str(get_cart_total(request)),
        }


@extend_schema(tags=['Reviews'])
class ProductReviewView(CreateAPIView):
    """
    Product reviews endpoint.

    Provides public read access and authenticated write access
    to product reviews. Users can only review products they've purchased.

    Attributes:
        serializer_class: Serializer for review data.
        authentication_classes: Authentication classes (JWT and Session).

    Examples:
        GET /api/products/{id}/reviews/ - List product reviews
        POST /api/products/{id}/reviews/ - Create review (authenticated)
    """
    serializer_class = ReviewSerializer
    authentication_classes = [JWTAuthentication, SessionAuthentication]

    def get_permissions(self) -> list[permissions.BasePermission]:
        """
        Return permission classes based on request method.

        GET requests are public, other methods require authentication.

        Returns:
            list[permissions.BasePermission]: List of permission instances.
        """
        if self.request.method == 'GET':
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    @extend_schema(
        responses=ReviewSerializer(many=True),
        description='List all reviews for a specific product.'
    )
    def get(self, request: Request, product_id: int) -> Response:
        """
        List all reviews for a specific product.

        Args:
            request: HTTP request object.
            product_id: ID of the product.

        Returns:
            Response: List of reviews with user information.
        """
        queryset = Review.objects.filter(
            product_id=product_id,
        ).select_related('user')
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @extend_schema(
        request=ReviewSerializer,
        responses={
            201: ReviewSerializer,
            400: OpenApiResponse(description='Already reviewed or other validation error'),
            403: OpenApiResponse(description='User has not purchased this product'),
        },
        examples=[
            OpenApiExample(
                'Create Review',
                value={
                    'rating': 5,
                    'comment': 'Excellent product! Highly recommended.',
                },
                request_only=True,
            ),
        ]
    )
    def perform_create(self, serializer: ReviewSerializer) -> None:
        """
        Create a review, ensuring user hasn't reviewed this product before.

        Args:
            serializer: Review serializer instance.

        Raises:
            ValidationError: If user has already reviewed this product.
            PermissionDenied: If user has not purchased this product.
        """
        with transaction.atomic():
            product = Product.objects.select_for_update().get(
                id=self.kwargs['product_id'],
                is_active=True,
            )

            can_review, error_message = user_can_review(self.request.user, product)
            if not can_review:
                if error_message and 'already reviewed' in error_message:
                    raise ValidationError(error_message)
                else:
                    raise PermissionDenied(error_message)

            try:
                serializer.save(product=product, user=self.request.user)
            except IntegrityError:
                raise ValidationError('You have already reviewed this product.')
