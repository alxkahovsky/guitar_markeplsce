from django.contrib import admin
from .models import Product, ProductPhotos, Seller
from django.shortcuts import render, get_object_or_404, redirect
from django.core.exceptions import ValidationError
from django import forms
from django.forms import SelectMultiple, CheckboxSelectMultiple
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
from transliterate import translit
from transliterate.utils import LanguageDetectionError
from django.utils.safestring import mark_safe
from django.urls import reverse


class ProductPhotoInline(admin.TabularInline):
    """Метод для отображения фото товара в инлайне"""
    def show_detail_img(self):
        print(self.image.url)
        if self.image:
            return mark_safe(f'<img src="{self.image.url}" height="250px" width="250px">')
        else:
            return 'No image'
    show_detail_img.short_description = 'Предпросмотр'
    model = ProductPhotos
    extra = 0
    readonly_fields = [show_detail_img, 'created', 'updated']


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
    category = fields.Field(column_name='category',
                            attribute='category',
                            widget=ForeignKeyWidget(ProductCategory, field='name'))

    class Meta:
        model = Product
        fields = ['id', 'shop', 'category', 'name', 'slug', 'brand',
                  'model', 'code', 'price', 'attributes', 'available']
        export_order = ['id', 'shop', 'category', 'name', 'slug', 'brand',
                        'model', 'code', 'price', 'attributes', 'available']


class CustomImportForm(ImportForm):
    category = forms.ModelMultipleChoiceField(
        queryset=ProductCategory.objects.filter(children=None),
        required=True, widget=SelectMultiple)


class CustomConfirmImportForm(ConfirmImportForm):
    category = forms.ModelMultipleChoiceField(
        queryset=ProductCategory.objects.filter(children=None),
        required=True, widget=SelectMultiple)


