from decimal import Decimal
from django.db.models import Avg

from products.models import Product
from reviews.models import Review


def recalculate_product_rating(product: Product) -> None:
    """
    Update product rating.
    """
    rating = Review.objects.filter(product=product).aggregate(
        value=Avg('rating'),
    )['value']

    product.rating = Decimal(str(rating or 0)).quantize(Decimal('0.1'))
    product.save(update_fields=['rating'])
