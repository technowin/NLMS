from django.urls import path
from . import views

urlpatterns = [
    path('book-report/', views.BookReportView.as_view(), name='book_report'),
    path('book-list-data/', views.BookListDataView.as_view(), name='book_list_data'),
    path('tab-data/<str:tab_name>/', views.TabDataView.as_view(), name='tab_data'),
    path('get-book-options/', views.GetBookOptionsView.as_view(), name='get_book_options'),
    path('export-report/', views.ExportReportView.as_view(), name='export_report'),
    path('export-all-data/', views.ExportAllDataView.as_view(), name='export_all_data'),
    path('books/export-filtered/', views.ExportFilteredDataView.as_view(), name='export_filtered_data'),
]