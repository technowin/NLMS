from django.db import models
from Account.models import *
from Masters.models import *

class LibraryMaster(models.Model):
    id = models.AutoField(primary_key=True)  # auto-increment
    library_code = models.TextField(null=True, blank=True)
    library_name = models.TextField(null=True, blank=True)
    location = models.ForeignKey(LibraryLocationMaster, on_delete=models.SET_NULL, related_name="libraries", db_column="location_id", null=True, blank=True)
    parent_ward = models.ForeignKey(WardMaster, on_delete=models.SET_NULL, related_name="ward_libraries", db_column="ward_id", null=True, blank=True)
    library_accounting_code = models.ForeignKey(WardMaster, on_delete=models.SET_NULL, related_name="ward_accounting_code", db_column="accounting_id", null=True, blank=True)
    landing_page_link = models.TextField(null=True, blank=True)
    about_library = models.TextField(null=True, blank=True)
    membership_page_link = models.TextField(null=True, blank=True)
    is_active = models.IntegerField(default=1)
    establishedYear = models.TextField(null=True, blank=True)
    image_url = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    created_by = models.TextField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    updated_by = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'tbl_librarymaster'

    def __str__(self):
        return f"{self.library_name} ({self.library_code})"
