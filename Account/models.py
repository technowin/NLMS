
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager,PermissionsMixin
from django.db import models
from django.utils import timezone

class CustomUserManager(BaseUserManager):

    def create_user(self, username, email, password=None, **extra_fields):
        if not username:
            raise ValueError('The Username field must be set')
        if not email:
            raise ValueError('The Email field must be set')

        email = self.normalize_email(email)
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(username, email, password, **extra_fields)

class CustomUser(AbstractBaseUser,PermissionsMixin):
    USER_TYPES = (
        ('admin', 'Admin'),
        ('librarian', 'Librarian'),
        ('account', 'Accounts'),
        ('student', 'Student/Member'),
        ('guest', 'Guest'),
    )

    id = models.AutoField(primary_key=True)
    first_name = models.CharField(max_length=255, null=True, blank=True)
    last_name = models.CharField(max_length=255, null=True, blank=True)
    full_name = models.CharField(max_length=255)
    email = models.EmailField()
    phone = models.CharField(max_length=15)
    first_time_login = models.IntegerField(default=1)
    last_login = models.DateTimeField(default=timezone.now)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=True)
    role_id = models.BigIntegerField(null=True, blank=True)
    profile_image = models.ImageField(upload_to='profile_images/', null=True, blank=True)
    dark_mode = models.BooleanField(default=False)
    email_verified = models.BooleanField(default=False)
    session_key = models.CharField(max_length=255, null=True, blank=True)
    is_logged_in = models.BooleanField(default=False)
    phone_verified = models.BooleanField(default=False)
    last_activity = models.DateTimeField(auto_now=True)
    date_joined = models.DateTimeField(auto_now_add=True)   # ✅ better than auto_now

    # 🔹 New unique username field
    username = models.CharField(max_length=255, unique=True)

    user_type = models.CharField(max_length=10, choices=USER_TYPES, default='guest')
    address = models.TextField(blank=True)
    govt_id = models.CharField(max_length=50, blank=True)
    id_proof = models.FileField(upload_to='id_proofs/', blank=True)

    objects = CustomUserManager()

    # 🔹 Authentication will now use `username`
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email', 'full_name', 'phone']  

    class Meta:
        db_table = 'users'

    def __str__(self):
        return self.username   # ✅ display username instead of email

    def get_full_name(self):
        return f"{self.full_name}".strip()

    @property
    def profile_picture_url(self):
        if self.profile_image and hasattr(self.profile_image, 'url'):
            return self.profile_image.url
        return '/static/images/user.png'

class roles(models.Model):
    id = models.AutoField(primary_key=True)
    role_name = models.TextField(null=True, blank=True)
    role_disc = models.TextField(null=True, blank=True)
    role_type = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(null=True, blank=True, auto_now_add=True)
    updated_at = models.DateTimeField(null=True, blank=True, auto_now=True)
    created_by = models.TextField(null=True, blank=True)
    updated_by = models.TextField(null=True, blank=True)
    class Meta:
        db_table = 'roles'
    
class password_storage(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE,related_name='user_id_repos',blank=True, null=True,db_column='user_id')
    passwordText =models.CharField(max_length=255,null=True,blank=True)
    
    class Meta:
        db_table = 'password_storage'

class error_log(models.Model):
    id = models.AutoField(primary_key=True)
    method =models.TextField(null=True,blank=True)
    error =models.TextField(null=True,blank=True)
    error_date = models.DateTimeField(null=True,blank=True,auto_now_add=True)
    user_id = models.TextField(null=True,blank=True)
    
    class Meta:
        db_table = 'error_log'

class common_model(models.Model):
    name = models.CharField(max_length=255)
    id1 =models.CharField(max_length=255)
    def __str__(self):
        return self.id1    

class SMSLog(models.Model):
    user = models.CharField(max_length=255, blank=True, null=True)  # store username
    mobile = models.CharField(max_length=15)
    message = models.TextField()
    content = models.TextField(blank=True)
    status = models.CharField(max_length=50, blank=True)
    unique_id = models.CharField(max_length=255, blank=True)
    content_type = models.CharField(max_length=50, blank=True)
    response_status = models.CharField(max_length=50, blank=True)
    response_uri = models.CharField(max_length=255, blank=True)
    status_description = models.TextField(blank=True)
    error_exception = models.TextField(blank=True)
    error_message = models.TextField(blank=True)

    # Additional text fields
    library_code = models.TextField(null=True, blank=True)
    membership_id = models.TextField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "sms_log"

class OTPMessage(models.Model):
    OTPText = models.TextField()
    OTPPurpose = models.CharField(max_length=255)
    OTPIDNumber = models.PositiveIntegerField(unique=True)

    class Meta:
        db_table = 'otp_messages'

    def __str__(self):
        return f"{self.OTPPurpose} - {self.OTPIDNumber}"
    
class SmsTemplate(models.Model):
    template_id = models.CharField(max_length=100, unique=True)
    template_name = models.CharField(max_length=255)
    template_message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.CharField(max_length=100)
    
    class Meta:
        db_table = 'sms_templates'
    
    def __str__(self):
        return self.template_name
    
class OTPLog(models.Model):
    username = models.CharField(max_length=255)  # or use email, based on your system
    otp = models.CharField(max_length=6)  # Store OTP
    is_verified = models.BooleanField(default=False)  # Whether OTP is verified or not
    created_by = models.TextField()  # Assuming the OTP is created by an admin
    created_at = models.DateTimeField(auto_now_add=True)  # Automatically add the timestamp when created

    class Meta:
        db_table = 'tbl_otp_log'
        
        
class VerifyOtp(models.Model):
    otp_log = models.ForeignKey(OTPLog, on_delete=models.CASCADE,null=True,blank=True,related_name='otp_log_verify')
    username = models.CharField(max_length=255)  # or use email, based on your system
    otp = models.CharField(max_length=6)  # Store OTP
    is_verified = models.BooleanField(default=False)  # Whether OTP is verified or not
    created_by = models.TextField()  # Assuming the OTP is created by an admin
    created_at = models.DateTimeField(auto_now_add=True)  # Automatically add the timestamp when created

    class Meta:
        db_table = 'tbl_verify_log'
        
class SessionActivityLog(models.Model):
    """
    Logs session binding and suspicious activity.
    No FK intentionally (audit table).
    """

    user_id = models.CharField(max_length=50, null=True, blank=True)
    user_type = models.CharField(
        max_length=20,
        choices=(('admin', 'Admin'), ('citizen', 'Citizen')),
        null=True,
        blank=True
    )

    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent_hash = models.CharField(max_length=256, null=True, blank=True)
    stored_user_agent_hash = models.CharField(max_length=256, null=True, blank=True)
    stored_ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    user_agent = models.TextField(null=True, blank=True)
    stored_user_agent = models.TextField(null=True, blank=True)

    action = models.CharField(max_length=100)  
    # examples:
    # session_created, session_verified, mismatch_detected, forced_logout

    remarks = models.TextField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'tbl_session_activity_log'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user_type} | {self.user_id} | {self.action}"
