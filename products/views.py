from django.db.models import Q
from django.shortcuts import render
from django.views.generic import TemplateView, ListView, DetailView

from config.settings import PRODUCT_ALLOWED_SORTING
from products.models import Product, Category


class GuidesView(TemplateView):
    template_name = 'products/guides-recipes.html'


class ProductListView(ListView):
    model = Product
    template_name = 'products/product-list.html'
    context_object_name = 'products'
    paginate_by = 6

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all().values('name', 'slug')
        sorting_data = [
            ('-created_at', 'New'),
            ('price', 'Price ascending'),
            ('-price', 'Price descending'),
            ('-rating', 'Rating'),
        ]
        checked_categories = self.request.GET.get('categories', '')
        context['checked_categories'] = checked_categories.split(',') if checked_categories else []
        context['sorting_data'] = sorting_data
        return context

    def get_queryset(self):
        queryset = Product.objects.filter(is_active= True)
        categories = self.request.GET.get('categories')
        categories = categories.split(',') if categories else []
        if categories:
            queryset = queryset.filter(category__slug__in= categories)

        sorting = self.request.GET.get('sorting', '-created_at')
        if sorting and sorting in PRODUCT_ALLOWED_SORTING:
            queryset = queryset.order_by(sorting)

        q = self.request.GET.get('q')
        if q:
            queryset = queryset.filter(Q(name__icontains= q) | Q(description__icontains= q))

        return queryset


class ProductDetailView(DetailView):
    model = Product
    template_name = 'products/product-detail.html'
    slug_url_kwarg = 'slug'
