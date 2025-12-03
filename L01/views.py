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
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q
import json
from django.shortcuts import render, get_object_or_404
from django.shortcuts import render, get_object_or_404
from django.conf import settings
from .models import CompetitiveExamMaster, Sections, Subjects, Topics, Chapters 
from .models import BookCatalog
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
from Masters.models import *
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
from datetime import datetime, date, timedelta
from django.http import JsonResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404
import barcode
from barcode.writer import ImageWriter
import base64
from django.core.exceptions import ObjectDoesNotExist
logger = logging.getLogger(__name__)
from django.db import transaction as db_transaction
from PIL import Image, ImageDraw, ImageFont
from barcode import Code128
from reportlab.lib.utils import ImageReader
from django.db.models import IntegerField
from django.db.models.functions import Cast
from django.db.models import Value, CharField
from django.db.models.functions import Concat
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader
from PIL import Image, ImageFont, ImageDraw
from django.core.paginator import Paginator
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

# Part First While Filling Membership Form

def index(request):
    # Get the library code from session
    library_code = request.session.get('library_db', None)

    if library_code:
        library_details = LibraryMaster.objects.using('default').filter(
            is_active=1, 
            library_code=library_code
        )

        for lilo in library_details:

            encrypted_library_code = enc(lilo.library_code)
            lilo.libraries = encrypted_library_code

            # -------------------------------------------
            # FETCH RECENT 5 BOOKS
            # -------------------------------------------
            books = BookCatalog.objects.filter(status_id=1).order_by('-cat_ref_num')[:5]

            lilo.books = [
                {
                    "title": book.title or "Untitled",
                    "subtitle": book.subtitle or "",
                    "author": book.author or "Unknown",
                    "publisher": book.publisher or "",
                    "isbn_issn": book.isbn_issn or "",
                    "edition": book.edition or "",
                    "publication_place": book.publication_place or "",
                    "year_of_publication": book.year_of_publication or "N/A",
                    "pages": book.pages or "",
                    "language": book.language or "Unknown",
                    "front_page_photo": book.front_page_photo if book.front_page_photo else "",
                    "last_page_photo": book.last_page_photo if book.last_page_photo else "",
                    "remarks": book.remarks or "",
                    "description": book.remarks or "No description available.",
                    "ebook_available": book.ebook_available or "No"   # ⭐ ADDED LINE
                }
                for book in books
            ]

            # -------------------------------------------
            # FETCH RECENT 5 EBOOKS
            # -------------------------------------------
            ebooks = LibraryEbook.objects.filter(eb_status_id=1).order_by('-ebook_id')[:5]

            lilo.ebooks = [
                {
                    "eb_title": ebook.eb_title or "Untitled",
                    "eb_subtitle": ebook.eb_subtitle or "",
                    "eb_author": ebook.eb_author or "Unknown",
                    "eb_publisher": ebook.eb_publisher or "",
                    "eb_isbn_issn": ebook.eb_isbn_issn or "",
                    "eb_edition": ebook.eb_edition or "",
                    "eb_publication_place": ebook.eb_publication_place or "",
                    "eb_year_of_publication": ebook.eb_year_of_publication or "N/A",
                    "eb_pages": ebook.eb_pages or "",
                    "eb_language": ebook.eb_language or "Unknown",
                    "eb_front_page_photo": ebook.eb_front_page_photo if ebook.eb_front_page_photo else "",
                    "eb_last_page_photo": ebook.eb_last_page_photo if ebook.eb_last_page_photo else "",
                    "remarks": ebook.remarks or "",
                    "description": ebook.eb_keywords or "No description available.",
                    "eb_pdf_url": ebook.eb_pdf_url or "",
                    "encrypted_ebook_id": enc(str(ebook.ebook_id)),
                    "encrypted_pdf_url": enc(ebook.eb_pdf_url or ""),
                }
                for ebook in ebooks
            ]

        library_name = library_details.first().library_name if library_details.exists() else ""

    else:
        # -------------------------------------------
        # WHEN NO LIBRARY IS SELECTED
        # -------------------------------------------
        library_details = LibraryMaster.objects.using('default').filter(is_active=1)

        for lilo in library_details:

            # --- Books fetch ---
            books = BookCatalog.objects.filter(status_id=1).order_by('-cat_ref_num')[:5]

            lilo.books = [
                {
                    "title": book.title or "Untitled",
                    "subtitle": book.subtitle or "",
                    "author": book.author or "Unknown",
                    "publisher": book.publisher or "",
                    "isbn_issn": book.isbn_issn or "",
                    "edition": book.edition or "",
                    "publication_place": book.publication_place or "",
                    "year_of_publication": book.year_of_publication or "N/A",
                    "pages": book.pages or "",
                    "language": book.language or "Unknown",
                    "front_page_photo": book.front_page_photo if book.front_page_photo else "",
                    "last_page_photo": book.last_page_photo if book.last_page_photo else "",
                    "remarks": book.remarks or "",
                    "description": book.remarks or "No description available.",
                    "ebook_available": book.ebook_available or "No"   # ⭐ ADDED LINE
                }
                for book in books
            ]

            # --- eBooks fetch ---
            ebooks = LibraryEbook.objects.filter(eb_status_id=1).order_by('-ebook_id')[:5]

            lilo.ebooks = [
                {
                    "eb_title": ebook.eb_title or "Untitled",
                    "eb_subtitle": ebook.eb_subtitle or "",
                    "eb_author": ebook.eb_author or "Unknown",
                    "eb_publisher": ebook.eb_publisher or "",
                    "eb_isbn_issn": ebook.eb_isbn_issn or "",
                    "eb_edition": ebook.eb_edition or "",
                    "eb_publication_place": ebook.eb_publication_place or "",
                    "eb_year_of_publication": ebook.eb_year_of_publication or "N/A",
                    "eb_pages": ebook.eb_pages or "",
                    "eb_language": ebook.eb_language or "Unknown",
                    "eb_front_page_photo": ebook.eb_front_page_photo if ebook.eb_front_page_photo else "",
                    "eb_last_page_photo": ebook.eb_last_page_photo if ebook.eb_last_page_photo else "",
                    "remarks": ebook.remarks or "",
                    "description": ebook.eb_keywords or "No description available.",
                    "eb_pdf_url": ebook.eb_pdf_url or "",
                    "encrypted_ebook_id": enc(str(ebook.ebook_id)),
                    "encrypted_pdf_url": enc(ebook.eb_pdf_url or ""),
                }
                for ebook in ebooks
            ]

        library_name = ""

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
            # ward = WardMaster.objects.using('default').get(ward_name=wardname, is_active=1)
            ward = WardMaster.objects.get(ward_name=wardname, is_active=1)
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
                    
                    # ward_details = WardMaster.objects.using('default').filter(is_active=1)
                    ward_details = WardMaster.objects.filter(is_active=1)
                    
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
                    
                    membertype = request.POST.get("membertype")

                    # Default education field
                    education_value = request.POST.get("education") or None

                    # Override if membertype == 5
                    if membertype == "5":
                        education_value = request.POST.get("practitioner_details") or None
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
                        "other_ward": request.POST.get("custom_ward_name") if request.POST.get("ward_name") == "Other" else None,
                        "pincode": (request.POST.get("custom_pincode") if request.POST.get("ward_name") == "Other" else request.POST.get("pincode")) or None,
                        "library_name": request.POST.get("library_name") or None,
                        "library_name_mar": request.POST.get("library_name_mar") or None,
                        "local_address": request.POST.get("local_address") or None,
                        "mobile_no": request.POST.get("mobile_number") or None,
                        "occupation": request.POST.get("occupation_details") or None,
                        "office_phone": request.POST.get("phone_number") or None,
                        "education": education_value,  # ✅ dynamic based on membertype
                        "institute_name": request.POST.get("institution_name") or None,
                        "recommender_details": request.POST.get("referrer_details") or None,
                        "member_type_id": membertype or None,
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
                            timestamp = datetime.now().strftime("%Y%m%dT%H%M%S")
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
                    # if CustomUser.objects.filter(email=data.get("email")).exists():
                    #     raise ValueError(f"❌ Email '{data.get('email')}' already exists!")

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

        # memberships = (MembershipDetails.objects.select_related("status").all().order_by("-created_at"))
        memberships = (
            MembershipDetails.objects
            .select_related("status")
            .all()
            .order_by("-updated_at")
        )

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
                    
                    # ward_details = WardMaster.objects.using('default').filter(is_active=1)
                    ward_details = WardMaster.objects.filter(is_active=1)
                    
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
                    
                    membertype = request.POST.get("membertype")

                    # Default education field
                    education_value = request.POST.get("education") or None

                    # Override if membertype == 5
                    if membertype == "5":
                        education_value = request.POST.get("practitioner_details") or None
                        
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
                        "other_ward": request.POST.get("custom_ward_name") if request.POST.get("ward_name") == "Other" else None,
                        "pincode": (request.POST.get("custom_pincode") if request.POST.get("ward_name") == "Other" else request.POST.get("pincode")) or None,
                        "library_name": request.POST.get("library_name") or None,
                        "library_name_mar": request.POST.get("library_name_mar") or None,
                        "local_address": request.POST.get("local_address") or None,
                        "mobile_no": request.POST.get("mobile_number") or None,
                        "occupation": request.POST.get("occupation_details") or None,
                        "office_phone": request.POST.get("phone_number") or None,
                        "education": education_value,  # ✅ dynamic based on membertype
                        "institute_name": request.POST.get("institution_name") or None,
                        "recommender_details": request.POST.get("referrer_details") or None,
                        "member_type_id": membertype or None,
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
                    
                    # if MembershipDetails.objects.filter(email=data.get("email")).exists():
                    #     messages.error(request, f"❌ ई-मेल '{data.get('email')}' आधी अस्तित्वात आहे!")
                    #     return redirect('L01:membership_form_create')

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
                            # timestamp = datetime.datetime.now().strftime("%Y%m%dT%H%M%S")
                            timestamp = datetime.now().strftime("%Y%m%dT%H%M%S")
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
                    
                    # if CustomUser.objects.filter(email=data.get("email")).exists():
                    #     messages.error(request, f"❌ ई-मेल '{data.get('email')}' आधी अस्तित्वात आहे!")
                    #     return redirect('L01:membership_form_create')  # go back to the form

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
                    
                    # ward_details = WardMaster.objects.using('default').filter(is_active=1)
                    ward_details = WardMaster.objects.filter(is_active=1)
                    
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
                
                membertype = request.POST.get("membertype")

                # Default: get education value
                education_value = request.POST.get("education") or None

                # Override education if membertype == 5
                if membertype == "5":
                    education_value = request.POST.get("practitioner_details") or None
                    
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
                
                # --- Handle Ward & Pincode (including "Other") ---
                ward_name = request.POST.get("ward_name")
                custom_ward = request.POST.get("custom_ward_name")
                custom_pincode = request.POST.get("custom_pincode")
                dropdown_pincode = request.POST.get("pincode")

                membership.ward = ward_name or None
                membership.other_ward = custom_ward if ward_name == "Other" else None
                membership.pincode = (custom_pincode if ward_name == "Other" else dropdown_pincode) or None
                updated = True  # mark as updated if any ward-related change
                
                date_fields = ["dob", "from_date", "to_date"]

                for form_field, model_field in field_map.items():
                    # new_value = request.POST.get(form_field)
                    if form_field == "education":
                        new_value = education_value
                    else:
                        new_value = request.POST.get(form_field)
                        
                    old_value = getattr(membership, model_field, None)

                    # --- Boolean-like fields ---
                    if model_field in ["is_resident_of_nmmc", "address_same_as_aadhar"]:
                        if new_value is not None:
                            new_value = 1 if str(new_value).lower() in ["1", "yes", "true", "on"] else 0
                        else:
                            new_value = None

                    # --- Integer fields ---
                    elif model_field == "membership_duration":
                        new_value = int(new_value) if new_value else None

                    # --- ForeignKey fields ---
                    elif model_field in ["membership_id", "member_type_id"]:
                        new_value = int(new_value) if new_value else None

                    # --- Date fields ---
                    elif model_field in date_fields:
                        if new_value:
                            try:
                                # Ensure we only keep date part
                                new_value = datetime.strptime(new_value.split(" ")[0], "%Y-%m-%d").date()
                            except Exception as e:
                                print("❌ Date parse error for", form_field, ":", new_value, "->", e)
                                new_value = None
                        else:
                            new_value = None

                    # --- Default ---
                    else:
                        new_value = new_value.strip() if isinstance(new_value, str) else new_value

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
                    
                    # ward_details = WardMaster.objects.using('default').filter(is_active=1)
                    ward_details = WardMaster.objects.filter(is_active=1)
                    
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

            if action == "payment_received":
                try:
                    with transaction.atomic():
                        payment_type = "Membership Renewed" if membership.membership_renew == 1 else "Membership"

                        status_received = StatusMaster.objects.get(id=5)
                        membership_master = membership.membership

                        # Step 1: Create PaymentDetails
                        PaymentDetails.objects.create(
                            membership=membership,
                            payment_mode="Offline",
                            payment_method="Cash/Cheque/Other",
                            payment_type=payment_type,
                            deposit_amount=membership.deposit,
                            entry_fee_amount=membership.entry_fees,
                            monthly_subscription_amount=membership_master.subscription_fees,
                            total_subscription_amount=membership.subscription,
                            subscription_from=membership.from_date,
                            subscription_to=membership.to_date,
                            status=status_received,
                            membership_code=membership.membership_code,
                            user_id=user_id,
                            created_by=user_code,
                            updated_by=user_code,
                            payment_date=timezone.now().date(),
                        )

                        # Step 2: Update MembershipDetails
                        membership.status = status_received
                        membership.membership_renew = 0
                        membership.updated_by = user_code
                        membership.save()

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
                            new_number_str = str(new_number).zfill(3)

                            membership_code = f"{increment_master.incrementFieldName}{new_number_str}"

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
            
            today = date.today()
            
            # member's membershp details
            memberships = (
                MembershipDetails.objects
                .select_related("status", "membership")
                .filter(user_id=username)
            )
            for mem in memberships:
                mem.membership_id_enc = enc(str(mem.id))        
                mem.per_month_subscription = mem.membership.subscription_fees if mem.membership else 0
                
                mem.show_renew_button = (
                    mem.to_date is not None and mem.to_date == today
                )
                
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
                    
                    # ward_details = WardMaster.objects.using('default').filter(is_active=1)
                    ward_details = WardMaster.objects.filter(is_active=1)
                    
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
                membership = get_object_or_404(MembershipDetails, id=membership_id)

                updated = False

                # 1️⃣ Field map (only relevant fields)
                field_map = {
                    "membershiptype": "membership_id",
                    "months": "membership_duration",
                    "fromDate": "from_date",
                    "toDate": "to_date",
                }

                # 2️⃣ Detect field changes
                for form_field, model_field in field_map.items():
                    new_value = request.POST.get(form_field)

                    if new_value in ["", "None", None]:
                        new_value = None

                    if model_field == "membership_duration" and new_value:
                        new_value = int(new_value)

                    if model_field == "membership_id" and new_value:
                        new_value = int(new_value)

                    if model_field in ["from_date", "to_date"] and new_value:
                        new_value = datetime.strptime(new_value, "%Y-%m-%d").date()

                    old_value = getattr(membership, model_field, None)
                    if new_value != old_value:
                        setattr(membership, model_field, new_value)
                        updated = True

                # 3️⃣ Monetary fields
                money_fields = ["deposit", "entry_fees", "subscription"]
                for field in money_fields:
                    new_value = request.POST.get(field)
                    new_value = float(new_value) if new_value else 0.0
                    old_value = getattr(membership, field, 0.0)
                    if new_value != old_value:
                        setattr(membership, field, new_value)
                        updated = True
                        
                if updated:
                    MembershipDetailsHistory.objects.create(
                        membership=membership,
                        membershipmaster=membership.membership,  # ✅ FIXED
                        status=membership.status,
                        member_type=membership.member_type,
                        first_name=membership.first_name,
                        middle_name=membership.middle_name,
                        last_name=membership.last_name,
                        first_name_mar=membership.first_name_mar,
                        middle_name_mar=membership.middle_name_mar,
                        last_name_mar=membership.last_name_mar,
                        ward=membership.ward,
                        other_ward=membership.other_ward,
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
                        actionperformed=membership.actionperformed,
                        reviewed=membership.reviewed,
                        reviewed_at=membership.reviewed_at,
                        isactive=membership.isactive,
                        membership_code=membership.membership_code,
                        membership_renew=1,  # ✅ history flag
                        created_at=membership.created_at,
                        created_by=membership.created_by,
                        updated_at=membership.updated_at,
                        updated_by=membership.updated_by,
                        changed_by=user_code,
                    )

                # 4️⃣ Save if updated
                if updated:
                    membership.updated_by = user_code
                    membership.status_id = 9
                    membership.membership_renew = 1
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

