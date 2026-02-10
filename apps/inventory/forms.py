from django import forms

from .models import Batch, Category, Location, Movement, Product


class BaseForm(forms.ModelForm):
    """Small helper to apply a consistent css class when bootstrap is available."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            existing = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = f"{existing} form-control".strip()


class CategoryForm(BaseForm):
    class Meta:
        model = Category
        fields = ["name"]


class LocationForm(BaseForm):
    class Meta:
        model = Location
        fields = ["name", "location_type", "notes"]


class ProductForm(BaseForm):
    class Meta:
        model = Product
        fields = ["name", "category", "unit", "min_stock", "default_location", "image"]
        widgets = {
            "image": forms.ClearableFileInput(attrs={"class": "form-control"}),
        }


class BatchForm(BaseForm):
    class Meta:
        model = Batch
        fields = ["product", "lot_code", "expiry_date", "quantity", "location"]
        widgets = {
            "expiry_date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
        }


class MovementForm(BaseForm):
    class Meta:
        model = Movement
        fields = ["batch", "movement_type", "quantity", "note"]
        widgets = {
            "note": forms.Textarea(attrs={"rows": 3}),
        }
