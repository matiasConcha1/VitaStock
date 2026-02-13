from django import forms

from .models import Batch, Category, Location, Movement, Product


class SpanishClearableFileInput(forms.ClearableFileInput):
    clear_checkbox_label = "Eliminar"
    initial_text = "Actual"
    input_text = "Cambiar"


class BaseForm(forms.ModelForm):
    """Aplica clase CSS y placeholders en español."""

    required_css_class = "required"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            existing = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = f"{existing} form-control".strip()
        if "category" in self.fields:
            self.fields["category"].empty_label = "Categoría"
        if "default_location" in self.fields:
            self.fields["default_location"].empty_label = "Ubicación"


class CategoryForm(BaseForm):
    class Meta:
        model = Category
        fields = ["name"]
        labels = {"name": "Nombre"}
        error_messages = {"name": {"required": "Este campo es obligatorio."}}


class LocationForm(BaseForm):
    class Meta:
        model = Location
        fields = ["name", "location_type", "notes"]
        labels = {
            "name": "Nombre",
            "location_type": "Tipo",
            "notes": "Notas",
        }
        widgets = {
            "notes": forms.Textarea(attrs={"rows": 2}),
        }
        error_messages = {
            "name": {"required": "Este campo es obligatorio."},
            "location_type": {"required": "Este campo es obligatorio."},
        }


class ProductForm(BaseForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.pk:
            # Valores por defecto solo al crear
            first_cat = self.fields["category"].queryset.first()
            if first_cat and not self.initial.get("category"):
                self.initial["category"] = first_cat.pk
            first_loc = self.fields["default_location"].queryset.first()
            if first_loc and not self.initial.get("default_location"):
                self.initial["default_location"] = first_loc.pk
            if not self.initial.get("unit"):
                self.initial["unit"] = Product.Unit.UNIT
            if not self.initial.get("min_stock"):
                self.initial["min_stock"] = 1

    def clean(self):
        cleaned = super().clean()
        # En creación, completar faltantes
        if not self.instance.pk:
            if not cleaned.get("category"):
                first_cat = self.fields["category"].queryset.first()
                if first_cat:
                    cleaned["category"] = first_cat
                else:
                    self.add_error("category", "Debes crear una categoría.")
            if not cleaned.get("default_location"):
                first_loc = self.fields["default_location"].queryset.first()
                if first_loc:
                    cleaned["default_location"] = first_loc
            if not cleaned.get("unit"):
                cleaned["unit"] = Product.Unit.UNIT
            if not cleaned.get("min_stock"):
                cleaned["min_stock"] = 1
        return cleaned

    def clean_min_stock(self):
        value = self.cleaned_data.get("min_stock")
        if value is None or value < 1:
            raise forms.ValidationError("El stock mínimo debe ser al menos 1.")
        return value

    class Meta:
        model = Product
        fields = ["name", "category", "unit", "min_stock", "default_location", "image"]
        labels = {
            "name": "Nombre",
            "category": "Categoría",
            "unit": "Unidad",
            "min_stock": "Stock mínimo",
            "default_location": "Ubicación por defecto",
            "image": "Imagen",
        }
        widgets = {
            "image": SpanishClearableFileInput(attrs={"class": "form-control", "accept": "image/*"}),
        }
        error_messages = {
            "name": {"required": "Este campo es obligatorio."},
            "category": {"required": "Este campo es obligatorio."},
            "unit": {"required": "Este campo es obligatorio."},
            "min_stock": {"required": "Este campo es obligatorio."},
        }


class BatchForm(BaseForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if "product" in self.fields:
            self.fields["product"].empty_label = "Producto"
        if "location" in self.fields:
            self.fields["location"].empty_label = "Ubicación"
        # Asegurar que en edición se muestre la fecha existente en formato ISO (compat. con input date)
        if self.instance and self.instance.pk and self.instance.expiry_date:
            self.initial["expiry_date"] = self.instance.expiry_date.strftime("%Y-%m-%d")

    class Meta:
        model = Batch
        fields = ["product", "lot_code", "expiry_date", "quantity", "location"]
        labels = {
            "product": "Producto",
            "lot_code": "Código de lote",
            "expiry_date": "Fecha de vencimiento",
            "quantity": "Cantidad",
            "location": "Ubicación",
        }
        widgets = {
            "expiry_date": forms.DateInput(attrs={"type": "date", "class": "form-control"}, format="%Y-%m-%d"),
        }
        input_formats = {"expiry_date": ["%Y-%m-%d"]}


class MovementForm(BaseForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if "batch" in self.fields:
            self.fields["batch"].empty_label = "Seleccione lote"
            self.fields["batch"].label = "Lote"
            self.fields["batch"].label_from_instance = (
                lambda obj: f"{obj.lot_code} - {obj.product.name} (disp: {obj.quantity})"
            )
        if "movement_type" in self.fields:
            self.fields["movement_type"].label = "Tipo de movimiento"
            self.fields["movement_type"].choices = [("", "Seleccione tipo de movimiento")] + list(
                Movement.MovementType.choices
            )
        if "quantity" in self.fields:
            self.fields["quantity"].label = "Cantidad"
            self.fields["quantity"].widget.attrs.update({"min": 1})
        if "destination_location" in self.fields:
            self.fields["destination_location"].label = "Ubicación destino"
            self.fields["destination_location"].empty_label = "Seleccione ubicación"
        if "note" in self.fields:
            self.fields["note"].label = "Nota"

    class Meta:
        model = Movement
        fields = ["batch", "movement_type", "quantity", "destination_location", "note"]
        widgets = {
            "note": forms.Textarea(attrs={"rows": 3}),
        }
