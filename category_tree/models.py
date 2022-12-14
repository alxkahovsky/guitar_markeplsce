from django.db import models
from mptt.models import MPTTModel, TreeForeignKey, TreeManyToManyField
from django.utils import timezone


class ProductCategory(MPTTModel):
    name = models.CharField(max_length=200, db_index=True, verbose_name='Подкатегория товара')
    slug = models.SlugField(max_length=200, db_index=True, unique=True, verbose_name='Уникальная строка')
    parent = TreeForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children',
                            verbose_name='Категория товара')
    icon = models.ImageField(upload_to='category_icon/', blank=True,
                             verbose_name='Иконка для категории', help_text='Иконка должна быть размерами 27х27 png')
    is_active = models.BooleanField(default=True, verbose_name='Активность категории')
    created = models.DateField(blank=True, null=True, default=timezone.now, verbose_name='Дата создания записи')
    updated = models.DateField(blank=True, null=True, default=timezone.now, verbose_name='Дата ред-ия записи')

    class MPTTMeta:
        order_insertion_by = ['name']
        verbose_name = 'Категория товаров'
        verbose_name_plural = 'Категории товаров'

    class Meta:
        verbose_name = 'Категория -> Подкатегория'
        verbose_name_plural = 'Категории -> Подкатегории'

    # def __str__(self):
    #     return '%s' % self.name

    def __str__(self):
        try:
            ancestors = self.get_ancestors(include_self=True)
            ancestors = [i.name for i in ancestors]
        except Exception as e:
            print(e)
            ancestors = [self.name]
        return ' >>> '.join(ancestors[:len(ancestors) + 1])

    def tested(self):
        try:
            ancestors = self.get_ancestors(include_self=True)
            ancestors = [i.name for i in ancestors]
        except Exception as e:
            print(e)
            ancestors = [self.name]
        return ancestors[-1]


class DefaultJSONData(models.Model):
    category = models.ForeignKey(ProductCategory, null=True, blank=True,
                                 on_delete=models.CASCADE, verbose_name='Категория')
    default_attributes = models.JSONField(blank=True, null=True, verbose_name='Атрибуты',
                                          help_text='задайте JSON-структуру по умолчанию (для данной категории)')

    class Meta:
        verbose_name = 'Атрибуты по умолчанию'
        verbose_name_plural = 'Атрибуты по умолчанию'

    def __str__(self):
        return f'JSON для товаров категории {self.category.name}'
