# Context Proessor 477

from django.conf import settings
from Account.models import *
from L01.models import *
from administration.models import *
from NLMS.encryption import dec
import Db
from .db_utils import callproc
from django.utils import timezone
from administration.thread_local import get_current_service  # ✅ import from your other app
from datetime import date

def logged_in_user(request):
    try:
        # =========================
        # DEFAULTS
        # =========================
        membership_active = False
        user = ''
        reports = ''
        menu_items = []

        session_cookie_age_seconds = settings.AUTO_LOGOUT['IDLE_TIME']
        session_timeout_minutes = session_cookie_age_seconds

        username = request.session.get('username', '')
        full_name = request.session.get('full_name', '')
        user_id = request.session.get('user_id', '')
        role_id = request.session.get('role_id', '')
        library_code = request.session.get('library_db', None)

        role_name = ''
        file_path = None  # Changed from static path to None
        library_name_show = None
        library_details = None
        membershipshow = None
        membership_page_link = None
        profile_picture_url = None  # Initialize as None
        
        if library_code != 'default':
            library_details = tbl_librarymasterL01.objects.using(library_code).filter(library_code=library_code).first()
        if library_details:
            membership_page_link = library_details.membership_page_link

        if request.user.is_authenticated:
            user = str(request.user.id or '')

        # =========================
        # LOAD MENU & ROLE
        # =========================
        if user_id and role_id:
            current_db = get_current_service() or 'default'

            if library_code == 'default':
                library_code = None

            if library_code:
                library_details = tbl_librarymasterL01.objects.filter(
                    library_code=library_code
                ).first()

            if library_details:
                library_name_show = library_details.library_name_mar

            role_obj = roles.objects.using(current_db).get(id=role_id)
            role_name = role_obj.role_name

            menu_data = callproc(
                "stp_get_side_navbar_details",
                [user_id, role_id]
            )

            items = []
            for row in menu_data:
                items.append({
                    'id': row[1],
                    'name': row[2],
                    'action': row[3],
                    'is_parent': row[4],
                    'parent_id': row[5],
                    'is_sub_menu': row[6],
                    'sub_menu': row[7],
                    'is_sub_menu2': row[8],
                    'sub_menu2': row[9],
                    'menu_icon': row[10],
                    'badge': row[11] if len(row) > 11 else None
                })

            # Build menu hierarchy
            for item in items:
                item['children'] = [
                    i for i in items if i['parent_id'] == item['id']
                ]

            menu_items = [
                item for item in items if item['parent_id'] == -1
            ]

        # =========================
        # MEMBER ROLE LOGIC
        # =========================
        if role_id == '3':  # Member
            try:
                user_obj = CustomUser.objects.get(id=user_id)
                username = user_obj.username
            except CustomUser.DoesNotExist:
                username = None

            if username:
                membershipshow = (
                    MembershipDetails.objects
                    .select_related('status', 'membership')
                    .filter(user_id=username)
                    .first()
                )

                if membershipshow:
                    # Profile picture - using FileStorageService
                    try:
                        document = DocumentDetails.objects.get(
                            membership_id=membershipshow.id,
                            document_id=1
                        )
                        file_path = document.file_path
                        
                        # ✅ Use FileStorageService to get the URL
                        if file_path:
                            # Import FileStorageService here to avoid circular imports
                            from services.file_storage_service import file_storage_service
                            profile_picture_url = file_storage_service.get_file_url(file_path)
                        else:
                            profile_picture_url = None
                            
                    except DocumentDetails.DoesNotExist:
                        profile_picture_url = None
                    except Exception as e:
                        print(f"Error getting profile picture URL: {e}")
                        profile_picture_url = None

                    # =========================
                    # ACCESS RULES
                    # =========================
                    today = date.today()

                    FULL_MENU_ACCESS_STATUSES = {
                        "PAY_SUCCESS",
                    }

                    LIFETIME_MEMBERSHIP_IDS = {
                        5, 6,   # lifetime memberships
                    }

                    has_valid_status = (
                        membershipshow.status
                        and membershipshow.status.status_code in FULL_MENU_ACCESS_STATUSES
                    )

                    is_lifetime = (
                        membershipshow.membership
                        and membershipshow.membership.id in LIFETIME_MEMBERSHIP_IDS
                    )

                    has_valid_dates = (
                        membershipshow.from_date
                        and membershipshow.to_date
                        and membershipshow.from_date <= today <= membershipshow.to_date
                    )

                    if has_valid_status and (is_lifetime or has_valid_dates):
                        membership_active = True
                    else:
                        # Restrict menu → only Membership Payment
                        menu_items = [
                            item for item in menu_items
                            if item['name'] == "सदस्यत्व देयक"
                        ]
                        membership_active = False

        # =========================
        # FALLBACK FOR PROFILE PICTURE
        # =========================
        if not profile_picture_url:
            # Use static default image
            from django.templatetags.static import static
            profile_picture_url = static('img/user.png')

        # =========================
        # CONTEXT RETURN
        # =========================
        return {
            'role_id': role_id,
            'username': username,
            'full_name': full_name,
            'role_name': role_name,
            'session_timeout_minutes': session_timeout_minutes,
            'reports': reports,
            'menu_items': menu_items,
            'profile_picture_url': profile_picture_url,  # ✅ Now uses FileStorageService
            'membershipshow': membershipshow,
            'library_name_show': library_name_show,
            'membership_active': membership_active,
            'membership_page_link':membership_page_link
        }

    except Exception as e:
        print(f"Error in context processor: {e}")
        import traceback
        traceback.print_exc()
        # Return safe defaults on error
        from django.templatetags.static import static
        return {
            'role_id': '',
            'username': '',
            'full_name': '',
            'role_name': '',
            'session_timeout_minutes': 30,
            'reports': '',
            'menu_items': [],
            'profile_picture_url': static('img/user.png'),
            'membershipshow': None,
            'library_name_show': None,
            'membership_active': False,
        }

