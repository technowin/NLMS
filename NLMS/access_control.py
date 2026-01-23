from django.shortcuts import redirect
from functools import wraps
# from Account.views import logoutView 
# from django.contrib.auth import logout

def no_direct_access(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        referer = request.META.get('HTTP_REFERER')
        current_host = request.get_host()

        if not referer or current_host not in referer:
           from Account.views import logoutView 
           return logoutView(request)  #use your logout function here            
            # logout(request)
            # return redirect('login')  # or your desired error page
        return view_func(request, *args, **kwargs)
    return _wrapped_view