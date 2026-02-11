from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("inventory", "0011_alter_movement_movement_type"),
    ]

    operations = [
        migrations.AddField(
            model_name="movement",
            name="destination_location",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="incoming_movements",
                to="inventory.location",
                verbose_name="Ubicación destino",
            ),
        ),
    ]
