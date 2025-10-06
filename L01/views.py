# L01/views.py
from django.http import HttpResponse
from L01.models import *
from administration.models import *
from django.conf import settings
import traceback
from django.contrib import messages
import Db
import requests
from django.http import HttpResponse, JsonResponse
from NLMS.encryption import *
from Account.db_utils import callproc
import re
from django.shortcuts import render, redirect
from django.db import transaction
import os
from django.http import HttpResponse, JsonResponse
from NLMS.encryption import *
import re
import json
from django.utils import timezone
import datetime
import uuid
from django.contrib.auth.hashers import make_password
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404
from django.http import Http404, FileResponse
from pathlib import Path
from django.core.files.storage import default_storage
import logging
from django.template.loader import render_to_string
from xhtml2pdf import pisa
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
import pathlib
from reportlab.platypus import Table, TableStyle
from reportlab.lib import colors
from io import BytesIO
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from datetime import datetime
from django.http import JsonResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404
import barcode
from barcode.writer import ImageWriter
from io import BytesIO
import base64

logger = logging.getLogger(__name__)

# Part First While Filling Membership Form

def index(request):
    # Get the library code from session
    library_code = request.session.get('library_db', None)

    if library_code:
        library_details = LibraryMaster.objects.using('default').filter(is_active=1, library_code=library_code)
        for lilo in library_details:
            encrypted_library_code = enc(lilo.library_code)
            lilo.libraries = encrypted_library_code
        library_name = library_details.first().library_name if library_details.exists() else ""
    else:
        library_details = LibraryMaster.objects.using('default').filter(is_active=1)
        library_name = ""

    # Pass to template
    return render(request, "L01/index.html", {
        'libraries': library_details,
        'library_name': library_name,
        'MEDIA_URL': settings.MEDIA_URL
    })

def check_user_id(request):
    Db.closeConnection()
    m = Db.get_connection()
    cursor = m.cursor()
    try:
       user_id = request.GET.get("user_id", "").strip()
       exists = MembershipDetails.objects.filter(user_id=user_id).exists()
       return JsonResponse({"exists": exists})
    except Exception as e:
            tb = traceback.extract_tb(e.__traceback__)
            fun = tb[0].name if tb else 'library_list'
            cursor.callproc("stp_error_log", [fun, str(e), ''])
            print(f"error: {e}")
            messages.error(request, 'Oops...! Something went wrong!')

def check_aadhar(request):
    Db.closeConnection()
    m = Db.get_connection()
    cursor = m.cursor()
    try:
        aadhar_no = request.GET.get("aadhar_number", "").strip()

        # Aadhar number format validation (12 digits)
        if not re.match(r'^\d{12}$', aadhar_no):
            return JsonResponse({"exists": False, "error": "Invalid Aadhar format (must be 12 digits)."})

        # Check if Aadhar already exists in the database
        exists = MembershipDetails.objects.filter(aadhar_no=aadhar_no).exists()

        return JsonResponse({"exists": exists})

    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        fun = tb[0].name if tb else 'check_aadhar'
        cursor.callproc("stp_error_log", [fun, str(e), ''])
        print(f"error: {e}")
        return JsonResponse({"error": "Oops... Something went wrong!"}, status=500)

def get_pincodes(request):
    wardname = request.GET.get("wardname")
    pincodes = []
    if wardname:
        try:
            ward = WardMaster.objects.using('default').get(ward_name=wardname, is_active=1)
            if ward.pincode:
                pincodes = ward.pincode.split(",")  # split comma-separated
                pincodes = [p.strip() for p in pincodes]  # remove extra spaces
        except WardMaster.DoesNotExist:
            pass
    return JsonResponse({"pincodes": pincodes})

def get_membership_details(request):
    if request.method == "GET":
        enc_id = request.GET.get("id")
        try:
            membership_id = enc_id  # decrypt back to int
            membership = MembershipMaster.objects.get(id=membership_id, isactive=1)
            data = {
                "deposit": str(membership.deposit),
                "entry_fees": str(membership.entry_fees),
                "subscription_fees": str(membership.subscription_fees),
            }
            return JsonResponse({"success": True, "data": data})
        except MembershipMaster.DoesNotExist:
            return JsonResponse({"success": False, "error": "Membership not found"})

# membership form filled by member first time registeration

def registration(request):
    Db.closeConnection()
    m = Db.get_connection()
    cursor = m.cursor()
    try:
        library_code = request.session.get('library_db', None)

        if request.method == "GET":
            
            formfilledsuccessfullyVariable = request.GET.get("formfilledsuccessfully", None)
            
            # you will get throgh post function formfilledsuccessfullyVariable encrypted value
            # decrypt it here
            if formfilledsuccessfullyVariable != None:
                
                formfilledsuccessfullyDecrypted = dec(formfilledsuccessfullyVariable)
                
                template = "L01/FormFilledSuccessfully.html"
                context = {'MEDIA_URL': settings.MEDIA_URL,
                           "library_code": request.session.get("library_db"),
                        }
                
            else:
                if library_code:
                    library_details = tbl_librarymasterL01.objects.filter(is_active=1, library_code=library_code)
                    for lilo in library_details:
                        encrypted_library_code = enc(lilo.library_code)
                        lilo.libraries = encrypted_library_code
                    print(library_details)
                
                    membership_options = parameter_master_L01.objects.filter(isactive=1,parameter_name='MembershipForm').order_by('parameter_id')
                    
                    ward_details = WardMaster.objects.using('default').filter(is_active=1)
                    
                    membership_Master = MembershipMaster.objects.filter(isactive=1)
                    if membership_Master.exists():
                        for mema in membership_Master:
                            encrypted_membership_id = enc(str(mema.id))
                            mema.membership_id_enc = encrypted_membership_id
                        print(membership_Master)

                template = "L01/registration.html"
                context = {
                    'MEDIA_URL': settings.MEDIA_URL,
                    'library_details': library_details,
                    'membership_options': membership_options,
                    'ward_details': ward_details,
                    'membership_Master': membership_Master,
                }
                
            return render(request, template, context)

        elif request.method == "POST":
            try:
                with transaction.atomic():
                    # === Collect Membership Data ===
                    data = {
                        "user_id": request.POST.get("user_id") or None,
                        "aadhar_no": request.POST.get("aadhar_no") or None,
                        "first_name": request.POST.get("first_name") or None,
                        "middle_name": request.POST.get("middle_name") or None,
                        "last_name": request.POST.get("last_name") or None,
                        "first_name_mar": request.POST.get("first_name_mar") or None,
                        "middle_name_mar": request.POST.get("middle_name_mar") or None,
                        "last_name_mar": request.POST.get("last_name_mar") or None,
                        "ward": request.POST.get("ward_name") or None,
                        "pincode": request.POST.get("pincode") or None,
                        "library_name": request.POST.get("library_name") or None,
                        "library_name_mar": request.POST.get("library_name_mar") or None,
                        "local_address": request.POST.get("local_address") or None,
                        "mobile_no": request.POST.get("mobile_number") or None,
                        "occupation": request.POST.get("occupation_details") or None,
                        "office_phone": request.POST.get("phone_number") or None,
                        "education": request.POST.get("education") or None,
                        "institute_name": request.POST.get("institution_name") or None,
                        "recommender_details": request.POST.get("referrer_details") or None,
                        "member_type_id": request.POST.get("membertype") or None,
                        "is_resident_of_nmmc": 1 if request.POST.get("is_nmmc") == "yes" else 0,
                        "address_same_as_aadhar": 1 if request.POST.get("same_aadhar") == "yes" else 0,
                        "membership_duration": request.POST.get("months") or None,
                        "from_date": request.POST.get("fromDate") or None,
                        "to_date": request.POST.get("toDate") or None,
                        "deposit": request.POST.get("deposit") or None,
                        "entry_fees": request.POST.get("entry_fees") or None,
                        "subscription": request.POST.get("subscription") or None,
                        "email": request.POST.get("email") or None,
                        "dob": request.POST.get("dob") or None,
                        "membership_id": request.POST.get("membershiptype") or None,
                        "created_by": request.POST.get("user_id"), 
                        "created_at": timezone.now(), 
                        "status_id": 1,   # pending
                        "isactive": 1,
                    }
                    
                    raw_password = request.POST.get("repeat_password")
                    username  = request.POST.get("user_id")

                    print("===== Membership Form Data =====")
                    for k, v in data.items():
                        print(f"{k}: {v}")
                    print(f"Password (future use): {raw_password}")

                    # === Save Membership ===
                    membership = MembershipDetails.objects.create(**data)
                    
                    # === Handle Document Uploads ===
                    library_code = request.session.get("library_db", "default")
                    documents_info = []

                    for field_name, doc_id in [
                        ("photo_upload", request.POST.get("document_photo_upload")),
                        ("id_upload", request.POST.get("document_id_upload")),
                        ("agreement_copy", request.POST.get("document_agreement_copy")),
                        ("nagarsevak_letter", request.POST.get("document_nagarsevak_letter")),
                        ("employee_letter", request.POST.get("employee_letter")),
                    ]:
                        file = request.FILES.get(field_name)
                        if file and doc_id:
                            # Extract original filename + extension
                            filename, ext = os.path.splitext(file.name)

                            # Generate unique filename
                            timestamp = datetime.datetime.now().strftime("%Y%m%dT%H%M%S")
                            short_uuid = str(uuid.uuid4())[:8]
                            unique_filename = f"{filename}_{timestamp}_{short_uuid}{ext}"

                            # Build save path -> library_code/Document - {doc_id}/unique_filename
                            save_dir = os.path.join(library_code, username, f"Document - {doc_id}")
                            save_path = os.path.join(save_dir, unique_filename)
                            full_path = os.path.join(settings.MEDIA_ROOT, save_path)

                            # ✅ Ensure directory exists
                            os.makedirs(os.path.dirname(full_path), exist_ok=True)

                            # ✅ Save file
                            with open(full_path, "wb+") as destination:
                                for chunk in file.chunks():
                                    destination.write(chunk)

                            # ✅ Save document record
                            DocumentDetails.objects.create(
                                membership=membership,
                                document_id=doc_id,
                                file_name=unique_filename,
                                file_path=save_path,
                                created_by=request.POST.get("user_id"),
                                created_at=timezone.now()
                            )

                            documents_info.append({
                                "document_id": doc_id,
                                "file_name": unique_filename,
                                "file_path": save_path,
                            })

                    print("\n===== Documents Uploaded =====")
                    for d in documents_info:
                        print(d)
                        
                    # === Check for duplicate email or user_id before creating user ===
                    if CustomUser.objects.filter(email=data.get("email")).exists():
                        raise ValueError(f"❌ Email '{data.get('email')}' already exists!")

                    if CustomUser.objects.filter(username=data.get("user_id")).exists():
                        raise ValueError(f"❌ User ID '{data.get('user_id')}' already exists!")

                    # === Create CustomUser ===

                    custom_user = CustomUser.objects.create(
                        first_name=data.get("first_name"),
                        last_name=data.get("last_name"),
                        full_name=f"{data.get('first_name', '')} {data.get('last_name', '')}".strip(),
                        email=data.get("email"),
                        phone=data.get("mobile_no"),
                        role_id=3,  # ✅ Hardcoded
                        address=data.get("local_address"),
                        govt_id=data.get("aadhar_no"),
                        is_active=False,
                        is_staff=True,
                        user_type="member",
                        username=data.get("user_id"),
                        password=make_password(raw_password),  # ✅ Hash password
                        first_time_login=1,
                    )

                    # === Save Raw Password in password_storage ===
                    password_storage.objects.create(
                        user=custom_user,
                        passwordText=raw_password
                    )
                    
                    formfilledsuccessfullyVariable = enc('1')

                    # return redirect('/registration/?formfilledsuccessfully=1')
                    return redirect(f'/{library_code}/registration?formfilledsuccessfully={formfilledsuccessfullyVariable}')


            except Exception as e:
                tb = traceback.extract_tb(e.__traceback__)
                fun = tb[0].name if tb else "registration"
                cursor.callproc("stp_error_log", [fun, str(e), request.session.get("library_db", "default_lib")])
                messages.error(request, f"❌ Error while saving: {str(e)}")
                return HttpResponse(f"Error: {str(e)}", status=500)
                
    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        fun = tb[0].name if tb else 'library_list'
        cursor.callproc("stp_error_log", [fun, str(e), library_code])
        print(f"error: {e}")
        messages.error(request, 'Oops...! Something went wrong!')

