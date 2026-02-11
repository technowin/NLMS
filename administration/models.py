from django.db import models
from Account.models import *
from Masters.models import *

class LibraryMaster(models.Model):
    id = models.AutoField(primary_key=True)  # auto-increment
    library_code = models.TextField(null=True, blank=True)
    library_name = models.TextField(null=True, blank=True)
    library_name_mar = models.TextField(null=True, blank=True)
    location = models.ForeignKey('Masters.LibraryLocationMaster', on_delete=models.SET_NULL, related_name="libraries", db_column="location_id", null=True, blank=True)
    parent_ward = models.ForeignKey('Masters.WardMaster', on_delete=models.SET_NULL, related_name="ward_libraries", db_column="ward_id", null=True, blank=True)
    library_accounting_code = models.ForeignKey('Masters.WardMaster', on_delete=models.SET_NULL, related_name="ward_accounting_code", db_column="accounting_id", null=True, blank=True)
    landing_page_link = models.TextField(null=True, blank=True)
    about_library = models.TextField(null=True, blank=True)
    library_rules = models.TextField(null=True, blank=True)
    membership_rules = models.TextField(null=True, blank=True)
    membership_page_link = models.TextField(null=True, blank=True)
    contact_email = models.TextField(null=True, blank=True)
    contact_phone = models.TextField(null=True, blank=True)
    opening_hours = models.TextField(null=True, blank=True)
    is_active = models.IntegerField(default=1)
    location_url = models.TextField(null=True, blank=True)
    librarian_name = models.TextField(null=True, blank=True)
    image_url = models.TextField(null=True, blank=True)
    facebook_url = models.TextField(null=True, blank=True)
    twitter_url = models.TextField(null=True, blank=True)
    instagram_url = models.TextField(null=True, blank=True)
    youtube_url = models.TextField(null=True, blank=True)
    est_year = models.TextField(null=True, blank=True)
    capacity = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    created_by = models.TextField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    updated_by = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'tbl_librarymaster'

    def __str__(self):
        return f"{self.library_name} ({self.library_code})"
    

