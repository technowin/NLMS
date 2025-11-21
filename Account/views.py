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

    if check_password(password, user.password):
        # Tell Django which backend authenticated this user
        user.backend = 'django.contrib.auth.backends.ModelBackend'
        safe_login(request, user, db_alias)
        return user
    
    return None

@csrf_exempt
def Login(request):

    if request.method == "GET":

        next_url = request.GET.get("next", "")

        library_code = request.session.get('library_db', None) 
        library = LibraryMaster.objects.using('default').filter(
            is_active=1, 
            library_code=library_code
        ).first()

        membership_url = library.membership_page_link.strip() if library and library.membership_page_link else "#"

        return render(request, 'bootstrap/account/login.html', {
            'library_code': library_code,
            'registration_url': membership_url,
            'next': next_url,
        })

    if request.method == "POST":

        username = request.POST.get('username')
        password = request.POST.get('password')
        remember_me = request.POST.get('remember_me')
        next_url = request.POST.get("next")
        db_alias = None

        if next_url:
            request.session['service'] = "L01"
            request.session['library_db'] = "L01"
            db_alias = "L01"
        else:
            request.session['service'] = "default"
            db_alias = "default"
            request.session['library_db'] = "default"

        # Authenticate user
        user = authenticate_from_db(request, username, password, db_alias)

        if user is not None:

            request.session.cycle_key()
            request.session["username"] = str(username)
            request.session["full_name"] = str(user.full_name)
            request.session["user_id"] = str(user.id)
            request.session["role_id"] = str(user.role_id)

            # --------------------------------------------------------
            # GET USER'S MEMBERSHIP ID
            # --------------------------------------------------------
            member = None
            membership = None
            if db_alias != 'default':
                member = MembershipDetails.objects.using(db_alias).filter(user_id=username).first()
                if member:
                    membership = MembershipMaster.objects.using(db_alias).get(id=member.membership_id)

            membership_id = None
            if member:
                membership_id = membership.id

            # --------------------------------------------------------
            # membership_id == 8 → give access
            # --------------------------------------------------------
            if membership_id == 8:
                if next_url:
                    return redirect(next_url)
                else:
                    # UPSC (L01)
                    if db_alias == "L01":
                        return redirect('L01:chapters_index', topic_id=1)

                    # MPSC (default)
                    if db_alias == "default":
                        return redirect('L01:mpsc_chapters_index', topic_id=1)

            else:
                # --------------------------------------------------------
                # NORMAL USERS (membership_id != 8)
                # --------------------------------------------------------
                request.session.set_expiry(0)
                return redirect('LMS_Dashboard')

        else:
            messages.error(request, 'Invalid Credentials')
            return redirect("Login")



        
# def logoutView(request):
#     logout(request)
#     return redirect("Account")  

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
        return redirect("Account")  
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
