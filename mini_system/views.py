
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from .models import IssuedBook, ExitScan, AlarmLog
from django.utils import timezone
import random
import string

# Helper functions
def generate_rfid():
    """Generate random RFID (10 hex characters)"""
    return ''.join(random.choices('0123456789ABCDEF', k=10))

def home(request):
    """Main simulation interface"""
    issued_books = IssuedBook.objects.filter(is_active=True)
    recent_scans = ExitScan.objects.all()[:10]
    
    # Statistics
    total_scans = ExitScan.objects.count()
    total_alarms = ExitScan.objects.filter(alarm_triggered=True).count()
    active_issued = issued_books.count()
    
    context = {
        'issued_books': issued_books,
        'recent_scans': recent_scans,
        'total_scans': total_scans,
        'total_alarms': total_alarms,
        'active_issued': active_issued,
    }
    return render(request, 'mini_system/home.html', context)

@csrf_exempt
def scan_rfid(request):
    """Simulate RFID scanning at exit gate"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            book_rfid = data.get('rfid', '').strip().upper()
            
            # If no RFID provided, generate one
            if not book_rfid:
                book_rfid = generate_rfid()
            
            # Check if book is issued
            try:
                issued_book = IssuedBook.objects.get(
                    book_rfid=book_rfid, 
                    is_active=True
                )
                
                # Book is properly issued
                is_authorized = True
                alarm_triggered = False
                message = f"✅ Book '{issued_book.book_title}' is properly issued to {issued_book.user_name}"
                book_title = issued_book.book_title
                user_name = issued_book.user_name
                
            except IssuedBook.DoesNotExist:
                # Book is NOT issued - ALARM!
                is_authorized = False
                alarm_triggered = True
                message = f"🚨 ALARM! Book with RFID {book_rfid} is not issued!"
                book_title = "Unknown"
                user_name = "Unknown"
                
                # Log the alarm
                AlarmLog.objects.create(
                    alarm_type='theft',
                    message=message
                )
            
            # Create scan record
            scan = ExitScan.objects.create(
                book_rfid=book_rfid,
                book_title=book_title,
                user_name=user_name,
                is_authorized=is_authorized,
                alarm_triggered=alarm_triggered,
                message=message
            )
            
            # Get recent scans
            recent_scans = ExitScan.objects.all()[:10]
            recent_data = [
                {
                    'book_rfid': s.book_rfid,
                    'book_title': s.book_title,
                    'status': 'Authorized' if s.is_authorized else 'Unauthorized',
                    'scan_time': s.scan_time.strftime("%H:%M:%S"),
                    'alarm_triggered': s.alarm_triggered,
                    'message': s.message
                }
                for s in recent_scans
            ]
            
            return JsonResponse({
                'success': True,
                'rfid': book_rfid,
                'is_authorized': is_authorized,
                'alarm_triggered': alarm_triggered,
                'message': message,
                'book_title': book_title,
                'user_name': user_name,
                'scan_time': scan.scan_time.strftime("%Y-%m-%d %H:%M:%S"),
                'recent_scans': recent_data,
                'stats': {
                    'total_scans': ExitScan.objects.count(),
                    'total_alarms': ExitScan.objects.filter(alarm_triggered=True).count(),
                    'active_issued': IssuedBook.objects.filter(is_active=True).count()
                }
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    
    return JsonResponse({'success': False, 'error': 'Invalid request'})

@csrf_exempt
def issue_book(request):
    """Issue a book in mini system"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            book_rfid = data.get('book_rfid', '').strip().upper()
            user_rfid = data.get('user_rfid', generate_rfid())
            user_name = data.get('user_name', 'Test User')
            book_title = data.get('book_title', 'Sample Book')
            
            # Generate RFID if not provided
            if not book_rfid:
                book_rfid = generate_rfid()
            
            # Check if already issued
            if IssuedBook.objects.filter(book_rfid=book_rfid, is_active=True).exists():
                return JsonResponse({
                    'success': False,
                    'message': f'Book {book_rfid} is already issued'
                })
            
            # Issue the book
            issued_book = IssuedBook.objects.create(
                book_rfid=book_rfid,
                user_rfid=user_rfid,
                user_name=user_name,
                book_title=book_title
            )
            
            return JsonResponse({
                'success': True,
                'message': f'✅ Book "{book_title}" issued successfully',
                'book_rfid': book_rfid,
                'user_name': user_name,
                'book_title': book_title
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    
    return JsonResponse({'success': False, 'error': 'Invalid request'})

@csrf_exempt
def return_book(request):
    """Return a book"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            book_rfid = data.get('book_rfid', '').strip().upper()
            
            if not book_rfid:
                return JsonResponse({
                    'success': False,
                    'message': 'RFID is required'
                })
            
            # Find and mark as returned
            try:
                issued_book = IssuedBook.objects.get(
                    book_rfid=book_rfid,
                    is_active=True
                )
                issued_book.is_active = False
                issued_book.save()
                
                return JsonResponse({
                    'success': True,
                    'message': f'Book "{issued_book.book_title}" returned successfully'
                })
                
            except IssuedBook.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'message': 'Book not found or not issued'
                })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    
    return JsonResponse({'success': False, 'error': 'Invalid request'})

def get_issued_books(request):
    """Get list of issued books"""
    issued_books = IssuedBook.objects.filter(is_active=True)
    
    data = [
        {
            'book_rfid': b.book_rfid,
            'user_rfid': b.user_rfid,
            'user_name': b.user_name,
            'book_title': b.book_title,
            'issue_time': b.issue_time.strftime("%Y-%m-%d %H:%M")
        }
        for b in issued_books
    ]
    
    return JsonResponse({
        'success': True,
        'books': data,
        'count': len(data)
    })

@csrf_exempt
def clear_data(request):
    """Clear all test data"""
    if request.method == 'POST':
        try:
            IssuedBook.objects.all().delete()
            ExitScan.objects.all().delete()
            AlarmLog.objects.all().delete()
            
            return JsonResponse({
                'success': True,
                'message': 'All data cleared successfully'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    
    return JsonResponse({'success': False, 'error': 'Invalid request'})

@csrf_exempt
def generate_test_data(request):
    """Generate test data"""
    if request.method == 'POST':
        try:
            # Create 5 test issued books
            for i in range(5):
                book_rfid = generate_rfid()
                user_rfid = generate_rfid()
                
                IssuedBook.objects.create(
                    book_rfid=book_rfid,
                    user_rfid=user_rfid,
                    user_name=f"Test User {i+1}",
                    book_title=f"Sample Book {i+1}"
                )
            
            return JsonResponse({
                'success': True,
                'message': 'Generated 5 test books'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    
    return JsonResponse({'success': False, 'error': 'Invalid request'})