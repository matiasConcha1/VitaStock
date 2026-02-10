from django.contrib import admin

from .models import Batch, Category, Location, Movement, Product


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ("name", "location_type")
    list_filter = ("location_type",)
    search_fields = ("name", "notes")


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "unit", "min_stock", "default_location", "created_at")
    list_filter = ("category", "unit", "default_location")
    search_fields = ("name",)


@admin.register(Batch)
class BatchAdmin(admin.ModelAdmin):
    list_display = ("product", "lot_code", "expiry_date", "quantity", "location", "created_at")
    list_filter = ("product", "location", "expiry_date")
    search_fields = ("lot_code", "product__name")


@admin.register(Movement)
class MovementAdmin(admin.ModelAdmin):
    list_display = ("batch", "movement_type", "quantity", "created_at")
    list_filter = ("movement_type", "created_at")
    search_fields = ("batch__product__name", "batch__lot_code", "note")
