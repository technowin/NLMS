from django.urls import path
from L01.views import *

urlpatterns = [
    path("index",index,name='index'),
]
