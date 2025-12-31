from .models import VisitorActivity

class VisitorTrackingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not request.session.session_key:
            request.session.create()

        session_key = request.session.session_key
        ip = self.get_client_ip(request)

        VisitorActivity.objects.using('default').get_or_create(
            session_key=session_key,
            defaults={'ip_address': ip}
        )


        return self.get_response(request)

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        return request.META.get('REMOTE_ADDR')
