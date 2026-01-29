# reports/urls.py - COMPLETE URL CONFIGURATION

from django.urls import path
from . import views

urlpatterns = [
    path('member-report/', views.MemberReportView.as_view(), name='member_report'),
    path('member-list-data/', views.MemberListDataView.as_view(), name='member_list_data'),
    path('tab-data/<str:tab_name>/', views.TabDataView.as_view(), name='tab_data'),
    path('export-report/', views.ExportReportView.as_view(), name='export_report'),
    path('export-all-data/', views.ExportAllDataView.as_view(), name='export_all_data'),
    path('save-report-session/', views.SaveReportSessionView.as_view(), name='save_report_session'),
    path('load-report-session/<int:session_id>/', views.LoadReportSessionView.as_view(), name='load_report_session'),
    path('list-sessions/', views.ListReportSessionsView.as_view(), name='list_report_sessions'),
    path('get-member-options/', views.GetMemberOptionsView.as_view(), name='get_member_options'),
    path('delete-session/<int:session_id>/', views.DeleteReportSessionView.as_view(), name='delete_report_session'),
    
    # API endpoints for document viewing
    path('api/members/<int:member_id>/documents/', views.MemberDocumentsView.as_view(), name='member_documents'),
    
    # PDF export endpoints
    path('export-pdf/<str:tab_name>/', views.ExportPDFView.as_view(), name='export_pdf'),
    path('export-complete-pdf/', views.ExportCompletePDFView.as_view(), name='export_complete_pdf'),

    path('list-sessions/', views.ListReportSessionsView.as_view(), name='list_report_sessions'),

    path('api/members/<int:member_id>/documents/', views.MemberDocumentsView.as_view(), name='member_documents'),
    path('delete-session/<int:session_id>/', views.DeleteReportSessionView.as_view(), name='delete_report_session'),
]