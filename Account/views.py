# Standard library
import json
import random
import string
import traceback
import logging
import hashlib
from datetime import date, timedelta

# Django core
from django.http import HttpResponse, JsonResponse, HttpResponseBadRequest
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import (
    authenticate, login, logout, get_user_model
)
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import update_last_login
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.hashers import (
    make_password, check_password
)
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.urls import reverse
from django.utils import timezone
from django.db import models, IntegrityError

# Django REST Framework
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.tokens import RefreshToken

# Third-party
import bcrypt
import requests

# Project / App imports
from L01.views import send_sms
from L01.models import *
from Account.forms import RegistrationForm
from Account.models import CustomUser, password_storage
from Account.serializers import *
from Account.utils import encrypt_email, decrypt_email
from NLMS.encryption import *
from Masters.models import *
from MenuManager.models import *
from administration.models import *
from .db_utils import callproc
import Db

# PDF generation
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph

# User model
User = get_user_model()

# Logger
logger = logging.getLogger(__name__)

def safe_login(request, user, db_alias):
    # Temporarily override update_last_login to use correct DB
    original_save = user.save

    def save_with_db(*args, **kwargs):
        kwargs['using'] = db_alias
        return original_save(*args, **kwargs)

    user.save = save_with_db  # monkey patch

    login(request, user)

    user.save = original_save
    
def authenticate_from_db(request, username, password, db_alias):
    try:
        user = User.objects.using(db_alias).get(username=username)
    except User.DoesNotExist:
        return None
    
    if not user.is_active:
        return None

    if check_password(password, user.password):
        # Tell Django which backend authenticated this user
        user.backend = 'django.contrib.auth.backends.ModelBackend'
        safe_login(request, user, db_alias)
        return user
    
    return None

