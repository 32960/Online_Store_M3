from decimal import Decimal
from django.db.models import Avg
from django.shortcuts import get_object_or_404
from rest_framework import filters, permissions, status, viewsets
from rest_framework.authentication import SessionAuthentication
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView
from orders.cart import (
    clear_cart,
    get_cart_items,
    get_cart_total,
    remove_from_cart,
    set_quantity,
)
from reviews.models import Review

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework_simplejwt.authentication import JWTAuthentication

from api.serializers import ProductListSerializer, ProductDetailSerializer, CategorySerializer, OrderSerializer, \
    RegisterSerializer, CartItemSerializer, CartSerializer, ReviewSerializer
from orders.models import Order, OrderItem
from products.models import Product, Category

from rest_framework.generics import CreateAPIView


class ProductViewSet(viewsets.ReadOnlyModelViewSet):
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

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.filter(is_active=True)

    def get_serializer_class(self):
        if self.action == 'list':
            return ProductListSerializer
        return ProductDetailSerializer


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.AllowAny]


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status']
    search_fields = ['user__username', 'user__email']
    ordering_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return Order.objects.none()
        if user.is_staff:
            return Order.objects.all()
        return Order.objects.filter(user=user)

    def perform_destroy(self, instance):
        if instance.status in {'shipped', 'delivered', 'cancelled'}:
            raise ValidationError('This order cannot be cancelled.')
        instance.status = 'cancelled'
        instance.save(update_fields=['status'])


class RegisterView(CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]


class CartAPIView(APIView):
    """Session cart endpoint usable with either JWT or browser sessions."""

    serializer_class = CartSerializer
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        return Response(self.get_cart_payload(request))

    def post(self, request):
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

    def patch(self, request):
        serializer = CartItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        product = serializer.validated_data['product']
        quantity = serializer.validated_data['quantity']
        success, message = set_quantity(request, product, quantity)
        if not success:
            raise ValidationError(message)
        return Response(self.get_cart_payload(request))

    def delete(self, request):
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
    def get_cart_payload(request):
        items = []
        for product, quantity in get_cart_items(request):
            subtotal = product.price * quantity
            items.append({
                'product': product.id,
                'name': product.name,
                'price': str(product.price),
                'quantity': quantity,
                'subtotal': str(subtotal.quantize(Decimal('0.01'))),
                'stock': product.stock,
            })
        return {
            'items': items,
            'total': str(get_cart_total(request)),
        }


class ProductReviewView(CreateAPIView):
    serializer_class = ReviewSerializer
    authentication_classes = [JWTAuthentication, SessionAuthentication]

    def get_permissions(self):
        if self.request.method == 'GET':
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    def get(self, request, product_id):
        queryset = Review.objects.filter(
            product_id=product_id,
        ).select_related('user')
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def perform_create(self, serializer):
        product = get_object_or_404(
            Product,
            id=self.kwargs['product_id'],
            is_active=True,
        )
        if not self.user_bought_product(self.request.user, product):
            raise PermissionDenied(
                'Only customers who bought this product can review it.',
            )

        serializer.save(product=product, user=self.request.user)
        rating = Review.objects.filter(product=product).aggregate(
            value=Avg('rating'),
        )['value']
        product.rating = Decimal(str(rating or 0)).quantize(Decimal('0.1'))
        product.save(update_fields=['rating'])

    @staticmethod
    def user_bought_product(user, product):
        return OrderItem.objects.filter(
            order__user=user,
            order__status__in=['paid', 'shipped', 'delivered'],
            product=product,
        ).exists()
