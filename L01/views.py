# L01/views.py
from django.shortcuts import render
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
        aadhar_no = request.GET.get("aadhar_no", "").strip()

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

        return render(request, "L01/registration.html", {
        # return render(request, "L01/registrationTest1.html", {
            'MEDIA_URL': settings.MEDIA_URL,
            'library_details':library_details,
            'membership_options':membership_options,
            'ward_details':ward_details,
            'membership_Master':membership_Master,
        })

    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        fun = tb[0].name if tb else 'library_list'
        cursor.callproc("stp_error_log", [fun, str(e), library_code])
        print(f"error: {e}")
        messages.error(request, 'Oops...! Something went wrong!')
