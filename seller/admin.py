from django.contrib import admin
from .models import Product, ProductPhotos, Seller
from django.shortcuts import render, get_object_or_404, redirect
from django.core.exceptions import ValidationError
from django import forms
from django.forms import SelectMultiple
from mptt.admin import MPTTModelAdmin
from mptt.models import TreeManyToManyField
from category_tree.models import ProductCategory
from django.contrib import admin
from mptt.admin import MPTTModelAdmin
from django.contrib.admin import SimpleListFilter


class ProductPhotoInline(admin.TabularInline):
    model = ProductPhotos
    extra = 0
    readonly_fields = ['created', 'updated']


class EndCategories(forms.ModelForm):
    """Переопределяем форму, для отображения ТОЛЬКО конечных категорий"""
    class Meta:
        model = Product
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super(EndCategories, self).__init__(*args, **kwargs)
        self.fields['category'].queryset = ProductCategory.objects.filter(children=None)
        self.fields['category'].level_indicator = ''
        self.fields['category'].help_text = 'Используйте "Ctrl" для выбора нескольких категорий'


class CategoryFilter(SimpleListFilter):
    """Переопределяем фильтр для фильтрации по товарам продавца с отображением ТОЛЬКО конечных категорий"""
    title = 'Категория'
    parameter_name = 'category'

    def lookups(self, request, model_admin):
        shop = get_object_or_404(Seller, user=request.user)
        categories = set([c.category.last() for c in model_admin.model.objects.filter(shop=shop)])
        return [(c.name, c) for c in categories if c is not None]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(category__name=self.value())


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    form = EndCategories
    formfield_overrides = {TreeManyToManyField: {'widget': SelectMultiple}}

    def get_queryset(self, request):
        qs = super(ProductAdmin, self).get_queryset(request)
        shop = get_object_or_404(Seller, user=request.user)
        return qs.filter(shop=shop)

    def save_model(self, request, instance, form, change):
        shop = get_object_or_404(Seller, user=request.user)
        instance = form.save(commit=False)
        if not change or not instance.shop:
            instance.shop = shop
        instance.shop = shop
        instance.save()
        form.save_m2m()
        return instance

    fields = ['category', 'name', 'slug', 'brand', 'model', 'code', 'price', 'attributes', 'available']
    list_display = ['name', 'brand', 'model', 'price', 'available']
    list_editable = ['price', 'available']
    prepopulated_fields = {'slug': ('name', 'brand', 'code')}
    inlines = [ProductPhotoInline]
    list_filter = [CategoryFilter, 'available', 'brand']


@admin.register(Seller)
class SellerAdmin(admin.ModelAdmin):
    def get_queryset(self, request):
        qs = super(SellerAdmin, self).get_queryset(request)
        return qs.filter(user=request.user)

    def save_model(self, request, instance, form, change):
        user = request.user
        instance = form.save(commit=False)
        if not change or not instance.user:
            instance.user = user
        instance.user = user
        instance.save()
        form.save_m2m()
        return instance
    fields = [('name', 'user'), 'slug', ('official_link', 'proof_link'), ('city', 'address', 'map', 'phone_number',
              'email'), ('weekday_from', 'weekday_to', 'saturday_from', 'saturday_to', 'sunday_from', 'sunday_to'),
              'is_active']
    list_display = ['name', 'is_active']
    list_editable = ['is_active']
    list_filter = ['is_active', 'created', 'updated']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['created', 'updated', 'user']