@login_required
def membership_form_cancellation(request):
    Db.closeConnection()
    m = Db.get_connection()
    cursor = m.cursor()
    try:
        library_code = request.session.get('library_db', None)
        user_id = request.session.get("user_id")
        
        if request.method == "GET":
            try:
                membership_id_enc = request.GET.get("membership_id")
                membership_id = dec(membership_id_enc)

                membership = MembershipDetails.objects.select_related("membership", "status").get(id=membership_id)

                data = {
                    "id": membership.id,
                    "full_name": f"{membership.first_name or ''} {membership.middle_name or ''} {membership.last_name or ''}".strip(),
                    "membership_type": membership.membership.membership_type,
                    "membership_type_en": membership.membership.membership_type_en,
                    "deposit": membership.deposit,
                    "entry_fees": membership.entry_fees,
                    "subscription": membership.subscription,
                    "duration": membership.membership_duration,
                    "from_date": membership.from_date.strftime("%d-%m-%Y") if membership.from_date else None,
                    "to_date": membership.to_date.strftime("%d-%m-%Y") if membership.to_date else None,
                    "status_name": membership.status.status_name,
                }
                return JsonResponse({"success": True, "data": data})

            except MembershipDetails.DoesNotExist:
                return JsonResponse({"success": False, "message": "सदस्य माहिती सापडली नाही."})
            except Exception as e:
                print("Error fetching membership details:", e)
                return JsonResponse({"success": False, "message": "सर्व्हर त्रुटी आली."})

            return JsonResponse({"success": False, "message": "Invalid request method."})
        
        if request.method == "POST":
            
            membership_id = dec(request.POST.get("membership_id"))
            membership = get_object_or_404(MembershipDetails, id=membership_id)
            
            action_by = request.POST.get("action_by")  # 'member' or 'librarian'

            if action_by == "member":
                # ✅ Step 1: Member requests cancellation
                cancelled_status = StatusMaster.objects.filter(status_name__iexact="Application Cancelled").first()
                if not cancelled_status:
                    raise Exception("Cancelled status not found in StatusMaster.")

                membership.status = cancelled_status
                membership.updated_by = user_id
                membership.remarks = "Cancelled by Member (Pending Librarian Approval)"
                # membership.save()
                return redirect("L01:membership_payment_index")

            elif action_by == "librarian":
                # ✅ Step 2: Librarian confirms cancellation & deactivates user + membership
                membership.updated_by = user_id  # librarian’s ID (for audit)
                membership.remarks = "Cancellation Approved by Librarian"
                membership.isactive = 0  # deactivate membership record
                # membership.save()

                # Deactivate the member's user account (not librarian’s)
                member_user = CustomUser.objects.filter(username=membership.user_id).first()
                if member_user:
                    member_user.is_active = False
                    # member_user.save()

                return JsonResponse({"success": True, "message": "सदस्यत्व रद्द प्रक्रिया यशस्वीपणे पूर्ण झाली आहे."})

    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        fun = tb[0].name if tb else "membership_form_cancellation"
        cursor.callproc("stp_error_log", [fun, str(e), library_code])
        print(f"Error: {e}")
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
            
            # barcode for bulk download
            
            circulation_accessions = list(
                CirculationCopyStatus.objects
                .filter(accession_no__isnull=False)
                .values('id', 'accession_no', 'accession_id')
            )

            for circ in circulation_accessions:
                circ['accession_encrypted_no'] = enc(str(circ['accession_no']))
                
            subjectNames = SubjectTypeMaster.objects.filter(is_active=1)
            for sub in subjectNames:
                sub.subjectIdEnc = enc(str(sub.id))
                
            location_list = ResourceLocationMaster.objects.filter(is_active=1)

            for loc in location_list:
                loc.locationEnc = enc(str(loc.location_id))
                loc.full_name = f"{loc.location_code} - {loc.location_name}"
        
            return render(
                request,
                "L01/Circulation/barcodeindex.html",
                {
                    "MEDIA_URL": settings.MEDIA_URL,
                    "library_code": library_code,
                    "accessions": accessions,
                    "circulation_accessions": circulation_accessions,
                    "subjectNames": subjectNames,
                    "location_list": location_list,
                    
                }
            )
        
        # In your barcode generation code, replace Marathi text with English:
        if request.method == "POST":
            if library_code:
                library_details = tbl_librarymasterL01.objects.filter(library_code=library_code).first()
                if not library_details:
                    return HttpResponseBadRequest("Invalid library code")
                library_location = library_details.location
            else:
                return HttpResponseBadRequest("Missing library code")

            # Decode accession numbers
            from_acc = dec(str(request.POST.get("from_accession")))
            to_acc = dec(str(request.POST.get("to_accession")))
            subject_id = request.POST.get("subject_id")
            location_id = request.POST.get("location_id")

            if subject_id:
                subject_id = dec(str(subject_id))
            if location_id:
                location_id = dec(str(location_id))

            if not from_acc or not to_acc:
                return JsonResponse({"error": "Missing fields"}, status=400)

            # Get circulation records
            circulation_qs = (
                CirculationCopyStatus.objects
                .select_related("bookcatalog", "bookcatalog__subject", "shelf_location")
                .annotate(barcode_int=Cast("barcode", IntegerField()))
                .filter(barcode_int__range=(int(from_acc), int(to_acc)))
                .order_by("barcode_int")
            )
            if subject_id:
                circulation_qs = circulation_qs.filter(bookcatalog__subject_id=subject_id)
            if location_id:
                circulation_qs = circulation_qs.filter(shelf_location=location_id)
            if not circulation_qs.exists():
                return JsonResponse({"error": "No matching records found"}, status=404)

            # PDF setup
            pdf_buffer = BytesIO()
            # TSC TE244: 50mm × 25mm, 203 DPI → 141.73 x 70.87 points
            label_width_pt = 50 * 2.83465
            label_height_pt = 25 * 2.83465

            p = canvas.Canvas(pdf_buffer, pagesize=(label_width_pt, label_height_pt))

            # Font path for Marathi
            font_path = os.path.join(settings.BASE_DIR, "static", "fonts", "NotoSerifDevanagari-Bold.ttf")

            for idx, record in enumerate(circulation_qs):
                accession_no = record.accession_no or "UNKNOWN"
                
                # Get subject name and location
                subject_name = ""
                if record.bookcatalog and record.bookcatalog.subject:
                    subject_name = record.bookcatalog.subject.subjectNameMarathi or ""
                
                location_name = ""
                if record.shelf_location:
                    location_name = record.shelf_location.location_name or ""

                # Create label image (50x25 mm → 400x200 px at 203 DPI)
                img_width = 400
                img_height = 200
                label_img = Image.new("RGB", (img_width, img_height), "white")
                draw = ImageDraw.Draw(label_img)

                # Load fonts with larger sizes
                try:
                    font_large = ImageFont.truetype(font_path, 28)
                    font_medium = ImageFont.truetype(font_path, 28)
                    font_small = ImageFont.truetype(font_path, 28)
                except:
                    font_large = ImageFont.load_default()
                    font_medium = ImageFont.load_default()
                    font_small = ImageFont.load_default()

                # Draw text content
                line1 = "नवी मुंबई महानगरपालिका"  # NMMC in Marathi
                line2 = f"{library_location} - {library_code}"
                
                # Generate barcode with larger size
                barcode_buffer = BytesIO()
                barcode_obj = Code128(accession_no, writer=ImageWriter())
                barcode_obj.write(barcode_buffer, {
                    "module_width": 0.32,
                    "module_height": 35,
                    "quiet_zone": 1.5,
                    "write_text": False,
                    "dpi": 203,
                })
                barcode_buffer.seek(0)
                barcode_img = Image.open(barcode_buffer)
                if barcode_img.mode != "RGB":
                    barcode_img = barcode_img.convert("RGB")
                barcode_img = barcode_img.resize((350, 50), Image.Resampling.LANCZOS)

                # Line 4: Accession no - Subject - Location
                line4 = f"{accession_no} - {subject_name} - {location_name}"

                # Calculate text dimensions
                bbox1 = draw.textbbox((0, 0), line1, font=font_large)
                text_height1 = bbox1[3] - bbox1[1]
                
                bbox2 = draw.textbbox((0, 0), line2, font=font_medium)
                text_height2 = bbox2[3] - bbox2[1]
                
                bbox4 = draw.textbbox((0, 0), line4, font=font_small)
                text_height4 = bbox4[3] - bbox4[1]

                # Calculate total content height and starting position for perfect centering
                total_content_height = text_height1 + 8 + text_height2 + 10 + 50 + 8 + text_height4
                start_y = (img_height - total_content_height) // 2

                # Line 1: Center aligned horizontally
                text_width1 = bbox1[2] - bbox1[0]
                line1_x = (img_width - text_width1) // 2
                line1_y = start_y
                draw.text((line1_x, line1_y), line1, font=font_large, fill="black")

                # Line 2: Center aligned horizontally
                text_width2 = bbox2[2] - bbox2[0]
                line2_x = (img_width - text_width2) // 2
                line2_y = line1_y + text_height1 + 8
                draw.text((line2_x, line2_y), line2, font=font_medium, fill="black")

                # Line 3: Barcode - perfectly centered horizontally
                barcode_x = (img_width - 350) // 2
                barcode_y = line2_y + text_height2 + 10
                label_img.paste(barcode_img, (barcode_x, barcode_y))

                # Line 4: Center aligned horizontally
                text_width4 = bbox4[2] - bbox4[0]
                line4_x = (img_width - text_width4) // 2
                line4_y = barcode_y + 50 + 8
                draw.text((line4_x, line4_y), line4, font=font_small, fill="black")

                # Convert label image to PDF page
                temp_buffer = BytesIO()
                label_img.save(temp_buffer, format="PNG", dpi=(203, 203))
                temp_buffer.seek(0)
                p.drawImage(ImageReader(temp_buffer), 0, 0, width=label_width_pt, height=label_height_pt)

                if idx < len(circulation_qs) - 1:
                    p.showPage()

            p.save()
            pdf_buffer.seek(0)
            filename = f"{from_acc}_to_{to_acc}_barcodes.pdf"
            response = HttpResponse(pdf_buffer, content_type="application/pdf")
            response['Content-Disposition'] = f'inline; filename="{filename}"'
            return response
        
    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        fun = tb[0].name if tb else "library_list"
        cursor.callproc("stp_error_log", [fun, str(e), library_code])
        print(f"error: {e}")
        messages.error(request, "Oops...! Something went wrong!")
        return render(request, "L01/Circulation/barcodeindex.html", {})

