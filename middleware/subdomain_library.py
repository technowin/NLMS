class SubdomainLibraryMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

        # 🔥 Single source of truth
        self.SUBDOMAIN_LIBRARY_MAP = {
            'vdb': 'L01',
            # future:
            # 'abc': 'L02',
            # 'xyz': 'L03'
        }

    def __call__(self, request):
        host = request.get_host().split(':')[0]  # remove port
        parts = host.split('.')

        # Expecting: subdomain.nmmclibrary.in
        if len(parts) >= 3:
            subdomain = parts[0].lower()

            library_code = self.SUBDOMAIN_LIBRARY_MAP.get(subdomain)

            if library_code:
                # ✅ set session only if not already set
                if request.session.get('library_db') != library_code:
                    request.session['library_db'] = library_code
                    request.session.modified = True

        return self.get_response(request)
