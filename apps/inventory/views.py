from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Sum
from django.db.models.functions import Coalesce
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from .filters import filter_by_query
from .forms import (
    BatchForm,
    CategoryForm,
    LocationForm,
    MovementForm,
    ProductForm,
)
from .models import Batch, Category, Location, Movement, Product


class InventoryBaseMixin:
    segment = ""
    page_title = ""

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["segment"] = self.segment
        context["page_title"] = self.page_title
        context["search_query"] = self.request.GET.get("q", "")
        return context


class CategoryListView(InventoryBaseMixin, ListView):
    model = Category
    template_name = "inventory/category/list.html"
    context_object_name = "categories"
    segment = "inventory_categories"
    page_title = "Categorías"


class CategoryCreateView(InventoryBaseMixin, SuccessMessageMixin, CreateView):
    model = Category
    template_name = "inventory/category/form.html"
    form_class = CategoryForm
    success_url = reverse_lazy("inventory:category_list")
    success_message = "Category created successfully."
    segment = "inventory_categories"
    page_title = "Crear categoría"


class CategoryUpdateView(InventoryBaseMixin, SuccessMessageMixin, UpdateView):
    model = Category
    template_name = "inventory/category/form.html"
    form_class = CategoryForm
    success_url = reverse_lazy("inventory:category_list")
    success_message = "Category updated successfully."
    segment = "inventory_categories"
    page_title = "Editar categoría"


class CategoryDeleteView(InventoryBaseMixin, DeleteView):
    model = Category
    template_name = "inventory/category/confirm_delete.html"
    success_url = reverse_lazy("inventory:category_list")
    segment = "inventory_categories"
    page_title = "Eliminar categoría"

    def delete(self, request, *args, **kwargs):
        messages.success(request, "Category deleted successfully.")
        return super().delete(request, *args, **kwargs)


class LocationListView(InventoryBaseMixin, ListView):
    model = Location
    template_name = "inventory/location/list.html"
    context_object_name = "locations"
    segment = "inventory_locations"
    page_title = "Ubicaciones"


class LocationCreateView(InventoryBaseMixin, SuccessMessageMixin, CreateView):
    model = Location
    template_name = "inventory/location/form.html"
    form_class = LocationForm
    success_url = reverse_lazy("inventory:location_list")
    success_message = "Location created successfully."
    segment = "inventory_locations"
    page_title = "Crear ubicación"


class LocationUpdateView(InventoryBaseMixin, SuccessMessageMixin, UpdateView):
    model = Location
    template_name = "inventory/location/form.html"
    form_class = LocationForm
    success_url = reverse_lazy("inventory:location_list")
    success_message = "Location updated successfully."
    segment = "inventory_locations"
    page_title = "Editar ubicación"


class LocationDeleteView(InventoryBaseMixin, DeleteView):
    model = Location
    template_name = "inventory/location/confirm_delete.html"
    success_url = reverse_lazy("inventory:location_list")
    segment = "inventory_locations"
    page_title = "Eliminar ubicación"

    def delete(self, request, *args, **kwargs):
        messages.success(request, "Location deleted successfully.")
        return super().delete(request, *args, **kwargs)


class ProductListView(InventoryBaseMixin, ListView):
    model = Product
    template_name = "inventory/product/list.html"
    context_object_name = "products"
    segment = "inventory_products"
    page_title = "Productos"

    def get_queryset(self):
        queryset = (
            Product.objects.select_related("category", "default_location")
            .annotate(total_stock=Coalesce(Sum("batches__quantity"), 0))
        )
        queryset = filter_by_query(
            queryset, self.request.GET.get("q"), ["name", "category__name", "default_location__name"]
        )
        category_id = self.request.GET.get("category")
        location_id = self.request.GET.get("location")
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        if location_id:
            queryset = queryset.filter(default_location_id=location_id)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["location_form"] = kwargs.get("location_form") or LocationForm()
        context["categories"] = Category.objects.all()
        context["locations"] = Location.objects.all()
        context["total_products"] = self.object_list.count() if hasattr(self, "object_list") else Product.objects.count()
        return context

    def post(self, request, *args, **kwargs):
        """Quick-create location from product list page."""
        form = LocationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Location created.")
        else:
            messages.error(request, "Could not create location. Please fix the errors.")
            self.object_list = self.get_queryset()
            context = self.get_context_data(location_form=form)
            return self.render_to_response(context)
        return redirect("inventory:product_list")


