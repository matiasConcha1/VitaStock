from django.urls import path

from . import views

app_name = "inventory"

urlpatterns = [
    # Accounts (admin/staff)
    path("accounts/", views.AccountListView.as_view(), name="account_list"),
    path("accounts/<int:pk>/toggle/", views.AccountToggleView.as_view(), name="account_toggle"),
    # Categories
    path("categories/", views.CategoryListView.as_view(), name="category_list"),
    path("categories/create/", views.CategoryCreateView.as_view(), name="category_create"),
    path("categories/<int:pk>/edit/", views.CategoryUpdateView.as_view(), name="category_update"),
    path("categories/<int:pk>/delete/", views.CategoryDeleteView.as_view(), name="category_delete"),
    # Locations
    path("locations/", views.LocationListView.as_view(), name="location_list"),
    path("locations/create/", views.LocationCreateView.as_view(), name="location_create"),
    path("locations/<int:pk>/edit/", views.LocationUpdateView.as_view(), name="location_update"),
    path("locations/<int:pk>/delete/", views.LocationDeleteView.as_view(), name="location_delete"),
    # Products
    path("products/", views.ProductListView.as_view(), name="product_list"),
    path("products/create/", views.ProductCreateView.as_view(), name="product_create"),
    path("products/<int:pk>/edit/", views.ProductUpdateView.as_view(), name="product_update"),
    path("products/<int:pk>/delete/", views.ProductDeleteView.as_view(), name="product_delete"),
    path("products/<int:pk>/image/", views.ProductImageView.as_view(), name="product_image"),
    # Dashboard
    path("dashboard/", views.DashboardView.as_view(), name="dashboard"),
    # Batches
    path("batches/", views.BatchListView.as_view(), name="batch_list"),
    path("batches/create/", views.BatchCreateView.as_view(), name="batch_create"),
    path("batches/<int:pk>/edit/", views.BatchUpdateView.as_view(), name="batch_update"),
    path("batches/<int:pk>/delete/", views.BatchDeleteView.as_view(), name="batch_delete"),
    # Movements
    path("movements/", views.MovementListView.as_view(), name="movement_list"),
    path("movements/create/", views.MovementCreateView.as_view(), name="movement_create"),
    path("movements/<int:pk>/edit/", views.MovementUpdateView.as_view(), name="movement_update"),
    path("movements/<int:pk>/delete/", views.MovementDeleteView.as_view(), name="movement_delete"),
]