# Part Second After Filling Membership Form Approval by Admin

@login_required
def membership_approval(request):
    Db.closeConnection()
    m = Db.get_connection()
    cursor = m.cursor()
    try:
        print("Membership Approval Page Accessed")
        library_code = request.session.get('library_db', None)

        memberships = (MembershipDetails.objects.select_related("status").all().order_by("-created_at"))
        library = tbl_librarymasterL01.objects.filter(library_code=library_code, is_active=1).first()
        library_name_mar = library.library_name_mar if library else ""
        # Encrypt membership IDs
        for mem in memberships:
            mem.membership_id_enc = enc(str(mem.id))

        return render(
            request,
            "L01/membership_approval/membership_approval.html",
            {
                "MEDIA_URL": settings.MEDIA_URL,
                "library_code": library_code,
                "memberships": memberships,
                "library_name_mar": library_name_mar,
            }
        )

    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        fun = tb[0].name if tb else "library_list"
        cursor.callproc("stp_error_log", [fun, str(e), library_code])
        print(f"error: {e}")
        messages.error(request, "Oops...! Something went wrong!")
        return render(request, "L01/membership_approval/membership_approval.html", {})

@login_required
def membership_form_create(request):
    Db.closeConnection()
    m = Db.get_connection()
    cursor = m.cursor()
    try:
        library_code = request.session.get('library_db', None)
        user_code = request.session["user_id"]

        if request.method == "GET":
            
            if library_code:
                    library_details = tbl_librarymasterL01.objects.filter(is_active=1, library_code=library_code)
                    for lilo in library_details:
                        encrypted_library_code = enc(lilo.library_code)
                        lilo.libraries = encrypted_library_code
                    print(library_details)
                
                    membership_options = parameter_master_L01.objects.filter(isactive=1,parameter_name='MembershipForm').order_by('parameter_id')
                    
                    ward_details = WardMaster.objects.using('default').filter(is_active=1)
                    
                    membership_Master = MembershipMaster.objects.filter(isactive=1)
                    if membership_Master.exists():
                        for mema in membership_Master:
                            encrypted_membership_id = enc(str(mema.id))
                            mema.membership_id_enc = encrypted_membership_id
                        print(membership_Master)
                        
            template = "L01/membership_approval/membership_form_create.html"
            context = {
                'MEDIA_URL': settings.MEDIA_URL,
                'library_details': library_details,
                'membership_options': membership_options,
                'ward_details': ward_details,
                'membership_Master': membership_Master,
                'library_code': library_code,
            }
                
            return render(request, template, context)

        elif request.method == "POST":
            try:
                with transaction.atomic():
                    # === Collect Membership Data ===
                    data = {
                        "user_id": request.POST.get("user_id") or None,
                        "aadhar_no": request.POST.get("aadhar_no") or None,
                        "first_name": request.POST.get("first_name") or None,
                        "middle_name": request.POST.get("middle_name") or None,
                        "last_name": request.POST.get("last_name") or None,
                        "first_name_mar": request.POST.get("first_name_mar") or None,
                        "middle_name_mar": request.POST.get("middle_name_mar") or None,
                        "last_name_mar": request.POST.get("last_name_mar") or None,
                        "ward": request.POST.get("ward_name") or None,
                        "pincode": request.POST.get("pincode") or None,
                        "library_name": request.POST.get("library_name") or None,
                        "library_name_mar": request.POST.get("library_name_mar") or None,
                        "local_address": request.POST.get("local_address") or None,
                        "mobile_no": request.POST.get("mobile_number") or None,
                        "occupation": request.POST.get("occupation_details") or None,
                        "office_phone": request.POST.get("phone_number") or None,
                        "education": request.POST.get("education") or None,
                        "institute_name": request.POST.get("institution_name") or None,
                        "recommender_details": request.POST.get("referrer_details") or None,
                        "member_type_id": request.POST.get("membertype") or None,
                        "is_resident_of_nmmc": 1 if request.POST.get("is_nmmc") == "yes" else 0,
                        "address_same_as_aadhar": 1 if request.POST.get("same_aadhar") == "yes" else 0,
                        "membership_duration": request.POST.get("months") or None,
                        "from_date": request.POST.get("fromDate") or None,
                        "to_date": request.POST.get("toDate") or None,
                        "deposit": request.POST.get("deposit") or None,
                        "entry_fees": request.POST.get("entry_fees") or None,
                        "subscription": request.POST.get("subscription") or None,
                        "email": request.POST.get("email") or None,
                        "dob": request.POST.get("dob") or None,
                        "membership_id": request.POST.get("membershiptype") or None,
                        "created_by": user_code, 
                        "created_at": timezone.now(), 
                        "status_id": 1,   # pending
                        "isactive": 1,
                    }
                    
                    raw_password = request.POST.get("repeat_password")
                    username  = request.POST.get("user_id")

                    print("===== Membership Form Data =====")
                    for k, v in data.items():
                        print(f"{k}: {v}")
                    print(f"Password (future use): {raw_password}")
                    
                    if MembershipDetails.objects.filter(email=data.get("email")).exists():
                        messages.error(request, f"❌ ई-मेल '{data.get('email')}' आधी अस्तित्वात आहे!")
                        return redirect('L01:membership_form_create')

                    # === Save Membership ===
                    membership = MembershipDetails.objects.create(**data)

                    # === Handle Document Uploads ===
                    library_code = request.session.get("library_db", "default")
                    documents_info = []

                    for field_name, doc_id in [
                        ("photo_upload", request.POST.get("document_photo_upload")),
                        ("id_upload", request.POST.get("document_id_upload")),
                        ("agreement_copy", request.POST.get("document_agreement_copy")),
                        ("nagarsevak_letter", request.POST.get("document_nagarsevak_letter")),
                        ("employee_letter", request.POST.get("employee_letter")),
                    ]:
                        file = request.FILES.get(field_name)
                        if file and doc_id:
                            # Extract original filename + extension
                            filename, ext = os.path.splitext(file.name)

                            # Generate unique filename
                            timestamp = datetime.datetime.now().strftime("%Y%m%dT%H%M%S")
                            short_uuid = str(uuid.uuid4())[:8]
                            unique_filename = f"{filename}_{timestamp}_{short_uuid}{ext}"

                            # Build save path -> library_code/Document - {doc_id}/unique_filename
                            save_dir = os.path.join(library_code, username, f"Document - {doc_id}")
                            save_path = os.path.join(save_dir, unique_filename)
                            full_path = os.path.join(settings.MEDIA_ROOT, save_path)

                            # ✅ Ensure directory exists
                            os.makedirs(os.path.dirname(full_path), exist_ok=True)

                            # ✅ Save file
                            with open(full_path, "wb+") as destination:
                                for chunk in file.chunks():
                                    destination.write(chunk)

                            # ✅ Save document record
                            DocumentDetails.objects.create(
                                membership=membership,
                                document_id=doc_id,
                                file_name=unique_filename,
                                file_path=save_path,
                                created_by=user_code,
                                created_at=timezone.now()
                            )

                            documents_info.append({
                                "document_id": doc_id,
                                "file_name": unique_filename,
                                "file_path": save_path,
                            })

                    print("\n===== Documents Uploaded =====")
                    for d in documents_info:
                        print(d)
                        
                    # === Check for duplicate email or user_id before creating user ===
                    
                    if CustomUser.objects.filter(email=data.get("email")).exists():
                        messages.error(request, f"❌ ई-मेल '{data.get('email')}' आधी अस्तित्वात आहे!")
                        return redirect('L01:membership_form_create')  # go back to the form

                    if CustomUser.objects.filter(username=data.get("user_id")).exists():
                        messages.error(request, f"❌ User ID '{data.get('user_id')}' आधी अस्तित्वात आहे!")
                        return redirect('L01:membership_form_create')  # go back to the form

                    # === Create CustomUser ===

                    custom_user = CustomUser.objects.create(
                        first_name=data.get("first_name"),
                        last_name=data.get("last_name"),
                        full_name=f"{data.get('first_name', '')} {data.get('last_name', '')}".strip(),
                        email=data.get("email"),
                        phone=data.get("mobile_no"),
                        role_id=3,  # ✅ Hardcoded
                        address=data.get("local_address"),
                        govt_id=data.get("aadhar_no"),
                        is_active=False,
                        is_staff=True,
                        user_type="member",
                        username=data.get("user_id"),
                        password=make_password(raw_password),  # ✅ Hash password
                        first_time_login=1,
                    )

                    # === Save Raw Password in password_storage ===
                    password_storage.objects.create(
                        user=custom_user,
                        passwordText=raw_password
                    )
                    
                    messages.success(request, "✅ नवीन सदस्य यशस्वीरित्या तयार झाला!")
                    return redirect('L01:membership_approval')

            except Exception as e:
                tb = traceback.extract_tb(e.__traceback__)
                fun = tb[0].name if tb else "registration"
                cursor.callproc("stp_error_log", [fun, str(e), request.session.get("library_db", "default_lib")])
                messages.error(request, f"❌ Error while saving: {str(e)}")
                return HttpResponse(f"Error: {str(e)}", status=500)
          
    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        fun = tb[0].name if tb else "library_list"
        cursor.callproc("stp_error_log", [fun, str(e), library_code])
        print(f"error: {e}")
        messages.error(request, "Oops...! Something went wrong!")
        return render(request, "L01/membership_approval/membership_approval.html", {})