class CustomShopAdmin(ImportMixin, admin.ModelAdmin):
    resource_class = ProductResource
    form = EndCategories
    formfield_overrides = {TreeManyToManyField: {'widget': SelectMultiple}}

    def get_import_form(self):
        return CustomImportForm

    def get_confirm_import_form(self):
        return CustomConfirmImportForm

    def get_form_kwargs(self, form, *args, **kwargs):
        if isinstance(form, CustomImportForm):
            if form.is_valid():
                category = form.cleaned_data['category']
                kwargs.update({'category': str(category.last().name)})
        return kwargs

    def _change_dataset(self, request, dataset):
        """Автозаполнение id, slug, shop полей"""
        user_dataset = tablib.Dataset()
        headers = dataset.headers
        headers[10] = 'shop'
        user_dataset.headers = headers
        shop = get_object_or_404(Seller, user=request.user)
        seller_products = Product.objects.filter(shop=shop)
        id = 1
        for row in dataset:
            row = list(row)
            row[10] = shop.id
            if row[0] not in [sp.id for sp in seller_products]:
                id += 1
                while len(Product.objects.filter(id=id)) > 0:
                    id += 1
                row[0] = id
            if row[3] is None:
                slug_dict = {
                    'name': str(row[2]),
                    'brand': str(row[4]),
                    'model': str(row[5]),
                    'id': str(row[0])
                }
                for key, value in slug_dict.items():
                    try:
                        str_translation = translit(value, reversed=True).replace(' ', '-')
                        slug_dict[key] = str_translation.lower()
                    except LanguageDetectionError:
                        slug_dict[key] = value.lower()
                        continue
                row[3] = f'{slug_dict["name"]}-{slug_dict["brand"]}-{slug_dict["model"]}-{slug_dict["id"]}'
            user_dataset.append(row)
        return user_dataset

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
                int(confirm_form.cleaned_data['input_format'])]()
            tmp_storage = self.get_tmp_storage_class()(name=confirm_form.cleaned_data['import_file_name'])
            data = tmp_storage.read(input_format.get_read_mode())
            if not input_format.is_binary() and self.from_encoding:
                data = force_str(data, self.from_encoding)
            #  используем кастомный метод change_dataset в котором вносим нужные нам изменения
            dataset = self._change_dataset(request, input_format.create_dataset(data))
            result = self.process_dataset(dataset, confirm_form, request, *args, **kwargs)
            tmp_storage.remove()
            return self.process_result(result, request)

    def import_action(self, request, *args, **kwargs):
        """
        Perform a dry_run of the import to make sure the import will not
        result in errors.  If there where no error, save the user
        uploaded file to a local temp file that will be used by
        'process_import' for the actual import.
        """
        if not self.has_import_permission(request):
            raise PermissionDenied
        context = self.get_import_context_data()
        import_formats = self.get_import_formats()
        form_type = self.get_import_form()
        form_kwargs = self.get_form_kwargs(form_type, *args, **kwargs)
        form = form_type(import_formats,
                         request.POST or None,
                         request.FILES or None,
                         **form_kwargs)
        if request.POST and form.is_valid():
            input_format = import_formats[
                int(form.cleaned_data['input_format'])]()
            import_file = form.cleaned_data['import_file']
            tmp_storage = self.write_to_tmp_storage(import_file, input_format)
            try:
                data = tmp_storage.read(input_format.get_read_mode())
                if not input_format.is_binary() and self.from_encoding:
                    data = force_str(data, self.from_encoding)
                #  используем кастомный метод change_dataset в котором вносим нужные нам изменения
                dataset = self._change_dataset(request, input_format.create_dataset(data))
            except UnicodeDecodeError as e:
                return HttpResponse(_(u"<h1>Imported file has a wrong encoding: %s</h1>" % e))
            except Exception as e:
                return HttpResponse(_(u"<h1>%s encountered while trying to read file: %s</h1>" %
                                      (type(e).__name__, import_file.name)))
            res_kwargs = self.get_import_resource_kwargs(request, form=form, *args, **kwargs)
            resource = self.get_import_resource_class()(**res_kwargs)
            # подготовка kwargs для import_data, если необходимо
            imp_kwargs = self.get_import_data_kwargs(request, form=form, *args, **kwargs)
            result = resource.import_data(dataset, dry_run=True,
                                          raise_errors=False,
                                          file_name=import_file.name,
                                          user=request.user,
                                          **imp_kwargs)
            context['result'] = result
            if not result.has_errors() and not result.has_validation_errors():
                initial = {
                    'import_file_name': tmp_storage.name,
                    'original_file_name': import_file.name,
                    'input_format': form.cleaned_data['input_format'],
                }
                confirm_form = self.get_confirm_import_form()
                initial = self.get_form_kwargs(form=form, **initial)
                context['confirm_form'] = confirm_form(initial=initial)
        else:
            res_kwargs = self.get_import_resource_kwargs(request, form=form, *args, **kwargs)
            resource = self.get_import_resource_class()(**res_kwargs)
        context.update(self.admin_site.each_context(request))
        context['title'] = "Import"
        context['form'] = form
        context['opts'] = self.model._meta
        context['fields'] = [f.column_name for f in resource.get_user_visible_fields()]
        request.current_app = self.admin_site.name
        return TemplateResponse(request, [self.import_template_name],
                                context)

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

    def show_main_img(self):
        """Показываем миниатюру изображения для товара"""
        main_img = None
        product_images = ProductPhotos.objects.filter(product=self.id)
        if len(product_images) != 0:
            for i in product_images:
                if i.is_main:
                    main_img = i
            if main_img is None:
                main_img = product_images[0]
        if main_img is not None:
            return mark_safe(f'<img src="{main_img.image.url}" alt="{self.name}" height="100px" width="100px">')
        else:
            return 'No image'

    show_main_img.short_description = 'Фото'

    def add_json_attrs(self):
        return mark_safe(f'<a href="{reverse("seller:add_json_attrs", args=[self.id])}">Добавить атрибуты</a>')

    fields = ['shop', 'category', 'name', 'slug', 'brand', 'model', 'code', 'price', 'attributes', 'available']
    list_display = ['name', 'brand', 'model', 'price', 'available', show_main_img, add_json_attrs]
    list_editable = ['price', 'available']
    prepopulated_fields = {'slug': ('name', 'brand')}
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
