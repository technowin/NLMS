# reports/urls.py
from django.urls import path
from . import views, views_config

app_name = 'reports'

urlpatterns = [
    # Report pages
    path('member/', views.MemberReportView.as_view(), name='member_report'),
    path('book/', views.BookReportView.as_view(), name='book_report'),
    
    # API endpoints for reports
    path('api/load-members/', views.LoadMemberListAPI.as_view(), name='load_member_list'),
    path('api/data/', views.ReportDataAPI.as_view(), name='report_data'),
    path('api/export/', views.ExportReportAPI.as_view(), name='export_report'),
    # path('api/filters/', views.ReportFiltersAPI.as_view(), name='report_filters'),
    path('api/filter-options/', views.GetFilterOptionsAPI.as_view(), name='report_filters'),
    path('api/documents/', views.DocumentViewAPI.as_view(), name='document_view'),
    path('api/statistics/', views.ReportStatisticsAPI.as_view(), name='report_statistics'),
    path('api/save-config/', views.SaveReportConfigurationAPI.as_view(), name='save_configuration'),
    path('api/load-config/', views.LoadReportConfigurationAPI.as_view(), name='load_configuration'),
    
    # Configuration Management
    path('configurations/', views_config.ReportConfigurationListView.as_view(), name='config_list'),
    path('configurations/create/', views_config.ReportConfigurationCreateView.as_view(), name='config_create'),
    path('configurations/<int:pk>/edit/', views_config.ReportConfigurationUpdateView.as_view(), name='config_edit'),
    path('configurations/<int:pk>/preview/', views_config.ReportConfigurationPreviewView.as_view(), name='config_preview'),
    path('configurations/<int:pk>/export/', views_config.ReportConfigurationExportView.as_view(), name='config_export'),
    
    # Configuration APIs
    path('api/config/save/', views_config.ReportConfigurationSaveAPI.as_view(), name='config_save'),
    path('api/config/delete/', views_config.ReportConfigurationDeleteView.as_view(), name='config_delete'),
    path('api/config/clone/', views_config.CloneReportConfigurationAPI.as_view(), name='config_clone'),
    path('api/config/import/', views_config.ReportConfigurationImportView.as_view(), name='config_import'),
    path('api/model/fields/', views_config.GetModelFieldsAPI.as_view(), name='get_model_fields'),
]