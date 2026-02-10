from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
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
    page_title = "Categories"


class CategoryCreateView(InventoryBaseMixin, SuccessMessageMixin, CreateView):
    model = Category
    template_name = "inventory/category/form.html"
    form_class = CategoryForm
    success_url = reverse_lazy("inventory:category_list")
    success_message = "Category created successfully."
    segment = "inventory_categories"
    page_title = "Create Category"


class CategoryUpdateView(InventoryBaseMixin, SuccessMessageMixin, UpdateView):
    model = Category
    template_name = "inventory/category/form.html"
    form_class = CategoryForm
    success_url = reverse_lazy("inventory:category_list")
    success_message = "Category updated successfully."
    segment = "inventory_categories"
    page_title = "Edit Category"


class CategoryDeleteView(InventoryBaseMixin, DeleteView):
    model = Category
    template_name = "inventory/category/confirm_delete.html"
    success_url = reverse_lazy("inventory:category_list")
    segment = "inventory_categories"
    page_title = "Delete Category"

    def delete(self, request, *args, **kwargs):
        messages.success(request, "Category deleted successfully.")
        return super().delete(request, *args, **kwargs)


class LocationListView(InventoryBaseMixin, ListView):
    model = Location
    template_name = "inventory/location/list.html"
    context_object_name = "locations"
    segment = "inventory_locations"
    page_title = "Locations"


class LocationCreateView(InventoryBaseMixin, SuccessMessageMixin, CreateView):
    model = Location
    template_name = "inventory/location/form.html"
    form_class = LocationForm
    success_url = reverse_lazy("inventory:location_list")
    success_message = "Location created successfully."
    segment = "inventory_locations"
    page_title = "Create Location"


class LocationUpdateView(InventoryBaseMixin, SuccessMessageMixin, UpdateView):
    model = Location
    template_name = "inventory/location/form.html"
    form_class = LocationForm
    success_url = reverse_lazy("inventory:location_list")
    success_message = "Location updated successfully."
    segment = "inventory_locations"
    page_title = "Edit Location"


class LocationDeleteView(InventoryBaseMixin, DeleteView):
    model = Location
    template_name = "inventory/location/confirm_delete.html"
    success_url = reverse_lazy("inventory:location_list")
    segment = "inventory_locations"
    page_title = "Delete Location"

    def delete(self, request, *args, **kwargs):
        messages.success(request, "Location deleted successfully.")
        return super().delete(request, *args, **kwargs)


class ProductListView(InventoryBaseMixin, ListView):
    model = Product
    template_name = "inventory/product/list.html"
    context_object_name = "products"
    segment = "inventory_products"
    page_title = "Products"

    def get_queryset(self):
        queryset = Product.objects.select_related("category")
        return filter_by_query(queryset, self.request.GET.get("q"), ["name", "category__name"])


class ProductCreateView(InventoryBaseMixin, SuccessMessageMixin, CreateView):
    model = Product
    template_name = "inventory/product/form.html"
    form_class = ProductForm
    success_url = reverse_lazy("inventory:product_list")
    success_message = "Product created successfully."
    segment = "inventory_products"
    page_title = "Create Product"


class ProductUpdateView(InventoryBaseMixin, SuccessMessageMixin, UpdateView):
    model = Product
    template_name = "inventory/product/form.html"
    form_class = ProductForm
    success_url = reverse_lazy("inventory:product_list")
    success_message = "Product updated successfully."
    segment = "inventory_products"
    page_title = "Edit Product"


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
    page_title = "Batches"

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
    page_title = "Create Batch"


class BatchUpdateView(InventoryBaseMixin, SuccessMessageMixin, UpdateView):
    model = Batch
    template_name = "inventory/batch/form.html"
    form_class = BatchForm
    success_url = reverse_lazy("inventory:batch_list")
    success_message = "Batch updated successfully."
    segment = "inventory_batches"
    page_title = "Edit Batch"


class BatchDeleteView(InventoryBaseMixin, DeleteView):
    model = Batch
    template_name = "inventory/batch/confirm_delete.html"
    success_url = reverse_lazy("inventory:batch_list")
    segment = "inventory_batches"
    page_title = "Delete Batch"

    def delete(self, request, *args, **kwargs):
        messages.success(request, "Batch deleted successfully.")
        return super().delete(request, *args, **kwargs)


class MovementListView(InventoryBaseMixin, ListView):
    model = Movement
    template_name = "inventory/movement/list.html"
    context_object_name = "movements"
    segment = "inventory_movements"
    page_title = "Movements"

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
    page_title = "Register Movement"

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, self.success_message)
        return response