@login_required
def membership_form_edit(request):
    Db.closeConnection()
    m = Db.get_connection()
    cursor = m.cursor()
    try:
        library_code = request.session.get('library_db', None)
        user_code = request.session["user_id"]

        if request.method == "GET":
            
            if library_code:
                
                    membershipid = dec(request.GET.get('membershipid'))
                
                    library_details = tbl_librarymasterL01.objects.filter(is_active=1, library_code=library_code)
                    for lilo in library_details:
                        encrypted_library_code = enc(lilo.library_code)
                        lilo.libraries = encrypted_library_code
                    print(library_details)
                
                    membership_options = parameter_master_L01.objects.filter(isactive=1,parameter_name='MembershipForm').order_by('parameter_id')
                    
                    ward_details = WardMaster.objects.using('default').filter(is_active=1)
                    
                    membership_Master = MembershipMaster.objects.filter(isactive=1)
                    if membership_Master.exists():
                        for mema in membership_Master:
                            encrypted_membership_id = enc(str(mema.id))
                            mema.membership_id_enc = encrypted_membership_id
                        print(membership_Master)
                        
                    membership = get_object_or_404(MembershipDetails, id=membershipid, isactive=1)    
                    
                    document_details = DocumentDetails.objects.filter(
                        membership=membership, isactive=1
                    ).select_related("document")

                    documents_map = {}
                    for doc in document_details:
                        doc.doc_id_enc = enc(str(doc.id))  # encrypt document ID
                        documents_map[doc.document.id] = doc
                        
            template = "L01/membership_approval/membership_form_edit.html"
            context = {
                'MEDIA_URL': settings.MEDIA_URL,
                'library_details': library_details,
                'membership_options': membership_options,
                'ward_details': ward_details,
                'membership_Master': membership_Master,
                'library_code': library_code,
                'membership': membership,
                'documents_map': documents_map,
            }
                
            return render(request, template, context)
        
        # notepad++ 352 
        
        if request.method == "POST":
            with transaction.atomic():
                membership_id = request.POST.get("membership_id")
                user_id = request.POST.get("user_id")
                membership = get_object_or_404(MembershipDetails, id=membership_id)

                updated = False  # flag to track changes

                # Mapping of form fields -> model fields
                field_map = {
                    "first_name": "first_name",
                    "first_name_mar": "first_name_mar",
                    "middle_name": "middle_name",
                    "middle_name_mar": "middle_name_mar",
                    "last_name": "last_name",
                    "last_name_mar": "last_name_mar",
                    "ward_name": "ward",
                    "pincode": "pincode",
                    "occupation_details": "occupation",
                    "phone_number": "office_phone",
                    "education": "education",
                    "institution_name": "institute_name",
                    "referrer_details": "recommender_details",
                    "is_nmmc": "is_resident_of_nmmc",
                    "same_aadhar": "address_same_as_aadhar",
                    "local_address": "local_address",
                    "membershiptype": "membership_id",  # FK to MembershipMaster
                    "membertype": "member_type_id",     # FK to parameter_master_L01
                    "months": "membership_duration",
                    "fromDate": "from_date",
                    "dob": "dob",
                }

                for form_field, model_field in field_map.items():
                    new_value = request.POST.get(form_field)
                    old_value = getattr(membership, model_field, None)

                    # Convert boolean-like fields
                    if model_field in ["is_resident_of_nmmc", "address_same_as_aadhar"]:
                        if new_value is not None:
                            new_value = 1 if new_value.lower() in ["1", "yes", "true", "on"] else 0
                        else:
                            new_value = None

                    # Convert integer fields
                    if model_field == "membership_duration":
                        new_value = int(new_value) if new_value else None

                    # Convert FK fields
                    if model_field in ["membership_id", "member_type_id"]:
                        new_value = int(new_value) if new_value else None

                    if new_value != old_value:
                        setattr(membership, model_field, new_value)
                        updated = True

                # --- Handle monetary fields ---
                money_fields = {
                    "deposit": "deposit",
                    "entry_fees": "entry_fees",
                    "subscription": "subscription"
                }

                for field_name, model_field in money_fields.items():
                    new_value = request.POST.get(field_name)
                    new_value = float(new_value) if new_value else 0.0
                    old_value = getattr(membership, model_field, 0.0)
                    if new_value != old_value:
                        setattr(membership, model_field, new_value)
                        updated = True

                # Handle file uploads
                file_fields = {
                    "photo_upload": 1,
                    "id_upload": 2,
                    "employee_letter": 3,
                    "nagarsevak_letter": 4,
                    "agreement_copy": 5
                }

                for field_name, doc_type in file_fields.items():
                    uploaded_file = request.FILES.get(field_name)
                    if uploaded_file:
                        # Get existing document
                        old_doc = DocumentDetails.objects.filter(
                            membership=membership, document_id=doc_type
                        ).first()

                        # Delete old file if exists
                        if old_doc and old_doc.file_path:
                            old_path = os.path.join(settings.MEDIA_ROOT, old_doc.file_path)
                            if os.path.isfile(old_path):
                                os.remove(old_path)
                            old_doc.delete()

                        # Construct path: library_code/<user_id>/Document - X/
                        user_folder = f"{library_code}/{user_id}"
                        doc_type_folder = f"Document - {doc_type}"
                        save_dir = os.path.join(settings.MEDIA_ROOT, user_folder, doc_type_folder)
                        os.makedirs(save_dir, exist_ok=True)

                        timestamp = timezone.now().strftime("%Y%m%dT%H%M%S")
                        filename = f"{uploaded_file.name.rsplit('.', 1)[0]}_{timestamp}.{uploaded_file.name.rsplit('.', 1)[1]}"
                        save_path = os.path.join(save_dir, filename)

                        # Save file manually
                        with open(save_path, 'wb+') as destination:
                            for chunk in uploaded_file.chunks():
                                destination.write(chunk)

                        # Store relative path in DB (so MEDIA_ROOT can be prepended later)
                        relative_path = os.path.relpath(save_path, settings.MEDIA_ROOT)

                        if old_doc:
                            # Update existing record
                            old_doc.file_name = filename
                            old_doc.file_path = relative_path
                            old_doc.updated_by = user_code
                            old_doc.save()
                        else:
                            # Create new record
                            DocumentDetails.objects.create(
                                membership=membership,
                                document_id=doc_type,
                                file_name=filename,
                                file_path=relative_path,
                                created_by=user_code,
                            )
                        updated = True

                if updated:
                    membership.updated_by = user_code
                    membership.save()
                    messages.success(request, "Membership updated successfully!")
                else:
                    messages.info(request, "No changes detected. Membership not updated.")

            return redirect("L01:membership_approval")
         
    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        fun = tb[0].name if tb else "library_list"
        cursor.callproc("stp_error_log", [fun, str(e), library_code])
        print(f"error: {e}")
        messages.error(request, "Oops...! Something went wrong!")
        return redirect("L01:membership_approval")

