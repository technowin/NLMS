"""
URL configuration for NLMS project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('',home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path,include
from django.conf import settings
from django.conf.urls.static import static
from django.views import defaults as default_views
from django.views.generic import TemplateView
from Account.views import *
from Masters.views import *
from Reports.views import *
from MenuManager.views import *
from administration.views import *
from administration.routers import ServiceRouter

# from ChatBot.views import *
urlpatterns = [
    
    # Django Admin, use {% url 'admin:index' %}

    path('admin/', admin.site.urls),
    # User management
    # path("users/", include("bootstrap.users.urls", namespace="users")),
    # Your stuff: custom urls includes go here
    path("apps/", include("bootstrap.apps.urls", namespace="apps")),
    path("apps/crm/", include("bootstrap.crm.urls", namespace="crm")),
    path("apps/ecommerce/", include("bootstrap.ecommerce.urls", namespace="ecommerce")),
    path("pages/", include("bootstrap.pages.urls", namespace="pages")),
    path("ui/", include("bootstrap.ui.urls", namespace="ui")),
    path("extended/", include("bootstrap.extended.urls", namespace="extended")),
    path("icons/", include("bootstrap.icons.urls", namespace="icons")),
    path("charts/", include("bootstrap.charts.urls", namespace="charts")),
    path("forms/", include("bootstrap.form.urls", namespace="form")),
    path("tables/", include("bootstrap.tables.urls", namespace="tables")),
    path("maps/", include("bootstrap.maps.urls", namespace="maps")),
    path("layouts/", include("bootstrap.layouts.urls", namespace="layouts")),
    path("dashboard/", include("bootstrap.dashboard.urls", namespace="dashboard")),
    path("landing", view=TemplateView.as_view(template_name="bootstrap/landing.html"), name="landing"),
    # path("", view=TemplateView.as_view(template_name="bootstrap/landing.html"), name="landing"),

    # translate in marathi
    path('translate/word/', translate_word, name='translate_word'),
    path('secure-ebook-file/<str:file_type_enc>/', secure_ebook_file_view, name='secure_ebook_file_view'),

    # Account
    path("", library_list,name='library_list'),
    # path("", Login,name='Account'),
    path("Login", Login,name='Account'),
    path("Login", Login,name='Login'),
    path("home", home,name='home'),
    path("logout",logoutView,name='logout'),
    path("forgot_password",forgot_password,name='forgot_password'),
    path('search/', search, name='search'),
    path("register_new_user",register_new_user, name="register_new_user"),
    path("reset_password",reset_password, name="reset_password"),
    path("change_password",change_password, name="change_password"),
    path("forget_password_change",forget_password_change, name="forget_password_change"),
    path("library_list_index", library_list_index,name='library_list_index'),

    # Masters
    path('masters/', masters, name='masters'),
    path('Test_sample/', Test_sample, name='Test_sample'),
    path('LMS_Dashboard/', LMS_Dashboard, name='LMS_Dashboard'),
    path('book_catalog_index/', book_catalog_index, name='book_catalog_index'),
    path('book_catalog_create/', book_catalog_create, name='book_catalog_create'),
    path('book_catalog_edit/', book_catalog_edit, name='book_catalog_edit'),
    path('book_accession_index/', book_accession_index, name='book_accession_index'),
    path('book_accession_create/', book_accession_create, name='book_accession_create'),
    path('material_type_master_index/', material_type_master_index, name='material_type_master_index'),
    path("updatestatus", updatestatus, name="updatestatus"),
    path('materialtype_list/', materialtype_list, name='materialtype_list'),
    path('material_type_create/', material_type_create, name='material_type_create'),
    path('materialtype_view/', materialtype_view, name='materialtype_view'),
    path('materialtype_edit/', materialtype_edit, name='materialtype_edit'),
    path('materialtype_delete/', materialtype_delete, name='materialtype_delete'),
    path('subject_type_master_index/', subject_type_master_index, name='subject_type_master_index'),
    path('subject_type_create/', subject_type_create, name='subject_type_create'),
    path('subject_type_view/', subject_type_view, name='subject_type_view'),
    path('subject_edit/', subject_edit, name='subject_edit'),
    path('subject_delete/', subject_delete, name='subject_delete'),
    path("update-subject-status/", update_subject_status, name="update_subject_status"),
    path("language_master_index/", language_master_index, name="language_master_index"),
    path("update_language_status/", update_language_status, name="update_language_status"),
    path('language_create/', language_create, name='language_create'),
    path('language_edit/', language_edit, name='language_edit'),
    path('language_view/', language_view, name='language_view'),
    path('language_delete/', language_delete, name='language_delete'),
    path('supplier_master_index/', supplier_master_index, name='supplier_master_index'),
    path('supplier_create/', supplier_create, name='supplier_create'),
    path('update_supplier_status/', update_supplier_status, name='update_supplier_status'),
    path('supplier_view/', supplier_view, name='supplier_view'),
    path('supplier_edit/', supplier_edit, name='supplier_edit'),
    path('supplier_delete/', supplier_delete, name='supplier_delete'),
    path('fundingsource_master_index/', fundingsource_master_index, name='fundingsource_master_index'),
    path('update_fundingsource_status/', update_fundingsource_status, name='update_fundingsource_status'),
    path('fundingsource_create/', fundingsource_create, name='fundingsource_create'),
    path('fundingsource_edit/', fundingsource_edit, name='fundingsource_edit'),
    path('fundingsource_view/', fundingsource_view, name='fundingsource_view'),
    path('fundingsource_delete/', fundingsource_delete, name='fundingsource_delete'),
    path('conditionatentry_master_index/', conditionatentry_master_index, name='conditionatentry_master_index'),
    path('update_conditionatentry_status/', update_conditionatentry_status, name='update_conditionatentry_status'),
    path('conditionatentry_edit/', conditionatentry_edit, name='conditionatentry_edit'),
    path('conditionatentry_create/', conditionatentry_create, name='conditionatentry_create'),
    path('conditionatentry_view/', conditionatentry_view, name='conditionatentry_view'),
    path('conditionatentry_delete/', conditionatentry_delete, name='conditionatentry_delete'),
    path('ward_master_index/', ward_master_index, name='ward_master_index'),
    path('update_ward_status/', update_ward_status, name='update_ward_status'),
    path('ward_create/', ward_create, name='ward_create'),
    path('ward_master_edit/', ward_master_edit, name='ward_master_edit'),
    path('ward_master_view/', ward_master_view, name='ward_master_view'),
    path('ward_master_delete/', ward_master_delete, name='ward_master_delete'),
    path('location_master_index/', location_master_index, name='location_master_index'),
    path('update_location_status/', update_location_status, name='update_location_status'),
    path('location_create/', location_create, name='location_create'),
    path('location_master_edit/', location_master_edit, name='location_master_edit'), 
    path('location_master_view/', location_master_view, name='location_master_view'), 
    path('location_master_delete/', location_master_delete, name='location_master_delete'),  
    path('library_master_index/', library_master_index, name='library_master_index'), 
    path('update_library_status/', update_library_status, name='update_library_status'), 
    path('library_create/', library_create, name='library_create'),
    path('library_master_edit/', library_master_edit, name='library_master_edit'),
    path('library_master_view/', library_master_view, name='library_master_view'),
    path('library_master_delete/', library_master_delete, name='library_master_delete'),
    path('circulation_master_index/', circulation_master_index, name='circulation_master_index'),
    path('circulation_master_edit/', circulation_master_edit, name='circulation_master_edit'),
    path('circulation_master_view/', circulation_master_view, name='circulation_master_view'),
    path('ebook_catalog_index/', ebook_catalog_index, name='ebook_catalog_index'),
    path('ebook_create/', ebook_create, name='ebook_create'),
    path('ebook_edit/', ebook_edit, name='ebook_edit'),

    #Reports 
    path('payment_report', payment_report, name='payment_report'),
    path('get_payment_preview/', get_payment_preview, name='get_payment_preview'),
    path('view_payment_report', view_payment_report, name='view_payment_report'),
    path('edit_payment_report', edit_payment_report, name='edit_payment_report'),
    path('view_secure_receipt/<str:enc_id>/', view_secure_receipt, name='view_secure_receipt'),
    path('download_secure_receipt/', download_secure_receipt, name='download_secure_receipt'),

    # Reports previously defined paths
    path('common_html', common_html, name='common_html'),
    path('get_filter', get_filter, name='get_filter'),
    path('get_sub_filter', get_sub_filter, name='get_sub_filter'),
    path('add_new_filter', add_new_filter, name='add_new_filter'),
    path('partial_report', partial_report, name='partial_report'),
    path('report_pdf', report_pdf, name='report_pdf'),
    path('report_xlsx', report_xlsx, name='report_xlsx'),
    path('save_filters', save_filters, name='save_filters'),
    path('delete_filters', delete_filters, name='delete_filters'),
    path('saved_filters', saved_filters, name='saved_filters'),
    path('download/<str:file_id>/', dl_file, name='dl_file'),

    # Menu Management
    path("menu_admin",menu_admin, name="menu_admin"),
    path("menu_master",menu_master, name="menu_master"),
    path("assign_menu",assign_menu, name="assign_menu"),
    path("get_assigned_values",get_assigned_values, name="get_assigned_values"),
    path("menu_order",menu_order, name="menu_order"),
    path("delete_menu",delete_menu, name="delete_menu"),
    
    # Bootstarp Pages
    path("dashboard",dashboard,name='dashboard'),
    path("buttons",buttons,name='buttons'),
    path("cards",cards,name='cards'),
    path("utilities_color",utilities_color,name='utilities_color'),
    path("utilities_border",utilities_border,name='utilities_border'),
    path("utilities_animation",utilities_animation,name='utilities_animation'),
    path("utilities_other",utilities_other,name='utilities_other'),
    path("error_page",error_page,name='error_page'),
    path("blank",blank,name='blank'),
    path("charts",charts,name='charts'),  
    path("tables",tables,name='tables'),
    
    # library list
    path("library_list",library_list,name='library_list'),
    path('service_redirect', service_redirect, name='service_redirect'),
    path('set_library_session_and_login', set_library_session_and_login, name='set_library_session_and_login'),
    path('L01/', include(('L01.urls', 'L01'), namespace='L01')),
    path('L02/', include(('L02.urls', 'L02'), namespace='L02')),
    
    path('track-click/', track_click, name='track_click'),
    path('should-show-popup/', should_show_popup, name='should_show_popup'),
    path('save-lead/', save_lead, name='save_lead'),
    
    # Layout
    path('commissioner-message/', commissioner_message, name='commissioner_message'),

    # Media files
    *static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)