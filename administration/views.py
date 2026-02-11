import traceback
from django.shortcuts import render, redirect
from django.contrib import messages
import Db
from administration.models import *
from NLMS.encryption import *
from django.http import JsonResponse
from django.http import HttpResponse
from django.contrib.sessions.models import Session
from services.file_storage_service import file_storage_service
from .thread_local import set_current_service
from django.conf import settings
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Count, Sum, Q, F, Avg
from L01.models import *
from django.db.models import Max, Count, Avg, Exists, OuterRef
import os
from django.http import FileResponse, Http404
from NLMS.access_control import no_direct_access

def library_list(request):
    Db.closeConnection()
    m = Db.get_connection()
    cursor = m.cursor()
    try:
        host = request.get_host().split(':')[0]
        if host.endswith("nmmclibrary.in"):
            subdomain = host.replace(".nmmclibrary.in", "")
            if subdomain == "vdb":
                library_code = "L01"
            else:
                library_code = None
            if library_code:
                request.session['library_db'] = library_code
                request.session.modified = True
                set_current_service(library_code)
                return redirect(f"{library_code}:index")
        # Get ALL active libraries for dropdown (no pagination)
        all_libraries = LibraryMaster.objects.using('default').select_related("location").filter(is_active=1)

        # Add encrypted library code and membership link status to ALL libraries
        for lilo in all_libraries:
            encrypted_library_code = enc(lilo.library_code)
            lilo.libraries = encrypted_library_code
            lilo.main_image = ""
            if lilo.image_url:
                first_image_path = lilo.image_url.split(",")[0].strip()
                if first_image_path:
                    lilo.main_image = file_storage_service.get_file_url(first_image_path)
            has_membership_link = bool(
                lilo.membership_page_link and 
                str(lilo.membership_page_link).strip() != '' and
                str(lilo.membership_page_link).strip() != 'None'
            )
            lilo.has_membership_link = has_membership_link
        
        # Handle AJAX requests for pagination - CHANGE: 6 per page instead of 4
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            page = request.GET.get('page', 1)
            paginator = Paginator(all_libraries, 6)  # CHANGED: 6 per page
            try:
                libraries_page = paginator.page(page)
            except (PageNotAnInteger, EmptyPage):
                libraries_page = paginator.page(1)
            
            libraries_data = []
            for library in libraries_page:
                
                first_image_path = ""
                if library.image_url:
                    first_image_path = library.image_url.split(",")[0].strip()
                first_image_url = file_storage_service.get_file_url(first_image_path)
                has_membership_link = bool(
                    library.membership_page_link and 
                    str(library.membership_page_link).strip() != '' and
                    str(library.membership_page_link).strip() != 'None'
                )
                libraries_data.append({
                    'id': library.id,
                    'library_name': library.library_name,
                    'library_name_mar': library.library_name_mar,
                    'location_name': library.location.location_name if library.location else '',
                    'est_year': library.est_year,
                    'about_library': library.about_library,
                    'image_url': first_image_url,
                    'libraries': library.libraries,  # encrypted code
                    'has_membership_link': has_membership_link
                })
            return JsonResponse({
                'libraries': libraries_data,
                'has_next': libraries_page.has_next(),
                'has_previous': libraries_page.has_previous(),
                'current_page': int(page),
                'total_pages': paginator.num_pages,
                'total_count': paginator.count
            })
        # Regular request
        paginator = Paginator(all_libraries, 6)  # CHANGED: 6 per page
        page = request.GET.get('page', 1)
        
        try:
            library_details = paginator.page(page)
        except (PageNotAnInteger, EmptyPage):
            library_details = paginator.page(1)
        
        # Get first library's membership status for initial display
        initial_has_membership = False
        if all_libraries and len(all_libraries) > 0:
            first_library = all_libraries[0]
            initial_has_membership = bool(
                first_library.membership_page_link and 
                str(first_library.membership_page_link).strip() != '' and
                str(first_library.membership_page_link).strip() != 'None'
            )
        
        return render(request, 'administration/library_list.html', {
            'library_details': library_details,
            'all_libraries': all_libraries,
            'MEDIA_URL': settings.MEDIA_URL,
            'total_pages': paginator.num_pages,
            'total_count': paginator.count,
            'initial_has_membership': initial_has_membership  # Add this
        })
    
    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        fun = tb[0].name if tb else 'library_list'
        cursor.callproc("stp_error_log", [fun, str(e), ''])
        print(f"error: {e}")
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'error': str(e)}, status=500)
        
        messages.error(request, 'Oops...! Something went wrong!')
        return redirect("Meta_Index")

