from django.shortcuts import redirect
from django.contrib import messages

class SessionExpiryRedirectMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if (
            hasattr(request, 'user') and
            not request.user.is_authenticated and
            request.session.get('_session_expired')
        ):
            request.session.pop('_session_expired', None)

            messages.warning(
                request,
                "Your session has expired. Please continue browsing."
            )
            return redirect('library_list')

        return self.get_response(request)