@login_required
def generate_barcode(request):
    try:
        # Database connection
        Db.closeConnection()
        m = Db.get_connection()
        cursor = m.cursor()

        # Session variables
        library_code = request.session.get('library_db', None)
        username = request.session.get('username', None)
        user_id = request.session.get("user_id")
        role_id = request.session.get("role_id")

        # 🔹 GET: Generate barcode
        if request.method == "GET":
            
            place = request.GET.get("place")
            
            if place:
                
                books_qs = CirculationCopyStatus.objects.filter(shelf_location__isnull=True).select_related('accession', 'accession__catalogue')
                books = []
                for b in books_qs:
                    accession_no = b.accession.accession_no if b.accession else ''
                    title = b.accession.catalogue.title if b.accession and b.accession.catalogue else ''
                    label = f"{accession_no} - {title}"
                    books.append({'accession_id': b.accession_id, 'accession_no': b.accession_no, 'label': label})

                # Fetch active locations
                locations_qs = ResourceLocationMaster.objects.filter(is_active=1)
                locations = [{'location_id': loc.location_id, 'location_name': loc.location_name} for loc in locations_qs]

                return JsonResponse({'books': books, 'locations': locations})
            
            else:
                
                if library_code: 
                    library_details = tbl_librarymasterL01.objects.filter(library_code=library_code).first() 
                    library_location = library_details.location 
                else:
                    library_location = None
                    return HttpResponseBadRequest("Invalid library code")
                
                accession_id = request.GET.get("accessionid")
                if not accession_id:
                    return HttpResponseBadRequest("Missing accession ID")

                try:
                    decrypted_id = dec(accession_id)
                except Exception:
                    return HttpResponseBadRequest("Invalid accession ID")

                accession = get_object_or_404(BookAccession, accession_id=decrypted_id)
                accession_number = accession.accession_no or "UNKNOWN"
                subject_name = accession.catalogue.subject.subjectNameMarathi or ""

                # ✅ Generate barcode
                CODE = barcode.get_barcode_class('code128')
                writer_options = {
                    "module_width": 0.4,
                    "module_height": 8,
                    "quiet_zone": 2,
                    "font_size": 6,
                    "text_distance": 2.5,
                    "write_text": False,  # we’ll handle text manually
                }

                buffer = BytesIO()
                CODE(accession_number, writer=ImageWriter()).write(buffer, options=writer_options)
                buffer.seek(0)
                barcode_image = Image.open(buffer)

                # ✅ Font path
                font_path = os.path.join(settings.BASE_DIR, "static", "fonts", "NotoSansDevanagari-Regular.ttf")

                # ✅ Load fonts with proper sizes
                try:
                    marathi_font = ImageFont.truetype(font_path, 18)
                    number_font = ImageFont.truetype(font_path, 16)
                except:
                    marathi_font = ImageFont.load_default()
                    number_font = ImageFont.load_default()

                # ✅ Text setup
                marathi_text = "नवी मुंबई महानगरपालिका"
                marathi_text = f"{marathi_text} - {library_location}"
                
                number_text = f"{accession_number} - {subject_name}"

                # ✅ Measure text widths
                draw_temp = ImageDraw.Draw(barcode_image)
                marathi_width = draw_temp.textlength(marathi_text, font=marathi_font)
                number_width = draw_temp.textlength(number_text, font=number_font)

                # ✅ Calculate total height (Marathi + small gap + barcode + small gap + number)
                top_margin = 5
                gap_above_barcode = 6
                gap_below_barcode = 6
                new_height = top_margin + marathi_font.size + gap_above_barcode + barcode_image.height + gap_below_barcode + number_font.size

                new_image = Image.new("RGB", (barcode_image.width, new_height), "white")
                draw = ImageDraw.Draw(new_image)

                # ✅ Marathi text (top)
                text_x = (barcode_image.width - marathi_width) // 2
                text_y = top_margin
                draw.text((text_x, text_y), marathi_text, fill="black", font=marathi_font)

                # ✅ Barcode (middle)
                barcode_y = text_y + marathi_font.size + gap_above_barcode
                new_image.paste(barcode_image, (0, barcode_y))

                # ✅ Accession number + subject (bottom)
                number_x = (barcode_image.width - number_width) // 2
                number_y = barcode_y + barcode_image.height + gap_below_barcode
                draw.text((number_x, number_y), number_text, fill="black", font=number_font)

                # ✅ Encode to Base64
                output = BytesIO()
                new_image.save(output, format="PNG")
                barcode_image_b64 = base64.b64encode(output.getvalue()).decode("utf-8")

                return JsonResponse({
                    "accession_no": accession_number,
                    "subject_name": subject_name,
                    "barcode_image": barcode_image_b64,
                })

        # 🔹 POST: Save barcode
        elif request.method == "POST":
            
            place = request.POST.get("place")
            
            if place:
                
                accession_no = request.POST.get("accession_id")
                shelf_location = request.POST.get("shelf_location")
                
                # Validate input
                if not accession_no or not shelf_location:
                    messages.error(request, "Accession आणि Shelf Location आवश्यक आहेत.")
                    return redirect("L01:bar_code_index")

                try:
                    with transaction.atomic():
                        # Fetch the circulation copy by accession_no
                        ccs = CirculationCopyStatus.objects.get(accession_no=accession_no)
                        
                        # Update shelf location and audit fields
                        ccs.shelf_location_id = shelf_location
                        ccs.updated_by = user_id
                        ccs.save(update_fields=['shelf_location', 'updated_at', 'updated_by'])

                    messages.success(request, "Shelf location यशस्वीरित्या जतन झाली आहे.")
                    return redirect("L01:bar_code_index")

                except CirculationCopyStatus.DoesNotExist:
                    messages.error(request, "संबंधित Circulation copy सापडली नाही.")
                    return redirect("L01:bar_code_index")

                except Exception as e:
                    messages.error(request, f"Shelf location जतन करताना त्रुटी: {str(e)}")
                    return redirect("L01:bar_code_index")
            
            else:
                
                # Form fields
                accession_id_enc = request.POST.get("accession_id")
                accession_no = request.POST.get("accession_no")
                barcode_no = request.POST.get("barcode_no")
                user = request.session.get("user_id")

                if not accession_id_enc or not barcode_no:
                    messages.error(request, "काही आवश्यक माहिती गायब आहे!")
                    return redirect("L01:bar_code_index")

                try:
                    # Decrypt accession ID
                    accession_id = dec(str(accession_id_enc))
                    accession = get_object_or_404(BookAccession, accession_id=accession_id)

                    # Get status objects
                    processing_status = status_master.objects.get(status_id=7)  # Inventory: Ready
                    current_status = status_master.objects.get(status_id=13)    # Circulation: On-Shelf

                    # Wrap in transaction
                    with transaction.atomic():
                        # 1️⃣ Insert into CirculationCopyStatus
                        CirculationCopyStatus.objects.create(
                            accession=accession,
                            bookcatalog=accession.catalogue,
                            accession_no=accession_no,
                            barcode=barcode_no,
                            processing_status=processing_status,
                            current_status=current_status,
                            date_processed=timezone.now().date(),
                            created_by=user,
                        )

                        # 2️⃣ Update BookAccession status
                        accession.status_id = 5
                        accession.updated_by = user
                        accession.save(update_fields=['status_id', 'updated_at', 'updated_by'])

                    messages.success(request, "बारकोड यशस्वीरित्या जतन झाला!")
                    return redirect("L01:bar_code_index")

                except Exception as e_post:
                    # Optional: log error in DB
                    messages.error(request, f"त्रुटी आली: {str(e_post)}")
                    return redirect("L01:bar_code_index")

        # Unsupported method
        else:
            return HttpResponseBadRequest("Invalid request method")

    except Exception as e:
        # Global exception catch
        tb = traceback.extract_tb(e.__traceback__)
        fun = tb[0].name if tb else "generate_barcode"
        cursor.callproc("stp_error_log", [fun, str(e), library_code])
        print(f"error: {e}")
        messages.error(request, "Oops...! Something went wrong!")
        return redirect("L01:bar_code_index")

# Issue Book / Return Book
@login_required
def issue_return_book_create(request):
    try:
        Db.closeConnection()
        m = Db.get_connection()
        cursor = m.cursor()
        library_code = request.session.get('library_db', None)
        username = request.session.get('username', None)
        user_id = request.session["user_id"]
        role_id = request.session["role_id"]

        if request.method == "GET":
            
            # members = MembershipDetails.objects.filter(isactive=1)
            # members = MembershipDetails.objects.filter(isactive=1).exclude(membership__id=8)
            active_usernames = CustomUser.objects.filter(
                is_active=True
            ).values_list("username", flat=True)

            members = (
                MembershipDetails.objects
                .filter(isactive=1)                       # active members only
                .exclude(membership__id=8)               # exclude Practitioner Branch
                .filter(user_id__in=active_usernames)    # join on username = user_id
            )
            
            for m in members:
                m.member_encrypted_id = enc(str(m.id))
                
            # circulation = CirculationCopyStatus.objects.all()
            circulation = CirculationCopyStatus.objects.filter(shelf_location__isnull=False)
            
            for circ in circulation:
                circ.circ_encrypted_barcode = enc(str(circ.barcode))
                circ.circ_encrypted_id = enc(str(circ.id))
                # circ.circ_encrypted_accession_id = enc(str(circ.accession.accession_id))
            
            # barcode for returned books
            
            barcodes_qs = CirculationCopyStatus.objects.filter(current_status=14).values_list('barcode', flat=True)
            circulationTran = CirculationTransaction.objects.select_related(
                'catalog', 'member', 'circulation', 'return_condition'
            ).filter(
                barcode__in=barcodes_qs,
                return_condition_id=14  # assuming 14 is the PK for return_condition
            )
            
            for tran in circulationTran:
                tran.circulation_encrypted_barcode = enc(str(tran.barcode))
            
            # book Info
            
            bookcatelog = BookCatalog.objects.all()
            
            for bc in bookcatelog:
                bc.bc_encryp_id = enc(str(bc.cat_ref_num))
                
            # status dropdown for return condition
            
            status = status_master.objects.filter(status_type='circulation transaction', is_active=1)
            for st in status:
                st.status_encrypted_id = enc(str(st.status_id))
                
            return render(
                request,
                "L01/Circulation/issue_return_book_create.html",
                {
                    "MEDIA_URL": settings.MEDIA_URL,
                    "members": members,
                    "circulation": circulation,
                    "bookcatelog": bookcatelog,
                    "circulationTran": circulationTran,
                    "status_list": status,
                }
            )
        
        if request.method == "POST":

            # Check if it is issue or return
            if request.POST.get("issue") == "1":
                # ------------------- ISSUE LOGIC -------------------
                member_id = dec(str(request.POST.get("member_id")))
                barcode_id = dec(str(request.POST.get("barcode_id")))

                circ = CirculationCopyStatus.objects.select_related('accession', 'bookcatalog').get(barcode=barcode_id)
                member = MembershipDetails.objects.get(id=member_id)

                accession = circ.accession
                circulation = circ
                bookcatalog = circ.bookcatalog
                membercode = member.membership_code

                issue_date = request.POST.get("issue_date")
                due_date = request.POST.get("due_date")
                notes = request.POST.get("notes")

                return_condition_status = status_master.objects.get(status_id=14)  # default issued condition

                # Save transaction
                transaction = CirculationTransaction.objects.create(
                    catalog=bookcatalog,
                    accession=accession,
                    circulation=circulation,
                    member=member,
                    barcode=circ.barcode,
                    issue_date=issue_date,
                    due_date=due_date,
                    remarks=notes,
                    membership_code=membercode,
                    return_condition=return_condition_status,
                    issued_by=user_id,
                    created_by=user_id
                )

                # Update copy status
                circ.current_status = return_condition_status
                circ.save()

                messages.success(request, "ग्रंथ यशस्वीरित्या निर्गम केला गेला आहे!")

            elif request.POST.get("return") == "1":
                barcode_id = dec(str(request.POST.get("barcode_id")))

                trans_obj = CirculationTransaction.objects.filter(
                    barcode=barcode_id,
                    return_date__isnull=True
                ).first()

                if not trans_obj:
                    messages.error(request, "सक्षम पुस्तके परत करण्यासाठी रेकॉर्ड सापडले नाही!")
                    return redirect('L01:issue_return_book_create')

                # Book condition and fine
                condition_name = request.POST.get("book_condition")
                fine_amount = float(request.POST.get("fine_amount", 0) or 0)
                adjusted_fine = float(request.POST.get("adjusted_amount", 0) or 0)  # <-- new
                book_price_amount = float(request.POST.get("book_price_amount", 0) or 0)
                total_amount = float(request.POST.get("total_amount", 0))
                fine_Breakdown = float(request.POST.get("fine_Breakdown", 0))
                notes = request.POST.get("notes", "")
                payment_method = request.POST.get("payment_method", "Cash")

                # Determine new circulation status
                if condition_name == '17':  # Good
                    new_copy_status = status_master.objects.get(status_id=13)
                elif condition_name in ['18', '19']:  # Torn or Lost
                    new_copy_status = status_master.objects.get(status_id=19)
                else:
                    new_copy_status = status_master.objects.get(status_id=13)

                # Wrap all DB operations in a transaction
                try:
                    with db_transaction.atomic():
                        # Update CirculationTransaction
                        
                        final_fine = adjusted_fine if adjusted_fine > 0 else fine_amount
                        
                        trans_obj.return_date = timezone.now().date()
                        trans_obj.return_condition = new_copy_status
                        trans_obj.fine_amount = fine_amount
                        trans_obj.adjusted_fine = adjusted_fine  # <-- save adjusted fine
                        trans_obj.book_fine_amount = book_price_amount
                        trans_obj.total_fine = total_amount
                        trans_obj.days_overdue_count = fine_Breakdown
                        trans_obj.fine_status = "Paid" if fine_amount > 0 else "None"
                        trans_obj.fine_paid_date = timezone.now().date()
                        trans_obj.transaction_status = "Success"
                        trans_obj.transaction_type = "Offline"
                        trans_obj.received_by = user_id
                        trans_obj.remarks = notes
                        trans_obj.updated_by = user_id
                        trans_obj.save()

                        # Update book copy status
                        circ = trans_obj.circulation
                        circ.current_status = new_copy_status
                        circ.save()

                        # Payment logic
                        fine_nonzero = fine_amount > 0.001
                        book_nonzero = book_price_amount > 0.001

                        if fine_nonzero and not book_nonzero:
                            payment_type = "Fine"
                        elif fine_nonzero and book_nonzero:
                            payment_type = "Fine and Book Price"
                        elif not fine_nonzero and book_nonzero:
                            payment_type = "Loss"
                        else:
                            payment_type = None

                        if total_amount > 0 and payment_type:
                            PaymentDetails.objects.create(
                                membership=trans_obj.member,
                                circulation_transaction=trans_obj,
                                payment_mode="Offline",
                                payment_method=payment_method,
                                payment_type=payment_type,
                                fine_amount=final_fine,              
                                book_fine_amount=book_price_amount,  
                                user_id=trans_obj.member.user_id,
                                membership_code=trans_obj.membership_code,
                                payment_date=timezone.now().date(),
                                created_by=user_id,
                                updated_by=user_id,
                                status=StatusMaster.objects.get(id=5),
                            )

                    messages.success(request, "पुस्तक यशस्वीरित्या परत झाले आहे!")

                except Exception as e:
                    # Rollback automatically on any error
                    messages.error(request, f"त्रुटी: {str(e)}. कृपया पुन्हा प्रयत्न करा!")
                    return redirect('L01:issue_return_book_create')
            
            return redirect('L01:issue_return_book_create')
        
    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        fun = tb[0].name if tb else "library_list"
        cursor.callproc("stp_error_log", [fun, str(e), library_code])
        print(f"error: {e}")
        messages.error(request, "Oops...! Something went wrong!")
        return render(request, "L01/Circulation/issue_return_book_create.html", {})

