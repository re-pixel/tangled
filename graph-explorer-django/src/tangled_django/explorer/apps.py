from django.apps import AppConfig


class ExplorerConfig(AppConfig):
    name = "tangled_django.explorer"
    verbose_name = "Tangled Graph Explorer"
    default_auto_field = "django.db.models.BigAutoField"

    def ready(self):
        from tangled_platform import Platform
        import tangled_django.explorer as mod
        mod.platform = Platform()
