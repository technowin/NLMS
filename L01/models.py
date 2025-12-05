from django.db import models
from decimal import Decimal
from Masters.models import *

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
    other_ward = models.TextField(null=True, blank=True)  
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
    actionperformed = models.TextField(null=True, blank=True)  # admin username/id
    reviewed = models.CharField(max_length=50, null=True, blank=True)  # admin username/id
    reviewed_at = models.DateTimeField(null=True, blank=True)
    isactive = models.IntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    created_by = models.CharField(max_length=50, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    updated_by = models.CharField(max_length=50, null=True, blank=True)
    membership_code = models.TextField(null=True, blank=True)
    membership_renew = models.IntegerField(default=0)
    remarks = models.TextField(null=True, blank=True)

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

class IncrementMaster(models.Model):
    id = models.AutoField(primary_key=True)
    incrementFieldName = models.CharField(max_length=50, unique=True)
    incrementFieldNumber = models.TextField(null=True, blank=True)
    isactive = models.IntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    created_by = models.CharField(max_length=50, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    updated_by = models.CharField(max_length=50, null=True, blank=True)

    class Meta:
        db_table = "tbl_incrementmaster"

class PaymentDetails(models.Model):
    id = models.AutoField(primary_key=True)
    membership = models.ForeignKey(MembershipDetails,on_delete=models.CASCADE,db_column="membership_id",related_name="payments")
    payment_mode = models.CharField(max_length=20)
    payment_type = models.TextField(null=True, blank=True)  
    payment_method = models.CharField(max_length=50, null=True, blank=True)  # e.g., 'Cash', 'Cheque', 'UPI', 'Card'
    deposit_amount = models.FloatField(null=True, blank=True)
    entry_fee_amount = models.FloatField(null=True, blank=True)
    monthly_subscription_amount = models.FloatField(null=True, blank=True)
    total_subscription_amount = models.FloatField(null=True, blank=True)
    fine_amount = models.FloatField(null=True, blank=True)
    book_fine_amount = models.FloatField(null=True, blank=True)
    subscription_from = models.DateField(null=True, blank=True)
    subscription_to = models.DateField(null=True, blank=True)
    status = models.ForeignKey(StatusMaster,on_delete=models.SET_NULL,null=True,blank=True,db_column="status_id",related_name="payment_statuses")
    transaction_id = models.CharField(max_length=100, null=True, blank=True)  # Online txn ID or receipt
    remarks = models.TextField(null=True, blank=True)
    user_id = models.CharField(max_length=50, null=True, blank=True)
    membership_code = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.CharField(max_length=50, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.CharField(max_length=50, null=True, blank=True)
    payment_date = models.DateField(null=True, blank=True) 
    circulation_transaction = models.ForeignKey('CirculationTransaction', on_delete=models.SET_NULL, null=True, blank=True, db_column="circulation_transaction_id", related_name="payments")

    class Meta:
        db_table = "tbl_paymentdetails"

    def __str__(self):
        return f"{self.membership} - {self.payment_mode} - {self.total_amount} ₹"

class MembershipDetailsHistory(models.Model):
    id = models.AutoField(primary_key=True)
    membership = models.ForeignKey(MembershipDetails, on_delete=models.CASCADE, db_column='membershipdetails_id', related_name='history')
    membershipmaster = models.ForeignKey(MembershipMaster, on_delete=models.SET_NULL, null=True, blank=True, db_column='membershipmaster_id', related_name='membership_holders_history')
    status = models.ForeignKey(StatusMaster, on_delete=models.SET_NULL, null=True, blank=True, db_column='status_id', related_name='memberships_history')
    member_type = models.ForeignKey(parameter_master_L01, on_delete=models.SET_NULL, null=True, blank=True, db_column='member_type_id', related_name='membership_types_history')
    
    first_name = models.TextField(null=True, blank=True)
    middle_name = models.TextField(null=True, blank=True)
    last_name = models.TextField(null=True, blank=True)
    first_name_mar = models.TextField(null=True, blank=True)
    middle_name_mar = models.TextField(null=True, blank=True)
    last_name_mar = models.TextField(null=True, blank=True)
    ward = models.TextField(null=True, blank=True)
    other_ward = models.TextField(null=True, blank=True)  
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
    aadhar_no = models.CharField(max_length=12, null=True, blank=True)
    user_id = models.CharField(max_length=50, null=True, blank=True)
    password = models.CharField(max_length=255, null=True, blank=True)
    membership_duration = models.IntegerField(null=True, blank=True)
    from_date = models.DateField(null=True, blank=True)
    to_date = models.DateField(null=True, blank=True)
    deposit = models.FloatField(null=True, blank=True)
    entry_fees = models.FloatField(null=True, blank=True)
    subscription = models.FloatField(null=True, blank=True)
    email = models.EmailField(max_length=255, null=True, blank=True)
    is_resident_of_nmmc = models.IntegerField(default=0)
    address_same_as_aadhar = models.IntegerField(default=0)
    actionperformed = models.TextField(null=True, blank=True)
    reviewed = models.CharField(max_length=50, null=True, blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    isactive = models.IntegerField(default=1)
    membership_code = models.TextField(null=True, blank=True)
    membership_renew = models.IntegerField(default=0)
    created_at = models.DateTimeField(null=True, blank=True)
    created_by = models.CharField(max_length=50, null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)
    updated_by = models.CharField(max_length=50, null=True, blank=True)

    # History tracking fields
    changed_by = models.CharField(max_length=50, null=True, blank=True)
    changed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "tbl_membershipdetails_history"

    def __str__(self):
        full_name = " ".join(filter(None, [self.first_name, self.middle_name, self.last_name]))
        return f"{full_name} ({self.change_type} at {self.changed_at})"

class DocumentDetailsHistory(models.Model):
    id = models.AutoField(primary_key=True)
    original_document = models.ForeignKey(DocumentDetails,on_delete=models.SET_NULL,null=True,blank=True,db_column="documentdetails_id",related_name="history_versions")
    document = models.ForeignKey(DocumentMaster,on_delete=models.CASCADE,db_column="document_id",related_name="document_history")
    membership = models.ForeignKey(MembershipDetails,on_delete=models.CASCADE,db_column="membership_id",related_name="document_history")
    file_name = models.CharField(max_length=555)
    file_path = models.CharField(max_length=555)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.CharField(max_length=50, null=True, blank=True)

    class Meta:
        db_table = "tbl_documentdetails_history"

    def __str__(self):
        return f"{self.membership.full_name} - {self.document.document_name} ({self.uploaded_at})"

class CirculationCopyStatus(models.Model):
    id = models.AutoField(primary_key=True)
    accession = models.ForeignKey(
        BookAccession,
        on_delete=models.CASCADE,
        db_column="accession_id",
        blank=True,
        null=True,
        related_name="accession_status"
    )
    bookcatalog = models.ForeignKey(
        BookCatalog,
        on_delete=models.CASCADE,
        db_column="bookcatalog_id",
        blank=True,
        null=True,
        related_name="bookcatalog_status"
    )
    barcode = models.CharField(max_length=50, unique=True, blank=True, null=True)
    accession_no = models.CharField(max_length=50, unique=True, blank=True, null=True)
    shelf_location = models.ForeignKey(
        ResourceLocationMaster,
        on_delete=models.SET_NULL,
        db_column="shelf_location_status_id",
        blank=True,
        null=True,
        related_name="shelf_location_status",
    )
    processing_status = models.ForeignKey(
        status_master,
        on_delete=models.SET_NULL,
        db_column="processing_status_id",
        blank=True,
        null=True,
        related_name="processing_status",
    )
    current_status = models.ForeignKey(
        status_master,
        on_delete=models.SET_NULL,
        db_column="current_status_id",
        blank=True,
        null=True,
        related_name="current_status",
    )
    date_processed = models.DateField(blank=True, null=True)
    remarks = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    created_by = models.TextField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    updated_by = models.TextField(null=True, blank=True)
    
    class Meta:
        db_table = "tbl_circulation"
    
    def __str__(self):
        return f"{self.barcode or 'No Barcode'} ({self.current_status or 'Unknown'})"
    
class CirculationTransaction(models.Model):
    id = models.AutoField(primary_key=True)
    catalog = models.ForeignKey(BookCatalog,on_delete=models.SET_NULL,null=True,blank=True,db_column="cat_ref_num",related_name="transactions")  # All transactions for this catalog/book title
    accession = models.ForeignKey( BookAccession,on_delete=models.CASCADE,db_column="accession_id",related_name="transactions" )
    circulation = models.ForeignKey(CirculationCopyStatus,on_delete=models.SET_NULL,null=True,blank=True,db_column="copy_status_id",related_name="transactions")  # All transactions linked to a particular copy status)
    member = models.ForeignKey(MembershipDetails,on_delete=models.CASCADE,db_column="member_id",related_name="transactions" )
    barcode = models.CharField(max_length=50, blank=True, null=True)
    issue_date = models.DateField(blank=True, null=True)
    due_date = models.DateField(blank=True, null=True)
    return_date = models.DateField(blank=True, null=True)
    days_overdue_count = models.IntegerField(default=0)
    book_fine_amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    total_fine = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    fine_amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    adjusted_fine = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, default=0)  # <-- new
    fine_status = models.CharField(max_length=20, blank=True, null=True)
    fine_paid_date = models.DateField(blank=True, null=True)
    transaction_type = models.CharField(max_length=20, blank=True, null=True)
    transaction_status = models.CharField(max_length=20, blank=True, null=True)
    issued_by = models.TextField(null=True, blank=True)
    received_by = models.TextField(null=True, blank=True)
    membership_code = models.TextField(blank=True, null=True)
    return_condition = models.ForeignKey(status_master,on_delete=models.SET_NULL,null=True,blank=True,related_name="transactions_with_condition")
    remarks = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    created_by = models.TextField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    updated_by = models.TextField(null=True, blank=True)

    class Meta:
        db_table = "tbl_circulation_transaction"

class PaymentReport(models.Model):
    id = models.AutoField(primary_key=True)
    from_date = models.DateField()
    to_date = models.DateField()
    generated_date = models.DateField(auto_now_add=True)
    receipt_no = models.CharField(max_length=500, blank=True, null=True)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    deposit_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    deposit_date = models.DateTimeField(blank=True, null=True)
    receipt_upload = models.TextField(blank=True, null=True)  # storing folder/file path
    remarks = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    created_by = models.TextField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    updated_by = models.TextField(null=True, blank=True)

    class Meta:
        db_table = "tbl_payment_report"

    def __str__(self):
        return f"Receipt #{self.receipt_no or self.id} ({self.from_date} - {self.to_date})"
    
class PaymentReportKeyValue(models.Model):
    id = models.AutoField(primary_key=True)
    payment_report = models.ForeignKey(
        PaymentReport,
        on_delete=models.CASCADE,
        related_name="key_values",
        db_column="payment_report_id"
    )
    key = models.CharField(max_length=255)
    value = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "tbl_payment_report_keyvalue"

    def __str__(self):
        return f"{self.key}: {self.value}"

class CompetitiveExamMaster(models.Model):
    competitive_id = models.AutoField(primary_key=True)
    full_name = models.TextField(null=True, blank=True)
    short_form = models.CharField(max_length=50, null=True, blank=True)
    competitive_description = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    created_by = models.CharField(max_length=50, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    updated_by = models.CharField(max_length=50, null=True, blank=True)

    class Meta:
        db_table = "tbl_competitive_exam_master"

    def __str__(self):
        return f"{self.full_name} ({self.short_form})" if self.short_form else self.full_name

class Sections(models.Model):
    section_no = models.CharField(max_length=50, primary_key=True)
    competitive_id = models.ForeignKey(CompetitiveExamMaster, on_delete=models.CASCADE, db_column="competitive_id", related_name="sections")
    section_name = models.TextField(null=True, blank=True)
    section_description = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    created_by = models.CharField(max_length=50, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    updated_by = models.CharField(max_length=50, null=True, blank=True)

    class Meta:
        db_table = "tbl_sections"

    def __str__(self):
        return f"{self.section_no} - {self.section_name}" if self.section_name else self.section_no

class Subjects(models.Model):
    subject_id = models.AutoField(primary_key=True)
    section_no = models.ForeignKey(Sections, on_delete=models.CASCADE, db_column="section_no", related_name="subjects")

    competitive_id = models.ForeignKey(
        CompetitiveExamMaster,
        on_delete=models.CASCADE,
        db_column="competitive_id",
        related_name="subjects",
        null=True, blank=True
    )

    subject_name = models.TextField(null=True, blank=True)
    subject_description = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    created_by = models.CharField(max_length=50, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    updated_by = models.CharField(max_length=50, null=True, blank=True)

    class Meta:
        db_table = "tbl_subjects"

    def __str__(self):
        return f"{self.subject_name}" if self.subject_name else f"Subject {self.subject_id}"

class Topics(models.Model):
    topic_id = models.AutoField(primary_key=True)
    section_no = models.ForeignKey(
        Sections,
        on_delete=models.CASCADE,
        db_column="section_no",
        related_name="topics",
        null=True, blank=True
    )

    competitive_id = models.ForeignKey(
        CompetitiveExamMaster,
        on_delete=models.CASCADE,
        db_column="competitive_id",
        related_name="topics",
        null=True, blank=True
    )

    subject_id = models.ForeignKey(
        Subjects,
        on_delete=models.CASCADE,
        db_column="subject_id",
        related_name="topics"
    )
    topic_name = models.TextField(null=True, blank=True)
    topic_reference = models.TextField(null=True, blank=True)
    topic_image_url = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    created_by = models.CharField(max_length=50, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    updated_by = models.CharField(max_length=50, null=True, blank=True)

    class Meta:
        db_table = "tbl_topics"

    def __str__(self):
        return f"{self.topic_name}" if self.topic_name else f"Topic {self.topic_id}"

class Chapters(models.Model):
    chapter_no = models.CharField(max_length=50, primary_key=True)

    section_no = models.ForeignKey(
        Sections,
        on_delete=models.CASCADE,
        db_column="section_no",
        related_name="chapters",
        null=True, blank=True
    )

    competitive_id = models.ForeignKey(
        CompetitiveExamMaster,
        on_delete=models.CASCADE,
        db_column="competitive_id",
        related_name="chapters",
        null=True, blank=True
    )

    topic_id = models.ForeignKey(
        Topics,
        on_delete=models.CASCADE,
        db_column="topic_id",
        related_name="chapters"
    )
    chapter_name = models.TextField(null=True, blank=True)
    chapter_pdf_url = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    created_by = models.CharField(max_length=50, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    updated_by = models.CharField(max_length=50, null=True, blank=True)

    class Meta:
        db_table = "tbl_chapters"

    def __str__(self):
        return f"{self.chapter_no} - {self.chapter_name}" if self.chapter_name else self.chapter_no

class MemberEntryExit(models.Model):
    membership_code = models.CharField(max_length=100)
    entry_time = models.DateTimeField(null=True, blank=True)
    exit_time = models.DateTimeField(null=True, blank=True)
    role_id = models.IntegerField(null=True, blank=True)
    remark = models.TextField(null=True, blank=True)
    created_by = models.ForeignKey(CustomUser, related_name='member_entry_created',on_delete=models.SET_NULL, null=True, blank=True)
    updated_by = models.ForeignKey(CustomUser, related_name='member_entry_updated',on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "tbl_member_log"

    def __str__(self):
        return f"{self.membership_code} - Entry/Exit"
    

    class EbookTypeMaster(models.Model):
        type_id = models.AutoField(primary_key=True)
        ebookTypeCode = models.TextField(blank=True, null=True)
        ebookTypeNameEnglish = models.TextField(blank=True, null=True)
        ebookTypeNameMarathi = models.TextField(blank=True, null=True)
        is_active = models.IntegerField(null=True, blank=True, default=1)
        created_at = models.DateTimeField(auto_now_add=True)
        updated_at = models.DateTimeField(auto_now=True)
        created_by = models.TextField(blank=True, null=True)
        updated_by = models.TextField(blank=True, null=True)

        class Meta:
            db_table = 'tbl_ebooktypemaster'

        def __str__(self):
            return (
                self.ebookTypeNameMarathi 
                or self.ebookTypeNameEnglish 
                or f"EbookType {self.type_id}"
            )
        
class LibraryEbook(models.Model):
        ebook_id = models.AutoField(primary_key=True)
        eb_title = models.TextField(blank=True, null=True)
        eb_subtitle = models.TextField(blank=True, null=True)
        eb_author = models.TextField(blank=True, null=True)
        eb_publisher = models.TextField(blank=True, null=True)
        eb_isbn_issn = models.TextField(blank=True, null=True)
        eb_edition = models.TextField(blank=True, null=True)
        eb_pdf_url = models.TextField(blank=True, null=True)
        eb_subject = models.ForeignKey(SubjectTypeMaster, on_delete=models.SET_NULL, blank=True, null=True, db_column='subject_id')
        call_number = models.TextField(blank=True, null=True)  # NEW
        cutter_number = models.TextField(blank=True, null=True)  # NEW
        e_publication_year = models.TextField(blank=True, null=True)  # NEW
        ebook_type = models.ForeignKey('EbookTypeMaster',on_delete=models.SET_NULL,null=True,blank=True,db_column='ebook_type_id')
        remarks = models.TextField(blank=True, null=True)  # NEW
        eb_keywords = models.TextField(blank=True, null=True)
        eb_language = models.TextField(blank=True, null=True)
        eb_publication_place = models.TextField(blank=True, null=True)
        eb_year_of_publication = models.IntegerField(blank=True, null=True)
        eb_classification_number = models.TextField(blank=True, null=True)
        eb_pages = models.TextField(blank=True, null=True)
        eb_date_of_registration = models.DateField(blank=True, null=True)
        eb_other_authors = models.TextField(blank=True, null=True)
        eb_front_page_photo = models.TextField(blank=True, null=True)
        eb_last_page_photo = models.TextField(blank=True, null=True)
        eb_status_id = models.IntegerField(blank=True, null=True)
        created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
        created_by = models.TextField(null=True, blank=True)
        updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
        updated_by = models.TextField(null=True, blank=True)

        class Meta:
            db_table = 'tbl_library_ebooks'

        def __str__(self):
            return f"{self.ebook_id} - {self.title}"
class EODLog(models.Model):
    date = models.DateField()
    is_eod_done = models.BooleanField(default=False)
    status = models.CharField(max_length=100, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name='eod_created_by')
    updated_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name='eod_updated_by')

    def __str__(self):
        return f"EODLog {self.id} - {self.date}"
    
    class Meta:
            db_table = 'tbl_eod_log'
class BookReturnLog(models.Model):
    eod_log = models.ForeignKey(EODLog, on_delete=models.CASCADE, related_name='return_logs')
    cat_rem_num = models.ForeignKey(BookCatalog, on_delete=models.CASCADE, related_name='catalog_returns')
    barcode = models.CharField(max_length=100)
    is_shelved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name='return_created_by')
    updated_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name='return_updated_by')

    def __str__(self):
        return f"ReturnLog {self.id} - {self.barcode}"
    
    class Meta:
            db_table = 'tbl_book_return_log'

class BookReview(models.Model):
    book = models.ForeignKey(BookCatalog, on_delete=models.SET_NULL, blank=True, null=True, db_column='cat_ref_id', related_name='cat_ref_id_reviews')
    user_id = models.IntegerField()  # store member id as int
    rating = models.PositiveSmallIntegerField()  # 1-5
    review = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    library_code = models.CharField(max_length=50, null=True, blank=True)  # optional

    class Meta:
        db_table = 'tbl_book_review'
        ordering = ['-created_at']

    def __str__(self):
        return f"Review by User {self.user_id} for Book {self.book.title}"
    
class BookMaster(models.Model):
    isbn_10 = models.CharField(max_length=20, null=True, blank=True)
    isbn_13 = models.CharField(max_length=20, null=True, blank=True)
    title = models.CharField(max_length=500)
    description = models.TextField(null=True, blank=True)
    language = models.CharField(max_length=10, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.TextField(null=True, blank=True)
    updated_by = models.TextField(null=True, blank=True)
    def __str__(self):
        return self.title
    class Meta:
        db_table = 'tbl_book_master'


class BookDetails(models.Model):
    master = models.ForeignKey(BookMaster, on_delete=models.CASCADE, related_name='details')
    author = models.CharField(max_length=255, null=True, blank=True)
    publisher = models.CharField(max_length=255, null=True, blank=True)
    published_date = models.CharField(max_length=20, null=True, blank=True)
    page_count = models.IntegerField(null=True, blank=True)
    category = models.CharField(max_length=255, null=True, blank=True)
    preview_link = models.TextField(null=True, blank=True)
    edition = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.TextField(null=True, blank=True)
    updated_by = models.TextField(null=True, blank=True)
    def __str__(self):
        return f"{self.master.title} - {self.author}"
    
    class Meta:
        db_table = 'tbl_book_detail'