@csrf_exempt  # Only if needed; otherwise use CSRF token in JS
def get_member_details(request):
    if request.method != "POST":
        return JsonResponse({"success": False, "error": "Invalid request method"})

    member_id = dec(str(request.POST.get("member_id")))
    if not member_id:
        return JsonResponse({"success": False, "error": "Member ID missing"})

    try:
        Db.closeConnection()
        m = Db.get_connection()
        cursor = m.cursor()
        library_code = request.session.get('library_db', None)
        username = request.session.get('username', None)
        user_id = request.session["user_id"]
        role_id = request.session["role_id"]

        # Fetch DocumentDetails for this member where document_id=1
        documents = DocumentDetails.objects.filter(
            membership_id=member_id,
            document_id=1,
            isactive=1
        ).select_related(
            'membership__membership',       # MembershipMaster
            'membership__member_type',      # parameter_master_L01
            'document'
        )

        document_list = []
        for doc in documents:
            membership = doc.membership
            membership_master = membership.membership
            member_type_param = membership.member_type
            
            # Format dates
            from_date = membership.from_date.strftime("%d %b %Y") if membership.from_date else '-'
            to_date = membership.to_date.strftime("%d %b %Y") if membership.to_date else '-'

            document_list.append({
                "membership_id": membership.id,
                "full_name": f"{membership.first_name} {membership.middle_name or ''} {membership.last_name}",
                "email": membership.email,
                "mobile_no": membership.mobile_no,
                "membership_code": membership_master.membership_code if membership_master else '',
                "membership_type": membership_master.membership_type_en if membership_master else '',
                "membership_item": membership_master.item if membership_master else '',
                "membership_days": membership_master.days if membership_master else '',
                "member_type_name": member_type_param.parameter_name if member_type_param else '',
                "membership_fromDate": from_date,
                "membership_toDate": to_date,
                "membership_duration": membership.membership_duration,
                "document_id": doc.document.id,
                "document_name": doc.document.document_name if doc.document else '',
                "file_name": doc.file_name,
                "file_path": doc.file_path,
            })
            
        issued_books_count = CirculationTransaction.objects.filter(
            member_id=member_id,
            return_condition_id=14
        ).count()

        return JsonResponse({
            "success": True,
            "documents": document_list,
            "MEDIA_URL": settings.MEDIA_URL,
            "issued_books_count":issued_books_count,
        })

    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        fun = tb[0].name if tb else "library_list"
        cursor.callproc("stp_error_log", [fun, str(e), library_code])
        print(f"error: {e}")
        messages.error(request, "Oops...! Something went wrong!")
        return render(request, "L01/Circulation/issue_return_book_create.html", {})

@csrf_exempt  # Remove this if you’re using CSRF token in AJAX
def get_book_details(request):
    if request.method == "POST":
        try:
            # --- Session Variables ---
            library_code = request.session.get('library_db', None)
            username = request.session.get('username', None)
            user_id = request.session.get("user_id")
            role_id = request.session.get("role_id")

            # --- Barcode / Encrypted ID ---
            barcode_id = request.POST.get("barcode_id")
            returnProcess = request.POST.get("returnProcess")
            
            if not barcode_id:
                return JsonResponse({"success": False, "message": "Barcode ID missing."}, status=400)
            
            if not returnProcess:

                # --- Decrypt if needed ---
                try:
                    barcode_id = dec(barcode_id)
                except Exception:
                    # If not encrypted, just use it as-is
                    pass

                # --- Fetch Book Details ---
                circ = (
                    CirculationCopyStatus.objects
                    .select_related("bookcatalog", "shelf_location", "current_status")
                    .get(barcode=barcode_id)  # <--- match by barcode
                )

                data = {
                    "success": True,
                    "MEDIA_URL": settings.MEDIA_URL,
                    "book": {
                        "title": circ.bookcatalog.title if circ.bookcatalog else "-",
                        "author": circ.bookcatalog.author if circ.bookcatalog else "-",
                        "isbn_issn": circ.bookcatalog.isbn_issn if circ.bookcatalog else "-",
                        "pages": circ.bookcatalog.pages if circ.bookcatalog else "-",
                        "language": circ.bookcatalog.language if circ.bookcatalog else "-",
                        "front_page_photo": circ.bookcatalog.front_page_photo if circ.bookcatalog else "",
                        "location_name": circ.shelf_location.location_name if circ.shelf_location else "-",
                        "status_name": circ.current_status.status_name if circ.current_status else "Unknown",
                        "status_color": circ.current_status.status_color if circ.current_status else "#999",
                    },
                }
                return JsonResponse(data)
            
            else:   
                
                barcode_id = dec(barcode_id)
                
                try:
                    circ = CirculationTransaction.objects.select_related(
                        "catalog", "member", "circulation", "return_condition","accession"
                    ).get(barcode=barcode_id,
                          return_condition__status_id=14)

                    book = circ.catalog
                    member = circ.member
                    membership_master = member.membership
                    price = circ.accession.price if circ.accession else 0
                    today = timezone.now().date()

                    # Format due date nicely (e.g., 10 Jan 2025)
                    due_date_str = (
                        circ.due_date.strftime("%d %b %Y") if circ.due_date else "-"
                    )

                    # Calculate overdue days
                    days_overdue = 0
                    status_name = (
                        circ.return_condition.status_name if circ.circulation else "Unknown"
                    )

                    if circ.due_date and today > circ.due_date:
                        days_overdue = (today - circ.due_date).days
                        status_name = "Overdue"
                        
                    # Calculate fine amount
                    fine_per_day = float(membership_master.fine or 0)  # default 0 if None
                    total_fine = days_overdue * fine_per_day

                    # Fetch member profile photo (Document ID = 1)
                    profile_doc = (
                        DocumentDetails.objects.filter(
                            membership=member, document_id=1, isactive=1
                        )
                        .order_by("-created_at")
                        .first()
                    )
                    profile_photo = profile_doc.file_path if profile_doc else ""

                    # Member full name
                    member_name = " ".join(
                        filter(None, [member.first_name, member.middle_name, member.last_name])
                    )

                    # Construct return data
                    data = {
                        "success": True,
                        "MEDIA_URL": settings.MEDIA_URL,
                        "book": {
                            "title": book.title if book else "-",
                            "author": book.author if book else "-",
                            "isbn_issn": book.isbn_issn if book else "-",
                            "front_page_photo": book.front_page_photo if book else "",
                            "status_name": status_name,
                            "due_date": due_date_str,
                            "issue_date": (
                                circ.issue_date.strftime("%d %b %Y")
                                if circ.issue_date
                                else "-"
                            ),
                            "days_overdue": days_overdue,
                            "fine_amount": total_fine,  # ✅ calculated fine
                            "price": price,
                        },
                        "member": {
                            "member_name": member_name,
                            "member_code": member.membership_code or "-",
                            "profile_photo": profile_photo,
                            "mobile_no": member.mobile_no or "-",
                        },
                    }

                    return JsonResponse(data)
                
                except ObjectDoesNotExist:
                    return JsonResponse({
                        "success": False,
                        "error": "No circulation transaction found for this barcode."
                    })

        except Exception as e:
            tb = traceback.extract_tb(e.__traceback__)
            fun = tb[0].name if tb else "get_book_details"

            try:
                # Log error in DB (if your stored procedure exists)
                Db.closeConnection()
                m = Db.get_connection()
                cursor = m.cursor()
                cursor.callproc("stp_error_log", [fun, str(e), library_code])
            except Exception:
                pass

            print(f"Error in {fun}: {e}")
            messages.error(request, "Oops...! Something went wrong!")
            return JsonResponse({"success": False, "message": "Internal Server Error"}, status=500)

    else:
        return JsonResponse({"success": False, "message": "Invalid request method"}, status=405)

@csrf_exempt
def get_book_circulation_status(request):
    if request.method == "POST":
        book_id = dec(str(request.POST.get("book_id")))
        if not book_id:
            return JsonResponse({"error": "Missing book_id"}, status=400)

        records = (
            CirculationCopyStatus.objects.filter(bookcatalog_id=book_id)
            .select_related("bookcatalog", "current_status", "accession")
            .values(
                "id",
                "barcode",
                "bookcatalog__cat_ref_num",
                "bookcatalog__title",
                "bookcatalog__author",
                "bookcatalog__classification_number",
                "current_status__status_name",
                "accession__accession_no"
            )
        )

        return JsonResponse(list(records), safe=False)

