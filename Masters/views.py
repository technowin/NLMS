import json
import pydoc
import re
from urllib.parse import urlparse, unquote
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render,redirect,get_object_or_404
from django.contrib.auth import authenticate, login ,logout,get_user_model
from Account.forms import RegistrationForm
from Account.models import *
from Masters.forms import LibraryEventForm
from Masters.models import *
from L01.models import *
import Db 
import bcrypt
from django.utils.text import slugify
from django.contrib.auth.decorators import login_required
from NLMS.encryption import *
from django.http import HttpResponse
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph
from Account.utils import decrypt_email, encrypt_email
import requests
import traceback
import pandas as pd
from django.core.files.storage import FileSystemStorage
from django.conf import settings
from django.contrib import messages
import openpyxl
from openpyxl.styles import Font, Border, Side
import calendar
from datetime import datetime, timedelta
from django.utils import timezone
from datetime import timedelta
from django.db.models import Q, Count
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.tokens import AccessToken
from django.utils import timezone
from Account.models import *
from Masters.models import *
from Account.db_utils import callproc
from django.views.decorators.csrf import csrf_exempt
import os
from django.urls import reverse
from NLMS.settings import *
import logging
from django.http import FileResponse, Http404
import mimetypes
from datetime import date
import re
from django.db import transaction
import re
from indic_transliteration.sanscript import transliterate, DEVANAGARI, HK
logger = logging.getLogger(__name__)
from administration.models import *
from django.db.models import F
from django.utils.text import get_valid_filename
from services.file_storage_service import file_storage_service
import boto3
from botocore.exceptions import ClientError
from django.http import HttpResponse, Http404, StreamingHttpResponse
import mimetypes
import uuid
from datetime import datetime as dt, date
from NLMS.access_control import no_direct_access

# Part First While Filling Membership Form

@login_required
def masters(request):
    pre_url = request.META.get('HTTP_REFERER')
    header, data = [], []
    entity = type = name = id = text_name = dpl = dp = em = mb = forms = sf = ''

    try:
        if request.user.is_authenticated ==True:                
                global user,role_id
                user = request.user.id    
                role_id = request.user.role_id 
        if request.method=="GET":
            entity = request.GET.get('entity', '')
            sf = request.GET.get('sf', '')
            type = request.GET.get('type', '')
            datalist1= callproc("stp_get_masters",[entity,type,'name',user])
            name = datalist1[0][0]
            header = callproc("stp_get_masters", [entity, type, 'header',user])
            rows = callproc("stp_get_masters",[entity,type,'data',user])
            if entity == 'form_master':
                forms = callproc("stp_get_forms",['view_form',user])  
                type = 'i'
                if sf == '' or None:
                   sf =  forms[0][0]   
                header = callproc("stp_get_view_form_header",[sf])          
                rows = callproc("stp_get_view_forms",[sf])          
            if entity == 'su':
                dpl = callproc("stp_get_dropdown_values",['dept'])

            id = request.GET.get('id', '')
            if type=='ed' and id != '0':
                if id != '0' and id != '':
                    id = dec(id)
                rows = callproc("stp_get_masters",[entity,type,'data',id])
                text_name = rows[0][0]
                if entity == 'su':
                    em = rows[0][1]
                    mb = rows[0][2]
                    dp = rows[0][3]
                id = enc(id)
            data = []
            for row in rows:
                encrypted_id = enc(str(row[0]))
                data.append((encrypted_id,) + row[1:])

        if request.method=="POST":
            entity = request.POST.get('entity', '')
            id = request.POST.get('id', '')
            dp = request.POST.get('dp', '')
            em = request.POST.get('em', '')
            mb = request.POST.get('mb', '')
            if id != '0' and id != '':
                id = dec(id)
            name = request.POST.get('text_name', '')
            if entity == 'su':
                datalist1= callproc("stp_post_user_masters",[id,name,em,mb,dp,user])
            else: datalist1= callproc("stp_post_masters",[entity,id,name,user])

            if datalist1[0][0] == 'insert':
                messages.success(request, 'Data inserted successfully !')
            elif datalist1[0][0] == 'update':
                messages.success(request, 'Data updated successfully !')
            elif datalist1[0][0] == 'exist':
                messages.error(request, 'Data already exist !')
            
                          
    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        fun = tb[0].name
        callproc("stp_error_log",[fun,str(e),user])  
        messages.error(request, 'Oops...! Something went wrong!')
    finally:
        Db.closeConnection()
        if request.method=="GET":
             return render(request,'Master/index.html',
              {'entity':entity,'forms':forms,'sf':sf,'type':type,'name':name,'header':header,'data':data,
              'id':id,'text_name':text_name,'dp':dp,'em':em,'mb':mb,'dpl':dpl})
        elif request.method=="POST":  
            new_url = f'/masters?entity={entity}&type=i'
            return redirect(new_url) 
 
def sample_xlsx(request):
    pre_url = request.META.get('HTTP_REFERER')
    response =''
    global user
    user  = request.session.get('user_id', '')
    try:
        workbook = openpyxl.Workbook()
        sheet = workbook.active
        sheet.title = 'Sample Format'
        columns = []
        if request.method=="GET":
            entity = request.GET.get('entity', '')
            type = request.GET.get('type', '')
        if request.method=="POST":
            entity = request.POST.get('entity', '')
            type = request.POST.get('type', '')
        file_name = {'em': 'Employee Master','sm': 'Worksite Master','cm': 'Company Master','r': 'Roster'}[entity]
        columns = callproc("stp_get_masters", [entity, type, 'sample_xlsx',user])
        if columns and columns[0]:
            columns = [col[0] for col in columns[0]]

        black_border = Border(
            left=Side(border_style="thin", color="000000"),
            right=Side(border_style="thin", color="000000"),
            top=Side(border_style="thin", color="000000"),
            bottom=Side(border_style="thin", color="000000")
        )
        
        for col_num, header in enumerate(columns, 1):
            cell = sheet.cell(row=1, column=col_num)
            cell.value = header
            cell.font = Font(bold=True)
            cell.border = black_border
        
        for col in sheet.columns:
            max_length = 0
            column = col[0].column_letter  
            for cell in col:
                if len(str(cell.value)) > max_length:
                    max_length = len(str(cell.value))
                    
            adjusted_width = max_length + 2 
            sheet.column_dimensions[column].width = adjusted_width  
        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename="' + str(file_name) +" "+str(datetime.now().strftime("%d-%m-%Y")) + '.xlsx"'
        workbook.save(response)
    
    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        fun = tb[0].name
        callproc("stp_error_log",[fun,str(e),user])  
        messages.error(request, 'Oops...! Something went wrong!')
    finally:
        return response      

@login_required
def Test_sample(request):
    try:
        if request.user.is_authenticated ==True:                
                global user,role_id
                user = request.user.id    
                role_id = request.user.role_id 
        if request.method=="GET":
            print("GET")
    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        fun = tb[0].name
        callproc("stp_error_log",[fun,str(e),user])  
        messages.error(request, 'Oops...! Something went wrong!')
    finally:
        Db.closeConnection()
        if request.method=="GET":
             return render(request,'Master/Test_sample.html')
         
# @login_required
# def LMS_Dashboard(request):
#     try:
#         if request.user.is_authenticated ==True:                
#                 global user,role_id
#                 user = request.user.id    
#                 role_id = request.user.role_id 
#         if request.method=="GET":
#             print("GET")
#     except Exception as e:
#         tb = traceback.extract_tb(e.__traceback__)
#         fun = tb[0].name
#         callproc("stp_error_log",[fun,str(e),user])  
#         messages.error(request, 'Oops...! Something went wrong!')
#     finally:
#         Db.closeConnection()
#         if request.method=="GET":
#              return render(request,'Workflow/index.html')

@login_required
def LMS_Dashboard(request):
    try:
        if request.user.is_authenticated:
            global user, role_id
            user = request.user.id
            role_id = request.user.role_id

        if request.method == "GET":
            print("GET")

            # Get today's date
            today = date.today()

            # # Fetch today's returned books
            # returned_books = CirculationTransaction.objects.filter(
            #     return_date=today
            # )

            context = {
                # "returned_books": returned_books
            }

            return render(request, 'Workflow/index.html', context)

    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        fun = tb[0].name
        callproc("stp_error_log", [fun, str(e), user])
        messages.error(request, 'Oops...! Something went wrong!')

# notepad ++ book_catalog_index
@no_direct_access
@login_required
def book_catalog_index(request):
    if not request.user.is_authenticated:
        # Clear any session flags
        if '_session_expired' in request.session:
            request.session.pop('_session_expired')
        messages.warning(request, "Your session has expired. Please log in again.")
        return redirect('library_list')
    user = request.user.id
    try:
        catalogs = (
            BookCatalog.objects
            .select_related("subject", "material")
            .order_by("-cat_ref_num")
        )

        # 🔹 Fetch all statuses once
        status_map = {
            s.status_id: s
            for s in status_master.objects.all()
        }

        for c in catalogs:
            c.status_obj = status_map.get(c.status_id)
            c.encrypted_id = enc(str(c.cat_ref_num))

        return render(
            request,
            'Master/book_catalog_index.html',
            {"catalogs": catalogs}
        )

    except Exception as e:
        callproc("stp_error_log", ["book_catalog_index", str(e), user])
        messages.error(request, "Oops! Something went wrong.")
        return render(
            request,
            'Master/book_catalog_index.html',
            {"catalogs": []}
        )

# Book Catalog Create
@no_direct_access 
@login_required 
def book_catalog_create(request):
    try:
        if not request.user.is_authenticated:
            # Clear any session flags
            if '_session_expired' in request.session:
                request.session.pop('_session_expired')
            messages.warning(request, "Your session has expired. Please log in again.")
            return redirect('library_list')
        
        user = request.user.id

        # ---------- AJAX endpoints ----------
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            action = request.GET.get('action', '').strip()
            response_data = []

            # --- Authors Dropdown ---
            if action == "get_authors":
                language_id_encrypted = request.GET.get('language_id', '').strip()
                if language_id_encrypted:
                    try:
                        language_id = dec(language_id_encrypted)
                        lang_obj = LanguageMaster.objects.filter(id=language_id).first()
                        lang_name = lang_obj.language_name.lower() if lang_obj else ""

                        if lang_name == "marathi":
                            response_data = AuthorMaster.objects.filter(is_active=True) \
                                .exclude(author_name_marathi__isnull=True) \
                                .values_list('author_name_marathi', flat=True) \
                                .distinct().order_by('author_name_marathi')
                        else:
                            response_data = AuthorMaster.objects.filter(is_active=True) \
                                .exclude(author_name_english__isnull=True) \
                                .values_list('author_name_english', flat=True) \
                                .distinct().order_by('author_name_english')
                    except Exception:
                        response_data = []

            # --- Publishers Dropdown ---
            elif action == "get_publishers":
                response_data = BookCatalog.objects.filter(~Q(publisher__exact=""), publisher__isnull=False) \
                    .values_list('publisher', flat=True).distinct().order_by('publisher')

            # --- Publication Places Dropdown ---
            elif action == "get_places":
                response_data = BookCatalog.objects.filter(~Q(publication_place__exact=""), publication_place__isnull=False) \
                    .values_list('publication_place', flat=True).distinct().order_by('publication_place')

            return JsonResponse({"data": list(response_data)})

        # ---------- GET Request ----------
        if request.method == "GET":
            languages = LanguageMaster.objects.filter(is_active=1)
            for lang in languages:
                lang.encrypted_id = enc(str(lang.id))

            subjects = SubjectTypeMaster.objects.filter(is_active=True)
            for sub in subjects:
                sub.encrypted_id = enc(str(sub.id))

            materials = MaterialTypeMaster.objects.filter(is_active=True)
            for mat in materials:
                mat.encrypted_id = enc(str(mat.id))

            # Years dropdown
            from datetime import datetime
            current_year = datetime.now().year
            years = list(range(current_year, 1899, -1))

            selected_language_id_encrypted = request.GET.get('language_id')
            if selected_language_id_encrypted:
                try:
                    selected_language_id = dec(selected_language_id_encrypted)
                    lang_obj = LanguageMaster.objects.filter(id=selected_language_id).first()
                except Exception:
                    lang_obj = languages[0] if languages else None
            else:
                lang_obj = languages[0] if languages else None

            lang_name = lang_obj.language_name.lower() if lang_obj else "english"

            # Author dropdown based on language
            if lang_name == "marathi":
                authors = AuthorMaster.objects.filter(is_active=True) \
                    .values_list('author_name_marathi', flat=True).distinct().order_by('author_name_marathi')
            else:
                authors = AuthorMaster.objects.filter(is_active=True) \
                    .values_list('author_name_english', flat=True).distinct().order_by('author_name_english')

            publishers = BookCatalog.objects.filter(~Q(publisher__exact=""), publisher__isnull=False) \
                .values_list('publisher', flat=True).distinct().order_by('publisher')

            publication_places = BookCatalog.objects.filter(~Q(publication_place__exact=""), publication_place__isnull=False) \
                .values_list('publication_place', flat=True).distinct().order_by('publication_place')

            context = {
                'languages': languages,
                'subjects': subjects,
                'materials': materials,
                'authors': authors,
                'publishers': publishers,
                'publication_places': publication_places,
                'years': years
            }
            return render(request, 'Master/book_catalog_create.html', context)

        # ---------- POST Request ----------
        
        # Notepad ++ book_catalog_create-Po
        
        if request.method == "POST":
            form_data = {
                "title": request.POST.get('title', '').strip(),
                "subtitle": request.POST.get('subtitle', '').strip(),
                "author": request.POST.get('author', '').strip(),
                "other_authors": request.POST.get('other_authors', '').strip(),
                "publisher": request.POST.get('publisher', '').strip(),
                "isbn": request.POST.get('isbn', '').strip(),
                "edition": request.POST.get('edition', '').strip(),
                "subject_id": dec(request.POST.get('subject_id', '').strip()) if request.POST.get('subject_id', '').strip() else '',
                "material_id": dec(request.POST.get('material_id', '').strip()) if request.POST.get('material_id', '').strip() else '',
                "remarks": request.POST.get('remarks', '').strip(),
                "keywords": request.POST.get('keywords', '').strip(),
                "language_id": dec(request.POST.get('language_id_hidden', '').strip()) if request.POST.get('language_id_hidden', '').strip() else '',
                "publication_place": request.POST.get('publication_place', '').strip(),
                "year_of_publication": request.POST.get('year_of_publication', '').strip(),
                "pages": request.POST.get('page_nos', '').strip(),
            }

            required_fields = ["title", "author", "publisher", "subject_id", "material_id", "language_id"]
            missing = [f for f in required_fields if not form_data[f]]
            if missing:
                messages.error(request, f"Please fill in all required fields: {', '.join(missing)}")
                return redirect('book_catalog_create')

            try:
                with transaction.atomic():
                    subject = SubjectTypeMaster.objects.filter(id=form_data["subject_id"]).first()
                    material = MaterialTypeMaster.objects.filter(id=form_data["material_id"]).first()
                    language = LanguageMaster.objects.filter(id=form_data["language_id"]).first()

                    author = form_data["author"]
                    other_authors = form_data.get("other_authors", "").strip()

                    # author transliteration logic
                    if contains_non_english(author):
                        authorEnglish = transliterate_to_english(author).lower()
                        authorMarathi = author
                    else:
                        authorEnglish = author.lower()
                        authorMarathi = None

                    if contains_non_english(other_authors):
                        otherAuthorEnglish = transliterate_to_english(other_authors).lower()
                        otherAuthorMarathi = other_authors
                    else:
                        otherAuthorEnglish = other_authors.lower()
                        otherAuthorMarathi = None

                    ClassificationNumber = f"{subject.subjectCode:03}" if subject and subject.subjectCode else "000"
                    author_name_clean = ''.join(filter(str.isalpha, authorEnglish))
                    CutterNumber = author_name_clean[:3].title() if author_name_clean else "XXX"
                    pub_year = form_data['year_of_publication'] or "0000"
                    call_number = f"{ClassificationNumber}.{CutterNumber}.{pub_year}"

                    # 🔴 UPDATED: Create or get AuthorMaster first
                    existing_author = AuthorMaster.objects.filter(author_name_english=authorEnglish).first()
                    
                    if not existing_author:
                        # Create new author
                        existing_author = AuthorMaster.objects.create(
                            author_short_name=CutterNumber,
                            author_name_english=authorEnglish,
                            author_name_other_english=otherAuthorEnglish,
                            author_name_marathi=authorMarathi,
                            author_name_other_marathi=otherAuthorMarathi,
                            detail_entered="Book Catalog Entry",
                            is_active=1,
                            created_by=user,
                            updated_by=user
                        )
                    else:
                        # Update existing author if needed
                        if not existing_author.author_short_name:
                            existing_author.author_short_name = CutterNumber
                            existing_author.save()

                    # 🔴 UPDATED: Create BookCatalog with author_fk and author_short_name
                    book = BookCatalog.objects.create(
                        title=form_data["title"],
                        subtitle=form_data["subtitle"],
                        author=author,  # Keep original author text
                        author_fk=existing_author,  # ForeignKey to AuthorMaster
                        author_short_name=existing_author.author_short_name,  # Short name from AuthorMaster
                        other_authors=other_authors,
                        publisher=form_data["publisher"],
                        isbn_issn=form_data["isbn"],
                        edition=form_data["edition"],
                        subject=subject,
                        call_number=call_number,
                        classification_number=ClassificationNumber,
                        cutter_number=CutterNumber,
                        publication_year=pub_year,
                        material=material,
                        remarks=form_data["remarks"],
                        keywords=form_data["keywords"],
                        language=language.language_name if language else None,
                        publication_place=form_data["publication_place"],
                        year_of_publication=int(pub_year) if pub_year.isdigit() else None,
                        pages=form_data["pages"],
                        date_of_registration=date.today(),
                        status_id=1,
                        created_by=user,
                        updated_by=user
                    )

                    # ---------- UPDATED IMAGE LOGIC USING FileStorageService ----------
                    front_photo = request.FILES.get('front_page_image')
                    last_photo = request.FILES.get('last_page_image')
                    
                    # Get library code from session
                    library_code = request.session.get('library_db', 'default')
                    
                    # Use library_code for folder structure
                    book_folder = f"{library_code}/{book.cat_ref_num}"
                    
                    # Generate unique timestamps for filenames
                    timestamp = dt.now().strftime("%Y%m%dT%H%M%S")
                    
                    # --- Front Page Image ---
                    if front_photo:
                        try:
                            # Extract original filename and extension
                            filename, ext = os.path.splitext(front_photo.name)
                            
                            # Generate unique filename
                            short_uuid = str(uuid.uuid4())[:8]
                            # Remove special characters from filename for safety
                            safe_filename = ''.join(c for c in filename if c.isalnum() or c in (' ', '-', '_')).rstrip()
                            unique_filename = f"{book.cat_ref_num}_front_{safe_filename}_{timestamp}_{short_uuid}{ext}"
                            
                            # Build save path
                            save_path = f"{book_folder}/{unique_filename}"
                            
                            # ✅ USE STORAGE SERVICE TO SAVE FILE
                            saved_file_path = file_storage_service.save_file(front_photo, save_path)
                            
                            # Update book record with saved path
                            book.front_page_photo = saved_file_path
                            
                            print(f"✅ Front page image saved for library {library_code}: {saved_file_path}")
                            
                        except Exception as e:
                            print(f"❌ Error saving front page image: {str(e)}")
                            # Continue without image, don't fail the entire transaction
                            messages.warning(request, f"Front page image could not be saved: {str(e)}")
                    
                    # --- Last Page Image ---
                    if last_photo:
                        try:
                            # Extract original filename and extension
                            filename, ext = os.path.splitext(last_photo.name)
                            
                            # Generate unique filename
                            short_uuid = str(uuid.uuid4())[:8]
                            # Remove special characters from filename for safety
                            safe_filename = ''.join(c for c in filename if c.isalnum() or c in (' ', '-', '_')).rstrip()
                            unique_filename = f"{book.cat_ref_num}_back_{safe_filename}_{timestamp}_{short_uuid}{ext}"
                            
                            # Build save path
                            save_path = f"{book_folder}/{unique_filename}"
                            
                            # ✅ USE STORAGE SERVICE TO SAVE FILE
                            saved_file_path = file_storage_service.save_file(last_photo, save_path)
                            
                            # Update book record with saved path
                            book.last_page_photo = saved_file_path
                            
                            print(f"✅ Last page image saved for library {library_code}: {saved_file_path}")
                            
                        except Exception as e:
                            print(f"❌ Error saving last page image: {str(e)}")
                            # Continue without image, don't fail the entire transaction
                            messages.warning(request, f"Last page image could not be saved: {str(e)}")
                    
                    # Save book with updated image paths
                    book.save()

                messages.success(request, f"Book '{book.title}' saved successfully!")
                return redirect('book_catalog_index')

            except Exception as e:
                messages.error(request, f"Error adding book: {str(e)}")
                return redirect('book_catalog_create')

    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        fun = tb[0].name
        callproc("stp_error_log", [fun, str(e), user])
        messages.error(request, 'Oops...! Something went wrong!')

