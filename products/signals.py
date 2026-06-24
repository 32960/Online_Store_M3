from django.db.models.signals import post_save
from django.dispatch import receiver

from reviews.models import Review
from products.services import recalculate_product_rating


@receiver(post_save, sender=Review)
def update_product_rating(sender, instance: Review, **kwargs):
    recalculate_product_rating(instance.product)