@csrf_exempt
def circulation_transaction_details(request):
    Db.closeConnection()
    m = Db.get_connection()
    cursor = m.cursor()
    try:
        library_code = request.session.get('library_db', None)
        username = request.session.get('username', None)
        user_id = request.session.get("user_id")
        role_id = request.session.get("role_id")
        
        member_id = request.GET.get("member_id")
        
        barcodeName = request.GET.get("barcodeName")
        
        if not member_id:
            if barcodeName:
                barcode = request.GET.get("barcode")
            else:
                barcode = dec(str(request.GET.get("barcode")))
        
        
        if member_id:

            transactions = (
                CirculationTransaction.objects
                .select_related("catalog", "accession", "return_condition")
                .filter(
                    member_id=member_id,
                    return_condition__status_id=14
                )
                .values(
                    "catalog__title",
                    "accession__accession_no",
                    "issue_date",
                    "due_date",
                    "return_condition__status_name"
                )
            )

            transaction_list = [
                {
                    "title": t["catalog__title"],
                    "accession_no": t["accession__accession_no"],
                    "issue_date": t["issue_date"].strftime("%Y-%m-%d") if t["issue_date"] else None,
                    "due_date": t["due_date"].strftime("%Y-%m-%d") if t["due_date"] else None,
                    "status_name": t["return_condition__status_name"],
                }
                for t in transactions
            ]

            return JsonResponse({"success": True, "transactions": transaction_list})
        
        if barcode:
            
            transactions = (
                CirculationTransaction.objects
                .select_related("catalog", "accession", "member", "return_condition")
                .filter(barcode=barcode,
                        return_condition__status_id=14)
                .values(
                    "catalog__title",
                    "accession__accession_no",
                    "issue_date",
                    "due_date",
                    "return_condition__status_name",
                    "member__first_name",
                    "member__last_name",
                    "member__membership_code"
                )
            )

            transaction_list = [
                {
                    "title": t["catalog__title"],
                    "accession_no": t["accession__accession_no"],
                    "issue_date": t["issue_date"].strftime("%Y-%m-%d") if t["issue_date"] else None,
                    "due_date": t["due_date"].strftime("%Y-%m-%d") if t["due_date"] else None,
                    "status_name": t["return_condition__status_name"],
                    "member_name": f"{t['member__first_name']} {t['member__last_name']}",
                    "membership_code": t["member__membership_code"]
                }
                for t in transactions
            ]

            return JsonResponse({"success": True, "transactions": transaction_list})
        
    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        fun = tb[0].name if tb else 'library_list'
        cursor.callproc("stp_error_log", [fun, str(e), library_code])
        print(f"error: {e}")
        messages.error(request, 'Oops...! Something went wrong!')
    
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

def view_catalogue(request):
    return render(request, "L01/view_catalogue.html", {
        "MEDIA_URL": settings.MEDIA_URL
    })

def view_ebook_catalogue(request):
    return render(request, "L01/view_ebook_catalogue.html", {
        "MEDIA_URL": settings.MEDIA_URL
    })

@csrf_exempt
def bookcatalog_search(request):
    try:
        if request.method != "POST":
            return JsonResponse({"error": "Invalid request method. Use POST."}, status=405)

        query = request.POST.get("query", "").strip()
        search_type = request.POST.get("searchType", "").strip().lower()

        if not query or not search_type:
            return JsonResponse({"error": "Please provide both query and search type."}, status=400)

        # Base queryset from L01 database
        results = BookCatalog.objects.using('L01').all()

        # Filter by selected search type
        if search_type in ["title", "books"]:
            results = results.filter(title__icontains=query)
        elif search_type == "author":
            results = results.filter(author__icontains=query)
        elif search_type == "publisher":
            results = results.filter(publisher__icontains=query)
        elif search_type == "language":
            results = results.filter(language__icontains=query)
        elif search_type == "keyword":
            results = results.filter(keywords__icontains=query)
        elif search_type == "year":
            year_filters = Q()
            if query.isdigit():
                year_filters |= Q(year_of_publication=int(query))
            year_filters |= Q(publication_year__icontains=query)
            results = results.filter(year_filters)
        elif search_type == "call_number":
            results = results.filter(call_number__icontains=query)
        elif search_type == "cutter_number":
            results = results.filter(cutter_number__icontains=query)
        else:
            return JsonResponse({"error": f"Invalid search type: {search_type}"}, status=400)

        # Limit results to 50
        results = results.values(
            "title",
            "author",
            "publisher",
            "language",
            "year_of_publication",
            "publication_year",
            "call_number",
            "cutter_number",
            "front_page_photo",
            "ebook_available",
            "cat_ref_num",  # <-- Include cat_ref_num from DB
        )[:50]

        # Convert front_page_photo to absolute URL
        updated_results = []
        for r in results:
            image_path = r.get("front_page_photo")
            r["front_page_photo"] = request.build_absolute_uri(f"/media/{image_path}") if image_path else ""
            updated_results.append(r)

        return JsonResponse(updated_results, safe=False)

    except Exception as e:
        return JsonResponse(
            {"error": "An unexpected error occurred.", "details": str(e)},
            status=500
        )
    
@csrf_exempt
def index_book_search(request):
    try:
        if request.method != "POST":
            return JsonResponse({"error": "Invalid request method. Use POST."}, status=405)

        query = request.POST.get("query", "").strip()
        search_type = request.POST.get("searchType", "").strip().lower()  # Optional filter type

        if not query:
            return JsonResponse({"error": "Please enter a search term."}, status=400)

        # Base queryset
        results = BookCatalog.objects.using('L01').all()

        # Search only from FIRST letter (using istartswith)
        if search_type in ["title", "books", ""]:
            results = results.filter(title__istartswith=query)

        elif search_type == "author":
            results = results.filter(author__istartswith=query)

        elif search_type == "publisher":
            results = results.filter(publisher__istartswith=query)

        elif search_type == "language":
            results = results.filter(language__istartswith=query)

        elif search_type == "keyword":
            results = results.filter(keywords__istartswith=query)

        elif search_type == "year":
            # Publication year should also start with the query
            year_filters = Q(publication_year__istartswith=query) | Q(year_of_publication__istartswith=query)
            results = results.filter(year_filters)

        else:
            return JsonResponse({"error": f"Invalid search type: {search_type}"}, status=400)

        # Limit results
        results = results.values(
            "title",
            "author",
            "publisher",
            "language",
            "year_of_publication",
            "publication_year",
            "call_number",
            "cutter_number",
            "front_page_photo",
            "ebook_available",
        )[:50]

        # Convert image path to absolute URL
        updated_results = []
        for r in results:
            image_path = r.get("front_page_photo")
            r["front_page_photo"] = (
                request.build_absolute_uri(f"/media/{image_path}") if image_path else ""
            )
            updated_results.append(r)

        return JsonResponse(updated_results, safe=False)

    except Exception as e:
        return JsonResponse(
            {"error": "An unexpected error occurred.", "details": str(e)},
            status=500
        )


    try:
        if request.method != "POST":
            return JsonResponse({"error": "Invalid request method. Use POST."}, status=405)

        query = request.POST.get("query", "").strip()
        search_type = request.POST.get("searchType", "").strip().lower()

        if not query or not search_type:
            return JsonResponse({"error": "Please provide both query and search type."}, status=400)

        # Base queryset from L01 database
        results = BookCatalog.objects.using('L01').all()

        # Filter by selected search type
        if search_type == "title" or search_type == "books":
            results = results.filter(title__icontains=query)
        elif search_type == "author":
            results = results.filter(author__icontains=query)
        elif search_type == "publisher":
            results = results.filter(publisher__icontains=query)
        elif search_type == "language":
            results = results.filter(language__icontains=query)
        elif search_type == "keyword":
            results = results.filter(keywords__icontains=query)
        elif search_type == "year":
            year_filters = Q()
            if query.isdigit():
                year_filters |= Q(year_of_publication=int(query))
            year_filters |= Q(publication_year__icontains=query)
            results = results.filter(year_filters)
        elif search_type == "call_number":
            results = results.filter(call_number__icontains=query)
        elif search_type == "cutter_number":
            results = results.filter(cutter_number__icontains=query)
        else:
            return JsonResponse({"error": f"Invalid search type: {search_type}"}, status=400)

        # Limit results to 50
        results = results.values(
            "title",
            "author",
            "publisher",
            "language",
            "year_of_publication",
            "publication_year",
            "call_number",
            "cutter_number",
            "front_page_photo",
            "ebook_available",
        )[:50]

        # Convert front_page_photo to absolute URL
        updated_results = []
        for r in results:
            image_path = r.get("front_page_photo")
            r["front_page_photo"] = request.build_absolute_uri(f"/media/{image_path}") if image_path else ""
            updated_results.append(r)

        return JsonResponse(updated_results, safe=False)

    except Exception as e:
        return JsonResponse(
            {"error": "An unexpected error occurred.", "details": str(e)},
            status=500
        )

@csrf_exempt
def libraryebook_search(request):
    try:
        if request.method != "POST":
            return JsonResponse({"error": "Invalid request method. Use POST."}, status=405)

        query = request.POST.get("query", "").strip()
        search_type = request.POST.get("searchType", "").strip().lower()

        if not query or not search_type:
            return JsonResponse({"error": "Please provide both query and search type."}, status=400)

        # Base queryset
        results = LibraryEbook.objects.using('L01').all()

        # ---- FILTER BASED ON SEARCH TYPE ----
        if search_type in ["title", "ebook", "book"]:
            results = results.filter(eb_title__icontains=query)

        elif search_type == "author":
            results = results.filter(
                Q(eb_author__icontains=query) |
                Q(eb_other_authors__icontains=query)
            )

        elif search_type == "publisher":
            results = results.filter(eb_publisher__icontains=query)

        elif search_type == "language":
            results = results.filter(eb_language__icontains=query)

        elif search_type == "keyword":
            results = results.filter(eb_keywords__icontains=query)

        elif search_type in ["isbn", "issn"]:
            results = results.filter(eb_isbn_issn__icontains=query)

        elif search_type == "year":
            year_filters = Q()
            if query.isdigit():
                year_filters |= Q(eb_year_of_publication=int(query))
            year_filters |= Q(eb_year_of_publication__icontains=query)
            results = results.filter(year_filters)

        else:
            return JsonResponse({"error": f"Invalid search type: {search_type}"}, status=400)

        # ---- LIMIT AND RETURN FIELDS ----
        results = results.values(
            "ebook_id",
            "eb_title",
            "eb_author",
            "eb_other_authors",
            "eb_publisher",
            "eb_language",
            "eb_year_of_publication",
            "eb_keywords",
            "eb_isbn_issn",
            "eb_pdf_url",
            "eb_front_page_photo"
        )[:50]

        # ---- FORMAT + ENCRYPT ----
        updated_results = []
        for r in results:
            # absolute image url
            img = r.get("eb_front_page_photo")
            r["eb_front_page_photo"] = (
                request.build_absolute_uri(f"/media/{img}") if img else ""
            )

            # Encrypt ID + PDF URL
            r["encrypted_ebook_id"] = enc(str(r["ebook_id"]))
            r["encrypted_pdf_url"] = enc(r["eb_pdf_url"]) if r["eb_pdf_url"] else ""

            updated_results.append(r)

        return JsonResponse(updated_results, safe=False)

    except Exception as e:
        return JsonResponse(
            {"error": "An unexpected error occurred.", "details": str(e)},
            status=500
        )

    

@csrf_exempt
def index_ebook_search(request):
    try:
        library_code = request.session.get('library_db', None)
        if request.method != "POST":
            return JsonResponse({"error": "Invalid request method. Use POST."}, status=405)

        query = request.POST.get("query", "").strip()
        search_type = request.POST.get("searchType", "").strip().lower()

        if not query:
            return JsonResponse({"error": "Please enter a search term."}, status=400)

        # Base queryset
        results = LibraryEbook.objects.using('L01').all()

        # ---- FIRST-LETTER SEARCH ----
        if search_type in ["title", "book", "ebook", ""]:
            results = results.filter(eb_title__istartswith=query)

        elif search_type == "author":
            results = results.filter(
                Q(eb_author__istartswith=query) |
                Q(eb_other_authors__istartswith=query)
            )

        elif search_type == "publisher":
            results = results.filter(eb_publisher__istartswith=query)

        elif search_type == "language":
            results = results.filter(eb_language__istartswith=query)

        elif search_type == "keyword":
            results = results.filter(eb_keywords__istartswith=query)

        elif search_type in ["isbn", "issn"]:
            results = results.filter(eb_isbn_issn__istartswith=query)

        elif search_type == "year":
            results = results.filter(eb_year_of_publication__istartswith=query)

        else:
            return JsonResponse({"error": f"Invalid search type: {search_type}"}, status=400)

        # ---- SELECT FIELDS ----
        results = results.values(
            "ebook_id",
            "eb_title",
            "eb_author",
            "eb_other_authors",
            "eb_publisher",
            "eb_language",
            "eb_year_of_publication",
            "eb_keywords",
            "eb_isbn_issn",
            "eb_pdf_url",
            "eb_front_page_photo",
        )[:50]

        # ---- FORMAT + ENCRYPT ----
        updated_results = []
        for r in results:
            img = r.get("eb_front_page_photo")
            r["eb_front_page_photo"] = (
                request.build_absolute_uri(f"/media/{img}") if img else ""
            )

            # Encrypt ID + PDF URL
            r["encrypted_ebook_id"] = enc(str(r["ebook_id"]))
            r["encrypted_pdf_url"] = enc(r["eb_pdf_url"]) if r["eb_pdf_url"] else ""

            updated_results.append(r)

        return JsonResponse(updated_results, safe=False)

    except Exception as e:
        return JsonResponse(
            {"error": "An unexpected error occurred.", "details": str(e)},
            status=500
        )


