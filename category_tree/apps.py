from django.apps import AppConfig


class CategoryTreeConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'category_tree'
    verbose_name = 'Категория товара'
    verbose_name_plural = 'Категории товаров'
