from django.db import models
from administration.models import * 

class error_log(models.Model):
    id = models.AutoField(primary_key=True)
    method =models.TextField(null=True,blank=True)
    error =models.TextField(null=True,blank=True)
    error_date = models.DateTimeField(null=True,blank=True,auto_now_add=True)
    user_id = models.TextField(null=True,blank=True)
    
    class Meta:
        db_table = 'error_log'

class WardMaster(models.Model):
    ward_id = models.AutoField(primary_key=True)
    ward_name = models.TextField(null=True, blank=True)              # Ward name
    ward_address = models.TextField(null=True, blank=True)           # Address of the ward
    pincode = models.TextField(null=True, blank=True)                # comma-separated pincodes
    accounting_code = models.TextField(null=True, blank=True)        # accounting code
    is_active = models.IntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    created_by = models.TextField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    updated_by = models.TextField(null=True, blank=True)

    class Meta:
        db_table = "tbl_wardmaster"

    def __str__(self):
        return f"Ward {self.ward_no} - {self.ward_name}"
    
class LibraryLocationMaster(models.Model):
    location_id = models.AutoField(primary_key=True)
    location_name = models.TextField(null=True, blank=True)                # Library name
    address = models.TextField(null=True, blank=True)                      # Address of library
    pincode = models.TextField(null=True, blank=True)                      # Pincode
    ward = models.ForeignKey(WardMaster,on_delete=models.CASCADE,related_name="libraries",   db_column="ward_id",null=True,blank=True)
    is_active = models.IntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    created_by = models.TextField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    updated_by = models.TextField(null=True, blank=True)

    class Meta:
        db_table = "tbl_librarylocationmaster"

    def __str__(self):
        return f"{self.location_name} ({self.location_code})"

class tbl_librarymasterL01(models.Model):
    id = models.AutoField(primary_key=True)  # auto-increment
    library_code = models.TextField(null=True, blank=True)
    library_name = models.TextField(null=True, blank=True)
    location = models.ForeignKey(LibraryLocationMaster, on_delete=models.SET_NULL, related_name="librariesL01", db_column="location_id", null=True, blank=True)
    parent_ward = models.ForeignKey(WardMaster, on_delete=models.SET_NULL, related_name="ward_librariesL01", db_column="ward_id", null=True, blank=True)
    library_accounting_code = models.ForeignKey(WardMaster, on_delete=models.SET_NULL, related_name="ward_accounting_codeL01", db_column="accounting_id", null=True, blank=True)
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
    capacity = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    created_by = models.TextField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    updated_by = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'tbl_librarymasterL01'

    def __str__(self):
        return f"{self.library_name} ({self.library_code})"