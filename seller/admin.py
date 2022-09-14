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
from import_export import resources, fields
from import_export.admin import ImportExportModelAdmin, ImportMixin, ImportForm, ConfirmImportForm
from import_export.widgets import ForeignKeyWidget, ManyToManyWidget, Decimal, IntegerWidget, BooleanWidget
from uuid import uuid4
from django.dispatch import receiver
from import_export.signals import post_import, post_export
from django.template.response import TemplateResponse
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_POST
from django.urls import path, reverse
from django.http import HttpResponse, HttpResponseRedirect
import tablib



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



class ProductResource(resources.ModelResource):
    category = fields.Field(column_name='Категория',
                            attribute='category',
                            widget=ManyToManyWidget(ProductCategory, field='name'))
    # shop = fields.Field(column_name='Магазин', attribute='shop', widget=ForeignKeyWidget(Seller, field='name'))

    class Meta:
        model = Product
        fields = ['id', 'shop', 'category', 'name', 'slug', 'brand', 'model', 'code', 'price', 'attributes', 'available']
        export_order = ['id', 'shop', 'category', 'name', 'slug', 'brand', 'model', 'code', 'price', 'attributes', 'available']


# class CustomImportForm(ImportForm):
#     shop = forms.ModelChoiceField(
#         queryset=Seller.objects.all(),
#         required=True)
#
#
# class CustomConfirmImportForm(ConfirmImportForm):
#     shop = forms.ModelChoiceField(
#         queryset=Seller.objects.all(),
#         required=True)


class CustomShopAdmin(ImportMixin, admin.ModelAdmin):
    resource_class = ProductResource
    form = EndCategories
    formfield_overrides = {TreeManyToManyField: {'widget': SelectMultiple}}

    # def get_import_form(self):
    #     return CustomImportForm
    #
    # def get_confirm_import_form(self):
    #     return CustomConfirmImportForm
    #
    # def get_form_kwargs(self, form, *args, **kwargs):
    #     # pass on `author` to the kwargs for the custom confirm form
    #     if isinstance(form, CustomImportForm):
    #         if form.is_valid():
    #             shop = form.cleaned_data['shop']
    #
    #             kwargs.update({'shop': shop.id})
    #
    #     return kwargs
    #
    # def get_import_data_kwargs(self, request, *args, **kwargs):
    #     """
    #     Prepare kwargs for import_data.
    #     """
    #     form = kwargs.get('form')
    #     if form:
    #         kwargs.pop('form')
    #         return kwargs
    #     return {}

    @method_decorator(require_POST)
    def process_import(self, request, *args, **kwargs):
        """
        Perform the actual import action (after the user has confirmed the import)
        """
        if not self.has_import_permission(request):
            raise PermissionDenied

        form_type = self.get_confirm_import_form()
        confirm_form = form_type(request.POST)
        if confirm_form.is_valid():
            import_formats = self.get_import_formats()
            input_format = import_formats[
                int(confirm_form.cleaned_data['input_format'])
            ]()
            tmp_storage = self.get_tmp_storage_class()(name=confirm_form.cleaned_data['import_file_name'])
            data = tmp_storage.read(input_format.get_read_mode())
            if not input_format.is_binary() and self.from_encoding:
                data = force_str(data, self.from_encoding)
            dataset = input_format.create_dataset(data)
            user_dataset = tablib.Dataset()
            headers = dataset.headers
            headers[10] = 'shop'
            user_dataset.headers = headers
            shop = get_object_or_404(Seller, user=request.user)
            for row in dataset:
                row = list(row)
                row[10] = shop.id
                user_dataset.append(row)
            result = self.process_dataset(user_dataset, confirm_form, request, *args, **kwargs)
            tmp_storage.remove()

            return self.process_result(result, request)

    def get_queryset(self, request):
        qs = super(CustomShopAdmin, self).get_queryset(request)
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

    fields = ['shop', 'category', 'name', 'slug', 'brand', 'model', 'code', 'price', 'attributes', 'available']
    list_display = ['name', 'brand', 'model', 'price', 'available']
    list_editable = ['price', 'available']
    prepopulated_fields = {'slug': ('name', 'brand', 'code')}
    inlines = [ProductPhotoInline]
    list_filter = [CategoryFilter, 'available', 'brand']
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


admin.site.register(Product, CustomShopAdmin)