class ProductCreateView(InventoryBaseMixin, SuccessMessageMixin, CreateView):
    model = Product
    template_name = "inventory/product/form.html"
    form_class = ProductForm
    success_url = reverse_lazy("inventory:product_list")
    success_message = "Producto creado con éxito."
    segment = "inventory_products"
    page_title = "Crear producto"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["files"] = self.request.FILES
        return kwargs


class ProductUpdateView(InventoryBaseMixin, SuccessMessageMixin, UpdateView):
    model = Product
    template_name = "inventory/product/form.html"
    form_class = ProductForm
    success_url = reverse_lazy("inventory:product_list")
    success_message = "Producto actualizado con éxito."
    segment = "inventory_products"
    page_title = "Editar producto"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["files"] = self.request.FILES
        return kwargs


class ProductDeleteView(InventoryBaseMixin, DeleteView):
    model = Product
    template_name = "inventory/product/confirm_delete.html"
    success_url = reverse_lazy("inventory:product_list")
    segment = "inventory_products"
    page_title = "Delete Product"

    def delete(self, request, *args, **kwargs):
        messages.success(request, "Product deleted successfully.")
        return super().delete(request, *args, **kwargs)


class BatchListView(InventoryBaseMixin, ListView):
    model = Batch
    template_name = "inventory/batch/list.html"
    context_object_name = "batches"
    segment = "inventory_batches"
    page_title = "Lotes"

    def get_queryset(self):
        queryset = Batch.objects.select_related("product", "location", "product__category")
        return filter_by_query(
            queryset,
            self.request.GET.get("q"),
            ["product__name", "lot_code", "location__name"],
        )


class BatchCreateView(InventoryBaseMixin, SuccessMessageMixin, CreateView):
    model = Batch
    template_name = "inventory/batch/form.html"
    form_class = BatchForm
    success_url = reverse_lazy("inventory:batch_list")
    success_message = "Batch created successfully."
    segment = "inventory_batches"
    page_title = "Crear lote"


class BatchUpdateView(InventoryBaseMixin, SuccessMessageMixin, UpdateView):
    model = Batch
    template_name = "inventory/batch/form.html"
    form_class = BatchForm
    success_url = reverse_lazy("inventory:batch_list")
    success_message = "Batch updated successfully."
    segment = "inventory_batches"
    page_title = "Editar lote"


class BatchDeleteView(InventoryBaseMixin, DeleteView):
    model = Batch
    template_name = "inventory/batch/confirm_delete.html"
    success_url = reverse_lazy("inventory:batch_list")
    segment = "inventory_batches"
    page_title = "Eliminar lote"

    def delete(self, request, *args, **kwargs):
        messages.success(request, "Batch deleted successfully.")
        return super().delete(request, *args, **kwargs)


class MovementListView(InventoryBaseMixin, ListView):
    model = Movement
    template_name = "inventory/movement/list.html"
    context_object_name = "movements"
    segment = "inventory_movements"
    page_title = "Movimientos"

    def get_queryset(self):
        return (
            Movement.objects.select_related("batch", "batch__product", "batch__location")
            .all()
        )


class MovementCreateView(InventoryBaseMixin, SuccessMessageMixin, CreateView):
    model = Movement
    template_name = "inventory/movement/form.html"
    form_class = MovementForm
    success_url = reverse_lazy("inventory:movement_list")
    success_message = "Movement registered successfully."
    segment = "inventory_movements"
    page_title = "Registrar movimiento"

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, self.success_message)
        return response
