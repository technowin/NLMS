# reports/signals.py
from datetime import timezone
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.db import transaction
from .models import ReportSession, ReportExport
import os

@receiver(post_save, sender=ReportExport)
def cleanup_old_exports(sender, instance, created, **kwargs):
    """Clean up old export files"""
    if created:
        # Delete exports older than 30 days
        old_exports = ReportExport.objects.filter(
            exported_at__lt=timezone.now() - timezone.timedelta(days=30)
        )
        
        for export in old_exports:
            if export.file_path and os.path.exists(export.file_path):
                try:
                    os.remove(export.file_path)
                except:
                    pass
        
        old_exports.delete()

@receiver(pre_delete, sender=ReportSession)
def cleanup_session_exports(sender, instance, **kwargs):
    """Clean up exports when session is deleted"""
    # Delete associated export files
    exports = ReportExport.objects.filter(session=instance)
    for export in exports:
        if export.file_path and os.path.exists(export.file_path):
            try:
                os.remove(export.file_path)
            except:
                pass