from django.urls import path
from L01.views import *

urlpatterns = [
    path("index",index,name='index'),
    path("registration",registration,name='registration'),
    path("check_user_id", check_user_id, name="check_user_id"),
    path("check_aadhar", check_aadhar, name="check_aadhar"),
    path("get_pincodes", get_pincodes, name="get_pincodes"),
    path("get_membership_details", get_membership_details, name="get_membership_details"),
]