def secure_document_view(request, doc_id_enc):
    try:
        # Decrypt the document ID
        doc_id = dec(doc_id_enc)
        document = get_object_or_404(DocumentDetails, id=doc_id, isactive=1)

        # Build full file path safely
        file_path = Path(settings.MEDIA_ROOT) / Path(document.file_path.replace("\\", "/"))

        if not file_path.exists():
            raise Http404("Document file not found")

        return FileResponse(open(file_path, 'rb'), as_attachment=False, filename=document.file_name)
    except Exception:
        raise Http404("Document not found")
    
@login_required
def membership_form_view(request):
    Db.closeConnection()
    m = Db.get_connection()
    cursor = m.cursor()
    try:
        library_code = request.session.get('library_db', None)
        user_code = request.session["user_id"]
        role_id = request.session["role_id"]
        
        if request.method == "GET":
            
            if library_code:
                
                    membershipid = dec(request.GET.get('membershipid'))
                
                    library_details = tbl_librarymasterL01.objects.filter(is_active=1, library_code=library_code)
                    for lilo in library_details:
                        encrypted_library_code = enc(lilo.library_code)
                        lilo.libraries = encrypted_library_code
                    print(library_details)
                
                    membership_options = parameter_master_L01.objects.filter(isactive=1,parameter_name='MembershipForm').order_by('parameter_id')
                    
                    ward_details = WardMaster.objects.using('default').filter(is_active=1)
                    
                    membership = get_object_or_404(MembershipDetails, id=membershipid, isactive=1)    
                    
                    membership_Master = MembershipMaster.objects.filter(isactive=1)
                    if membership_Master.exists():
                        for mema in membership_Master:
                            mema.membership_id_enc = enc(str(mema.id))
                            mema.membership_code_enc = enc(str(mema.membership_code)) if mema.membership_code else None

                        print(membership_Master)
                    
                    document_details = DocumentDetails.objects.filter(
                        membership=membership, isactive=1
                    ).select_related("document")

                    documents_map = {}
                    for doc in document_details:
                        doc.doc_id_enc = enc(str(doc.id))  # encrypt document ID
                        documents_map[doc.document.id] = doc
                        
            template = "L01/membership_approval/membership_form_view.html"
            context = {
                'MEDIA_URL': settings.MEDIA_URL,
                'library_details': library_details,
                'membership_options': membership_options,
                'ward_details': ward_details,
                'membership_Master': membership_Master,
                'library_code': library_code,
                'membership': membership,
                'documents_map': documents_map,
                'role_id': role_id,
            }
                
            return render(request, template, context)
        
        if request.method == "POST":
            # Step 1: Get POST data
            membership_id = request.POST.get("membership_id")
            action = request.POST.get("action")  # approve / reject
            user_id = request.POST.get("user_id")

            # Step 2: Get the membership object
            membership = get_object_or_404(MembershipDetails, id=membership_id, isactive=1)

            if action == 'payment_received':
                
                try:
                    # Step 1: Update MembershipDetails status
                    status_received = StatusMaster.objects.get(id=5)  # status_id = 5
                    membership.status = status_received
                    membership.updated_by = user_code
                    membership.save()
                    
                    membership_master = membership.membership    
                    # Step 2: Insert a row in PaymentDetails
                    PaymentDetails.objects.create(
                        membership=membership,
                        payment_mode="Offline",
                        payment_method="Cash/Cheque/Other",  # choose dynamically if needed
                        payment_type="Membership",  # choose dynamically if needed
                        deposit_amount=membership.deposit,
                        entry_fee_amount=membership.entry_fees,
                        monthly_subscription_amount=membership_master.subscription_fees,
                        total_subscription_amount=(membership.subscription),
                        subscription_from=membership.from_date,
                        subscription_to=membership.to_date,
                        status=status_received,
                        membership_code=membership.membership_code,
                        user_id=user_id,
                        created_by=user_code,
                        updated_by=user_code,
                        payment_date=timezone.now().date(),
                    )

                    messages.success(request, "Payment marked as received successfully!")
                    return redirect("L01:membership_approval")

                except Exception as e:
                    messages.error(request, f"Error processing payment: {str(e)}")
                    return redirect("L01:membership_approval")
            
            else:
                # Step 3: Map actions to status IDs
                status_map = {
                    "approved": 2,
                    "rejected": 3,
                }
                new_status_id = status_map.get(action)

                if new_status_id:
                    # --- Only generate code if approved ---
                    if new_status_id == 2:  # APPROVED
                        if membership.membership_code:
                            messages.warning(request, "Membership code already exists. No new code generated.")
                        else:
                            increment_master = get_object_or_404(
                                IncrementMaster,
                                id=1,
                                isactive=1
                            )

                            current_number = int(increment_master.incrementFieldNumber)
                            new_number = current_number + 1
                            new_number_str = str(new_number).zfill(5)

                            membership_code = f"{increment_master.incrementFieldName}_{timezone.now().strftime('%Y%m%d')}_{new_number_str}"

                            increment_master.incrementFieldNumber = new_number_str
                            increment_master.save()

                            membership.membership_code = membership_code

                        # --- Update user status to active ---
                        user = CustomUser.objects.get(username=user_id)
                        user.is_active = True
                        user.save()
                        
                        # --- Get password from password_storage ---
                        password_entry = get_object_or_404(password_storage, user=user)
                        user_password = password_entry.passwordText  # Password fetched from password_storage

                        # --- Retrieve OTP message template ---
                        otp_template = get_object_or_404(OTPMessage, OTPIDNumber=1)  # Assuming OTPIDNumber=1 for registration
                        message = otp_template.OTPText.replace('@UserId', f"{user.username} and {user_password}")

                        # --- Send SMS ---
                        send_sms(user.phone, message)  # Send SMS to the user's mobile

                        # --- Log the SMS ---
                        log_sms(user, user.phone, message, 'Success', 'unique_id_here')  # You can generate a unique ID as needed

                        messages.success(request, f"User {user.username} activated successfully and SMS sent.")

                    # --- Update membership fields ---
                    membership.actionperformed = action
                    membership.reviewed = user_code
                    membership.reviewed_at = timezone.now()
                    membership.status_id = new_status_id
                    membership.save()

                    messages.success(request, f"Membership {action.capitalize()}d successfully.")
                else:
                    messages.error(request, "Invalid action!")

            return redirect("L01:membership_approval")
        
    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        fun = tb[0].name if tb else "library_list"
        cursor.callproc("stp_error_log", [fun, str(e), library_code])
        print(f"error: {e}")
        messages.error(request, "Oops...! Something went wrong!")
        return redirect("L01:membership_approval")

def send_sms(mobile, message):
    try:
        api_url = f"https://api.pinnacle.in/index.php/sms/send/NMMCSV/{mobile}/{message}/TXT?apikey=6ac137-a52260-71ad83-05eea9-422b6e"

        response = requests.get(api_url)
        if response.status_code == 200:
            return True
        else:
            logger.error(f"Error sending SMS to {mobile}: {response.text}")
            return False
    except Exception as e:
        logger.error(f"Error sending SMS to {mobile}: {e}")
        return False

def log_sms(user, mobile, message, status, unique_id):
    try:
        SMSLog.objects.create(
            user=user,
            mobile=mobile,
            message=message,
            status=status,
            unique_id=unique_id,
            content_type="text",
            response_status="Success" if status == 'Success' else "Failed",
            response_uri="API_URL",
            status_description="Message Sent" if status == 'Success' else "Failed",
            error_exception="N/A",
            error_message="N/A",
        )
    except Exception as e:
        logger.error(f"Error logging SMS for user {user.username} (ID: {user.id}): {e}")
        SMSLog.objects.create(
            user=user,
            mobile=mobile,
            message=message,
            status="Failed",
            unique_id=unique_id,
            content_type="text",
            response_status="Failed",
            response_uri="API_URL",
            status_description="Logging Failed",
            error_exception=str(e),
            error_message="Failed to log SMS due to an exception",
        )

# Membership Management Views by Member

@login_required
def membership_payment_index(request):
    Db.closeConnection()
    m = Db.get_connection()
    cursor = m.cursor()
    try:
        library_code = request.session.get('library_db', None)
        username = request.session.get('username', None)
        user_id = request.session["user_id"]
        role_id = request.session["role_id"]

        if request.method == "GET":
            # member's membershp details
            memberships = (
                MembershipDetails.objects
                .select_related("status", "membership")
                .filter(user_id=username)
            )
            for mem in memberships:
                mem.membership_id_enc = enc(str(mem.id))        
                mem.per_month_subscription = mem.membership.subscription_fees if mem.membership else 0
                
            # Library Name
            library = tbl_librarymasterL01.objects.filter(library_code=library_code, is_active=1).first()
            library_name_mar = library.library_name_mar if library else ""
                
            return render(
                request,
                "L01/Member Payment/member_payment.html",
                {
                    "MEDIA_URL": settings.MEDIA_URL,
                    "library_code": library_code,
                    "memberships": memberships,
                    "library_name_mar": library_name_mar,
                }
            )
            
        if request.method == "POST":
            membership_id = dec(request.POST.get("membership_id"))
            payment_type = request.POST.get("payment_type")
            
            # Update membership details as offline payment pending
            mem = MembershipDetails.objects.filter(id=membership_id, user_id=username).first()
            if mem:
                # Set status to Payment Pending
                pay_pending_status = StatusMaster.objects.get(status_code="PAY_OFFLINE")
                mem.status = pay_pending_status
                mem.updated_by = user_id
                mem.save()
                messages.success(request, "ऑफलाइन देयक प्रक्रिया सुरू आहे. स्थिती 'Payment Offline' मध्ये बदलली गेली आहे.")
                return redirect("L01:membership_payment_index")

    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        fun = tb[0].name if tb else "library_list"
        cursor.callproc("stp_error_log", [fun, str(e), library_code])
        print(f"error: {e}")
        messages.error(request, "Oops...! Something went wrong!")
        return render(request, "L01/Member Payment/member_payment.html", {})

