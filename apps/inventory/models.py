from datetime import timedelta

from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.utils import timezone


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class Location(models.Model):
    class LocationType(models.TextChoices):
        SHELF = "SHELF", "Estante"
        BOX = "BOX", "Caja"
        FURNITURE = "FURNITURE", "Mueble"
        FRIDGE = "FRIDGE", "Refrigerador"
        FREEZER = "FREEZER", "Congeladora"
        OTHER = "OTHER", "Otro"

    name = models.CharField(max_length=100, unique=True, verbose_name="Nombre")
    location_type = models.CharField(
        max_length=20,
        choices=LocationType.choices,
        default=LocationType.OTHER,
        verbose_name="Tipo de ubicación",
    )
    notes = models.TextField(blank=True, verbose_name="Notas")

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class Product(models.Model):
    class Unit(models.TextChoices):
        UNIT = "unit", "Unidad"
        KILOGRAM = "kg", "Kg"
        LITER = "lt", "Lt"
        CC = "cc", "Cc"
        GRAM = "gr", "Gr"

    name = models.CharField(max_length=150, verbose_name="Nombre")
    category = models.ForeignKey(
        Category, on_delete=models.PROTECT, related_name="products", verbose_name="Categoría"
    )
    unit = models.CharField(max_length=10, choices=Unit.choices, default=Unit.UNIT, verbose_name="Unidad")
    min_stock = models.PositiveIntegerField(default=1, verbose_name="Stock mínimo")
    default_location = models.ForeignKey(
        Location,
        on_delete=models.SET_NULL,
        related_name="default_products",
        null=True,
        blank=True,
        verbose_name="Ubicación por defecto",
    )
    image = models.FileField(upload_to="products/", null=True, blank=True, verbose_name="Imagen")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Creado")

    class Meta:
        ordering = ["name"]
        unique_together = ("name", "category")

    def __str__(self) -> str:
        return self.name


class Batch(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="batches")
    lot_code = models.CharField(max_length=100, verbose_name="Código de lote")
    expiry_date = models.DateField(verbose_name="Fecha de vencimiento")
    quantity = models.PositiveIntegerField(default=0, verbose_name="Cantidad")
    location = models.ForeignKey(Location, on_delete=models.PROTECT, related_name="batches", verbose_name="Ubicación")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Creado")

    class Meta:
        ordering = ["expiry_date"]
        unique_together = ("product", "lot_code", "location")

    def __str__(self) -> str:
        return f"{self.product} - {self.lot_code}"

    @property
    def is_expired(self) -> bool:
        return self.expiry_date < timezone.localdate()

    @property
    def expires_soon(self) -> bool:
        today = timezone.localdate()
        return today <= self.expiry_date <= today + timedelta(days=7)

    @property
    def status_label(self) -> str:
        if self.is_expired:
            return "expired"
        if self.expires_soon:
            return "warning"
        return "ok"


class Movement(models.Model):
    class MovementType(models.TextChoices):
        IN = "IN", "Entrada"
        OUT = "OUT", "Salida"
        WASTE = "WASTE", "Merma"
        ADJUST = "ADJUST", "Ajuste"
        TRANSFER = "TRANSFER", "Traslado"

    batch = models.ForeignKey(Batch, on_delete=models.CASCADE, related_name="movements")
    movement_type = models.CharField(max_length=10, choices=MovementType.choices, verbose_name="Tipo de movimiento")
    quantity = models.PositiveIntegerField(verbose_name="Cantidad")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Creado")
    note = models.TextField(blank=True, verbose_name="Nota")
    destination_location = models.ForeignKey(
        "Location",
        on_delete=models.PROTECT,
        related_name="incoming_movements",
        null=True,
        blank=True,
        verbose_name="Ubicación destino",
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.get_movement_type_display()} - {self.batch} ({self.quantity})"

    def clean(self):
        if self.quantity is None or self.quantity < 1:
            raise ValidationError({"quantity": "La cantidad debe ser positiva."})
        if self.batch_id:
            if self.movement_type in {self.MovementType.OUT, self.MovementType.WASTE} and self.quantity > self.batch.quantity:
                raise ValidationError({"quantity": "No hay stock suficiente en el lote."})
            if self.movement_type == self.MovementType.TRANSFER:
                if not self.destination_location:
                    raise ValidationError({"destination_location": "Debes indicar la ubicación destino."})
                if self.destination_location_id == self.batch.location_id:
                    raise ValidationError({"destination_location": "La ubicación destino debe ser diferente a la actual."})
                if self.quantity > self.batch.quantity:
                    raise ValidationError({"quantity": "No hay stock suficiente para el traslado."})

    def save(self, *args, **kwargs):
        with transaction.atomic():
            # Refrescar lote y aplicar movimiento
            batch = Batch.objects.select_for_update().get(pk=self.batch_id)
            if self.movement_type == self.MovementType.IN:
                batch.quantity += self.quantity
            elif self.movement_type == self.MovementType.OUT:
                if self.quantity > batch.quantity:
                    raise ValidationError("No hay stock suficiente para la salida.")
                batch.quantity -= self.quantity
            elif self.movement_type == self.MovementType.WASTE:
                if self.quantity > batch.quantity:
                    raise ValidationError("No hay stock suficiente para la merma.")
                batch.quantity -= self.quantity
            elif self.movement_type == self.MovementType.ADJUST:
                batch.quantity = max(0, self.quantity)
            elif self.movement_type == self.MovementType.TRANSFER:
                # Restar al lote origen y sumar a un lote destino (mismo producto y lote) en la ubicación elegida.
                if self.quantity > batch.quantity:
                    raise ValidationError("No hay stock suficiente para el traslado.")
                dest_batch, _ = Batch.objects.select_for_update().get_or_create(
                    product=batch.product,
                    lot_code=batch.lot_code,
                    expiry_date=batch.expiry_date,
                    location=self.destination_location,
                    defaults={"quantity": 0},
                )
                batch.quantity -= self.quantity
                dest_batch.quantity += self.quantity
                dest_batch.save()
            batch.save()
            super().save(*args, **kwargs)