def service_redirect(request):
    Db.closeConnection()
    m = Db.get_connection()
    cursor = m.cursor()
    try:
        # Get the library code from POST
        service_code_decrypted = request.POST.get('library_code')
        if not service_code_decrypted:
            return redirect("library_list")

        service_code = dec(service_code_decrypted)

        # Save to session
        request.session['library_db'] = service_code
        request.session.modified = True  # mark session as changed

        # Update thread-local storage for database routing
        set_current_service(service_code)

        # Redirect based on service code
        if service_code == "L01":
            
            if settings.ENVIRONMENT == 'local':
                return redirect("http://127.0.0.1:8000/L01/index")
            elif settings.ENVIRONMENT == 'test':
                return redirect("http://3.111.76.175/L01/index")
            else:  # production
                return redirect("http://vdb.nmmclibrary.in/L01/index")

        elif service_code == "L02":
            return redirect("L02:index")
        else:
            return redirect("library_list_index")
    except Exception as e:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'error': str(e)}, status=500)
        tb = traceback.extract_tb(e.__traceback__)
        fun = tb[0].name if tb else 'library_list'
        cursor.callproc("stp_error_log", [fun, str(e), ''])
        print(f"error: {e}")
        messages.error(request, 'Oops...! Something went wrong!')
        return redirect("Meta_Index")

def set_library_session_and_login(request):
    Db.closeConnection()
    m = Db.get_connection()
    cursor = m.cursor()
    try:
        if request.method == 'POST':
            library_code = request.POST.get('library_code')
            library_code_decrypted = dec(library_code)

            if library_code_decrypted:
                request.session['library_db'] = library_code_decrypted

                # SIMPLE IF CONDITION
                if library_code_decrypted == 'L01':
                    
                    if settings.ENVIRONMENT == 'local':
                        return redirect("http://127.0.0.1:8000/Login")
                    elif settings.ENVIRONMENT == 'test':
                        return redirect("http://3.111.76.175/Login")
                    else:  # production
                        return redirect("http://vdb.nmmclibrary.in/Login")  

                # default login
                return redirect('Login')

    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        fun = tb[0].name if tb else 'set_library_session_and_login'
        cursor.callproc("stp_error_log", [fun, str(e), ''])
        messages.error(request, 'Oops...! Something went wrong!')
        return redirect("Meta_Index")

    
def library_list_index(request):
    Db.closeConnection()
    m = Db.get_connection()
    cursor = m.cursor()
    try:
        library_code = request.session.get('library_db', None)

        if library_code:
            library_details = LibraryMaster.objects.using('default').filter(
                is_active=1, 
                library_code=library_code
            )
            image_urls = []

            for lilo in library_details:

                image_urls = []

                if lilo.image_url:
                    image_paths = [p.strip() for p in lilo.image_url.split(",") if p.strip()]
                    for path in image_paths:
                        image_urls.append(file_storage_service.get_file_url(path))

                # ✅ attach list to object
                lilo.image_urls = image_urls

                # ✅ first image (for big preview)
                lilo.main_image = image_urls[0] if image_urls else ""

            library = library_details.first()
            library_name = library_details.first().library_name if library_details.exists() else ""
            library_name_mar = library_details.first().library_name_mar if library_details.exists() else ""

        return render(request, "administration/library_list_index.html", {
            'libraries': library_details,
            'library_name': library_name,
            'library_name_mar':library_name_mar,
            'MEDIA_URL': settings.MEDIA_URL
        })
    except Exception as e:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'error': str(e)}, status=500)
        
        tb = traceback.extract_tb(e.__traceback__)
        fun = tb[0].name if tb else 'library_list'
        cursor.callproc("stp_error_log", [fun, str(e), ''])
        print(f"error: {e}")
        messages.error(request, 'Oops...! Something went wrong!')
        return redirect("library_list_index")

