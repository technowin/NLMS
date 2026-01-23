# L02/views.py
from django.shortcuts import render
from django.http import HttpResponse
from L02.models import *
from administration.models import *
from django.conf import settings
from NLMS.access_control import no_direct_access
from services.file_storage_service import file_storage_service

@no_direct_access
def index(request):
    # Get the library code from session
    library_code = request.session.get('library_db', None)

    if library_code:
        library_details = LibraryMaster.objects.using('default').filter(is_active=1, library_code=library_code)
        # Get the first library name safely, or default to empty string
        library_name = library_details.first().library_name if library_details.exists() else ""

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
    else:
        library_details = LibraryMaster.objects.using('default').filter(is_active=1)
        library_name = ""  # no specific library selected

    # Pass to template
    return render(request, "L02/index.html", {
        'libraries': library_details,
        'library_name': library_name,
        'MEDIA_URL': settings.MEDIA_URL
    })
