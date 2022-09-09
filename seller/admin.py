from django.contrib import admin
from .models import Product, ProductPhotos, Seller
from django.shortcuts import render, get_object_or_404, redirect
from django.core.exceptions import ValidationError
from django.contrib import messages


class ProductPhotoInline(admin.TabularInline):
    model = ProductPhotos
    extra = 0
    readonly_fields = ['created', 'updated']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
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
        if not change or instance.category.last() != instance.category:
            raise ValidationError("Укажите конечную категорию")
        return instance
    fields = ['shop', 'category', 'name', 'slug', 'brand', 'model', 'code', 'price', 'attributes', 'available']
    list_display = ['name', 'brand', 'model', 'price', 'available']
    list_editable = ['price', 'available']
    prepopulated_fields = {'slug': ('name', 'brand', 'code')}
    inlines = [ProductPhotoInline]
    readonly_fields = ['shop']


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


