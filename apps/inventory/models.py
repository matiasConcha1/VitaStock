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
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class Product(models.Model):
    class Unit(models.TextChoices):
        UNIT = "unit", "Unit"
        KILOGRAM = "kg", "Kg"
        LITER = "lt", "Liter"

    name = models.CharField(max_length=150)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="products")
    unit = models.CharField(max_length=10, choices=Unit.choices, default=Unit.UNIT)
    min_stock = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]
        unique_together = ("name", "category")

    def __str__(self) -> str:
        return self.name


class Batch(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="batches")
    lot_code = models.CharField(max_length=100)
    expiry_date = models.DateField()
    quantity = models.PositiveIntegerField(default=0)
    location = models.ForeignKey(Location, on_delete=models.PROTECT, related_name="batches")
    created_at = models.DateTimeField(auto_now_add=True)

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
        IN = "IN", "In"
        OUT = "OUT", "Out"
        WASTE = "WASTE", "Waste"
        ADJUST = "ADJUST", "Adjust"

    batch = models.ForeignKey(Batch, on_delete=models.CASCADE, related_name="movements")
    movement_type = models.CharField(max_length=10, choices=MovementType.choices)
    quantity = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    note = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.movement_type} - {self.batch} ({self.quantity})"

    def clean(self):
        if self.quantity <= 0:
            raise ValidationError({"quantity": "Quantity must be greater than zero."})
        if self.movement_type in {self.MovementType.OUT, self.MovementType.WASTE} and self.batch_id:
            if self.batch.quantity < self.quantity:
                raise ValidationError({"quantity": "Insufficient batch quantity for this movement."})

    def apply_to_batch(self):
        """Update batch stock according to the movement semantics."""
        batch = self.batch
        if self.movement_type == self.MovementType.IN:
            batch.quantity += self.quantity
        elif self.movement_type in {self.MovementType.OUT, self.MovementType.WASTE}:
            batch.quantity = max(0, batch.quantity - self.quantity)
        elif self.movement_type == self.MovementType.ADJUST:
            # Treat adjust as delta (positive corrections only to keep it simple and safe).
            batch.quantity += self.quantity
        batch.save(update_fields=["quantity"])

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        self.full_clean()
        with transaction.atomic():
            response = super().save(*args, **kwargs)
            if is_new:
                self.apply_to_batch()
        return response
