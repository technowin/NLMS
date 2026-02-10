# mini_system/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='mini_system_home'),
    path('scan/', views.scan_rfid, name='scan_rfid'),
    path('issue-book/', views.issue_book, name='issue_book'),
    path('return-book/', views.return_book, name='return_book'),
    path('get-issued-books/', views.get_issued_books, name='get_issued_books'),
    path('clear-data/', views.clear_data, name='clear_data'),
    path('generate-test-data/', views.generate_test_data, name='generate_test_data'),
]