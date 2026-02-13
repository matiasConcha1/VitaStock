from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.messages.views import SuccessMessageMixin
import json

from django.db.models import Sum
from django.db.models.functions import Coalesce
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView, TemplateView, View
from django.core.serializers.json import DjangoJSONEncoder
from django.http import FileResponse, Http404
from django.contrib.auth import get_user_model
import mimetypes

User = get_user_model()
import os

from .filters import filter_by_query
from .forms import BatchForm, CategoryForm, LocationForm, MovementForm, ProductForm
from .models import Batch, Category, Location, Movement, Product
from .services import (
    get_category_distribution,
    get_dashboard_data,
    get_expiry_timeseries,
    get_expiry_calendar,
    get_kpis,
    get_priority_actions,
    get_recent_movements,
)


class InventoryBaseMixin(LoginRequiredMixin):
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
    success_message = "Categoría creada con éxito."
    segment = "inventory_categories"
    page_title = "Crear categoría"


class CategoryUpdateView(InventoryBaseMixin, SuccessMessageMixin, UpdateView):
    model = Category
    template_name = "inventory/category/form.html"
    form_class = CategoryForm
    success_url = reverse_lazy("inventory:category_list")
    success_message = "Categoría actualizada con éxito."
    segment = "inventory_categories"
    page_title = "Editar categoría"


class CategoryDeleteView(InventoryBaseMixin, DeleteView):
    model = Category
    template_name = "inventory/category/confirm_delete.html"
    success_url = reverse_lazy("inventory:category_list")
    segment = "inventory_categories"
    page_title = "Eliminar categoría"

    def delete(self, request, *args, **kwargs):
        messages.success(request, "Categoría eliminada con éxito.")
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
    success_message = "Ubicación creada con éxito."
    segment = "inventory_locations"
    page_title = "Crear ubicación"


class LocationUpdateView(InventoryBaseMixin, SuccessMessageMixin, UpdateView):
    model = Location
    template_name = "inventory/location/form.html"
    form_class = LocationForm
    success_url = reverse_lazy("inventory:location_list")
    success_message = "Ubicación actualizada con éxito."
    segment = "inventory_locations"
    page_title = "Editar ubicación"


class LocationDeleteView(InventoryBaseMixin, DeleteView):
    model = Location
    template_name = "inventory/location/confirm_delete.html"
    success_url = reverse_lazy("inventory:location_list")
    segment = "inventory_locations"
    page_title = "Eliminar ubicación"

    def delete(self, request, *args, **kwargs):
        messages.success(request, "Ubicación eliminada con éxito.")
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
        """Creación rápida de ubicación desde la lista de productos."""
        form = LocationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Ubicación creada.")
        else:
            messages.error(request, "No se pudo crear la ubicación. Corrige los errores.")
            self.object_list = self.get_queryset()
            context = self.get_context_data(location_form=form)
            return self.render_to_response(context)
        return redirect("inventory:product_list")


class ProductImageView(LoginRequiredMixin, View):
    """Sirve la imagen del producto aun si el servidor de media falla."""

    def get(self, request, pk):
        product = get_object_or_404(Product, pk=pk)
        if not product.image:
            raise Http404("Imagen no disponible")
        path = product.image.path
        if not os.path.exists(path):
            raise Http404("Archivo no encontrado")
        ctype, _ = mimetypes.guess_type(path)
        return FileResponse(open(path, "rb"), content_type=ctype or "application/octet-stream")


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
        if self.request.method in ("POST", "PUT", "PATCH") and self.request.FILES:
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
        if self.request.method in ("POST", "PUT", "PATCH") and self.request.FILES:
            kwargs["files"] = self.request.FILES
        return kwargs


class ProductDeleteView(InventoryBaseMixin, DeleteView):
    model = Product
    template_name = "inventory/product/confirm_delete.html"
    success_url = reverse_lazy("inventory:product_list")
    segment = "inventory_products"
    page_title = "Eliminar producto"

    def delete(self, request, *args, **kwargs):
        messages.success(request, "Producto eliminado con éxito.")
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
    success_message = "Lote creado con éxito."
    segment = "inventory_batches"
    page_title = "Crear lote"


class BatchUpdateView(InventoryBaseMixin, SuccessMessageMixin, UpdateView):
    model = Batch
    template_name = "inventory/batch/form.html"
    form_class = BatchForm
    success_url = reverse_lazy("inventory:batch_list")
    success_message = "Lote actualizado con éxito."
    segment = "inventory_batches"
    page_title = "Editar lote"


class BatchDeleteView(InventoryBaseMixin, DeleteView):
    model = Batch
    template_name = "inventory/batch/confirm_delete.html"
    success_url = reverse_lazy("inventory:batch_list")
    segment = "inventory_batches"
    page_title = "Eliminar lote"

    def delete(self, request, *args, **kwargs):
        messages.success(request, "Lote eliminado con éxito.")
        return super().delete(request, *args, **kwargs)


