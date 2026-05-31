from django.shortcuts import render
from django.views.generic import TemplateView


class GuidesView(TemplateView):
    template_name = 'products/guides-recipes.html'

class ProductListView(TemplateView):
    template_name = 'products/product-list.html'

class ProductDetailView(TemplateView):
    template_name = 'products/product-detail.html'

