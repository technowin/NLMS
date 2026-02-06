class NoCacheMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        
        # Check for ADMIN authentication (Django auth)
        is_admin_authenticated = hasattr(request, 'user') and request.user.is_authenticated
        
        # ✅ Check if admin flow is completed (your flag)
        admin_flow_done = request.session.get('admin_flow_completed', False)
        
        # Apply no-cache headers if authenticated OR flow is completed
        if is_admin_authenticated or admin_flow_done:
            response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0, post-check=0, pre-check=0'
            response['Pragma'] = 'no-cache'
            response['Expires'] = 'Mon, 01 Jan 1990 00:00:00 GMT'
            response['Vary'] = '*'
        
        # Also prevent caching for ALL auth-related pages
        auth_paths = [
            '/librarian-login/',  # Librarian login
            '/logout/',
            '/login/',
            '/admin/',
            '/L01/',  # All L01 app paths
        ]
        
        # Check if path starts with any auth path
        path_matches = any(request.path.startswith(path) for path in auth_paths)
        
        if path_matches:
            response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'
            
        # ✅ EXTRA: Also add cache headers for POST requests
        if request.method == 'POST':
            response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'
        
        return response