@no_direct_access    
def commissioner_message(request):
    Db.closeConnection()
    m = Db.get_connection()
    cursor = m.cursor()
    try:
        context = {
            'page_title': 'Message from Commissioner',
            'page_title_mar': 'आयुक्तांचे संदेश',
            'MEDIA_URL': settings.MEDIA_URL
        }
        return render(request, 'administration/commissioner_message.html', context)
    except Exception as e:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'error': str(e)}, status=500)
        
        tb = traceback.extract_tb(e.__traceback__)
        fun = tb[0].name if tb else 'library_list'
        cursor.callproc("stp_error_log", [fun, str(e), ''])
        print(f"error: {e}")
        messages.error(request, 'Oops...! Something went wrong!')
        return redirect("commissioner_message")

@no_direct_access    
def swd_libraries(request):
    Db.closeConnection()
    m = Db.get_connection()
    cursor = m.cursor()
    try:
        context = {
            'page_title': 'SWD - Library Information',
            'page_title_mar': 'समाज विकास विभाग - ग्रंथालय माहिती',
            'MEDIA_URL': settings.MEDIA_URL
        }
        return render(request, 'administration/swd_libraries.html', context)
    except Exception as e:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'error': str(e)}, status=500)
        
        tb = traceback.extract_tb(e.__traceback__)
        fun = tb[0].name if tb else 'swd_libraries'
        cursor.callproc("stp_error_log", [fun, str(e), ''])
        print(f"error: {e}")
        messages.error(request, 'Oops...! Something went wrong!')
        return redirect("swd_libraries")

@no_direct_access
def vision_mission(request):
    """Display Vision, Mission, Objectives page in both English and Marathi"""
    Db.closeConnection()
    m = Db.get_connection()
    cursor = m.cursor()
    try:
        return render(request, 'administration/vision_mission.html')
    except Exception as e:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'error': str(e)}, status=500)
        
        tb = traceback.extract_tb(e.__traceback__)
        fun = tb[0].name if tb else 'swd_libraries'
        cursor.callproc("stp_error_log", [fun, str(e), ''])
        print(f"error: {e}")
        messages.error(request, 'Oops...! Something went wrong!')
        return redirect("swd_libraries")
    