@csrf_exempt
def Login(request):
    """
    Member login view with session security and back button protection
    """
    
    # 🔴 ADD: Check for expired session from back button
    expired = request.GET.get('expired')
    if expired:
        request.session.flush()
        messages.warning(request, 'Your session has expired. Please login again.')
        return redirect('library_list')

    library_code = request.session.get('library_db', None)
    today = date.today()

    # ============================================================
    # GET METHOD
    # ============================================================
    if request.method == "GET":
       
        next_url = request.GET.get("next", "")
        db_alias = request.GET.get("db_alias")
        if not db_alias:
            db_alias = None
        else:
            db_alias = enc(db_alias)
    
        encrypted_cat_ref_num = request.GET.get("cat_ref_num", "")
        encrypted_ebook_id = request.GET.get("ebook_id")
        encrypted_pdf_url = request.GET.get("pdf_url")

        ebook_id = dec(encrypted_ebook_id) if encrypted_ebook_id else None
        pdf_url = dec(encrypted_pdf_url) if encrypted_pdf_url else None
        cat_ref_num = dec(encrypted_cat_ref_num) if encrypted_cat_ref_num else None

        library = LibraryMaster.objects.using('default').filter(
            is_active=1,
            library_code=library_code
        ).first()

        membership_url = library.membership_page_link.strip() if library and library.membership_page_link else "#"

        # 🔴 ADD: Create response with no-cache headers
        response = render(request, 'bootstrap/account/login.html', {
            'library_code': library_code,
            'registration_url': membership_url,
            'next': next_url,
            'cat': encrypted_cat_ref_num,
            'ebook_id': encrypted_ebook_id,
            'pdf_url': encrypted_pdf_url,
            'db_alias': db_alias
        })
        response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'
        return response

    # ============================================================
    # POST METHOD
    # ============================================================
    if request.method == "POST":

        username = request.POST.get('username')
        password = request.POST.get('password')
        remember_me = request.POST.get('remember_me')
        next_url = request.POST.get('next')
        
        encrypted_cat_ref_num = request.POST.get("cat")
        encrypted_ebook_id = request.POST.get("ebook_id")
        encrypted_pdf_url = request.POST.get("pdf_url")
        db_alias = request.POST.get("db_alias")
        
        if db_alias == 'None':
            db_alias = None
        else:
            library_code = dec(db_alias)

        ebook_id = dec(encrypted_ebook_id) if encrypted_ebook_id else None
        pdf_url = dec(encrypted_pdf_url) if encrypted_pdf_url else None

        # Remove the first if condition, keep only the else part logic
        
        params = {}

        if encrypted_cat_ref_num and encrypted_cat_ref_num.strip():
            params['cat_ref_num'] = encrypted_cat_ref_num.strip()

        if encrypted_ebook_id:
            params['ebook_id'] = encrypted_ebook_id

        if encrypted_pdf_url:
            params['pdf_url'] = encrypted_pdf_url
            
        print("Library code:", library_code)
        
        # Default to L01 if not specified
        if not db_alias or db_alias == 'None':
            db_alias = "L01"
            
        request.session['service'] = db_alias
        request.session['library_db'] = db_alias

        user = authenticate_from_db(request, username, password, db_alias)

        # 🔴 FIX: Check if user is None BEFORE accessing attributes
        if user is None:
            messages.error(request, 'Login unsuccessful. Please verify your credentials.')
            
            if next_url and next_url.strip():
                return redirect(f"{reverse('Login')}?next={next_url}")
            
            if params:
                from urllib.parse import urlencode2
                login_url = f"{reverse('Login')}?{urlencode(params)}"
                return redirect(login_url)
            
            return redirect("Login")

        # ------------------------------------------
        # Authenticate user - NOW user is guaranteed not to be None
        # ------------------------------------------
        if user.is_logged_in:

                # timeout = timedelta(seconds=settings.SESSION_COOKIE_AGE)
                timeout = timedelta(minutes=5)

                if user.last_activity and \
                timezone.now() - user.last_activity < timeout:

                    messages.error(
                        request,
                        'Login unsuccessful. You are already logged in on another device.'
                    )

                    return redirect("Login")

                else:
                    # expired session cleanup
                    user.is_logged_in = False
                    user.session_key = None
                    user.save()

        # import secrets
        # from django.contrib.auth import login as log
        # log(request, user)
        # token = secrets.token_hex(32)
        # request.session["login_token"] = token
        # user.session_key = token
        user.is_logged_in = True
        user.last_activity = timezone.now()
        user.save()

        # 🔒 ROLE GATE — ONLY MEMBERS ALLOWED
        if str(user.role_id) != '3':
            messages.error(
                request,
                'Access denied. This portal is available to registered members only.'
            )
            
            if next_url and next_url.strip():
                return redirect(f"{reverse('Login')}?next={next_url}")
            
            if params:
                from urllib.parse import urlencode
                login_url = f"{reverse('Login')}?{urlencode(params)}"
                return redirect(login_url)
            
            return redirect("Login")

        # ------------------------------------------
        # Set session user data
        # ------------------------------------------
        request.session.cycle_key()
        request.session["username"] = str(username)
        request.session["full_name"] = str(user.full_name)
        request.session["user_id"] = str(user.id)
        request.session["role_id"] = str(user.role_id)
        request.session['library_db'] = db_alias
        
        # 🔴 ADD: Session fingerprinting for security
        import hashlib
        ua = request.META.get('HTTP_USER_AGENT', '')
        request.session['_ua_hash'] = hashlib.sha256(ua.encode()).hexdigest()
        request.session['_ua_raw'] = ua
        request.session['_ip'] = get_client_ip(request)
        
        # 🔴 ADD: Set member flow completed flag for back button protection
        request.session['member_flow_completed'] = True
        request.session.modified = True

        # ------------------------------------------
        # Get membership info
        # ------------------------------------------
        member = MembershipDetails.objects.using(db_alias).filter(user_id=username).first()

        membership_id = None
        if member:
            try:
                membership = MembershipMaster.objects.using(db_alias).get(id=member.membership_id)
                membership_id = membership.id
            except MembershipMaster.DoesNotExist:
                membership_id = None
                
        if str(user.role_id) == '3' and member:
            try:
                login_session = MemberLoginSession.objects.using('L01').create(
                    member=member,   # ✅ pass MembershipDetails instance
                    ip_address=request.META.get('REMOTE_ADDR'),
                    created_by=str(user.id)
                )

                request.session['login_session_id'] = login_session.id

            except Exception as e:
                print(f"Error creating MemberLoginSession: {e}")
                
        # Inactive membership
        if member and member.isactive != 1:
            request.session["sweet_alert"] = {
                "title": "Membership Inactive",
                "text": "आपली सदस्यता सध्या सक्रिय नाही. कृपया प्रशासनाशी संपर्क साधा.",
                "icon": "warning"
            }
            request.session.set_expiry(0)
            return redirect("L01:membership_dashboard")

        # Membership expired
        if member and today > member.to_date:
            request.session["sweet_alert"] = {
                "title": "Membership Expired",
                "text": "आपली सदस्यता संपलेली आहे. कृपया नूतनीकरण करा.",
                "icon": "warning"
            }
            request.session.set_expiry(0)
            return redirect("L01:membership_dashboard")

        # Membership not started yet
        if member and today < member.from_date:
            request.session["sweet_alert"] = {
                "title": "Membership Not Active Yet",
                "text": "आपली सदस्यता अद्याप सुरू झालेली नाही.",
                "icon": "info"
            }
            request.session.set_expiry(0)
            return redirect("L01:membership_dashboard")
            
        if membership_id == 8:

            # Clear any previous pending action
            request.session.pop("pending_action", None)

            if next_url:
                request.session["pending_action"] = {
                    "type": "next_url",
                    "url": next_url,
                    "message": "कृपया आपले पुस्तक उघडण्यासाठी पुढे जा."
                }

                request.session.set_expiry(0)
                return redirect("L01:membership_dashboard")
                
            if ebook_id and pdf_url or encrypted_cat_ref_num:
                request.session["sweet_alert"] = {
                    "title": "Access Restricted",
                    "text": "हे पुस्तक अभ्यासिका शाखेसाठी उपलब्ध नाही.",
                    "icon": "warning"
                }

                request.session.set_expiry(0)
                return redirect("L01:membership_dashboard") 

            return redirect("L01:membership_dashboard")

        # ============================================================
        # VALID MEMBERSHIP (NOT PRACTITIONER)
        # ============================================================
        if membership_id is not None and membership_id != 8:

            # Clear any previous pending action
            request.session.pop("pending_action", None)
            if next_url:
                request.session["sweet_alert"] = {
                    "title": "Access Restricted",
                    "text": "हे पुस्तक उघडण्यासाठी अभ्यासिका शाखेत नोंदणी करा.",
                    "icon": "warning"
                }

                request.session.set_expiry(0)
                return redirect("L01:membership_dashboard")

            # Ebook + PDF intent
            elif ebook_id and encrypted_pdf_url:
                request.session["pending_action"] = {
                    "type": "pdf",
                    "url": encrypted_pdf_url,
                    "message": "कृपया आपले ई-बुक उघडण्यासाठी पुढे जा."
                }

            # Catalog detail intent
            elif encrypted_cat_ref_num:
                request.session["pending_action"] = {
                    "type": "catalog",
                    "url": f"/{library_code}/view_book_detail/?cat_ref_num={encrypted_cat_ref_num}",
                    "message": "कृपया आपले पुस्तक उघडण्यासाठी पुढे जा."
                }

            request.session.set_expiry(0)
            return redirect("L01:membership_dashboard")

        # ============================================================
        # NO MEMBERSHIP FOUND
        # ============================================================
        if membership_id is None:
            request.session.set_expiry(0)
            return redirect('L01:dashboard')

        # ============================================================
        # Role fallback
        # ============================================================
        if str(user.role_id) == '3':
            return redirect('L01:membership_dashboard')

        return redirect('L01:dashboard')

    else:
        messages.error(request, 'Invalid Credentials')
        return redirect("Login")

