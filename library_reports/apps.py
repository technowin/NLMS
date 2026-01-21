from django.apps import AppConfig


class LibraryReportsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'library_reports'

    def ready(self):
        import library_reports.signals