def upsc_ebook_index(request):
    try:
        # Fetch the competitive exam details for UPSC (id = 1) from L01 DB
        competitive_exam = get_object_or_404(
            CompetitiveExamMaster.objects.using('L01'),
            competitive_id=1
        )

        # Fetch all related sections linked to UPSC (from L01 DB)
        sections = Sections.objects.using('L01').filter(
            competitive_id=1
        ).order_by('section_no')

        # ✅ Fetch subjects for each section (order by subject_id)
        # Keep as list of tuples (section_no, subjects)
        subjects_by_section = []
        for section in sections:
            subjects = Subjects.objects.using('L01').filter(
                section_no=section.section_no
            ).order_by('subject_id')  # use subject_id since subject_no doesn't exist
            subjects_by_section.append((section.section_no, subjects))

        # Pass everything to template without converting to dict
        return render(request, "L01/UPSC/upsc_ebook_index.html", {
            "MEDIA_URL": settings.MEDIA_URL,
            "competitive_exam": competitive_exam,
            "sections": sections,
            "subjects_by_section": subjects_by_section,  # list of tuples
        })
    except Exception as e:
        return JsonResponse(
            {"error": "An unexpected error occurred.", "details": str(e)},
            status=500
        )

def topic_index(request, section_no):
    try:
        # ✅ Get the competitive exam (UPSC)
        competitive_exam = get_object_or_404(
            CompetitiveExamMaster.objects.using('L01'),
            competitive_id=1
        )

        # ✅ Fetch the specific section using the passed section_no
        section = get_object_or_404(
            Sections.objects.using('L01'),
            section_no=section_no
        )

        # ✅ Fetch all subjects under this section
        subjects = Subjects.objects.using('L01').filter(
            section_no=section.section_no
        ).order_by('subject_id')

        subjects_data = []

        # ✅ For each subject, fetch topics under the same section
        for subject in subjects:
            topics = Topics.objects.using('L01').filter(
                subject_id=subject.subject_id,
                section_no=section.section_no
            ).order_by('topic_id')

            subjects_data.append({
                "subject": subject,
                "topics": topics
            })

        # ✅ Pass the structured data to the template
        return render(request, "L01/UPSC/topics_index.html", {
            "MEDIA_URL": settings.MEDIA_URL,
            "competitive_exam": competitive_exam,
            "section": section,
            "subjects_data": subjects_data,
        })

    except Exception as e:
        return JsonResponse(
            {"error": "An unexpected error occurred.", "details": str(e)},
            status=500
        )

def chapters_index(request, topic_id):
    try:
        
        library_code = request.session.get('library_db', None)
        
        # ✅ Fetch the selected topic from L01
        topic = get_object_or_404(
            Topics.objects.using('L01'),
            topic_id=topic_id
        )

        # ✅ Fetch the parent section for breadcrumb
        section = get_object_or_404(
            Sections.objects.using('L01'),
            section_no=topic.section_no_id
        )

        # ✅ Fetch all chapters under this topic (sorted numerically)
        chapters = Chapters.objects.using('L01') \
            .filter(topic_id=topic_id) \
            .annotate(
                chapter_no_int=Cast('chapter_no', IntegerField())
            ) \
            .order_by('chapter_no_int')

        # ✅ Prepare structured data (if needed for template)
        chapters_data = []
        for chapter in chapters:
            chapters_data.append({
                "chapter": chapter
            })

        # ✅ Render the chapters page
        return render(request, "L01/UPSC/chapters_index.html", {
            "MEDIA_URL": settings.MEDIA_URL,
            "section": section,
            "topic": topic,
            "chapters_data": chapters_data,
        })

    except Exception as e:
        return JsonResponse(
            {"error": "An unexpected error occurred.", "details": str(e)},
            status=500
        )
    
def get_membership_code(request):
    username = request.session.get("username")
    # email = get_object_or_404(CustomUser, id = user_id).email
    member = MembershipDetails.objects.get(user_id=username)

    return JsonResponse({
        "membership_code": member.membership_code
    })

def mpsc_ebook_index(request):
    try:
        # Fetch the competitive exam details for MPSC (id = 2) from L01 DB
        competitive_exam = get_object_or_404(
            CompetitiveExamMaster.objects.using('L01'),
            competitive_id=2
        )

        # Fetch all related sections linked to MPSC (from L01 DB)
        sections = Sections.objects.using('L01').filter(
            competitive_id=2
        ).order_by('section_no')

        # ✅ Fetch subjects for each section (order by subject_id)
        subjects_by_section = []
        for section in sections:
            subjects = Subjects.objects.using('L01').filter(
                section_no=section.section_no
            ).order_by('subject_id')  # using subject_id same as UPSC
            subjects_by_section.append((section.section_no, subjects))

        # Pass everything to template without converting to dict
        return render(request, "L01/MPSC/mpsc_ebooks_index.html", {
            "MEDIA_URL": settings.MEDIA_URL,
            "competitive_exam": competitive_exam,
            "sections": sections,
            "subjects_by_section": subjects_by_section,
        })

    except Exception as e:
        return JsonResponse(
            {"error": "An unexpected error occurred.", "details": str(e)},
            status=500
        )

def mpsc_topics_index(request, section_no):
    try:
        # ✅ Get the competitive exam (MPSC)
        competitive_exam = get_object_or_404(
            CompetitiveExamMaster.objects.using('L01'),
            competitive_id=2   # ← MPSC ID
        )

        # ✅ Fetch the specific section using the passed section_no
        section = get_object_or_404(
            Sections.objects.using('L01'),
            section_no=section_no
        )

        # ✅ Fetch all subjects under this section
        subjects = Subjects.objects.using('L01').filter(
            section_no=section.section_no
        ).order_by('subject_id')

        subjects_data = []

        # ✅ For each subject, fetch topics under the same section
        for subject in subjects:
            topics = Topics.objects.using('L01').filter(
                subject_id=subject.subject_id,
                section_no=section.section_no
            ).order_by('topic_id')

            subjects_data.append({
                "subject": subject,
                "topics": topics
            })

        # ✅ Render the MPSC topics page
        return render(request, "L01/MPSC/mpsc_topics_index.html", {   # ← Change template if needed
            "MEDIA_URL": settings.MEDIA_URL,
            "competitive_exam": competitive_exam,
            "section": section,
            "subjects_data": subjects_data,
        })

    except Exception as e:
        return JsonResponse(
            {"error": "An unexpected error occurred.", "details": str(e)},
            status=500
        )

def mpsc_chapters_index(request, topic_id):
    try:
        # Fetch competitive exam (MPSC)
        competitive_exam = get_object_or_404(
            CompetitiveExamMaster.objects.using('L01'),
            competitive_id=2
        )

        # Fetch the topic
        topic = get_object_or_404(
            Topics.objects.using('L01'),
            topic_id=topic_id
        )

        # Fetch parent section
        section = get_object_or_404(
            Sections.objects.using('L01'),
            section_no=topic.section_no_id
        )

        # Fetch chapters under this topic
        chapters = Chapters.objects.using('L01') \
            .filter(topic_id=topic_id) \
            .annotate(chapter_no_int=Cast('chapter_no', IntegerField())) \
            .order_by('chapter_no_int')

        chapters_data = [{"chapter": chapter} for chapter in chapters]

        return render(request, "L01/MPSC/mpsc_chapters_index.html", {
            "MEDIA_URL": settings.MEDIA_URL,
            "competitive_exam": competitive_exam,
            "section": section,
            "topic": topic,
            "chapters_data": chapters_data,
        })

    except Exception as e:
        return JsonResponse(
            {"error": "An unexpected error occurred.", "details": str(e)},
            status=500
        )
    
def member_entry_exit(request):
    from django.utils.timezone import localdate
    active_user_ids = CustomUser.objects.filter(
        is_active=1
    ).values_list('username', flat=True)   # <-- important


    # 2️⃣ Filter MembershipDetails for those active user_ids
    members = MembershipDetails.objects.using('L01').filter(
        isactive=1,
        user_id__in=active_user_ids
    ).annotate(
        display_name=Concat(
            'first_name', Value(' '),
            'middle_name', Value(' '),
            'last_name', Value(' - '),
            'membership_code',
            output_field=CharField()
        )
    ).values('membership_code', 'display_name')
    active_members = MembershipDetails.objects.using('L01').filter(isactive=True).count()
    today = date.today()

    today = localdate()

    scan_today = MemberEntryExit.objects.using('L01').filter(
        entry_time__date=today
    ).count()



    context = {
        'members': list(members),
        'active_members': active_members,
        'scan_today': scan_today
    }

    return render(request, 'L01/Member Payment/member_log.html', context)

def get_member_detail(request, membership_code):
    try:
        # Query from L01 database
        member = MembershipDetails.objects.using('L01').get(membership_code=membership_code)
        # membership_typemember_type = f"{member.membership.membership_type '+' (member.membership.membership_code)})"
        
        # Check if membership is valid based on to_date
        current_date = date.today()
        is_valid = (member.from_date <= current_date <= member.to_date if (member.from_date and member.to_date) else False)

        
        # Get profile picture from DocumentDetails in L01 database
        # profile_pic = '/static/images/default-profile.png'
        try:
            document = DocumentDetails.objects.using('L01').get(membership=member.id, document_id=1)
            if document.file_path:
                file_path = Path(settings.MEDIA_ROOT) / Path(document.file_path.replace("\\", "/"))
                if file_path.exists():
                    profile_pic = f"{settings.MEDIA_URL}{document.file_path.replace('\\', '/')}"
        except DocumentDetails.DoesNotExist:
            pass  # Use default profile picture
        
        # Prepare response data
        member_data = {
            'membership_code': member.membership_code,
            'full_name': f"{member.first_name} {member.middle_name} {member.last_name}".strip(),
            'ward': member.ward or 'Not specified',
            'member_type': member.membership.membership_type,
            'is_active': member.isactive,
            'status': 'valid' if is_valid else 'invalid',
            'profile_pic': profile_pic,
            'to_date': member.to_date.strftime('%Y-%m-%d') if member.to_date else 'N/A',
            'membership_expired': not is_valid  # Add this flag
        }
        
        # AUTO CREATE ENTRY ONLY IF MEMBERSHIP IS VALID (to_date not passed)
        if is_valid and member.isactive:
            current_time = datetime.now()
            
            # Check for existing open entry today
            today_start = current_time.replace(hour=0, minute=0, second=0, microsecond=0)
            today_end = current_time.replace(hour=23, minute=59, second=59, microsecond=999999)
            
            existing_entry = MemberEntryExit.objects.using('L01').filter(
                membership_code=membership_code,
                entry_time__gte=today_start,
                entry_time__lte=today_end,
                exit_time__isnull=True
            ).first()
            
            if not existing_entry:
                # Create new entry record
                entry_record = MemberEntryExit.objects.using('L01').create(
                    membership_code=membership_code,
                    entry_time=current_time,
                    exit_time=None,
                    role_id=getattr(member, 'role_id', None),
                    created_by=request.user if request.user.is_authenticated else None,
                    updated_by=request.user if request.user.is_authenticated else None
                )
                
                member_data['auto_entry_created'] = True
                member_data['entry_time'] = current_time.strftime('%Y-%m-%d %H:%M:%S')
                member_data['entry_id'] = entry_record.id
                member_data['log_message'] = f"Entry log successfully created for {member.first_name} {member.last_name}"
            else:
                member_data['auto_entry_created'] = False
                member_data['log_message'] = f"Active entry already exists for {member.first_name} {member.last_name}"
        else:
            member_data['auto_entry_created'] = False
            if not is_valid:
                member_data['log_message'] = f"Membership expired for {member.first_name} {member.last_name}."
            elif not member.isactive:
                member_data['log_message'] = f"Member account is inactive for {member.first_name} {member.last_name}."
        
        return JsonResponse(member_data)
    
    except MembershipDetails.DoesNotExist:
        return JsonResponse({"error": "Member not found"}, status=404)
    except Exception as e:
        return JsonResponse({"error": "An unexpected error occurred.", "details": str(e)}, status=500)

@login_required
def membership_dashboard(request):
    # Get username from session
    username = request.session.get('username')
    
    if not username:
        # Handle case where user is not logged in
        return render(request, 'error.html', {'error': 'User not logged in'})
    
    try:
        # Get membership details
        membership = MembershipDetails.objects.get(user_id=username)
        membership_code = membership.membership_code
        
        # Current date for calculations
        today = timezone.now().date()
        
        # Calculate due soon threshold (2 days from now)
        due_soon_threshold = today + timedelta(days=2)
        
        # Get currently borrowed books (return_date is null)
        currently_borrowed = CirculationTransaction.objects.filter(
            membership_code=membership_code,
            return_date__isnull=True
        ).count()
        
        # Get due soon books (due date within 2 days and not returned)
        due_soon = CirculationTransaction.objects.filter(
            membership_code=membership_code,
            due_date__lte=due_soon_threshold,
            due_date__gte=today,
            return_date__isnull=True
        ).count()
        
        # Get overdue books (due date passed and not returned)
        overdue = CirculationTransaction.objects.filter(
            membership_code=membership_code,
            due_date__lt=today,
            return_date__isnull=True
        ).count()
        
        # Get latest 3 borrowed books with catalog details
        latest_books = []
        transactions = CirculationTransaction.objects.filter(
            membership_code=membership_code,
            return_date__isnull=True
        ).select_related('catalog').order_by('-issue_date')[:3]
        open_pdf_url = request.session.get("open_pdf_url")  # saved during login
        for transaction in transactions:
            book_data = {
                'transaction': transaction,
                'title': transaction.catalog.title if transaction.catalog else 'Unknown Title',
                'author': transaction.catalog.author if transaction.catalog and transaction.catalog.author else 'Unknown Author',
                'issue_date': transaction.issue_date,
                'due_date': transaction.due_date,
                'cover_image': get_book_cover(transaction.catalog) if transaction.catalog else None
            }
            latest_books.append(book_data)
        
        context = {
            'username': username,
            'membership_code': membership_code,
            'currently_borrowed': currently_borrowed,
            'due_soon': due_soon,
            'overdue': overdue,
            'latest_books': latest_books,
            'today': today,
            'open_pdf_url': open_pdf_url,   # send to template
        }
        
        return render(request, 'L01/Dashboard/member_dashboard.html', context)
        
    except MembershipDetails.DoesNotExist:
        return render(request, 'error.html', {'error': 'Membership not found'})
    except Exception as e:
        return render(request, 'error.html', {'error': str(e)})

