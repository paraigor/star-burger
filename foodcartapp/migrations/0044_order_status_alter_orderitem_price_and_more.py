# Generated by Django 4.2.9 on 2024-11-23 19:56

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('foodcartapp', '0043_auto_20241123_1806'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='status',
            field=models.CharField(choices=[('accepted', 'Принят'), ('prepared', 'Готовится'), ('delivering', 'В доставке'), ('completed', 'Выполнен'), ('canceled', 'Отменен')], db_index=True, default='accepted', max_length=20, verbose_name='Статус заказа'),
        ),
        migrations.AlterField(
            model_name='orderitem',
            name='price',
            field=models.DecimalField(db_index=True, decimal_places=2, default=0.0, max_digits=8, validators=[django.core.validators.MinValueValidator(0)], verbose_name='цена'),
        ),
        migrations.AlterField(
            model_name='orderitem',
            name='quantity',
            field=models.PositiveSmallIntegerField(db_index=True, verbose_name='Количество'),
        ),
    ]