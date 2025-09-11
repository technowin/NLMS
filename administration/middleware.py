# yourapp/middleware.py
from django.utils.deprecation import MiddlewareMixin
from .thread_local import set_current_service

class LibraryDatabaseMiddleware(MiddlewareMixin):
    """
    Middleware to set the database for the current request based on the session's library_db.
    If no session exists, it will set 'nlms_db' as the default.
    """
    def process_request(self, request):
        # If the 'library_db' is not in the session, set it to 'default' (i.e., 'nlms_db')
        if 'library_db' not in request.session:
            request.session['library_db'] = 'default'
            request.session.modified = True  # Save the session
            
        # Set the current service (i.e., which database to use) in thread-local storage
        library_db = request.session.get('library_db', 'default')
        set_current_service(library_db)
        
        # Attach the library_db to the request for future reference
        request.library_db = library_db
