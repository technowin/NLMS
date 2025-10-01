from django.db import models
from django.db import models
from Account.models import *
class status_master(models.Model):
    status_id = models.AutoField(primary_key=True)
    status_name = models.TextField(null=True, blank=True)
    status_type = models.TextField(null=True, blank=True)
    status_color = models.TextField(null=True, blank=True)
    is_active = models.IntegerField(default=1)  
    level = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    created_by = models.TextField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    updated_by = models.TextField(null=True, blank=True)
    
    class Meta:
        db_table = 'status_master'
        
    def __str__(self):
        return self.status_name or f"Status {self.status_id}"

class status_color(models.Model):
    id = models.AutoField(primary_key=True)
    color = models.TextField(null=True, blank=True)
    
    class Meta:
        db_table = 'status_color'

class department_master(models.Model):
    id = models.AutoField(primary_key=True)
    name =  models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    created_by =  models.TextField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    updated_by =  models.TextField(null=True, blank=True)
    
    class Meta:
        db_table = 'department_master'

class branch_master(models.Model):
    id = models.AutoField(primary_key=True)
    name =  models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    created_by =  models.TextField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    updated_by =  models.TextField(null=True, blank=True)
    
    class Meta:
        db_table = 'branch_master'

class stakeholders(models.Model):
    id = models.AutoField(primary_key=True)
    name =  models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    created_by =  models.TextField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    updated_by =  models.TextField(null=True, blank=True)
    
    class Meta:
        db_table = 'stakeholders'

class send_user(models.Model):
    id = models.AutoField(primary_key=True)
    name =  models.TextField(null=True, blank=True)
    email =  models.TextField(null=True, blank=True)
    mobile =  models.TextField(null=True, blank=True)
    department =  models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    created_by =  models.TextField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    updated_by =  models.TextField(null=True, blank=True)
    
    class Meta:
        db_table = 'send_user'       

class Log(models.Model):
    log_text = models.TextField(null=True,blank=True)
    
    class Meta:
        db_table = 'logs'

class StateMaster(models.Model):
    state_id = models.AutoField(primary_key=True)
    state_name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    created_by =  models.TextField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    updated_by =  models.TextField(null=True, blank=True)

    def __str__(self):
        return self.state_name
    
    class Meta:
        db_table = 'state_master'

class CityMaster(models.Model):
    city_id = models.AutoField(primary_key=True)
    city_name = models.CharField(max_length=100)
    state = models.ForeignKey(StateMaster, null=True, blank=True,on_delete=models.CASCADE, related_name='cities')
    district = models.ForeignKey('Masters.DistrictMaster',null=True, blank=True, on_delete=models.CASCADE, related_name='districts_id')
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    created_by =  models.TextField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    updated_by =  models.TextField(null=True, blank=True)

    def __str__(self):
        return self.city_name
    
    class Meta:
        db_table = 'city_master'

class DistrictMaster(models.Model):
    district_id = models.AutoField(primary_key=True)
    district_name = models.CharField(max_length=100)
    state = models.ForeignKey(StateMaster,null=True, blank=True, on_delete=models.CASCADE, related_name='districts')
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    created_by =  models.TextField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    updated_by =  models.TextField(null=True, blank=True)

    def __str__(self):
        return self.district_name
    
    class Meta:
        db_table = 'district_master'
        
class para_master(models.Model):
    id = models.AutoField(primary_key=True)
    para_name = models.CharField(max_length=100,null=True, blank=True)
    para_details = models.CharField(max_length=100,null=True, blank=True)
    description = models.CharField(max_length=100,null=True, blank=True)
    def __str__(self):
        return self.para_name
    
    class Meta:
        db_table = 'para_master'

