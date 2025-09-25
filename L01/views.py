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
import re
from django.shortcuts import render, redirect
from django.db import transaction
import os
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
            }
                
            return render(request, template, context)
        
        if request.method == "POST":
            membership_id = request.POST.get("membership_id")
            action = request.POST.get("action")  # approve / reject

            membership = get_object_or_404(MembershipDetails, id=membership_id, isactive=1)

            # Map actions to status IDs
            status_map = {
                "approved": 2,  # APPROVED
                "rejected": 3,   # REJECT
            }
            new_status_id = status_map.get(action)

            if new_status_id:
                membership.actionperformed = action
                membership.reviewed = user_code
                membership.reviewed_at = timezone.now()
                membership.status_id = new_status_id  # update status foreign key
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