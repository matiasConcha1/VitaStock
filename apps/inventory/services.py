from datetime import timedelta

from django.db import models
from django.utils import timezone


def get_expired_batches(queryset):
    today = timezone.localdate()
    return queryset.filter(expiry_date__lt=today)


def get_batches_expiring_soon(queryset, days=7):
    today = timezone.localdate()
    return queryset.filter(expiry_date__range=(today, today + timedelta(days=days)))


def get_low_stock_products(queryset):
    return queryset.filter(batches__quantity__lt=models.F("min_stock")).distinct()
