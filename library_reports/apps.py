# reports/apps.py
from django.apps import AppConfig

class ReportsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'library_reports'
    verbose_name = 'Reports Module'
    
    def ready(self):
        # Import signals if any
        pass