"""config URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static
from django.urls import re_path
from django.views.static import serve
from django.contrib.auth import views as auth_views

from apps.pages.views import VitaStockLoginView, VitaStockRegisterView
from apps.inventory.views import DashboardView

urlpatterns = [
    path("iniciar-sesion/", VitaStockLoginView.as_view(), name="login"),
    path("registrarse/", VitaStockRegisterView.as_view(), name="register"),
    path("cerrar-sesion/", auth_views.LogoutView.as_view(), name="logout"),
    path("panel/", DashboardView.as_view(), name="panel"),
    path('', include('apps.pages.urls')),
    path('', include('apps.dyn_dt.urls')),
    path('', include('apps.dyn_api.urls')),
    path('charts/', include('apps.charts.urls')),
    path("inventory/", include(("apps.inventory.urls", "inventory"), namespace="inventory")),
    path("admin/", admin.site.urls),
    path("", include('admin_soft.urls'))
]

# Servir media (incluso si DEBUG=False en local)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns.append(
    re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT})
)
