from django.urls import path
from L01.views import *

urlpatterns = [
    path("index",index,name='index'),
    path("registration",registration,name='registration'),
    path("check_user_id", check_user_id, name="check_user_id"),
    path("check_aadhar", check_aadhar, name="check_aadhar"),
    path("get_pincodes", get_pincodes, name="get_pincodes"),
    path("get_membership_details", get_membership_details, name="get_membership_details"),
    
    # membership approval
    path("membership_approval", membership_approval, name="membership_approval"),
    path("membership_form_create", membership_form_create, name="membership_form_create"),
    path("membership_form_edit", membership_form_edit, name="membership_form_edit"),
    path("membership_form_view", membership_form_view, name="membership_form_view"),
    path("secure_document_view/<str:doc_id_enc>/", secure_document_view, name="secure_document_view"),
    
    # membership side
    path("membership_payment_index", membership_payment_index, name="membership_payment_index"),
    path("membership_paymentreceipt_download", membership_paymentreceipt_download, name="membership_paymentreceipt_download"),
    path("membership_form_renew", membership_form_renew, name="membership_form_renew"),
    
    # Palaves work
    path('library_master_index_individual', library_master_index_individual, name='library_master_index_individual'), 
]
