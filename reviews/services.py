from orders.models import OrderItem
from reviews.models import Review


def user_bought_product(user, product) -> bool:
    """
    Check if user has purchased the product.

    Args:
        user: User instance
        product: Product instance

    Returns:
        bool: True if user has purchased the product with paid/shipped/delivered status
    """
    return OrderItem.objects.filter(
        order__user=user,
        order__status__in=['paid', 'shipped', 'delivered'],
        product=product,
    ).exists()


def user_already_reviewed(user, product) -> bool:
    """
    Check if user has already reviewed the product.

    Args:
        user: User instance
        product: Product instance

    Returns:
        bool: True if user has already reviewed the product
    """
    return Review.objects.filter(
        product=product,
        user=user,
    ).exists()


def user_can_review(user, product) -> tuple[bool, str | None]:
    """
    Check if user can review the product.

    Args:
        user: User instance
        product: Product instance

    Returns:
        tuple[bool, str | None]: (can_review, error_message)
            - can_review: True if user can review
            - error_message: Error message if user cannot review, None otherwise
    """
    if not user_bought_product(user, product):
        return False, 'You can only review products you have purchased.'

    if user_already_reviewed(user, product):
        return False, 'You have already reviewed this product.'

    return True, None