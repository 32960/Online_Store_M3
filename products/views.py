from PIL.ImageFilter import DETAIL
from django.shortcuts import render
from django.views.generic import TemplateView, ListView, DetailView

from products.models import Product, Category


class GuidesView(TemplateView):
    template_name = 'products/guides-recipes.html'


class ProductListView(ListView):
    model = Product
    template_name = 'products/product-list.html'
    context_object_name = 'products'
    queryset = Product.objects.filter(is_active= True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all().values('name')
        return context


class ProductDetailView(DetailView):
    model = Product
    template_name = 'products/product-detail.html'
    slug_url_kwarg = 'slug'

