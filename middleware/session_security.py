from django.shortcuts import redirect
from django.contrib import messages
from django.urls import reverse

class SessionExpiryRedirectMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        
        skip_paths = [
            '/librarian-login/',
            '/logout/',
            '/Login/',
            '/library_list/',
            '/library_list_login/',
        ]
        
        # ✅ CRITICAL: Skip ALL AJAX requests (your book report uses these)
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return self.get_response(request)
        
        # ✅ Skip your book report API endpoints
        if request.path.startswith('/books/') or request.path.startswith('/api/'):
            return self.get_response(request)
        
        if request.path in skip_paths:
            return self.get_response(request)
        
        response = self.get_response(request)
        
        # ✅ Only redirect for regular page loads (not AJAX)
        if (
            hasattr(request, 'user')
            and not request.user.is_authenticated
            and request.session.get('_session_expired', False)
            and not request.session.get('_user_logged_out', False)
            and not request.headers.get('x-requested-with') == 'XMLHttpRequest'
        ):
            request.session.pop('_session_expired', None)
            
            messages.warning(
                request,
                "Your session has expired. Please log in again."
            )
            
            response = redirect('library_list')
            response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'
            return response
        
        return response