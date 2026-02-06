from django.shortcuts import redirect
from django.urls import reverse, NoReverseMatch
from django.contrib.auth import logout

class AuthFlowGuardMiddleware:
    """
    Prevent authenticated users from accessing login pages using back/forward navigation
    Handles Admin, Librarian, AND Member logins with proper dashboard URLs
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        path = request.path
        
        # Get ALL session flags for different user types
        admin_flow_done = request.session.get('admin_flow_completed', False)
        member_flow_done = request.session.get('member_flow_completed', False)
        is_admin = request.session.get('is_admin', False)
        is_librarian = request.session.get('is_librarian', False)
        library_code = request.session.get('library_db')
        role_id = request.session.get('role_id')
        
        # URLs for different login pages
        librarian_login_url = reverse('librarianLogin')
        admin_login_url = reverse('adminLogin')
        member_login_url = reverse('Login')  # Member login
        
        # 🔴 1. CHECK IF USER IS ACCESSING LOGIN PAGE AFTER AUTH (BACK BUTTON)
        
        # If admin and accessing admin login
        if is_admin and path.startswith(admin_login_url):
            if hasattr(request, 'user') and request.user.is_authenticated:
                logout(request)
            request.session.flush()
            return redirect(f'{admin_login_url}?expired=1')
        
        # If librarian flow done and accessing librarian login
        if admin_flow_done and path.startswith(librarian_login_url):
            if hasattr(request, 'user') and request.user.is_authenticated:
                logout(request)
            request.session.flush()
            return redirect(f'{librarian_login_url}?expired=1')
        
        # If member flow done and accessing member login
        if member_flow_done and path.startswith(member_login_url):
            if hasattr(request, 'user') and request.user.is_authenticated:
                logout(request)
            request.session.flush()
            return redirect(f'{member_login_url}?expired=1')
        
        # 🔴 2. PROTECT DASHBOARDS FROM UNAUTHORIZED ACCESS
        
        # 2A. PROTECT LIBRARIAN DASHBOARDS (L01:dashboard, L02:dashboard, etc.)
        if library_code and library_code not in [None, 'default']:
            try:
                librarian_dashboard_url = reverse(f'{library_code}:dashboard')
                # Check if accessing librarian dashboard without flow flag
                if path.startswith(librarian_dashboard_url) and not admin_flow_done:
                    if hasattr(request, 'user') and request.user.is_authenticated:
                        logout(request)
                    request.session.flush()
                    return redirect(librarian_login_url)
            except NoReverseMatch:
                pass
        
        # 2B. PROTECT ADMIN DASHBOARD (LMS_Dashboard)
        try:
            admin_dashboard_url = reverse('LMS_Dashboard')
            # Check if accessing admin dashboard without is_admin flag
            if path.startswith(admin_dashboard_url) and not is_admin:
                if hasattr(request, 'user') and request.user.is_authenticated:
                    logout(request)
                request.session.flush()
                return redirect(admin_login_url)
        except NoReverseMatch:
            pass
        
        # 2C. PROTECT MEMBER DASHBOARDS (L01:membership_dashboard, etc.)
        if library_code and library_code not in [None, 'default']:
            try:
                member_dashboard_url = reverse(f'{library_code}:membership_dashboard')
                # Check if accessing member dashboard without flow flag
                if path.startswith(member_dashboard_url) and not member_flow_done:
                    if hasattr(request, 'user') and request.user.is_authenticated:
                        logout(request)
                    request.session.flush()
                    return redirect(member_login_url)
            except NoReverseMatch:
                pass
        
        return self.get_response(request)
    
# from django.shortcuts import redirect
# from django.urls import reverse, NoReverseMatch
# from django.contrib.auth import logout

# class AuthFlowGuardMiddleware:
#     """
#     Prevent authenticated users from accessing login page using back/forward navigation
#     """
    
#     def __init__(self, get_response):
#         self.get_response = get_response
    
#     def __call__(self, request):
#         path = request.path
        
#         # Get session flags
#         admin_flow_done = request.session.get('admin_flow_completed', False)
#         library_code = request.session.get('library_db')
        
#         # URLs
#         login_url = reverse('librarianLogin')
        
#         # 🔴 FIX: Safely get dashboard URL
#         dashboard_url = None
#         if library_code and library_code not in [None, 'default']:
#             try:
#                 dashboard_url = reverse(f'{library_code}:dashboard')
#             except NoReverseMatch:
#                 dashboard_url = None
        
#         # 🔴 EXACT SAME LOGIC AS YOUR OTP PROJECT:
#         # If admin flow is completed AND user accesses login page
#         if admin_flow_done and path.startswith(login_url):
#             # User is coming back to login via back button
#             if hasattr(request, 'user') and request.user.is_authenticated:
#                 logout(request)
#             request.session.flush()
            
#             return redirect(f'{login_url}?expired=1')
        
#         # 🔴 Prevent accessing dashboard without proper login flow
#         # Only check if we have a valid dashboard_url
#         if dashboard_url and path.startswith(dashboard_url) and not admin_flow_done:
#             if hasattr(request, 'user') and request.user.is_authenticated:
#                 logout(request)
#             request.session.flush()
#             return redirect(login_url)
        
#         return self.get_response(request)