# Generated manually for wms_builder app

from django.db import migrations, models
import django.core.validators
from decimal import Decimal


class Migration(migrations.Migration):

    dependencies = [
        ('wms_builder', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='warehousezone',
            name='width',
            field=models.DecimalField(decimal_places=2, default=Decimal('200.00'), max_digits=10, validators=[django.core.validators.MinValueValidator(Decimal('50.00'))], verbose_name='Szerokość'),
        ),
        migrations.AddField(
            model_name='warehousezone',
            name='height',
            field=models.DecimalField(decimal_places=2, default=Decimal('150.00'), max_digits=10, validators=[django.core.validators.MinValueValidator(Decimal('50.00'))], verbose_name='Wysokość'),
        ),
    ]

