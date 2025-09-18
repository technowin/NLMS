from django.db import models
from decimal import Decimal

class tbl_librarymasterL01(models.Model):
    id = models.AutoField(primary_key=True)  # auto-increment
    library_code = models.TextField(null=True, blank=True)
    library_name = models.TextField(null=True, blank=True)
    library_name_mar = models.TextField(null=True, blank=True)
    location = models.TextField(null=True, blank=True)
    parent_ward = models.TextField(null=True, blank=True)
    library_accounting_code = models.TextField(null=True, blank=True)
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
        db_table = 'tbl_librarymasterL01'

    def __str__(self):
        return f"{self.library_name} ({self.library_code})"

class MembershipMaster(models.Model):
    id = models.AutoField(primary_key=True)
    membership_code = models.CharField(max_length=50, unique=True, null=True, blank=True)  # <-- changed
    membership_type = models.TextField(null=True, blank=True)
    membership_type_en = models.TextField(null=True, blank=True)
    deposit = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    entry_fees = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    subscription_fees = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    fine = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    outsider = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    days = models.IntegerField(default=0)
    item = models.IntegerField(default=0)
    remarks_txt = models.TextField(null=True, blank=True)
    isactive = models.IntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    created_by = models.TextField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    updated_by = models.TextField(null=True, blank=True)

    class Meta:
        db_table = "tbl_membershipmaster"

    def __str__(self):
        return f"{self.membership_code} - {self.membership_type}"

class StatusMaster(models.Model):
    id = models.AutoField(primary_key=True)
    status_code = models.CharField(max_length=50, unique=True)
    status_name = models.CharField(max_length=100)
    description = models.TextField(null=True, blank=True)
    isactive = models.IntegerField(default=1)

    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    created_by = models.CharField(max_length=50, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    updated_by = models.CharField(max_length=50, null=True, blank=True)

    class Meta:
        db_table = "tbl_statusmaster"

    def __str__(self):
        return f"{self.status_code} - {self.status_name}"
    
class DocumentMaster(models.Model):
    id = models.AutoField(primary_key=True)
    document_name = models.CharField(max_length=500)
    document_name_mar = models.CharField(max_length=500)
    description = models.TextField(null=True, blank=True)
    isactive = models.IntegerField(default=1)

    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    created_by = models.CharField(max_length=50, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    updated_by = models.CharField(max_length=50, null=True, blank=True)

    class Meta:
        db_table = "tbl_documentmaster"

    def __str__(self):
        return self.document_name

class parameter_master_L01(models.Model):
    parameter_id = models.AutoField(primary_key=True)
    parameter_name =models.TextField(null=True,blank=True)
    parameter_value =models.TextField(null=True,blank=True)
    isactive = models.IntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    created_by = models.CharField(max_length=50, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    updated_by = models.CharField(max_length=50, null=True, blank=True)
    
    class Meta:
        db_table = 'parameter_master_L01'
    def __str__(self):
        return self.parameter_name
    
class MembershipDetails(models.Model):
    id = models.AutoField(primary_key=True)
    first_name = models.TextField(null=True, blank=True)
    middle_name = models.TextField(null=True, blank=True)
    last_name = models.TextField(null=True, blank=True)
    first_name_mar = models.TextField(null=True, blank=True)
    middle_name_mar = models.TextField(null=True, blank=True)
    last_name_mar = models.TextField(null=True, blank=True)
    ward = models.TextField(null=True, blank=True)
    pincode = models.TextField(null=True, blank=True)
    library_name = models.TextField(null=True, blank=True)
    library_name_mar = models.TextField(null=True, blank=True)
    local_address = models.TextField(null=True, blank=True)
    mobile_no = models.TextField(null=True, blank=True)
    occupation = models.TextField(null=True, blank=True)
    office_phone = models.TextField(null=True, blank=True)
    education = models.TextField(null=True, blank=True)
    institute_name = models.TextField(null=True, blank=True)
    recommender_details = models.TextField(null=True, blank=True)
    dob = models.DateField(null=True, blank=True)
    membership = models.ForeignKey(MembershipMaster, on_delete=models.CASCADE, db_column="membershipmaster_id", related_name="membership_holders")
    status = models.ForeignKey(StatusMaster, on_delete=models.CASCADE, db_column="status_id", related_name="memberships")
    aadhar_no = models.CharField(max_length=12, unique=True)
    user_id = models.CharField(max_length=50, unique=True)
    password = models.CharField(max_length=255)
    member_type = models.ForeignKey(parameter_master_L01, on_delete=models.SET_NULL, null=True, blank=True, db_column="member_type_id", related_name="membership_types")
    is_resident_of_nmmc = models.IntegerField(default=0)   # 0 = No, 1 = Yes
    address_same_as_aadhar = models.IntegerField(default=0)  # 0 = No, 1 = Yes
    membership_duration = models.IntegerField(null=True, blank=True)  # ✅ months
    from_date = models.DateField(null=True, blank=True)   # ✅ new
    to_date = models.DateField(null=True, blank=True)     # ✅ new
    deposit = models.FloatField(null=True, blank=True)    # ✅ new
    entry_fees = models.FloatField(null=True, blank=True) # ✅ new
    subscription = models.FloatField(null=True, blank=True) # ✅ new
    email = models.EmailField(max_length=255, null=True, blank=True, unique=True)

    isactive = models.IntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    created_by = models.CharField(max_length=50, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    updated_by = models.CharField(max_length=50, null=True, blank=True)

    class Meta: db_table = "tbl_membershipdetails"

    def __str__(self):
        full_name = " ".join(filter(None, [self.first_name, self.middle_name, self.last_name]))
        return f"{full_name} ({self.user_id})"

class DocumentDetails(models.Model):
    id = models.AutoField(primary_key=True)
    membership = models.ForeignKey(MembershipDetails, on_delete=models.CASCADE, db_column="membership_id", related_name="documents")
    document = models.ForeignKey(DocumentMaster, on_delete=models.CASCADE, db_column="document_id", related_name="document_usages")
    file_name = models.CharField(max_length=555, null=True, blank=True)
    file_path = models.CharField(max_length=555, null=True, blank=True)
    isactive = models.IntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    created_by = models.CharField(max_length=50, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    updated_by = models.CharField(max_length=50, null=True, blank=True)

    class Meta: db_table = "tbl_documentdetails"
    def __str__(self): return f"{self.membership.full_name} - {self.document.document_name}"

