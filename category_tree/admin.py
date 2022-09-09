from django.contrib import admin
from .models import ProductCategory


@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    fields = ['name', 'slug', 'parent', 'icon', 'is_active', 'created', 'updated']
    list_display = ['name', 'slug', 'is_active', 'created', 'updated']
    list_editable = ['is_active']
    list_filter = ['is_active', 'created', 'updated']
    prepopulated_fields = {'slug': ('name',)}

