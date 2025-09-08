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


@login_required
def material_type_master_index(request):
    try:
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

        

@login_required
def material_type_create(request):
    try:
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



@login_required
def materialtype_view(request):
    try:
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



@login_required
def materialtype_edit(request):
    try:
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




@login_required
def subject_type_master_index(request):
    try:
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


@login_required
def subject_type_create(request):
    try:
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
    
    
@login_required
def subject_type_view(request):
    try:
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




@login_required
def subject_edit(request):
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


@login_required
def language_master_index(request):
    try:
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


@login_required
def language_create(request):
    try:
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

@login_required
def language_edit(request):
    language = None

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

@login_required
def language_view(request):
    try:
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


@login_required
def supplier_master_index(request):
    try:
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

@login_required
def supplier_create(request):
    try:
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

@login_required
def supplier_view(request):
    try:
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


@login_required
def supplier_edit(request):
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


@login_required
def fundingsource_master_index(request):
    try:
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


@login_required
def fundingsource_create(request):
    try:
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


@login_required
def fundingsource_edit(request):
    funding = None

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

@login_required
def fundingsource_view(request):
    try:
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
