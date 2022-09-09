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

    def __str__(self):
        return '%s' % self.name