# Public view - doesn't require login
def public_library_catalogue(request):
    """
    Public-facing book catalog (no login required)
    """
    try:
        # No session checks for public access
        
        # --- SUBJECTS ---
        subjects_qs = SubjectTypeMaster.objects.filter(is_active=1)
        subjects = []
        for s in subjects_qs:
            s.id_enc = enc(str(s.id))  # encoding function
            subjects.append(s)

        first_subject = subjects[0] if subjects else None

        # --- BOOKS BY FIRST SUBJECT ---
        if first_subject:
            books = BookCatalog.objects.filter(subject_id=first_subject.id)\
                           .select_related('subject', 'material', 'ebook')\
                           .order_by('-cat_ref_num')
        else:
            books = BookCatalog.objects.none()
            
        # --- ADD FILE URLs TO BOOKS ---
        for book in books:
            book.bookIdEnc = enc(str(book.cat_ref_num))
            
            # Get book cover image
            if book.front_page_photo:
                book.front_page_url = file_storage_service.get_file_url(book.front_page_photo)
            else:
                book.front_page_url = None
                
            # PUBLIC ACCESS: Don't include ebook links or detailed view links

        # --- PAGINATION ---
        paginator = Paginator(books, 8)
        page_number = request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)

        for b in page_obj:
            b.bookIdEnc = enc(str(b.cat_ref_num))

        # --- UPCOMING / LATEST BOOKS ---
        latest_created_at = BookCatalog.objects.aggregate(latest=Max('created_at'))['latest']
        recent_books = BookCatalog.objects.filter(created_at=latest_created_at) if latest_created_at else BookCatalog.objects.none()

        remaining_count = 10 - recent_books.count()
        fallback_books = BookCatalog.objects.exclude(cat_ref_num__in=recent_books.values_list('cat_ref_num', flat=True))\
                                           .order_by('-cat_ref_num')[:remaining_count] if remaining_count > 0 else BookCatalog.objects.none()

        new_books = list(recent_books) + list(fallback_books)
        for b in new_books:
            b.bookIdEnc = enc(str(b.cat_ref_num))
            
            if b.front_page_photo:
                b.front_page_url = file_storage_service.get_file_url(b.front_page_photo)
            else:
                b.front_page_url = None

        # --- MOST REVIEWED BOOKS ---
        most_reviewed_books = (
            BookCatalog.objects.annotate(
                review_count=Count('cat_ref_id_reviews'),
                avg_rating=Avg('cat_ref_id_reviews__rating')
            )
            .filter(review_count__gt=0)
            .order_by('-avg_rating', '-review_count')[:10]
        )

        for b in most_reviewed_books:
            b.bookIdEnc = enc(str(b.cat_ref_num))
            avg = b.avg_rating or 0
            b.avg_rating = round(avg, 1)
            b.stars = [True if i < round(avg) else False for i in range(5)]
            
            if b.front_page_photo:
                b.front_page_url = file_storage_service.get_file_url(b.front_page_photo)
            else:
                b.front_page_url = None

        # --- NEW ARRIVALS IN CIRCULATION ---
        new_arrivals_qs = BookCatalog.objects.annotate(
            in_circulation=Exists(
                CirculationCopyStatus.objects.filter(bookcatalog_id=OuterRef('cat_ref_num'))
            )
        ).filter(in_circulation=True).order_by('-cat_ref_num')[:10]

        for b in new_arrivals_qs:
            b.bookIdEnc = enc(str(b.cat_ref_num))
            
            if b.front_page_photo:
                b.front_page_url = file_storage_service.get_file_url(b.front_page_photo)
            else:
                b.front_page_url = None

        # --- CONTEXT ---
        context = {
            'subjects': subjects,
            'books': page_obj,
            'paginator': paginator,
            'page_number': int(page_number),
            'first_subject_id_enc': first_subject.id_enc if first_subject else None,
            'MEDIA_URL': settings.MEDIA_URL,
            'new_books': new_books,
            'most_reviewed_books': most_reviewed_books,
            'new_arrivals_qs': new_arrivals_qs,
            'is_public_view': True,  # Flag to identify public view
        }

        return render(request, "administration/public_book_catalogue.html", context)

    except Exception as e:
        print(f"Error in public catalog: {e}")
        return render(request, "administration/public_book_catalogue.html", {})

# Public AJAX endpoint (no login required)
def public_get_books_by_subject(request):
    """
    AJAX endpoint for public book filtering
    """
    try:
        subject_id_enc = request.GET.get('subject_id')
        subject_id = dec(subject_id_enc) if subject_id_enc else None

        search = request.GET.get('search', '').strip()
        searching = request.GET.get('searching', '').strip()
        
        if searching:
            # Global search mode
            all_books = BookCatalog.objects.all().select_related('subject', 'material', 'ebook').order_by('-cat_ref_num')

            if search:
                all_books = all_books.filter(
                    Q(title__icontains=search) |
                    Q(author__icontains=search)
                )
            elif subject_id:
                all_books = all_books.filter(subject_id=subject_id)

        else:
            # Filter by specific subject
            if not subject_id:
                return JsonResponse({'error': 'Subject ID required'}, status=400)
                
            all_books = BookCatalog.objects.filter(subject_id=subject_id)\
                                           .select_related('subject', 'material', 'ebook').order_by('-cat_ref_num')

            if search:
                all_books = all_books.filter(
                    Q(title__icontains=search) |
                    Q(author__icontains=search)
                )

        # Add file URLs (PUBLIC ACCESS: no ebook or detailed links)
        for b in all_books:
            b.bookIdEnc = enc(str(b.cat_ref_num))
            
            if b.front_page_photo:
                b.front_page_url = file_storage_service.get_file_url(b.front_page_photo)
            else:
                b.front_page_url = None
            # NO EBOOK LINKS FOR PUBLIC

        # Pagination
        paginator = Paginator(all_books, 8)
        page_number = request.GET.get('page', 1)
        books_page = paginator.get_page(page_number)

        context = {
            'books': books_page,
            'MEDIA_URL': settings.MEDIA_URL,
            'subject_id_enc': subject_id_enc,
            'is_public_view': True,  # Flag for template
        }
        
        return render(request, "administration/public_book_list_partial.html", context)

    except Exception as e:
        print(f"Error in public AJAX: {e}")
        return JsonResponse({'error': 'Something went wrong'}, status=500)

