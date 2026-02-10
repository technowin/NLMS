from django.db import models
from django.utils import timezone

class IssuedBook(models.Model):
    """Books issued in the mini system"""
    book_rfid = models.CharField(max_length=50, unique=True, primary_key=True)
    user_rfid = models.CharField(max_length=50)
    user_name = models.CharField(max_length=100, default="Test User")
    book_title = models.CharField(max_length=200, default="Test Book")
    issue_time = models.DateTimeField(default=timezone.now)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-issue_time']
    
    def __str__(self):
        return f"{self.book_title} ({self.book_rfid})"
    class Meta:
        db_table = "tbl_issued_book"

class ExitScan(models.Model):
    """Records of books scanned at exit gate"""
    book_rfid = models.CharField(max_length=50)
    book_title = models.CharField(max_length=200, blank=True)
    user_name = models.CharField(max_length=100, blank=True)
    scan_time = models.DateTimeField(default=timezone.now)
    is_authorized = models.BooleanField(default=False)
    alarm_triggered = models.BooleanField(default=False)
    message = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-scan_time']
    
    def __str__(self):
        status = "Authorized" if self.is_authorized else "Unauthorized"
        return f"{self.book_rfid} - {status} - {self.scan_time}"
    
    class Meta:
        db_table = "tbl_exit_scan"

class AlarmLog(models.Model):
    """Records of alarm triggers"""
    ALARM_TYPES = [
        ('theft', 'Theft Attempt'),
        ('test', 'Test Alarm'),
        ('system', 'System Error'),
    ]
    
    alarm_type = models.CharField(max_length=20, choices=ALARM_TYPES)
    message = models.TextField()
    triggered_at = models.DateTimeField(default=timezone.now)
    resolved = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-triggered_at']
    
    def __str__(self):
        return f"{self.get_alarm_type_display()} - {self.triggered_at}"
    
    class Meta:
        db_table = "tbl_alarm_log"