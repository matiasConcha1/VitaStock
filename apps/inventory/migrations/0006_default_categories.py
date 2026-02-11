from django.db import migrations


def add_default_categories(apps, schema_editor):
    Category = apps.get_model('inventory', 'Category')
    defaults = [
        'Alimentos', 'Bebidas', 'Limpieza', 'Higiene personal',
        'Medicamentos', 'Mascotas', 'Congelados', 'Otros'
    ]
    for name in defaults:
        Category.objects.get_or_create(name=name)


def remove_default_categories(apps, schema_editor):
    Category = apps.get_model('inventory', 'Category')
    defaults = [
        'Alimentos', 'Bebidas', 'Limpieza', 'Higiene personal',
        'Medicamentos', 'Mascotas', 'Congelados', 'Otros'
    ]
    Category.objects.filter(name__in=defaults).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0005_alter_product_unit'),
    ]

    operations = [
        migrations.RunPython(add_default_categories, remove_default_categories),
    ]