from django.db import connections
from django.db.utils import ConnectionDoesNotExist

@csrf_protect
def adminLogin(request):
    """
    Administrative login view for library administrators
    Uses password_storage table for authentication
    Only allows users with role_id = 1 (Admin) to login
    """
    # IMPORTANT: Clear problematic session keys FIRST THING
    # This must be the very first operation
    if 'library_db' in request.session:
        del request.session['library_db']
    if 'using_database' in request.session:
        del request.session['using_database']
    
    # Clear ALL library-related session data
    keys_to_delete = []
    for key in request.session.keys():
        key_lower = key.lower()
        if any(term in key_lower for term in ['library', 'db', 'branch', 'l0', 'l1', 'l2', 'l3']):
            keys_to_delete.append(key)
    
    for key in keys_to_delete:
        del request.session[key]
    
    # Force session save immediately
    request.session.save()
    
    # If user is already authenticated, redirect to admin dashboard
    if request.user.is_authenticated and request.user.is_staff:
        return redirect('LMS_Dashboard')
    
    # 🔴 ADD: Check for expired session from back button
    expired = request.GET.get('expired')
    if expired:
        request.session.flush()
        messages.warning(request, 'Your session has expired. Please login again.')
        return redirect('library_list')
    
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()
        
        # Validate input
        if not username or not password:
            messages.error(request, 'Please provide both username and password.')
            # Add no-cache headers to error response too
            response = render(request, 'bootstrap/account/admin_login.html')
            response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'
            return response
        
        try:
            User = get_user_model()
            
            try:
                # Find user in default database
                user = User.objects.using('default').get(username=username)
                
                # Check password_storage table
                try:
                    from .models import password_storage
                    pwd_storage = password_storage.objects.using('default').get(user=user)
                    
                    # Verify password from storage
                    if pwd_storage.passwordText == password:
                        # Check admin privileges
                        if user.is_staff or user.is_superuser:
                            # Check if user has role_id = 1 (Admin role)
                            if hasattr(user, 'role_id') and user.role_id == 1:
                                # Login user
                                user.backend = 'django.contrib.auth.backends.ModelBackend'
                                login(request, user)
                                
                                # Set session variables - ONLY default database
                                request.session['using_database'] = 'default'
                                request.session['library_db'] = 'default'
                                request.session['is_admin'] = True  # 🔴 SET THIS FLAG
                                request.session['username'] = str(user.username)
                                request.session['full_name'] = str(user.full_name)
                                request.session['user_id'] = str(user.id)
                                request.session['role_id'] = str(user.role_id)
                                request.session['last_login'] = user.last_login.isoformat() if user.last_login else ''
                                
                                # 🔐 Fingerprinting
                                ua = request.META.get('HTTP_USER_AGENT', '')
                                request.session['_ua_hash'] = hashlib.sha256(ua.encode()).hexdigest()
                                request.session['_ua_raw'] = ua
                                request.session['_ip'] = get_client_ip(request)
                                
                                # 🔴 ALSO set admin_flow_completed for consistency
                                request.session['admin_flow_completed'] = True
                                request.session.modified = True  # Ensure it's saved
                                
                                # Update last_login timestamp
                                user.last_login = timezone.now()
                                user.save(update_fields=['last_login'])
                                
                                messages.success(request, f'Administrative login successful! Welcome, {user.full_name or user.username}.')
                                return redirect('LMS_Dashboard')
                            else:
                                messages.error(request, 'Access denied. This login is for administrators only.')
                        else:
                            messages.error(request, 'Access denied. This login is for administrative staff only.')
                    else:
                        messages.error(request, 'Invalid username or password.')
                        
                except password_storage.DoesNotExist:
                    messages.error(request, 'Password not configured. Please contact system administrator.')
                    
            except User.DoesNotExist:
                messages.error(request, 'Invalid username or password.')
                
        except Exception as e:
            messages.error(request, 'An error occurred during login. Please try again.')
            # Log the error properly in production
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Admin login error for user '{username}': {str(e)}", exc_info=True)
    
    # 🔴 ADD no-cache headers to ALL responses
    response = render(request, 'bootstrap/account/admin_login.html')
    response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response

