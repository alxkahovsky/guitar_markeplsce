from django.apps import AppConfig


class SellerConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'seller'
    verbose_name = 'Продавец'
    verbose_name_plural = 'Продавцы'