@no_direct_access
def sop_view(request):
    Db.closeConnection()
    m = Db.get_connection()
    cursor = m.cursor()
    
    try:
        
        role_id = request.session.get("role_id")
        library_code = request.session.get('library_db', None)
        
        # Librarian Staff SOPs
        if library_code and role_id != '3' and role_id is not None:
            
            if not request.user.is_authenticated:
                # Clear any session flags
                if '_session_expired' in request.session:
                    request.session.pop('_session_expired')
                messages.warning(request, "Your session has expired. Please log in again.")
                return redirect('library_list')
        
            sop_files = [
                {
                    'id': 4,
                    'name_en': 'Book Issue/Return SOP for Librarian',
                    'name_mr': 'ग्रंथपालासाठी पुस्तक जारी/परतावा',
                    'filename': 'Book IssueReturn SOP for Librarian.pdf',
                    'description_en': 'Standard operating procedure for book issue and return by librarians',
                    'description_mr': 'ग्रंथपालांद्वारे पुस्तक जारी आणि परताव्यासाठी मानक संचालन प्रक्रिया',
                    'size': '1.1 MB'
                },
                {
                    'id': 5,
                    'name_en': 'Cancellation SOP for Librarian',
                    'name_mr': 'ग्रंथपालासाठी रद्दीकरण',
                    'filename': 'Cancellation SOP for Librarian.pdf',
                    'description_en': 'Standard operating procedure for cancellation by librarians',
                    'description_mr': 'ग्रंथपालांद्वारे रद्दीकरणासाठी मानक संचालन प्रक्रिया',
                    'size': '726 KB'
                },
                {
                    'id': 6,
                    'name_en': 'Registration SOP for Librarian',
                    'name_mr': 'ग्रंथपालासाठी नोंदणी',
                    'filename': 'Registration SOP for Librarian.pdf',
                    'description_en': 'Standard operating procedure for registration by librarians',
                    'description_mr': 'ग्रंथपालांद्वारे नोंदणीसाठी मानक संचालन प्रक्रिया',
                    'size': '986 KB'
                },
                {
                    'id': 7,
                    'name_en': 'Renewal SOP for Librarian',
                    'name_mr': 'ग्रंथपालासाठी नूतनीकरण',
                    'filename': 'Renewal SOP for Librarian.pdf',
                    'description_en': 'Standard operating procedure for renewal by librarians',
                    'description_mr': 'ग्रंथपालांद्वारे नूतनीकरणासाठी मानक संचालन प्रक्रिया',
                    'size': '936 KB'
                }
            ]
        
        # member sops
        elif library_code and role_id == '3' and role_id is not None:
            
            if not request.user.is_authenticated:
                # Clear any session flags
                if '_session_expired' in request.session:
                    request.session.pop('_session_expired')
                messages.warning(request, "Your session has expired. Please log in again.")
                return redirect('library_list')
            
            sop_files = [
                {
                    'id': 1,
                    'name_en': 'Cancellation SOP for Member',
                    'name_mr': 'सदस्यासाठी रद्दीकरण ',
                    'filename': 'Cancellation SOP for Member.pdf',
                    'description_en': 'Standard operating procedure for member cancellation',
                    'description_mr': 'सदस्य रद्दीकरणासाठी मानक संचालन प्रक्रिया',
                    'size': '581 KB'
                },
                {
                    'id': 2,
                    'name_en': 'Registration SOP for Member',
                    'name_mr': 'सदस्यासाठी नोंदणी ',
                    'filename': 'Registration SOP for Member.pdf',
                    'description_en': 'Standard operating procedure for member registration',
                    'description_mr': 'सदस्य नोंदणीसाठी मानक संचालन प्रक्रिया',
                    'size': '1.1 MB'
                },
                {
                    'id': 3,
                    'name_en': 'Renewal SOP for Member',
                    'name_mr': 'सदस्यासाठी नूतनीकरण ',
                    'filename': 'Renewal SOP for Member.pdf',
                    'description_en': 'Standard operating procedure for member renewal',
                    'description_mr': 'सदस्य नूतनीकरणासाठी मानक संचालन प्रक्रिया',
                    'size': '732 KB'
                }
            ]
        
        # to show on landing page
        else:
            sop_files = [
            {
                'id': 1,
                'name_en': 'Cancellation SOP for Member',
                'name_mr': 'सदस्यासाठी रद्दीकरण ',
                'filename': 'Cancellation SOP for Member.pdf',
                'description_en': 'Standard operating procedure for member cancellation',
                'description_mr': 'सदस्य रद्दीकरणासाठी मानक संचालन प्रक्रिया',
                'size': '581 KB'
            },
            {
                'id': 2,
                'name_en': 'Registration SOP for Member',
                'name_mr': 'सदस्यासाठी नोंदणी ',
                'filename': 'Registration SOP for Member.pdf',
                'description_en': 'Standard operating procedure for member registration',
                'description_mr': 'सदस्य नोंदणीसाठी मानक संचालन प्रक्रिया',
                'size': '1.1 MB'
            },
            {
                'id': 3,
                'name_en': 'Renewal SOP for Member',
                'name_mr': 'सदस्यासाठी नूतनीकरण ',
                'filename': 'Renewal SOP for Member.pdf',
                'description_en': 'Standard operating procedure for member renewal',
                'description_mr': 'सदस्य नूतनीकरणासाठी मानक संचालन प्रक्रिया',
                'size': '732 KB'
            },
            {
                'id': 4,
                'name_en': 'Book Issue/Return SOP for Librarian',
                'name_mr': 'ग्रंथपालासाठी पुस्तक जारी/परतावा ',
                'filename': 'Book IssueReturn SOP for Librarian.pdf',
                'description_en': 'Standard operating procedure for book issue and return by librarians',
                'description_mr': 'ग्रंथपालांद्वारे पुस्तक जारी आणि परताव्यासाठी मानक संचालन प्रक्रिया',
                'size': '1.1 MB'
            },
            {
                'id': 5,
                'name_en': 'Cancellation SOP for Librarian',
                'name_mr': 'ग्रंथपालासाठी रद्दीकरण ',
                'filename': 'Cancellation SOP for Librarian.pdf',
                'description_en': 'Standard operating procedure for cancellation by librarians',
                'description_mr': 'ग्रंथपालांद्वारे रद्दीकरणासाठी मानक संचालन प्रक्रिया',
                'size': '726 KB'
            },
            {
                'id': 6,
                'name_en': 'Registration SOP for Librarian',
                'name_mr': 'ग्रंथपालासाठी नोंदणी ',
                'filename': 'Registration SOP for Librarian.pdf',
                'description_en': 'Standard operating procedure for registration by librarians',
                'description_mr': 'ग्रंथपालांद्वारे नोंदणीसाठी मानक संचालन प्रक्रिया',
                'size': '986 KB'
            },
            {
                'id': 7,
                'name_en': 'Renewal SOP for Librarian',
                'name_mr': 'ग्रंथपालासाठी नूतनीकरण ',
                'filename': 'Renewal SOP for Librarian.pdf',
                'description_en': 'Standard operating procedure for renewal by librarians',
                'description_mr': 'ग्रंथपालांद्वारे नूतनीकरणासाठी मानक संचालन प्रक्रिया',
                'size': '936 KB'
            }
        ]
        
        # Optional: Dynamically verify file sizes
        for sop in sop_files:
            sop['enc_filename'] = enc(sop['filename'])
            file_path = os.path.join(settings.BASE_DIR, 'static', 'images', 'PDF', 'Library SOP', sop['filename'])
            if os.path.exists(file_path):
                size_bytes = os.path.getsize(file_path)
                size_kb = size_bytes / 1024
                
                # Format size nicely
                if size_kb < 1024:
                    actual_size = f"{size_kb:.0f} KB"
                else:
                    size_mb = size_kb / 1024
                    actual_size = f"{size_mb:.1f} MB"
                
                # You can compare with hardcoded size if needed
                # print(f"File: {sop['filename']}, Expected: {sop['size']}, Actual: {actual_size}")
                
        context = {
            'sop_files': sop_files,
        }
        
        if library_code and role_id != '3' and role_id is not None:
            return render(request, 'L01/sopLibrarian.html', context)
        elif library_code and role_id == '3' and role_id is not None:
            return render(request, 'L01/sopMember.html', context)
        else:
            return render(request, 'L01/sop.html', context)
        
    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        fun = tb[0].name if tb else 'library_list'
        cursor.callproc("stp_error_log", [fun, str(e), ''])
        print(f"error: {e}")
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'error': str(e)}, status=500)
        
        messages.error(request, 'Oops...! Something went wrong!')
        return redirect("library_list")