def get_client_ip(request):
    """
    Returns the real client IP.
    Works correctly behind proxies / load balancers.
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')

@csrf_protect
def librarianLogin(request):
    """
    Librarian staff login view.
    Prevents session fixation & basic hijacking.
    """

    # 🔴 ADD THIS AT THE BEGINNING: Check if user is already authenticated
    # This handles direct URL access while logged in
    
    library_code = request.session.get('library_db')  # Default to L01
    
    if request.user.is_authenticated:
        # Redirect to appropriate dashboard based on library_code
        from django.urls import reverse
        return redirect(f'{library_code}:dashboard')
       
    
    # 🔴 ADD THIS: Check for expired session from back button
    expired = request.GET.get('expired')
    if expired:
        # Clear session completely when coming from expired redirect
        request.session.flush()
        messages.warning(request, 'Your session has expired. Please login again.')
        return redirect('library_list')

    library_code = request.session.get('library_db')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()

        if not username or not password:
            messages.error(request, 'Login unsuccessful. Please verify your credentials.')
            return render(request, 'bootstrap/account/librarian_login.html')

        try:

            user = authenticate(request, username=username, password=password)

            if user and getattr(user, 'role_id', None) != 3:
                
                login(request, user)  # Django creates fresh session here

                # ✅ App-specific session data
                request.session['using_database'] = library_code
                request.session['is_librarian'] = True
                request.session['username'] = user.username
                request.session['full_name'] = getattr(user, 'full_name', user.username)
                request.session['user_id'] = user.id
                request.session['role_id'] = user.role_id
                request.session['last_login'] = (
                    user.last_login.isoformat() if user.last_login else ''
                )

                # 🔐 Fingerprinting
                ua = request.META.get('HTTP_USER_AGENT', '')
                request.session['_ua_hash'] = hashlib.sha256(ua.encode()).hexdigest()
                request.session['_ua_raw'] = ua
                request.session['_ip'] = get_client_ip(request)

                # 🧹 Cleanup flags
                request.session.pop('_session_expired', None)
                request.session.pop('_user_logged_out', None)
                
                # 🔴 CRITICAL: Set this flag exactly as in your working OTP project
                request.session['admin_flow_completed'] = True
                # Also set session modified to ensure it's saved
                request.session.modified = True
                
                return redirect(f'{library_code}:dashboard')
                

            # Generic failure (VAPT-friendly)
            messages.error(
                request,
                'Login unsuccessful. Invalid credentials or insufficient access rights.'
            )

        except Exception:
            logger.exception("Librarian login error for username '%s'", username)
            messages.error(
                request,
                'Login could not be completed at this time. Please try again later.'
            )

    # 🔴 ADD THIS: Create response with no-cache headers
    response = render(request, 'bootstrap/account/librarian_login.html')
    response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    
    return response

def logoutView(request):
    """
    Universal logout view that handles both Admin and Librarian logout
    """
    try:
        # Determine user type and redirect URL BEFORE clearing session
        is_admin = request.session.get('is_admin', False)
        is_librarian = request.session.get('is_librarian', False)
        
        # Set appropriate redirect URL based on user type
        if is_admin:
            redirect_url = reverse('library_list')  # Redirect to admin login
        elif is_librarian:
            redirect_url = reverse('library_list')  # Redirect to library selection
        else:
            # Default fallback
            redirect_url = reverse('library_list')
        
        # 1️⃣ Clear ALL authentication flags (CRITICAL for middleware)
        flags_to_clear = [
            'admin_flow_completed',  # Librarian flag
            'is_admin',              # Admin flag
            'is_librarian',          # Librarian flag
        ]
        
        for flag in flags_to_clear:
            request.session.pop(flag, None)
        
        # 2️⃣ Update user status if authenticated
        if request.user.is_authenticated:
            user = request.user
            if hasattr(user, 'is_logged_in'):
                user.is_logged_in = False
            if hasattr(user, 'session_key'):
                user.session_key = None
            
            # Save only if we modified fields
            update_fields = []
            if hasattr(user, 'is_logged_in') and user.is_logged_in is False:
                update_fields.append('is_logged_in')
            if hasattr(user, 'session_key') and user.session_key is None:
                update_fields.append('session_key')
            
            if update_fields:
                user.save(update_fields=update_fields)
        
        # 3️⃣ Clear ALL session keys
        session_keys_to_clear = [
            # Auth flags
            'admin_flow_completed', 'is_admin', 'is_librarian',
            
            # User data
            'using_database', 'library_db', 'username', 'full_name',
            'user_id', 'role_id', 'last_login',
            
            # Fingerprinting
            '_ua_hash', '_ua_raw', '_ip',
            
            # Status flags
            '_session_expired', '_user_logged_out'
        ]
        
        # Also clear any keys that start with specific patterns
        all_keys = list(request.session.keys())
        for key in all_keys:
            # Clear any remaining auth/session keys
            if key not in session_keys_to_clear:
                if any(term in key.lower() for term in ['auth', 'login', 'session', 'user']):
                    request.session.pop(key, None)
        
        for key in session_keys_to_clear:
            request.session.pop(key, None)
        
        # 4️⃣ Django logout (clears authentication)
        from django.contrib.auth import logout as django_logout
        django_logout(request)
        
        # 5️⃣ Mark session as modified
        request.session.modified = True
        
        # 6️⃣ Flush entire session
        request.session.flush()
        
        # 7️⃣ Add logout flag to new session
        request.session['_user_logged_out'] = True
        
        # 8️⃣ Add cache-busting parameter
        import time
        final_redirect_url = f"{redirect_url}?_={int(time.time())}"
        
        # Optional: Add success message
        messages.success(request, "You have been logged out successfully.")
        
        return redirect(final_redirect_url)
        
    except Exception as e:
        # Log error but still redirect
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Logout error: {e}")
        
        # Fallback redirect to library list
        return redirect('library_list')

def register_new_user(request):
    Db.closeConnection()
    m = Db.get_connection()
    cursor=m.cursor()
    if request.method=="GET":
        id = request.GET.get('id', '')
        cursor.callproc("stp_get_dropdown_values",['roles'])
        for result in cursor.stored_results():
            roles = list(result.fetchall())
        
        cursor.callproc("stp_get_dropdown_values",['category'])
        for result in cursor.stored_results():
            category = list(result.fetchall())
            
        cursor.callproc("stp_get_dropdown_values",['moduleL'])
        for result in cursor.stored_results():
            moduleL = list(result.fetchall())

        if id != '0':
            id1 = dec(id)
            users = get_object_or_404(CustomUser, id=id1)
            full_name = users.full_name.split(" ", 1) 
            first_name = full_name[0] 
            last_name = full_name[1] if len(full_name) > 1 else ""  


            context = {'users':users,'first_name':first_name,'last_name':last_name,'roles':roles,'category':category,"edit_mode": True,"moduleL":moduleL,}
           
        else:

            context = {'id':id,'roles': roles,'category':category,"moduleL":moduleL,}


    if request.method == "POST":
        id = request.POST.get('id', '')
        try:  
            if id == '0':
               # Extract data from the request
                
                firstname = request.POST.get('firstname')
                lastname = request.POST.get('lastname')
                email = request.POST.get('email')
                password = request.POST.get('password') 
                phone = request.POST.get('mobileNumber')
                role_id = request.POST.get('role_id')
                
                # category_raw = request.POST.getlist('customCategoryDropdown[]')
                # file_category = category_raw.split(',') if category_raw else []
                
                file_category_str = request.POST.getlist('customCategoryDropdown[]')
                file_category = ",".join(file_category_str)
                
                client_module_str = request.POST.getlist('clientModDropdown[]')
                module = ",".join(client_module_str)


                
                full_name = f"{firstname} {lastname}"

                user = CustomUser(
                    full_name=full_name, email=email, phone=phone,
                    role_id=role_id,file_category=file_category,module=module,
                )
                user.username = user.email
                user.is_active = True 
                try:
                    validate_password(password, user=user)
                    user.set_password(password)
                    user.save()
                    password_storage.objects.create(user=user, passwordText=password)
                    assigned_menus = RoleMenuMaster.objects.filter(role_id=role_id)

                # Insert assigned menus into userMenuMaster1
                    for menu in assigned_menus:
                        UserMenuDetails.objects.create(
                            user_id=user.id,
                            menu_id=menu.menu_id,
                            role_id=role_id
                    )

                    messages.success(request, "User registered successfully!")

                except ValidationError as e:
                    messages.error(request, ' '.join(e.messages))
                    
            else:
                firstname = request.POST.get('firstname')
                lastname = request.POST.get('lastname')
                email = request.POST.get('email')
                full_name = f"{firstname} {lastname}"
                phone = request.POST.get('mobileNumber')
                role_id = request.POST.get('role_id')
                
                file_category_str = request.POST.getlist('customCategoryDropdown[]')
                file_category = ",".join(file_category_str)
                
                client_module_str = request.POST.getlist('clientModDropdown[]')
                module = ",".join(client_module_str)
                
                user = CustomUser.objects.get(id=id)
                user.full_name = full_name
                user.email = email
                user.phone = phone
                user.role_id = role_id
                
                user.file_category = file_category 
                user.module = module  
                user.save()

                UserMenuDetails.objects.filter(user_id=user.id).delete()

                # Fetch the menus for the new role
                assigned_menus = RoleMenuMaster.objects.filter(role_id=role_id)

                # Assign the new menus to the user
                for menu in assigned_menus:
                    UserMenuDetails.objects.create(
                        user_id=user.id,
                        menu_id=menu.menu_id,
                        role_id=role_id
                    )

                messages.success(request, "User details updated successfully!")

        except Exception as e:
            tb = traceback.extract_tb(e.__traceback__)
            fun = tb[0].name
            cursor.callproc("stp_error_log",[fun,str(e),request.user.id])  
            print(f"error: {e}")
            messages.error(request, 'Oops...! Something went wrong!')
            response = {'result': 'fail','messages ':'something went wrong !'}   

    if request.method=="GET":
        return render(request,'Account/register_new_user.html',context)
    elif request.method == "POST":
        return redirect('/masters?entity=user&type=i')  

def home(request):
    return render(request,'Account/home.html') 

@login_required
def search(request):
    results = []
    try:
        query = request.GET.get('q')
        if query != "":
           results = callproc("stp_get_application_search",[query])        
    except Exception as e:
        print("error-"+e)
    finally:
        return render(request, 'Bootstrap/search_results.html', {'query': query, 'results': results})

@login_required       
def change_password(request):
    try:
        if request.method == "POST":
            password = request.POST.get('password')  # The password entered by the user
            username = request.session.get('username', '')  # The username from the session
            user = CustomUser.objects.get(email=username)
            if check_password(password, user.password):
                status = "1"
            else:
                status = "0" 

    except Exception as e:
            tb = traceback.extract_tb(e.__traceback__)
            fun = tb[0].name
            callproc("stp_error_log",[fun,str(e),request.user.id])  
            print(f"error: {e}")
            messages.error(request, 'Oops...! Something went wrong!')
            response = {'result': 'fail','messages ':'something went wrong !'}
    finally:
        if request.method == "GET":
            return render(request,'Account/change_password.html')
        else:
           return JsonResponse({'status': status})
        
@login_required
def reset_password(request):
    try:
        email = request.POST.get('email')
        if not email:
            email = request.session.get('username', '')
        password = request.POST.get('password')
        user = CustomUser.objects.get(email=email)
        # Update password
        user.set_password(password)
        user.save()
        messages.success(request, 'Password has been successfully updated.')

    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        fun = tb[0].name
        callproc("stp_error_log", [fun, str(e), request.user.id])
        messages.error(request, 'Oops...! Something went wrong!')
    
    finally:
        return redirect( f'change_password')
    
@login_required    
def forget_password_change(request):
    try:
        email = request.POST.get('email')
        password = request.POST.get('password')
        user = CustomUser.objects.get(email=email)
        user.set_password(password)
        user.save()
        messages.success(request, 'Password has been successfully updated.')

    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        fun = tb[0].name
        callproc("stp_error_log", [fun, str(e), request.user.id])
        messages.error(request, 'Oops...! Something went wrong!')
    
    finally:
        return redirect( f'Login')
        
def dashboard(request):
    return render(request,'Bootstrap/index.html') 

def buttons(request):
    return render(request,'Bootstrap/buttons.html') 

def cards(request):
    return render(request,'Bootstrap/cards.html') 

def utilities_color(request):
    return render(request,'Bootstrap/utilities-color.html') 

def utilities_border(request):
    return render(request,'Bootstrap/utilities-border.html') 

def utilities_animation(request):
    return render(request,'Bootstrap/utilities-animation.html') 

def utilities_other(request):
    return render(request,'Bootstrap/utilities-other.html') 

def error_page(request):
    return render(request,'Bootstrap/404.html')

def blank(request):
    return render(request,'Bootstrap/blank.html')

def charts(request):
    return render(request,'Bootstrap/charts.html')

def tables(request):
    return render(request,'Bootstrap/tables.html')

def forgot_password(request, member):
    Db.closeConnection()
    m = Db.get_connection()
    cursor = m.cursor()
    try:
        if request.method == 'POST':
            username = request.POST.get('username')
            try:
                user = CustomUser.objects.get(username=username)
                # Role checks
                if int(member) == 1 and user.role_id != 3:
                    return JsonResponse({"status": "invalid_role", "message": "You are not a valid library member"})
                elif int(member) != 1 and user.role_id == 3:
                    return JsonResponse({"status": "invalid_role", "message": "Library members cannot reset password here"})

                mobile_no = user.phone
                otp = random.randint(100000, 999999)
                template = SmsTemplate.objects.using('L01').filter(template_id=1107176880362727316).first()

                if template:
                    message = template.template_message.replace('{#var#}', user.username)
                    message = message.replace('@OTP', str(otp))
                    request.session['otp'] = otp
                    send_sms(mobile_no, message)

                    otp_log = OTPLog.objects.using('L01').create(
                        username=username,
                        otp=str(otp),
                        is_verified=False,
                        created_by=request.user
                    )
                    otp_id = otp_log.id

                    verify_log = VerifyOtp.objects.using('L01').create(
                        otp_log=otp_log,
                        username=username,
                        otp=str(otp),
                        is_verified=False,
                        created_by=request.user
                    )

                    return JsonResponse({'status': 'otp_sent','username': username,'otp_id':otp_id,'member': member })
                else:
                    return JsonResponse({'status': 'template_not_found'}, status=400)

            except CustomUser.DoesNotExist:
                return JsonResponse({'status': 'user_not_found'}, status=400)

        else:
            return render(request, 'bootstrap/account/forgot_password.html', {'member': member})

    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        fun = tb[0].name if tb else 'library_list'
        cursor.callproc("stp_error_log", [fun, str(e), ''])
        print(f"error: {e}")
        if request.method == 'POST':
            return JsonResponse({'status': 'error', 'message': 'Oops...! Something went wrong!'}, status=500)
        else:
            messages.error(request, 'Oops...! Something went wrong!')
            return render(request, 'bootstrap/account/forgot_password.html', {'member': member})
        
def update_password(request):
    if request.method == "POST":
        username = request.POST.get("username")
        new_password = request.POST.get("new_password")
        if not username or not new_password:
            return JsonResponse({
                "status": "error",
                "message": "Missing data"
            }, status=400)

        try:
            user = CustomUser.objects.get(username=username)
        except CustomUser.DoesNotExist:
            return JsonResponse({
                "status": "error",
                "message": "User not found"
            }, status=404)

        # ✅ update encrypted password
        user.password = make_password(new_password)
        user.save()

        # ✅ store raw password separately
        password_storage.objects.using('L01').filter(user=user).update(
            passwordText=new_password
        )

        mobile_no = user.phone

        template = SmsTemplate.objects.using('L01').filter(
            template_id=1107176880391914288
        ).first()

        if template:
            message = template.template_message
            message = message.replace('{#var#}', user.full_name, 1)
            message = message.replace(
                '{#var#}',
                f"{user.username} and {new_password}",
                1
            )

            send_sms(mobile_no, message)

        return JsonResponse({
            "status": "success",
            "message": "Password updated successfully"
        })
    
def verify_otp(request):
    if request.method == "POST":

        verify_id = request.POST.get("otp_id")
        entered_otp = request.POST.get("otp")

        try:
            verify_row = VerifyOtp.objects.using('L01').get(
                otp_log=verify_id
            )
        except Exception as e:
            return JsonResponse({
                "status": "error",
                "message": "Invalid or expired OTP"
            })

        otp_log = verify_row.otp_log

        # expiry check
        if timezone.now() > otp_log.created_at + timedelta(minutes=2):
            verify_row.delete()
            return JsonResponse({
                "status": "expired",
                "message": "OTP expired"
            })

        # OTP mismatch
        if entered_otp != verify_row.otp:
            return JsonResponse({
                "status": "invalid",
                "message": "Invalid OTP"
            })

        # ✅ SUCCESS
        otp_log.is_verified = True
        otp_log.save()

        # delete verify row
        verify_row.delete()

        return JsonResponse({
            "status": "otp_verified",
            "message": "OTP verified successfully"
        })