@no_direct_access 
@login_required 
def book_catalog_edit(request):
    try:
        if not request.user.is_authenticated:
            # Clear any session flags
            if '_session_expired' in request.session:
                request.session.pop('_session_expired')
            messages.warning(request, "Your session has expired. Please log in again.")
            return redirect('library_list')

        if request.method == "GET":
            
            user = request.user.id
            obj = None
            cat_ref_num_encrypted = request.GET.get('cat_ref_num', '').strip()
            cat_ref_num = None
            
            # -------------------- Load Existing Record --------------------
            if cat_ref_num_encrypted:
                try:
                    cat_ref_num = dec(cat_ref_num_encrypted)
                    obj = BookCatalog.objects.filter(cat_ref_num=cat_ref_num).first()
                except Exception as e:
                    messages.warning(request, f"Could not load existing record: {str(e)}")

            # -------------------- Authors By Language ---------------------
            lang_name = obj.language if obj else None
            authors = []
            if lang_name:
                try:
                    if lang_name == "Marathi":
                        authors = AuthorMaster.objects.filter(is_active=True) \
                            .exclude(author_name_marathi__isnull=True) \
                            .exclude(author_name_marathi__exact="") \
                            .values_list('author_name_marathi', flat=True) \
                            .distinct().order_by('author_name_marathi')
                    else:
                        authors = AuthorMaster.objects.filter(is_active=True) \
                            .exclude(author_name_english__isnull=True) \
                            .exclude(author_name_english__exact="") \
                            .values_list('author_name_english', flat=True) \
                            .distinct().order_by('author_name_english')
                except:
                    authors = []

            # -------------------- Dropdown Data ---------------------------
            subjects = SubjectTypeMaster.objects.filter(is_active=True)
            for s in subjects:
                s.encrypted_id = enc(str(s.id))

            materials = MaterialTypeMaster.objects.filter(is_active=True)
            for m in materials:
                m.encrypted_id = enc(str(m.id))

            publishers = BookCatalog.objects.values_list('publisher', flat=True) \
                .exclude(publisher__isnull=True).exclude(publisher__exact='') \
                .distinct().order_by('publisher')

            places = BookCatalog.objects.values_list('publication_place', flat=True) \
                .exclude(publication_place__isnull=True).exclude(publication_place__exact='') \
                .distinct().order_by('publication_place')

            current_year = timezone.now().year
            years = list(range(current_year, 1899, -1))

            # -------------------- Selected Dropdown Values ----------------
            selected_subject = None
            selected_material = None
            selected_publisher = None
            selected_place = None

            if obj:
                obj.refresh_from_db()
                if obj.subject_id:
                    selected_subject = SubjectTypeMaster.objects.filter(id=obj.subject_id).first()
                if obj.material_id:
                    selected_material = MaterialTypeMaster.objects.filter(id=obj.material_id).first()
                if obj.publisher:
                    selected_publisher = obj.publisher
                if obj.publication_place:
                    selected_place = obj.publication_place

            # -------------------- Ensure Selected Appears First ----------------
            # Materials
            materials_list = list(materials)
            if selected_material and not any(m.id == selected_material.id for m in materials):
                materials_list = [selected_material] + materials_list

            # Subjects
            subjects_list = list(subjects)
            if selected_subject and not any(s.id == selected_subject.id for s in subjects):
                subjects_list = [selected_subject] + subjects_list

            # Publishers
            publishers_list = list(publishers)
            if selected_publisher and selected_publisher not in publishers:
                publishers_list = [selected_publisher] + publishers_list

            # Places
            places_list = list(places)
            if selected_place and selected_place not in places:
                places_list = [selected_place] + places_list
                
            front_page_url = None
            last_page_url = None
            
            if obj and obj.front_page_photo:
                front_page_url = file_storage_service.get_file_url(obj.front_page_photo)
            
            if obj and obj.last_page_photo:
                last_page_url = file_storage_service.get_file_url(obj.last_page_photo)

            # -------------------- Render Context --------------------------
            context = {
                'subjects': subjects_list,
                'materials': materials_list,
                'authors': authors,
                'publishers': publishers_list,
                'places': places_list,
                'years': years,
                'obj': obj,
                'selected_subject': selected_subject,
                'selected_material': selected_material,
                'selected_publisher': selected_publisher,
                'selected_place': selected_place,
                'catalog': {'encrypted_id': cat_ref_num_encrypted} if cat_ref_num_encrypted else None,
                'MEDIA_URL': settings.MEDIA_URL,
                'front_page_url': front_page_url,  # ✅ Pre-calculated
                'last_page_url': last_page_url, 
            }
            
            return render(request, 'Master/book_catalog_edit.html', context)
    
        # -------------------- Handle POST (Update) --------------------
        
        # Notepad ++ book_catalog_edit-POST
        
        if request.method == "POST":
    
            user = request.user.id
            
            # 🔥 FIX — fetch object first
            cat_ref_num_encrypted = request.GET.get('cat_ref_num')
            cat_ref_num = dec(cat_ref_num_encrypted)
            obj = get_object_or_404(BookCatalog, cat_ref_num=cat_ref_num)
            
            form_data = {
                "title": request.POST.get("title", "").strip(),
                "subtitle": request.POST.get("subtitle", "").strip(),
                "author_id": dec(request.POST.get("author_id", "").strip()) if request.POST.get("author_id") else None,
                "author": request.POST.get("author", "").strip(),  # Keep original name
                "other_authors": request.POST.get("other_authors", "").strip(),
                "publisher": request.POST.get("publisher", "").strip(),
                "isbn": request.POST.get("isbn", "").strip(),
                "edition": request.POST.get("edition", "").strip(),
                "subject_id": dec(request.POST.get("subject_id", "").strip()) if request.POST.get("subject_id") else None,
                "material_id": dec(request.POST.get("material_id", "").strip()) if request.POST.get("material_id") else None,
                "remarks": request.POST.get("remarks", "").strip(),
                "keywords": request.POST.get("keywords", "").strip(),
                "publication_place": request.POST.get("publication_place", "").strip(),
                "year_of_publication": request.POST.get("year_of_publication", "").strip(),
                "page_nos": request.POST.get("page_nos", "").strip(),
                "front_page_photo": request.FILES.get("front_page_image"),
                "last_page_photo": request.FILES.get("last_page_image"),
            }
            
            field_map = {
                "title": "title",
                "subtitle": "subtitle",
                "author": "author",
                "other_authors": "other_authors",
                "publisher": "publisher",
                "isbn": "isbn_issn",
                "edition": "edition",
                "subject_id": "subject_id",
                "material_id": "material_id",
                "remarks": "remarks",
                "keywords": "keywords",
                "publication_place": "publication_place",
                "year_of_publication": "year_of_publication",
                "page_nos": "pages",
                "front_page_photo": "front_page_photo",
                "last_page_photo": "last_page_photo",
            }

            # Check for changes
            changes = []

            for form_field, model_field in field_map.items():
                new_value = form_data[form_field]
                old_value = getattr(obj, model_field)

                # FILE fields
                if form_field in ["front_page_photo", "last_page_photo"]:
                    if new_value:      # user uploaded a file?
                        changes.append(form_field)
                    continue

                # Text/normal fields
                if str(old_value or "") != str(new_value or ""):
                    changes.append(form_field)

            if not changes:
                messages.info(request, "No changes detected. Nothing was updated.")
                return redirect('book_catalog_index')

            # 🔴 SIMPLE AUTHOR HANDLING - CHECK ONLY TWO COLUMNS
            author_obj = None
            
            # 1. FIRST: Check if author selected from dropdown
            if form_data["author_id"]:
                try:
                    author_obj = AuthorMaster.objects.get(author_code=form_data["author_id"])
                    print(f"✅ Author from dropdown: {author_obj.author_code} - {author_obj.author_name_english}")
                except AuthorMaster.DoesNotExist:
                    print(f"❌ Author ID {form_data['author_id']} not found in database")
            
            # 2. SECOND: If no dropdown selection but author text changed, try to match
            if not author_obj and form_data["author"] and form_data["author"] != obj.author:
                author_text = form_data["author"].strip()
                print(f"🔍 Searching for author: '{author_text}'")
                
                # 🔴 CHECK ONLY TWO COLUMNS AS YOU SAID:
                # 2A. Check Marathi name exact match
                author_obj = AuthorMaster.objects.filter(author_name_marathi=author_text).first()
                if author_obj:
                    print(f"✅ Found by author_name_marathi exact match")
                
                # 2B. Check English name exact match (case-insensitive)
                if not author_obj:
                    author_obj = AuthorMaster.objects.filter(author_name_english__iexact=author_text).first()
                    if author_obj:
                        print(f"✅ Found by author_name_english exact match")
                
                if not author_obj:
                    print(f"❌ No author match found in database for: '{author_text}'")
            
            # 3. UPDATE BOOK WITH AUTHOR INFO
            if author_obj:
                # Author found in database - set foreign key and short name
                obj.author_fk = author_obj
                obj.author_short_name = author_obj.author_short_name
                
                # Also update the text author field
                # Keep the original text from form
                obj.author = form_data["author"]
                
                # Track these changes
                if "author_fk" not in changes:
                    changes.append("author_fk")
                if "author_short_name" not in changes:
                    changes.append("author_short_name")
                    
                print(f"✅ Book linked to author: {author_obj.author_code} - {author_obj.author_name_english}")
            elif form_data["author"]:
                # No author found in database - clear FK but keep text
                obj.author_fk = None
                obj.author_short_name = None
                obj.author = form_data["author"]
                
                # Still track author change
                if "author_fk" not in changes:
                    changes.append("author_fk")
                if "author_short_name" not in changes:
                    changes.append("author_short_name")
                
                print(f"⚠️ Author not found in database, keeping as text only: '{form_data['author']}'")

            # Update object with basic fields
            obj.title = form_data["title"]
            obj.subtitle = form_data["subtitle"]
            obj.other_authors = form_data["other_authors"]
            obj.publisher = form_data["publisher"]
            obj.isbn_issn = form_data["isbn"]
            obj.edition = form_data["edition"]
            obj.subject_id = form_data["subject_id"]
            obj.material_id = form_data["material_id"]
            obj.remarks = form_data["remarks"]
            obj.keywords = form_data["keywords"]
            obj.publication_place = form_data["publication_place"]
            obj.year_of_publication = form_data["year_of_publication"]
            obj.pages = form_data["page_nos"]
            obj.updated_by = request.user.id
            obj.updated_at = timezone.now()

            # ---------- FILE HANDLING USING FileStorageService ----------
            front_photo = request.FILES.get('front_page_image')
            last_photo = request.FILES.get('last_page_image')
            
            if front_photo or last_photo:
                # Get library code from session
                library_code = request.session.get('library_db', 'default')
                
                # Use library_code for folder structure
                book_folder = f"{library_code}/{obj.cat_ref_num}"
                
                # Generate unique timestamps for filenames
                timestamp = dt.now().strftime("%Y%m%dT%H%M%S")
                
                # --- Front Page Image ---
                if front_photo:
                    try:
                        # Extract original filename and extension
                        filename, ext = os.path.splitext(front_photo.name)
                        
                        # Generate unique filename
                        short_uuid = str(uuid.uuid4())[:8]
                        # Remove special characters from filename for safety
                        safe_filename = ''.join(c for c in filename if c.isalnum() or c in (' ', '-', '_')).rstrip()
                        unique_filename = f"{obj.cat_ref_num}_front_{safe_filename}_{timestamp}_{short_uuid}{ext}"
                        
                        # Build save path
                        save_path = f"{book_folder}/{unique_filename}"
                        
                        # ✅ USE STORAGE SERVICE TO SAVE FILE
                        saved_file_path = file_storage_service.save_file(front_photo, save_path)
                        
                        # Update book record with saved path
                        obj.front_page_photo = saved_file_path
                        
                        print(f"✅ Front page image saved for library {library_code}: {saved_file_path}")
                        
                    except Exception as e:
                        print(f"❌ Error saving front page image: {str(e)}")
                        messages.warning(request, f"Front page image could not be saved: {str(e)}")
                
                # --- Last Page Image ---
                if last_photo:
                    try:
                        # Extract original filename and extension
                        filename, ext = os.path.splitext(last_photo.name)
                        
                        # Generate unique filename
                        short_uuid = str(uuid.uuid4())[:8]
                        # Remove special characters from filename for safety
                        safe_filename = ''.join(c for c in filename if c.isalnum() or c in (' ', '-', '_')).rstrip()
                        unique_filename = f"{obj.cat_ref_num}_back_{safe_filename}_{timestamp}_{short_uuid}{ext}"
                        
                        # Build save path
                        save_path = f"{book_folder}/{unique_filename}"
                        
                        # ✅ USE STORAGE SERVICE TO SAVE FILE
                        saved_file_path = file_storage_service.save_file(last_photo, save_path)
                        
                        # Update book record with saved path
                        obj.last_page_photo = saved_file_path
                        
                        print(f"✅ Last page image saved for library {library_code}: {saved_file_path}")
                        
                    except Exception as e:
                        print(f"❌ Error saving last page image: {str(e)}")
                        messages.warning(request, f"Last page image could not be saved: {str(e)}")

            obj.save()
            
            # Show appropriate success message
            if obj.author_fk:
                messages.success(request, 
                    f"Book '{obj.title}' updated successfully! Linked to author: {obj.author_fk.author_name_english}"
                )
            else:
                messages.success(request, 
                    f"Book '{obj.title}' updated successfully!"
                )

            return redirect('book_catalog_index')
        
    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        fun = tb[0].name
        callproc("stp_error_log", [fun, str(e), user])
        messages.error(request, 'Oops...! Something went wrong!')
        return redirect('book_catalog_index')

# Book Accession Index     
@no_direct_access 
@login_required 
def book_accession_index(request):
    try:
        
        if not request.user.is_authenticated:
            # Clear any session flags
            if '_session_expired' in request.session:
                request.session.pop('_session_expired')
            messages.warning(request, "Your session has expired. Please log in again.")
            return redirect('library_list')
        
        user_id = request.user.id
        role_id = getattr(request.user, 'role_id', None)

        if request.method == "GET":
            accessions = BookAccession.objects.select_related(
                'catalogue',  # 👈 pulls in BookCatalog
                'supplier', 'currency', 'funding_source',
                'condition_at_entry', 'location', 'status'
            ).all().order_by("-accession_id")
            
            for a in accessions:
                a.encrypted_id = enc(str(a.accession_id))
            
            context = {
                'accessions': accessions
            }
            return render(request, 'Master/book_accession_index.html', context)

    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        fun = tb[-1].name
        callproc("stp_error_log", [fun, str(e), user_id])
        messages.error(request, 'Oops...! Something went wrong!')
        return render(request, 'Master/book_accession_index.html', {'accessions': []})

# Book Accession Create
@no_direct_access 
@login_required 
def book_accession_create(request):
    try:
        if not request.user.is_authenticated:
            # Clear any session flags
            if '_session_expired' in request.session:
                request.session.pop('_session_expired')
            messages.warning(request, "Your session has expired. Please log in again.")
            return redirect('library_list')
        
        user = request.user.id
        if request.method == "GET":
            # Fetch dropdown data
            suppliers = SupplierMaster.objects.filter(is_active=1)
            for sup in suppliers:
                sup.encrypted_id = enc(str(sup.supplier_id))

            funding_sources = FundingSourceMaster.objects.filter(is_active=1)
            for fs in funding_sources:
                fs.encrypted_id = enc(str(fs.source_id))

            conditions = ConditionAtEntryMaster.objects.filter(is_active=1)
            for cond in conditions:
                cond.encrypted_id = enc(str(cond.condition_id))

            currencies = CurrencyMaster.objects.filter(is_active=1)
            for cur in currencies:
                cur.encrypted_id = enc(str(cur.currency_id))

            locations = ResourceLocationMaster.objects.filter(is_active=1)
            for loc in locations:
                loc.encrypted_id = enc(str(loc.location_id))

            statuses = status_master.objects.filter(is_active=1, status_type="Accession")
            for st in statuses:
                st.encrypted_id = enc(str(st.status_id))

            catalogues = BookCatalog.objects.all()
            for cat in catalogues:
                cat.encrypted_id = enc(str(cat.cat_ref_num))

            context = {
                'suppliers': suppliers,
                'funding_sources': funding_sources,
                'conditions': conditions,
                'currencies': currencies,
                'locations': locations,
                'statuses': statuses,
                'catalogues': catalogues,
            }
            return render(request, 'Master/book_accession_create.html', context)

        if request.method == "POST":
            catalogue_id = dec(request.POST.get("catalogue_id"))
            copy_number = int(request.POST.get("copy_number"))
            acquisition_date = request.POST.get("acquisition_date")
            supplier_id = dec(request.POST.get("supplier_id")) if request.POST.get("supplier_id") else None
            invoice_number = request.POST.get("invoice_number") or None
            invoice_date = request.POST.get("invoice_date") or None
            price = request.POST.get("price") or None
            currency_id = dec(request.POST.get("currency_id")) if request.POST.get("currency_id") else None
            funding_source_id = dec(request.POST.get("funding_source_id")) if request.POST.get("funding_source_id") else None
            condition_id = dec(request.POST.get("condition_id")) if request.POST.get("condition_id") else None
            status_id = 4
            remarks = request.POST.get("remarks") or None

            last_copy = BookAccession.objects.filter(
                catalogue_id=catalogue_id
            ).aggregate(max_copy=models.Max('copy_number'))['max_copy'] or 0

            # ✅ Fetch latest accession number
            increment = IncrementMaster.objects.get(id=2)
            start_no = increment.incrementFieldNumber
            start_no = int(start_no)

            for i in range(1, copy_number + 1):
                start_no += 1
                BookAccession.objects.create(
                    catalogue_id=catalogue_id,
                    copy_number=last_copy + i,
                    accession_no=start_no,
                    acquisition_date=acquisition_date,
                    supplier_id=supplier_id,
                    invoice_number=invoice_number,
                    invoice_date=invoice_date,
                    price=price,
                    currency_id=currency_id,
                    funding_source_id=funding_source_id,
                    condition_at_entry_id=condition_id,
                    status_id=status_id,
                    remarks=remarks,
                    created_by=user
                )

            # ✅ Update the master once (after all inserts)
            increment.incrementFieldNumber = start_no
            increment.save()

            messages.success(
                request,
                f"{copy_number} new copy(ies) successfully added starting from copy number {last_copy + 1}."
            )
            return redirect('book_accession_index')

        
    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        fun = tb[0].name
        callproc("stp_error_log", [fun, str(e), user])
        messages.error(request, 'Oops...! Something went wrong!')

# Book Accession Edit
@no_direct_access 
@login_required 
def book_accession_edit(request):
    try:
        if not request.user.is_authenticated:
            # Clear any session flags
            if '_session_expired' in request.session:
                request.session.pop('_session_expired')
            messages.warning(request, "Your session has expired. Please log in again.")
            return redirect('library_list')
        user_id = request.user.id
        
        # Get encrypted_id from URL parameter
        encrypted_id = request.GET.get('encrypted_id')
        if not encrypted_id:
            messages.error(request, 'Invalid record ID')
            return redirect('book_accession_index')
        
        # Decrypt the ID
        try:
            accession_id = dec(str(encrypted_id.strip()))
        except:
            messages.error(request, 'Invalid record ID')
            return redirect('book_accession_index')
        
        # Get the accession record
        accession = get_object_or_404(BookAccession, accession_id=accession_id)
        
        if request.method == "GET":
            # Fetch dropdown data
            suppliers = SupplierMaster.objects.filter(is_active=1)
            for sup in suppliers:
                sup.encrypted_id = enc(str(sup.supplier_id))

            funding_sources = FundingSourceMaster.objects.filter(is_active=1)
            for fs in funding_sources:
                fs.encrypted_id = enc(str(fs.source_id))

            conditions = ConditionAtEntryMaster.objects.filter(is_active=1)
            for cond in conditions:
                cond.encrypted_id = enc(str(cond.condition_id))

            currencies = CurrencyMaster.objects.filter(is_active=1)
            for cur in currencies:
                cur.encrypted_id = enc(str(cur.currency_id))

            locations = ResourceLocationMaster.objects.filter(is_active=1)
            for loc in locations:
                loc.encrypted_id = enc(str(loc.location_id))

            statuses = status_master.objects.filter(is_active=1)
            for st in statuses:
                st.encrypted_id = enc(str(st.status_id))

            catalogues = BookCatalog.objects.all()
            for cat in catalogues:
                cat.encrypted_id = enc(str(cat.cat_ref_num))
            
            # Create context with current values
            context = {
                'accession': accession,
                'suppliers': suppliers,
                'funding_sources': funding_sources,
                'conditions': conditions,
                'currencies': currencies,
                'locations': locations,
                'statuses': statuses,
                'catalogues': catalogues,
            }
            return render(request, 'Master/book_accession_edit.html', context)
        
        elif request.method == "POST":
            # Check if any data has actually changed
            has_changed = False
            original_data = {}
            
            # Store original data for comparison
            original_data = {
                'catalogue_id': accession.catalogue_id,
                # 'copy_number': accession.copy_number,
                'acquisition_date': accession.acquisition_date,
                'supplier_id': accession.supplier_id,
                'invoice_number': accession.invoice_number,
                'invoice_date': accession.invoice_date,
                'price': accession.price,
                'currency_id': accession.currency_id,
                'funding_source_id': accession.funding_source_id,
                'condition_id': accession.condition_at_entry_id,
                'location_id': accession.location_id,
                # 'status_id': accession.status_id,
                'remarks': accession.remarks,
            }
            
            # Prepare new data
            new_data = {}
            
            # Catalogue
            if request.POST.get('catalogue_id'):
                new_catalogue_id = dec(str(request.POST.get('catalogue_id')))
                if new_catalogue_id != original_data['catalogue_id']:
                    accession.catalogue_id = new_catalogue_id
                    has_changed = True
            
            # Copy Number
            # new_copy_number = request.POST.get('copy_number')
            # if new_copy_number and str(new_copy_number) != str(original_data['copy_number']):
            #     accession.copy_number = new_copy_number
            #     has_changed = True
            
            # Acquisition Date
            new_acquisition_date = request.POST.get('acquisition_date')
            if new_acquisition_date and str(new_acquisition_date) != str(original_data['acquisition_date']):
                accession.acquisition_date = new_acquisition_date
                has_changed = True
            
            # Supplier
            if request.POST.get('supplier_id'):
                new_supplier_id = dec(str(request.POST.get('supplier_id')))
                if new_supplier_id != original_data['supplier_id']:
                    accession.supplier_id = new_supplier_id
                    has_changed = True
            
            # Invoice Number
            new_invoice_number = request.POST.get('invoice_number')
            if new_invoice_number != original_data['invoice_number']:
                accession.invoice_number = new_invoice_number
                has_changed = True
            
            # Invoice Date
            new_invoice_date = request.POST.get('invoice_date')
            if new_invoice_date and str(new_invoice_date) != str(original_data['invoice_date']):
                accession.invoice_date = new_invoice_date
                has_changed = True
            
            # Price
            new_price = request.POST.get('price')
            if new_price and str(new_price) != str(original_data['price']):
                accession.price = new_price
                has_changed = True
            
            # Currency
            if request.POST.get('currency_id'):
                new_currency_id = dec(str(request.POST.get('currency_id')))
                if new_currency_id != original_data['currency_id']:
                    accession.currency_id = new_currency_id
                    has_changed = True
            
            # Funding Source
            if request.POST.get('funding_source_id'):
                new_funding_source_id = dec(str(request.POST.get('funding_source_id')))
                if new_funding_source_id != original_data['funding_source_id']:
                    accession.funding_source_id = new_funding_source_id
                    has_changed = True
            
            # Condition
            if request.POST.get('condition_id'):
                new_condition_id = dec(str(request.POST.get('condition_id')))
                if new_condition_id != original_data['condition_id']:
                    accession.condition_at_entry_id = new_condition_id
                    has_changed = True
            
            # Location
            if request.POST.get('location_id'):
                new_location_id = dec(str(request.POST.get('location_id')))
                if new_location_id != original_data['location_id']:
                    accession.location_id = new_location_id
                    has_changed = True
            
            # Status
            # if request.POST.get('status_id'):
            #     new_status_id = dec(str(request.POST.get('status_id')))
            #     if new_status_id != original_data['status_id']:
            #         accession.status_id = new_status_id
            #         has_changed = True
            
            # Remarks
            new_remarks = request.POST.get('remarks')
            if new_remarks != original_data['remarks']:
                accession.remarks = new_remarks
                has_changed = True
            
            # Only save if something changed
            if has_changed:
                accession.updated_by = request.user.username
                accession.save()
                messages.success(request, 'Book accession updated successfully!')
            else:
                messages.info(request, 'No changes were made to the record.')
            
            return redirect('book_accession_index')
           
    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        fun = tb[-1].name
        callproc("stp_error_log", [fun, str(e), user_id])
        messages.error(request, 'Oops...! Something went wrong while updating!')
        return redirect('book_accession_index')

# Book Accession view
@no_direct_access 
@login_required 
def book_accession_view(request, encrypted_id=None):
    try:
        if not request.user.is_authenticated:
            # Clear any session flags
            if '_session_expired' in request.session:
                request.session.pop('_session_expired')
            messages.warning(request, "Your session has expired. Please log in again.")
            return redirect('library_list')
        
        user_id = request.user.id
        
        # Get encrypted_id from either URL parameter or query parameter
        if encrypted_id:
            # From URL path: /view/encrypted_value/
            enc_id = encrypted_id
        else:
            # From query parameter: /view/?encrypted_id=encrypted_value
            enc_id = request.GET.get('encrypted_id', '')
        
        if not enc_id:
            messages.error(request, 'Invalid record ID')
            return redirect('book_accession_index')
        
        # Decrypt the ID
        try:
            accession_id = int(dec(enc_id.strip()))
        except Exception as dec_error:
            print(f"Decryption error: {dec_error}")
            messages.error(request, 'Invalid record ID')
            return redirect('book_accession_index')
        
        # Get the accession record with all related data
        accession = get_object_or_404(
            BookAccession.objects.select_related(
                'catalogue',
                'supplier', 
                'currency', 
                'funding_source',
                'condition_at_entry', 
                'location', 
                'status'
            ), 
            accession_id=accession_id
        )
        
        # Add encrypted_id to the accession object (like you do in index view)
        accession.encrypted_id = enc_id
        
        # Fetch all related data for display context
        context = {
            'accession': accession,
            'is_view_mode': True,
            'encrypted_id': enc_id,  # Also pass separately if needed
        }
        
        return render(request, 'Master/book_accession_view.html', context)
            
    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        fun = tb[-1].name
        callproc("stp_error_log", [fun, str(e), user_id])
        messages.error(request, 'Oops...! Something went wrong while loading the record!')
        return redirect('book_accession_index')
# translate_word

def translate_word(request):
    word = request.GET.get("q", "").strip()
    if word:
        try:
            response = requests.get(
                "https://inputtools.google.com/request",
                params={
                    "text": word,
                    "itc": "mr-t-i0-und",  # 'mr' is Marathi
                    "num": 1,
                    "cp": 0,
                    "cs": 1,
                    "ie": "utf-8",
                    "oe": "utf-8",
                    "app": "demo"
                }
            )
            data = response.json()
            if data[0] == "SUCCESS":
                suggestion = data[1][0][1][0]
                return JsonResponse({"translated": suggestion})
            else:
                return JsonResponse({"translated": word, "error": "No translation found"})
        except Exception as e:
            return JsonResponse({"translated": word, "error": str(e)})

    return JsonResponse({"translated": ""})

def contains_non_english(text):
    """
    Detects if text contains Devanagari characters (Marathi/Hindi).
    Returns False if any error occurs.
    """
    try:
        if not text:
            return False
        return bool(re.search(r'[\u0900-\u097F]', text))
    except Exception as e:
        print(f"Error in contains_non_english: {e}")
        return False

def transliterate_to_english(text):
    """
    Converts Marathi/Hindi text (Devanagari) into English phonetic form.
    Uses HK scheme (simple ASCII output, no diacritics).
    """
    try:
        if not text:
            return ""
        return transliterate(text, DEVANAGARI, HK)
    except Exception as e:
        print(f"Error in transliterate_to_english: {e}")
        return text or ""

@no_direct_access 
@login_required
def material_type_master_index(request):
    try:
        if not request.user.is_authenticated:
            # Clear any session flags
            if '_session_expired' in request.session:
                request.session.pop('_session_expired')
            messages.warning(request, "Your session has expired. Please log in again.")
            return redirect('library_list')
        
        user = request.user.id
        role_id = request.user.role_id

        if request.method == "GET":
            materials = MaterialTypeMaster.objects.all()
            for mat in materials:
                mat.encrypted_id = enc(str(mat.id))   # 🔹 add encrypted ID

            return render(request, "Master/material_type_master_index.html", {
                "materials": materials
            })
    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        fun = tb[0].name
        callproc("stp_error_log",[fun,str(e),user])  
        messages.error(request, 'Oops...! Something went wrong!')
    
@login_required
def updatestatus(request):
    if request.method == "POST":
        import json
        try:
            data = json.loads(request.body)  # Expecting JSON
            enc_id = data.get("id")  # 🔹 Encrypted ID
            status = data.get("status")

            # 🔹 Decrypt ID
            mat_id = int(dec(enc_id))

            # 🔹 Fetch and update material
            material = MaterialTypeMaster.objects.get(id=mat_id)
            material.is_active = bool(int(status))  # ensure 0/1 → True/False
            material.save()

            return JsonResponse({"success": True, "status": int(material.is_active)})

        except MaterialTypeMaster.DoesNotExist:
            return JsonResponse({"success": False, "error": "Material not found"}, status=404)
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)}, status=400)

    return JsonResponse({"success": False, "error": "Invalid request"}, status=400)

