"""
Views for review management in the Hop & Barley online store.

This module provides views for:
- Creating product reviews with permission checks
- Validating user purchase history before allowing reviews

All review operations require user authentication and purchase verification.
"""
from typing import Any

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction, IntegrityError
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import CreateView

from products.models import Product
from reviews.forms import ReviewForm
from reviews.models import Review
from reviews.services import user_can_review


class ReviewCreateView(LoginRequiredMixin, CreateView):
    """
    View for creating product reviews.

    Handles review creation with comprehensive permission checks:
    - User must be authenticated
    - User must have purchased the product
    - User must not have already reviewed the product

    Attributes:
        model: Review model class.
        form_class: ReviewForm for review data.
        template_name: Path to review form template.
        product: Product instance being reviewed (set in dispatch).

    Note:
        Uses database transactions to prevent race conditions
        when creating reviews.
    """
    model = Review
    form_class = ReviewForm
    template_name = 'reviews/review_form.html'
    product: Product

    def dispatch(
            self,
            request: HttpRequest,
            *args: Any,
            **kwargs: Any,
    ) -> HttpResponse:
        """
        Check access rights before request processing.

        Verifies:
        - User is authenticated
        - Product exists
        - User can review the product (purchased and not reviewed)

        Args:
            request: HTTP request object.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments including 'slug'.

        Returns:
            HttpResponse: Redirect with error message or dispatched response.
        """

        if not request.user.is_authenticated:
            messages.error(request, 'You must be logged in to leave a review.')
            return redirect('products:product-detail', slug=kwargs['slug'])

        self.product = get_object_or_404(Product, slug=kwargs['slug'])

        can_review, error_message = user_can_review(request.user, self.product)
        if not can_review:
            messages.error(request, error_message)
            return redirect('products:product-detail', slug=kwargs['slug'])
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form: ReviewForm) -> HttpResponse:
        """
        Save review linked to product and user.

        Uses atomic transaction to prevent duplicate reviews
        in case of race conditions.

        Args:
            form: Valid review form instance.

        Returns:
            HttpResponse: Redirect to product page with success message.
        """
        try:
            with transaction.atomic():
                form.instance.product = self.product
                form.instance.user = self.request.user
                response = super().form_valid(form)
                messages.success(self.request, 'Your review has been submitted successfully!')
                return response
        except IntegrityError:
            messages.error(self.request, 'You have already reviewed this product.')
            return redirect('products:product-detail', slug=self.product.slug)

    def get_success_url(self) -> str:
        """
        Return URL to redirect after creating a review.

        Returns:
            str: URL to the product detail page.
        """
        return self.product.get_absolute_url()

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """
        Add product to template context.

        Args:
            **kwargs: Additional keyword arguments.

        Returns:
            dict[str, Any]: Context with product instance.
        """
        context = super().get_context_data(**kwargs)
        context['product'] = self.product
        return context
