# Generated manually for wms_builder app

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.core.validators


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Warehouse',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200, verbose_name='Nazwa magazynu')),
                ('description', models.TextField(blank=True, verbose_name='Opis')),
                ('width', models.DecimalField(decimal_places=2, default=1000.0, max_digits=10, validators=[django.core.validators.MinValueValidator(1.0)], verbose_name='Szerokość (jednostki)')),
                ('height', models.DecimalField(decimal_places=2, default=1000.0, max_digits=10, validators=[django.core.validators.MinValueValidator(1.0)], verbose_name='Wysokość (jednostki)')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Utworzono')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Zaktualizowano')),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL, verbose_name='Utworzył')),
            ],
            options={
                'verbose_name': 'Magazyn',
                'verbose_name_plural': 'Magazyny',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='WarehouseZone',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200, verbose_name='Nazwa strefy')),
                ('x', models.DecimalField(decimal_places=2, default=0.0, max_digits=10, verbose_name='Pozycja X')),
                ('y', models.DecimalField(decimal_places=2, default=0.0, max_digits=10, verbose_name='Pozycja Y')),
                ('color', models.CharField(default='#007bff', max_length=7, verbose_name='Kolor')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Utworzono')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Zaktualizowano')),
                ('warehouse', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='zones', to='wms_builder.warehouse', verbose_name='Magazyn')),
            ],
            options={
                'verbose_name': 'Strefa',
                'verbose_name_plural': 'Strefy',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='WarehouseRack',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200, verbose_name='Nazwa regału')),
                ('x', models.DecimalField(decimal_places=2, default=0.0, max_digits=10, verbose_name='Pozycja X')),
                ('y', models.DecimalField(decimal_places=2, default=0.0, max_digits=10, verbose_name='Pozycja Y')),
                ('color', models.CharField(default='#28a745', max_length=7, verbose_name='Kolor')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Utworzono')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Zaktualizowano')),
                ('zone', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='racks', to='wms_builder.warehousezone', verbose_name='Strefa')),
            ],
            options={
                'verbose_name': 'Regał',
                'verbose_name_plural': 'Regały',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='WarehouseShelf',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200, verbose_name='Nazwa półki')),
                ('x', models.DecimalField(decimal_places=2, default=0.0, max_digits=10, verbose_name='Pozycja X')),
                ('y', models.DecimalField(decimal_places=2, default=0.0, max_digits=10, verbose_name='Pozycja Y')),
                ('color', models.CharField(default='#ffc107', max_length=7, verbose_name='Kolor')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Utworzono')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Zaktualizowano')),
                ('rack', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='shelves', to='wms_builder.warehouserack', verbose_name='Regał')),
            ],
            options={
                'verbose_name': 'Półka',
                'verbose_name_plural': 'Półki',
                'ordering': ['name'],
            },
        ),
    ]