def get_book_cover(catalog):
    """Get book cover image path from BookCatalog"""
    try:
        if catalog and catalog.front_page_photo:
            # Use the front_page_photo field directly
            file_path = Path(settings.MEDIA_ROOT) / Path(catalog.front_page_photo.replace("\\", "/"))
            if file_path.exists():
                return f"{settings.MEDIA_URL}{catalog.front_page_photo.replace('\\', '/')}"
        
        # Return default book cover if no image found
        return "{% static 'images/default-book-cover.jpg' %}"
    except Exception as e:
        print(f"Error getting book cover: {e}")
        # Return default book cover if any error occurs
        return "{% static 'images/default-book-cover.jpg' %}"
    
def get_borrowing_history(request):
    """AJAX view to get member's borrowing history"""
    username = request.session.get('username')
    
    if not username:
        return JsonResponse({'success': False, 'error': 'User not logged in'})
    
    try:
        # Get membership details
        membership = MembershipDetails.objects.get(user_id=username)
        membership_code = membership.membership_code
        
        # Get all circulation transactions for this member
        transactions = CirculationTransaction.objects.filter(
            membership_code=membership_code
        ).select_related('catalog', 'return_condition').order_by('-issue_date')
        
        history_data = []
        for transaction in transactions:
            # Determine status based on dates
            status = "Issued"
            if transaction.return_date:
                status = "Returned"
            elif transaction.due_date and transaction.due_date < timezone.now().date():
                status = "Overdue"
            elif transaction.due_date and transaction.due_date <= timezone.now().date() + timedelta(days=2):
                status = "Due Soon"
            
            history_data.append({
                'book_title': transaction.catalog.title if transaction.catalog else 'Unknown Title',
                'author': transaction.catalog.author if transaction.catalog and transaction.catalog.author else 'Unknown Author',
                'issue_date': transaction.issue_date.strftime('%b %d, %Y') if transaction.issue_date else 'N/A',
                'return_date': transaction.return_date.strftime('%b %d, %Y') if transaction.return_date else None,
                'status': status,
                'return_condition': transaction.return_condition.status_name if transaction.return_condition else 'N/A'
            })
        
        return JsonResponse({
            'success': True,
            'history': history_data
        })
        
    except MembershipDetails.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Membership not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
    
def view_catalogue_login_page(request):
    try:
        # Get username from session safely
        username = request.session.get('username')
        
        # Initialize member variables
        member_id = None
        member_details = None
        library_name_from_session = None
        library_address = None
        library_phone = None
        user_image_url = None
        transaction_details = []
        
        # Get library_code from session
        library_code_from_session = request.session.get('library_db', None)
        
        # If library_code is provided in session, get library details from tbl_librarymasterL01
        if library_code_from_session:
            try:
                library = tbl_librarymasterL01.objects.filter(library_code__iexact=library_code_from_session).first()
                if library:
                    library_name_from_session = library.library_name
                    library_address = library.location
                    library_phone = library.contact_phone
            except Exception:
                pass
        
        # If username exists, get the member details from tbl_membershipdetails using user_id field
        if username:
            try:
                # Get the member using user_id field which matches the username from session
                member = MembershipDetails.objects.get(user_id=username)
                member_id = member.id
                
                # Also store member_id in session for future use
                request.session['member_id'] = member_id
                
                # Get user image from tbl_documentdetails
                try:
                    document = DocumentDetails.objects.filter(
                        membership_id=member_id, 
                        isactive=1
                    ).first()
                    if document and document.file_path:
                        user_image_url = document.file_path
                except Exception:
                    pass
                
                # Get transaction details from tbl_circulation_transaction
                try:
                    transactions = CirculationTransaction.objects.filter(
                        member_id=member_id
                    ).select_related('catalog')  # Join with BookCatalog table
                    
                    for transaction in transactions:
                        if transaction.catalog:  # Check if catalog exists
                            transaction_details.append({
                                'book_title': transaction.catalog.title or 'Not available',
                                'author': transaction.catalog.author or 'Not available',
                                'issue_date': transaction.issue_date.strftime('%d-%b-%Y') if transaction.issue_date else 'Not set',
                                'due_date': transaction.due_date.strftime('%d-%b-%Y') if transaction.due_date else 'Not set',
                                'return_date': transaction.return_date.strftime('%d-%b-%Y') if transaction.return_date else 'Not returned',
                                'due_date_raw': transaction.due_date  # for comparison
                            })
                except Exception:
                    pass
                
                # Prepare member details for template
                member_details = {
                    'id': member.id,
                    'name': f"{member.first_name or ''} {member.middle_name or ''} {member.last_name or ''}".strip(),
                    'address': member.local_address or 'Not available',
                    'mobile_no': member.mobile_no or 'Not available',
                    'membership_from': member.from_date.strftime('%d-%b-%Y') if member.from_date else 'Not set',
                    'membership_to': member.to_date.strftime('%d-%b-%Y') if member.to_date else 'Not set',
                    'membership_code': member.membership_code or 'Not available',
                    'library_name': library_name_from_session or member.library_name or 'Not available',
                    'email': member.email or 'Not available',
                    'user_id': member.user_id,
                    'library_address': library_address or 'Not available',
                    'library_phone': library_phone or 'Not available',
                    'user_image_url': user_image_url
                }
                
            except MembershipDetails.DoesNotExist:
                pass
            except Exception:
                pass
        
        # Prepare context with media URL, username, member_id and member_details
        context = {
            "MEDIA_URL": settings.MEDIA_URL,
            "username": username,
            "member_id": member_id,
            "member_details": member_details,
            "library_name_from_session": library_name_from_session,
            "transaction_details": transaction_details,
            "current_date": date.today(),  # your existing variable
            "today": date.today()          # added for due_date comparison
        }
        
        # Check if this is an AJAX request for library card data
        if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.GET.get('member_id'):
            member_id = (
                request.GET.get("member_id") or 
                request.POST.get("member_id") or
                member_id or
                request.session.get('member_id')
            )

            library_code = request.session.get('library_db', None)

            if not member_id:
                return JsonResponse({"status": "error", "message": "Member ID missing"})

            try:
                member = MembershipDetails.objects.get(id=member_id)
                
                if not library_code:
                    library_code = (
                        getattr(member, 'library_name', '') or
                        getattr(member, 'membership_code', '')
                    ).strip()

                if not library_code:
                    return JsonResponse({
                        "status": "error", 
                        "message": "Library code missing"
                    })

                library = tbl_librarymasterL01.objects.filter(library_code__iexact=library_code).first()

                if library:
                    return JsonResponse({
                        "status": "success",
                        "library_code": library_code,
                        "library_name": library.library_name,
                        "library_address": getattr(library, "location", "Not available"),
                        "library_phone": getattr(library, "contact_phone", "Not available"),
                    })
                else:
                    return JsonResponse({
                        "status": "success",
                        "library_code": library_code,
                        "library_name": member_details.get('library_name', 'Not available') if member_details else 'Not available',
                        "library_address": "Not available",
                        "library_phone": "Not available",
                    })

            except MembershipDetails.DoesNotExist:
                return JsonResponse({
                    "status": "error", 
                    "message": "Invalid Member ID"
                })
            except Exception as e:
                return JsonResponse({
                    "status": "error", 
                    "message": f"Server error: {str(e)}"
                })
        
        # Regular page render
        return render(request, "L01/view_catalogue_login_page.html", context)
        
    except KeyError:
        return render(request, "L01/view_catalogue_login_page.html", {
            "MEDIA_URL": settings.MEDIA_URL,
            "username": None,
            "member_id": None,
            "member_details": None,
            "library_name_from_session": None,
            "transaction_details": [],
            "current_date": date.today(),
            "today": date.today()
        })
        
    except Exception:
        return render(request, "L01/view_catalogue_login_page.html", {
            "MEDIA_URL": settings.MEDIA_URL,
            "username": None,
            "member_id": None,
            "member_details": None,
            "library_name_from_session": None,
            "transaction_details": [],
            "current_date": date.today(),
            "today": date.today()
        })
        
def book_info_login(request):
    try:
        # Get cat_ref_num from GET params
        cat_ref_num = request.GET.get("cat_ref_num")
        if not cat_ref_num:
            return render(request, "L01/error.html", {"message": "cat_ref_num not provided"})

        # Fetch the book object
        book = get_object_or_404(BookCatalog.objects.using('L01'), cat_ref_num=cat_ref_num)

        # Build URLs for front and last pages
        front_page_url = request.build_absolute_uri(f"/media/{book.front_page_photo}") if book.front_page_photo else ""
        last_page_url = request.build_absolute_uri(f"/media/{book.last_page_photo}") if book.last_page_photo else ""

        # Pass data to template
        context = {
            "book": book,
            "front_page_url": front_page_url,
            "last_page_url": last_page_url,
        }

        return render(request, "L01/book_info_login.html", context)

    except Exception as e:
        print(f"Error in book_info_login: {e}")
        return render(request, "L01/error.html", {"message": "Something went wrong"})
    
@login_required
def save_eod_log(request):
    try:
        if request.method == "POST":

            # Step 1: Get all returned transaction IDs
            all_ids_raw = request.POST.get("all_ids", "")
            all_ids = [int(x) for x in all_ids_raw.split(",") if x]

            # Step 2: Validation: every book MUST be checked
            for tid in all_ids:
                if not request.POST.get(f"shelved_{tid}"):
                    return messages.error(("Please confirm that all books are put on shelf and then try again."))
                    # return JsonResponse({
                    #     "success": False,
                    #     "error": "Please confirm that all books are put on shelf and then try again."
                    # })

            # Step 3: Create master EOD entry
            today = timezone.now().date()
            eod_log = EODLog.objects.create(
                date=today,
                is_active=True,
                created_by=request.user,
                updated_by=request.user,
            )

            # Step 4: Insert details for each returned book 
            for tid in all_ids:
                ciculation_id = get_object_or_404(CirculationTransaction,id =tid)
                catalog_id = ciculation_id.catalog.cat_ref_num
                barcode = request.POST.get(f"barcode_{tid}", "")
                is_shelved = 1  # all must be checked to reach here

                cat_obj = BookCatalog.objects.get(cat_ref_num=catalog_id)

                BookReturnLog.objects.create(
                    eod_log=eod_log,
                    cat_rem_num=cat_obj,
                    barcode=barcode,
                    is_shelved=is_shelved,
                    created_by=request.user,
                    updated_by=request.user,
                )

            return redirect("payment_report")

    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)})

@login_required
def visit_Library_catalogue(request):
    try:
        # Session checks
        library_code = request.session.get('library_db')
        username = request.session.get('username')
        user_id = request.session.get('user_id')
        role_id = request.session.get('role_id')

        if not all([library_code, username, user_id, role_id]):
            messages.warning(request, "Session expired or invalid. Please login again.")
            return render(request, "L01/LibraryCateVisit/visit_library_Cate.html", {})

        subjects_qs = SubjectTypeMaster.objects.filter(is_active=1)
        subjects = []
        for s in subjects_qs:
            s.id_enc = enc(str(s.id))  # your encoding function
            subjects.append(s)

        first_subject = subjects[0] if subjects else None

        if first_subject:
            books = BookCatalog.objects.filter(subject=first_subject).select_related('subject', 'material')
        else:
            books = BookCatalog.objects.none()

        # Pagination: 8 books per page
        paginator = Paginator(books, 8)
        page_number = request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)

        # Encode book IDs
        for b in page_obj:
            b.bookIdEnc = enc(str(b.cat_ref_num)) if 'enc' in globals() else b.cat_ref_num
            
        # --- NEW ARRIVALS LOGIC ---
        thirty_days_ago = timezone.now() - timedelta(days=30)
        new_books = BookCatalog.objects.filter(created_at__gte=thirty_days_ago).order_by('-created_at')

        if not new_books.exists():
            # Fallback: last 10 books
            new_books = BookCatalog.objects.all().order_by('-cat_ref_num')[:10]

        for b in new_books:
            b.bookIdEnc = enc(str(b.cat_ref_num)) if 'enc' in globals() else b.cat_ref_num

        context = {
            'subjects': subjects,
            'books': page_obj,
            'paginator': paginator,
            'page_number': int(page_number),
            'first_subject_id_enc': first_subject.id_enc if first_subject else None,
            'MEDIA_URL': settings.MEDIA_URL,
            'new_books': new_books,  # Pass to template
        }

        return render(request, "L01/LibraryCateVisit/visit_library_Cate.html", context)

    except Exception as e:
        print(f"Error: {e}")
        return render(request, "L01/LibraryCateVisit/visit_library_Cate.html", {})

