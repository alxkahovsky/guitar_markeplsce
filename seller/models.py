from django.db import models
from django.core.validators import RegexValidator
from django.utils import timezone
from django.conf import settings
from mptt.models import MPTTModel, TreeForeignKey, TreeManyToManyField
from category_tree.models import ProductCategory

# from django.contrib.postgres.fields import JSONField


class Seller(models.Model):
    name = models.CharField(max_length=50, verbose_name='Наименование')
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name='Аккаунт')
    slug = models.SlugField(blank=True, null=True, max_length=200, unique=True, verbose_name='Уникальная строка')
    official_link = models.URLField(unique=True, verbose_name='Ссылка на оф. ресурс')
    proof_link = models.URLField(unique=True, verbose_name='Пруф ссылка')
    city = models.CharField(max_length=20, verbose_name='Город')
    address = models.CharField(max_length=200, verbose_name='Адрес')
    map = models.CharField(max_length=512, null=True, blank=True, verbose_name='Карта',
                                       help_text='При импорте необходимо указать атрибут ширины 100%!')
    phone_regex = RegexValidator(regex=r'^\+?1?\d{9,13}$',
                                 message="Номер телефона должен иметь формат: '+79999999999' ")
    phone_number = models.CharField(validators=[phone_regex], max_length=13, verbose_name='Номер тел. магазина',
                                    help_text='Номер телефона должен иметь формат: +79999999999')
    email = models.EmailField(verbose_name='Электронная почта')
    weekday_from = models.TimeField(default=None, verbose_name='Пн-пт с:',
                                    help_text='Начало рабочего дня по будням')
    weekday_to = models.TimeField(default=None, verbose_name='Пн-пт до:',
                                  help_text='Конец рабочего дня по будням')
    saturday_from = models.TimeField(default=None, blank=True, verbose_name='Сб с:',
                                     help_text='Начало рабочего дня в субботу')
    saturday_to = models.TimeField(default=None, blank=True, verbose_name='Сб до:',
                                   help_text='Конец рабочего дня в субботу')
    sunday_from = models.TimeField(default=None, blank=True, verbose_name='Вс с:',
                                   help_text='Начало рабочего дня в воскресенье')
    sunday_to = models.TimeField(default=None, blank=True, verbose_name='Вс до:',
                                 help_text='Конец рабочего дня в воскресенье')
    is_active = models.BooleanField(default=True, verbose_name='Активность магазина')
    created = models.DateField(blank=True, null=True, default=timezone.now, verbose_name='Дата создания записи')
    updated = models.DateField(blank=True, null=True, auto_now=True, verbose_name='Дата ред-ия записи')

    def __str__(self):
        return '%s' % self.name


class Product(models.Model):
    shop = models.ForeignKey(Seller, default=None, null=True, on_delete=models.CASCADE, verbose_name='Продавец',
                             related_name='product_list', help_text='Заполняется автоматически')
    category = TreeManyToManyField(ProductCategory, blank=True, symmetrical=False, related_name='products',
                                   verbose_name='Категория->Подкатегория')
    name = models.CharField(max_length=50, verbose_name='Наименование')
    slug = models.SlugField(unique=True, verbose_name='Уникальная строка')
    brand = models.CharField(max_length=50, verbose_name='Бренд/Производитель')
    model = models.CharField(max_length=50, verbose_name='Модель')
    code = models.CharField(max_length=16, db_index=True, unique=True, default=None, verbose_name='Код товара',
                            help_text="Код товара должен быть в числовом виде формата: <em>000000</em>.")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Цена')
    # text_description = RichTextUploadingField(max_length=10000, blank=True, verbose_name='Описание товара')
    attributes = models.JSONField(blank=True, null=True, verbose_name='Атрибуты', help_text='используйте JSON-формат')
    available = models.BooleanField(default=True, verbose_name='Доступен к покупке')





class ProductPhotos(models.Model):
    product = models.ForeignKey(Product, blank=True, null=True, default=None, on_delete=models.CASCADE,
                                verbose_name='Товар')
    image = models.ImageField(upload_to='product_photos/', blank=True,
                                verbose_name='Фотография товара', help_text='Иконка должна быть размерами 27х27 png')
    is_main = models.BooleanField(default=False, verbose_name='Основная фотография')
    created = models.DateField(blank=True, null=True, default=timezone.now, verbose_name='Дата создания записи')
    updated = models.DateField(blank=True, null=True, default=timezone.now, verbose_name='Дата ред-ия записи')