@no_direct_access 
@login_required
def material_type_create(request):
    try:
        if not request.user.is_authenticated:
            # Clear any session flags
            if '_session_expired' in request.session:
                request.session.pop('_session_expired')
            messages.warning(request, "Your session has expired. Please log in again.")
            return redirect('library_list')
        
        user = request.user.id

        if request.method == "POST":
            material_code = request.POST.get("materialCode", "").strip()
            name_eng = request.POST.get("materialNameEnglish", "").strip()
            name_mar = request.POST.get("materialNameMarathi", "").strip()
            is_active = request.POST.get("is_active", 1)  # Default active

            # 🔹 Duplicate check (case-insensitive & trimmed)
            if MaterialTypeMaster.objects.filter(materialCode__iexact=material_code).exists():
                messages.error(request, f"Material code '{material_code}' already exists!")
                return redirect("material_type_create")

            # 🔹 Create new record
            MaterialTypeMaster.objects.create(
                materialCode=material_code,
                materialNameEnglish=name_eng,
                materialNameMarathi=name_mar,
                is_active=bool(int(is_active)),  # make sure it's 0/1 → True/False
                created_by=user,
                created_at=timezone.now(),
            )

            messages.success(request, "Material type created successfully!")
            return redirect("material_type_master_index")

        # 🔹 GET method – load existing materials
        materials = MaterialTypeMaster.objects.filter(is_active=True)
        for mat in materials:
            mat.encrypted_id = enc(str(mat.id))

        context = {
            "materials": materials,
        }
        return render(request, "Master/material_type_create.html", context)

    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        fun = tb[0].name
        callproc("stp_error_log", [fun, str(e), user])
        messages.error(request, "Oops...! Something went wrong!")
        return redirect("material_type_create")

@login_required
def materialtype_list(request):
    materials = MaterialTypeMaster.objects.all()
    for mat in materials:
        mat.encrypted_id = enc(str(mat.id))   # add encrypted_id attribute
        print(f"Mat ID: {mat.id}, Encrypted: {mat.encrypted_id}")  # debug
    return render(request, "Master/materialtype_list.html", {"materials": materials})

@no_direct_access 
@login_required
def materialtype_view(request):
    try:
        if not request.user.is_authenticated:
            # Clear any session flags
            if '_session_expired' in request.session:
                request.session.pop('_session_expired')
            messages.warning(request, "Your session has expired. Please log in again.")
            return redirect('library_list')
        if request.method == "POST":
            # 🔹 ID comes from hidden field in POST
            enc_id = request.POST.get("id")
            mat_id = int(dec(enc_id))  # decrypt
            material = MaterialTypeMaster.objects.get(id=mat_id)

        else:  # GET request
            # 🔹 ID comes from URL query param
            enc_id = request.GET.get("id")
            mat_id = int(dec(enc_id))  # decrypt
            material = MaterialTypeMaster.objects.get(id=mat_id)

        # always regenerate encrypted_id for reuse in template
        material.encrypted_id = enc(str(material.id))

        return render(
            request,
            "Master/materialtype_view.html",
            {"material": material}
        )

    except MaterialTypeMaster.DoesNotExist:
        messages.error(request, "Material not found!")
        return redirect("material_type_master_index")
    except Exception as e:
        print("❌ Decryption/View Error:", e)
        messages.error(request, "Invalid or corrupted ID!")
        return redirect("material_type_master_index")

@no_direct_access 
@login_required
def materialtype_edit(request):
    try:
        if not request.user.is_authenticated:
            # Clear any session flags
            if '_session_expired' in request.session:
                request.session.pop('_session_expired')
            messages.warning(request, "Your session has expired. Please log in again.")
            return redirect('library_list')
        
        if request.method == "POST":
            # 🔹 Get encrypted id from hidden field
            enc_id = request.POST.get("id")
            if not enc_id:
                messages.error(request, "Missing ID in form!")
                return redirect("material_type_master_index")

            mat_id = int(dec(enc_id))  # decrypt
            material = MaterialTypeMaster.objects.get(id=mat_id)

            # 🔹 Update fields
            material.materialNameEnglish = request.POST.get("materialNameEnglish")
            material.materialNameMarathi = request.POST.get("materialNameMarathi")
            material.save()

            messages.success(request, "Material updated successfully!")
            return redirect("material_type_master_index")

        else:  # 🔹 GET request
            enc_id = request.GET.get("id")
            if not enc_id:
                messages.error(request, "Missing ID in URL!")
                return redirect("material_type_master_index")

            mat_id = int(dec(enc_id))  # decrypt
            material = MaterialTypeMaster.objects.get(id=mat_id)

            # Re-attach encrypted id so template can send it back in hidden field
            material.encrypted_id = enc(str(material.id))

            return render(request, "Master/materialtype_edit.html", {"material": material})

    except MaterialTypeMaster.DoesNotExist:
        messages.error(request, "Material not found!")
        return redirect("material_type_master_index")
    except Exception as e:
        print("❌ Edit Error:", e)
        messages.error(request, "Invalid or corrupted ID!")
        return redirect("material_type_master_index")

@login_required
def materialtype_delete(request):
    if request.method == "POST":
        try:
            enc_id = request.POST.get("id")   # Encrypted ID from form
            if not enc_id:
                return JsonResponse({"success": False, "error": "Missing ID"})
            
            mat_id = int(dec(enc_id))         # 🔹 Decrypt back to integer
            material = MaterialTypeMaster.objects.get(id=mat_id)
            material.delete()
            
            return JsonResponse({"success": True})
        except MaterialTypeMaster.DoesNotExist:
            return JsonResponse({"success": False, "error": "Material not found"})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})
    return JsonResponse({"success": False, "error": "Invalid request"})

# subject type master index

@no_direct_access 
@login_required
def subject_type_master_index(request):
    try:
        if not request.user.is_authenticated:
            # Clear any session flags
            if '_session_expired' in request.session:
                request.session.pop('_session_expired')
            messages.warning(request, "Your session has expired. Please log in again.")
            return redirect('library_list')
        
        if request.user.is_authenticated:                
            global user, role_id
            user = request.user.id    
            role_id = request.user.role_id 

        if request.method == "GET":
            subjects = SubjectTypeMaster.objects.all()

            # 🔹 Encrypt the ID for each subject
            for sub in subjects:
                sub.encrypted_id = enc(str(sub.id))

            return render(
                request,
                'Master/subject_type_master_index.html',
                {"subjects": subjects}
            )

    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        fun = tb[0].name
        callproc("stp_error_log", [fun, str(e), user])  
        messages.error(request, 'Oops...! Something went wrong!')
        return redirect("dashboard")  # fallback redirect

@no_direct_access 
@login_required
def subject_type_create(request):
    try:
        if not request.user.is_authenticated:
            # Clear any session flags
            if '_session_expired' in request.session:
                request.session.pop('_session_expired')
            messages.warning(request, "Your session has expired. Please log in again.")
            return redirect('library_list')
        
        user = request.user.id

        if request.method == "POST":
            subject_code = request.POST.get('subjectCode')
            name_eng = request.POST.get('subjectNameEnglish')
            name_mar = request.POST.get('subjectNameMarathi')
            description = request.POST.get('subjectDescription')
            is_active = request.POST.get('is_active', 1)  # Default active

            # ✅ Check for duplicate subject code
            if SubjectTypeMaster.objects.filter(subjectCode=subject_code).exists():
                messages.error(request, f"Subject code '{subject_code}' already exists!")
                return redirect('subject_type_create')

            # ✅ Check for duplicate subject name (English)
            if SubjectTypeMaster.objects.filter(subjectNameEnglish=name_eng).exists():
                messages.error(request, f"Subject '{name_eng}' already exists!")
                return redirect('subject_type_create')

            # ✅ Create new subject type with created_by and created_at
            SubjectTypeMaster.objects.create(
                subjectCode=subject_code,
                subjectNameEnglish=name_eng,
                subjectNameMarathi=name_mar,
                subjectDescription=description,
                is_active=1,
                created_by=user,
                created_at=timezone.now()
            )
            messages.success(request, "Subject type created successfully!")
            return redirect('subject_type_master_index')

        # GET method – show existing subjects
        subjects = SubjectTypeMaster.objects.filter(is_active=True)
        for sub in subjects:
            sub.encrypted_id = enc(str(sub.id))

        context = {
            'subjects': subjects,
        }
        return render(request, 'Master/subject_type_create.html', context)

    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        fun = tb[0].name
        callproc("stp_error_log", [fun, str(e), user])
        messages.error(request, 'Oops...! Something went wrong!')
        return redirect('subject_type_create')
    
@no_direct_access 
@login_required
def subject_type_view(request):
    try:
        if not request.user.is_authenticated:
            # Clear any session flags
            if '_session_expired' in request.session:
                request.session.pop('_session_expired')
            messages.warning(request, "Your session has expired. Please log in again.")
            return redirect('library_list')
        
        enc_id = request.GET.get("id")  # fetch encrypted id from URL
        if not enc_id:
            messages.error(request, "Missing ID!")
            return redirect("subject_type_master_index")

        # 🔹 Decrypt the ID
        sub_id = int(dec(enc_id))

        # 🔹 Fetch subject
        subject = SubjectTypeMaster.objects.get(id=sub_id)

        # 🔹 Add encrypted_id back (if you need for buttons in template)
        subject.encrypted_id = enc(str(subject.id))

        context = {
            "subject": subject
        }
        return render(request, "Master/subject_type_view.html", context)

    except SubjectTypeMaster.DoesNotExist:
        messages.error(request, "Subject not found!")
        return redirect("subject_type_master_index")
    except Exception as e:
        print("❌ Decryption/View Error:", e)
        messages.error(request, "Invalid or corrupted ID!")
        return redirect("subject_type_master_index")

@no_direct_access 
@login_required
def subject_edit(request):
    if not request.user.is_authenticated:
        # Clear any session flags
        if '_session_expired' in request.session:
            request.session.pop('_session_expired')
        messages.warning(request, "Your session has expired. Please log in again.")
        return redirect('library_list')
        
    subject = None

    if request.method == "POST":
        try:
            # 🔹 Decrypt ID from hidden field (if provided)
            enc_id = request.POST.get("id")
            if enc_id:
                sub_id = int(dec(enc_id))  # decrypt
                subject = SubjectTypeMaster.objects.get(id=sub_id)

            user_id = request.user.id

            # Get form data safely
            subject_code = request.POST.get("subjectCode", "").strip()
            name_eng = request.POST.get("subjectNameEnglish", "").strip()
            name_mar = request.POST.get("subjectNameMarathi", "").strip()
            is_active = request.POST.get("is_active", "1")  # default active

            # Validate required fields
            if not subject_code or not name_eng or not name_mar:
                messages.error(request, "All fields are required!")
                return redirect(request.path)

            # 🔹 Duplicate check
            duplicate = SubjectTypeMaster.objects.filter(subjectCode__iexact=subject_code)
            if subject:
                duplicate = duplicate.exclude(id=subject.id)
            if duplicate.exists():
                messages.error(request, f"Subject code '{subject_code}' already exists!")
                return redirect("subject_type_master_index")

            # 🔹 Update or Create
            if subject:  # update
                subject.subjectCode = subject_code
                subject.subjectNameEnglish = name_eng
                subject.subjectNameMarathi = name_mar
                subject.is_active = bool(int(is_active))
                subject.updated_by = user_id
                subject.updated_at = timezone.now()
                subject.save()
                messages.success(request, "Subject updated successfully!")
            else:  # create new
                SubjectTypeMaster.objects.create(
                    subjectCode=subject_code,
                    subjectNameEnglish=name_eng,
                    subjectNameMarathi=name_mar,
                    is_active=bool(int(is_active)),
                    created_by=user_id,
                    created_at=timezone.now()
                )
                messages.success(request, "Subject created successfully!")

            return redirect("subject_type_master_index")

        except SubjectTypeMaster.DoesNotExist:
            messages.error(request, "Subject not found!")
            return redirect("subject_type_master_index")
        except Exception as e:
            print("❌ Edit Error:", e)
            messages.error(request, "Invalid or corrupted ID!")
            return redirect("subject_type_master_index")

    else:  # GET request
        try:
            enc_id = request.GET.get("id")
            if enc_id:
                sub_id = int(dec(enc_id))  # 🔹 decrypt here
                subject = SubjectTypeMaster.objects.get(id=sub_id)
                # add encrypted_id for hidden field
                subject.encrypted_id = enc(str(subject.id))

        except Exception as e:
            print("❌ GET Edit Error:", e)
            messages.error(request, "Invalid or corrupted ID!")
            return redirect("subject_type_master_index")

        return render(request, "Master/subject_edit.html", {"subject": subject})

@login_required
def subject_delete(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)  # parse JSON from request
            enc_id = data.get("id")  # encrypted id
        except (json.JSONDecodeError, KeyError):
            return JsonResponse({"success": False, "error": "Invalid data"})

        if not enc_id:
            return JsonResponse({"success": False, "error": "Subject ID is missing"})

        try:
            # 🔹 Decrypt the ID
            sub_id = int(dec(enc_id))

            # 🔹 Fetch and delete
            subject = SubjectTypeMaster.objects.get(id=sub_id)
            subject.delete()
            return JsonResponse({"success": True})

        except SubjectTypeMaster.DoesNotExist:
            return JsonResponse({"success": False, "error": "Subject not found"})
        except Exception as e:
            print("❌ Delete Error:", e)
            return JsonResponse({"success": False, "error": "Invalid or corrupted ID"})

    return JsonResponse({"success": False, "error": "Invalid request"})

@login_required
def update_subject_status(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)  # Expecting JSON
            sub_id = data.get("id")
            status = data.get("status")

            subject = SubjectTypeMaster.objects.get(id=sub_id)
            subject.is_active = bool(status)
            subject.save()
            return JsonResponse({"success": True, "status": int(subject.is_active)})
        except SubjectTypeMaster.DoesNotExist:
            return JsonResponse({"success": False, "error": "Subject not found"}, status=404)
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)}, status=400)

    return JsonResponse({"success": False, "error": "Invalid request"}, status=400)

# language master index

@no_direct_access 
@login_required
def language_master_index(request):
    try:
        if not request.user.is_authenticated:
            # Clear any session flags
            if '_session_expired' in request.session:
                request.session.pop('_session_expired')
            messages.warning(request, "Your session has expired. Please log in again.")
            return redirect('library_list')
    
        if request.user.is_authenticated:                
            global user, role_id
            user = request.user.id    
            role_id = request.user.role_id 

        if request.method == "GET":
            languages = LanguageMaster.objects.all()

            # 🔹 Encrypt the ID for each language
            for lang in languages:
                lang.encrypted_id = enc(str(lang.id))

            return render(
                request,
                'Master/language_master_index.html',
                {"languages": languages}
            )

    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        fun = tb[0].name
        callproc("stp_error_log", [fun, str(e), user])  
        messages.error(request, 'Oops...! Something went wrong!')
        return redirect("dashboard")  # fallback redirect

@login_required
def update_language_status(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)  # Expecting JSON
            encrypted_id = data.get("id")    # Encrypted ID from frontend
            is_active = data.get("is_active")  # Status sent from frontend

            if encrypted_id is None or is_active is None:
                return JsonResponse({"success": False, "error": "Missing data"}, status=400)

            # Decrypt the ID
            lang_id = dec(encrypted_id)

            language = LanguageMaster.objects.get(id=lang_id)
            language.is_active = bool(is_active)
            language.save()

            return JsonResponse({"success": True, "status": int(language.is_active)})

        except LanguageMaster.DoesNotExist:
            return JsonResponse({"success": False, "error": "Language not found"}, status=404)
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)}, status=400)

    return JsonResponse({"success": False, "error": "Invalid request"}, status=400)

@no_direct_access 
@login_required
def language_create(request):
    try:
        if not request.user.is_authenticated:
            # Clear any session flags
            if '_session_expired' in request.session:
                request.session.pop('_session_expired')
            messages.warning(request, "Your session has expired. Please log in again.")
            return redirect('library_list')
        
        user = request.user.id

        if request.method == "POST":
            language_code = request.POST.get('languageCode')
            name_eng = request.POST.get('languageNameEnglish')
            is_active = request.POST.get('is_active', 1)  # Default active

            # ✅ Check for duplicate language code
            if LanguageMaster.objects.filter(language_code=language_code).exists():
                messages.error(request, f"Language code '{language_code}' already exists!")
                return redirect('language_create')

            # ✅ Check for duplicate language name (English)
            if LanguageMaster.objects.filter(language_name=name_eng).exists():
                messages.error(request, f"Language '{name_eng}' already exists!")
                return redirect('language_create')

            # ✅ Create new language with created_by and created_at
            LanguageMaster.objects.create(
                language_code=language_code,
                language_name=name_eng,
                is_active=1,
                created_by=user,
                created_at=timezone.now()
            )
            messages.success(request, "Language created successfully!")
            return redirect('language_master_index')

        # GET method – show existing languages
        languages = LanguageMaster.objects.filter(is_active=True)
        for lang in languages:
            lang.encrypted_id = enc(str(lang.id))

        context = {
            'languages': languages,
        }
        return render(request, 'Master/language_create.html', context)

    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        fun = tb[0].name
        callproc("stp_error_log", [fun, str(e), user])
        messages.error(request, 'Oops...! Something went wrong!')
        return redirect('language_create')

@no_direct_access 
@login_required
def language_edit(request):
    language = None
    
    if not request.user.is_authenticated:
            # Clear any session flags
            if '_session_expired' in request.session:
                request.session.pop('_session_expired')
            messages.warning(request, "Your session has expired. Please log in again.")
            return redirect('library_list')

    if request.method == "POST":
        try:
            # 🔹 Decrypt ID from hidden field
            enc_id = request.POST.get("id")
            if enc_id:
                lang_id = int(dec(enc_id))  # decrypt
                language = LanguageMaster.objects.get(id=lang_id)

            user_id = request.user.id

            # Get form data safely
            language_code = request.POST.get("languageCode", "").strip()
            name_eng = request.POST.get("languageNameEnglish", "").strip()
            is_active = request.POST.get("is_active", "1")  # default active

            # Validate required fields
            if not language_code or not name_eng:
                messages.error(request, "All fields are required!")
                return redirect(request.path)

            # 🔹 Duplicate check for language_code
            duplicate = LanguageMaster.objects.filter(language_code__iexact=language_code)
            if language:
                duplicate = duplicate.exclude(id=language.id)
            if duplicate.exists():
                messages.error(request, f"Language code '{language_code}' already exists!")
                return redirect("language_master_index")

            # 🔹 Duplicate check for language_name
            duplicate_name = LanguageMaster.objects.filter(language_name__iexact=name_eng)
            if language:
                duplicate_name = duplicate_name.exclude(id=language.id)
            if duplicate_name.exists():
                messages.error(request, f"Language '{name_eng}' already exists!")
                return redirect("language_master_index")

            # 🔹 Update or Create
            if language:  # update
                language.language_code = language_code
                language.language_name = name_eng
                language.is_active = bool(int(is_active))
                language.updated_by = user_id
                language.updated_at = timezone.now()
                language.save()
                messages.success(request, "Language updated successfully!")
            else:  # create new
                LanguageMaster.objects.create(
                    language_code=language_code,
                    language_name=name_eng,
                    is_active=bool(int(is_active)),
                    created_by=user_id,
                    created_at=timezone.now()
                )
                messages.success(request, "Language created successfully!")

            return redirect("language_master_index")

        except LanguageMaster.DoesNotExist:
            messages.error(request, "Language not found!")
            return redirect("language_master_index")
        except Exception as e:
            print("❌ Edit Error:", e)
            messages.error(request, "Invalid or corrupted ID!")
            return redirect("language_master_index")

    else:  # GET request
        try:
            enc_id = request.GET.get("id")
            if enc_id:
                lang_id = int(dec(enc_id))  # 🔹 decrypt
                language = LanguageMaster.objects.get(id=lang_id)
                # add encrypted_id for hidden field
                language.encrypted_id = enc(str(language.id))

        except Exception as e:
            print("❌ GET Edit Error:", e)
            messages.error(request, "Invalid or corrupted ID!")
            return redirect("language_master_index")

        return render(request, "Master/language_edit.html", {"language": language})

@no_direct_access 
@login_required
def language_view(request):
    try:
        if not request.user.is_authenticated:
            # Clear any session flags
            if '_session_expired' in request.session:
                request.session.pop('_session_expired')
            messages.warning(request, "Your session has expired. Please log in again.")
            return redirect('library_list')
        
        enc_id = request.GET.get("id")  # fetch encrypted id from URL
        if not enc_id:
            messages.error(request, "Missing ID!")
            return redirect("language_master_index")

        # 🔹 Decrypt the ID
        lang_id = int(dec(enc_id))

        # 🔹 Fetch language
        language = LanguageMaster.objects.get(id=lang_id)

        # 🔹 Add encrypted_id back (for buttons in template)
        language.encrypted_id = enc(str(language.id))

        context = {
            "language": language
        }
        return render(request, "Master/language_view.html", context)

    except LanguageMaster.DoesNotExist:
        messages.error(request, "Language not found!")
        return redirect("language_master_index")
    except Exception as e:
        print("❌ Decryption/View Error:", e)
        messages.error(request, "Invalid or corrupted ID!")
        return redirect("language_master_index")

@login_required
def language_delete(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)  # parse JSON from request
            enc_id = data.get("id")  # encrypted id
        except (json.JSONDecodeError, KeyError):
            return JsonResponse({"success": False, "error": "Invalid data"})

        if not enc_id:
            return JsonResponse({"success": False, "error": "Language ID is missing"})

        try:
            # 🔹 Decrypt the ID
            lang_id = int(dec(enc_id))

            # 🔹 Fetch and delete
            language = LanguageMaster.objects.get(id=lang_id)
            language.delete()
            return JsonResponse({"success": True})

        except LanguageMaster.DoesNotExist:
            return JsonResponse({"success": False, "error": "Language not found"})
        except Exception as e:
            print("❌ Delete Error:", e)
            return JsonResponse({"success": False, "error": "Invalid or corrupted ID"})

    return JsonResponse({"success": False, "error": "Invalid request"})

# supplier master index

@no_direct_access 
@login_required
def supplier_master_index(request):
    try:
        if not request.user.is_authenticated:
            # Clear any session flags
            if '_session_expired' in request.session:
                request.session.pop('_session_expired')
            messages.warning(request, "Your session has expired. Please log in again.")
            return redirect('library_list')
        
        if request.user.is_authenticated:                
            global user, role_id
            user = request.user.id    
            role_id = request.user.role_id 

        if request.method == "GET":
            # 🔹 Fetch all suppliers
            suppliers = SupplierMaster.objects.all()

            # 🔹 Encrypt the supplier_id for each supplier
            for sup in suppliers:
                sup.encrypted_id = enc(str(sup.supplier_id))

            return render(
                request,
                'Master/supplier_master_index.html',
                {"suppliers": suppliers}
            )

    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        fun = tb[0].name
        callproc("stp_error_log", [fun, str(e), user])  
        messages.error(request, 'Oops...! Something went wrong!')
        return redirect("dashboard")  # fallback redirect

from django.db.models import Max

@no_direct_access 
@login_required
def supplier_create(request):
    try:
        if not request.user.is_authenticated:
            # Clear any session flags
            if '_session_expired' in request.session:
                request.session.pop('_session_expired')
            messages.warning(request, "Your session has expired. Please log in again.")
            return redirect('library_list')
        
        user = request.user.id

        if request.method == "POST":
            supplier_name = request.POST.get('supplierName')
            supplier_mobile = request.POST.get('supplierMobile')
            supplier_email = request.POST.get('supplierEmail')
            supplier_address = request.POST.get('supplierAddress')
            supplier_pincode = request.POST.get('supplierPincode')
            is_active = request.POST.get('is_active', 1)

            # ✅ Auto-generate Supplier Code
            last_code = SupplierMaster.objects.aggregate(max_code=Max('supplier_code'))['max_code']
            
            if last_code:
                # Extract number from "SUPxxx"
                last_number = int(last_code.replace("SUP", ""))
                new_number = last_number + 1
            else:
                new_number = 1  # First supplier

            new_code = f"SUP{new_number:03d}"  # Format as SUP001, SUP002 ...

            # ✅ Create supplier
            SupplierMaster.objects.create(
                supplier_code=new_code,
                supplier_name=supplier_name,
                supplier_mobile=supplier_mobile,
                supplier_email=supplier_email,
                supplier_address=supplier_address,
                supplier_pincode=supplier_pincode,
                is_active=is_active,
                created_by=user,
                created_at=timezone.now()
            )
            messages.success(request, f"Supplier '{supplier_name}' created successfully with code {new_code}!")
            return redirect('supplier_master_index')

        # GET method – show form
        return render(request, "Master/supplier_create.html")

    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        fun = tb[0].name
        callproc("stp_error_log", [fun, str(e), user])
        messages.error(request, 'Oops...! Something went wrong!')
        return redirect("supplier_master_index")