@login_required
def get_books_by_subject(request):
    try:
        subject_id_enc = request.GET.get('subject_id')
        subject_id = dec(subject_id_enc)

        search = request.GET.get('search', '').strip()

        # Base queryset
        all_books = BookCatalog.objects.filter(subject_id=subject_id).select_related('subject', 'material')

        # Search filter
        if search:
            all_books = all_books.filter(
                Q(title__icontains=search) |
                Q(author__icontains=search)
            )

        # Encode book IDs
        for b in all_books:
            b.bookIdEnc = enc(str(b.cat_ref_num)) if 'enc' in globals() else b.cat_ref_num

        # Pagination
        paginator = Paginator(all_books, 8)
        page_number = request.GET.get('page', 1)
        books_page = paginator.get_page(page_number)

        context = {
            'books': books_page,
            'MEDIA_URL': settings.MEDIA_URL,
            'subject_id_enc': subject_id_enc
        }
        return render(request, "L01/LibraryCateVisit/book_list_partial.html", context)

    except Exception as e:
        print("Error fetching books for subject:", e)
        return JsonResponse({'error': 'Failed to fetch books'}, status=500)
    
def membership_card(request):
    username = request.session.get('username')
    member_id = None
    member_details = None
    library_name_from_session = None
    library_address = None
    library_phone = None
    user_image_url = None
    transaction_details = []

    # Get library_code from session
    library_code_from_session = request.session.get('library_db', None)

    # Fetch library details
    if library_code_from_session:
        try:
            library = tbl_librarymasterL01.objects.filter(library_code__iexact=library_code_from_session).first()
            if library:
                library_name_from_session = library.library_name
                library_address = library.location
                library_phone = library.contact_phone
        except Exception:
            pass

    # Fetch member details
    if username:
        try:
            member = MembershipDetails.objects.get(user_id=username)
            member_id = member.id
            request.session['member_id'] = member_id

            # Fetch user image
            try:
                document = DocumentDetails.objects.filter(
                    membership_id=member_id, 
                    isactive=1
                ).first()

                if document and document.file_path:
                    if document.file_path.startswith(settings.MEDIA_URL):
                        user_image_url = document.file_path
                    else:
                        user_image_url = f"{settings.MEDIA_URL}{document.file_path}"
            except Exception:
                pass

            # Fetch full transaction list (NO PAGINATION)
            try:
                transactions = (
                    CirculationTransaction.objects
                    .filter(member_id=member_id)
                    .select_related('catalog')
                    .order_by('-issue_date')
                )

                for transaction in transactions:
                    is_overdue = False
                    if transaction.due_date and transaction.return_date is None:
                        is_overdue = transaction.due_date < date.today()

                    transaction_details.append({
                        'book_title': transaction.catalog.title if transaction.catalog else 'Not available',
                        'author': transaction.catalog.author if transaction.catalog else 'Not available',
                        'issue_date': transaction.issue_date.strftime('%d-%b-%Y') if transaction.issue_date else 'Not set',
                        'due_date': transaction.due_date.strftime('%d-%b-%Y') if transaction.due_date else 'Not set',
                        'return_date': transaction.return_date.strftime('%d-%b-%Y') if transaction.return_date else 'Not returned',
                        'due_date_raw': transaction.due_date,
                        'is_overdue': is_overdue
                    })

            except Exception as e:
                print(f"Error fetching transactions: {e}")

            # Prepare member details
            member_details = {
                'id': member.id,
                'name': f"{member.first_name_mar or ''} {member.middle_name_mar or ''} {member.last_name_mar or ''}".strip(),
                'address': member.local_address or 'Not available',
                "member_type":member.membership.membership_type,
                'mobile_no': member.mobile_no or 'Not available',
                'membership_from': member.from_date.strftime('%d-%b-%Y') if member.from_date else 'Not set',
                'membership_to': member.to_date.strftime('%d-%b-%Y') if member.to_date else 'Not set',
                'membership_code': member.membership_code or 'Not available',
                'library_name':  member.library_name_mar or 'Not available',
                'email': member.email or 'Not available',
                'user_id': member.user_id,
                'library_address': library_address or 'Not available',
                'library_phone': library_phone or 'Not available',
                'user_image_url': user_image_url
            }

        except MembershipDetails.DoesNotExist:
            member_details = None

    # Context WITHOUT pagination
    context = {
        "MEDIA_URL": settings.MEDIA_URL,
        "username": username,
        "member_id": member_id,
        "member_details": member_details,
        "library_name_from_session": library_name_from_session,
        "transaction_details": transaction_details,
        "current_date": date.today().strftime('%d-%b-%Y'),
        "today": date.today(),
    }

    return render(request, "Master/membership_card.html", context)

@login_required
def view_book_detail(request):
    try:
        library_code = request.session.get('library_db')
        username = request.session.get('username')
        user_id = request.session.get('user_id')
        role_id = request.session.get('role_id')

        if not all([library_code, username, user_id, role_id]):
            messages.warning(request, "Session expired or invalid. Please login again.")
            return render(request, "L01/LibraryCateVisit/visit_library_Cate.html", {})
        
        cat_ref_num_enc = request.GET.get('cat_ref_num')
        if not cat_ref_num_enc:
            messages.error(request, "Invalid book request.")
            return redirect("visit_library_catalogue")

        cat_ref_num = dec(cat_ref_num_enc)

        # Fetch the book
        book = get_object_or_404(BookCatalog, cat_ref_num=cat_ref_num)

        # Collect images
        images = []
        if book.front_page_photo:
            images.append(book.front_page_photo)
        if book.last_page_photo:
            images.append(book.last_page_photo)

        # Fetch all circulation rows for this book
        circulation_qs = CirculationCopyStatus.objects.filter(bookcatalog_id=book.cat_ref_num)
        total_qty = circulation_qs.count()

        # Get status master entries for current and processing statuses
        status_on_shelf = status_master.objects.filter(status_name__iexact="On-Shelf").first()
        status_unknown = "Not Available"

        # Count how many copies are currently "On-Shelf"
        current_on_shelf_count = circulation_qs.filter(current_status=status_on_shelf).count() if status_on_shelf else 0

        # Decide display values for availability
        if total_qty > 0:
            if current_on_shelf_count > 0:
                current_status_display = "On-Shelf"
                availability_text = f"{current_on_shelf_count} of {total_qty} available"
            else:
                current_status_display = status_unknown
                availability_text = f"0 of {total_qty} available"
        else:
            current_status_display = status_unknown
            availability_text = "-"

        # Calculate location display **only for On-Shelf copies**
        location_counts = {}
        if status_on_shelf:
            on_shelf_copies = circulation_qs.filter(current_status=status_on_shelf)
            for circ in on_shelf_copies:
                if circ.shelf_location:
                    loc_name = circ.shelf_location.location_name
                    location_counts[loc_name] = location_counts.get(loc_name, 0) + 1

        if location_counts:
            # Join multiple locations with count if multiple exist
            location_display = ", ".join([f"{loc} ({count})" for loc, count in location_counts.items()])
        else:
            location_display = "Unknown"
            
        # --- REVIEWS WITH USER JOIN ---
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        # Get all reviews for this book ordered by latest
        all_reviews = BookReview.objects.filter(book=book).order_by('-created_at')
        
        # Get distinct user IDs from reviews
        user_ids = all_reviews.values_list('user_id', flat=True).distinct()
        
        # Fetch all users in one query
        users = User.objects.filter(id__in=user_ids)
        
        # Create a dictionary for quick lookup: user_id -> user object
        user_dict = {user.id: user for user in users}
        
        # Add user objects to reviews
        reviews_with_users = []
        for review in all_reviews:
            # Create a copy of the review with added user information
            review.user_obj = user_dict.get(review.user_id)
            reviews_with_users.append(review)
        
        # Get current user from session
        current_user_id = request.session.get('user_id')
        
        # Check if current user has reviewed
        user_review = None
        if current_user_id:
            try:
                user_review = all_reviews.filter(user_id=int(current_user_id)).first()
                if user_review:
                    user_review.user_obj = user_dict.get(int(current_user_id))
            except (ValueError, TypeError):
                user_review = None
        
        # Calculate average rating
        avg_rating = all_reviews.aggregate(avg=models.Avg('rating'))['avg'] or 0
        total_reviews = all_reviews.count()
        
        # Pagination - Show only 5 reviews per page
        reviews_per_page = 5
        show_pagination = total_reviews > reviews_per_page
        
        if show_pagination:
            # Paginate the reviews_with_users list
            paginator = Paginator(reviews_with_users, reviews_per_page)
            page_number = request.GET.get('page', 1)
            
            try:
                reviews_page = paginator.page(page_number)
            except PageNotAnInteger:
                reviews_page = paginator.page(1)
            except EmptyPage:
                reviews_page = paginator.page(paginator.num_pages)
        else:
            # If 5 or fewer reviews, show all
            reviews_page = reviews_with_users

        context = {
            'book': book,
            'images': images,
            'MEDIA_URL': settings.MEDIA_URL,
            'total_qty': total_qty,
            'current_status_display': current_status_display,
            'availability_text': availability_text,
            'location_display': location_display,
            'reviews': reviews_page,  # Now includes user objects
            'user_review': user_review,
            'avg_rating': round(avg_rating, 1),
            'total_reviews': total_reviews,
            'show_pagination': show_pagination,
            'reviews_per_page': reviews_per_page,
            'current_params': request.GET.copy(),
            'cat_ref_num_enc': cat_ref_num_enc,
        }

        return render(request, "L01/LibraryCateVisit/view_book_detail.html", context)

    except Exception as e:
        print("Error in view_book_detail:", e)
        messages.error(request, "Unable to load book details.")
        return redirect("visit_library_catalogue")

@csrf_exempt
@login_required
def submit_review(request):

    if request.method == "POST":
        try:
            # Get data from request
            if request.content_type == 'application/json':
                data = json.loads(request.body)
                book_id = data.get('book_id')
                rating = int(data.get('rating'))
                review_text = data.get('review')
            else:
                book_id = request.POST.get('book_id')
                rating = int(request.POST.get('rating'))
                review_text = request.POST.get('review')
            
            user_id = request.session.get('user_id')
            library_code = request.session.get('library_db')

            # Validate required fields
            if not all([book_id, rating, review_text, user_id]):
                return JsonResponse({
                    "success": False, 
                    "message": "Missing required fields"
                }, status=400)

            # Get book
            try:
                book = BookCatalog.objects.get(cat_ref_num=book_id)
            except BookCatalog.DoesNotExist:
                return JsonResponse({
                    "success": False, 
                    "message": "Book not found"
                }, status=404)

            # Prevent multiple reviews
            if BookReview.objects.filter(book=book, user_id=user_id).exists():
                return JsonResponse({
                    "success": False, 
                    "message": "You have already reviewed this book."
                })

            # Create review
            BookReview.objects.create(
                book=book,
                user_id=user_id,
                rating=rating,
                review=review_text,
                library_code=library_code
            )

            # Get latest reviews with user information
            from django.contrib.auth import get_user_model
            User = get_user_model()
            
            all_reviews = BookReview.objects.filter(book=book).order_by('-created_at')
            
            # Get user IDs from reviews
            user_ids = all_reviews.values_list('user_id', flat=True).distinct()
            
            # Fetch users
            users = User.objects.filter(id__in=user_ids)
            user_dict = {user.id: user for user in users}
            
            # Add user objects to reviews
            reviews_with_users = []
            for review in all_reviews:
                review.user_obj = user_dict.get(review.user_id)
                reviews_with_users.append(review)
            
            # Calculate average rating
            avg_rating = all_reviews.aggregate(avg=models.Avg('rating'))['avg'] or 0
            total_reviews = all_reviews.count()
            
            # Get only FIRST 5 reviews for display
            from django.core.paginator import Paginator
            paginator = Paginator(reviews_with_users, 5)
            first_page_reviews = paginator.page(1)
            
            # Render reviews HTML
            reviews_html = render_to_string(
                "L01/LibraryCateVisit/review_list.html", 
                {
                    "reviews": first_page_reviews,
                    "MEDIA_URL": settings.MEDIA_URL
                }
            )

            return JsonResponse({
                "success": True,
                "message": "Review submitted successfully!",
                "reviews_html": reviews_html,
                "avg_rating": round(avg_rating, 1),
                "total_reviews": total_reviews,
                "has_next_page": first_page_reviews.has_next(),
                "total_pages": paginator.num_pages,
                "current_page": 1
            })
            
        except ValueError as e:
            print(f"ValueError: {e}")
            return JsonResponse({
                "success": False, 
                "message": "Invalid rating value"
            }, status=400)
        except Exception as e:
            print(f"Error in submit_review: {e}")
            import traceback
            traceback.print_exc()
            return JsonResponse({
                "success": False, 
                "message": f"Server error: {str(e)}"
            }, status=500)
    
    return JsonResponse({
        "success": False, 
        "message": "Invalid request method"
    }, status=405)
    
@csrf_exempt
def clear_pdf_session(request):
    request.session.pop("open_pdf_url", None)
    return JsonResponse({"status": "ok"})