class MovementListView(InventoryBaseMixin, ListView):
    model = Movement
    template_name = "inventory/movement/list.html"
    context_object_name = "movements"
    segment = "inventory_movements"
    page_title = "Movimientos"

    def get_queryset(self):
        return Movement.objects.select_related("batch", "batch__product", "batch__location")


class MovementCreateView(InventoryBaseMixin, SuccessMessageMixin, CreateView):
    model = Movement
    template_name = "inventory/movement/form.html"
    form_class = MovementForm
    success_url = reverse_lazy("inventory:movement_list")
    success_message = "Movimiento registrado con éxito."
    segment = "inventory_movements"
    page_title = "Registrar movimiento"

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, self.success_message)
        return response


class MovementUpdateView(InventoryBaseMixin, SuccessMessageMixin, UpdateView):
    model = Movement
    template_name = "inventory/movement/form.html"
    form_class = MovementForm
    success_url = reverse_lazy("inventory:movement_list")
    success_message = "Movimiento actualizado con éxito."
    segment = "inventory_movements"
    page_title = "Editar movimiento"


class MovementDeleteView(InventoryBaseMixin, DeleteView):
    model = Movement
    template_name = "inventory/movement/confirm_delete.html"
    success_url = reverse_lazy("inventory:movement_list")
    segment = "inventory_movements"
    page_title = "Eliminar movimiento"

    def delete(self, request, *args, **kwargs):
        messages.success(request, "Movimiento eliminado con éxito.")
        return super().delete(request, *args, **kwargs)


class DashboardView(InventoryBaseMixin, TemplateView):
    template_name = "dashboard/calendar_new.html"
    segment = "dashboard"
    page_title = "Panel de control"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # KPIs
        kpis = get_kpis()
        context.update(
            {
                "expired_count": kpis["lotes_vencidos"],
                "soon7_count": kpis["vencen_7"],
                "soon30_count": kpis["vencen_30"],
                "low_stock_count": kpis["stock_bajo"],
                "kpi_items": [
                    {"title": "Lotes vencidos", "value": kpis["lotes_vencidos"], "note": "Últimos 30 días"},
                    {"title": "Vence en 7 días", "value": kpis["vencen_7"], "note": "Actualizado hoy"},
                    {"title": "Vence en 30 días", "value": kpis["vencen_30"], "note": "Actualizado hoy"},
                    {"title": "Stock bajo", "value": kpis["stock_bajo"], "note": "Actualizado hoy"},
                ],
            }
        )

        # series para 7/30/90
        context["series_7"] = get_expiry_timeseries(7)
        context["series_30"] = get_expiry_timeseries(30)
        context["series_90"] = get_expiry_timeseries(90)
        context["calendar_days"] = list(zip(context["series_30"]["labels"], context["series_30"]["data"]))
        calendar_map = get_expiry_calendar(365)
        context["calendar_data"] = calendar_map
        # serialización para Chart.js
        context["series_json"] = json.dumps(
            {
                "7": context["series_7"],
                "30": context["series_30"],
                "90": context["series_90"],
            },
            cls=DjangoJSONEncoder,
        )
        context["calendar_data_json"] = json.dumps(calendar_map, cls=DjangoJSONEncoder)

        # distribución por categoría
        cat_dist = get_category_distribution()
        context["cat_dist_labels"] = json.dumps(cat_dist["labels"], cls=DjangoJSONEncoder)
        context["cat_dist_data"] = json.dumps(cat_dist["data"], cls=DjangoJSONEncoder)

        # acciones prioritarias
        context["priority_actions"] = get_priority_actions()

        # movimientos recientes
        context["last_movements"] = get_recent_movements()

        # apoyo para barras de categoría
        context["category_summary"] = get_dashboard_data().get("category_summary")
        context["max_cat_total"] = get_dashboard_data().get("max_cat_total")
        return context


class StaffRequiredMixin(UserPassesTestMixin):
    """Solo staff o superusuarios."""

    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser


class AccountListView(StaffRequiredMixin, InventoryBaseMixin, ListView):
    model = User
    template_name = "inventory/accounts/list.html"
    context_object_name = "users"
    segment = "admin_accounts"
    page_title = "Cuentas"

    def get_queryset(self):
        return User.objects.order_by("-is_active", "username")


class AccountToggleView(StaffRequiredMixin, InventoryBaseMixin, View):
    def post(self, request, pk):
        if request.user.pk == pk:
            messages.warning(request, "No puedes desactivar tu propia cuenta.")
            return redirect("inventory:account_list")
        user = get_object_or_404(User, pk=pk)
        user.is_active = not user.is_active
        user.save()
        estado = "activada" if user.is_active else "desactivada"
        messages.success(request, f"Cuenta {user.username} {estado}.")
        return redirect("inventory:account_list")