@login_required
def membership_paymentreceipt_download(request):
    try:
        membership_id = dec(request.GET.get("membershipid"))
        membership = get_object_or_404(MembershipDetails, id=membership_id)
        membership_master = membership.membership
        payments = PaymentDetails.objects.filter(
            membership=membership,
            payment_type='Membership'
        ).order_by('-id')[:1] 

        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4

        regular_font_path = os.path.join(settings.BASE_DIR, 'static/fonts/Merriweather_120pt-Regular.ttf')
        bold_font_path = os.path.join(settings.BASE_DIR, 'static/fonts/Merriweather_120pt-Bold.ttf')
        pdfmetrics.registerFont(TTFont('Merriweather', regular_font_path))
        pdfmetrics.registerFont(TTFont('Merriweather-Bold', bold_font_path))

        # Page margins
        left_margin = 20*mm
        right_margin = width - 20*mm
        top_margin = height - 10*mm
        bottom_margin = 20*mm
        y = top_margin

        # ✅ Full-page border
        c.setLineWidth(1)
        c.rect(10, 10, width - 20, height - 20)

        # Logo
        logo_path = os.path.join(settings.BASE_DIR, 'static/images/administrative/nmmc-logo.jpeg')
        logo_width = 30*mm
        logo_height = 30*mm
        if os.path.exists(logo_path):
            c.drawImage(logo_path, left_margin, y - logo_height, width=logo_width, height=logo_height, mask='auto')

        # Header text - side by side with logo
        text_x = left_margin + logo_width + 10*mm
        text_y = y - logo_height/2 + 12

        c.setFont("Merriweather", 24)
        c.drawString(text_x, text_y, "Navi Mumbai Municipal Corporation")

        c.setFont("Merriweather", 14)
        c.drawString(text_x, text_y - 30, "Membership Payment Receipt")

        # Move y down for next content
        y = y - logo_height - 30

        # ---------------- Member Details Table ----------------
        c.setFont("Merriweather-Bold", 14)
        c.drawString(left_margin, y, "Member Details:")
        y -= 60

        table_data = [
            ["Field", "Details"],
            ["Full Name", f"{membership.first_name} {membership.middle_name or ''} {membership.last_name}"],
            ["User ID", membership.user_id],
            ["Library", membership.library_name],
            ["Membership Name", membership_master.membership_type_en],
            ["Membership Duration", f"{membership.membership_duration} months ({membership.from_date} to {membership.to_date})"]
        ]

        table = Table(table_data, colWidths=[60*mm, 100*mm], hAlign='LEFT')
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('FONTNAME', (0, 0), (-1, 0), 'Merriweather-Bold'),
            ('FONTNAME', (0, 1), (-1, -1), 'Merriweather'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('BOTTOMPADDING', (0,0), (-1,-1), 8),
            ('TOPPADDING', (0,0), (-1,-1), 8),
            ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        ]))
        table.wrapOn(c, width, height)
        table.drawOn(c, left_margin, y - (len(table_data) * 20))
        y = y - (len(table_data) * 20) - 20

        # ---------------- Payment Details Table ----------------
        y -= 10
        c.setFont("Merriweather-Bold", 14)
        c.drawString(left_margin, y, "Payment Details:")
        y -= 60

        payment_data_list = []
        for idx, p in enumerate(payments, start=1):
            payment_data_list.append(["Field", "Details"])
            payment_data_list.append(["Payment Date", str(p.payment_date)])
            payment_data_list.append(["Payment Mode", str(p.payment_mode)])
            payment_data_list.append(["Payment Status", str(p.status.status_name if p.status else "")])
            payment_data_list.append(["Deposit (₹)", f"{p.deposit_amount or 0:.2f}"])
            payment_data_list.append(["Entry Fee (₹)", f"{p.entry_fee_amount or 0:.2f}"])
            payment_data_list.append(["Subscription (₹)", f"{p.monthly_subscription_amount or 0:.2f}"])
            payment_data_list.append(["Total Paid (₹)", f"{p.total_subscription_amount or 0:.2f}"])
            payment_data_list.append(["Transaction / Remarks", f"{p.transaction_id or ''} {('(' + p.remarks + ')' if p.remarks else '')}"])

        if not payment_data_list:
            payment_data_list = [["No payments found", ""]]

        payment_table = Table(payment_data_list, colWidths=[60*mm, 100*mm], hAlign='LEFT')
        payment_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('FONTNAME', (0, 0), (-1, 0), 'Merriweather-Bold'),
            ('FONTNAME', (0, 1), (-1, -1), 'Merriweather'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('GRID', (0,0), (-1,-1), 0.5, colors.black),
            ('TOPPADDING', (0,0), (-1,-1), 6),
            ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ]))
        payment_table.wrapOn(c, width, height)
        payment_table.drawOn(c, left_margin, y - (len(payment_data_list) * 20))
        y = y - (len(payment_data_list) * 20) - 20

        # ---------------- Membership Summary Table ----------------
        y -= 10
        c.setFont("Merriweather-Bold", 14)
        c.drawString(left_margin, y, "Membership Summary:")
        y -= 20

        sub_data = [
            ["Total Subscription Fee (₹)", f"{membership.subscription:.2f}"]
        ]

        summary_table = Table(sub_data, colWidths=[60*mm, 100*mm], hAlign='LEFT')
        summary_table.setStyle(TableStyle([
            ('FONTNAME', (0,0), (-1,-1), 'Merriweather'),
            ('FONTSIZE', (0,0), (-1,-1), 12),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('GRID', (0,0), (-1,-1), 0.5, colors.black),
            ('TOPPADDING', (0,0), (-1,-1), 6),
            ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ]))
        summary_table.wrapOn(c, width, height)
        summary_table.drawOn(c, left_margin, y - (len(sub_data) * 20))
        y = y - (len(sub_data) * 20) - 20

        # Footer
        c.setFont("Merriweather", 12)
        c.drawString(left_margin, bottom_margin, "This is a computer-generated receipt and does not require signature. NMMC Library")

        c.save()
        buffer.seek(0)
        response = HttpResponse(buffer, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="payment_receipt_{membership.user_id}.pdf"'
        return response

    except Exception as e:
        print(f"Error generating PDF: {e}")
        messages.error(request, "Oops! Something went wrong!")
        return render(request, "L01/Member Payment/member_payment.html", {})

@login_required
def membership_form_renew(request):
    Db.closeConnection()
    m = Db.get_connection()
    cursor = m.cursor()
    try:
        library_code = request.session.get('library_db', None)
        user_code = request.session["user_id"]

        if request.method == "GET":
            
            if library_code:
                
                    membershipid = dec(request.GET.get('membershipid'))
                
                    library_details = tbl_librarymasterL01.objects.filter(is_active=1, library_code=library_code)
                    for lilo in library_details:
                        encrypted_library_code = enc(lilo.library_code)
                        lilo.libraries = encrypted_library_code
                    print(library_details)
                
                    membership_options = parameter_master_L01.objects.filter(isactive=1,parameter_name='MembershipForm').order_by('parameter_id')
                    
                    ward_details = WardMaster.objects.using('default').filter(is_active=1)
                    
                    membership_Master = MembershipMaster.objects.filter(isactive=1)
                    if membership_Master.exists():
                        for mema in membership_Master:
                            encrypted_membership_id = enc(str(mema.id))
                            mema.membership_id_enc = encrypted_membership_id
                        print(membership_Master)
                        
                    membership = get_object_or_404(MembershipDetails, id=membershipid, isactive=1)    
                    
                    document_details = DocumentDetails.objects.filter(
                        membership=membership, isactive=1
                    ).select_related("document")

                    documents_map = {}
                    for doc in document_details:
                        doc.doc_id_enc = enc(str(doc.id))  # encrypt document ID
                        documents_map[doc.document.id] = doc
                        
            template = "L01/membership_approval/membership_form_renew.html"
            context = {
                'MEDIA_URL': settings.MEDIA_URL,
                'library_details': library_details,
                'membership_options': membership_options,
                'ward_details': ward_details,
                'membership_Master': membership_Master,
                'library_code': library_code,
                'membership': membership,
                'documents_map': documents_map,
            }
                
            return render(request, template, context)
        
        if request.method == "POST":
            with transaction.atomic():
                membership_id = request.POST.get("membership_id")
                user_id = request.POST.get("user_id")
                membership = get_object_or_404(MembershipDetails, id=membership_id)

                updated = False  # Flag to track if any changes happened

                # ------------------------------
                # 1. Mapping form fields to model fields
                # ------------------------------
                field_map = {
                    "occupation_details": "occupation",
                    "phone_number": "office_phone",
                    "education": "education",
                    "institution_name": "institute_name",
                    "referrer_details": "recommender_details",
                    "membershiptype": "membership_id",  # FK to MembershipMaster
                    "membertype": "member_type_id",     # FK to parameter_master_L01
                    "months": "membership_duration",
                    "fromDate": "from_date",
                    "toDate": "to_date",
                }

                # ------------------------------
                # 2. Check if any field changed (before updating)
                # ------------------------------
                for form_field, model_field in field_map.items():
                    new_value = request.POST.get(form_field)

                    # Normalize string 'None' or empty strings to Python None
                    if new_value in ["", "None", None]:
                        new_value = None

                    # Convert integer fields
                    if model_field == "membership_duration" and new_value is not None:
                        new_value = int(new_value)

                    # Convert FK fields
                    if model_field in ["membership_id", "member_type_id"] and new_value is not None:
                        new_value = int(new_value)

                    # Convert date fields
                    if model_field in ["from_date", "to_date"] and new_value is not None:
                        new_value = datetime.strptime(new_value, "%Y-%m-%d").date()

                    old_value = getattr(membership, model_field, None)
                    if old_value in ["", "None", None]:
                        old_value = None

                    if new_value != old_value:
                        updated = True
                        break

                # ------------------------------
                # 3. Check monetary fields
                # ------------------------------
                money_fields = ["deposit", "entry_fees", "subscription"]
                for field in money_fields:
                    new_value = request.POST.get(field)
                    new_value = float(new_value) if new_value else 0.0
                    old_value = getattr(membership, field, 0.0)
                    if new_value != old_value:
                        updated = True
                        break

                # ------------------------------
                # 4. Check if any files uploaded
                # ------------------------------
                file_fields = ["photo_upload", "id_upload", "employee_letter", "nagarsevak_letter", "agreement_copy"]
                for field in file_fields:
                    if request.FILES.get(field):
                        updated = True
                        break

                # ------------------------------
                # 5. Save current membership state to history (only if updates detected)
                # ------------------------------
                
                if updated:
                    MembershipDetailsHistory.objects.create(
                        membership=membership,
                        membershipmaster=membership.membership,
                        status=membership.status,
                        member_type=membership.member_type,  
                        first_name=membership.first_name,
                        middle_name=membership.middle_name,
                        last_name=membership.last_name,
                        first_name_mar=membership.first_name_mar,
                        middle_name_mar=membership.middle_name_mar,
                        last_name_mar=membership.last_name_mar,
                        ward=membership.ward,
                        pincode=membership.pincode,
                        library_name=membership.library_name,
                        library_name_mar=membership.library_name_mar,
                        local_address=membership.local_address,
                        mobile_no=membership.mobile_no,
                        occupation=membership.occupation,
                        office_phone=membership.office_phone,
                        education=membership.education,
                        institute_name=membership.institute_name,
                        recommender_details=membership.recommender_details,
                        dob=membership.dob,
                        aadhar_no=membership.aadhar_no,
                        user_id=membership.user_id,
                        password=membership.password,
                        membership_duration=membership.membership_duration,
                        from_date=membership.from_date,
                        to_date=membership.to_date,
                        deposit=membership.deposit,
                        entry_fees=membership.entry_fees,
                        subscription=membership.subscription,
                        email=membership.email,
                        is_resident_of_nmmc=membership.is_resident_of_nmmc,
                        address_same_as_aadhar=membership.address_same_as_aadhar,
                        actionperformed = membership.actionperformed,
                        reviewed = membership.reviewed,
                        reviewed_at = membership.reviewed_at,
                        membership_code=membership.membership_code,
                        created_at=membership.created_at,
                        created_by=membership.created_by,
                        updated_at=membership.updated_at,
                        updated_by=membership.updated_by,
                        changed_by=user_code,
                    )

                # ------------------------------
                # 6. Update normal fields if changed
                # ------------------------------
                for form_field, model_field in field_map.items():
                    new_value = request.POST.get(form_field)

                    if model_field == "membership_duration":
                        new_value = int(new_value) if new_value else None
                    if model_field in ["membership_id", "member_type_id"]:
                        new_value = int(new_value) if new_value else None

                    old_value = getattr(membership, model_field, None)
                    if new_value != old_value:
                        setattr(membership, model_field, new_value)

                # ------------------------------
                # 7. Update monetary fields
                # ------------------------------
                for field in money_fields:
                    new_value = request.POST.get(field)
                    new_value = float(new_value) if new_value else 0.0
                    old_value = getattr(membership, field, 0.0)
                    if new_value != old_value:
                        setattr(membership, field, new_value)

                # ------------------------------
                # 8. Handle file uploads
                # ------------------------------
                file_map = {
                    "photo_upload": 1,
                    "id_upload": 2,
                    "employee_letter": 3,
                    "nagarsevak_letter": 4,
                    "agreement_copy": 5
                }

                for field_name, doc_type in file_map.items():
                    uploaded_file = request.FILES.get(field_name)
                    if uploaded_file:
                        # 1️⃣ Save old file in history if exists
                        old_doc = DocumentDetails.objects.filter(
                            membership=membership, document_id=doc_type
                        ).first()
                        if old_doc:
                            DocumentDetailsHistory.objects.create(
                                original_document=old_doc,
                                membership=membership,
                                document=old_doc.document,
                                file_name=old_doc.file_name,
                                file_path=old_doc.file_path,
                                uploaded_by=old_doc.updated_by or old_doc.created_by
                            )

                        # 2️⃣ Save new file in DocumentDetails
                        user_folder = f"{library_code}/{user_id}"
                        doc_type_folder = f"Document - {doc_type}"
                        save_dir = os.path.join(settings.MEDIA_ROOT, user_folder, doc_type_folder)
                        os.makedirs(save_dir, exist_ok=True)

                        timestamp = timezone.now().strftime("%Y%m%dT%H%M%S")
                        filename = f"{uploaded_file.name.rsplit('.', 1)[0]}_{timestamp}.{uploaded_file.name.rsplit('.', 1)[1]}"
                        save_path = os.path.join(save_dir, filename)

                        with open(save_path, 'wb+') as destination:
                            for chunk in uploaded_file.chunks():
                                destination.write(chunk)

                        relative_path = os.path.relpath(save_path, settings.MEDIA_ROOT)

                        if old_doc:
                            # Update existing record
                            old_doc.file_name = filename
                            old_doc.file_path = relative_path
                            old_doc.updated_by = user_code
                            old_doc.save()
                        else:
                            DocumentDetails.objects.create(
                                membership=membership,
                                document_id=doc_type,
                                file_name=filename,
                                file_path=relative_path,
                                created_by=user_code,
                            )

                # ------------------------------
                # 9. Save membership if updated
                # ------------------------------
                if updated:
                    membership.updated_by = user_code
                    membership.status_id = 9
                    membership.actionperformed = None
                    membership.reviewed = None
                    membership.reviewed_at = None
                    membership.save()
                    messages.success(request, "Membership updated successfully!")
                else:
                    messages.info(request, "No changes detected. Membership not updated.")

                return redirect("L01:membership_payment_index")
       
    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        fun = tb[0].name if tb else "library_list"
        cursor.callproc("stp_error_log", [fun, str(e), library_code])
        print(f"error: {e}")
        messages.error(request, "Oops...! Something went wrong!")
        return redirect("L01:membership_payment_index")

# circulation
@login_required
def bar_code_index(request):
    Db.closeConnection()
    m = Db.get_connection()
    cursor = m.cursor()
    try:
        library_code = request.session.get('library_db', None)
        username = request.session.get('username', None)
        user_id = request.session["user_id"]
        role_id = request.session["role_id"]

        if request.method == "GET":
            
            accessions = BookAccession.objects.select_related(
                'catalogue',  # 👈 pulls in BookCatalog
                'supplier', 'currency', 'funding_source',
                'condition_at_entry', 'location', 'status'
            ).filter(status__status_id=4).order_by("-accession_id")
            
            for a in accessions:
                a.encrypted_id = enc(str(a.accession_id))
        
            return render(
                request,
                "L01/Circulation/barcodeindex.html",
                {
                    "MEDIA_URL": settings.MEDIA_URL,
                    "library_code": library_code,
                    "accessions": accessions,
                }
            )
            
    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        fun = tb[0].name if tb else "library_list"
        cursor.callproc("stp_error_log", [fun, str(e), library_code])
        print(f"error: {e}")
        messages.error(request, "Oops...! Something went wrong!")
        return render(request, "L01/Circulation/barcodeindex.html", {})

@login_required
def generate_barcode(request):
    accession_id = request.GET.get("accessionid")
    if not accession_id:
        return HttpResponseBadRequest("Missing accession ID")

    try:
        decrypted_id = dec(accession_id)  # your existing decrypt method
    except Exception:
        return HttpResponseBadRequest("Invalid accession ID")

    accession = get_object_or_404(BookAccession, accession_id=decrypted_id)

    accession_number = accession.accession_no or "UNKNOWN"

    # Generate barcode
    CODE = barcode.get_barcode_class('code128')
    writer_options = {
        "module_width": 0.4,   
        "module_height": 8,   
        "quiet_zone": 2,       
        "font_size": 6,       # slightly bigger number
        "text_distance": 2.5,    # distance between barcode and number
        "write_text": True
    }
    buffer = BytesIO()
    CODE(accession_number, writer=ImageWriter()).write(buffer, options=writer_options)

    # Convert image to base64
    barcode_image = base64.b64encode(buffer.getvalue()).decode('utf-8')

    return JsonResponse({
        "accession_no": accession_number,
        "barcode_image": barcode_image,
    })

# Palavees work
@login_required
def library_master_index_individual(request):
    library = None
    library_name = ""
    ward_name = ""
    location_name = ""
    accounting_code_name = ""
    library_details = []
    ward_details = []
    location_details = []
    accounting_code_details = []

    Db.closeConnection()
    m = Db.get_connection()
    cursor = m.cursor()

    try:
        if request.method == "POST":
            # ------------------------
            # Form fields
            # ------------------------
            library_code = request.POST.get("library_code", "").strip()
            library_name = request.POST.get("library_name", "").strip()
            library_name_mar = request.POST.get("library_name_mar", "").strip()
            location_id = request.POST.get("location_id", "").strip()
            parent_ward_id = request.POST.get("parent_ward_id", "").strip()
            accounting_code_id = request.POST.get("accounting_code_id", "").strip()
            librarian_name = request.POST.get("librarian_name", "").strip()
            contact_email = request.POST.get("contact_email", "").strip()
            contact_phone = request.POST.get("contact_phone", "").strip()
            about_library = request.POST.get("about_library", "").strip()
            is_active = int(request.POST.get("is_active", 1))

            # ------------------------
            # Check if library code exists in L01 DB
            # ------------------------
            try:
                library = tbl_librarymasterL01.objects.get(library_code=library_code)
            except tbl_librarymasterL01.DoesNotExist:
                library = tbl_librarymasterL01()  # create new if not exists

            # ------------------------
            # Additional fields from template
            # ------------------------
            landing_page_link = request.POST.get("landing_page_link", "").strip()
            membership_page_link = request.POST.get("membership_page_link", "").strip()
            library_rules = request.POST.get("library_rules", "").strip()
            membership_rules = request.POST.get("membership_rules", "").strip()
            facebook_url = request.POST.get("facebook_url", "").strip()
            twitter_url = request.POST.get("twitter_url", "").strip()
            instagram_url = request.POST.get("instagram_url", "").strip()
            youtube_url = request.POST.get("youtube_url", "").strip()
            capacity = request.POST.get("capacity", "").strip()
            opening_hours = request.POST.get("opening_hours", "").strip()
            location_url = request.POST.get("location_url", "").strip()
            est_year = request.POST.get("est_year", "").strip()

            # ------------------------
            # Uploaded image (keep old if no new one)
            # ------------------------
            library_image = request.FILES.get("library_photo")
            image_url = getattr(library, "image_url", "")  # keep old image if no new one

            if library_image:
                library_folder = os.path.join(settings.MEDIA_ROOT, library_code, "library_images")
                os.makedirs(library_folder, exist_ok=True)
                image_path = os.path.join(library_folder, library_image.name)
                with open(image_path, "wb+") as f:
                    for chunk in library_image.chunks():
                        f.write(chunk)
                image_url = os.path.join(library_code, "library_images", library_image.name).replace("\\", "/")

            # ------------------------
            # Validation
            # ------------------------
            if not library_name:
                messages.error(request, "Library Name is required!")
            else:
                # ------------------------
                # Save/Update record in tbl_librarymasterL01
                # ------------------------
                library.library_code = library_code
                library.library_name = library_name
                library.library_name_mar = library_name_mar
                library.location = location_id
                library.parent_ward = parent_ward_id
                library.library_accounting_code = accounting_code_id
                library.librarian_name = librarian_name
                library.contact_email = contact_email
                library.contact_phone = contact_phone
                library.about_library = about_library
                library.landing_page_link = landing_page_link
                library.membership_page_link = membership_page_link
                library.library_rules = library_rules
                library.membership_rules = membership_rules
                library.facebook_url = facebook_url
                library.twitter_url = twitter_url
                library.instagram_url = instagram_url
                library.youtube_url = youtube_url
                library.capacity = capacity
                library.opening_hours = opening_hours
                library.location_url = location_url
                library.est_year = int(est_year) if est_year.isdigit() else None
                library.image_url = image_url
                library.is_active = bool(is_active)
                library.updated_by = request.user.id
                library.updated_at = timezone.now()
                library.save()

                # ------------------------
                # Sync with LibraryMaster (default DB)
                # ------------------------
                try:
                    # ------------------------
                    # Get related FK IDs from default DB
                    # ------------------------
                    location_obj_id = None
                    if location_id:
                        if not str(location_id).isdigit():
                            loc_obj = LibraryLocationMaster.objects.using("default").filter(location_name=location_id).first()
                            location_obj_id = loc_obj.location_id if loc_obj else None
                        else:
                            location_obj_id = int(location_id)

                    parent_ward_obj_id = None
                    if parent_ward_id:
                        if not str(parent_ward_id).isdigit():
                            ward_obj = WardMaster.objects.using("default").filter(ward_name=parent_ward_id).first()
                            parent_ward_obj_id = ward_obj.ward_id if ward_obj else None
                        else:
                            parent_ward_obj_id = int(parent_ward_id)

                    accounting_code_obj_id = None
                    if accounting_code_id:
                        if not str(accounting_code_id).isdigit():
                            ac_obj = WardMaster.objects.using("default").filter(accounting_code=accounting_code_id).first()
                            accounting_code_obj_id = ac_obj.ward_id if ac_obj else None
                        else:
                            accounting_code_obj_id = int(accounting_code_id)

                    # ------------------------
                    # Save to LibraryMaster (default DB)
                    # ------------------------
                    library_master, created = LibraryMaster.objects.using("default").get_or_create(
                        library_code=library_code,
                        defaults={
                            "library_name": library_name,
                            "library_name_mar": library_name_mar,
                            "location_id": location_obj_id,
                            "parent_ward_id": parent_ward_obj_id,
                            "library_accounting_code_id": accounting_code_obj_id,
                            "librarian_name": librarian_name,
                            "contact_email": contact_email,
                            "contact_phone": contact_phone,
                            "about_library": about_library,
                            "landing_page_link": landing_page_link,
                            "membership_page_link": membership_page_link,
                            "library_rules": library_rules,
                            "membership_rules": membership_rules,
                            "facebook_url": facebook_url,
                            "twitter_url": twitter_url,
                            "instagram_url": instagram_url,
                            "youtube_url": youtube_url,
                            "capacity": capacity,
                            "opening_hours": opening_hours,
                            "location_url": location_url,
                            "est_year": int(est_year) if est_year.isdigit() else None,
                            "image_url": image_url,
                            "is_active": bool(is_active),
                            "created_by": str(request.user.id),
                            "created_at": timezone.now(),
                            "updated_by": str(request.user.id),
                            "updated_at": timezone.now(),
                        }
                    )

                    if not created:
                        library_master.library_name = library_name
                        library_master.library_name_mar = library_name_mar
                        library_master.location_id = location_obj_id
                        library_master.parent_ward_id = parent_ward_obj_id
                        library_master.library_accounting_code_id = accounting_code_obj_id
                        library_master.librarian_name = librarian_name
                        library_master.contact_email = contact_email
                        library_master.contact_phone = contact_phone
                        library_master.about_library = about_library
                        library_master.landing_page_link = landing_page_link
                        library_master.membership_page_link = membership_page_link
                        library_master.library_rules = library_rules
                        library_master.membership_rules = membership_rules
                        library_master.facebook_url = facebook_url
                        library_master.twitter_url = twitter_url
                        library_master.instagram_url = instagram_url
                        library_master.youtube_url = youtube_url
                        library_master.capacity = capacity
                        library_master.opening_hours = opening_hours
                        library_master.location_url = location_url
                        library_master.est_year = int(est_year) if est_year.isdigit() else None
                        library_master.image_url = image_url
                        library_master.is_active = bool(is_active)
                        library_master.updated_by = str(request.user.id)
                        library_master.updated_at = timezone.now()
                        library_master.save(using="default")

                except Exception as ex:
                    import traceback
                    print("Error syncing LibraryMaster:", ex)
                    print(traceback.format_exc())

                messages.success(request, f"Library '{library_name}' saved successfully!")

            # ------------------------
            # After saving, reload page with updated values
            # ------------------------
            if library_code:
                library = tbl_librarymasterL01.objects.get(library_code=library_code)

        # ------------------------ GET request or after POST ----------------
        library_code = request.session.get("library_db", None)
        if library_code:
            library_details = LibraryMaster.objects.using("default").filter(is_active=1, library_code=library_code)
            for lilo in library_details:
                lilo.libraries = enc(lilo.library_code)
            if library_details.exists() and not library:
                library = library_details.first()
                library_name = library.library_name
        else:
            library_details = LibraryMaster.objects.using("default").filter(is_active=1)

        ward_code = request.session.get("ward_db", None)
        if ward_code:
            ward_details = WardMaster.objects.using("default").filter(is_active=1, ward_code=ward_code)
            for w in ward_details:
                w.wards = enc(w.ward_code)
            ward_name = ward_details.first().ward_name if ward_details.exists() else ""
        else:
            ward_details = WardMaster.objects.using("default").filter(is_active=1)

        location_code = request.session.get("location_db", None)
        if location_code:
            location_details = LibraryLocationMaster.objects.using("default").filter(is_active=1, location_code=location_code)
            for loc in location_details:
                loc.locations = enc(loc.location_code)
            location_name = location_details.first().location_name if location_details.exists() else ""
        else:
            location_details = LibraryLocationMaster.objects.using("default").filter(is_active=1)

        accounting_code = request.session.get("accounting_code_db", None)
        if accounting_code:
            accounting_code_details = WardMaster.objects.using("default").filter(is_active=1, accounting_code=accounting_code)
            for ac in accounting_code_details:
                ac.codes = enc(ac.accounting_code)
            accounting_code_name = accounting_code_details.first().accounting_code if accounting_code_details.exists() else ""
        else:
            accounting_code_details = WardMaster.objects.using("default").filter(is_active=1)

        return render(
            request,
            "L01/Master/library_master_index_individual.html",
            {
                "library": library,
                "libraries": library_details,
                "wards": ward_details,
                "locations": location_details,
                "accounting_codes": accounting_code_details,
                "library_name": library_name,
                "ward_name": ward_name,
                "location_name": location_name,
                "accounting_code_name": accounting_code_name,
                "MEDIA_URL": settings.MEDIA_URL,
            },
        )

    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        fun = tb[0].name if tb else 'library_list'
        cursor.callproc("stp_error_log", [fun, str(e), library_code])
        print(f"error: {e}")
        messages.error(request, 'Oops...! Something went wrong!')

@login_required
def user_master_index(request):
    try:
        if request.user.is_authenticated:
            global user, role_id
            user = request.user.id
            role_id = request.user.role_id

        if request.method == "GET":
            # 🔹 Fetch all user records with related role
            users = CustomUser.objects.all()

            # 🔹 Attach encrypted_id & role_name for each user
            for usr in users:
                usr.encrypted_id = enc(str(usr.id))

                try:
                    role = roles.objects.get(id=usr.id)
                    usr.role_name = role.role_name
                except roles.DoesNotExist:
                    usr.role_name = "N/A"

            return render(
                request,
                'L01/Master/user_master_index.html',
                {"users": users}
            )

    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        fun = tb[0].name
        callproc("stp_error_log", [fun, str(e), user])
        messages.error(request, 'Oops...! Something went wrong!')
        return redirect("user_master_index")

@login_required
def update_user_status(request):
    if request.method == "POST":
        try:
            print("Request body raw:", request.body)
            try:
                data = json.loads(request.body.decode("utf-8"))
            except (json.JSONDecodeError, UnicodeDecodeError) as e:
                print("JSON parse error:", e)
                return JsonResponse({"success": False, "error": "Invalid JSON"}, status=400)

            print("Parsed data:", data)

            encrypted_id = data.get("id")
            is_active = data.get("status")

            if encrypted_id is None or is_active is None:
                return JsonResponse({"success": False, "error": "Missing data"}, status=400)

            user_id = int(dec(encrypted_id))
            user = CustomUser.objects.get(id=user_id)
            user.is_active = bool(int(is_active))
            user.save()

            return JsonResponse({"success": True, "status": int(user.is_active)})

        except CustomUser.DoesNotExist:
            return JsonResponse({"success": False, "error": "User not found"}, status=404)
        except Exception as e:
            print("❌ Error:", e)
            return JsonResponse({"success": False, "error": str(e)}, status=400)

    return JsonResponse({"success": False, "error": "Invalid request"}, status=400)

@login_required
def user_create(request):
    try:
        user_id = request.user.id

        if request.method == "POST":

            enc_id = request.POST.get("id")  # Hidden encrypted ID (for editing)
            username = request.POST.get("username", "").strip()
            first_name = request.POST.get("first_name", "").strip()
            last_name = request.POST.get("last_name", "").strip()
            full_name = f"{first_name} {last_name}".strip()  # auto-generate full name
            email = request.POST.get("email", "").strip()
            phone = request.POST.get("mobile", "").strip()  # ✅ Added phone
            role_id = request.POST.get("role_id", "").strip()
            is_active = request.POST.get("is_active", 1)
            password = request.POST.get("password", "").strip()

            # 🔹 Validation
            if not username:
                messages.error(request, "User Name is required!")
            elif not first_name:
                messages.error(request, "First Name is required!")
            elif not last_name:
                messages.error(request, "Last Name is required!")
            elif not email:
                messages.error(request, "Email is required!")
            elif not phone:
                messages.error(request, "Phone Number is required!")  # ✅ Validation added
            elif not role_id:
                messages.error(request, "Role is required!")
            elif not enc_id and not password:
                messages.error(request, "Password is required for new user!")

            # If there were validation errors → re-render form
            if messages.get_messages(request):
                roles_list = roles.objects.exclude(role_type='member')
                return render(request, "L01/Master/user_create.html", {
                    "roles_list": roles_list,
                    "post_data": request.POST,
                    "user_obj": None
                })

            # 🔹 Update existing user
            if enc_id:
                try:
                    user_pk = int(dec(enc_id))
                    user_obj = CustomUser.objects.get(pk=user_pk)

                    user_obj.username = username
                    user_obj.first_name = first_name
                    user_obj.last_name = last_name
                    user_obj.full_name = full_name
                    user_obj.email = email
                    user_obj.phone = phone  # ✅ Save phone
                    user_obj.is_active = bool(int(is_active))
                    user_obj.role_id = role_id   # direct field in CustomUser
                    user_obj.updated_by = user_id
                    user_obj.updated_at = timezone.now()

                    if password:
                        user_obj.set_password(password)

                    user_obj.save()

                    messages.success(request, f"User '{username}' updated successfully!")
                    return redirect("L01:user_master_index")

                except CustomUser.DoesNotExist:
                    messages.error(request, "User not found.")
                    return redirect("L01:user_master_index")

            # 🔹 Create new user
            new_user = CustomUser.objects.create_user(
                username=username,
                email=email,
                password=password,
                is_active=bool(int(is_active))
            )
            new_user.first_name = first_name
            new_user.last_name = last_name
            new_user.full_name = full_name
            new_user.phone = phone  # ✅ Save phone
            new_user.role_id = role_id
            new_user.created_by = user_id
            new_user.created_at = timezone.now()
            new_user.save()

            messages.success(request, f"User '{username}' created successfully!")
            return redirect("L01:user_master_index")

        # GET → Show form, exclude 'member' roles
        roles_list = roles.objects.exclude(role_type='member')
        return render(request, "L01/Master/user_create.html", {
            "roles_list": roles_list,
            "user_obj": None
        })

    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        fun = tb[0].name
        callproc("stp_error_log", [fun, str(e), user_id])
        messages.error(request, 'Oops...! Something went wrong!')
        return redirect("L01:user_master_index")

@login_required
def user_edit(request):
    try:
        user_id = request.user.id

        # 🔹 Read from query string or hidden field
        enc_id = request.GET.get("user_id") or request.POST.get("id")
        if not enc_id:
            messages.error(request, "Invalid user reference.")
            return redirect("L01:user_master_index")

        user_pk = int(dec(enc_id))  # Decrypt the ID

        # 🔹 Fetch user or show error
        try:
            user_obj = CustomUser.objects.get(pk=user_pk)
        except CustomUser.DoesNotExist:
            messages.error(request, "User not found.")
            return redirect("L01:user_master_index")

        if request.method == "POST":
            username = request.POST.get("username", "").strip()
            first_name = request.POST.get("first_name", "").strip()
            last_name = request.POST.get("last_name", "").strip()
            full_name = f"{first_name} {last_name}".strip()
            email = request.POST.get("email", "").strip()
            phone = request.POST.get("mobile", "").strip()
            role_id = request.POST.get("role_id", "").strip()
            is_active = request.POST.get("is_active", 1)
            password = request.POST.get("password", "").strip()
            confirm_password = request.POST.get("confirm_password", "").strip()
            address = request.POST.get("address", "").strip()

            # 🔹 Validation
            if not username:
                messages.error(request, "User Name is required!")
            elif not first_name:
                messages.error(request, "First Name is required!")
            elif not last_name:
                messages.error(request, "Last Name is required!")
            elif not email:
                messages.error(request, "Email is required!")
            elif not phone:
                messages.error(request, "Phone Number is required!")
            elif not role_id:
                messages.error(request, "Role is required!")
            elif password and password != confirm_password:
                messages.error(request, "Passwords do not match!")

            # If errors → re-render with form data
            if messages.get_messages(request):
                roles_list = roles.objects.exclude(role_type="member")
                return render(request, "L01/Master/user_edit.html", {
                    "roles_list": roles_list,
                    "post_data": request.POST,
                    "user_obj": user_obj
                })

            # 🔹 Update user
            user_obj.username = username
            user_obj.first_name = first_name
            user_obj.last_name = last_name
            user_obj.full_name = full_name
            user_obj.email = email
            user_obj.phone = phone
            user_obj.address = address
            user_obj.password = password
            user_obj.confirm_password = confirm_password
            user_obj.is_active = bool(int(is_active))
            user_obj.role_id = role_id
            user_obj.updated_by = user_id
            user_obj.updated_at = timezone.now()

            if password:
                user_obj.set_password(password)

            user_obj.save()

            messages.success(request, f"User '{username}' updated successfully!")
            return redirect("L01:user_master_index")

        # GET → load edit form
        roles_list = roles.objects.exclude(role_type="member")
        return render(request, "L01/Master/user_edit.html", {
            "roles_list": roles_list,
            "user_obj": user_obj
        })

    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        fun = tb[0].name
        callproc("stp_error_log", [fun, str(e), user_id])
        messages.error(request, "Oops...! Something went wrong!")
        return redirect("L01:user_master_index")

@login_required
def user_view(request):
    try:
        user_id = request.user.id

        enc_id = request.GET.get("user_id")
        if not enc_id:
            messages.error(request, "Invalid user reference.")
            return redirect("L01:user_master_index")

        user_pk = int(dec(enc_id))  # Decrypt ID

        try:
            user_obj = CustomUser.objects.get(pk=user_pk)
        except CustomUser.DoesNotExist:
            messages.error(request, "User not found.")
            return redirect("L01:user_master_index")

        # Fetch the role object using role_id
        role_obj = roles.objects.filter(id=user_obj.role_id).first()

        return render(request, "L01/Master/user_view.html", {
            "user_obj": user_obj,
            "role_obj": role_obj
        })

    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        fun = tb[0].name
        callproc("stp_error_log", [fun, str(e), user_id])
        messages.error(request, "Oops...! Something went wrong!")
        return redirect("L01:user_master_index")
