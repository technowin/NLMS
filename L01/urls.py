from django.urls import path
from L01.views import *

urlpatterns = [
    path("index",index,name='index'),
    path("view_catalogue",view_catalogue,name='view_catalogue'),
    path("view_ebook_catalogue",view_ebook_catalogue,name='view_ebook_catalogue'),
    path('upsc_ebook_index/', upsc_ebook_index, name='upsc_ebook_index'),
    path('topic_index/<int:section_no>/', topic_index, name='topic_index'),
    path('chapters_index/<int:topic_id>/',chapters_index, name='chapters_index'),
    path("book_info_login/", book_info_login, name="book_info_login"),
    path("view_catalogue_login_page",view_catalogue_login_page,name='view_catalogue_login_page'),
    path('mpsc_ebooks_index/', mpsc_ebook_index, name='mpsc_ebooks_index'),
    path('mpsc_topics_index/<int:section_no>/', mpsc_topics_index, name='mpsc_topics_index'),
    path('mpsc_chapters_index/<int:topic_id>/', mpsc_chapters_index, name='mpsc_chapters_index'),
    path("index_book_search", index_book_search, name="index_book_search"),
    path("bookcatalog-search", bookcatalog_search, name="bookcatalog_search"),
    path("libraryebook_search", libraryebook_search, name="libraryebook_search"),
    path("registration",registration,name='registration'),
    path("check_user_id", check_user_id, name="check_user_id"),
    path("check_aadhar", check_aadhar, name="check_aadhar"),
    path("get_pincodes", get_pincodes, name="get_pincodes"),
    path("get_membership_details", get_membership_details, name="get_membership_details"),
    path("get-membership-code/",get_membership_code, name="get_membership_code"),
    
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
    
    # visit library master index views
    path('visit_Library_catalogue', visit_Library_catalogue, name='visit_Library_catalogue'),
    path('get_books_by_subject', get_books_by_subject, name='get_books_by_subject'),
    
    # Palaves work
    path('library_master_index_individual', library_master_index_individual, name='library_master_index_individual'), 
    path('user_master_index/', user_master_index, name='user_master_index'), 
    path('update_user_status', update_user_status, name='update_user_status'),
    path('user_create', user_create, name='user_create'),
    path('user_edit', user_edit, name='user_edit'),
    path('user_view', user_view, name='user_view'),

    path('user_view', user_view, name='user_view'),
    path('user_view', user_view, name='user_view'),

    path('member-entry-exit/', member_entry_exit, name='member_entry_exit'),
    path('get-member-details/<str:membership_code>/', get_member_detail, name='get_member_detail'),

    path('membership_dashboard/', membership_dashboard, name='membership_dashboard'),
    path('get-borrowing-history/',get_borrowing_history, name='get_borrowing_history'),
    
     path("save-eod-log/", save_eod_log, name="save_eod_log"),
     path("membership_card/", membership_card, name="membership_card"),
    # ... your other URLs
]
