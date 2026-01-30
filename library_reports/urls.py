# reports/urls.py - COMPLETE URL CONFIGURATION

from django.urls import path
from . import views

urlpatterns = [
    path('member-report/', views.MemberReportView.as_view(), name='member_report'),
    path('member-list-data/', views.MemberListDataView.as_view(), name='member_list_data'),
    path('tab-data/<str:tab_name>/', views.TabDataView.as_view(), name='tab_data'),
    path('get-member-options/', views.GetMemberOptionsView.as_view(), name='get_member_options'),
    path('api/members/<int:member_id>/documents/', views.MemberDocumentsView.as_view(), name='member_documents'),
    path('export-report/', views.ExportReportView.as_view(), name='export_report'),
    path('export-all-data/', views.ExportAllDataView.as_view(), name='export_all_data'),
]