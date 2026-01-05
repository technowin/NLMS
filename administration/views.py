import traceback
from django.shortcuts import render, redirect
from django.contrib import messages
import Db
from administration.models import *
from NLMS.encryption import *
from django.http import JsonResponse
from django.http import HttpResponse
from django.contrib.sessions.models import Session
from .thread_local import set_current_service
from django.conf import settings
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

def library_list(request):
    Db.closeConnection()
    m = Db.get_connection()
    cursor = m.cursor()
    
    try:
        # Get ALL active libraries for dropdown (no pagination)
        all_libraries = LibraryMaster.objects.using('default').select_related("location").filter(is_active=1)
        
        # Add encrypted library code to ALL libraries
        for lilo in all_libraries:
            encrypted_library_code = enc(lilo.library_code)
            lilo.libraries = encrypted_library_code
        
        # Handle AJAX requests for pagination (grid display only)
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            page = request.GET.get('page', 1)
            
            # Create paginator for display grid only
            paginator = Paginator(all_libraries, 4)  # 4 libraries per page for grid
            
            try:
                libraries_page = paginator.page(page)
            except (PageNotAnInteger, EmptyPage):
                libraries_page = paginator.page(1)
            
            # Prepare data for JSON response (grid only)
            libraries_data = []
            for library in libraries_page:
                libraries_data.append({
                    'id': library.id,
                    'library_name': library.library_name,
                    'library_name_mar': library.library_name_mar,
                    'location_name': library.location.location_name if library.location else '',
                    'est_year': library.est_year,
                    'about_library': library.about_library,
                    'image_url': library.image_url,
                    'libraries': library.libraries  # encrypted code
                })
            
            return JsonResponse({
                'libraries': libraries_data,
                'has_next': libraries_page.has_next(),
                'has_previous': libraries_page.has_previous(),
                'current_page': int(page),
                'total_pages': paginator.num_pages,
                'total_count': paginator.count
            })
        
        # Regular request - paginate for grid display
        paginator = Paginator(all_libraries, 4)
        page = request.GET.get('page', 1)
        
        try:
            library_details = paginator.page(page)
        except (PageNotAnInteger, EmptyPage):
            library_details = paginator.page(1)
        
        return render(request, 'administration/library_list.html', {
            'library_details': library_details,  # Paginated for grid display (4 per page)
            'all_libraries': all_libraries,      # ALL libraries for dropdown (no pagination)
            'MEDIA_URL': settings.MEDIA_URL,
            'total_pages': paginator.num_pages,
            'total_count': paginator.count
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
        service_code = dec(service_code_decrypted)

        # Save to session
        request.session['library_db'] = service_code
        request.session.modified = True  # mark session as changed

        # Update thread-local storage for database routing
        set_current_service(service_code)

        # Redirect based on service code
        if service_code == "L01":
            return redirect("L01:index")
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
            if library_code:
                request.session['library_db'] = library_code_decrypted
        return redirect('Login')  # actual login page
    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        fun = tb[0].name if tb else 'library_list'
        cursor.callproc("stp_error_log", [fun, str(e), ''])
        print(f"error: {e}")
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

            library = library_details.first()
            library_name = library_details.first().library_name if library_details.exists() else ""
            # library_name =(library.library_name_mar if library and library.library_name_mar else library.library_name if library else "")
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