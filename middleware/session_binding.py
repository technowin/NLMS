import hashlib
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.views.decorators.csrf import csrf_exempt
from Account.views import get_client_ip
from Account.models import SessionActivityLog

class SessionBindingMiddleware:
    """
    Binds a session to a specific browser + IP.
    Protects against session hijacking.
    Works for:
    - Admin users (Django auth)
    - Citizen users (OTP/session-based)
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Skip session binding for unauthenticated users
        if not request.session.get('_ua_hash'):
            return self.get_response(request)
        
        ua = request.META.get('HTTP_USER_AGENT', '')
        ip = get_client_ip(request)

        current_ua_hash = hashlib.sha256(ua.encode()).hexdigest()
        stored_ua_hash = request.session.get('_ua_hash')
        stored_ua = request.session.get('_ua_raw')
        stored_ip = request.session.get('_ip')

        # Check if session binding exists
        if stored_ua_hash:
                
            # 🔐 Admin user
            if request.user.is_authenticated:
                    
                if stored_ua_hash != current_ua_hash or stored_ip != ip:
                    
                    log_session_activity(
                        request,
                        action='mismatch_detected',
                        remarks='UA or IP mismatch – forced logout',
                        current_ua=ua,
                        current_ua_hash=current_ua_hash,
                        current_ip=ip,
                        stored_ua=stored_ua,
                        stored_ua_hash=stored_ua_hash,
                        stored_ip=stored_ip,
                    )
                        
                    logout(request)
                    request.session.flush()
                    return redirect('library_list')  # Redirect to admin login
        
        return self.get_response(request)
    
def log_session_activity(
    request,
    action,
    remarks='',
    current_ua=None,
    current_ua_hash=None,
    current_ip=None,
    stored_ua=None,
    stored_ua_hash=None,
    stored_ip=None
):
    try:
        user_id = None
        user_type = None
        role_id = None
        username = None

        # Get role_id from session (set by both adminLogin and librarianLogin)
        role_id = request.session.get('role_id')
        
        # Get user_id from either Django user or session
        if hasattr(request, 'user') and request.user.is_authenticated:
            user_id = str(request.user.id)
            username = str(request.user.username)
        elif request.session.get('user_id'):
            user_id = str(request.session.get('user_id'))
            username = request.session.get('username', '')

        # Determine user_type based on role_id from session
        if role_id:
            role_id_str = str(role_id)
            if role_id_str == '1':
                user_type = 'admin'
            elif role_id_str == '2':
                user_type = 'librarian'
            elif role_id_str == '3':
                user_type = 'member'
            elif role_id_str == '4':
                user_type = 'kiosk_user'
            else:
                user_type = 'unknown'
        else:
            # If no role_id in session, check other indicators
            if request.session.get('is_admin'):
                user_type = 'admin'
            elif request.session.get('is_librarian'):
                user_type = 'librarian'
            elif hasattr(request, 'user') and request.user.is_authenticated:
                # Default authenticated user to admin
                user_type = 'admin'
            else:
                user_type = 'citizen'

        # ✅ FORCE DEFAULT DB
        SessionActivityLog.objects.using('default').create(
            user_id=user_id,
            user_type=user_type,
            role_id=role_id,
            username=username,

            ip_address=current_ip,
            stored_ip_address=stored_ip,

            user_agent=current_ua,
            stored_user_agent=stored_ua,

            user_agent_hash=current_ua_hash,
            stored_user_agent_hash=stored_ua_hash,

            action=action,
            remarks=remarks
        )

    except Exception as e:
        import logging
        logging.getLogger('session_debug').error(
            f"SessionActivityLog failed: {e}",
            exc_info=True
        )

# from django.contrib.auth import logout
# from django.shortcuts import redirect
# from django.contrib import messages
# import hashlib

# class SessionBindingMiddleware:
#     def __init__(self, get_response):
#         self.get_response = get_response

#     def __call__(self, request):
#         if request.user.is_authenticated:
#             ua = request.META.get('HTTP_USER_AGENT', '')
#             ip = request.META.get('REMOTE_ADDR', '')

#             current_ua = hashlib.sha256(ua.encode()).hexdigest()
#             stored_ua = request.session.get('_ua_hash')
#             stored_ip = request.session.get('_ip')  

#             # If session is hijacked / used from different device
#             if stored_ua != current_ua or stored_ip != ip:
#                 # Log out user and flush session
#                 logout(request)
#                 request.session.flush()

#                 # Add a message so user knows what happened
#                 messages.warning(
#                     request,
#                     "We detected a change in your login environment. For your security, you’ve been logged out."
#                 )
#                 return redirect('citizenLoginAccount')

#         return self.get_response(request)