@login_required
def update_supplier_status(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            encrypted_id = data.get("id")      # from JS
            is_active = data.get("status")     # from JS

            if encrypted_id is None or is_active is None:
                return JsonResponse({"success": False, "error": "Missing data"}, status=400)

            # 🔹 Decrypt and convert
            supplier_id = int(dec(encrypted_id))

            # 🔹 Fetch supplier using the correct PK
            supplier = SupplierMaster.objects.get(supplier_id=supplier_id)

            supplier.is_active = bool(is_active)
            supplier.save()

            return JsonResponse({"success": True, "status": int(supplier.is_active)})

        except SupplierMaster.DoesNotExist:
            return JsonResponse({"success": False, "error": "Supplier not found"}, status=404)
        except Exception as e:
            print("❌ Error:", e)
            return JsonResponse({"success": False, "error": str(e)}, status=400)

    return JsonResponse({"success": False, "error": "Invalid request"}, status=400)

@no_direct_access 
@login_required
def supplier_view(request):
    try:
        if not request.user.is_authenticated:
            # Clear any session flags
            if '_session_expired' in request.session:
                request.session.pop('_session_expired')
            messages.warning(request, "Your session has expired. Please log in again.")
            return redirect('library_list')
        
        enc_id = request.GET.get("id")  # fetch encrypted id from URL
        if not enc_id:
            messages.error(request, "Missing ID!")
            return redirect("supplier_master_index")  # 👈 your supplier list page

        # 🔹 Decrypt the ID
        supplier_id = int(dec(enc_id))

        # 🔹 Fetch supplier
        supplier = SupplierMaster.objects.get(supplier_id=supplier_id)  # 👈 use correct PK field

        # 🔹 Add encrypted_id back (for buttons in template)
        supplier.encrypted_id = enc(str(supplier.supplier_id))

        context = {
            "supplier": supplier
        }
        return render(request, "Master/supplier_view.html", context)

    except SupplierMaster.DoesNotExist:
        messages.error(request, "Supplier not found!")
        return redirect("supplier_master_index")
    except Exception as e:
        print("❌ Decryption/View Error:", e)
        messages.error(request, "Invalid or corrupted ID!")
        return redirect("supplier_master_index")

@no_direct_access 
@login_required
def supplier_edit(request):
    
    if not request.user.is_authenticated:
        # Clear any session flags
        if '_session_expired' in request.session:
            request.session.pop('_session_expired')
        messages.warning(request, "Your session has expired. Please log in again.")
        return redirect('library_list')
        
    supplier = None

    if request.method == "POST":
        try:
            # 🔹 Decrypt ID from hidden field
            enc_id = request.POST.get("id")
            if enc_id:
                supplier_id = int(dec(enc_id))  # decrypt
                supplier = SupplierMaster.objects.get(supplier_id=supplier_id)

            user_id = request.user.id

            # ✅ Get form data safely
            supplier_code = request.POST.get("supplierCode", "").strip()
            supplier_name = request.POST.get("supplierName", "").strip()
            supplier_email = request.POST.get("supplierEmail", "").strip()
            supplier_mobile = request.POST.get("supplierMobile", "").strip()
            supplier_address = request.POST.get("supplierAddress", "").strip()
            supplier_pincode = request.POST.get("supplierPincode", "").strip()
            is_active = request.POST.get("is_active", "1")

            # ✅ Validate required fields
            if not supplier_code or not supplier_name or not supplier_mobile:
                messages.error(request, "Supplier Code, Name, and Mobile are required!")
                return redirect(request.path)

            # 🔹 Duplicate check for supplier_code
            duplicate = SupplierMaster.objects.filter(supplier_code__iexact=supplier_code)
            if supplier:
                duplicate = duplicate.exclude(supplier_id=supplier.supplier_id)
            if duplicate.exists():
                messages.error(request, f"Supplier code '{supplier_code}' already exists!")
                return redirect("supplier_master_index")

            # 🔹 Duplicate check for supplier_name
            duplicate_name = SupplierMaster.objects.filter(supplier_name__iexact=supplier_name)
            if supplier:
                duplicate_name = duplicate_name.exclude(supplier_id=supplier.supplier_id)
            if duplicate_name.exists():
                messages.error(request, f"Supplier '{supplier_name}' already exists!")
                return redirect("supplier_master_index")

            # 🔹 Update or Create
            if supplier:  # update
                supplier.supplier_code = supplier_code
                supplier.supplier_name = supplier_name
                supplier.supplier_email = supplier_email
                supplier.supplier_mobile = supplier_mobile
                supplier.supplier_address = supplier_address
                supplier.supplier_pincode = supplier_pincode
                supplier.is_active = bool(int(is_active))
                supplier.updated_by = user_id
                supplier.updated_at = timezone.now()
                supplier.save()
                messages.success(request, "Supplier updated successfully!")
            else:  # create new
                SupplierMaster.objects.create(
                    supplier_code=supplier_code,
                    supplier_name=supplier_name,
                    supplier_email=supplier_email,
                    supplier_mobile=supplier_mobile,
                    supplier_address=supplier_address,
                    supplier_pincode=supplier_pincode,
                    is_active=bool(int(is_active)),
                    created_by=user_id,
                    created_at=timezone.now()
                )
                messages.success(request, "Supplier created successfully!")

            return redirect("supplier_master_index")

        except SupplierMaster.DoesNotExist:
            messages.error(request, "Supplier not found!")
            return redirect("supplier_master_index")
        except Exception as e:
            print("❌ Edit Error:", e)
            messages.error(request, "Invalid or corrupted ID!")
            return redirect("supplier_master_index")

    else:  # GET request
        try:
            enc_id = request.GET.get("id")
            if enc_id:
                supplier_id = int(dec(enc_id))  # 🔹 decrypt
                supplier = SupplierMaster.objects.get(supplier_id=supplier_id)
                # add encrypted_id for hidden field
                supplier.encrypted_id = enc(str(supplier.supplier_id))

        except Exception as e:
            print("❌ GET Edit Error:", e)
            messages.error(request, "Invalid or corrupted ID!")
            return redirect("supplier_master_index")

        return render(request, "Master/supplier_edit.html", {"supplier": supplier})

@login_required
def supplier_delete(request):
    if request.method == "POST":
        try:
            enc_id = request.POST.get("id")  # Encrypted ID from form
            if not enc_id:
                messages.error(request, "Missing ID")
                return redirect("supplier_master_index")
            
            supplier_id = int(dec(enc_id))  # 🔹 Decrypt back to integer
            supplier = SupplierMaster.objects.get(supplier_id=supplier_id)
            supplier.delete()
            
            messages.success(request, "Supplier deleted successfully")
            return redirect("supplier_master_index")
        
        except SupplierMaster.DoesNotExist:
            messages.error(request, "Supplier not found")
            return redirect("supplier_master_index")
        
        except Exception as e:
            messages.error(request, f"Error: {str(e)}")
            return redirect("supplier_master_index")
    
    messages.error(request, "Invalid request")
    return redirect("supplier_master_index")

# funding source master index

@no_direct_access 
@login_required
def fundingsource_master_index(request):
    try:
        if not request.user.is_authenticated:
            # Clear any session flags
            if '_session_expired' in request.session:
                request.session.pop('_session_expired')
            messages.warning(request, "Your session has expired. Please log in again.")
            return redirect('library_list')
        
        if request.user.is_authenticated:                
            global user, role_id
            user = request.user.id    
            role_id = request.user.role_id 

        if request.method == "GET":
            # 🔹 Fetch all funding sources
            fundingsources = FundingSourceMaster.objects.all()

            # 🔹 Encrypt the source_id for each funding source
            for fs in fundingsources:
                fs.encrypted_id = enc(str(fs.source_id))

            return render(
                request,
                'Master/fundingsource_master_index.html',
                {"fundingsources": fundingsources}
            )

    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        fun = tb[0].name
        callproc("stp_error_log", [fun, str(e), user])  
        messages.error(request, 'Oops...! Something went wrong!')
        return redirect("dashboard")  # fallback redirect
    
@login_required
def update_fundingsource_status(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            encrypted_id = data.get("id")      # from JS
            is_active = data.get("status")     # from JS

            if encrypted_id is None or is_active is None:
                return JsonResponse({"success": False, "error": "Missing data"}, status=400)

            # 🔹 Decrypt and convert
            source_id = int(dec(encrypted_id))

            # 🔹 Fetch funding source using the correct PK
            fundingsource = FundingSourceMaster.objects.get(source_id=source_id)

            fundingsource.is_active = bool(int(is_active))
            fundingsource.save()

            return JsonResponse({"success": True, "status": int(fundingsource.is_active)})

        except FundingSourceMaster.DoesNotExist:
            return JsonResponse({"success": False, "error": "Funding Source not found"}, status=404)
        except Exception as e:
            print("❌ Error:", e)
            return JsonResponse({"success": False, "error": str(e)}, status=400)

    return JsonResponse({"success": False, "error": "Invalid request"}, status=400)

@no_direct_access 
@login_required
def fundingsource_create(request):
    try:
        if not request.user.is_authenticated:
            # Clear any session flags
            if '_session_expired' in request.session:
                request.session.pop('_session_expired')
            messages.warning(request, "Your session has expired. Please log in again.")
            return redirect('library_list')
        
        user = request.user.id

        if request.method == "POST":
            enc_id = request.POST.get("id")   # 🔹 Hidden encrypted ID (if editing)
            funding_source_name = request.POST.get('funding_source_name')
            source_prefix = request.POST.get('sourcePrefix')
            is_active = request.POST.get('is_active', 1)

            if not source_prefix:
                messages.error(request, "Prefix is required!")
                return redirect("fundingsource_create")

            # 🔹 If enc_id exists → decrypt & update
            if enc_id:
                try:
                    fund_id = int(dec(enc_id))  # ✅ decrypt
                    funding = FundingSourceMaster.objects.get(fund_id=fund_id)

                    funding.funding_source_name = funding_source_name
                    funding.source_code = source_prefix   # ✅ update prefix also
                    funding.is_active = is_active
                    funding.updated_by = user
                    funding.updated_at = timezone.now()
                    funding.save()

                    messages.success(request, f"Funding Source '{funding_source_name}' updated successfully!")
                    return redirect("fundingsource_master_index")

                except FundingSourceMaster.DoesNotExist:
                    messages.error(request, "Funding Source not found.")
                    return redirect("fundingsource_master_index")

            # 🔹 Create new funding source with only prefix
            FundingSourceMaster.objects.create(
                source_code=source_prefix,      # ✅ only prefix, no numbers
                funding_source_name=funding_source_name,
                is_active=is_active,
                created_by=user,
                created_at=timezone.now()
            )

            messages.success(request, f"Funding Source '{funding_source_name}' created successfully with code {source_prefix}!")
            return redirect('fundingsource_master_index')

        # GET → Show form
        return render(request, "Master/fundingsource_create.html")

    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        fun = tb[0].name
        callproc("stp_error_log", [fun, str(e), user])
        messages.error(request, 'Oops...! Something went wrong!')
        return redirect("fundingsource_master_index")

@no_direct_access 
@login_required
def fundingsource_edit(request):
    funding = None

    if not request.user.is_authenticated:
            # Clear any session flags
            if '_session_expired' in request.session:
                request.session.pop('_session_expired')
            messages.warning(request, "Your session has expired. Please log in again.")
            return redirect('library_list')
        
    try:
        if request.method == "POST":
            # 🔹 Get encrypted ID from hidden form field
            enc_id = request.POST.get("source_id")
            if not enc_id:
                messages.error(request, "Missing Funding Source ID!")
                return redirect("fundingsource_master_index")

            # 🔹 Decrypt the ID
            try:
                source_id = int(dec(enc_id))
            except Exception as e:
                print("❌ Decryption error:", e)
                messages.error(request, "Invalid or corrupted ID!")
                return redirect("fundingsource_master_index")

            # 🔹 Fetch the funding source
            try:
                funding = FundingSourceMaster.objects.get(source_id=source_id)
            except FundingSourceMaster.DoesNotExist:
                messages.error(request, "Funding Source not found!")
                return redirect("fundingsource_master_index")

            user_id = request.user.id

            # ✅ Get form data
            source_code = request.POST.get("sourcePrefix", "").strip()
            funding_source_name = request.POST.get("funding_source_name", "").strip()
            is_active = request.POST.get("is_active", "1")

            # ✅ Validate required fields
            if not source_code or not funding_source_name:
                messages.error(request, "Funding Source Code and Name are required!")
                return redirect(request.path)

            # 🔹 Duplicate check for funding source name only
            duplicate_name = FundingSourceMaster.objects.filter(
                funding_source_name__iexact=funding_source_name
            ).exclude(source_id=funding.source_id)
            if duplicate_name.exists():
                messages.error(request, f"Funding Source '{funding_source_name}' already exists!")
                return redirect("fundingsource_master_index")

            # 🔹 Update the record
            funding.source_code = source_code
            funding.funding_source_name = funding_source_name
            funding.is_active = bool(int(is_active))
            funding.updated_by = user_id
            funding.updated_at = timezone.now()
            funding.save()

            messages.success(request, "Funding Source updated successfully!")
            return redirect("fundingsource_master_index")

        else:  # GET request
            enc_id = request.GET.get("source_id")
            if not enc_id:
                messages.error(request, "Missing Funding Source ID!")
                return redirect("fundingsource_master_index")

            # 🔹 Decrypt ID
            try:
                source_id = int(dec(enc_id))
            except Exception as e:
                print("❌ Decryption error:", e)
                messages.error(request, "Invalid or corrupted ID!")
                return redirect("fundingsource_master_index")

            # 🔹 Fetch record to pre-fill the form
            try:
                funding = FundingSourceMaster.objects.get(source_id=source_id)
                funding.encrypted_id = enc(str(funding.source_id))  # for hidden input
            except FundingSourceMaster.DoesNotExist:
                messages.error(request, "Funding Source not found!")
                return redirect("fundingsource_master_index")

    except Exception as e:
        print("❌ Unexpected Error:", e)
        messages.error(request, "An unexpected error occurred!")
        return redirect("fundingsource_master_index")

    # 🔹 Render edit form
    return render(request, "Master/fundingsource_edit.html", {"funding": funding})

@no_direct_access 
@login_required
def fundingsource_view(request):
    try:
        if not request.user.is_authenticated:
            # Clear any session flags
            if '_session_expired' in request.session:
                request.session.pop('_session_expired')
            messages.warning(request, "Your session has expired. Please log in again.")
            return redirect('library_list')
        
        enc_id = request.GET.get("source_id")
        if not enc_id:
            messages.error(request, "Missing Funding Source ID!")
            return redirect("fundingsource_master_index")

        # 🔹 Decrypt ID
        source_id = int(dec(enc_id))

        # 🔹 Fetch funding source
        funding = FundingSourceMaster.objects.get(source_id=source_id)

        # 🔹 Add encrypted_id for buttons/links
        funding.encrypted_id = enc(str(funding.source_id))

        context = {"funding": funding}
        return render(request, "Master/fundingsource_view.html", context)

    except FundingSourceMaster.DoesNotExist:
        messages.error(request, "Funding Source not found!")
        return redirect("fundingsource_master_index")
    except Exception as e:
        print("❌ Decryption/View Error:", e)
        messages.error(request, "Invalid or corrupted ID!")
        return redirect("fundingsource_master_index")
    
@login_required
def fundingsource_delete(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)  # parse JSON
            enc_id = data.get("id")  # encrypted ID
        except (json.JSONDecodeError, KeyError):
            return JsonResponse({"success": False, "error": "Invalid data"})

        if not enc_id:
            return JsonResponse({"success": False, "error": "Funding Source ID is missing"})

        try:
            # 🔹 Decrypt the ID
            source_id = int(dec(enc_id))

            # 🔹 Fetch and delete using the correct field name
            funding_source = FundingSourceMaster.objects.get(source_id=source_id)
            funding_source.delete()
            return JsonResponse({"success": True})

        except FundingSourceMaster.DoesNotExist:
            return JsonResponse({"success": False, "error": "Funding Source not found"})
        except Exception as e:
            print("❌ Delete Error:", e)
            return JsonResponse({"success": False, "error": "Invalid or corrupted ID"})

    return JsonResponse({"success": False, "error": "Invalid request"})

# condition at entry master index

@no_direct_access 
@login_required
def conditionatentry_master_index(request):
    try:
        if not request.user.is_authenticated:
            # Clear any session flags
            if '_session_expired' in request.session:
                request.session.pop('_session_expired')
            messages.warning(request, "Your session has expired. Please log in again.")
            return redirect('library_list')
        
        if request.user.is_authenticated:                
            global user, role_id
            user = request.user.id    
            role_id = request.user.role_id 

        if request.method == "GET":
            # 🔹 Fetch all condition at entry records (ascending by condition_id)
            conditions = ConditionAtEntryMaster.objects.all().order_by('condition_id')

            # 🔹 Encrypt the condition_id for each record
            for cond in conditions:
                cond.encrypted_id = enc(str(cond.condition_id))

            # 🔹 Render the page
            return render(
                request,
                'Master/conditionatentry_master_index.html',
                {"conditions": conditions}
            )

    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        fun = tb[0].name
        callproc("stp_error_log", [fun, str(e), user])  
        messages.error(request, 'Oops...! Something went wrong!')
        return redirect("dashboard")  # fallback redirect

@login_required
def update_conditionatentry_status(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            encrypted_id = data.get("id")      # from JS
            is_active = data.get("status")     # from JS

            if encrypted_id is None or is_active is None:
                return JsonResponse({"success": False, "error": "Missing data"}, status=400)

            # 🔹 Decrypt and convert
            condition_id = int(dec(encrypted_id))

            # 🔹 Fetch condition entry using the correct PK
            condition = ConditionAtEntryMaster.objects.get(condition_id=condition_id)

            condition.is_active = bool(int(is_active))
            condition.save()

            return JsonResponse({"success": True, "status": int(condition.is_active)})

        except ConditionAtEntryMaster.DoesNotExist:
            return JsonResponse({"success": False, "error": "Condition Entry not found"}, status=404)
        except Exception as e:
            print("❌ Error:", e)
            return JsonResponse({"success": False, "error": str(e)}, status=400)

    return JsonResponse({"success": False, "error": "Invalid request"}, status=400)

@no_direct_access 
@login_required
def conditionatentry_edit(request):
    condition = None
    
    if not request.user.is_authenticated:
        # Clear any session flags
        if '_session_expired' in request.session:
            request.session.pop('_session_expired')
        messages.warning(request, "Your session has expired. Please log in again.")
        return redirect('library_list')

    try:
        if request.method == "POST":
            # 🔹 Get encrypted ID from hidden form field
            enc_id = request.POST.get("condition_id")
            if not enc_id:
                messages.error(request, "Missing Condition ID!")
                return redirect("conditionatentry_master_index")

            # 🔹 Decrypt the ID
            try:
                condition_id = int(dec(enc_id))
            except Exception as e:
                print("❌ Decryption error:", e)
                messages.error(request, "Invalid or corrupted ID!")
                return redirect("conditionatentry_master_index")

            # 🔹 Fetch the condition record
            condition = ConditionAtEntryMaster.objects.get(condition_id=condition_id)

            user_id = request.user.id

            # ✅ Get form data
            condition_code = request.POST.get("condition_code", "").strip()
            condition_at_entry = request.POST.get("condition_at_entry", "").strip()
            is_active = request.POST.get("is_active", "1")

            # ✅ Validate required fields
            if not condition_code or not condition_at_entry:
                messages.error(request, "Condition Code and Name are required!")
                return redirect(request.path)

            # 🔹 Duplicate check for condition_at_entry
            duplicate_name = ConditionAtEntryMaster.objects.filter(
                condition_at_entry__iexact=condition_at_entry
            ).exclude(condition_id=condition.condition_id)
            if duplicate_name.exists():
                messages.error(request, f"Condition '{condition_at_entry}' already exists!")
                return redirect("conditionatentry_master_index")

            # 🔹 Update the record
            condition.condition_code = condition_code
            condition.condition_at_entry = condition_at_entry
            condition.is_active = bool(int(is_active))
            condition.updated_by = user_id
            condition.updated_at = timezone.now()
            condition.save()

            messages.success(request, "Condition updated successfully!")
            return redirect("conditionatentry_master_index")

        else:  # GET request
            enc_id = request.GET.get("condition_id")
            if not enc_id:
                messages.error(request, "Missing Condition ID!")
                return redirect("conditionatentry_master_index")

            # 🔹 Decrypt ID
            try:
                condition_id = int(dec(enc_id))
            except Exception as e:
                print("❌ Decryption error:", e)
                messages.error(request, "Invalid or corrupted ID!")
                return redirect("conditionatentry_master_index")

            # 🔹 Fetch record directly
            condition = ConditionAtEntryMaster.objects.get(condition_id=condition_id)
            condition.encrypted_id = enc(str(condition.condition_id))  # for hidden input

    except Exception as e:
        print("❌ Unexpected Error:", e)
        messages.error(request, "An unexpected error occurred!")
        return redirect("conditionatentry_master_index")

    # 🔹 Render edit form
    return render(request, "Master/conditionatentry_edit.html", {"condition": condition})

@no_direct_access 
@login_required
def conditionatentry_create(request):
    try:
        if not request.user.is_authenticated:
            # Clear any session flags
            if '_session_expired' in request.session:
                request.session.pop('_session_expired')
            messages.warning(request, "Your session has expired. Please log in again.")
            return redirect('library_list')
    
        user = request.user.id

        if request.method == "POST":
            enc_id = request.POST.get("id")   # 🔹 Hidden encrypted ID (if editing)
            condition_at_entry = request.POST.get("condition_at_entry", "").strip()
            condition_code = request.POST.get("condition_code", "").strip()
            is_active = request.POST.get("is_active", 1)

            if not condition_code:
                messages.error(request, "Condition Code is required!")
                return redirect("conditionatentry_create")

            # 🔹 If enc_id exists → decrypt & update
            if enc_id:
                try:
                    condition_id = int(dec(enc_id))  # ✅ decrypt
                    condition = ConditionAtEntryMaster.objects.get(condition_id=condition_id)

                    condition.condition_at_entry = condition_at_entry
                    condition.condition_code = condition_code
                    condition.is_active = is_active
                    condition.updated_by = user
                    condition.updated_at = timezone.now()
                    condition.save()

                    messages.success(request, f"Condition '{condition_at_entry}' updated successfully!")
                    return redirect("conditionatentry_master_index")

                except ConditionAtEntryMaster.DoesNotExist:
                    messages.error(request, "Condition not found.")
                    return redirect("conditionatentry_master_index")

            # 🔹 Create new condition at entry
            ConditionAtEntryMaster.objects.create(
                condition_code=condition_code,
                condition_at_entry=condition_at_entry,
                is_active=is_active,
                created_by=user,
                created_at=timezone.now()
            )

            messages.success(request, f"Condition '{condition_at_entry}' created successfully with code {condition_code}!")
            return redirect("conditionatentry_master_index")

        # GET → Show form
        return render(request, "Master/conditionatentry_create.html")

    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        fun = tb[0].name
        callproc("stp_error_log", [fun, str(e), user])
        messages.error(request, 'Oops...! Something went wrong!')
        return redirect("conditionatentry_master_index")

@no_direct_access 
@login_required
def conditionatentry_view(request):
    try:
        if not request.user.is_authenticated:
            # Clear any session flags
            if '_session_expired' in request.session:
                request.session.pop('_session_expired')
            messages.warning(request, "Your session has expired. Please log in again.")
            return redirect('library_list')
        
        enc_id = request.GET.get("condition_id")
        if not enc_id:
            messages.error(request, "Missing Condition ID!")
            return redirect("conditionatentry_master_index")

        # 🔹 Decrypt ID
        condition_id = int(dec(enc_id))

        # 🔹 Fetch condition record
        condition = ConditionAtEntryMaster.objects.get(condition_id=condition_id)

        # 🔹 Add encrypted_id for buttons/links
        condition.encrypted_id = enc(str(condition.condition_id))

        context = {"condition": condition}
        return render(request, "Master/conditionatentry_view.html", context)

    except ConditionAtEntryMaster.DoesNotExist:
        messages.error(request, "Condition record not found!")
        return redirect("conditionatentry_master_index")
    except Exception as e:
        print("❌ Decryption/View Error:", e)
        messages.error(request, "Invalid or corrupted ID!")
        return redirect("conditionatentry_master_index")

@login_required
def conditionatentry_delete(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)  # parse JSON
            enc_id = data.get("id")  # encrypted ID
        except (json.JSONDecodeError, KeyError):
            return JsonResponse({"success": False, "error": "Invalid data"})

        if not enc_id:
            return JsonResponse({"success": False, "error": "Condition At Entry ID is missing"})

        try:
            # 🔹 Decrypt the ID
            condition_id = int(dec(enc_id))

            # 🔹 Fetch and delete using the correct field name
            condition = ConditionAtEntryMaster.objects.get(condition_id=condition_id)
            condition.delete()
            return JsonResponse({"success": True})

        except ConditionAtEntryMaster.DoesNotExist:
            return JsonResponse({"success": False, "error": "Condition At Entry not found"})
        except Exception as e:
            print("❌ Delete Error:", e)
            return JsonResponse({"success": False, "error": "Invalid or corrupted ID"})

    return JsonResponse({"success": False, "error": "Invalid request"})

# ward master index

@no_direct_access 
@login_required
def ward_master_index(request):
    try:
        if not request.user.is_authenticated:
            # Clear any session flags
            if '_session_expired' in request.session:
                request.session.pop('_session_expired')
            messages.warning(request, "Your session has expired. Please log in again.")
            return redirect('library_list')
        
        if request.user.is_authenticated:                
            global user, role_id
            user = request.user.id    
            role_id = request.user.role_id 

        if request.method == "GET":
            # 🔹 Fetch all ward records
            wards = WardMaster.objects.all()

            # 🔹 Encrypt the ward_id for each record
            for ward in wards:
                ward.encrypted_id = enc(str(ward.ward_id))

            return render(
                request,
                'Master/ward_master_index.html',
                {"wards": wards}
            )

    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        fun = tb[0].name
        callproc("stp_error_log", [fun, str(e), user])  
        messages.error(request, 'Oops...! Something went wrong!')
        return redirect("dashboard")  # fallback redirect

@no_direct_access 
@login_required
def update_ward_status(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            encrypted_id = data.get("id")      # from JS
            is_active = data.get("status")     # from JS

            if encrypted_id is None or is_active is None:
                return JsonResponse({"success": False, "error": "Missing data"}, status=400)

            # 🔹 Decrypt and convert
            ward_id = int(dec(encrypted_id))

            # 🔹 Fetch ward using the correct PK
            ward = WardMaster.objects.get(ward_id=ward_id)

            ward.is_active = bool(int(is_active))
            ward.save()

            return JsonResponse({"success": True, "status": int(ward.is_active)})

        except WardMaster.DoesNotExist:
            return JsonResponse({"success": False, "error": "Ward not found"}, status=404)
        except Exception as e:
            print("❌ Error:", e)
            return JsonResponse({"success": False, "error": str(e)}, status=400)

    return JsonResponse({"success": False, "error": "Invalid request"}, status=400)

@no_direct_access 
@login_required
def ward_create(request):
    try:
        if not request.user.is_authenticated:
            # Clear any session flags
            if '_session_expired' in request.session:
                request.session.pop('_session_expired')
            messages.warning(request, "Your session has expired. Please log in again.")
            return redirect('library_list')
        
        user = request.user.id

        if request.method == "POST":
            enc_id = request.POST.get("id")   # 🔹 Hidden encrypted ID (if editing)
            ward_name = request.POST.get("ward_name", "").strip()
            pincode = request.POST.get("pincode", "").strip()
            ward_address = request.POST.get("ward_address", "").strip()
            accounting_code_id = request.POST.get("accounting_code")  # ForeignKey
            is_active = int(request.POST.get("is_active", 1))

            if not ward_name:
                messages.error(request, "Ward Name is required!")
                return redirect("ward_create")

            # 🔹 If enc_id exists → decrypt & update
            if enc_id:
                try:
                    ward_id = int(dec(enc_id))  # ✅ decrypt
                    ward = WardMaster.objects.get(ward_id=ward_id)

                    ward.ward_name = ward_name
                    ward.ward_address = ward_address
                    ward.pincode = pincode

                    if accounting_code_id:
                        ward.accounting_code_id = int(accounting_code_id)  # assign FK id
                    else:
                        ward.accounting_code = None

                    ward.is_active = is_active
                    ward.updated_by = user
                    ward.updated_at = timezone.now()
                    ward.save()

                    messages.success(request, f"Ward '{ward_name}' updated successfully!")
                    return redirect("ward_master_index")

                except WardMaster.DoesNotExist:
                    messages.error(request, "Ward not found.")
                    return redirect("ward_master_index")

            # 🔹 Create new ward
            WardMaster.objects.create(
                ward_name=ward_name,
                ward_address=ward_address,
                pincode=pincode,
                accounting_code_id=int(accounting_code_id) if accounting_code_id else None,
                is_active=is_active,
                created_by=user,
                created_at=timezone.now()
            )

            messages.success(request, f"Ward '{ward_name}' created successfully!")
            return redirect("ward_master_index")

        # GET → Show form
        # ✅ Pass only active accounting codes if you need a dropdown
        active_accounting_codes = WardMaster.objects.filter(is_active=1)
        return render(
            request, 
            "Master/ward_create.html", 
            {"accounting_codes": active_accounting_codes}
        )

    except Exception as e:
        import traceback
        tb = traceback.extract_tb(e.__traceback__)
        fun = tb[0].name
        callproc("stp_error_log", [fun, str(e), user])
        messages.error(request, 'Oops...! Something went wrong!')
        return redirect("ward_master_index")
    
@no_direct_access 
@login_required
def ward_master_edit(request):
    try:
        if not request.user.is_authenticated:
            # Clear any session flags
            if '_session_expired' in request.session:
                request.session.pop('_session_expired')
            messages.warning(request, "Your session has expired. Please log in again.")
            return redirect('library_list')
        
        user_id = request.user.id

        if request.method == "POST":

            # 🔹 Get encrypted ID
            enc_id = request.POST.get("id")
            if not enc_id:
                messages.error(request, "Missing Ward ID!")
                return redirect("ward_master_index")

            # 🔹 Decrypt ID
            try:
                ward_id = int(dec(enc_id))
            except Exception as e:
                print("❌ Decryption error:", e)
                messages.error(request, "Invalid or corrupted ID!")
                return redirect("ward_master_index")

            # 🔹 Fetch the record
            ward = WardMaster.objects.get(ward_id=ward_id)

            # ✅ Get form data
            ward_name = request.POST.get("ward_name", "").strip()
            pincode = request.POST.get("pincode", "").strip()
            ward_address = request.POST.get("ward_address", "").strip()

            # 🔹 accounting_code is a TextField — NOT a ForeignKey
            accounting_code = request.POST.get("accounting_code", "").strip()

            is_active = int(request.POST.get("is_active", "1"))

            # Validate required fields
            if not ward_name or not ward_address or not pincode:
                messages.error(request, "Ward Name, Address, and Pincode are required!")
                return redirect(request.path)

            # Duplicate check
            duplicate_name = WardMaster.objects.filter(
                ward_name__iexact=ward_name
            ).exclude(ward_id=ward.ward_id)

            if duplicate_name.exists():
                messages.error(request, f"Ward '{ward_name}' already exists!")
                return redirect("ward_master_index")

            # 🔹 Update the record
            ward.ward_name = ward_name
            ward.ward_address = ward_address
            ward.pincode = pincode
            ward.accounting_code = accounting_code  # ✔ Correct
            ward.is_active = is_active
            ward.updated_by = user_id
            ward.updated_at = timezone.now()
            ward.save()

            messages.success(request, "Ward updated successfully!")
            return redirect("ward_master_index")

        else:  # GET request
            enc_id = request.GET.get("ward_id")
            if not enc_id:
                messages.error(request, "Missing Ward ID!")
                return redirect("ward_master_index")

            # Decrypt ID
            try:
                ward_id = int(dec(enc_id))
            except Exception as e:
                print("❌ Decryption error:", e)
                messages.error(request, "Invalid or corrupted ID!")
                return redirect("ward_master_index")

            # Fetch record
            ward = WardMaster.objects.get(ward_id=ward_id)
            ward.encrypted_id = enc(str(ward.ward_id))  # for hidden input

        # Only active wards for dropdown (if needed)
        active_accounting_codes = WardMaster.objects.filter(is_active=1)

        return render(
            request,
            "Master/ward_master_edit.html",
            {
                "ward": ward,
                "accounting_codes": active_accounting_codes
            }
        )

    except Exception as e:
        import traceback
        tb = traceback.extract_tb(e.__traceback__)
        fun = tb[0].name
        callproc("stp_error_log", [fun, str(e), user_id])
        messages.error(request, "An unexpected error occurred!")
        return redirect("ward_master_index")

@no_direct_access 
@login_required
def ward_master_view(request):
    try:
        if not request.user.is_authenticated:
            # Clear any session flags
            if '_session_expired' in request.session:
                request.session.pop('_session_expired')
            messages.warning(request, "Your session has expired. Please log in again.")
            return redirect('library_list')
        
        enc_id = request.GET.get("ward_id")
        if not enc_id:
            messages.error(request, "Missing Ward ID!")
            return redirect("ward_master_index")

        # 🔹 Decrypt ID
        ward_id = int(dec(enc_id))

        # 🔹 Fetch ward record
        ward = WardMaster.objects.get(ward_id=ward_id)

        # 🔹 Add encrypted_id for buttons/links
        ward.encrypted_id = enc(str(ward.ward_id))

        context = {"ward": ward}
        return render(request, "Master/ward_master_view.html", context)

    except WardMaster.DoesNotExist:
        messages.error(request, "Ward not found!")
        return redirect("ward_master_index")
    except Exception as e:
        print("❌ Decryption/View Error:", e)
        messages.error(request, "Invalid or corrupted ID!")
        return redirect("ward_master_index")
    
@login_required
def ward_master_delete(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)  # parse JSON
            enc_id = data.get("id")  # encrypted ID
        except (json.JSONDecodeError, KeyError):
            return JsonResponse({"success": False, "error": "Invalid data"})

        if not enc_id:
            return JsonResponse({"success": False, "error": "Ward ID is missing"})

        try:
            # 🔹 Decrypt the ID
            ward_id = int(dec(enc_id))

            # 🔹 Fetch and delete record
            ward = WardMaster.objects.get(ward_id=ward_id)
            ward.delete()
            return JsonResponse({"success": True})

        except WardMaster.DoesNotExist:
            return JsonResponse({"success": False, "error": "Ward not found"})
        except Exception as e:
            print("❌ Delete Error:", e)
            return JsonResponse({"success": False, "error": "Invalid or corrupted ID"})

    return JsonResponse({"success": False, "error": "Invalid request"})

# location master index

@no_direct_access 
@login_required
def location_master_index(request):
    try:
        if not request.user.is_authenticated:
            # Clear any session flags
            if '_session_expired' in request.session:
                request.session.pop('_session_expired')
            messages.warning(request, "Your session has expired. Please log in again.")
            return redirect('library_list')
        
        if request.user.is_authenticated:                
            global user, role_id
            user = request.user.id    
            role_id = request.user.role_id 

        if request.method == "GET":
            # 🔹 Fetch all location records with related ward
            locations = LibraryLocationMaster.objects.all()

            # 🔹 Attach encrypted_id & ward_name for each record
            for location in locations:
                location.encrypted_id = enc(str(location.location_id))

                try:
                    ward = WardMaster.objects.get(ward_id=location.ward_id)
                    location.ward_name = ward.ward_name
                except WardMaster.DoesNotExist:
                    location.ward_name = "N/A"

            return render(
                request,
                'Master/location_master_index.html',
                {"locations": locations}
            )

    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        fun = tb[0].name
        callproc("stp_error_log", [fun, str(e), user])  
        messages.error(request, 'Oops...! Something went wrong!')
        return redirect("dashboard")  # fallback redirect
    
@login_required
def update_location_status(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            encrypted_id = data.get("id")      # from JS
            is_active = data.get("status")     # from JS

            if encrypted_id is None or is_active is None:
                return JsonResponse({"success": False, "error": "Missing data"}, status=400)

            # 🔹 Decrypt and convert
            location_id = int(dec(encrypted_id))

            # 🔹 Fetch location using the correct PK
            location = LibraryLocationMaster.objects.get(location_id=location_id)

            location.is_active = bool(int(is_active))
            location.save()

            return JsonResponse({"success": True, "status": int(location.is_active)})

        except LibraryLocationMaster.DoesNotExist:
            return JsonResponse({"success": False, "error": "Location not found"}, status=404)
        except Exception as e:
            print("❌ Error:", e)
            return JsonResponse({"success": False, "error": str(e)}, status=400)

    return JsonResponse({"success": False, "error": "Invalid request"}, status=400)

@no_direct_access 
@login_required
def location_create(request):
    try:
        if not request.user.is_authenticated:
            # Clear any session flags
            if '_session_expired' in request.session:
                request.session.pop('_session_expired')
            messages.warning(request, "Your session has expired. Please log in again.")
            return redirect('library_list')
        
        user = request.user.id

        if request.method == "POST":
            enc_id = request.POST.get("id")   # Hidden encrypted ID (if editing)
            location_name = request.POST.get("location_name", "").strip()
            address = request.POST.get("address", "").strip()
            pincode = request.POST.get("pincode", "").strip()
            ward_id = request.POST.get("ward_id", "").strip()
            is_active = request.POST.get("is_active", 1)

            if not location_name:
                messages.error(request, "Location Name is required!")
                return redirect("location_create")

            # 🔹 If enc_id exists → Update
            if enc_id:
                try:
                    location_id = int(dec(enc_id))
                    location = LibraryLocationMaster.objects.get(location_id=location_id)

                    location.location_name = location_name
                    location.address = address
                    location.pincode = pincode
                    location.ward_id = ward_id if ward_id else None
                    location.is_active = is_active
                    location.updated_by = user
                    location.updated_at = timezone.now()
                    location.save()

                    messages.success(request, f"Location '{location_name}' updated successfully!")
                    return redirect("location_master_index")

                except LibraryLocationMaster.DoesNotExist:
                    messages.error(request, "Location not found.")
                    return redirect("location_master_index")

            # 🔹 Create new
            LibraryLocationMaster.objects.create(
                location_name=location_name,
                address=address,
                pincode=pincode,
                ward_id=ward_id if ward_id else None,
                is_active=is_active,
                created_by=user,
                created_at=timezone.now()
            )

            messages.success(request, f"Location '{location_name}' created successfully!")
            return redirect("location_master_index")

        # GET → Show form
        wards = WardMaster.objects.filter(is_active=True)  # 🔹 Fetch active wards
        return render(request, "Master/location_create.html", {"wards": wards})

    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        fun = tb[0].name
        callproc("stp_error_log", [fun, str(e), user])
        messages.error(request, 'Oops...! Something went wrong!')
        return redirect("location_master_index")

@no_direct_access 
@login_required
def location_master_edit(request):
    location = None

    if not request.user.is_authenticated:
        # Clear any session flags
        if '_session_expired' in request.session:
            request.session.pop('_session_expired')
        messages.warning(request, "Your session has expired. Please log in again.")
        return redirect('library_list')
        
    try:
        if request.method == "POST":
            # 🔹 Get encrypted ID from hidden form field
            enc_id = request.POST.get("id")
            if not enc_id:
                messages.error(request, "Missing Location ID!")
                return redirect("location_master_index")

            # 🔹 Decrypt the ID
            try:
                location_id = int(dec(enc_id))
            except Exception as e:
                print("❌ Decryption error:", e)
                messages.error(request, "Invalid or corrupted ID!")
                return redirect("location_master_index")

            # 🔹 Fetch the location record
            location = LibraryLocationMaster.objects.get(location_id=location_id)
            user_id = request.user.id

            # ✅ Get form data
            location_name = request.POST.get("location_name", "").strip()
            address = request.POST.get("address", "").strip()
            pincode = request.POST.get("pincode", "").strip()
            ward_id = request.POST.get("ward_id", "").strip()
            is_active = request.POST.get("is_active", "1")

            # ✅ Validate required fields
            if not location_name or not address or not pincode or not ward_id:
                messages.error(request, "All fields are required!")
                return redirect(request.path)

            # 🔹 Duplicate check for location_name
            duplicate_name = LibraryLocationMaster.objects.filter(
                location_name__iexact=location_name
            ).exclude(location_id=location.location_id)
            if duplicate_name.exists():
                messages.error(request, f"Location '{location_name}' already exists!")
                return redirect("location_master_index")

            # 🔹 Update the record
            location.location_name = location_name
            location.address = address
            location.pincode = pincode
            location.ward_id = ward_id if ward_id else None
            location.is_active = bool(int(is_active))
            location.updated_by = user_id
            location.updated_at = timezone.now()
            location.save()

            messages.success(request, "Location updated successfully!")
            return redirect("location_master_index")

        else:  # GET request
            enc_id = request.GET.get("location_id")
            if not enc_id:
                messages.error(request, "Missing Location ID!")
                return redirect("location_master_index")

            # 🔹 Decrypt ID
            try:
                location_id = int(dec(enc_id))
            except Exception as e:
                print("❌ Decryption error:", e)
                messages.error(request, "Invalid or corrupted ID!")
                return redirect("location_master_index")

            # 🔹 Fetch record directly
            location = LibraryLocationMaster.objects.get(location_id=location_id)
            location.encrypted_id = enc(str(location.location_id))  # for hidden input

    except Exception as e:
        print("❌ Unexpected Error:", e)
        messages.error(request, "An unexpected error occurred!")
        return redirect("location_master_index")

    # 🔹 Fetch active wards for dropdown
    wards = WardMaster.objects.filter(is_active=True)

    # 🔹 Render edit form
    return render(request, "Master/location_master_edit.html", {
        "location": location,
        "wards": wards
    })

@no_direct_access 
@login_required
def location_master_view(request):
    try:
        if not request.user.is_authenticated:
            # Clear any session flags
            if '_session_expired' in request.session:
                request.session.pop('_session_expired')
            messages.warning(request, "Your session has expired. Please log in again.")
            return redirect('library_list')
    
        enc_id = request.GET.get("location_id")
        if not enc_id:
            messages.error(request, "Missing Location ID!")
            return redirect("location_master_index")

        # 🔹 Decrypt Location ID
        location_id = int(dec(enc_id))

        # 🔹 Fetch location record
        location = LibraryLocationMaster.objects.get(location_id=location_id)

        # 🔹 Add encrypted_id for buttons/links
        location.encrypted_id = enc(str(location.location_id))

        # 🔹 If ward_id exists → decrypt & fetch ward details
        ward = None
        if location.ward_id:
            try:
                ward = WardMaster.objects.get(ward_id=location.ward_id)
                ward.encrypted_id = enc(str(ward.ward_id))
            except WardMaster.DoesNotExist:
                ward = None

        context = {
            "location": location,
            "ward": ward  # ⚡ full ward object (with decrypted/encrypted ID)
        }
        return render(request, "Master/location_master_view.html", context)

    except LibraryLocationMaster.DoesNotExist:
        messages.error(request, "Location not found!")
        return redirect("location_master_index")
    except Exception as e:
        print("❌ Decryption/View Error:", e)
        messages.error(request, "Invalid or corrupted ID!")
        return redirect("location_master_index")

@login_required
def location_master_delete(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)  # parse JSON
            enc_id = data.get("id")  # encrypted ID
        except (json.JSONDecodeError, KeyError):
            return JsonResponse({"success": False, "error": "Invalid data"})

        if not enc_id:
            return JsonResponse({"success": False, "error": "Location ID is missing"})

        try:
            # 🔹 Decrypt the ID
            location_id = int(dec(enc_id))

            # 🔹 Fetch and delete record
            location = LibraryLocationMaster.objects.get(location_id=location_id)
            location.delete()
            return JsonResponse({"success": True})

        except LibraryLocationMaster.DoesNotExist:
            return JsonResponse({"success": False, "error": "Location not found"})
        except Exception as e:
            print("❌ Delete Error:", e)
            return JsonResponse({"success": False, "error": "Invalid or corrupted ID"})

    return JsonResponse({"success": False, "error": "Invalid request"})

@no_direct_access
@login_required
def library_master_index(request):
    try:
        if request.user.is_authenticated:                
            user = request.user.id    
            role_id = request.user.role_id 

        if request.method == "GET":
            # 🔹 Fetch all library records
            libraries = LibraryMaster.objects.all()

            # 🔹 Attach encrypted_id, ward_name, accounting_code_name, location_name
            for library in libraries:
                library.encrypted_id = enc(str(library.id))

                # ✅ Fetch parent ward name safely
                if library.parent_ward:
                    library.parent_ward_name = library.parent_ward.ward_name
                else:
                    library.parent_ward_name = "N/A"

                # ✅ Fetch library accounting code (ward) name safely
                if library.library_accounting_code:
                    library.accounting_code_name = library.library_accounting_code.accounting_code
                else:
                    library.accounting_code_name = "N/A"

                # ✅ Fetch location name safely
                if library.location:
                    library.location_name = library.location.location_name
                else:
                    library.location_name = "N/A"

            return render(
                request,
                'Master/library_master_index.html',
                {"libraries": libraries}
            )

    except Exception as e:
        import traceback
        tb = traceback.extract_tb(e.__traceback__)
        fun = tb[0].name
        callproc("stp_error_log", [fun, str(e), user])  
        messages.error(request, 'Oops...! Something went wrong!')
        return redirect("dashboard")

@login_required
def update_library_status(request):
    if request.method == "POST":
        try:
            import json
            data = json.loads(request.body)
            encrypted_id = data.get("id")      # from JS
            is_active = data.get("status")     # from JS

            if encrypted_id is None or is_active is None:
                return JsonResponse({"success": False, "error": "Missing data"}, status=400)

            # 🔹 Decrypt and convert
            library_id = int(dec(encrypted_id))

            # 🔹 Fetch library using the correct PK
            library = LibraryMaster.objects.get(id=library_id)

            library.is_active = bool(int(is_active))
            library.save()

            return JsonResponse({"success": True, "status": int(library.is_active)})

        except LibraryMaster.DoesNotExist:
            return JsonResponse({"success": False, "error": "Library not found"}, status=404)
        except Exception as e:
            print("❌ Error:", e)
            return JsonResponse({"success": False, "error": str(e)}, status=400)

    return JsonResponse({"success": False, "error": "Invalid request"}, status=400)

@no_direct_access
@login_required
def library_create(request):
    try:
        if not request.user.is_authenticated:
            # Clear any session flags
            if '_session_expired' in request.session:
                request.session.pop('_session_expired')
            messages.warning(request, "Your session has expired. Please log in again.")
            return redirect('library_list')
        
        user = request.user.id

        if request.method == "POST":
            enc_id = request.POST.get("id")  # Hidden encrypted ID (if editing)

            # 🔹 Form fields
            library_code = request.POST.get("library_code", "").strip()
            library_name = request.POST.get("library_name", "").strip()
            library_name_mar = request.POST.get("library_name_mar", "").strip()
            location_id = request.POST.get("location_id", "").strip()
            accounting_code_id = request.POST.get("accounting_code_id", "").strip()
            parent_ward_id = request.POST.get("parent_ward_id", "").strip()
            librarian_name = request.POST.get("librarian_name", "").strip()
            contact_email = request.POST.get("contact_email", "").strip()
            contact_phone = request.POST.get("contact_phone", "").strip()
            landing_page_link = request.POST.get("landing_page_link", "").strip()
            about_library = request.POST.get("about_library", "").strip()
            library_rules = request.POST.get("library_rules", "").strip()
            membership_rules = request.POST.get("membership_rules", "").strip()
            membership_page_link = request.POST.get("membership_page_link", "").strip()
            opening_hours = request.POST.get("opening_hours", "").strip()
            est_year = request.POST.get("est_year", "").strip()
            location_url = request.POST.get("location_url", "").strip()
            facebook_url = request.POST.get("facebook_url", "").strip()
            twitter_url = request.POST.get("twitter_url", "").strip()
            instagram_url = request.POST.get("instagram_url", "").strip()
            youtube_url = request.POST.get("youtube_url", "").strip()
            capacity = request.POST.get("capacity", "").strip()

            # Safe conversion for is_active
            try:
                is_active = int(request.POST.get("is_active", 1))
            except ValueError:
                is_active = 1

            # 🔹 Uploaded file

            # 🔹 Validation
            if not library_name:
                messages.error(request, "Library Name is required!")
                return redirect("library_create")

            # ========================================================
            # 📂 Save in Documents: MEDIA_ROOT/<library_code>/library_images/
            # ========================================================
            # image_url = ""
            # if library_image:
            #     # Full path for saving the file
            #     image_path = os.path.join(
            #         settings.MEDIA_ROOT,
            #         library_code,
            #         "library_images",
            #         library_image.name
            #     )

            #     # Ensure directory exists
            #     os.makedirs(os.path.dirname(image_path), exist_ok=True)

            #     # Save uploaded file
            #     with open(image_path, "wb+") as f:
            #         for chunk in library_image.chunks():
            #             f.write(chunk)

            #     # ✅ Relative path for DB (no leading slash, works with MEDIA_URL)
            #     image_url = f"/{library_code}/library_images/{library_image.name}"

            # 🔹 Update existing library
            
            image_urls = []

            library_images = request.FILES.getlist("library_image")  # ✅ THIS IS THE FIX

            if library_images:
                from django.utils.timezone import now
                import os, uuid

                for library_image in library_images[:3]:  # max 3
                    filename, ext = os.path.splitext(library_image.name)

                    short_uuid = str(uuid.uuid4())[:8]
                    timestamp = now().strftime("%Y%m%d%H%M%S")

                    safe_filename = ''.join(
                        c for c in filename if c.isalnum() or c in (' ', '-', '_')
                    ).rstrip()

                    unique_filename = (
                        f"{library_code}_library_{safe_filename}_{timestamp}_{short_uuid}{ext}"
                    )

                    save_path = f"{library_code}/library_images/{unique_filename}"

                    saved_path = file_storage_service.save_file(
                        library_image,
                        save_path
                    )

                    image_urls.append(saved_path)

            image_url = ",".join(image_urls)
            
            
            if enc_id:
                library_id = int(dec(enc_id))
                library = LibraryMaster.objects.get(id=library_id)

                library.library_code = library_code
                library.library_name = library_name
                library.library_name_mar = library_name_mar
                library.location_id = int(location_id) if location_id and location_id.isdigit() else None
                library.parent_ward_id = int(parent_ward_id) if parent_ward_id and parent_ward_id.isdigit() else None
                library.library_accounting_code_id = int(accounting_code_id) if accounting_code_id and accounting_code_id.isdigit() else None
                library.librarian_name = librarian_name
                library.contact_email = contact_email
                library.contact_phone = contact_phone
                library.landing_page_link = landing_page_link
                library.about_library = about_library
                library.library_rules = library_rules
                library.membership_rules = membership_rules
                library.membership_page_link = membership_page_link
                library.opening_hours = opening_hours
                library.est_year = int(est_year) if est_year.isdigit() else None
                library.location_url = location_url
                library.facebook_url = facebook_url
                library.twitter_url = twitter_url
                library.instagram_url = instagram_url
                library.youtube_url = youtube_url
                library.capacity = capacity
                library.is_active = is_active
                library.updated_by = user
                library.updated_at = timezone.now()
                if image_url:
                    library.image_url = image_url
                library.save()

                messages.success(request, f"Library '{library_name}' updated successfully!")
                return redirect("library_master_index")

            # 🔹 Create new library
            LibraryMaster.objects.create(
                library_code=library_code,
                library_name=library_name,
                library_name_mar=library_name_mar,
                location_id=int(location_id) if location_id and location_id.isdigit() else None,
                parent_ward_id=int(parent_ward_id) if parent_ward_id and parent_ward_id.isdigit() else None,
                library_accounting_code_id=int(accounting_code_id) if accounting_code_id and accounting_code_id.isdigit() else None,
                librarian_name=librarian_name,
                contact_email=contact_email,
                contact_phone=contact_phone,
                landing_page_link=landing_page_link,
                about_library=about_library,
                library_rules=library_rules,
                membership_rules=membership_rules,
                membership_page_link=membership_page_link,
                opening_hours=opening_hours,
                est_year=int(est_year) if est_year.isdigit() else None,
                location_url=location_url,
                image_url=image_url,
                facebook_url=facebook_url,
                twitter_url=twitter_url,
                instagram_url=instagram_url,
                youtube_url=youtube_url,
                capacity=capacity,
                is_active=is_active,
                created_by=user,
                created_at=timezone.now()
            )
            messages.success(request, f"Library '{library_name}' created successfully!")
            return redirect("library_master_index")

        # ---------- GET request (form) ----------
        last_code = LibraryMaster.objects.aggregate(max_code=Max("library_code"))["max_code"]
        if last_code:
            try:
                last_number = int(last_code.replace("L", ""))
            except:
                last_number = 0
            next_number = last_number + 1
        else:
            next_number = 1
        new_library_code = f"L{next_number:02d}"

        active_wards = WardMaster.objects.filter(is_active=1)
        active_locations = LibraryLocationMaster.objects.filter(is_active=1)
        active_accounting_codes = WardMaster.objects.filter(is_active=1)

        return render(
            request,
            "Master/library_create.html",
            {
                "wards": active_wards,
                "locations": active_locations,
                "accounting_codes": active_accounting_codes,
                "new_library_code": new_library_code,
            }
        )

    except Exception as e:
        import traceback
        tb = traceback.extract_tb(e.__traceback__)
        fun = tb[0].name
        callproc("stp_error_log", [fun, str(e), user])
        print("❌ Library Create Error:", e)
        messages.error(request, "Oops...! Something went wrong!")
        return redirect("library_master_index")

@no_direct_access
@login_required
def library_master_edit(request):
    library = None

    try:
        
        if not request.user.is_authenticated:
            # Clear any session flags
            if '_session_expired' in request.session:
                request.session.pop('_session_expired')
            messages.warning(request, "Your session has expired. Please log in again.")
            return redirect('library_list')
        
        if request.method == "POST":
            # 🔹 Get encrypted ID from hidden form
            enc_id = request.POST.get("id")
            if not enc_id:
                messages.error(request, "Missing Library ID!")
                return redirect("library_master_index")

            # 🔹 Decrypt ID safely
            try:
                library_id = int(dec(enc_id))
            except Exception:
                messages.error(request, "Invalid or corrupted ID!")
                return redirect("library_master_index")

            # 🔹 Fetch library record
            try:
                library = LibraryMaster.objects.get(id=library_id)
            except LibraryMaster.DoesNotExist:
                messages.error(request, "Library not found!")
                return redirect("library_master_index")

            user_id = request.user.id

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
            landing_page_link = request.POST.get("landing_page_link", "").strip()
            about_library = request.POST.get("about_library", "").strip()
            library_rules = request.POST.get("library_rules", "").strip()
            membership_rules = request.POST.get("membership_rules", "").strip()
            membership_page_link = request.POST.get("membership_page_link", "").strip()
            opening_hours = request.POST.get("opening_hours", "").strip()
            est_year = request.POST.get("est_year", "").strip()
            location_url = request.POST.get("location_url", "").strip()
            facebook_url = request.POST.get("facebook_url", "").strip()
            twitter_url = request.POST.get("twitter_url", "").strip()
            instagram_url = request.POST.get("instagram_url", "").strip()
            youtube_url = request.POST.get("youtube_url", "").strip()
            capacity = request.POST.get("capacity", "").strip()
            is_active = int(request.POST.get("is_active", 1))

            # ------------------------
            # Uploaded image
            # ------------------------
            # library_image = request.FILES.get("library_photo")
            # image_url = library.image_url  # keep old if no new image

            # if library_image:
            #     library_folder = os.path.join(settings.MEDIA_ROOT, library_code, "library_images")
            #     os.makedirs(library_folder, exist_ok=True)

            #     image_path = os.path.join(library_folder, library_image.name)
            #     with open(image_path, "wb+") as f:
            #         for chunk in library_image.chunks():
            #             f.write(chunk)

            #     image_url = os.path.join(library_code, "library_images", library_image.name).replace("\\", "/")
            
            library_images = request.FILES.getlist("library_photo")
            removed_images = request.POST.get("removed_images")

            # 1️⃣ Existing DB paths
            existing_paths = []
            if library.image_url:
                existing_paths = [
                    p.strip().lstrip("/")
                    for p in library.image_url.split(",")
                    if p.strip()
                ]
            removed_paths = []

            if removed_images:
                removed_urls = json.loads(removed_images)

                for full_url in removed_urls:
                    decoded_url = unquote(full_url)
                    parsed_path = urlparse(decoded_url).path

                    for db_path in existing_paths:
                        # 🔥 KEY FIX: match by suffix
                        if parsed_path.endswith(db_path):
                            removed_paths.append(db_path)
                            break

            print("DB PATHS:", existing_paths)
            print("REMOVED PATHS:", removed_paths)

            # 3️⃣ Remaining images
            remaining_existing = [
                p for p in existing_paths if p not in removed_paths
            ]

            # 4️⃣ Save new images
            new_paths = []
            for image in library_images:
                save_path = f"{library_code}/library_images/{image.name}"

                normalized_path = file_storage_service.save_file(
                    file=image,
                    save_path=save_path
                )
                new_paths.append(normalized_path)

            # 5️⃣ Merge & save
            final_paths = remaining_existing + new_paths
            image_url = ",".join(final_paths) if final_paths else ""

            # ------------------------
            # Validation
            # ------------------------
            if not library_name:
                messages.error(request, "Library Name is required!")
                return redirect(request.path)

            # ------------------------
            # Duplicate checks
            # ------------------------
            duplicate_code = LibraryMaster.objects.filter(library_code__iexact=library_code).exclude(id=library.id)
            if duplicate_code.exists():
                messages.error(request, f"Library Code '{library_code}' already exists!")
                return redirect("library_master_index")

            duplicate_name = LibraryMaster.objects.filter(library_name__iexact=library_name).exclude(id=library.id)
            if duplicate_name.exists():
                messages.error(request, f"Library Name '{library_name}' already exists!")
                return redirect("library_master_index")

            # ------------------------
            # Update record
            # ------------------------
            library.library_code = library_code
            library.library_name = library_name
            library.library_name_mar = library_name_mar
            library.location_id = int(location_id) if location_id.isdigit() else None
            library.parent_ward_id = int(parent_ward_id) if parent_ward_id.isdigit() else None
            library.library_accounting_code_id = int(accounting_code_id) if accounting_code_id.isdigit() else None
            library.librarian_name = librarian_name
            library.contact_email = contact_email
            library.contact_phone = contact_phone
            library.landing_page_link = landing_page_link
            library.about_library = about_library
            library.library_rules = library_rules
            library.membership_rules = membership_rules
            library.membership_page_link = membership_page_link
            library.opening_hours = opening_hours
            library.est_year = int(est_year) if est_year.isdigit() else None
            library.location_url = location_url
            library.image_url = image_url
            library.facebook_url = facebook_url
            library.twitter_url = twitter_url
            library.instagram_url = instagram_url
            library.youtube_url = youtube_url
            library.capacity = capacity
            library.is_active = bool(is_active)
            library.updated_by = user_id
            library.updated_at = timezone.now()
            library.save()

            messages.success(request, f"Library '{library_name}' updated successfully!")
            return redirect("library_master_index")

        else:  # GET request
            enc_id = request.GET.get("library_id")
            if not enc_id:
                messages.error(request, "Missing Library ID!")
                return redirect("library_master_index")

            try:
                library_id = int(dec(enc_id))
            except Exception:
                messages.error(request, "Invalid or corrupted ID!")
                return redirect("library_master_index")

            try:
                library = LibraryMaster.objects.get(id=library_id)
            except LibraryMaster.DoesNotExist:
                messages.error(request, "Library not found!")
                return redirect("library_master_index")

            library.encrypted_id = enc(str(library.id))

        # ------------------------
        # Prepare display image
        # ------------------------
        if library.image_url:
            library.display_image_urls = [
                file_storage_service.get_file_url(img.strip().lstrip("/"))
                for img in library.image_url.split(",")
                if img.strip()
            ]
        else:
            library.display_image_urls = []

    except Exception as e:
        import traceback
        print("❌ Library Edit Error:", traceback.format_exc())
        messages.error(request, "Oops...! Something went wrong!")
        return redirect("library_master_index")

    # ------------------------
    # Dropdowns
    # ------------------------
    active_wards = WardMaster.objects.filter(is_active=True)
    active_locations = LibraryLocationMaster.objects.filter(is_active=True)
    active_accounting_codes = WardMaster.objects.filter(is_active=True)

    return render(request, "Master/library_master_edit.html", {
        "library": library,
        "wards": active_wards,
        "locations": active_locations,
        "accounting_codes": active_accounting_codes,
    })

@no_direct_access    
@login_required
def library_master_view(request):
    try:
        
        if not request.user.is_authenticated:
            # Clear any session flags
            if '_session_expired' in request.session:
                request.session.pop('_session_expired')
            messages.warning(request, "Your session has expired. Please log in again.")
            return redirect('library_list')
        
        enc_id = request.GET.get("id")  # Must match your template link: ?id={{ library.encrypted_id }}
        if not enc_id:
            messages.error(request, "Missing Library ID!")
            return redirect("library_master_index")

        # 🔹 Decrypt Library ID
        library_id = int(dec(enc_id))

        # 🔹 Fetch main library record
        library = LibraryMaster.objects.get(id=library_id)
        library.encrypted_id = enc(str(library.id))

        # 🔹 Set display image URL
        # library.display_image_url = None
        # if library.image_url:
        #     library.display_image_url = settings.MEDIA_URL + str(library.image_url)
        
        if library.image_url:
            # If multiple images stored as comma-separated
            paths = [p.strip() for p in library.image_url.split(",") if p.strip()]
            # Convert each path to full URL using your storage service
            library.display_image_urls = [file_storage_service.get_file_url(p) for p in paths]
        else:
            library.display_image_urls = []

        # 🔹 Fetch location details if location_id exists (if stored in LibraryMaster)
        location = None
        if library.location_id:
            try:
                location = LibraryMaster.objects.get(id=library.location_id)
                location.encrypted_id = enc(str(location.id))
            except LibraryMaster.DoesNotExist:
                location = None

        context = {
            "library": library,
            "location": location
        }
        return render(request, "Master/library_master_view.html", context)

    except LibraryMaster.DoesNotExist:
        messages.error(request, "Library not found!")
        return redirect("library_master_index")
    except Exception as e:
        print("❌ Decryption/View Error:", e)
        messages.error(request, "Invalid or corrupted ID!")
        return redirect("library_master_index")

@login_required
def library_master_delete(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)  # parse JSON
            enc_id = data.get("id")  # encrypted ID
        except (json.JSONDecodeError, KeyError):
            return JsonResponse({"success": False, "error": "Invalid data"})

        if not enc_id:
            return JsonResponse({"success": False, "error": "Library ID is missing"})

        try:
            # 🔹 Decrypt the ID
            library_id = int(dec(enc_id))

            # 🔹 Fetch and delete record
            library = LibraryMaster.objects.get(id=library_id)
            library.delete()
            return JsonResponse({"success": True})

        except LibraryMaster.DoesNotExist:
            return JsonResponse({"success": False, "error": "Library not found"})
        except Exception as e:
            print("❌ Delete Error:", e)
            return JsonResponse({"success": False, "error": "Invalid or corrupted ID"})

    return JsonResponse({"success": False, "error": "Invalid request"})

# circulation master

@no_direct_access 
@login_required   
def circulation_master_index(request):
    try:
            
        if not request.user.is_authenticated:
            # Clear any session flags
            if '_session_expired' in request.session:
                request.session.pop('_session_expired')
            messages.warning(request, "Your session has expired. Please log in again.")
            return redirect('library_list')
        
        user = request.user.id    
        role_id = request.user.role_id 
        library_code = request.session.get('library_db', None)
        username = request.session.get('username', None)

        if request.method == "GET":
            # Fetch circulation data with joins
            circulation_data = (
                CirculationCopyStatus.objects
                .select_related(
                    'bookcatalog',
                    'bookcatalog__subject',
                    'shelf_location',
                    'current_status',
                    'processing_status'
                )
                .annotate(
                    cat_ref_num=F('bookcatalog__cat_ref_num'),
                    title=F('bookcatalog__title'),
                    isbn=F('bookcatalog__isbn_issn'),
                    subject=F('bookcatalog__subject__subjectNameEnglish'),  # you can switch to Marathi
                    shelf_location_name=F('shelf_location__location_name'),
                    current_status_name=F('current_status__status_name'),
                    processing_status_name=F('processing_status__status_name'),
                )
                .values(
                    'id',
                    'cat_ref_num',
                    'title',
                    'isbn',
                    'subject',
                    'barcode',
                    'shelf_location_name',
                    'current_status_name',
                    'processing_status_name',
                    'accession_no',
                )
            )
            
            for cd in circulation_data:
                cd['circulation_id_enc'] = enc(str(cd['id']))

            context = {
                'circulation_data': circulation_data
            }

            return render(request, 'Master/circulation_master_index.html', context)

    except Exception as e:
        import traceback
        tb = traceback.extract_tb(e.__traceback__)
        fun = tb[0].name
        callproc("stp_error_log", [fun, str(e), user])  
        messages.error(request, 'Oops...! Something went wrong!')
        return redirect("circulation_master_index")

@no_direct_access 
@login_required 
def circulation_master_view(request):
    try:
            
        if not request.user.is_authenticated:
            # Clear any session flags
            if '_session_expired' in request.session:
                request.session.pop('_session_expired')
            messages.warning(request, "Your session has expired. Please log in again.")
            return redirect('library_list')
        
        user = request.user.id    
        role_id = request.user.role_id 
        library_code = request.session.get('library_db', None)
        username = request.session.get('username', None)
            
        circulation_id = dec(str(request.GET.get("circulationid")))
        if not circulation_id:
            messages.error(request, "Missing Circulation ID!")
            return redirect("circulation_master_index")
        

        # Fetch circulation record with joins
        circulation = (
            CirculationCopyStatus.objects
            .select_related(
                'bookcatalog',
                'bookcatalog__subject',
                'shelf_location',
                'current_status',
                'processing_status'
            )
            .get(id=circulation_id)
        )
        
        # Get image URLs using FileStorageService
        front_page_url = "#"
        last_page_url = "#"
        
        if circulation.bookcatalog.front_page_photo:
            front_page_url = file_storage_service.get_file_url(circulation.bookcatalog.front_page_photo)
        
        if circulation.bookcatalog.last_page_photo:
            last_page_url = file_storage_service.get_file_url(circulation.bookcatalog.last_page_photo)

        return render(request, "Master/circulation_master_view.html", {
            "circulation": circulation,
            'front_page_url': front_page_url,
            'last_page_url': last_page_url,
            'MEDIA_URL': settings.MEDIA_URL,  # Still useful for other media
            'file_storage_service': file_storage_service,  # Pass service instance
        })

    except Exception as e:
        import traceback
        tb = traceback.extract_tb(e.__traceback__)
        fun = tb[0].name
        callproc("stp_error_log", [fun, str(e), user])  
        messages.error(request, 'Oops...! Something went wrong!')
        return redirect("circulation_master_index")
    
@no_direct_access 
@login_required   
def circulation_master_edit(request):
    try:
        if not request.user.is_authenticated:
            # Clear any session flags
            if '_session_expired' in request.session:
                request.session.pop('_session_expired')
            messages.warning(request, "Your session has expired. Please log in again.")
            return redirect('library_list')
        
        user = request.user.id    
        role_id = request.user.role_id 
        library_code = request.session.get('library_db', None)
        username = request.session.get('username', None)
        
        if request.method == "GET":    
            circulation_id = dec(str(request.GET.get("circulationid")))
            if not circulation_id:
                messages.error(request, "Missing Circulation ID!")
                return redirect("circulation_master_index")

            # Fetch the circulation record with joins
            circulation = (
                CirculationCopyStatus.objects
                .select_related(
                    'bookcatalog',
                    'bookcatalog__subject',
                    'shelf_location',
                    'current_status',
                    'processing_status'
                )
                .get(id=circulation_id)
            )
            
            for circulation in [circulation]:
                circulation.circulation_id_enc = enc(str(circulation.id))
                
            # Get image URLs using FileStorageService
            front_page_url = "#"
            last_page_url = "#"
            
            if circulation.bookcatalog.front_page_photo:
                front_page_url = file_storage_service.get_file_url(circulation.bookcatalog.front_page_photo)
            
            if circulation.bookcatalog.last_page_photo:
                last_page_url = file_storage_service.get_file_url(circulation.bookcatalog.last_page_photo)

            # Dropdown options
            circulation_statuses = status_master.objects.filter(status_type="Circulation Status", is_active=1)
            processing_statuses = status_master.objects.filter(status_type="Inventory", is_active=1)
            locations = ResourceLocationMaster.objects.filter(is_active=1)
            
            return render(request, "Master/circulation_master_edit.html", {
                "circulation": circulation,
                "circulation_statuses": circulation_statuses,
                "processing_statuses": processing_statuses,
                "locations": locations,
                'MEDIA_URL': settings.MEDIA_URL,
                'front_page_url': front_page_url,
                'last_page_url': last_page_url,
                'file_storage_service': file_storage_service,  # Pass service instance if needed
            })

        if request.method == "POST":
            circulation_id = dec(str(request.POST.get("circulation_id")))
            if not circulation_id:
                messages.error(request, "Circulation ID missing!")
                return redirect("circulation_master_index")

            try:
                circulation = CirculationCopyStatus.objects.get(id=circulation_id)

                # Get posted values (could be typed text)
                status_id = request.POST.get("status")
                processing_status_id = request.POST.get("processing_status")
                location_id = request.POST.get("location")

                # --- Only update if values changed ---
                updated = False

                if circulation.current_status_id != int(status_id):
                    circulation.current_status_id = int(status_id)
                    updated = True

                if circulation.processing_status_id != int(processing_status_id):
                    circulation.processing_status_id = int(processing_status_id)
                    updated = True

                if circulation.shelf_location_id != int(location_id):
                    circulation.shelf_location_id = int(location_id)
                    updated = True

                if updated:
                    circulation.updated_by = user  # or request.user.username
                    circulation.save()
                    messages.success(request, "परिपत्रक तपशील यशस्वीपणे अद्यतनित केले गेले आहेत.")
                else:
                    messages.info(request, "काहीही बदललेले नाही, अद्यतन आवश्यक नाही.")

                return redirect("circulation_master_index")

            except Exception as e:
                import traceback
                tb = traceback.extract_tb(e.__traceback__)
                fun = tb[0].name
                user = request.session.get("username")
                callproc("stp_error_log", [fun, str(e), user])
                messages.error(request, 'Oops...! Something went wrong!')
                return redirect("circulation_master_index")


    except Exception as e:
        import traceback
        tb = traceback.extract_tb(e.__traceback__)
        fun = tb[0].name
        user = request.session.get("username")
        callproc("stp_error_log", [fun, str(e), user])
        messages.error(request, 'Oops...! Something went wrong!')
        return redirect("circulation_master_index")
    
@no_direct_access 
@login_required    
def ebook_catalog_index(request):
    try:
        if not request.user.is_authenticated:
            # Clear any session flags
            if '_session_expired' in request.session:
                request.session.pop('_session_expired')
            messages.warning(request, "Your session has expired. Please log in again.")
            return redirect('library_list')
        user = request.user.id
        role_id = request.user.role_id

       
        ecatalogs = LibraryEbook.objects.all().order_by("-ebook_id")

        for c in ecatalogs:
        
            c.encrypted_id = enc(str(c.ebook_id))
            c.status_obj = status_master.objects.filter(pk=c.eb_status_id).first()

        # return render(request, "Master/ebook_catalog_index.html", {"catalogs": ecatalogs})
    
        return render(request, "Master/ebook_catalog_index.html", {
                "catalogs": ecatalogs,
            })

    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        fun = tb[0].name
        callproc("stp_error_log", [fun, str(e), user])
        messages.error(request, 'Oops...! Something went wrong!')
        # Always return HttpResponse, even on error
        return render(request, 'Master/ebook_catalog_index.html', {"catalogs": []})

@no_direct_access 
@login_required   
def ebook_create(request):
    try:
        if not request.user.is_authenticated:
            # Clear any session flags
            if '_session_expired' in request.session:
                request.session.pop('_session_expired')
            messages.warning(request, "Your session has expired. Please log in again.")
            return redirect('library_list')
        user = request.user.id

        # ---------- AJAX endpoints ----------
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            action = request.GET.get('action', '').strip()
            search_term = request.GET.get('search', '').strip().lower()
            response_data = []

            if action == "get_titles":
                language = request.GET.get("language", "").strip()
                search = request.GET.get("search", "").strip()

                qs = BookCatalog.objects.filter(language=language)

                if search:
                    qs = qs.filter(title__icontains=search)

                titles = qs.values("cat_ref_num", "title")[:50]
                return JsonResponse({"data": list(titles)})

            elif action == "search_authors":
                authors_query = BookCatalog.objects.filter(
                    ~Q(author__exact=""),
                    author__isnull=False
                ).values_list('author', flat=True).distinct()

                if search_term:
                    response_data = [a for a in authors_query if search_term in a.lower()]

                return JsonResponse({"data": list(response_data)[:50]})

            elif action == "get_publishers":
                response_data = LibraryEbook.objects.filter(
                    ~Q(eb_publisher__exact=""),
                    eb_publisher__isnull=False
                ).values_list('eb_publisher', flat=True).distinct().order_by('eb_publisher')

                return JsonResponse({"data": list(response_data)})

            
        # ---------- GET ----------
        if request.method == "GET":
            languages = (
                BookCatalog.objects
                .exclude(language__isnull=True)
                .exclude(language__exact="")
                .values_list("language", flat=True)
                .distinct()
                .order_by("language")
            )


            subjects = SubjectTypeMaster.objects.filter(is_active=True)
            for s in subjects:
                s.encrypted_id = enc(str(s.id))
                s.subjectCode = s.subjectCode or "000"

            ebook_types = EbookTypeMaster.objects.filter(is_active=True).order_by("ebookTypeCode")
            for et in ebook_types:
                et.encrypted_id = enc(str(et.type_id))

            authors = BookCatalog.objects.filter(
                ~Q(author__exact=""),
                author__isnull=False
            ).values_list("author", flat=True).distinct()[:10]

            publishers = LibraryEbook.objects.filter(
                ~Q(eb_publisher__exact=""),
                eb_publisher__isnull=False
            ).values_list("eb_publisher", flat=True).distinct()

            from datetime import datetime
            years = list(range(datetime.now().year, 1899, -1))

            return render(request, "Master/ebook_create.html", {
                "languages": languages,
                "subjects": subjects,
                "ebook_types": ebook_types,
                "authors": authors,
                "publishers": publishers,
                "years": years
            })

        # ---------- POST ----------
        if request.method == "POST":

            # ---------- TITLE HANDLING ----------
            # manual_title = request.POST.get("eb_title_text", "").strip()
            # catalog_title = request.POST.get("eb_title_catalog", "").strip()
            eb_title = request.POST.get("eb_title_text", "").strip()
            cat_id = request.POST.get("cat_id", "").strip()

            ebook_type_value = request.POST.get("ebook_type", "").strip()
            ebook_type_id = dec(ebook_type_value) if ebook_type_value else None
            ebook_type = EbookTypeMaster.objects.filter(type_id=ebook_type_id).first()

            # if ebook_type and "library" in ebook_type.ebookTypeCode.lower() and cat_id:
            #     eb_title = catalog_title
            # else:
            #     eb_title = manual_title
            #     cat_id = None
            if not (ebook_type and "library" in ebook_type.ebookTypeCode.lower()):cat_id = None


            # ---------- FILE INPUTS ----------
            pdf_file = request.FILES.get("eb_pdf_url")
            front_photo = request.FILES.get("eb_front_page_photo")
            last_photo = request.FILES.get("eb_last_page_photo")

            # ---------- FORM DATA ----------
            form_data = {
                "eb_title": eb_title,
                "eb_subtitle": request.POST.get("eb_subtitle", "").strip(),
                "eb_author": request.POST.get("eb_author", "").strip(),
                "eb_other_authors": request.POST.get("eb_other_authors", "").strip(),
                "eb_publisher": request.POST.get("eb_publisher", "").strip(),
                "eb_isbn_issn": request.POST.get("eb_isbn_issn", "").strip(),
                "eb_edition": request.POST.get("eb_edition", "").strip(),
                "eb_subject": dec(request.POST.get("eb_subject")) if request.POST.get("eb_subject") else None,
                "remarks": request.POST.get("remarks", "").strip(),
                "eb_keywords": request.POST.get("eb_keywords", "").strip(),
                "eb_language": request.POST.get("eb_language", "").strip(),
                "eb_publication_place": request.POST.get("eb_publication_place", "").strip(),
                "eb_year_of_publication": request.POST.get("eb_year_of_publication", "").strip(),
                "eb_pages": request.POST.get("eb_pages", "").strip(),
                "call_number": request.POST.get("call_number", "").strip(),
                "cutter_number": request.POST.get("cutter_number", "").strip(),
                "eb_classification_number": request.POST.get("eb_classification_number", "").strip(),
                "eb_date_of_registration": request.POST.get("eb_date_of_registration") or date.today(),
            }

            required = ["eb_title", "eb_author", "eb_language", "eb_subject"]
            subject = SubjectTypeMaster.objects.filter(id=form_data["eb_subject"]).first()
            if any(not form_data[k] for k in required):
                messages.error(request, "Please fill all mandatory fields")
                return redirect("ebook_create")
             # ---------- AUTO-GENERATE CUTTER NUMBER ----------
            if not form_data["cutter_number"] and form_data["eb_author"]:
                author_clean = ''.join(c for c in form_data["eb_author"] if c.isalpha())
                form_data["cutter_number"] = author_clean[:3].upper() if author_clean else "XXX"

            # ---------- AUTO-GENERATE CLASSIFICATION NUMBER ----------
            if not form_data["eb_classification_number"] and subject and subject.subjectCode:
                form_data["eb_classification_number"] = f"{subject.subjectCode:03}"

            # ---------- AUTO-GENERATE CALL NUMBER ----------
            if not form_data["call_number"] and form_data["eb_classification_number"] and form_data["cutter_number"]:
                year = form_data["eb_year_of_publication"] if form_data["eb_year_of_publication"].isdigit() else "XXXX"
                form_data["call_number"] = f"{form_data['eb_classification_number']}.{form_data['cutter_number']}.{year}"
            

            try:
                with transaction.atomic():
                    # Create ebook instance without file paths initially
                    ebook = LibraryEbook.objects.create(
                        eb_title=form_data["eb_title"],
                        eb_subtitle=form_data["eb_subtitle"],
                        eb_author=form_data["eb_author"],
                        eb_other_authors=form_data["eb_other_authors"],
                        eb_publisher=form_data["eb_publisher"],
                        eb_isbn_issn=form_data["eb_isbn_issn"],
                        eb_edition=form_data["eb_edition"],
                        eb_subject=subject,
                        ebook_type=ebook_type,
                        remarks=form_data["remarks"],
                        eb_keywords=form_data["eb_keywords"],
                        eb_language=form_data["eb_language"],
                        eb_publication_place=form_data["eb_publication_place"],
                        eb_year_of_publication=int(form_data["eb_year_of_publication"]) if form_data["eb_year_of_publication"].isdigit() else None,
                        eb_pages=form_data["eb_pages"],
                        eb_pdf_url=None,
                        eb_front_page_photo=None,
                        eb_last_page_photo=None,
                        call_number=form_data["call_number"],
                        cutter_number=form_data["cutter_number"],
                        eb_classification_number=form_data["eb_classification_number"],
                        eb_date_of_registration=form_data["eb_date_of_registration"],
                        eb_status_id=1,
                        created_by=user,
                        updated_by=user
                    )

                    # ---------- SAVE FILES USING FILE STORAGE SERVICE ----------
                    # Base directory structure
                    library_code = request.session.get("library_db", "default")
                    base_dir = f"{library_code}/EBooks/{ebook.ebook_id}"
                    
                    # ---------- SAVE PDF ----------
                    if pdf_file:
                        # Generate unique filename for PDF
                        original_name = os.path.splitext(pdf_file.name)[0]
                        timestamp = timezone.now().strftime("%Y%m%d_%H%M%S")
                        unique_filename = f"ebook_{original_name}_{timestamp}.pdf"
                        
                        # Build save path
                        pdf_save_path = f"{base_dir}/book_pdf/{unique_filename}"
                        
                        # ✅ Use FileStorageService to save file
                        saved_pdf_path = file_storage_service.save_file(pdf_file, pdf_save_path)
                        ebook.eb_pdf_url = saved_pdf_path

                    # ---------- SAVE FRONT IMAGE ----------
                    if front_photo:
                        # Generate unique filename for front image
                        original_ext = os.path.splitext(front_photo.name)[1].lower()
                        timestamp = timezone.now().strftime("%Y%m%d_%H%M%S")
                        unique_filename = f"front_{ebook.ebook_id}_{timestamp}{original_ext}"
                        
                        # Build save path
                        front_save_path = f"{base_dir}/book_images/{unique_filename}"
                        
                        # ✅ Use FileStorageService to save file
                        saved_front_path = file_storage_service.save_file(front_photo, front_save_path)
                        ebook.eb_front_page_photo = saved_front_path

                    # ---------- SAVE LAST IMAGE ----------
                    if last_photo:
                        # Generate unique filename for last image
                        original_ext = os.path.splitext(last_photo.name)[1].lower()
                        timestamp = timezone.now().strftime("%Y%m%d_%H%M%S")
                        unique_filename = f"back_{ebook.ebook_id}_{timestamp}{original_ext}"
                        
                        # Build save path
                        last_save_path = f"{base_dir}/book_images/{unique_filename}"
                        
                        # ✅ Use FileStorageService to save file
                        saved_last_path = file_storage_service.save_file(last_photo, last_save_path)
                        ebook.eb_last_page_photo = saved_last_path

                    # Save ebook with file paths
                    ebook.save()


                    # ---------- UPDATE BookCatalog ----------
                    if cat_id:
                        book = BookCatalog.objects.filter(cat_ref_num=cat_id).first()
                        if book:
                            book.ebook_id = ebook
                            book.ebook_available = "Yes"
                            book.updated_by = user
                            book.save()

                    ebook.save()

                messages.success(request, f"E-Book '{ebook.eb_title}' saved successfully!")
                return redirect("ebook_catalog_index")

            except Exception as e:
                messages.error(request, str(e))
                return redirect("ebook_create")

    
    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        callproc("stp_error_log", [tb[0].name, str(e), user])
        messages.error(request, "Oops! Something went wrong.")
        return redirect("ebook_create")

@no_direct_access 
@login_required   
def ebook_edit(request):
    try:
        if not request.user.is_authenticated:
            # Clear any session flags
            if '_session_expired' in request.session:
                request.session.pop('_session_expired')
            messages.warning(request, "Your session has expired. Please log in again.")
            return redirect('library_list')
        user = request.user.id

        # =========================================================
        # GET REQUEST
        # =========================================================
        if request.method == "GET":

            # ---------- AJAX AUTHOR SEARCH (FOR DROPDOWN) ----------
            if request.headers.get("x-requested-with") == "XMLHttpRequest":
                action = request.GET.get("action")

                if action == "search_authors":
                    search = request.GET.get("search", "").strip()

                    authors = (
                        BookCatalog.objects
                        .filter(author__icontains=search)
                        .values_list("author", flat=True)
                        .distinct()[:10]
                    )

                    return JsonResponse({"data": list(authors)})

            # ---------- NORMAL EDIT PAGE LOAD ----------
            encrypted_id = request.GET.get('ebook_id')

            if not encrypted_id:
                messages.error(request, "Invalid e-book.")
                return redirect('ebook_catalog_index')

            try:
                ebook_id = dec(encrypted_id)
            except:
                messages.error(request, "Invalid e-book.")
                return redirect('ebook_catalog_index')

            ebook = LibraryEbook.objects.filter(ebook_id=ebook_id).first()
            if not ebook:
                messages.error(request, "E-Book not found.")
                return redirect('ebook_catalog_index')

            languages = (
                BookCatalog.objects
                .exclude(language__isnull=True)
                .exclude(language__exact="")
                .values_list("language", flat=True)
                .distinct()
                .order_by("language")
            )

            subjects = SubjectTypeMaster.objects.filter(is_active=True)
            for sub in subjects:
                sub.encrypted_id = enc(str(sub.id))
                sub.subjectCode = sub.subjectCode or "000"

            ebook_types = EbookTypeMaster.objects.filter(is_active=True).order_by('ebookTypeCode')
            for etype in ebook_types:
                etype.encrypted_id = enc(str(etype.type_id))

            from datetime import datetime
            current_year = datetime.now().year
            years = list(range(current_year, 1899, -1))

            context = {
                "ebook": ebook,
                "languages": languages,
                "subjects": subjects,
                "ebook_types": ebook_types,
                "years": years,
                "encrypted_id": encrypted_id,
                "front_page_enc": enc(str(ebook.ebook_id) + "_front") if ebook.eb_front_page_photo else None,
                "last_page_enc": enc(str(ebook.ebook_id) + "_back") if ebook.eb_last_page_photo else None,
                "pdf_enc": enc(str(ebook.ebook_id) + "_pdf") if ebook.eb_pdf_url and not ebook.eb_pdf_url.startswith(('http://', 'https://')) else None,
            }

            return render(request, "Master/ebook_edit.html", context)

        # =========================================================
        # POST REQUEST (UPDATE)
        # =========================================================
        elif request.method == "POST":

            encrypted_id = request.POST.get('encrypted_id')
            if not encrypted_id:
                messages.error(request, "Invalid e-book.")
                return redirect('ebook_catalog_index')

            try:
                ebook_id = dec(encrypted_id)
            except:
                messages.error(request, "Invalid e-book.")
                return redirect('ebook_catalog_index')

            ebook = LibraryEbook.objects.filter(ebook_id=ebook_id).first()
            if not ebook:
                messages.error(request, "E-Book not found.")
                return redirect('ebook_catalog_index')

            form = request.POST

            # ---------- ALLOWED FIELD UPDATES ----------
            # ❗ Title & Ebook Type intentionally NOT updated (readonly)
            ebook.eb_subtitle = form.get('eb_subtitle', '').strip()
            ebook.eb_author = form.get('eb_author', '').strip()
            ebook.eb_other_authors = form.get('eb_other_authors', '').strip()
            ebook.eb_publisher = form.get('eb_publisher', '').strip()
            ebook.eb_isbn_issn = form.get('eb_isbn_issn', '').strip()
            ebook.eb_edition = form.get('eb_edition', '').strip()
            ebook.eb_keywords = form.get('eb_keywords', '').strip()
            ebook.eb_publication_place = form.get('eb_publication_place', '').strip()
            ebook.eb_year_of_publication = form.get('eb_year_of_publication') or None
            ebook.eb_pages = form.get('eb_pages', '').strip()
            ebook.remarks = form.get('remarks', '').strip()
            ebook.eb_language = form.get('eb_language', '').strip()
            external_url = form.get('eb_pdf_url', '').strip()

            ebook.eb_date_of_registration = (
                form.get('eb_date_of_registration')
                or ebook.eb_date_of_registration
            )

            # ---------- SUBJECT ----------
            subject_enc = form.get("eb_subject")
            ebook.eb_subject = (
                SubjectTypeMaster.objects.filter(id=dec(subject_enc)).first()
                if subject_enc else None
            )

            # ---------- REQUIRED FIELDS ----------
            if not ebook.eb_author or not ebook.eb_language or not ebook.eb_subject:
                messages.error(request, "Please fill all required fields.")
                return redirect(f"{request.path}?ebook_id={encrypted_id}")

            # =========================================================
            # FILE HANDLING WITH FILE STORAGE SERVICE
            # =========================================================
            library_code = request.session.get("library_db", "default")
            base_dir = f"{library_code}/EBooks/{ebook.ebook_id}"

            try:
                # ---------- PDF UPLOAD ----------
                pdf_file = request.FILES.get("ebook_file")
                if pdf_file:
                    # Validate file type
                    if not pdf_file.name.lower().endswith('.pdf'):
                        messages.error(request, "Only PDF files are allowed for ebooks.")
                        return redirect(f"{request.path}?ebook_id={encrypted_id}")
                    
                    # Generate unique filename
                    original_name = os.path.splitext(pdf_file.name)[0]
                    timestamp = timezone.now().strftime("%Y%m%d_%H%M%S")
                    unique_filename = f"ebook_{original_name}_{timestamp}.pdf"
                    
                    # Build save path
                    pdf_save_path = f"{base_dir}/book_pdf/{unique_filename}"
                    
                    # ✅ Delete old PDF file if exists
                    if ebook.eb_pdf_url and not ebook.eb_pdf_url.startswith(('http://', 'https://')):
                        file_storage_service.delete_file(ebook.eb_pdf_url)
                    
                    # ✅ Save new PDF using FileStorageService
                    saved_pdf_path = file_storage_service.save_file(pdf_file, pdf_save_path)
                    ebook.eb_pdf_url = saved_pdf_path
                
                elif external_url and external_url.startswith(("http://", "https://")):
                    # If updating with external URL and had a local PDF, delete the local file
                    if ebook.eb_pdf_url and not ebook.eb_pdf_url.startswith(('http://', 'https://')):
                        file_storage_service.delete_file(ebook.eb_pdf_url)
                    ebook.eb_pdf_url = external_url

                # ---------- FRONT IMAGE ----------
                front = request.FILES.get("eb_front_page_photo")
                if front:
                    # Validate image file
                    allowed_image_ext = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
                    ext = os.path.splitext(front.name)[1].lower()
                    if ext not in allowed_image_ext:
                        messages.error(request, "Only JPG, PNG, GIF, or WebP images are allowed.")
                        return redirect(f"{request.path}?ebook_id={encrypted_id}")
                    
                    # Generate unique filename
                    timestamp = timezone.now().strftime("%Y%m%d_%H%M%S")
                    unique_filename = f"front_{ebook.ebook_id}_{timestamp}{ext}"
                    
                    # Build save path
                    front_save_path = f"{base_dir}/book_images/{unique_filename}"
                    
                    # ✅ Delete old front image if exists
                    if ebook.eb_front_page_photo:
                        file_storage_service.delete_file(ebook.eb_front_page_photo)
                    
                    # ✅ Save new front image using FileStorageService
                    saved_front_path = file_storage_service.save_file(front, front_save_path)
                    ebook.eb_front_page_photo = saved_front_path

                # ---------- LAST IMAGE ----------
                last = request.FILES.get("eb_last_page_photo")
                if last:
                    # Validate image file
                    allowed_image_ext = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
                    ext = os.path.splitext(last.name)[1].lower()
                    if ext not in allowed_image_ext:
                        messages.error(request, "Only JPG, PNG, GIF, or WebP images are allowed.")
                        return redirect(f"{request.path}?ebook_id={encrypted_id}")
                    
                    # Generate unique filename
                    timestamp = timezone.now().strftime("%Y%m%d_%H%M%S")
                    unique_filename = f"back_{ebook.ebook_id}_{timestamp}{ext}"
                    
                    # Build save path
                    last_save_path = f"{base_dir}/book_images/{unique_filename}"
                    
                    # ✅ Delete old last image if exists
                    if ebook.eb_last_page_photo:
                        file_storage_service.delete_file(ebook.eb_last_page_photo)
                    
                    # ✅ Save new last image using FileStorageService
                    saved_last_path = file_storage_service.save_file(last, last_save_path)
                    ebook.eb_last_page_photo = saved_last_path

                # ---------- SAVE ----------
                ebook.updated_by = user
                ebook.save()

                messages.success(request, f"E-Book '{ebook.eb_title}' updated successfully!")
                return redirect('ebook_catalog_index')
            except Exception as e:
                messages.error(request, f"Error updating files: {str(e)}")
                return redirect(f"{request.path}?ebook_id={encrypted_id}")

    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        fun = tb[0].name
        callproc("stp_error_log", [fun, str(e), request.user.id])
        messages.error(request, "Oops... Something went wrong!")
        return redirect('ebook_catalog_index')
    
def secure_ebook_file_view(request, file_type_enc):
    """
    Secure view for ebook files (front page, last page, PDF)
    """
    try:
        # Decrypt the file type
        decrypted = dec(file_type_enc)
        ebook_id, file_type = decrypted.rsplit('_', 1)
        
        # Get the ebook
        ebook = get_object_or_404(LibraryEbook, ebook_id=int(ebook_id))
        
        # Determine which file to serve
        if file_type == 'front':
            file_path = ebook.eb_front_page_photo
            file_name = f"front_page_{ebook.ebook_id}.jpg"
        elif file_type == 'back':
            file_path = ebook.eb_last_page_photo
            file_name = f"last_page_{ebook.ebook_id}.jpg"
        elif file_type == 'pdf':
            file_path = ebook.eb_pdf_url
            file_name = f"{ebook.eb_title.replace(' ', '_')}.pdf"
        else:
            raise Http404("Invalid file type")
        
        if not file_path:
            raise Http404("File not found")
        
        # If it's an external URL, redirect to it
        if file_path.startswith(('http://', 'https://')):
            return redirect(file_path)
        
        # Get environment
        environment = getattr(settings, 'ENVIRONMENT', 'local')
        
        if environment == 'production':
            # ========== PRODUCTION: Stream from S3 ==========
            # Prepare S3 path
            s3_path = file_storage_service._prepare_path(file_path, add_base=True)
            
            # Get AWS credentials
            aws_access_key = getattr(settings, 'AWS_ACCESS_KEY_ID', '')
            aws_secret_key = getattr(settings, 'AWS_SECRET_ACCESS_KEY', '')
            bucket_name = getattr(settings, 'AWS_STORAGE_BUCKET_NAME', '')
            region = getattr(settings, 'AWS_S3_REGION_NAME', 'ap-south-1')
            
            if not all([aws_access_key, aws_secret_key, bucket_name]):
                raise Http404("S3 configuration missing")
            
            # Create S3 client
            s3_client = boto3.client(
                's3',
                aws_access_key_id=aws_access_key,
                aws_secret_access_key=aws_secret_key,
                region_name=region
            )
            
            try:
                # Get file from S3
                s3_response = s3_client.get_object(Bucket=bucket_name, Key=s3_path)
                
                # Get content type
                content_type = s3_response.get('ContentType', 'application/octet-stream')
                if content_type == 'application/octet-stream':
                    # Guess from filename
                    import mimetypes
                    guessed_type, _ = mimetypes.guess_type(file_name)
                    if guessed_type:
                        content_type = guessed_type
                
                # Stream the file
                from django.http import StreamingHttpResponse
                
                def file_iterator(file_obj, chunk_size=8192):
                    while True:
                        chunk = file_obj.read(chunk_size)
                        if not chunk:
                            break
                        yield chunk
                
                response = StreamingHttpResponse(
                    file_iterator(s3_response['Body']),
                    content_type=content_type
                )
                
                # Set headers
                from urllib.parse import quote
                response['Content-Disposition'] = f'inline; filename="{quote(file_name)}"'
                response['Content-Length'] = str(s3_response['ContentLength'])
                response['X-Content-Type-Options'] = 'nosniff'
                
                return response
                
            except ClientError as e:
                print(f"[secure_ebook_file_view] S3 error: {e}")
                raise Http404("File not found on S3")
                
        else:
            # ========== LOCAL/TEST: Serve from local filesystem ==========
            from django.http import FileResponse
            from pathlib import Path
            
            # Get file path
            file_path = Path(settings.MEDIA_ROOT) / Path(file_path.replace("\\", "/"))
            
            if not file_path.exists():
                raise Http404(f"File not found at: {file_path}")
            
            # Determine content type
            import mimetypes
            content_type, encoding = mimetypes.guess_type(str(file_path))
            if content_type is None:
                content_type = 'application/octet-stream'
            
            # Serve the file
            response = FileResponse(
                open(file_path, 'rb'),
                content_type=content_type,
                as_attachment=False,
                filename=file_name
            )
            
            response['X-Content-Type-Options'] = 'nosniff'
            
            return response
            
    except Http404:
        raise
    except Exception as e:
        print(f"[secure_ebook_file_view] Error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise Http404("File not found")

def track_click(request):
    if request.method == "POST":
        data = json.loads(request.body)
        page = data.get('page')

        # ✅ Only store clicks if page has a URL
        if not page:  
            return JsonResponse({'status': 'ignored', 'reason': 'no URL'})

        visitor, _ = VisitorActivity.objects.using('default').get_or_create(
            session_key=request.session.session_key
        )

        # Save click in the first available slot
        for i in range(1, 6):
            if getattr(visitor, f'click_{i}') is None:
                setattr(visitor, f'click_{i}', page)
                visitor.save(using='default')
                break

        return JsonResponse({'status': 'ok'})
    
def should_show_popup(request):
    try:
        visitor = VisitorActivity.objects.using('default').get(
            session_key=request.session.session_key
        )

        seconds = int((timezone.now() - visitor.session_start).total_seconds())

        if seconds >= 30000:
            visitor.popup_shown = True
            visitor.total_time_seconds = seconds
            visitor.save()
            return JsonResponse({'show_popup': True})

        return JsonResponse({'show_popup': False})
    except Exception as e:
        print("❌ Unexpected Error:", e)

def save_lead(request):
    try:
        if request.method == "POST":

            if not request.session.session_key:
                request.session.create()

            session = request.session.session_key

            visitor, created = VisitorActivity.objects.using('default').get_or_create(
                session_key=session
            )

            visitor.name = request.POST.get('name')
            visitor.popup_shown = True
            visitor.phone = request.POST.get('phone')
            visitor.email = request.POST.get('email')
            visitor.remark = request.POST.get('remark')

            visitor.save(using='default')  # 🔥 IMPORTANT

            return JsonResponse({'status': 'saved'})

        return JsonResponse({'status': 'invalid'}, status=400)

    except Exception as e:
        print("❌ Unexpected Error:", e)
        return JsonResponse({'status': 'error'}, status=500)

@login_required
def book_catalog_create_isbn(request):
    try:
        user = request.user.id

        # ---------- AJAX endpoints ----------
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            action = request.GET.get('action', '').strip()
            response_data = []

            # --- Authors Dropdown ---
            if action == "get_authors":
                language_id_encrypted = request.GET.get('language_id', '').strip()
                if language_id_encrypted:
                    try:
                        language_id = dec(language_id_encrypted)
                        lang_obj = LanguageMaster.objects.filter(id=language_id).first()
                        lang_name = lang_obj.language_name.lower() if lang_obj else ""

                        if lang_name == "marathi":
                            response_data = AuthorMaster.objects.filter(is_active=True) \
                                .exclude(author_name_marathi__isnull=True) \
                                .values_list('author_name_marathi', flat=True) \
                                .distinct().order_by('author_name_marathi')
                        else:
                            response_data = AuthorMaster.objects.filter(is_active=True) \
                                .exclude(author_name_english__isnull=True) \
                                .values_list('author_name_english', flat=True) \
                                .distinct().order_by('author_name_english')
                    except Exception:
                        response_data = []

            # --- Publishers Dropdown ---
            elif action == "get_publishers":
                response_data = BookCatalog.objects.filter(~Q(publisher__exact=""), publisher__isnull=False) \
                    .values_list('publisher', flat=True).distinct().order_by('publisher')

            # --- Publication Places Dropdown ---
            elif action == "get_places":
                response_data = BookCatalog.objects.filter(~Q(publication_place__exact=""), publication_place__isnull=False) \
                    .values_list('publication_place', flat=True).distinct().order_by('publication_place')

            return JsonResponse({"data": list(response_data)})

        # ---------- GET Request ----------
        if request.method == "GET":
            languages = LanguageMaster.objects.filter(is_active=1)
            for lang in languages:
                lang.encrypted_id = enc(str(lang.id))

            subjects = SubjectTypeMaster.objects.filter(is_active=True)
            for sub in subjects:
                sub.encrypted_id = enc(str(sub.id))

            materials = MaterialTypeMaster.objects.filter(is_active=True)
            for mat in materials:
                mat.encrypted_id = enc(str(mat.id))

            # Years dropdown
            from datetime import datetime
            current_year = datetime.now().year
            years = list(range(current_year, 1899, -1))

            selected_language_id_encrypted = request.GET.get('language_id')
            if selected_language_id_encrypted:
                try:
                    selected_language_id = dec(selected_language_id_encrypted)
                    lang_obj = LanguageMaster.objects.filter(id=selected_language_id).first()
                except Exception:
                    lang_obj = languages[0] if languages else None
            else:
                lang_obj = languages[0] if languages else None

            lang_name = lang_obj.language_name.lower() if lang_obj else "english"

            # Author dropdown based on language
            if lang_name == "marathi":
                authors = AuthorMaster.objects.filter(is_active=True) \
                    .values_list('author_name_marathi', flat=True).distinct().order_by('author_name_marathi')
            else:
                authors = AuthorMaster.objects.filter(is_active=True) \
                    .values_list('author_name_english', flat=True).distinct().order_by('author_name_english')

            publishers = BookCatalog.objects.filter(~Q(publisher__exact=""), publisher__isnull=False) \
                .values_list('publisher', flat=True).distinct().order_by('publisher')

            publication_places = BookCatalog.objects.filter(~Q(publication_place__exact=""), publication_place__isnull=False) \
                .values_list('publication_place', flat=True).distinct().order_by('publication_place')

            context = {
                'languages': languages,
                'subjects': subjects,
                'materials': materials,
                'authors': authors,
                'publishers': publishers,
                'publication_places': publication_places,
                'years': years
            }
            return render(request, 'Master/book_catalog_create_isbn.html', context)

        # ---------- POST Request ----------
        if request.method == "POST":
            form_data = {
                "title": request.POST.get('title', '').strip(),
                "subtitle": request.POST.get('subtitle', '').strip(),
                "author": request.POST.get('author', '').strip(),
                "other_authors": request.POST.get('other_authors', '').strip(),
                "publisher": request.POST.get('publisher', '').strip(),
                "isbn": request.POST.get('isbn', '').strip(),
                "edition": request.POST.get('edition', '').strip(),
                "subject_id": dec(request.POST.get('subject_id', '').strip()) if request.POST.get('subject_id', '').strip() else '',
                "material_id": dec(request.POST.get('material_id', '').strip()) if request.POST.get('material_id', '').strip() else '',
                "remarks": request.POST.get('remarks', '').strip(),
                "keywords": request.POST.get('keywords', '').strip(),
                "language_id": dec(request.POST.get('language_id_hidden', '').strip()) if request.POST.get('language_id_hidden', '').strip() else '',
                "publication_place": request.POST.get('publication_place', '').strip(),
                "year_of_publication": request.POST.get('year_of_publication', '').strip(),
                "pages": request.POST.get('page_nos', '').strip(),
            }

            required_fields = ["title", "author", "publisher", "subject_id", "material_id", "language_id"]
            missing = [f for f in required_fields if not form_data[f]]
            if missing:
                messages.error(request, f"Please fill in all required fields: {', '.join(missing)}")
                return redirect('book_catalog_create_isbn')

            try:
                with transaction.atomic():
                    subject = SubjectTypeMaster.objects.filter(id=form_data["subject_id"]).first()
                    material = MaterialTypeMaster.objects.filter(id=form_data["material_id"]).first()
                    language = LanguageMaster.objects.filter(id=form_data["language_id"]).first()

                    author = form_data["author"]
                    other_authors = form_data.get("other_authors", "").strip()

                    # author transliteration logic
                    if contains_non_english(author):
                        authorEnglish = transliterate_to_english(author).lower()
                        authorMarathi = author
                    else:
                        authorEnglish = author.lower()
                        authorMarathi = None

                    if contains_non_english(other_authors):
                        otherAuthorEnglish = transliterate_to_english(other_authors).lower()
                        otherAuthorMarathi = other_authors
                    else:
                        otherAuthorEnglish = other_authors.lower()
                        otherAuthorMarathi = None

                    ClassificationNumber = f"{subject.subjectCode:03}" if subject and subject.subjectCode else "000"
                    author_name_clean = ''.join(filter(str.isalpha, authorEnglish))
                    CutterNumber = author_name_clean[:3].title() if author_name_clean else "XXX"
                    pub_year = form_data['year_of_publication'] or "0000"
                    call_number = f"{ClassificationNumber}.{CutterNumber}.{pub_year}"

                    book = BookCatalog.objects.create(
                        title=form_data["title"],
                        subtitle=form_data["subtitle"],
                        author=form_data["author"],
                        other_authors=other_authors,
                        publisher=form_data["publisher"],
                        isbn_issn=form_data["isbn"],
                        edition=form_data["edition"],
                        subject=subject,
                        call_number=call_number,
                        classification_number=ClassificationNumber,
                        cutter_number=CutterNumber,
                        publication_year=pub_year,
                        material=material,
                        remarks=form_data["remarks"],
                        keywords=form_data["keywords"],
                        language=language.language_name if language else None,
                        publication_place=form_data["publication_place"],
                        year_of_publication=int(pub_year) if pub_year.isdigit() else None,
                        pages=form_data["pages"],
                        date_of_registration=date.today(),
                        status_id=1,
                        created_by=user,
                        updated_by=user
                    )

                    # Save Author
                    existing_author = AuthorMaster.objects.filter(author_name_english=authorEnglish).first()
                    if not existing_author:
                        AuthorMaster.objects.create(
                            author_short_name=CutterNumber,
                            author_name_english=authorEnglish,
                            author_name_other_english=otherAuthorEnglish,
                            author_name_marathi=authorMarathi,
                            author_name_other_marathi=otherAuthorMarathi,
                            created_by=user,
                            updated_by=user
                        )

                    # ---------- UPDATED IMAGE LOGIC USING FileStorageService ----------
                    front_photo = request.FILES.get('front_page_image')
                    last_photo = request.FILES.get('last_page_image')
                    
                    # Get library code from session
                    library_code = request.session.get('library_db', 'default')
                    
                    # Use library_code for folder structure
                    book_folder = f"{library_code}/{book.cat_ref_num}"
                    
                    # Generate unique timestamps for filenames
                    timestamp = dt.now().strftime("%Y%m%dT%H%M%S")
                    
                    # --- Front Page Image ---
                    if front_photo:
                        try:
                            # Extract original filename and extension
                            filename, ext = os.path.splitext(front_photo.name)
                            
                            # Generate unique filename
                            short_uuid = str(uuid.uuid4())[:8]
                            # Remove special characters from filename for safety
                            safe_filename = ''.join(c for c in filename if c.isalnum() or c in (' ', '-', '_')).rstrip()
                            unique_filename = f"{book.cat_ref_num}_front_{safe_filename}_{timestamp}_{short_uuid}{ext}"
                            
                            # Build save path
                            save_path = f"{book_folder}/{unique_filename}"
                            
                            # ✅ USE STORAGE SERVICE TO SAVE FILE
                            saved_file_path = file_storage_service.save_file(front_photo, save_path)
                            
                            # Update book record with saved path
                            book.front_page_photo = saved_file_path
                            
                            print(f"✅ Front page image saved for library {library_code}: {saved_file_path}")
                            
                        except Exception as e:
                            print(f"❌ Error saving front page image: {str(e)}")
                            # Continue without image, don't fail the entire transaction
                            messages.warning(request, f"Front page image could not be saved: {str(e)}")
                    
                    # --- Last Page Image ---
                    if last_photo:
                        try:
                            # Extract original filename and extension
                            filename, ext = os.path.splitext(last_photo.name)
                            
                            # Generate unique filename
                            short_uuid = str(uuid.uuid4())[:8]
                            # Remove special characters from filename for safety
                            safe_filename = ''.join(c for c in filename if c.isalnum() or c in (' ', '-', '_')).rstrip()
                            unique_filename = f"{book.cat_ref_num}_back_{safe_filename}_{timestamp}_{short_uuid}{ext}"
                            
                            # Build save path
                            save_path = f"{book_folder}/{unique_filename}"
                            
                            # ✅ USE STORAGE SERVICE TO SAVE FILE
                            saved_file_path = file_storage_service.save_file(last_photo, save_path)
                            
                            # Update book record with saved path
                            book.last_page_photo = saved_file_path
                            
                            print(f"✅ Last page image saved for library {library_code}: {saved_file_path}")
                            
                        except Exception as e:
                            print(f"❌ Error saving last page image: {str(e)}")
                            # Continue without image, don't fail the entire transaction
                            messages.warning(request, f"Last page image could not be saved: {str(e)}")
                    
                    # Save book with updated image paths
                    book.save()

                messages.success(request, f"Book '{book.title}' saved successfully!")
                return redirect('book_catalog_index')

            except Exception as e:
                messages.error(request, f"Error adding book: {str(e)}")
                return redirect('book_catalog_create_isbn')

    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        fun = tb[0].name
        callproc("stp_error_log", [fun, str(e), user])
        messages.error(request, 'Oops...! Something went wrong!')

def isbn_lookup(request):
    library_code = request.session.get('library_code')
    """Lookup book information by ISBN"""
    if request.method == 'GET':
        isbn = request.GET.get('isbn', '').strip()
        
        if not isbn:
            return JsonResponse({
                'success': False,
                'message': 'ISBN is required'
            })
        
        try:
            # First check if ISBN exists in GoogleBookMaster
            book_master = GoogleBookMaster.objects.using(library_code).filter(
                Q(isbn=isbn)
            ).first()
            
            if not book_master:
                return JsonResponse({
                    'success': False,
                    'message': 'Book not found in database'
                })
            
            # Get all details for this book from GoogleBookDetail
            book_details = GoogleBookDetail.objects.using(library_code).filter(book=book_master)
            
            # Prepare minimal response data
            data = {
                'title': book_master.title or '',
                'authors': [],
                'publishedDate': '',
                'pageCount': '',
                'isbn': isbn
            }
            
            # Collect data from detail table (key-value pairs)
            if book_details.exists():
                # Get all detail records
                for detail in book_details:
                    # Check if this is the right detail record
                    # Published Date
                    if hasattr(detail, 'key') and detail.key == 'items_0_volumeInfo_publishedDate':
                        if hasattr(detail, 'value'):
                            data['publishedDate'] = detail.value
                    
                    # Page Count
                    elif hasattr(detail, 'key') and detail.key == 'items_0_volumeInfo_pageCount':
                        if hasattr(detail, 'value'):
                            data['pageCount'] = detail.value
                    
                    # Authors - collect all authors
                    elif hasattr(detail, 'key') and detail.key.startswith('items_0_volumeInfo_authors_'):
                        if hasattr(detail, 'value') and detail.value:
                            # Extract author index from key like 'items_0_volumeInfo_authors_0'
                            data['authors'].append(detail.value)
            
            print(f"Found data: {data}")
            
            return JsonResponse({
                'success': True,
                'data': data
            })
            
        except Exception as e:
            print(f"Error in isbn_lookup: {str(e)}")
            return JsonResponse({
                'success': False,
                'message': f'Error: {str(e)}'
            })
    
    return JsonResponse({
        'success': False,
        'message': 'Invalid request'
    })

# Competitive Exams
from L01.models import (
    CompetitiveExamMaster, Sections, Subjects, 
    Topics, Chapters
)
from django.core.files.storage import default_storage
from django.db.models import Max, IntegerField
from django.db.models.functions import Cast

@no_direct_access 
@login_required    
def create_competitive_book(request):
    if not request.user.is_authenticated:
        # Clear any session flags
        if '_session_expired' in request.session:
            request.session.pop('_session_expired')
        messages.warning(request, "Your session has expired. Please log in again.")
        return redirect('library_list')
    exams = CompetitiveExamMaster.objects.all().order_by("full_name")

    return render(
        request,
        "L01/UPSC/create_competitive_book.html",
        {"exams": exams}
    )

def get_sections_by_competitive(request):
    competitive_id = request.GET.get("competitive_id")

    if not competitive_id:
        return JsonResponse({"sections": []})

    sections = Sections.objects.filter(
        competitive_id=competitive_id
    ).order_by("section_no")

    return JsonResponse({
        "sections": list(
            sections.values("section_no", "section_name")
        )
    })

def get_subjects_by_section(request):
    competitive_id = request.GET.get("competitive_id")
    section_no = request.GET.get("section_no")

    if not competitive_id or not section_no:
        return JsonResponse({"subjects": []})

    subjects = Subjects.objects.filter(
        competitive_id=competitive_id,
        section_no=section_no
    ).order_by("subject_name")

    return JsonResponse({
        "subjects": list(
            subjects.values("subject_id", "subject_name")
        )
    })

def get_topics_by_competitive(request):
    competitive_id = request.GET.get("competitive_id")
    if not competitive_id:
        return JsonResponse({"topics": []})

    topics = Topics.objects.filter(competitive_id=competitive_id).order_by("topic_name")
    return JsonResponse({
        "topics": list(topics.values("topic_id", "topic_name"))
    })

def save_competitive_book(request):
    if request.method != "POST":
        return redirect("create_competitive_book")

    try:
        with transaction.atomic():
            user = request.user.username

            competitive_id = request.POST.get("competitive_id")
            section_no = request.POST.get("section_no")
            subject_id = request.POST.get("subject_id")

            existing_topic_id = request.POST.get("existing_topic_id")
            new_topic_name = request.POST.get("new_topic_name", "").strip()
            chapter_name_input = request.POST.get("chapter_name", "").strip()
            topic_reference = request.POST.get("topic_reference", "").strip()

            cover_image = request.FILES.get("cover_image")
            chapter_pdf = request.FILES.get("chapter_pdf")

            # ---------- VALIDATION ----------
            if not all([competitive_id, section_no, subject_id, cover_image, chapter_pdf]):
                messages.error(request, "Please fill all required fields")
                return redirect("create_competitive_book")

            # ---------- MASTER DATA ----------
            competitive = CompetitiveExamMaster.objects.get(competitive_id=competitive_id)
            section = Sections.objects.get(section_no=section_no)
            subject = Subjects.objects.get(subject_id=subject_id)
            competitive_code = (competitive.short_form or "UNKNOWN").upper().strip()
            library_code = request.session.get("library_db", "L01")

            # ---------- SELECT OR CREATE TOPIC ----------
            if existing_topic_id:
                topic = Topics.objects.get(topic_id=existing_topic_id)
                chapter_name = chapter_name_input or topic.topic_name
            else:
                if not new_topic_name:
                    messages.error(request, "Please select an existing topic or enter a new topic")
                    return redirect("create_competitive_book")

                topic = Topics.objects.create(
                    competitive_id=competitive,
                    section_no=section,
                    subject_id=subject,
                    topic_name=new_topic_name,
                    topic_reference=topic_reference,
                    created_by=user,
                    updated_by=user
                )
                chapter_name = chapter_name_input or new_topic_name

            # ---------- BASE DIRECTORY ----------
            base_dir = f"{library_code}/CompetitiveBooks/{competitive_code}/{topic.topic_id}"

            # ---------- SAVE COVER IMAGE ----------
            image_ext = os.path.splitext(cover_image.name)[1].lower()
            cover_filename = f"cover_{topic.topic_id}{image_ext}"
            cover_path = f"{base_dir}/book_images/{cover_filename}"
            saved_cover_path = file_storage_service.save_file(cover_image, cover_path)

            topic.topic_image_url = saved_cover_path
            topic.save(update_fields=["topic_image_url"])

            # ---------- CHAPTER NUMBER ----------
            last_no = Chapters.objects.annotate(
                chapter_no_int=Cast("chapter_no", IntegerField())
            ).aggregate(max_no=Max("chapter_no_int"))["max_no"] or 0
            new_no = last_no + 1

            # ---------- SAVE PDF ----------
            pdf_filename = f"chapter_{new_no}.pdf"
            pdf_path = f"{base_dir}/chapters/{pdf_filename}"
            saved_pdf_path = file_storage_service.save_file(chapter_pdf, pdf_path)

            # ---------- CREATE CHAPTER ----------
            Chapters.objects.create(
                chapter_no=str(new_no),
                chapter_name=chapter_name,
                topic_id=topic,
                competitive_id=competitive,
                section_no=section,
                chapter_pdf_url=saved_pdf_path,
                created_by=user,
                updated_by=user
            )

            messages.success(
                request,
                f"Chapter '{chapter_name}' created successfully (Chapter No: {new_no})"
            )
            return redirect("competitive_book_index")

    except Exception as e:
        messages.error(request, str(e))
        return redirect("competitive_book_index")
 
@no_direct_access 
@login_required    
def competitive_book_index(request):
    """
    Index page for Competitive Books (Topics & Chapters)
    """
    if not request.user.is_authenticated:
        # Clear any session flags
        if '_session_expired' in request.session:
            request.session.pop('_session_expired')
        messages.warning(request, "Your session has expired. Please log in again.")
        return redirect('library_list')

    chapters = (
        Chapters.objects
        .select_related(
            "topic_id",
            "competitive_id",
            "section_no",
            "topic_id__subject_id"
        )
        .order_by(
            "competitive_id__full_name",
            "section_no__section_no",
            "topic_id__subject_id__subject_name",
            "topic_id__topic_name",
            "chapter_no"
        )
    )
    for chapter in chapters:
        chapter.enc_chapter_no = enc(str(chapter.chapter_no))

    return render(
        request,
        "L01/Master/competitive_book_index.html",
        {
            "chapters": chapters
        }
    )

@no_direct_access 
@login_required    
def edit_competitive_book(request, enc_chapter_no):
    
    if not request.user.is_authenticated:
        # Clear any session flags
        if '_session_expired' in request.session:
            request.session.pop('_session_expired')
        messages.warning(request, "Your session has expired. Please log in again.")
        return redirect('library_list')
    
    chapter_no = dec(enc_chapter_no)

    chapter = get_object_or_404(Chapters, pk=chapter_no)
    topic = chapter.topic_id
    competitive = chapter.competitive_id
    section = chapter.section_no

    topic_image_url = file_storage_service.get_file_url(topic.topic_image_url)  # Get topic image URL
    chapter_pdf_url = file_storage_service.get_file_url(chapter.chapter_pdf_url)

    if request.method == "POST":
        try:
            with transaction.atomic():

                user = request.user.username

                chapter_name_input = request.POST.get("chapter_name", "").strip()
                topic_reference = request.POST.get("topic_reference", "").strip()

                cover_image = request.FILES.get("cover_image")
                chapter_pdf = request.FILES.get("chapter_pdf")

                # ---------- UPDATE TOPIC ----------
                topic.topic_reference = topic_reference

                # Replace cover image if uploaded
                if cover_image:
                    competitive_code = (competitive.short_form or "UNKNOWN").upper().strip()
                    library_code = request.session.get("library_db", "L01")

                    base_dir = f"{library_code}/CompetitiveBooks/{competitive_code}/{topic.topic_id}"

                    image_ext = os.path.splitext(cover_image.name)[1].lower()
                    cover_filename = f"cover_{topic.topic_id}{image_ext}"
                    cover_path = f"{base_dir}/book_images/{cover_filename}"

                    saved_cover_path = file_storage_service.save_file(
                        cover_image,
                        cover_path
                    )
                    topic.topic_image_url = saved_cover_path

                topic.updated_by = user
                topic.save()

                # ---------- UPDATE CHAPTER ----------
                chapter.chapter_name = (
                    chapter_name_input if chapter_name_input else topic.topic_name
                )

                # Replace PDF if uploaded
                if chapter_pdf:
                    competitive_code = (competitive.short_form or "UNKNOWN").upper().strip()
                    library_code = request.session.get("library_db", "L01")

                    base_dir = f"{library_code}/CompetitiveBooks/{competitive_code}/{topic.topic_id}"

                    pdf_filename = f"chapter_{chapter.chapter_no}.pdf"
                    pdf_path = f"{base_dir}/chapters/{pdf_filename}"

                    saved_pdf_path = file_storage_service.save_file(
                        chapter_pdf,
                        pdf_path
                    )
                    chapter.chapter_pdf_url = saved_pdf_path

                chapter.updated_by = user
                chapter.save()

                messages.success(
                    request,
                    "Competitive book chapter updated successfully"
                )
                return redirect("competitive_book_index")

        except Exception as e:
            messages.error(request, str(e))

    return render(
        request,
        "L01/Master/edit_competitive_book.html",
        {
            "chapter": chapter,
            'topic_image_url': topic_image_url,
            'chapter_pdf_url': chapter_pdf_url,
            "topic": topic,
            "competitive": competitive,
            "section": section,
            "subject": topic.subject_id
        }
    )

from django.db.models import Prefetch

def event_index(request):
    try:
        image_prefetch = Prefetch(
            'images',
            queryset=EventImage.objects.using('default')
        )
        pdf_prefetch = Prefetch(
            'pdfs',
            queryset=EventPDF.objects.using('default')
        )
        events = (
            LibraryEvent.objects.using('default')
            .prefetch_related(image_prefetch, pdf_prefetch)
            .order_by("-created_at")
        )
        for event in events:

            # First image as thumbnail
            first_image = event.images.first()

            if first_image and first_image.image:
                event.thumbnail = file_storage_service.get_file_url(
                    first_image.image
                )
            else:
                event.thumbnail = None

        context = {
            "events": events,
            "title": "Library Events"
        }

        return render(request, "Master/Event_list.html", context)

    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        fun = tb[0].name
        callproc("stp_error_log", [fun, str(e), ''])
        messages.error(request, "Oops...! Something went wrong!")
        return redirect("event_list")

@login_required
def create_event(request):
    if request.method == 'POST':
        # Get form data
        scope = request.POST.get('scope')
        library_id = request.POST.get('library')
        event_name = request.POST.get('event_name')
        description = request.POST.get('description')
        event_type = request.POST.get('event_type')
        date = request.POST.get('date')
        from_date = request.POST.get('from_date')
        to_date = request.POST.get('to_date')
        start_time = request.POST.get('start_time')
        end_time = request.POST.get('end_time')
        location = request.POST.get('location')
        images = request.FILES.getlist('images')
        pdfs = request.FILES.getlist('pdfs')
        # Create event
        try:
            event = LibraryEvent(
                scope=scope,
                library_id=library_id if scope == 'specific' else None,
                event_name=event_name,
                description=description,
                event_type=event_type,
                date=date if event_type == 'single' else None,
                from_date=from_date if event_type == 'multiple' else None,
                to_date=to_date if event_type == 'multiple' else None,
                start_time=start_time,
                end_time=end_time,
                location=location
            )
            event.save()
            
            # Save images
            for image in images:

                filename = image.name
                save_path = f"events/{event.id}/images/{filename}"

                saved_file_path = file_storage_service.save_file(
                    image,
                    save_path
                )

                EventImage.objects.create(
                    event=event,
                    image=saved_file_path
                )
            
            # Save PDFs
            for pdf in pdfs:

                filename = pdf.name
                save_path = f"events/{event.id}/pdfs/{filename}"

                saved_file_path = file_storage_service.save_file(
                    pdf,
                    save_path
                )

                EventPDF.objects.using('default').create(
                    event=event,
                    pdf_file=saved_file_path
                )

            
            messages.success(request, 'Event created successfully!')
            return redirect('event_index')
            
        except Exception as e:
            messages.error(request, f'Error creating event: {str(e)}')
            libraries = LibraryMaster.objects.all()
            context = {
                'libraries': libraries,
                'scope': scope,
                'library_id': library_id,
                'event_name': event_name,
                'description': description,
                'event_type': event_type,
                'date': date,
                'from_date': from_date,
                'to_date': to_date,
                'start_time': start_time,
                'end_time': end_time,
                'location': location,
                'title': 'Create New Event',
                'is_edit': False,
            }
            return render(request, 'Master/Event.html', context)
    
    else:  # GET request
        libraries = LibraryMaster.objects.all()
        context = {
            'libraries': libraries,
            'title': 'Create New Event',
            'is_edit': False,
        }
        return render(request, 'Master/Event.html', context)

@login_required
def edit_event(request, pk):
    event = get_object_or_404(LibraryEvent.objects.using('default'), pk=pk)

    if request.method == 'POST':

        scope = request.POST.get('scope')
        library_id = request.POST.get('library')
        event_name = request.POST.get('event_name')
        description = request.POST.get('description')
        event_type = request.POST.get('event_type')
        date = request.POST.get('date')
        from_date = request.POST.get('from_date')
        to_date = request.POST.get('to_date')
        start_time = request.POST.get('start_time')
        end_time = request.POST.get('end_time')
        location = request.POST.get('location')

        images = request.FILES.getlist('images')
        pdfs = request.FILES.getlist('pdfs')

        delete_images = request.POST.getlist('delete_images')
        delete_pdfs = request.POST.getlist('delete_pdfs')

        try:

            # ================= UPDATE EVENT =================

            event.scope = scope

            if scope == 'specific':
                event.library_id = library_id
            else:
                event.library = None

            event.event_name = event_name
            event.description = description
            event.event_type = event_type

            if event_type == 'single':
                event.date = date
                event.from_date = None
                event.to_date = None

            elif event_type == 'multiple':
                event.date = None
                event.from_date = from_date
                event.to_date = to_date

            event.start_time = start_time
            event.end_time = end_time
            event.location = location

            event.save()

            # ================= DELETE IMAGES =================

            for image_id in delete_images:

                try:
                    event_image = EventImage.objects.get(
                        id=image_id,
                        event=event
                    )

                    if event_image.image:
                        file_storage_service.delete_file(event_image.image)

                    event_image.delete()

                except EventImage.DoesNotExist:
                    pass

            # ================= DELETE PDFS =================

            for pdf_id in delete_pdfs:

                try:
                    event_pdf = EventPDF.objects.get(
                        id=pdf_id,
                        event=event
                    )

                    if event_pdf.pdf_file:
                        file_storage_service.delete_file(event_pdf.pdf_file)

                    event_pdf.delete()

                except EventPDF.DoesNotExist:
                    pass

            # ================= SAVE NEW IMAGES =================

            for image in images:

                filename = image.name
                save_path = f"events/{event.id}/images/{filename}"

                saved_file_path = file_storage_service.save_file(
                    image,
                    save_path
                )

                EventImage.objects.create(
                    event=event,
                    image=saved_file_path
                )

            # ================= SAVE NEW PDFS =================

            for pdf in pdfs:

                filename = pdf.name
                save_path = f"events/{event.id}/pdfs/{filename}"

                saved_file_path = file_storage_service.save_file(
                    pdf,
                    save_path
                )

                EventPDF.objects.using('default').create(
                    event=event,
                    pdf_file=saved_file_path
                )

            messages.success(request, 'Event updated successfully!')
            return redirect('event_index')

        except Exception as e:

            messages.error(request, f'Error updating event: {str(e)}')

            existing_images = event.images.all()
            existing_pdfs = event.pdfs.all()
            libraries = LibraryMaster.objects.using('default').all()

            context = {
                'event': event,
                'libraries': libraries,
                'existing_images': existing_images,
                'existing_pdfs': existing_pdfs,
                'scope': scope,
                'library_id': library_id,
                'event_name': event_name,
                'description': description,
                'event_type': event_type,
                'date': date,
                'from_date': from_date,
                'to_date': to_date,
                'start_time': start_time,
                'end_time': end_time,
                'location': location,
                'title': 'Edit Event',
                'is_edit': True,
            }

            return render(request, 'Master/Event.html', context)
    
    else:  # GET request
        # Get existing files for preview
        event = LibraryEvent.objects.using('default').get(id=event.id)

        # Prefetch images and PDFs using 'default' database
        image_prefetch = Prefetch(
            'images',
            queryset=EventImage.objects.using('default')
        )

        pdf_prefetch = Prefetch(
            'pdfs',
            queryset=EventPDF.objects.using('default')
        )

        # Query libraries
        libraries = LibraryMaster.objects.using('default').all()

        # Prefetch related images and PDFs
        event = LibraryEvent.objects.using('default') \
            .prefetch_related(image_prefetch, pdf_prefetch) \
            .get(id=event.id)

        existing_images = event.images.all()
        existing_pdfs = event.pdfs.all()

        images_with_urls = []
        for img in existing_images:
            images_with_urls.append({
                'id': img.id,
                'image': img.image,  # Path stored in DB
                'url': file_storage_service.get_file_url(img.image) if img.image else None,
                'uploaded_at': img.uploaded_at
            })

        pdfs_with_urls = []
        for pdf in existing_pdfs:
            pdfs_with_urls.append({
                'id': pdf.id,
                'pdf_file': pdf.pdf_file,  # Path stored in DB
                'url': file_storage_service.get_file_url(pdf.pdf_file) if pdf.pdf_file else None,
                'uploaded_at': pdf.uploaded_at,
                'filename': os.path.basename(pdf.pdf_file) if pdf.pdf_file else 'PDF File'
            })

        context = {
            'event': event,
            'libraries': libraries,
            'existing_images': images_with_urls,
            'existing_pdfs': pdfs_with_urls,
            'title': 'Edit Event',
            'is_edit': True,
        }

        return render(request, 'Master/Event.html', context)