class SubjectTypeMaster(models.Model):
    id = models.AutoField(primary_key=True)
    subjectNameEnglish = models.TextField(blank=True, null=True)
    subjectNameMarathi = models.TextField(blank=True, null=True)
    subjectDescription = models.TextField(blank=True, null=True)
    subjectCode = models.IntegerField(blank=True, null=True)
    is_active = models.IntegerField(null=True, blank=True, default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.TextField(blank=True, null=True)
    updated_by = models.TextField(blank=True, null=True)
    
    class Meta:
        db_table = 'tbl_subjecttypemaster'
        
    def __str__(self):
        return self.subjectNameMarathi or self.subjectNameEnglish or f"Subject {self.id}"
    
class BookCatalog(models.Model):
    cat_ref_num = models.AutoField(primary_key=True)
    title = models.TextField(blank=True, null=True)
    subtitle = models.TextField(blank=True, null=True)
    author = models.TextField(blank=True, null=True)
    publisher = models.TextField(blank=True, null=True)
    isbn_issn = models.TextField(blank=True, null=True)
    edition = models.TextField(blank=True, null=True)
    subject = models.ForeignKey(SubjectTypeMaster, on_delete=models.SET_NULL, blank=True, null=True, db_column='subject_id')
    call_number = models.TextField(blank=True, null=True)  # NEW
    cutter_number = models.TextField(blank=True, null=True)  # NEW
    publication_year = models.TextField(blank=True, null=True)  # NEW
    material = models.ForeignKey("Masters.MaterialTypeMaster", on_delete=models.SET_NULL, blank=True, null=True, db_column='material_id')
    remarks = models.TextField(blank=True, null=True)  # NEW
    keywords = models.TextField(blank=True, null=True)
    language = models.TextField(blank=True, null=True)
    publication_place = models.TextField(blank=True, null=True)
    year_of_publication = models.IntegerField(blank=True, null=True)
    classification_number = models.TextField(blank=True, null=True)
    pages = models.TextField(blank=True, null=True)
    date_of_registration = models.DateField(blank=True, null=True)
    other_authors = models.TextField(blank=True, null=True)
    status_id = models.IntegerField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    created_by = models.TextField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    updated_by = models.TextField(null=True, blank=True)
    
    class Meta:
        db_table = 'tbl_bookcatalog'
        
    def __str__(self):
        return f"{self.cat_ref_num} - {self.title or 'Untitled'}"
    
class TestBookCatalog(models.Model):
    cat_ref_num = models.AutoField(primary_key=True)
    title = models.TextField(blank=True, null=True)
    subtitle = models.TextField(blank=True, null=True)
    author = models.TextField(blank=True, null=True)
    publisher = models.TextField(blank=True, null=True)
    isbn_issn = models.TextField(blank=True, null=True)
    edition = models.TextField(blank=True, null=True)
    subject = models.ForeignKey(SubjectTypeMaster, on_delete=models.SET_NULL, blank=True, null=True, db_column='subject_id')
    keywords = models.TextField(blank=True, null=True)
    language = models.TextField(blank=True, null=True)
    publication_place = models.TextField(blank=True, null=True)
    year_of_publication = models.IntegerField(blank=True, null=True)
    classification_number = models.TextField(blank=True, null=True)
    pages = models.TextField(blank=True, null=True)
    date_of_registration = models.DateField(blank=True, null=True)
    status_id = models.IntegerField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    created_by = models.TextField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    updated_by = models.TextField(null=True, blank=True)
    
    class Meta:
        db_table = 'tbl_Testbookcatalog'
        
    def __str__(self):
        return f"{self.cat_ref_num} - {self.title or 'Untitled'}"
    
class LanguageMaster(models.Model):
    id = models.AutoField(primary_key=True)
    language_code = models.TextField(null=True, blank=True)
    language_name = models.TextField(null=True, blank=True)
    is_active = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    created_by = models.TextField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    updated_by = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'tbl_languagemaster'
        
class MaterialTypeMaster(models.Model):
    id = models.AutoField(primary_key=True)
    materialCode = models.TextField(blank=True, null=True)
    materialNameEnglish = models.TextField(blank=True, null=True)
    materialNameMarathi = models.TextField(blank=True, null=True)
    is_active = models.IntegerField(null=True, blank=True, default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.TextField(blank=True, null=True)
    updated_by = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'tbl_materialtypemaster'
        
    def __str__(self):
        return self.materialNameMarathi or self.materialNameEnglish or f"Material {self.id}"
        
class AuthorMaster(models.Model):
    author_code = models.AutoField(primary_key=True)  # Auto-increment
    author_short_name = models.TextField(null=True, blank=True)
    author_name_english = models.TextField(null=True, blank=True)
    author_name_other_english = models.TextField(null=True, blank=True)
    author_name_marathi = models.TextField(null=True, blank=True)
    author_name_other_marathi = models.TextField(null=True, blank=True)
    is_active = models.IntegerField(default=1, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    created_by = models.TextField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    updated_by = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'tbl_authormaster'

class BookAccession(models.Model):
    accession_id = models.AutoField(primary_key=True)
    catalogue = models.ForeignKey(BookCatalog, on_delete=models.CASCADE, db_column="catalog_ref_no", blank=True, null=True)  # Links to BookCatalog
    copy_number = models.IntegerField(blank=True, null=True)
    acquisition_date = models.DateField(blank=True, null=True)
    supplier = models.ForeignKey("Masters.SupplierMaster", on_delete=models.SET_NULL, db_column="supplier_id", blank=True, null=True)  # Links to SupplierMaster
    invoice_number = models.TextField(blank=True, null=True)
    invoice_date = models.DateField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    currency = models.ForeignKey("Masters.CurrencyMaster", on_delete=models.SET_NULL, db_column="currency_id", blank=True, null=True)  # Links to CurrencyMaster
    funding_source = models.ForeignKey("Masters.FundingSourceMaster", on_delete=models.SET_NULL, db_column="source_id", blank=True, null=True)  # Links to FundingSourceMaster
    condition_at_entry = models.ForeignKey("Masters.ConditionAtEntryMaster", on_delete=models.SET_NULL, db_column="condition_id", blank=True, null=True)  # Links to ConditionAtEntryMaster
    location = models.ForeignKey("Masters.ResourceLocationMaster", on_delete=models.SET_NULL, db_column="location_id", blank=True, null=True)  # Links to ResourceLocationMaster
    status = models.ForeignKey(status_master, on_delete=models.SET_NULL, db_column="status_id", blank=True, null=True)  # Links to StatusMaster
    remarks = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    created_by = models.TextField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    updated_by = models.TextField(null=True, blank=True)

    class Meta:
        db_table = "tbl_bookaccession"

class SupplierMaster(models.Model):
    supplier_id = models.AutoField(primary_key=True)
    supplier_code = models.CharField(max_length=50, unique=True)
    supplier_name = models.CharField(max_length=200)
    supplier_mobile = models.CharField(max_length=15, null=True, blank=True)
    supplier_email = models.EmailField(max_length=200, null=True, blank=True)
    supplier_address = models.TextField(null=True, blank=True)
    supplier_pincode = models.CharField(max_length=10, null=True, blank=True)
    is_active = models.IntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    created_by = models.TextField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    updated_by = models.TextField(null=True, blank=True)

    class Meta:
        db_table = "tbl_suppliermaster"
        
class FundingSourceMaster(models.Model):
    source_id = models.AutoField(primary_key=True)
    source_code = models.CharField(max_length=50, unique=True)
    funding_source_name = models.TextField(null=True, blank=True)
    is_active = models.IntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    created_by = models.TextField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    updated_by = models.TextField(null=True, blank=True)

    class Meta:
        db_table = "tbl_fundingsourcemaster"
        
class ConditionAtEntryMaster(models.Model):
    condition_id = models.AutoField(primary_key=True)
    condition_code = models.CharField(max_length=50, unique=True)
    condition_at_entry = models.CharField(max_length=200)
    is_active = models.IntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    created_by = models.TextField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    updated_by = models.TextField(null=True, blank=True)

    class Meta:
        db_table = "tbl_conditionatentrymaster"
        
class CurrencyMaster(models.Model):
    currency_id = models.AutoField(primary_key=True)
    currency_code = models.CharField(max_length=10, unique=True)   # e.g. USD, INR
    currency_name = models.CharField(max_length=100)               # e.g. US Dollar, Indian Rupee
    is_active = models.IntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    created_by = models.TextField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    updated_by = models.TextField(null=True, blank=True)

    class Meta:
        db_table = "tbl_currencymaster"
       
class ResourceLocationMaster(models.Model):
    location_id = models.AutoField(primary_key=True)
    location_code = models.CharField(max_length=50, unique=True)   # e.g. LOC001, STOR1
    location_name = models.CharField(max_length=200)               # e.g. Main Library, Storage Room
    is_active = models.IntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    created_by = models.TextField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    updated_by = models.TextField(null=True, blank=True)

    class Meta:
        db_table = "tbl_resourcelocationmaster"
        
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
        return f"Ward {self.ward_id} - {self.ward_name}"
    
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
        return f"{self.location_name} ({self.location_id})"