def download_sop(request):
    Db.closeConnection()
    m = Db.get_connection()
    cursor = m.cursor()
    
    try:
        
        # Secure the filename
        enc_filename = request.GET.get('enc_filename')
        decrypted_filename = dec(enc_filename)
        filename = os.path.basename(decrypted_filename)
        file_path = os.path.join(settings.BASE_DIR, 'static', 'images', 'PDF', 'Library SOP', filename)
        
        if os.path.exists(file_path):
            
            return FileResponse(
                open(file_path, 'rb'), 
                content_type='application/pdf',
                as_attachment=True,
                filename=filename
            )
        else:
            raise Http404(f"File '{filename}' not found")
            
    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        fun = tb[0].name if tb else 'library_list'
        cursor.callproc("stp_error_log", [fun, str(e), ''])
        print(f"error: {e}")
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'error': str(e)}, status=500)
        
        messages.error(request, 'Oops...! Something went wrong!')
        return redirect("library_list")
    
def event_list(request):
    from django.db.models.functions import Coalesce
    events = (
        LibraryEvent.objects.using('default')
        .filter(library__isnull=True)
        .annotate(
            event_order_date=Coalesce('date', 'from_date')
        )
        .order_by('event_order_date')
        .prefetch_related('images', 'pdfs')
    )

    events_data = []

    for event in events:

        # Images
        images = [
            file_storage_service.get_file_url(img.image)
            for img in event.images.all()
            if img.image
        ]

        # PDFs
        pdfs = [
            {
                "name": pdf.pdf_file.split("/")[-1],
                "url": file_storage_service.get_file_url(pdf.pdf_file)
            }
            for pdf in event.pdfs.all()
            if pdf.pdf_file
        ]

        # Date
        if event.event_type == "single":
            date_text = event.date.strftime("%d %b %Y") if event.date else ""
        else:
            date_text = f"{event.from_date.strftime('%d %b %Y')} - {event.to_date.strftime('%d %b %Y')}"

        events_data.append({
            "id": event.id,
            "name": event.event_name,
            "description": event.description,
            "date": date_text,
            "start_time": event.start_time.strftime("%H:%M") if event.start_time else "",
            "end_time": event.end_time.strftime("%H:%M") if event.end_time else "",
            "location": event.location,
            "images": images,
            "pdfs": pdfs,
        })


    return render(request, "administration/event_list.html", {
        "events": events_data
    })
    