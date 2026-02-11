from django.apps import AppConfig


class InventoryConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.inventory"
    verbose_name = "Inventory"

    def ready(self):
        # Enable AVIF support for Pillow (if plugin is installed)
        try:
            import pillow_avif_plugin  # noqa: F401
        except ImportError:
            pass
