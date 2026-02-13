from datetime import timedelta

from django.db import models
from django.db.models import Count, F, Max, Sum, Value
from django.db.models.functions import Coalesce
from django.utils import timezone

from .models import Batch, Category, Movement, Product


def get_expired_batches(queryset):
    today = timezone.localdate()
    return queryset.filter(expiry_date__lt=today)


def get_batches_expiring_soon(queryset, days=7):
    today = timezone.localdate()
    return queryset.filter(expiry_date__range=(today, today + timedelta(days=days)))


def get_low_stock_products(queryset):
    return (
        queryset.annotate(stock_total=Coalesce(Sum("batches__quantity"), Value(0)))
        .filter(stock_total__lt=F("min_stock"))
        .distinct()
    )


# ----- Dashboard helpers -----

def get_kpis():
    today = timezone.localdate()
    batches = Batch.objects.select_related("product", "location")
    expired = batches.filter(quantity__gt=0, expiry_date__lt=today).count()
    soon7 = batches.filter(quantity__gt=0, expiry_date__gte=today, expiry_date__lte=today + timedelta(days=7)).count()
    soon30 = batches.filter(quantity__gt=0, expiry_date__gte=today, expiry_date__lte=today + timedelta(days=30)).count()
    low_stock = (
        Product.objects.annotate(stock_total=Coalesce(Sum("batches__quantity"), Value(0)))
        .filter(stock_total__lt=F("min_stock"))
        .count()
    )
    return {
        "lotes_vencidos": expired,
        "vencen_7": soon7,
        "vencen_30": soon30,
        "stock_bajo": low_stock,
    }


def get_expiry_timeseries(days: int = 7):
    """Devuelve labels (fechas) y data (sumatoria de cantidades) por día."""
    today = timezone.localdate()
    buckets = []
    for i in range(days + 1):
        day = today + timedelta(days=i)
        qty = (
            Batch.objects.filter(expiry_date=day, quantity__gt=0)
            .aggregate(total=Coalesce(Sum("quantity"), Value(0)))
            .get("total")
        )
        buckets.append((day, qty))
    labels = [d.strftime("%Y-%m-%d") for d, _ in buckets]
    data = [q for _, q in buckets]
    return {"labels": labels, "data": data}


def get_category_distribution():
    qs = (
        Category.objects.annotate(total=Count("products", distinct=True))
        .order_by("-total", "name")[:6]
    )
    labels = [c.name for c in qs]
    data = [c.total for c in qs]
    return {"labels": labels, "data": data}


def get_priority_actions():
    today = timezone.localdate()
    actions = []

    expired = (
        Batch.objects.select_related("product", "location")
        .filter(quantity__gt=0, expiry_date__lt=today)
        .order_by("expiry_date")[:10]
    )
    for b in expired:
        actions.append(
            {
                "tipo": "vencido",
                "producto": b.product.name,
                "ubicacion": b.location.name if b.location else "-",
                "fecha": b.expiry_date,
                "cantidad": b.quantity,
                "batch_id": b.id,
            }
        )

    soon = (
        Batch.objects.select_related("product", "location")
        .filter(quantity__gt=0, expiry_date__gte=today, expiry_date__lte=today + timedelta(days=7))
        .order_by("expiry_date")[:10]
    )
    for b in soon:
        actions.append(
            {
                "tipo": "vence_pronto",
                "producto": b.product.name,
                "ubicacion": b.location.name if b.location else "-",
                "fecha": b.expiry_date,
                "cantidad": b.quantity,
                "batch_id": b.id,
            }
        )

    low_stock_products = (
        Product.objects.annotate(stock_total=Coalesce(Sum("batches__quantity"), Value(0)))
        .filter(stock_total__lt=F("min_stock"))
        .select_related("default_location")[:10]
    )
    for p in low_stock_products:
        actions.append(
            {
                "tipo": "stock_bajo",
                "producto": p.name,
                "ubicacion": p.default_location.name if p.default_location else "-",
                "fecha": None,
                "cantidad": p.stock_total if hasattr(p, "stock_total") else 0,
                "product_id": p.id,
            }
        )

    # Limitar a 10 mÃ¡s relevantes
    return actions[:10]


def get_recent_movements(limit=8):
    return (
        Movement.objects.select_related("batch", "batch__product", "batch__location")
        .order_by("-created_at")[:limit]
    )


def get_dashboard_data():
    """Agrega todas las mÃ©tricas necesarias para el panel de control."""
    kpis = get_kpis()
    expiring_list = (
        Batch.objects.select_related("product", "location")
        .filter(quantity__gt=0, expiry_date__lte=timezone.localdate() + timedelta(days=7))
        .order_by("expiry_date")[:8]
    )
    last_movements = get_recent_movements()
    category_summary = Category.objects.annotate(total=Count("products", distinct=True)).order_by("-total", "name")[:5]
    max_cat_total = category_summary.aggregate(mx=Coalesce(Max("total"), Value(0)))["mx"] or 0

    return {
        "expired_count": kpis["lotes_vencidos"],
        "soon7_count": kpis["vencen_7"],
        "soon30_count": kpis["vencen_30"],
        "low_stock_count": kpis["stock_bajo"],
        "expiring_list": expiring_list,
        "last_movements": last_movements,
        "category_summary": category_summary,
        "max_cat_total": max_cat_total,
    }


def get_expiry_calendar(days: int = 365):
    """
    Devuelve un mapa fecha->cantidad para los próximos `days` días,
    sumando cantidades de lotes que vencen cada día.
    """
    today = timezone.localdate()
    horizon = today + timedelta(days=days)
    qs = (
        Batch.objects.filter(quantity__gt=0, expiry_date__range=(today, horizon))
        .values("expiry_date")
        .annotate(total=Coalesce(Sum("quantity"), Value(0)))
        .order_by("expiry_date")
    )
    return {item["expiry_date"].strftime("%Y-%m-%d"): item["total"] for item in qs}

