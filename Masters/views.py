import json
import pydoc
import re
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render,redirect,get_object_or_404
from django.contrib.auth import authenticate, login ,logout,get_user_model
from Account.forms import RegistrationForm
from Account.models import *
from Masters.models import *
import Db 
import bcrypt
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
         
@login_required
def LMS_Dashboard(request):
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
             return render(request,'Workflow/index.html')
         
# Book Catalog Index     
@login_required
def book_catalog_index(request):
    try:
        user = request.user.id
        role_id = request.user.role_id

        # Fetch catalogs with related subject, material, status
        catalogs = BookCatalog.objects.select_related("subject", "material").all().order_by("-cat_ref_num")

        for c in catalogs:
            c.status_obj = status_master.objects.filter(pk=c.status_id).first()
            c.encrypted_id = enc(str(c.cat_ref_num))

        return render(request, 'Master/book_catalog_index.html', {"catalogs": catalogs})

    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        fun = tb[0].name
        callproc("stp_error_log", [fun, str(e), user])
        messages.error(request, 'Oops...! Something went wrong!')
        # Always return HttpResponse, even on error
        return render(request, 'Master/book_catalog_index.html', {"catalogs": []})

# Book Catalog Create
@login_required
def book_catalog_create(request):
    try:
        user = request.user.id
        if request.method == "GET":

            # Fetch active languages
            languages = LanguageMaster.objects.filter(is_active=1)
            
            # Encrypt IDs
            for lang in languages:
                lang.encrypted_id = enc(str(lang.id))
                
            # Fetch active subjects
            subjects = SubjectTypeMaster.objects.filter(is_active=True)
            for sub in subjects:
                sub.encrypted_id = enc(str(sub.id))
                
            materials = MaterialTypeMaster.objects.filter(is_active=True)
            for mat in materials:
                mat.encrypted_id = enc(str(mat.id))
                
            context = {
                'languages': languages,
                'subjects': subjects,
                'materials': materials
            }
            
            return render(request, 'Master/book_catalog_create.html', context)

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
                "place_of_publication": request.POST.get('place_of_publication', '').strip(),
                "year_of_publication": request.POST.get('year_of_publication', '').strip(),
                "pages": request.POST.get('page_nos', '').strip(),
            }

            # Required fields check
            required_fields = ["title", "author", "publisher", "subject_id", "material_id", "language_id"]
            missing = [f for f in required_fields if not form_data[f]]
            if missing:
                messages.error(request, f"Please fill in all required fields: {', '.join(missing)}")
                return redirect('book_catalog_create')

            try:
                with transaction.atomic():  # Atomic transaction for both tables

                    # Resolve FKs
                    subject = SubjectTypeMaster.objects.filter(id=form_data["subject_id"]).first()
                    material = MaterialTypeMaster.objects.filter(id=form_data["material_id"]).first()
                    material = MaterialTypeMaster.objects.filter(id=form_data["material_id"]).first()
                    language = LanguageMaster.objects.filter(id=form_data["language_id"]).first()

                    # Handle author transliteration if Devanagari
                    author = form_data["author"]
                    other_authors = form_data.get("other_authors", "").strip()

                    if contains_non_english(author):
                        authorEnglish = transliterate_to_english(author).lower()  # convert to lowercase
                        authorMarathi = author
                    else:
                        authorEnglish = author.lower()  # also lowercase English input
                        authorMarathi = None

                    if contains_non_english(other_authors):
                        otherAuthorEnglish = transliterate_to_english(other_authors).lower()
                        otherAuthorMarathi = other_authors
                    else:
                        otherAuthorEnglish = other_authors.lower()
                        otherAuthorMarathi = None

                    # Classification number (3-digit subjectCode)
                    ClassificationNumber = f"{subject.subjectCode:03}" if subject and subject.subjectCode else "000"

                    # Cutter number (first 3 letters of author English name)
                    author_name_clean = ''.join(filter(str.isalpha, authorEnglish))
                    CutterNumber = author_name_clean[:3].title() if author_name_clean else "XXX"

                    # Call number
                    pub_year = form_data['year_of_publication'] or "0000"
                    call_number = f"{ClassificationNumber}.{CutterNumber}.{pub_year}"

                    # --- Save BookCatalog ---
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
                        publication_place=form_data["place_of_publication"],
                        year_of_publication=int(pub_year) if pub_year.isdigit() else None,
                        pages=form_data["pages"],
                        date_of_registration=date.today(),
                        status_id=1,
                        created_by=user,
                        updated_by=user
                    )

                    # --- Save AuthorMaster ---
                    AuthorMaster.objects.create(
                        author_short_name=CutterNumber,
                        author_name_english=authorEnglish,
                        author_name_other_english=otherAuthorEnglish,
                        author_name_marathi=authorMarathi,
                        author_name_other_marathi=otherAuthorMarathi,
                        created_by=user,
                        updated_by=user
                    )

                messages.success(request, f"Book '{book.title}' and author saved successfully!")
                return redirect('book_catalog_index')

            except Exception as e:
                messages.error(request, f"Error adding book and author: {str(e)}")
                return redirect('book_catalog_create')

            
    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        fun = tb[0].name
        callproc("stp_error_log", [fun, str(e), user])
        messages.error(request, 'Oops...! Something went wrong!')

# Book Accession Index     
@login_required
def book_accession_index(request):
    try:
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
@login_required
def book_accession_create(request):
    try:
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
            # Get form data
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
            location_id = dec(request.POST.get("location_id"))
            status_id = dec(request.POST.get("status_id"))
            remarks = request.POST.get("remarks") or None

            # Find last copy number for this catalogue
            last_copy = BookAccession.objects.filter(catalogue_id=catalogue_id).aggregate(max_copy=models.Max('copy_number'))['max_copy'] or 0

            # Insert multiple rows starting from last_copy + 1
            for i in range(1, copy_number + 1):
                BookAccession.objects.create(
                    catalogue_id=catalogue_id,
                    copy_number=last_copy + i,
                    acquisition_date=acquisition_date,
                    supplier_id=supplier_id,
                    invoice_number=invoice_number,
                    invoice_date=invoice_date,
                    price=price,
                    currency_id=currency_id,
                    funding_source_id=funding_source_id,
                    condition_at_entry_id=condition_id,
                    location_id=location_id,
                    status_id=status_id,
                    remarks=remarks,
                    created_by=user
                )

            messages.success(request, f"{copy_number} new copy(ies) of the book have been successfully added, starting from copy number {last_copy + 1}.")
            return redirect('book_accession_index')
        
    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        fun = tb[0].name
        callproc("stp_error_log", [fun, str(e), user])
        messages.error(request, 'Oops...! Something went wrong!')

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
