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

def library_list(request):
    Db.closeConnection()
    m = Db.get_connection()
    cursor = m.cursor()
    
    try:
        # ✅ bring location in same query
        library_details = LibraryMaster.objects.using('default').select_related("location").filter(is_active=1)

        for lilo in library_details:
            encrypted_library_code = enc(lilo.library_code)
            lilo.libraries = encrypted_library_code
        
        return render(request, 'administration/library_list.html', {
            'library_details': library_details,
            'MEDIA_URL': settings.MEDIA_URL
        })
    
    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        fun = tb[0].name if tb else 'library_list'
        cursor.callproc("stp_error_log", [fun, str(e), ''])
        print(f"error: {e}")
        messages.error(request, 'Oops...! Something went wrong!')
        return redirect("library_list")
    
def service_redirect(request):
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
        return redirect("default:library_list")
