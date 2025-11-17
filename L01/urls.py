from django.urls import path
from L01.views import *

urlpatterns = [
    path("index",index,name='index'),
    path("view_catalogue",view_catalogue,name='view_catalogue'),
    path('upsc_ebook_index/', upsc_ebook_index, name='upsc_ebook_index'),
    path('topic_index/<int:section_no>/', topic_index, name='topic_index'),
    path('chapters_index/<int:topic_id>/',chapters_index, name='chapters_index'),
    path("bookcatalog-search", bookcatalog_search, name="bookcatalog_search"),
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
    path("membership_form_cancellation", membership_form_cancellation, name="membership_form_cancellation"),
    
    # barcode
    
    path("bar_code_index", bar_code_index, name="bar_code_index"),
    path("generate_barcode", generate_barcode, name="generate_barcode"),
    
    # Issue Book / Return Book
    path("issue_return_book_create", issue_return_book_create, name="issue_return_book_create"),
    path("get_member_details", get_member_details, name="get_member_details"),
    path("get_book_details", get_book_details, name="get_book_details"),
    path("get_book_circulation_status", get_book_circulation_status, name="get_book_circulation_status"),
    path("circulation_transaction_details", circulation_transaction_details, name="circulation_transaction_details"),
    
    # Palaves work
    path('library_master_index_individual', library_master_index_individual, name='library_master_index_individual'), 
    path('user_master_index/', user_master_index, name='user_master_index'), 
    path('update_user_status', update_user_status, name='update_user_status'),
    path('user_create', user_create, name='user_create'),
    path('user_edit', user_edit, name='user_edit'),
    path('user_view', user_view, name='user_view'),
]
