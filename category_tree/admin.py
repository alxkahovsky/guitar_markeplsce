from django.contrib import admin
from .models import ProductCategory, DefaultJSONData
from seller.admin import CategoryFilter, EndCategories
from mptt.models import TreeManyToManyField
from django.forms import SelectMultiple, CheckboxSelectMultiple


@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    fields = ['name', 'slug', 'parent', 'icon', 'is_active', 'created', 'updated']
    list_display = ['name', 'slug', 'is_active', 'created', 'updated']
    list_editable = ['is_active']
    list_filter = ['is_active', 'created', 'updated']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(DefaultJSONData)
class DefaultJSONDataAdmin(admin.ModelAdmin):
    form = EndCategories
    formfield_overrides = {TreeManyToManyField: {'widget': SelectMultiple}}
    fields = ['category', 'default_attributes']
    list_display = ['category']
    list_filter = ['category']
