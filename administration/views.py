from django.shortcuts import render

# Create your views here.
def library_list(request):
    return render(request, 'administration/library_list.html')   