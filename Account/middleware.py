from django.utils import timezone
from django.shortcuts import redirect

class SingleSessionMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):

        # ✅ if user NOT logged in → do nothing
        if not request.user.is_authenticated:
            return self.get_response(request)

        user = request.user

        # ❌ session mismatch → force logout
        if request.session.get("session_key") != user.session_key:
            user.is_logged_in = False
            user.session_key = None
            user.save(update_fields=["is_logged_in", "session_key"])
            request.session.flush()
            return redirect("login")

        # ✅ update activity timestamp
        user.last_activity = timezone.now()
        user.save(update_fields=["last_activity"])

        return self.get_response(request)
