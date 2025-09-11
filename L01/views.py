# L01/views.py
from django.shortcuts import render
from django.http import HttpResponse
from L01.models import *


def index(request):
    # Get the library code from session
    library_code = request.session.get('library_db', None)

    if library_code:
        library_details = LibraryMaster.objects.using('default').filter(is_active=1, library_code=library_code)
        # Get the first library name safely, or default to empty string
        library_name = library_details.first().library_name if library_details.exists() else ""
    else:
        library_details = LibraryMaster.objects.using('default').filter(is_active=1)
        library_name = ""  # no specific library selected

    # Pass to template
    return render(request, "L01/index.html", {
        'libraries': library_details,
        'library_name': library_name
    })

