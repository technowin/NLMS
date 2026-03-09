from django.urls import path
from L01.views import *

urlpatterns = [
    path("index",index,name='index'),
    path("view_catalogue_login_page",view_catalogue_login_page,name='view_catalogue_login_page'),
    path("view_ebook_catalogue",view_ebook_catalogue,name='view_ebook_catalogue'),
    path('upsc_ebook_index/', upsc_ebook_index, name='upsc_ebook_index'),
    path('topic_index/<str:section_no>/', topic_index, name='topic_index'),
    path('chapters_index/<str:topic_id>/',chapters_index, name='chapters_index'),
    path("book_info_login/", book_info_login, name="book_info_login"),
    path("view_catalogue_login_page",view_catalogue_login_page,name='view_catalogue_login_page'),
    path('mpsc_ebooks_index/', mpsc_ebook_index, name='mpsc_ebooks_index'),
    path("clear_pdf_session/", clear_pdf_session, name="clear_pdf_session"),
    path('mpsc_topics_index/<str:section_no>/', mpsc_topics_index, name='mpsc_topics_index'),
    path('mpsc_chapters_index/<str:topic_id>/', mpsc_chapters_index, name='mpsc_chapters_index'),
    path("index_book_search", index_book_search, name="index_book_search"),
    path("led_tv_index/", led_tv_index, name="led_tv_index"),
    path("bookcatalog-search", bookcatalog_search, name="bookcatalog_search"),
    path("libraryebook_search", libraryebook_search, name="libraryebook_search"),
    path("index_ebook_search", index_ebook_search, name="index_ebook_search"),
    path("registration",registration,name='registration'),
    path("check_user_id", check_user_id, name="check_user_id"),
    path("check_aadhar", check_aadhar, name="check_aadhar"),
    path("get_pincodes", get_pincodes, name="get_pincodes"),
    path("get_membership_details", get_membership_details, name="get_membership_details"),
    path("get-membership-code/",get_membership_code, name="get_membership_code"),
    
    path("kiosk_display/", kiosk_display, name="kiosk_display"),
    # path("visit_Library_ebook_catalogue/", visit_Library_ebook_catalogue, name="visit_library_Cate_ebooks"),
    path('visit_library_Cate_ebooks/', visit_library_Cate_ebooks, name='visit_library_Cate_ebooks'),
    path('visit_ebook_catalogue/', visit_ebook_catalogue, name='visit_ebook_catalogue'),
    path('get_ebooks_by_subject_kiosk/', get_ebooks_by_subject_kiosk, name='get_ebooks_by_subject_kiosk'),
    
    path("view_ebook_detail/", view_ebook_detail, name="view_ebook_detail"),
     # Both URLs use the same function
    path('kiosk_competitive_exam_type/', kiosk_competitive_exam_type, name='kiosk_competitive_exam_type'),
    
    # For detail view (with argument)
    # path('kiosk_competitive_exam_type/<int:competitive_id>/', kiosk_competitive_exam_type, name='kiosk_competitive_exam_type_detail'),
    
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
    path('show_Library_catalogue/', show_Library_catalogue, name='show_Library_catalogue'),
    path('visit_Library_catalogue', visit_Library_catalogue, name='visit_Library_catalogue'),
    path('read_ebook_secure', read_ebook_secure, name='read_ebook_secure'),
    path('serve_secure_pdf/', serve_secure_pdf, name='serve_secure_pdf'),
    path('view_book_detail/', view_book_detail, name='view_book_detail'),
    path('get_books_by_subject', get_books_by_subject, name='get_books_by_subject'),
    path('submit_review', submit_review, name='submit_review'),
    path('visit_Library_catalogue_kiosk', visit_Library_catalogue_kiosk, name='visit_Library_catalogue_kiosk'),
    path('get_books_by_subject_kiosk', get_books_by_subject_kiosk, name='get_books_by_subject_kiosk'),
    path('view_book_detail_kiosk/', view_book_detail_kiosk, name='view_book_detail_kiosk'),
    path('get_ebooks_by_subject', get_ebooks_by_subject, name='get_ebooks_by_subject'),
    
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
    path("clear-pending-action/", clear_pending_action, name="clear_pending_action"),
    
    path('competitive_exams_landing_page/',competitive_exams_landing_page, name='competitive_exams_landing_page'),
    path('upsc_index_logged/', upsc_index_logged, name='upsc_index_logged'),
    path('upsc_topics_logged/<str:section_no>/', upsc_topics_logged, name='upsc_topics_logged'),
    path('mpsc_index_logged/', mpsc_index_logged, name='mpsc_index_logged'),
    path('mpsc_topics_logged/<str:section_no>/', mpsc_topics_logged, name='mpsc_topics_logged'),
    path("open_pdf/", open_pdf, name="open_pdf"),
    # ... your other URLs
    
    # urls.py
    
    # for tv display
    
    path("tv/dashboard/", tv_dashboard_page, name="tv_dashboard_page"),
    path("tv/api/popular-books/", tv_popular_books_api, name="tv_popular_books_api"),
    path("tv/api/categories/", tv_categories_api, name="tv_categories_api"),
    path("tv/api/new-arrivals/", tv_new_arrivals_api, name="tv_new_arrivals_api"),
    path("tv/api/all-books/", tv_all_books_api, name="tv_all_books_api"),
    path("insert-book/<str:isbn>/", insert_book_by_isbn,name="insert_book_by_isbn"),
    
    path("advertisement_index/", advertisement_index, name="advertisement_index"),
    path('advertisement_toggle_status/<str:encrypted_id>/',advertisement_toggle_status,name='advertisement_toggle_status'),
    path("advertisement_create/", advertisement_create, name="advertisement_create"),
    path('advertisement_edit/<str:encrypted_id>/', advertisement_edit, name='advertisement_edit'),
    path("event_announcement_index/", event_announcement_index, name="event_announcement_index"),
    path('event_announcement_toggle_status/<str:encrypted_id>/',event_announcement_toggle_status,name='event_announcement_toggle_status'),
    path("event_announcement_create/", event_announcement_create, name="event_announcement_create"),
    path('event_announcement_edit/<str:encrypted_id>/', event_announcement_edit, name='event_announcement_edit'),
    
    # stock Checking By Imran
    path("scan-barcode/",scan_barcode, name="scan_barcode"),
    path("get_recent_scans/",get_recent_scans, name="get_recent_scans"),
    path('stock-report/', StockReportView.as_view(), name='stock_report'),
    path('export-stock-report/', ExportStockReportView.as_view(), name='export_stock_report'),
    path('complete-stock-batch/', complete_stock_batch, name='complete_stock_batch'),
    path('generate-final-report/', generate_final_report, name='generate_final_report'),
    path('generate-stock-report-api/', GenerateStockReportAPI.as_view(), name='generate_stock_report_api'),

    path('dashboard/', dashboard_view, name='dashboard'),
    path("catalog_data_ajax/", catalog_data_ajax, name="catalog_data_ajax"),
    path('dashboard/data/<str:dashboard_id>/', get_dashboard_data, name='dashboard_data'),
    path('catalog_detail_datatable/', catalog_detail_datatable, name='catalog_detail_datatable'),
    path('export_catalog_excel/', export_catalog_excel, name='export_catalog_excel'),
    path('export_catalog_pdf/', export_catalog_pdf, name='export_catalog_pdf'),
    
    # For Dashboard 4 Librarian Get DATA
    path("library_dashboard_data", library_dashboard_data, name="library_dashboard_data"),
    path('dashboard/details/', get_transaction_details, name='transaction_details'),
    path('get_dashboard3_data', get_dashboard3_data, name='get_dashboard3_data'),
    path('get_membershipType_data_dashboardThree', get_membershipType_data_dashboardThree, name='get_membershipType_data_dashboardThree'),
    path('dashboard/export/', dashboard_export, name='dashboard_export'),
    
    path('get_book_data_isbn/', get_book_data_isbn, name='get_book_data_isbn'),
    path('search-books/',search_books, name='search_books'),
    path('upload-excel/', upload_excel, name='upload_excel'),

    path('check-old-password/',check_old_password, name='check_old_password'),
    path('change-password/', change_password, name='change_password'),
    
    # kiosk competitive exam paths

    path('kiosk_competitive_sections/',  kiosk_competitive_sections, name='kiosk_competitive_sections'),
    path('kiosk_competitive_subjects/',  kiosk_competitive_subjects, name='kiosk_competitive_subjects'),
    path('kiosk_competitive_topics/',  kiosk_competitive_topics, name='kiosk_competitive_topics'),
    
    # AJAX endpoints
    path('get_competitive_sections/',  get_competitive_sections, name='get_competitive_sections'),
    path('get_competitive_subjects/',  get_competitive_subjects, name='get_competitive_subjects'),
    path('get_competitive_topics/',  get_competitive_topics, name='get_competitive_topics'),

]
