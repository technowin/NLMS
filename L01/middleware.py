from django.utils import timezone
from datetime import timedelta
from .models import MemberScreenActivity
import re





class MemberActivityMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # 🔐 Track ONLY member activity
        role_id = request.session.get('role_id')
        session_id = request.session.get('login_session_id')

        if role_id == '3' and session_id:
            path = request.path

            # ❌ Ignore static, media, admin, ajax
            if self.should_track(path, request):
                self.log_activity(session_id, path)

        return response

    def should_track(self, path, request):
        if path.startswith(('/static/', '/media/', '/admin/')):
            return False

        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return False

        return True

    def log_activity(self, session_id, path):
        # ⏱ Avoid duplicate entries on refresh (10 sec rule)
        last_entry = MemberScreenActivity.objects.filter(
            session_id=session_id,
            screen_route=path
        ).order_by('-visited_at').first()

        if not last_entry or timezone.now() - last_entry.visited_at > timedelta(seconds=10):
            MemberScreenActivity.objects.using('L01').create(
                session_id=session_id,
                screen_name=self.get_screen_name(path),
                screen_route=path
            )

    def get_screen_name(self, path):
        if path == '/':
            return 'Dashboard'

        # Remove leading/trailing slashes
        name = path.strip('/')

        # Remove L01 (case-insensitive)
        name = re.sub(r'\bL01\b', '', name, flags=re.IGNORECASE)

        # Replace _ and / with space
        name = name.replace('_', ' ').replace('/', ' ')

        # Remove extra spaces and title case
        name = re.sub(r'\s+', ' ', name).strip().title()

        return name
