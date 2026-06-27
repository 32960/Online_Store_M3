from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction, IntegrityError
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import CreateView
from django.contrib import messages

from products.models import Product
from reviews.forms import ReviewForm
from reviews.models import Review
from reviews.services import user_can_review


class ReviewCreateView(LoginRequiredMixin, CreateView):
    model = Review
    form_class = ReviewForm
    template_name = 'reviews/review_form.html'

    def dispatch(self, request, *args, **kwargs):
        """Access rights check before request processing."""
        if not request.user.is_authenticated:
            messages.error(request, 'You must be logged in to leave a review.')
            return redirect('products:product-detail', slug=kwargs['slug'])

        self.product = get_object_or_404(Product, slug=kwargs['slug'])

        can_review, error_message = user_can_review(request.user, self.product)
        if not can_review:
            messages.error(request, error_message)
            return redirect('products:product-detail', slug=kwargs['slug'])
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        """Saving a review linked to a product and a user."""
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

    def get_success_url(self):
        """Redirect to the product page after creating a review."""
        return self.product.get_absolute_url()

    def get_context_data(self, **kwargs):
        """Adding a product to the context."""
        context = super().get_context_data(**kwargs)
        context['product'] = self.product
        return context