# def logged_in_user(request):
#     user = ''
#     session_cookie_age_seconds = settings.AUTO_LOGOUT['IDLE_TIME']
#     session_timeout_minutes = session_cookie_age_seconds 
#     username = request.session.get('username', '')
#     full_name = request.session.get('full_name', '')
#     user_id = request.session.get('user_id', '')
#     role_id = request.session.get('role_id', '')
#     library_code = request.session.get('library_db', None) 
#     role_name = ''
#     if request.user.is_authenticated:
#         user = str(request.user.id or '')
    
#     reports = ''    
#     menu_items = []
    
#     # Initialize file path variable
#     file_path = '/static/images/user.png'  # Default fallback
#     library_name_show = None
#     library_details = None
#     if user_id != '' and role_id != '':
        
#         current_db = get_current_service() or 'default'
#         # library_name_show = 'none'  # default fallback

#         library_code = request.session.get('library_db', None)
#         if library_code == 'default':
#             library_code = None
        
#         if library_code: 
#             library_details = tbl_librarymasterL01.objects.filter(library_code=library_code).first()

#         if library_details:
#             library_name_show = library_details.library_name_mar
        
#         role_obj = roles.objects.using(current_db).get(id=role_id)
#         role_name = role_obj.role_name
#         menu_items = []
#         menu_data = callproc("stp_get_side_navbar_details", [user_id, role_id])
#         items = []
#         for row in menu_data:
#             item = {
#                 'id': row[1],
#                 'name': row[2],
#                 'action': row[3],
#                 'is_parent': row[4],
#                 'parent_id': row[5],
#                 'is_sub_menu': row[6],
#                 'sub_menu': row[7],
#                 'is_sub_menu2': row[8],
#                 'sub_menu2': row[9],
#                 'menu_icon': row[10],
#                 'badge': row[11] if len(row) > 11 else None  # Optional badge/count
#             }
#             items.append(item)

#         # Build hierarchy
#         for item in items:
#             item['children'] = [i for i in items if i['parent_id'] == item['id']]
    
#         # Get top level items (parent_id = -1 or your specific root indicator)
#         menu_items = [item for item in items if item['parent_id'] == -1]
        
#     membershipshow = None
    
#     # Step 1: Get the CustomUser model based on user_id
#     if role_id == '3':
#         try:
#             user_obj = CustomUser.objects.get(id=user_id)
#             username = user_obj.username  # Retrieve the username of the user
#         except CustomUser.DoesNotExist:
#             username = None

#         # Step 2: Find the MembershipDetails entry where user_id = username
#         if username:
#             try:
#                 membershipshow = MembershipDetails.objects.get(user_id=username)
                
#             except MembershipDetails.DoesNotExist:
#                 membershipshow = None

#             # Step 3: Find the DocumentDetails where membership_id = membership.id and document_id = 1
#             if membershipshow:
#                 try:
#                     document = DocumentDetails.objects.get(membership_id=membershipshow.id, document_id=1)
#                     file_path = document.file_path  # Retrieve the file path from DocumentDetails
                    
#                     today = date.today()

#                     # If membership exists, check validity
#                     if membershipshow:
#                         if membershipshow.from_date and membershipshow.to_date:
#                             if not (membershipshow.from_date <= today <= membershipshow.to_date):
#                                 # Membership expired or not active today
#                                 menu_items = []  # Hide all menu items
                                
#                 except DocumentDetails.DoesNotExist:
#                     file_path = '/static/images/user.png'  # Fallback in case the document is not found

#     # Return context with the file_path for image
#     return {
#         'role_id':role_id,
#         'username': username,
#         'full_name': full_name,
#         'role_name': role_name,
#         'session_timeout_minutes': session_timeout_minutes,
#         'reports': reports,
#         'menu_items': menu_items,
#         'profile_picture_url': settings.MEDIA_URL + file_path,  # Construct the full image path
#         'membershipshow': membershipshow, 
#         'library_name_show': library_name_show, 
#     }
    