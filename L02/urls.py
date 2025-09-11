# L02/urls.py
from django.urls import path
from L02.views import *

urlpatterns = [
    path("index",index,name='index'),
]
