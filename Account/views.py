import json
import random
import string
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, render,redirect
from django.contrib.auth import authenticate, login ,logout,get_user_model
from Account.forms import RegistrationForm
from Account.models import  CustomUser, password_storage
# import mysql.connector as sql
from Account.serializers import *
import Db 
import bcrypt
from L01.models import *
from django.contrib.auth.decorators import login_required
# from .models import SignUpModel
# from .forms import SignUpForm
from NLMS.encryption import *
from django.http import HttpResponse
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph
from Account.utils import decrypt_email, encrypt_email
import traceback
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.hashers import check_password
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.views.decorators.csrf import csrf_exempt
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.contrib.auth.backends import ModelBackend
from .db_utils import callproc
from django.utils import timezone
from Account.models import *
from Masters.models import *
from MenuManager.models import *
from django.db import IntegrityError
from django.urls import reverse
from django.http import HttpResponseBadRequest
import logging
import requests
from django.db import models
from administration.models import *
from django.views.decorators.csrf import csrf_protect
from datetime import date

# Set up logging
logger = logging.getLogger(__name__)

from django.contrib.auth.hashers import check_password
from django.contrib.auth import get_user_model
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.shortcuts import render, redirect

User = get_user_model()

from django.contrib.auth.models import update_last_login

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
            db_alias= enc(db_alias)
    
        encrypted_cat_ref_num= request.GET.get("cat_ref_num", "")
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

        return render(request, 'bootstrap/account/login.html', {
            'library_code': library_code,
            'registration_url': membership_url,
            'next': next_url,
            'cat': encrypted_cat_ref_num,
            'ebook_id': encrypted_ebook_id,
            'pdf_url': encrypted_pdf_url,
             'db_alias':db_alias
        })

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
        # cat_ref_num = encrypted_cat_ref_num if encrypted_cat_ref_num else None

        # ------------------------------------------
        # Database alias (static for L01)
        # ------------------------------------------
        
        # if library_code == 'default' or library_code is None and next_url == '':
        if ( library_code == 'default' or library_code is None ) and next_url == '':
            
            db_alias = library_code

            # ------------------------------------------
            # Authenticate user
            # ------------------------------------------
            user = authenticate_from_db(request, username, password, db_alias)
            if user is None:
                messages.error(request, 'Invalid Credentials')
                return redirect("Login")
            
            # ------------------------------------------
            # Set session user data
            # ------------------------------------------
            request.session.cycle_key()
            request.session["username"] = str(username)
            request.session["full_name"] = str(user.full_name)
            request.session["user_id"] = str(user.id)
            request.session["role_id"] = str(user.role_id)
            
            return redirect(f'LMS_Dashboard')
        
        else:
            
            print("Library code:", library_code)
            
            db_alias = "L01"
            request.session['service'] = db_alias
            request.session['library_db'] = db_alias

            # ------------------------------------------
            # Authenticate user
            # ------------------------------------------
            user = authenticate_from_db(request, username, password, db_alias)
            if user is None:
                messages.error(request, 'Invalid Credentials')
                return redirect("Login")

            # ------------------------------------------
            # Set session user data
            # ------------------------------------------
            request.session.cycle_key()
            request.session["username"] = str(username)
            request.session["full_name"] = str(user.full_name)
            request.session["user_id"] = str(user.id)
            request.session["role_id"] = str(user.role_id)

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
                    # file_url = settings.MEDIA_URL + pdf_url
                    # final_pdf_url = request.build_absolute_uri(file_url)

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
    
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()
        
        # Validate input
        if not username or not password:
            messages.error(request, 'Please provide both username and password.')
            return render(request, 'bootstrap/account/admin_login.html')
        
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
                                request.session['is_admin'] = True
                                request.session['username'] = str(user.username)
                                request.session['full_name'] = str(user.full_name)
                                request.session['user_id'] = str(user.id)
                                request.session['role_id'] = str(user.role_id)
                                request.session['last_login'] = user.last_login.isoformat() if user.last_login else ''
                                
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
    
    # REMOVE the problematic connection cleanup - it's causing issues
    # Just return the template
    return render(request, 'bootstrap/account/admin_login.html')

def logoutView(request):
    library_code = request.session.get('library_db', None)

    # Flush session
    request.session.flush()
    from django.contrib.auth import logout as django_logout
    django_logout(request)
    from django.shortcuts import redirect
    from django.contrib.auth.models import AnonymousUser
    # Ensure user is set to anonymous
    request.user = AnonymousUser()

    # Redirect based on whether library_code existed
    if library_code == 'default':
        return redirect("library_list")  
    else:
        return redirect("library_list")

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

def forgot_password(request):
    try:
        if request.method =="GET":
            type = request.GET.get('type')
            return render(request,'Account/forgot-password.html',{'type':type}) 
        if request.method == "POST":
            email = request.POST.get('email')
            if CustomUser.objects.filter(email=email).exists():
                messages.success(request, 'User id valid...Please update your password')
                type = 'pass'
            else:
                messages.error(request, 'User does not exist.Please Enter Correct Email.')
                type='email'
            return render(request,'Account/forgot-password.html',{'type':type,'email':email}) 

    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        fun = tb[0].name
        callproc("stp_error_log", [fun, str(e), request.user.id])
        messages.error(request, 'Oops...! Something went wrong!')

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
