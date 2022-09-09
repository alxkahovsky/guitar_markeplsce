# Generated by Django 4.1.1 on 2022-09-09 10:30

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import mptt.fields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='ProductCategory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(db_index=True, max_length=200, verbose_name='Подкатегория товара')),
                ('slug', models.SlugField(max_length=200, unique=True, verbose_name='Уникальная строка')),
                ('icon', models.ImageField(blank=True, help_text='Иконка должна быть размерами 27х27 png', upload_to='category_icon/', verbose_name='Иконка для категории')),
                ('is_active', models.BooleanField(default=True, verbose_name='Активность категории')),
                ('created', models.DateField(blank=True, default=django.utils.timezone.now, null=True, verbose_name='Дата создания записи')),
                ('updated', models.DateField(blank=True, default=django.utils.timezone.now, null=True, verbose_name='Дата ред-ия записи')),
                ('lft', models.PositiveIntegerField(editable=False)),
                ('rght', models.PositiveIntegerField(editable=False)),
                ('tree_id', models.PositiveIntegerField(db_index=True, editable=False)),
                ('level', models.PositiveIntegerField(editable=False)),
                ('parent', mptt.fields.TreeForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='children', to='category_tree.productcategory', verbose_name='Категория товара')),
            ],
            options={
                'verbose_name': 'Категория -> Подкатегория',
                'verbose_name_plural': 'Категории -> Подкатегории',
            },
        ),
    ]