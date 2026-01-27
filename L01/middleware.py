import re
from datetime import timedelta
from django.utils import timezone
from django.urls import resolve, Resolver404
from django.conf import settings
from .models import MemberLoginSession, MemberScreenActivity


class MemberActivityMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):

        response = self.get_response(request)

        # 🔐 Track ONLY logged-in members
        role_id = request.session.get('role_id')
        session_id = request.session.get('login_session_id')

        if role_id == '3' and session_id:
            path = request.path

            if self.should_track(path, request):

                ip_address = self.get_client_ip(request)
                device_type = self.get_device_type(request)
                self.update_login_session(request, session_id)

                self.log_activity(
                    session_id=session_id,
                    path=path,
                    ip_address=ip_address,
                    device_type=device_type
                )

        return response

    # -------------------------------------------------
    # ✅ FILTER VALID URLS
    # -------------------------------------------------
    def should_track(self, path, request):

        # ❌ Ignore static / media / admin
        if path.startswith(('/static/', '/media/', '/admin/')):
            return False

        # ❌ Ignore AJAX calls
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return False

        # ❌ Ignore special characters
        if re.search(r'[^a-zA-Z0-9/_-]', path):
            return False

        # ❌ Ignore invalid urls
        try:
            resolve(path)
        except Resolver404:
            return False

        return True

    # -------------------------------------------------
    # ✅ REAL IP ADDRESS
    # -------------------------------------------------
    def get_client_ip(self, request):

        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')

        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')

        return ip

    # -------------------------------------------------
    # ✅ DEVICE TYPE
    # -------------------------------------------------
    def get_device_type(self, request):

        ua = request.user_agent

        if ua.is_mobile:
            return 'Mobile'
        elif ua.is_tablet:
            return 'Tablet'
        elif ua.is_pc:
            return 'Desktop'
        return 'Unknown'

    # -------------------------------------------------
    # ✅ SAVE ACTIVITY
    # -------------------------------------------------
    def log_activity(self, session_id, path, ip_address, device_type):

        last_entry = MemberScreenActivity.objects.filter(
            session_id=session_id,
            screen_route=path
        ).order_by('-visited_at').first()


        # ⏱ 10 seconds duplicate prevention
        if not last_entry or timezone.now() - last_entry.visited_at > timedelta(seconds=10):

            MemberScreenActivity.objects.using('L01').create(
                session_id=session_id,
                screen_name=self.get_screen_name(path),
                screen_route=path
            )


    def update_login_session(self, request, login_session_id):

        try:
            # ✅ REAL IP
            ip_address = self.get_client_ip(request)

            # ✅ DEVICE TYPE (no package)
            device_type = self.get_device_type(request)

            # ✅ update only if empty
            MemberLoginSession.objects.using('L01').filter(
                id=login_session_id
            ).update(
                ip_address=ip_address,
                device_type=device_type
            )

        except Exception as e:
            print("Session update error:", e)


    # -------------------------------------------------
    # ✅ SCREEN NAME FORMATTER
    # -------------------------------------------------
    def get_screen_name(self, path):

        if path == '/':
            return 'Dashboard'

        name = path.strip('/')

        # remove L01
        name = re.sub(r'\bL01\b', '', name, flags=re.IGNORECASE)

        # formatting
        name = name.replace('_', ' ').replace('/', ' ')
        name = re.sub(r'\s+', ' ', name).strip().title()

        return name
