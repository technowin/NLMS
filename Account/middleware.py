from django.shortcuts import redirect
from django.conf import settings
from django.utils import timezone
from datetime import timedelta


from django.conf import settings
from django.utils import timezone
from datetime import timedelta


class SingleSessionMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response


    def __call__(self, request):

        # Skip login page

        if request.path == settings.LOGIN_URL:
            return self.get_response(request)

        # If not logged in → skip
        if not request.user.is_authenticated:
            return self.get_response(request)


        user = request.user

        # TIMEOUT = timedelta(seconds=30)
        TIMEOUT = timedelta(seconds=settings.SESSION_COOKIE_AGE)

        if user.last_activity:

            inactive_time = timezone.now() - user.last_activity

            if inactive_time > TIMEOUT:

                # Silent reset (NO redirect)
                user.is_logged_in = False
                user.session_key = None
                user.last_activity = None

                user.save(update_fields=[
                    "is_logged_in",
                    "session_key",
                    "last_activity"
                ])
                request.session.flush()


        # ================================
        # 2️⃣ NORMAL ACTIVITY
        # ================================

        user.last_activity = timezone.now()
        user.save(update_fields=["last_activity"])


        return self.get_response(request)
