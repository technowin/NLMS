# reports/views.py

import os
import json
import calendar
import tempfile
from io import BytesIO
from datetime import date, datetime, time, timedelta

import pandas as pd
import xlsxwriter

from django.conf import settings
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.views import View
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.utils import timezone
from django.core.paginator import Paginator
from django.core.files.storage import FileSystemStorage
from django.contrib import messages
from django.db import transaction, connection
from django.db.models import (
    Q, F, Value, CharField, IntegerField, Func, DateField
)
from django.db.models.functions import (
    Concat, Now, Cast, Coalesce, ExtractMonth
)

from book_report.models import *
from L01.models import *
from Account.models import CustomUser
from .forms import *
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

class ReportBaseView(LoginRequiredMixin, View):
    """Base view for handling dynamic database selection"""
    
    def get_library_db(self):
        """Get current library database from session"""
        library_code = self.request.session.get('library_db', 'default')
        if library_code not in settings.DATABASES:
            library_code = 'default'
        return library_code
    
    def get_queryset(self, model_class, **filters):
        """Get queryset with dynamic database"""
        db = self.get_library_db()
        return model_class.objects.using(db).filter(**filters)
    
    def get_book_queryset(self, list_type='title', filters=None):
        """Get book queryset based on list type with applied filters"""
        db = self.get_library_db()
        
        if list_type == 'title':
            qs = BookCatalog.objects.using(db).filter(status_id=1)
            
            # Apply filters
            if filters:
                if filters.get('language'):
                    if filters['language'] == "Hindi":
                        qs = qs.filter(language="हिंदी")
                    elif filters['language'] == "Marathi":
                        qs = qs.filter(language="मराठी")
                    else: qs = qs.filter(language=filters['language'])
                if filters.get('resource_type') == 'ebook':
                    qs = qs.filter(ebook_available='Yes')
                elif filters.get('resource_type') == 'book':
                    qs = qs.filter(Q(ebook_available__isnull=True) | Q(ebook_available='No'))
                
                if filters.get('search'):
                    search_term = filters['search']
                    qs = qs.filter(
                        Q(title__icontains=search_term) |
                        Q(isbn_issn__icontains=search_term) |
                        Q(author__icontains=search_term)
                    )
            
            return qs.values('cat_ref_num', 'title', 'language', 'ebook_available', 'author')
            
        elif list_type == 'author':
            qs = AuthorMaster.objects.using(db).all()
            
            if filters and filters.get('search'):
                search_term = filters['search']
                qs = qs.filter(
                    Q(author_name_english__icontains=search_term) |
                    Q(author_name_marathi__icontains=search_term)
                )
            
            return qs.values('author_code', 'author_name_english', 'author_name_marathi')
            
        elif list_type == 'category':
            qs = SubjectTypeMaster.objects.using(db).filter(is_active=1)
            
            if filters and filters.get('search'):
                search_term = filters['search']
                qs = qs.filter(
                    Q(subjectNameEnglish__icontains=search_term) |
                    Q(subjectNameMarathi__icontains=search_term)
                )
            
            return qs.values('id', 'subjectNameEnglish', 'subjectNameMarathi')
        
        return []

class BookReportView(ReportBaseView, TemplateView):
    """Main book report view"""
    template_name = 'book_report/book_report.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        db = self.get_library_db()
        
        # Initialize all filter forms
        context['book_list_form'] = BookListFilterForm()
        
        # Initialize all tab filter forms with dynamic choices
        catalogue_form = CatalogueFilterForm()
        accession_form = AccessionFilterForm()
        circulation_form = CirculationFilterForm()
        supplier_form = SupplierFilterForm()
        review_form = ReviewFilterForm()
        return_log_form = ReturnLogFilterForm()
        
        # Get dynamic choices for forms
        try:
            # Subjects
            subjects = SubjectTypeMaster.objects.using(db).filter(is_active=1).values_list('id', 'subjectNameEnglish')
            catalogue_form.fields['subject'].choices = [(s[0], s[1]) for s in subjects]
            
            # Statuses
            statuses = status_master.objects.using(db).filter(is_active=1).values_list('status_id', 'status_name')
            catalogue_form.fields['status'].choices = [(s[0], s[1]) for s in statuses]
            accession_form.fields['status'].choices = [(s[0], s[1]) for s in statuses]
            circulation_form.fields['processing_status'].choices = [(s[0], s[1]) for s in statuses]
            circulation_form.fields['current_status'].choices = [(s[0], s[1]) for s in statuses]
            
            # Conditions
            conditions = ConditionAtEntryMaster.objects.using(db).filter(is_active=1).values_list('condition_id', 'condition_at_entry')
            accession_form.fields['condition'].choices = [(c[0], c[1]) for c in conditions]
            
            # Sources
            sources = FundingSourceMaster.objects.using(db).filter(is_active=1).values_list('source_id', 'funding_source_name')
            accession_form.fields['source'].choices = [(s[0], s[1]) for s in sources]
            
            # Locations
            locations = ResourceLocationMaster.objects.using(db).filter(is_active=1).values_list('location_id', 'location_name')
            accession_form.fields['location'].choices = [(l[0], l[1]) for l in locations]
            circulation_form.fields['shelf_location'].choices = [(l[0], l[1]) for l in locations]
            
            # Suppliers
            suppliers = SupplierMaster.objects.using(db).filter(is_active=1).values_list('supplier_id', 'supplier_name')
            accession_form.fields['supplier'].choices = [(s[0], s[1]) for s in suppliers]
            supplier_form.fields['supplier'].choices = [(s[0], s[1]) for s in suppliers]
            
            # Libraries
            libraries = tbl_librarymasterL01.objects.using(db).filter(is_active=1).values_list('library_code', 'library_name')
            review_form.fields['library'].choices = [(l[0], l[1]) for l in libraries]
            
            # Catalogues for review filter
            catalogues = BookCatalog.objects.using(db).filter(status_id=1).values_list('cat_ref_num', 'title')[:100]
            review_form.fields['catalogue'].choices = [(c[0], c[1]) for c in catalogues]
            return_log_form.fields['catalog'].choices = [(c[0], c[1]) for c in catalogues]
            
        except Exception as e:
            print(f"Error loading filter options: {e}")

        # Subjects for catalogue filter
        subjects = SubjectTypeMaster.objects.using(db).filter(
            is_active=1
        ).values('id', 'subjectNameEnglish')
        # Material Type
        material_type = MaterialTypeMaster.objects.using(db).filter(
            is_active=1
        ).values('id', 'materialNameEnglish')
        
        # Conditions
        conditions = ConditionAtEntryMaster.objects.using(db).filter(
            is_active=1
        ).values('condition_id', 'condition_at_entry')
        
        # Funding sources
        sources = FundingSourceMaster.objects.using(db).filter(
            is_active=1
        ).values('source_id', 'funding_source_name')
        
        # Locations
        locations = ResourceLocationMaster.objects.using(db).filter(
            is_active=1
        ).values('location_id', 'location_name')
        
        # Suppliers
        suppliers = SupplierMaster.objects.using(db).filter(
            is_active=1
        ).values('supplier_id', 'supplier_name')
        
        # Processing Status
        processing_status = status_master.objects.using(db).filter(
            is_active=1,status_type="Inventory"
        ).values('status_id', 'status_name')
        # Current Status
        current_status = status_master.objects.using(db).filter(
            is_active=1,status_type="Circulation Status"
        ).values('status_id', 'status_name')
        # Libraries
        libraries = tbl_librarymasterL01.objects.using(db).filter(
            is_active=1
        ).values('library_code', 'library_name')
        
        # Catalogues for review filter
        catalogues = BookCatalog.objects.using(db).filter(
            status_id=1
        ).values('cat_ref_num', 'title')[:100]

        context['subjects'] = subjects
        context['material_type'] = material_type
        context['conditions'] = conditions
        context['sources'] = sources
        context['locations'] = locations
        context['suppliers'] = suppliers
        context['processing_status'] = processing_status
        context['current_status'] = current_status
        context['libraries'] = libraries
        context['catalogues'] = catalogues

        context['catalogue_form'] = catalogue_form
        context['accession_form'] = accession_form
        context['circulation_form'] = circulation_form
        context['loan_form'] = LoanFilterForm()
        context['circulation_transaction_form'] = CirculationTransactionFilterForm()
        context['supplier_form'] = supplier_form
        context['review_form'] = review_form
        context['return_log_form'] = return_log_form
        context['google_metadata_form'] = GoogleMetadataFilterForm()
        context['loc_metadata_form'] = LOCMetadataFilterForm()
        
        # Get initial book list (titles)
        books = BookCatalog.objects.using(db).filter(
            status_id=1
        ).select_related('status')[:50]
        
        context['books'] = books
        context['total_book_count'] = BookCatalog.objects.using(db).filter(
            status_id=1
        ).count()
        
        # Add library info
        context['library_db'] = self.get_library_db()
        context['current_library'] = self.request.session.get('library_name', 'Main Library')
        
        # Add user info for template
        context['user'] = self.request.user
        
        return context

class BookListDataView(ReportBaseView):
    """AJAX endpoint for book list data on left side"""
    
    def get(self, request):
        try:
            form = BookListFilterForm(request.GET)
            if not form.is_valid():
                return JsonResponse({'error': 'Invalid form data'}, status=400)
            
            filters = form.cleaned_data
            list_type = filters.get('list_type', 'title')
            
            # Try to get database connection
            try:
                db = self.get_library_db()
                if db not in settings.DATABASES:
                    return JsonResponse({'error': 'Invalid database connection'}, status=400)
            except Exception as e:
                return JsonResponse({'error': f'Database connection error: {str(e)}'}, status=500)
            
            # Get queryset with error handling
            try:
                books_qs = self.get_book_queryset(list_type, filters)
            except Exception as e:
                return JsonResponse({'error': f'Failed to fetch data: {str(e)}'}, status=500)
            
            # Convert queryset to list for pagination
            try:
                books_list = list(books_qs)
            except Exception as e:
                return JsonResponse({'error': f'Failed to process query results: {str(e)}'}, status=500)
            
            # Pagination with validation
            try:
                page = int(request.GET.get('page', 1))
                per_page = int(request.GET.get('per_page', 20))
                
                # Validate pagination values
                if page < 1:
                    page = 1
                if per_page < 1 or per_page > 1000:  # Limit max per page
                    per_page = 20
                    
            except ValueError:
                page = 1
                per_page = 20
            
            # Create paginator
            try:
                paginator = Paginator(books_list, per_page)
                
                try:
                    books_page = paginator.page(page)
                except EmptyPage:
                    books_page = paginator.page(1)
                except PageNotAnInteger:
                    books_page = paginator.page(1)
                    
            except Exception as e:
                return JsonResponse({'error': f'Pagination error: {str(e)}'}, status=500)
            
            # Prepare response data
            data = {
                'books': [],
                'total': paginator.count,
                'pages': paginator.num_pages,
                'current_page': page,
                'list_type': list_type
            }
            
            # Process each book with error handling
            for book in books_page.object_list:
                try:
                    if list_type == 'title':
                        data['books'].append({
                            'id': book.get('cat_ref_num', ''),
                            'name': book.get('title', 'Untitled'),
                            'code': book.get('cat_ref_num', ''),
                            'type': 'Title',
                            'subtext': f"Author: {book.get('author', 'N/A')} | Lang: {book.get('language', 'N/A')} | Ebook: {book.get('ebook_available', 'No')}"
                        })
                    elif list_type == 'author':
                        data['books'].append({
                            'id': book.get('author_code', ''),
                            'name': book.get('author_name_english', 'Unknown Author'),
                            'code': book.get('author_code', ''),
                            'type': 'Author',
                            'subtext': book.get('author_name_marathi', '')
                        })
                    elif list_type == 'category':
                        data['books'].append({
                            'id': book.get('id', ''),
                            'name': book.get('subjectNameEnglish', 'Unknown Category'),
                            'code': f"SUB{book.get('id', '')}",
                            'type': 'Category',
                            'subtext': book.get('subjectNameMarathi', '')
                        })
                except Exception as e:
                    # Log the error but continue processing other books
                    print(f"Error processing book item: {e}")
                    continue
            
            return JsonResponse(data)
            
        except Exception as e:
            # Catch-all for any unexpected errors
            import traceback
            traceback.print_exc()  # Log for debugging
            return JsonResponse({
                'error': f'An unexpected error occurred: {str(e)}'
            }, status=500)
            
class TabDataView(ReportBaseView):
    """AJAX endpoint for tab data on right side"""
    
    def get(self, request, tab_name):
        book_ids = request.GET.getlist('book_ids[]')
        list_type = request.GET.get('list_type', 'title')
        filters_json = request.GET.get('filters', '{}')
        
        try:
            filters = json.loads(filters_json)
        except:
            filters = {}
        
        db = self.get_library_db()
        
        # Map tab names to data retrieval methods
        tab_methods = {
            'catalogue': self.get_catalogue_data,
            'accession': self.get_accession_data,
            'circulation': self.get_circulation_data,
            'loan': self.get_loan_data,
            'circulation-transaction': self.get_circulation_transaction_data,
            'supplier': self.get_supplier_data,
            'review': self.get_review_data,
            'return-log': self.get_return_log_data,
            'google-metadata': self.get_google_metadata_data,
            'loc-metadata': self.get_loc_metadata_data,
        }
        
        method = tab_methods.get(tab_name)
        if method:
            data = method(db, book_ids, list_type, filters)
            return JsonResponse(data)
        
        return JsonResponse({'error': 'Invalid tab'}, status=400)
    
    def get_catalogue_data(self, db, book_ids, list_type, filters):
        """Get catalogue data for selected books"""
        qs = BookCatalog.objects.using(db).filter(status_id=1)
        
        # Apply filters based on list_type
        if list_type == 'title':
            qs = qs.filter(cat_ref_num__in=book_ids)
        elif list_type == 'author':
            # Get books by this author
            qs = qs.filter(author_fk__in=book_ids)
        elif list_type == 'category':
            # Get books in this category
            qs = qs.filter(subject_id__in=book_ids)
        
        # Apply  filters


        from datetime import datetime, timedelta
        from_date = filters.get('from_date')
        to_date = filters.get('to_date')
        
        if from_date:
            from_datetime = datetime.strptime(from_date, "%Y-%m-%d")
            qs = qs.filter(created_at__gte=from_datetime)

        if to_date:
            # Add 1 day to include full end date
            to_datetime = datetime.strptime(to_date, "%Y-%m-%d") + timedelta(days=1)
            qs = qs.filter(created_at__lt=to_datetime)

        
        if filters.get('language'):
            languages = filters['language'] if isinstance(filters['language'], list) else [filters['language']]
            qs = qs.filter(language__in=languages)
        
        if filters.get('subject'):
            subjects = filters['subject'] if isinstance(filters['subject'], list) else [filters['subject']]
            qs = qs.filter(subject_id__in=subjects)
        
        if filters.get('status'):
            statuses = filters['status'] if isinstance(filters['status'], list) else [filters['status']]
            qs = qs.filter(status_id__in=statuses)
        
        if filters.get('ebook_available') == 'Yes':
            qs = qs.filter(ebook_available='Yes')
        elif filters.get('ebook_available') == 'No':
            qs = qs.filter(Q(ebook_available__isnull=True) | Q(ebook_available='No'))
        
        qs = qs.select_related('subject', 'material')
        
        data = []
        for catalog in qs:
            data.append({
                'cat_ref_num': catalog.cat_ref_num,
                'title': catalog.title,
                'subtitle': catalog.subtitle or '',
                'author': catalog.author or '',
                'other_authors': catalog.other_authors or '',
                'publisher': catalog.publisher or '',
                'isbn_issn': catalog.isbn_issn or '',
                'edition': catalog.edition or '',
                'keywords': catalog.keywords or '',
                'language': catalog.language or '',
                'publication_place': catalog.publication_place or '',
                'year_of_publication': catalog.year_of_publication or '',
                'classification_number': catalog.classification_number or '',
                'pages': catalog.pages or '',
                'date_of_registration': catalog.date_of_registration.strftime('%Y-%m-%d') if catalog.date_of_registration else '',
                'status_name': 'Yes' if catalog.status_id else '',
                'subject_name': catalog.subject.subjectNameEnglish if catalog.subject else '',
                'call_number': catalog.call_number or '',
                'cutter_number': catalog.cutter_number or '',
                'publication_year': catalog.publication_year or '',
                'remarks': catalog.remarks or '',
                'material_name': catalog.material.materialNameEnglish if catalog.material else '',
                'ebook_available': catalog.ebook_available or 'No',
                'ebook_id': catalog.ebook_id or '',
                'created_at': catalog.created_at.strftime('%Y-%m-%d %H:%M') if catalog.created_at else '',
                'created_by': catalog.created_by or '',
                'updated_at': catalog.updated_at.strftime('%Y-%m-%d %H:%M') if catalog.updated_at else '',
                'updated_by': catalog.updated_by or '',
            })
        
        return {'data': data, 'total': len(data)}
    
    def get_accession_data(self, db, book_ids, list_type, filters):
        """Get accession data for selected books"""
        qs = (BookAccession.objects.using(db).select_related('catalogue','condition_at_entry','funding_source','location','status','supplier','currency'))
        # Apply filters based on list_type
        if list_type == 'title':
            qs = qs.filter(catalogue_id__in=book_ids)

        elif list_type == 'author':
            # author is TextField, so filtering directly
            catalog_ids = (
                BookCatalog.objects.using(db)
                .filter(author_fk__in=book_ids)
                .values_list('cat_ref_num', flat=True)
            )
            qs = qs.filter(catalogue_id__in=catalog_ids)

        elif list_type == 'category':
            catalog_ids = (
                BookCatalog.objects.using(db)
                .filter(subject_id__in=book_ids)
                .values_list('cat_ref_num', flat=True)
            )
            qs = qs.filter(catalogue_id__in=catalog_ids)
        
        # Apply filters
        if filters.get('from_date'):
            qs = qs.filter(acquisition_date__gte=filters['from_date'])

        if filters.get('to_date'):
            qs = qs.filter(acquisition_date__lte=filters['to_date'])
        
        if filters.get('condition'):
            conditions = filters['condition'] if isinstance(filters['condition'], list) else [filters['condition']]
            qs = qs.filter(condition_at_entry_id__in=conditions)
        
        if filters.get('source'):
            sources = filters['source'] if isinstance(filters['source'], list) else [filters['source']]
            qs = qs.filter(funding_source__in=sources)
        
        if filters.get('location'):
            locations = filters['location'] if isinstance(filters['location'], list) else [filters['location']]
            qs = qs.filter(location_id__in=locations)
        
        if filters.get('status'):
            statuses = filters['status'] if isinstance(filters['status'], list) else [filters['status']]
            qs = qs.filter(status_id__in=statuses)
        
        if filters.get('supplier'):
            suppliers = filters['supplier'] if isinstance(filters['supplier'], list) else [filters['supplier']]
            qs = qs.filter(supplier_id__in=suppliers)
        
        # qs = qs.select_related(
        #     'catalog_ref_no', 'condition_at_entry', 'source', 
        #     'location', 'status', 'supplier', 'currency'
        # )
        def apply_fk_filter(qs, field, value):
            if value:
                values = value if isinstance(value, list) else [value]
                return qs.filter(**{f"{field}__in": values})
            return qs

        qs = apply_fk_filter(qs, 'condition_at_entry_id', filters.get('condition'))
        qs = apply_fk_filter(qs, 'funding_source_id', filters.get('source'))
        qs = apply_fk_filter(qs, 'location_id', filters.get('location'))
        qs = apply_fk_filter(qs, 'status_id', filters.get('status'))
        qs = apply_fk_filter(qs, 'supplier_id', filters.get('supplier'))

        data = []
        for acc in qs:
            data.append({
                'accession_no': acc.accession_no,
                'acquisition_date': acc.acquisition_date.strftime('%Y-%m-%d') if acc.acquisition_date else '',
                'catalog_ref_no': acc.catalogue.cat_ref_num if acc.catalogue else '',
                'book_title': acc.catalogue.title if acc.catalogue else '',
                'copy_number': acc.copy_number or '',
                'invoice_number': acc.invoice_number or '',
                'invoice_date': acc.invoice_date.strftime('%Y-%m-%d') if acc.invoice_date else '',
                'price': float(acc.price) if acc.price else 0.0,
                'remarks': acc.remarks or '',
                'created_at': acc.created_at.strftime('%Y-%m-%d %H:%M') if acc.created_at else '',
                'created_by': acc.created_by or '',
                'updated_at': acc.updated_at.strftime('%Y-%m-%d %H:%M') if acc.updated_at else '',
                'updated_by': acc.updated_by or '',
                'condition_name': acc.condition_at_entry.condition_at_entry if acc.condition_at_entry else '',
                'currency_name': acc.currency.currency_name if acc.currency else '',
                'source_name': acc.funding_source.funding_source_name if acc.funding_source else '',
                'location_name': acc.location.location_name if acc.location else '',
                'status_name': acc.status.status_name if acc.status else '',
                'supplier_name': acc.supplier.supplier_name if acc.supplier else '',
            })
        
        return {'data': data, 'total': len(data)}
    
    def get_circulation_data(self, db, book_ids, list_type, filters):
        """Get circulation data for selected books"""
        qs = CirculationCopyStatus.objects.using(db).all()
        
        # Apply filters based on list_type
        if list_type == 'title':
            qs = qs.filter(bookcatalog_id__in=book_ids)
        elif list_type == 'author':
            # Get circulation for books by this author
            catalog_ids = BookCatalog.objects.using(db).filter(
                author_fk__in=book_ids
            ).values_list('cat_ref_num', flat=True)
            qs = qs.filter(bookcatalog_id__in=catalog_ids)
        elif list_type == 'category':
            # Get circulation for books in this category
            catalog_ids = BookCatalog.objects.using(db).filter(
                subject_id__in=book_ids
            ).values_list('cat_ref_num', flat=True)
            qs = qs.filter(bookcatalog_id__in=catalog_ids)
        
        # Apply filters

        if filters.get('from_date'):
            qs = qs.filter(date_processed__gte=filters['from_date'])

        if filters.get('to_date'):
            qs = qs.filter(date_processed__lte=filters['to_date'])

        if filters.get('processing_status'):
            statuses = filters['processing_status'] if isinstance(filters['processing_status'], list) else [filters['processing_status']]
            qs = qs.filter(processing_status_id__in=statuses)
        
        if filters.get('shelf_location'):
            locations = filters['shelf_location'] if isinstance(filters['shelf_location'], list) else [filters['shelf_location']]
            qs = qs.filter(shelf_location_id__in=locations)
        
        if filters.get('current_status'):
            statuses = filters['current_status'] if isinstance(filters['current_status'], list) else [filters['current_status']]
            qs = qs.filter(current_status_id__in=statuses)
        
        qs = qs.select_related(
            'accession', 'bookcatalog', 'shelf_location',
            'processing_status', 'current_status'
        )
        
        data = []
        for circulation in qs:
            data.append({
                'barcode': circulation.barcode or '',
                'book_title': circulation.bookcatalog.title if circulation.bookcatalog else '',
                'bookcatalog_id': circulation.bookcatalog.cat_ref_num if circulation.bookcatalog else '',
                'accession_no': circulation.accession.accession_no if circulation.accession else '',
                'date_processed': circulation.date_processed.strftime('%Y-%m-%d') if circulation.date_processed else '',
                'processing_status': circulation.processing_status.status_name if circulation.processing_status else '',
                'shelf_location': circulation.shelf_location.location_name if circulation.shelf_location else '',
                'remarks': circulation.remarks or '',
                'created_at': circulation.created_at.strftime('%Y-%m-%d %H:%M') if circulation.created_at else '',
                'created_by': circulation.created_by or '',
                'updated_at': circulation.updated_at.strftime('%Y-%m-%d %H:%M') if circulation.updated_at else '',
                'updated_by': circulation.updated_by or '',
                'current_status': circulation.current_status.status_name if circulation.current_status else '',
            })
        
        return {'data': data, 'total': len(data)}
    
    def get_loan_data(self, db, book_ids, list_type, filters):
        """Get loan data for selected books"""
        qs = CirculationTransaction.objects.using(db).filter(
            return_date__isnull=True,  # Only outstanding loans
            due_date__isnull=False
        )
        
        # Apply filters based on list_type
        if list_type == 'title':
            qs = qs.filter(catalog_id__in=book_ids)
        elif list_type == 'author':
            # Get loans for books by this author
            catalog_ids = BookCatalog.objects.using(db).filter(
                author_fk__in=book_ids
            ).values_list('cat_ref_num', flat=True)
            qs = qs.filter(catalog_id__in=catalog_ids)
        elif list_type == 'category':
            # Get loans for books in this category
            catalog_ids = BookCatalog.objects.using(db).filter(
                subject_id__in=book_ids
            ).values_list('cat_ref_num', flat=True)
            qs = qs.filter(catalog_id__in=catalog_ids)
        
        # Apply date filters
        if filters.get('issue_from_date'):
            qs = qs.filter(issue_date__gte=filters['issue_from_date'])

        if filters.get('issue_to_date'):
            qs = qs.filter(issue_date__lte=filters['issue_to_date'])

        if filters.get('due_from_date'):
            qs = qs.filter(due_date__gte=filters['due_from_date'])

        if filters.get('due_to_date'):
            qs = qs.filter(due_date__lte=filters['due_to_date'])
        
        
        # Apply overdue filter
        today = date.today()
        overdue_filter = filters.get('overdue')
        if overdue_filter == '0_3':
            qs = qs.filter(
                due_date__lt=today,
                due_date__gte=today - timedelta(days=3)
            )
        elif overdue_filter == '4_7':
            qs = qs.filter(
                due_date__lt=today - timedelta(days=3),
                due_date__gte=today - timedelta(days=7)
            )
        elif overdue_filter == '1_month':
            qs = qs.filter(
                due_date__lt=today - timedelta(days=30)
            )
        elif overdue_filter == '3_month':
            qs = qs.filter(
                due_date__lt=today - timedelta(days=90)
            )
        elif overdue_filter == '6_month':
            qs = qs.filter(
                due_date__lt=today - timedelta(days=180)
            )
        
        # Apply fine status filter
        if filters.get('fine_status') == 'paid':
            qs = qs.filter(fine_status='Paid')
        elif filters.get('fine_status') == 'unpaid':
            qs = qs.filter(Q(fine_status='Unpaid') | Q(fine_status__isnull=True))
        elif filters.get('fine_status') == 'adjusted':
            qs = qs.filter(fine_status='Adjusted')
        
        qs = qs.select_related('catalog', 'accession', 'member')
        
        # Calculate overdue days
        qs = qs.annotate(
            overdue_days=Func(
                Now(),
                F('due_date'),
                function='DATEDIFF',
                output_field=IntegerField()
            )
        )
        
        data = []
        for transaction in qs:
            data.append({
                'barcode': transaction.barcode or '',
                'accession_id': transaction.accession.accession_no if transaction.accession else '',
                'cat_ref_num': transaction.catalog.cat_ref_num if transaction.catalog else '',
                'book_title': transaction.catalog.title if transaction.catalog else '',
                'member_name': f"{transaction.member.first_name or ''} {transaction.member.last_name or ''}".strip() if transaction.member else '',
                'membership_code': transaction.membership_code or '',
                'issue_date': transaction.issue_date.strftime('%Y-%m-%d') if transaction.issue_date else '',
                'due_date': transaction.due_date.strftime('%Y-%m-%d') if transaction.due_date else '',
                'return_date': transaction.return_date.strftime('%Y-%m-%d') if transaction.return_date else '',
                'days_overdue_count': transaction.overdue_days if transaction.overdue_days and transaction.overdue_days > 0 else 0,
                'fine_amount': float(transaction.fine_amount) if transaction.fine_amount else 0.0,
                'issued_by': transaction.issued_by or '',
                'remarks': transaction.remarks or '',
                'created_at': transaction.created_at.strftime('%Y-%m-%d %H:%M') if transaction.created_at else '',
            })
        
        return {'data': data, 'total': len(data)}
    
    def get_circulation_transaction_data(self, db, book_ids, list_type, filters):
        """Get circulation transaction data"""
        qs = CirculationTransaction.objects.using(db).all()
        
        # Apply filters based on list_type
        if list_type == 'title':
            qs = qs.filter(catalog_id__in=book_ids)
        elif list_type == 'author':
            catalog_ids = BookCatalog.objects.using(db).filter(
                author_fk__in=book_ids
            ).values_list('cat_ref_num', flat=True)
            qs = qs.filter(catalog_id__in=catalog_ids)
        elif list_type == 'category':
            catalog_ids = BookCatalog.objects.using(db).filter(
                subject_id__in=book_ids
            ).values_list('cat_ref_num', flat=True)
            qs = qs.filter(catalog_id__in=catalog_ids)
        
        # Apply all date filters
        if filters.get('issue_from_date'):
            qs = qs.filter(issue_date__gte=filters['issue_from_date'])

        if filters.get('issue_to_date'):
            qs = qs.filter(issue_date__lte=filters['issue_to_date'])

        if filters.get('due_from_date'):
            qs = qs.filter(due_date__gte=filters['due_from_date'])

        if filters.get('due_to_date'):
            qs = qs.filter(due_date__lte=filters['due_to_date'])
        
        if filters.get('return_from_date'):
            qs = qs.filter(return_date__gte=filters['return_from_date'])

        if filters.get('return_to_date'):
            qs = qs.filter(return_date__lte=filters['return_to_date'])

        
        # Apply other filters
        if filters.get('book_fine') == 'yes':
            qs = qs.filter(book_fine_amount__gt=0)
        elif filters.get('book_fine') == 'no':
            qs = qs.filter(Q(book_fine_amount__isnull=True) | Q(book_fine_amount=0))
        
        if filters.get('book_loss_fine') == 'yes':
            qs = qs.filter(fine_amount__gt=0)
        elif filters.get('book_loss_fine') == 'no':
            qs = qs.filter(Q(fine_amount__isnull=True) | Q(fine_amount=0))
        
        if filters.get('fine_status'):
            qs = qs.filter(fine_status=filters['fine_status'])
        
        qs = qs.select_related('catalog', 'accession', 'member', 'return_condition')
        
        # Calculate late days
        qs = qs.annotate(
            late_days=Func(
                Coalesce(F('return_date'), Cast(Now(), DateField())),
                F('due_date'),
                function='DATEDIFF',
                output_field=IntegerField()
            )
        )
        
        data = []
        for transaction in qs:
            data.append({
                'barcode': transaction.barcode or '',
                'accession_id': transaction.accession.accession_no if transaction.accession else '',
                'cat_ref_num': transaction.catalog.cat_ref_num if transaction.catalog else '',
                'member_name': f"{transaction.member.first_name or ''} {transaction.member.last_name or ''}".strip() if transaction.member else '',
                'membership_code': transaction.membership_code or '',
                'issue_date': transaction.issue_date.strftime('%Y-%m-%d') if transaction.issue_date else '',
                'due_date': transaction.due_date.strftime('%Y-%m-%d') if transaction.due_date else '',
                'issued_by': transaction.issued_by or '',
                'created_at': transaction.created_at.strftime('%Y-%m-%d %H:%M') if transaction.created_at else '',
                'return_date': transaction.return_date.strftime('%Y-%m-%d') if transaction.return_date else '',
                'received_by': transaction.received_by or '',
                'days_overdue_count': transaction.late_days if transaction.late_days and transaction.late_days > 0 else 0,
                'fine_amount': float(transaction.fine_amount) if transaction.fine_amount else 0.0,
                'book_fine_amount': float(transaction.book_fine_amount) if transaction.book_fine_amount else 0.0,
                'total_fine': float(transaction.total_fine) if transaction.total_fine else 0.0,
                'adjusted_fine': float(transaction.adjusted_fine) if transaction.adjusted_fine else 0.0,
                'fine_status': transaction.fine_status or '',
                'fine_paid_date': transaction.fine_paid_date.strftime('%Y-%m-%d') if transaction.fine_paid_date else '',
                'remarks': transaction.remarks or '',
                'updated_at': transaction.updated_at.strftime('%Y-%m-%d %H:%M') if transaction.updated_at else '',
            })
        
        return {'data': data, 'total': len(data)}
    
    def get_supplier_data(self, db, book_ids, list_type, filters):
        """Get supplier data for selected books"""
        qs = BookAccession.objects.using(db).select_related('catalogue', 'supplier')
        
        # Apply filters based on list_type
        if list_type == 'title':
            qs = qs.filter(catalogue_id__in=book_ids)
    
        elif list_type == 'author':
            # author is TextField in BookCatalog (NOT FK)
            catalog_ids = BookCatalog.objects.using(db).filter(
                author__in=book_ids
            ).values_list('cat_ref_num', flat=True)
    
            qs = qs.filter(catalogue_id__in=catalog_ids)
    
        elif list_type == 'category':
            # subject is FK → subject_id is correct
            catalog_ids = BookCatalog.objects.using(db).filter(
                subject_id__in=book_ids
            ).values_list('cat_ref_num', flat=True)

            qs = qs.filter(catalogue_id__in=catalog_ids)
        
        # Apply supplier filters
        if filters.get('supplier'):
            suppliers = filters['supplier'] if isinstance(filters['supplier'], list) else [filters['supplier']]
            qs = qs.filter(supplier_id__in=suppliers)
        
        if filters.get('is_active') == '1':
            qs = qs.filter(supplier__is_active=1)
        elif filters.get('is_active') == '0':
            qs = qs.filter(supplier__is_active=0)
        
        qs = qs.exclude(supplier__isnull=True)
        qs = qs.order_by('supplier_id').distinct()

        
        data = []
        for acc in qs:
            supplier = acc.supplier
            catalog = acc.catalogue
    
            data.append({
                'accession_no': acc.accession_no or '',
                'acquisition_date': acc.acquisition_date.strftime('%Y-%m-%d') if acc.acquisition_date else '',
                'catalog_ref_no': catalog.cat_ref_num if catalog else '',
                'book_title': catalog.title if catalog else '',
                'supplier_code': supplier.supplier_code,
                'supplier_name': supplier.supplier_name,
                'supplier_mobile': supplier.supplier_mobile or '',
                'supplier_email': supplier.supplier_email or '',
                'supplier_address': supplier.supplier_address or '',
                'supplier_pincode': supplier.supplier_pincode or '',
                'is_active': 'Yes' if supplier.is_active == 1 else 'No',
            })
        
        return {'data': data, 'total': len(data)}
    
    def get_review_data(self, db, book_ids, list_type, filters):
        """Get review data for selected books"""
        qs = BookReview.objects.using(db).all()
        
        # Apply filters based on list_type
        if list_type == 'title':
            qs = qs.filter(book_id__in=book_ids)
        elif list_type == 'author':
            catalog_ids = BookCatalog.objects.using(db).filter(
                author_fk__in=book_ids
            ).values_list('cat_ref_num', flat=True)
            qs = qs.filter(book_id__in=catalog_ids)
        elif list_type == 'category':
            catalog_ids = BookCatalog.objects.using(db).filter(
                subject_id__in=book_ids
            ).values_list('cat_ref_num', flat=True)
            qs = qs.filter(book_id__in=catalog_ids)
        
        # Apply filters
        if filters.get('rating'):
            ratings = filters['rating'] if isinstance(filters['rating'], list) else [filters['rating']]
            qs = qs.filter(rating__in=ratings)
        
        if filters.get('library'):
            libraries = filters['library'] if isinstance(filters['library'], list) else [filters['library']]
            qs = qs.filter(library_code__in=libraries)
        
        if filters.get('book_title'):
            qs = qs.filter(book__title__icontains=filters['book_title'])
        
        if filters.get('catalogue'):
            catalogues = filters['catalogue'] if isinstance(filters['catalogue'], list) else [filters['catalogue']]
            qs = qs.filter(book_id__in=catalogues)
        
        qs = qs.select_related('book')
        
        data = []
        for review in qs:
            # Get member details if user_id is a member ID
            member_name = ''
            if review.user_id:
                try:
                    member = MembershipDetails.objects.using(db).filter(id=review.user_id).first()
                    if member:
                        member_name = f"{member.first_name or ''} {member.last_name or ''}".strip()
                except:
                    pass
            
            data.append({
                'user_name': f"User {review.user_id}",
                'member_name': member_name,
                'rating': review.rating,
                'review': review.review,
                'created_at': review.created_at.strftime('%Y-%m-%d %H:%M') if review.created_at else '',
                'updated_at': review.updated_at.strftime('%Y-%m-%d %H:%M') if review.updated_at else '',
                'library_code': review.library_code or '',
                'cat_ref_id': review.book.cat_ref_num if review.book else '',
                'book_title': review.book.title if review.book else '',
                'ebook_name': review.book.title if review.book and review.book.ebook_available == 'Yes' else '',
            })
        
        return {'data': data, 'total': len(data)}
    
    def get_return_log_data(self, db, book_ids, list_type, filters):
        """Get return log data for selected books"""
        qs = BookReturnLog.objects.using(db).all()
        
        # Apply filters based on list_type
        if list_type == 'title':
            qs = qs.filter(cat_rem_num_id__in=book_ids)
        elif list_type == 'author':
            catalog_ids = BookCatalog.objects.using(db).filter(
                author_fk__in=book_ids
            ).values_list('cat_ref_num', flat=True)
            qs = qs.filter(cat_rem_num_id__in=catalog_ids)
        elif list_type == 'category':
            catalog_ids = BookCatalog.objects.using(db).filter(
                subject_id__in=book_ids
            ).values_list('cat_ref_num', flat=True)
            qs = qs.filter(cat_rem_num_id__in=catalog_ids)
        
        # Apply filters

        from datetime import datetime, timedelta
        from_date = filters.get('from_date')
        to_date = filters.get('to_date')
        
        if from_date:
            from_datetime = datetime.strptime(from_date, "%Y-%m-%d")
            qs = qs.filter(created_at__gte=from_datetime)

        if to_date:
            # Add 1 day to include full end date
            to_datetime = datetime.strptime(to_date, "%Y-%m-%d") + timedelta(days=1)
            qs = qs.filter(created_at__lt=to_datetime)
        
        if filters.get('is_shelved') == 'true':
            qs = qs.filter(is_shelved=True)
        elif filters.get('is_shelved') == 'false':
            qs = qs.filter(is_shelved=False)
        
        if filters.get('catalog'):
            catalogs = filters['catalog'] if isinstance(filters['catalog'], list) else [filters['catalog']]
            qs = qs.filter(cat_rem_num_id__in=catalogs)
        
        qs = qs.select_related('cat_rem_num', 'eod_log', 'created_by', 'updated_by')
        
        data = []
        for log in qs:
            data.append({
                'barcode': log.barcode,
                'book_title': log.cat_rem_num.title if log.cat_rem_num else '',
                'cat_ref_num_id': log.cat_rem_num.cat_ref_num if log.cat_rem_num else '',
                'is_shelved': 'Yes' if log.is_shelved else 'No',
                'created_at': log.created_at.strftime('%Y-%m-%d %H:%M') if log.created_at else '',
                'updated_at': log.updated_at.strftime('%Y-%m-%d %H:%M') if log.updated_at else '',
                'created_by_name': log.created_by.full_name if log.created_by else '',
                'eod_log_id': log.eod_log_id,
                'updated_by_name': log.updated_by.full_name if log.updated_by else '',
            })
        
        return {'data': data, 'total': len(data)}
    
    def get_google_metadata_data(self, db, book_ids, list_type, filters):
        """Get Google metadata data"""
        qs = GoogleBookMaster.objects.using(db).all()
        
        # Apply filters
        if filters.get('title'):
            qs = qs.filter(title__icontains=filters['title'])
        
        if filters.get('isbn'):
            qs = qs.filter(isbn__icontains=filters['isbn'])
        
        from datetime import datetime, timedelta
        from_date = filters.get('from_date')
        to_date = filters.get('to_date')
        
        if from_date:
            from_datetime = datetime.strptime(from_date, "%Y-%m-%d")
            qs = qs.filter(created_at__gte=from_datetime)

        if to_date:
            # Add 1 day to include full end date
            to_datetime = datetime.strptime(to_date, "%Y-%m-%d") + timedelta(days=1)
            qs = qs.filter(created_at__lt=to_datetime)
        
        qs = qs.prefetch_related('google_details')
        
        data = []
        for book in qs:
            # Get all details as key-value pairs
            details = {}
            for detail in book.google_details.all():
                details[detail.key] = detail.value
            
            data.append({
                'title': book.title,
                'isbn': book.isbn,
                'created_at': book.created_at.strftime('%Y-%m-%d %H:%M') if book.created_at else '',
                'details': json.dumps(details)
            })
        
        return {'data': data, 'total': len(data)}
    
    def get_loc_metadata_data(self, db, book_ids, list_type, filters):
        """Get LOC metadata data"""
        qs = LOCBookMaster.objects.using(db).all()
        
        # Apply filters
        if filters.get('title'):
            qs = qs.filter(title__icontains=filters['title'])
        
        if filters.get('isbn'):
            qs = qs.filter(isbn__icontains=filters['isbn'])
        
        from datetime import datetime, timedelta
        from_date = filters.get('from_date')
        to_date = filters.get('to_date')
        
        if from_date:
            from_datetime = datetime.strptime(from_date, "%Y-%m-%d")
            qs = qs.filter(created_at__gte=from_datetime)

        if to_date:
            # Add 1 day to include full end date
            to_datetime = datetime.strptime(to_date, "%Y-%m-%d") + timedelta(days=1)
            qs = qs.filter(created_at__lt=to_datetime)
        
        qs = qs.prefetch_related('loc_details')
        
        data = []
        for book in qs:
            # Get all details as key-value pairs
            details = {}
            for detail in book.loc_details.all():
                details[detail.key] = detail.value
            
            data.append({
                'title': book.title,
                'isbn': book.isbn,
                'created_at': book.created_at.strftime('%Y-%m-%d %H:%M') if book.created_at else '',
                'details': json.dumps(details)
            })
        
        return {'data': data, 'total': len(data)}

class GetBookOptionsView(ReportBaseView):
    """Get filter options for book types, subjects, etc."""
    
    def get(self, request):
        db = self.get_library_db()
        
        # Get all filter options
        try:
            # Subjects for catalogue filter
            subjects = SubjectTypeMaster.objects.using(db).filter(
                is_active=1
            ).values('id', 'subjectNameEnglish')
            
            # Statuses
            statuses = status_master.objects.using(db).filter(
                is_active=1
            ).values('status_id', 'status_name')

            # Material Type
            material_type = MaterialTypeMaster.objects.using(db).filter(
                is_active=1
            ).values('id', 'materialNameEnglish')
            
            # Conditions
            conditions = ConditionAtEntryMaster.objects.using(db).filter(
                is_active=1
            ).values('condition_id', 'condition_at_entry')
            
            # Funding sources
            sources = FundingSourceMaster.objects.using(db).filter(
                is_active=1
            ).values('source_id', 'funding_source_name')
            
            # Locations
            locations = ResourceLocationMaster.objects.using(db).filter(
                is_active=1
            ).values('location_id', 'location_name')
            
            # Suppliers
            suppliers = SupplierMaster.objects.using(db).filter(
                is_active=1
            ).values('supplier_id', 'supplier_name')
            
            # Processing Status
            processing_status = status_master.objects.using(db).filter(
                is_active=1,status_type="Inventory"
            ).values('status_id', 'status_name')

            # Current Status
            current_status = status_master.objects.using(db).filter(
                is_active=1,status_type="Circulation Status"
            ).values('status_id', 'status_name')

            # Libraries
            libraries = tbl_librarymasterL01.objects.using(db).filter(
                is_active=1
            ).values('library_code', 'library_name')
            
            # Catalogues for review filter
            catalogues = BookCatalog.objects.using(db).filter(
                status_id=1
            ).values('cat_ref_num', 'title')[:100]
            
        except Exception as e:
            # Return empty arrays on error
            subjects = []
            statuses = []
            processing_status = []
            current_status = []
            material_type = []
            conditions = []
            sources = []
            locations = []
            suppliers = []
            libraries = []
            catalogues = []
        
        return JsonResponse({
            'subjects': list(subjects),
            'statuses': list(statuses),
            'processing_status': list(processing_status),
            'current_status': list(current_status),
            'material_type': list(material_type),
            'conditions': list(conditions),
            'sources': list(sources),
            'locations': list(locations),
            'suppliers': list(suppliers),
            'libraries': list(libraries),
            'catalogues': list(catalogues),
        })

def normalize_export_filters(filters, db=None):
   
    FILTER_MODEL_MAP = {

        # 🔽 Catalogue Filters

        'subject': {
            'model': SubjectTypeMaster,
            'pk': 'id',
            'label': 'subjectNameEnglish',
            'extra_filter': {'is_active': 1}
        },
        'material_type': {
            'model': MaterialTypeMaster,
            'pk': 'id',
            'label': 'materialNameEnglish',
            'extra_filter': {'is_active': 1}
        },
        'condition': {
            'model': ConditionAtEntryMaster,
            'pk': 'condition_id',
            'label': 'condition_at_entry',
            'extra_filter': {'is_active': 1}
        },
        'funding_source': {
            'model': FundingSourceMaster,
            'pk': 'source_id',
            'label': 'funding_source_name',
            'extra_filter': {'is_active': 1}
        },
        'location': {
            'model': ResourceLocationMaster,
            'pk': 'location_id',
            'label': 'location_name',
            'extra_filter': {'is_active': 1}
        },
        'supplier': {
            'model': SupplierMaster,
            'pk': 'supplier_id',
            'label': 'supplier_name',
            'extra_filter': {'is_active': 1}
        },
        'processing_status': {
            'model': status_master,
            'pk': 'status_id',
            'label': 'status_name',
            'extra_filter': {'is_active': 1, 'status_type': 'Inventory'}
        },
        'current_status': {
            'model': status_master,
            'pk': 'status_id',
            'label': 'status_name',
            'extra_filter': {'is_active': 1, 'status_type': 'Circulation Status'}
        },
        'library': {
            'model': tbl_librarymasterL01,
            'pk': 'library_code',
            'label': 'library_name',
            'extra_filter': {'is_active': 1}
        },
        'catalogue': {
            'model': BookCatalog,
            'pk': 'cat_ref_num',
            'label': 'title',
            'extra_filter': {'status_id': 1}
        },
    }

    normalized_filters = {}

    for key, value in filters.items():

        if not value:
            normalized_filters[key] = value
            continue

        if key in FILTER_MODEL_MAP:

            cfg = FILTER_MODEL_MAP[key]
            model = cfg['model']
            pk_field = cfg['pk']
            label_field = cfg['label']
            extra_filter = cfg.get('extra_filter', {})

            ids = value if isinstance(value, (list, tuple)) else [value]

            lookup = {f"{pk_field}__in": ids}
            lookup.update(extra_filter)

            qs = model.objects
            if db:
                qs = qs.using(db)

            names = list(
                qs.filter(**lookup)
                  .values_list(label_field, flat=True)
            )

            normalized_filters[key] = ", ".join(map(str, names))

        else:
            normalized_filters[key] = value

    return normalized_filters

def export_catalogue_to_excel(writer, db, book_ids, list_type, filters):

    # --------------------------------------------------
    # Get data (same source as UI)
    # --------------------------------------------------
    view = TabDataView()
    response = view.get_catalogue_data(db, book_ids, list_type, filters)
    data = response.get('data', [])

    # --------------------------------------------------
    # Prepare Data
    # --------------------------------------------------
    rows = []
    for item in data:
        rows.append({
            'Ref No': item.get('cat_ref_num', ''),
            'Title': item.get('title', ''),
            'Subtitle': item.get('subtitle', ''),
            'Author': item.get('author', ''),
            'Other Authors': item.get('other_authors', ''),
            'Publisher': item.get('publisher', ''),
            'ISBN / ISSN': item.get('isbn_issn', ''),
            'Edition': item.get('edition', ''),
            'Keywords': item.get('keywords', ''),
            'Language': item.get('language', ''),
            'Publication Place': item.get('publication_place', ''),
            'Year of Publication': item.get('year_of_publication', ''),
            'Classification Number': item.get('classification_number', ''),
            'Pages': item.get('pages', ''),
            'Date of Registration': item.get('date_of_registration', ''),
            'Status': item.get('status_name', ''),
            'Subject': item.get('subject_name', ''),
            'Call Number': item.get('call_number', ''),
            'Cutter Number': item.get('cutter_number', ''),
            'Publication Year': item.get('publication_year', ''),
            'Remarks': item.get('remarks', ''),
            'Material': item.get('material_name', ''),
            'Ebook Available': item.get('ebook_available', ''),
            'Ebook ID': item.get('ebook_id', ''),
            'Created At': item.get('created_at', ''),
            'Created By': item.get('created_by', ''),
            'Updated At': item.get('updated_at', ''),
            'Updated By': item.get('updated_by', ''),
        })

    df = pd.DataFrame(rows)

    sheet_name = 'Catalogue'
    start_row = 6  # same spacing as member report

    df.to_excel(
        writer,
        sheet_name=sheet_name,
        index=False,
        startrow=start_row
    )

    # --------------------------------------------------
    # Workbook & Worksheet
    # --------------------------------------------------
    workbook = writer.book
    worksheet = writer.sheets[sheet_name]

    # --------------------------------------------------
    # Formats (copied & aligned)
    # --------------------------------------------------
    title_format = workbook.add_format({
        'bold': True,
        'font_size': 16,
        'align': 'center',
        'valign': 'vcenter'
    })

    subtitle_format = workbook.add_format({
        'italic': True,
        'font_size': 10,
        'align': 'center'
    })

    header_format = workbook.add_format({
        'bold': True,
        'text_wrap': True,
        'border': 1,
        'align': 'center',
        'valign': 'middle',
        'bg_color': '#D9E1F2'
    })

    cell_format = workbook.add_format({
        'border': 1,
        'valign': 'top'
    })

    alt_row_format = workbook.add_format({
        'border': 1,
        'bg_color': '#F9F9F9'
    })

    filter_label_format = workbook.add_format({
        'bold': True
    })

    no_data_format = workbook.add_format({
        'align': 'center',
        'italic': True
    })

    # --------------------------------------------------
    # Report Title
    # --------------------------------------------------
    total_columns = len(df.columns)

    worksheet.merge_range(
        0, 0, 0, total_columns - 1,
        'Catalogue Report',
        title_format
    )

    worksheet.merge_range(
        1, 0, 1, total_columns - 1,
        f'Generated on: {timezone.now().strftime("%d-%m-%Y %H:%M")}',
        subtitle_format
    )

    # Convert filter IDs → names (ONLY for display)
    filters = normalize_export_filters(filters)

    # --------------------------------------------------
    # Applied Filters
    # --------------------------------------------------

    worksheet.write(3, 0, 'Applied Filters:', filter_label_format)

    col = 1
    worksheet.write(3, col, f'List Type: {list_type.title()}')
    
    col += 1

    for key, value in filters.items():
        if value:
            worksheet.write(
                3,
                col,
                f'{key.replace("_", " ").title()}: {value}'
            )
            col += 1

    # --------------------------------------------------
    # Header Styling
    # --------------------------------------------------
    for col_idx, col_name in enumerate(df.columns):
        worksheet.write(start_row, col_idx, col_name, header_format)

    # --------------------------------------------------
    # Data Rows Styling (alternate rows)
    # --------------------------------------------------
    for row_idx in range(len(df)):
        excel_row = start_row + 1 + row_idx
        row_format = alt_row_format if row_idx % 2 else cell_format

        for col_idx in range(total_columns):
            worksheet.write(
                excel_row,
                col_idx,
                df.iloc[row_idx, col_idx],
                row_format
            )

    # --------------------------------------------------
    # Auto Column Width
    # --------------------------------------------------
    for col_idx, column in enumerate(df.columns):
        max_len = max(
            df[column].astype(str).map(len).max() if not df.empty else 10,
            len(column)
        )
        worksheet.set_column(col_idx, col_idx, min(max_len + 3, 50))

    # --------------------------------------------------
    # Freeze Header & Enable AutoFilter
    # --------------------------------------------------
    worksheet.freeze_panes(start_row + 1, 0)
    if not df.empty:
        worksheet.autofilter(
            start_row,
            0,
            start_row + len(df),
            total_columns - 1
        )

    # --------------------------------------------------
    # No Data Message
    # --------------------------------------------------
    if df.empty:
        worksheet.merge_range(
            start_row + 1, 0,
            start_row + 2, total_columns - 1,
            'No records found for selected filters',
            no_data_format
        )

def export_accession_to_excel(writer, db, book_ids, list_type, filters):

    # --------------------------------------------------
    # Get data (same logic as UI)
    # --------------------------------------------------
    view = TabDataView()
    response = view.get_accession_data(db, book_ids, list_type, filters)
    data = response.get('data', [])

    # --------------------------------------------------
    # Prepare Data
    # --------------------------------------------------
    rows = []
    for item in data:
        rows.append({
            'Accession No': item.get('accession_no', ''),
            'Acquisition Date': item.get('acquisition_date', ''),
            'Catalog Ref No': item.get('catalog_ref_no', ''),
            'Book Title': item.get('book_title', ''),
            'Copy Number': item.get('copy_number', ''),
            'Invoice Number': item.get('invoice_number', ''),
            'Invoice Date': item.get('invoice_date', ''),
            'Price': item.get('price', ''),
            'Remarks': item.get('remarks', ''),
            'Condition': item.get('condition_name', ''),
            'Currency': item.get('currency_name', ''),
            'Source': item.get('source_name', ''),
            'Location': item.get('location_name', ''),
            'Status': item.get('status_name', ''),
            'Supplier': item.get('supplier_name', ''),
            'Created At': item.get('created_at', ''),
            'Created By': item.get('created_by', ''),
            'Updated At': item.get('updated_at', ''),
            'Updated By': item.get('updated_by', ''),
        })

    df = pd.DataFrame(rows)

    sheet_name = 'Accession'
    start_row = 6

    df.to_excel(
        writer,
        sheet_name=sheet_name,
        index=False,
        startrow=start_row
    )

    # --------------------------------------------------
    # Workbook & Worksheet
    # --------------------------------------------------
    workbook = writer.book
    worksheet = writer.sheets[sheet_name]

    # --------------------------------------------------
    # Formats (same as other exports)
    # --------------------------------------------------
    title_format = workbook.add_format({
        'bold': True,
        'font_size': 16,
        'align': 'center',
        'valign': 'vcenter'
    })

    subtitle_format = workbook.add_format({
        'italic': True,
        'font_size': 10,
        'align': 'center'
    })

    header_format = workbook.add_format({
        'bold': True,
        'text_wrap': True,
        'border': 1,
        'align': 'center',
        'valign': 'middle',
        'bg_color': '#D9E1F2'
    })

    cell_format = workbook.add_format({
        'border': 1,
        'valign': 'top'
    })

    alt_row_format = workbook.add_format({
        'border': 1,
        'bg_color': '#F9F9F9'
    })

    filter_label_format = workbook.add_format({
        'bold': True
    })

    no_data_format = workbook.add_format({
        'align': 'center',
        'italic': True
    })

    # --------------------------------------------------
    # Report Title
    # --------------------------------------------------
    total_columns = len(df.columns)

    worksheet.merge_range(
        0, 0, 0, total_columns - 1,
        'Accession Report',
        title_format
    )

    worksheet.merge_range(
        1, 0, 1, total_columns - 1,
        f'Generated on: {timezone.now().strftime("%d-%m-%Y %H:%M")}',
        subtitle_format
    )

    # Convert filter IDs → names (ONLY for display)
    filters = normalize_export_filters(filters)

    # --------------------------------------------------
    # Applied Filters
    # --------------------------------------------------

    worksheet.write(3, 0, 'Applied Filters:', filter_label_format)

    col = 1
    worksheet.write(3, col, f'List Type: {list_type.title()}')
    
    col += 1

    for key, value in filters.items():
        if value:
            worksheet.write(
                3,
                col,
                f'{key.replace("_", " ").title()}: {value}'
            )
            col += 1

    # --------------------------------------------------
    # Header Styling
    # --------------------------------------------------
    for col_idx, col_name in enumerate(df.columns):
        worksheet.write(start_row, col_idx, col_name, header_format)

    # --------------------------------------------------
    # Data Rows Styling
    # --------------------------------------------------
    for row_idx in range(len(df)):
        excel_row = start_row + 1 + row_idx
        row_format = alt_row_format if row_idx % 2 else cell_format

        for col_idx in range(total_columns):
            worksheet.write(
                excel_row,
                col_idx,
                df.iloc[row_idx, col_idx],
                row_format
            )

    # --------------------------------------------------
    # Auto Column Width
    # --------------------------------------------------
    for col_idx, column in enumerate(df.columns):
        max_len = max(
            df[column].astype(str).map(len).max() if not df.empty else 10,
            len(column)
        )
        worksheet.set_column(col_idx, col_idx, min(max_len + 3, 40))

    # --------------------------------------------------
    # Freeze Header & AutoFilter
    # --------------------------------------------------
    worksheet.freeze_panes(start_row + 1, 0)

    if not df.empty:
        worksheet.autofilter(
            start_row,
            0,
            start_row + len(df),
            total_columns - 1
        )

    # --------------------------------------------------
    # No Data Message
    # --------------------------------------------------
    if df.empty:
        worksheet.merge_range(
            start_row + 1, 0,
            start_row + 2, total_columns - 1,
            'No records found for selected filters',
            no_data_format
        )

def export_circulation_to_excel(writer, db, book_ids, list_type, filters):

    # --------------------------------------------------
    # Get data (same source as UI)
    # --------------------------------------------------
    view = TabDataView()
    response = view.get_circulation_data(db, book_ids, list_type, filters)
    data = response.get('data', [])

    # --------------------------------------------------
    # Prepare Data
    # --------------------------------------------------
    rows = []
    for item in data:
        rows.append({
            'Barcode': item.get('barcode', ''),
            'Book Title': item.get('book_title', ''),
            'Catalogue Ref No': item.get('bookcatalog_id', ''),
            'Accession No': item.get('accession_no', ''),
            'Date Processed': item.get('date_processed', ''),
            'Processing Status': item.get('processing_status', ''),
            'Shelf Location': item.get('shelf_location', ''),
            'Current Status': item.get('current_status', ''),
            'Remarks': item.get('remarks', ''),
            'Created At': item.get('created_at', ''),
            'Created By': item.get('created_by', ''),
            'Updated At': item.get('updated_at', ''),
            'Updated By': item.get('updated_by', ''),
        })

    df = pd.DataFrame(rows)

    sheet_name = 'Circulation'
    start_row = 6  # same spacing as other reports

    df.to_excel(
        writer,
        sheet_name=sheet_name,
        index=False,
        startrow=start_row
    )

    # --------------------------------------------------
    # Workbook & Worksheet
    # --------------------------------------------------
    workbook = writer.book
    worksheet = writer.sheets[sheet_name]

    # --------------------------------------------------
    # Formats
    # --------------------------------------------------
    title_format = workbook.add_format({
        'bold': True,
        'font_size': 16,
        'align': 'center',
        'valign': 'vcenter'
    })

    subtitle_format = workbook.add_format({
        'italic': True,
        'font_size': 10,
        'align': 'center'
    })

    header_format = workbook.add_format({
        'bold': True,
        'text_wrap': True,
        'border': 1,
        'align': 'center',
        'valign': 'middle',
        'bg_color': '#D9E1F2'
    })

    cell_format = workbook.add_format({
        'border': 1,
        'valign': 'top'
    })

    alt_row_format = workbook.add_format({
        'border': 1,
        'bg_color': '#F9F9F9'
    })

    filter_label_format = workbook.add_format({
        'bold': True
    })

    no_data_format = workbook.add_format({
        'align': 'center',
        'italic': True
    })

    # --------------------------------------------------
    # Report Title
    # --------------------------------------------------
    total_columns = len(df.columns)

    worksheet.merge_range(
        0, 0, 0, total_columns - 1,
        'Circulation Report',
        title_format
    )

    worksheet.merge_range(
        1, 0, 1, total_columns - 1,
        f'Generated on: {timezone.now().strftime("%d-%m-%Y %H:%M")}',
        subtitle_format
    )

    # Convert filter IDs → names (ONLY for display)
    filters = normalize_export_filters(filters)

    # --------------------------------------------------
    # Applied Filters
    # --------------------------------------------------
    worksheet.write(3, 0, 'Applied Filters:', filter_label_format)

    col = 1
    worksheet.write(3, col, f'List Type: {list_type.title()}')
    
    col += 1

    for key, value in filters.items():
        if value:
            worksheet.write(
                3,
                col,
                f'{key.replace("_", " ").title()}: {value}'
            )
            col += 1

    # --------------------------------------------------
    # Header Styling
    # --------------------------------------------------
    for col_idx, col_name in enumerate(df.columns):
        worksheet.write(start_row, col_idx, col_name, header_format)

    # --------------------------------------------------
    # Data Rows Styling (alternate rows)
    # --------------------------------------------------
    for row_idx in range(len(df)):
        excel_row = start_row + 1 + row_idx
        row_format = alt_row_format if row_idx % 2 else cell_format

        for col_idx in range(total_columns):
            worksheet.write(
                excel_row,
                col_idx,
                df.iloc[row_idx, col_idx],
                row_format
            )

    # --------------------------------------------------
    # Auto Column Width
    # --------------------------------------------------
    for col_idx, column in enumerate(df.columns):
        max_len = max(
            df[column].astype(str).map(len).max() if not df.empty else 10,
            len(column)
        )
        worksheet.set_column(col_idx, col_idx, min(max_len + 3, 50))

    # --------------------------------------------------
    # Freeze Header & Enable AutoFilter
    # --------------------------------------------------
    worksheet.freeze_panes(start_row + 1, 0)
    if not df.empty:
        worksheet.autofilter(
            start_row,
            0,
            start_row + len(df),
            total_columns - 1
        )

    # --------------------------------------------------
    # No Data Message
    # --------------------------------------------------
    if df.empty:
        worksheet.merge_range(
            start_row + 1, 0,
            start_row + 2, total_columns - 1,
            'No records found for selected filters',
            no_data_format
        )

def export_loan_to_excel(writer, db, book_ids, list_type, filters):

    # --------------------------------------------------
    # Get data (same source as UI)
    # --------------------------------------------------
    view = TabDataView()
    response = view.get_loan_data(db, book_ids, list_type, filters)
    data = response.get('data', [])

    # --------------------------------------------------
    # Prepare Data
    # --------------------------------------------------
    rows = []
    for item in data:
        rows.append({
            'Barcode': item.get('barcode', ''),
            'Accession No': item.get('accession_id', ''),
            'Catalogue Ref No': item.get('cat_ref_num', ''),
            'Book Title': item.get('book_title', ''),
            'Member Name': item.get('member_name', ''),
            'Membership Code': item.get('membership_code', ''),
            'Issue Date': item.get('issue_date', ''),
            'Due Date': item.get('due_date', ''),
            'Return Date': item.get('return_date', ''),
            'Days Overdue': item.get('days_overdue_count', 0),
            'Fine Amount': item.get('fine_amount', 0.0),
            'Issued By': item.get('issued_by', ''),
            'Remarks': item.get('remarks', ''),
            'Created At': item.get('created_at', ''),
        })

    df = pd.DataFrame(rows)

    sheet_name = 'Loans'
    start_row = 6

    df.to_excel(
        writer,
        sheet_name=sheet_name,
        index=False,
        startrow=start_row
    )

    # --------------------------------------------------
    # Workbook & Worksheet
    # --------------------------------------------------
    workbook = writer.book
    worksheet = writer.sheets[sheet_name]

    # --------------------------------------------------
    # Formats
    # --------------------------------------------------
    title_format = workbook.add_format({
        'bold': True,
        'font_size': 16,
        'align': 'center',
        'valign': 'vcenter'
    })

    subtitle_format = workbook.add_format({
        'italic': True,
        'font_size': 10,
        'align': 'center'
    })

    header_format = workbook.add_format({
        'bold': True,
        'text_wrap': True,
        'border': 1,
        'align': 'center',
        'valign': 'middle',
        'bg_color': '#D9E1F2'
    })

    cell_format = workbook.add_format({
        'border': 1,
        'valign': 'top'
    })

    alt_row_format = workbook.add_format({
        'border': 1,
        'bg_color': '#F9F9F9'
    })

    filter_label_format = workbook.add_format({
        'bold': True
    })

    no_data_format = workbook.add_format({
        'align': 'center',
        'italic': True
    })

    money_format = workbook.add_format({
        'border': 1,
        'num_format': '#,##0.00'
    })

    # --------------------------------------------------
    # Report Title
    # --------------------------------------------------
    total_columns = len(df.columns)

    worksheet.merge_range(
        0, 0, 0, total_columns - 1,
        'Loan Report',
        title_format
    )

    worksheet.merge_range(
        1, 0, 1, total_columns - 1,
        f'Generated on: {timezone.now().strftime("%d-%m-%Y %H:%M")}',
        subtitle_format
    )

    # Convert filter IDs → names (ONLY for display)
    filters = normalize_export_filters(filters)

    # --------------------------------------------------
    # Applied Filters
    # --------------------------------------------------
    worksheet.write(3, 0, 'Applied Filters:', filter_label_format)

    col = 1
    worksheet.write(3, col, f'List Type: {list_type.title()}')
    
    col += 1

    for key, value in filters.items():
        if value:
            worksheet.write(
                3,
                col,
                f'{key.replace("_", " ").title()}: {value}'
            )
            col += 1

    # --------------------------------------------------
    # Header Styling
    # --------------------------------------------------
    for col_idx, col_name in enumerate(df.columns):
        worksheet.write(start_row, col_idx, col_name, header_format)

    # --------------------------------------------------
    # Data Rows Styling (alternate rows)
    # --------------------------------------------------
    fine_col_idx = df.columns.get_loc('Fine Amount')

    for row_idx in range(len(df)):
        excel_row = start_row + 1 + row_idx
        row_format = alt_row_format if row_idx % 2 else cell_format

        for col_idx in range(total_columns):
            value = df.iloc[row_idx, col_idx]

            if col_idx == fine_col_idx:
                worksheet.write(excel_row, col_idx, value, money_format)
            else:
                worksheet.write(excel_row, col_idx, value, row_format)

    # --------------------------------------------------
    # Auto Column Width
    # --------------------------------------------------
    for col_idx, column in enumerate(df.columns):
        max_len = max(
            df[column].astype(str).map(len).max() if not df.empty else 10,
            len(column)
        )
        worksheet.set_column(col_idx, col_idx, min(max_len + 3, 50))

    # --------------------------------------------------
    # Freeze Header & Enable AutoFilter
    # --------------------------------------------------
    worksheet.freeze_panes(start_row + 1, 0)

    if not df.empty:
        worksheet.autofilter(
            start_row,
            0,
            start_row + len(df),
            total_columns - 1
        )

    # --------------------------------------------------
    # No Data Message
    # --------------------------------------------------
    if df.empty:
        worksheet.merge_range(
            start_row + 1, 0,
            start_row + 2, total_columns - 1,
            'No outstanding loan records found for selected filters',
            no_data_format
        )

def export_circulation_transaction_to_excel(writer, db, book_ids, list_type, filters):

    # --------------------------------------------------
    # Get data (same source as UI)
    # --------------------------------------------------
    view = TabDataView()
    response = view.get_circulation_transaction_data(db, book_ids, list_type, filters)
    data = response.get('data', [])

    # --------------------------------------------------
    # Prepare Data
    # --------------------------------------------------
    rows = []
    for item in data:
        rows.append({
            'Barcode': item.get('barcode', ''),
            'Accession No': item.get('accession_id', ''),
            'Catalogue Ref No': item.get('cat_ref_num', ''),
            'Member Name': item.get('member_name', ''),
            'Membership Code': item.get('membership_code', ''),
            'Issue Date': item.get('issue_date', ''),
            'Due Date': item.get('due_date', ''),
            'Issued By': item.get('issued_by', ''),
            'Created At': item.get('created_at', ''),
            'Return Date': item.get('return_date', ''),
            'Received By': item.get('received_by', ''),
            'Days Overdue': item.get('days_overdue_count', 0),
            'Book Fine Amount': item.get('book_fine_amount', 0.0),
            'Loss Fine Amount': item.get('fine_amount', 0.0),
            'Total Fine': item.get('total_fine', 0.0),
            'Adjusted Fine': item.get('adjusted_fine', 0.0),
            'Fine Status': item.get('fine_status', ''),
            'Fine Paid Date': item.get('fine_paid_date', ''),
            'Remarks': item.get('remarks', ''),
            'Updated At': item.get('updated_at', ''),
        })

    df = pd.DataFrame(rows)

    sheet_name = 'Circulation Transactions'
    start_row = 6

    df.to_excel(
        writer,
        sheet_name=sheet_name,
        index=False,
        startrow=start_row
    )

    # --------------------------------------------------
    # Workbook & Worksheet
    # --------------------------------------------------
    workbook = writer.book
    worksheet = writer.sheets[sheet_name]

    # --------------------------------------------------
    # Formats
    # --------------------------------------------------
    title_format = workbook.add_format({
        'bold': True,
        'font_size': 16,
        'align': 'center',
        'valign': 'vcenter'
    })

    subtitle_format = workbook.add_format({
        'italic': True,
        'font_size': 10,
        'align': 'center'
    })

    header_format = workbook.add_format({
        'bold': True,
        'text_wrap': True,
        'border': 1,
        'align': 'center',
        'valign': 'middle',
        'bg_color': '#D9E1F2'
    })

    cell_format = workbook.add_format({
        'border': 1,
        'valign': 'top'
    })

    alt_row_format = workbook.add_format({
        'border': 1,
        'bg_color': '#F9F9F9'
    })

    filter_label_format = workbook.add_format({
        'bold': True
    })

    no_data_format = workbook.add_format({
        'align': 'center',
        'italic': True
    })

    money_format = workbook.add_format({
        'border': 1,
        'num_format': '#,##0.00'
    })

    # --------------------------------------------------
    # Report Title
    # --------------------------------------------------
    total_columns = len(df.columns)

    worksheet.merge_range(
        0, 0, 0, total_columns - 1,
        'Circulation Transaction Report',
        title_format
    )

    worksheet.merge_range(
        1, 0, 1, total_columns - 1,
        f'Generated on: {timezone.now().strftime("%d-%m-%Y %H:%M")}',
        subtitle_format
    )

    # Convert filter IDs → names (ONLY for display)
    filters = normalize_export_filters(filters)

    # --------------------------------------------------
    # Applied Filters
    # --------------------------------------------------
    worksheet.write(3, 0, 'Applied Filters:', filter_label_format)

    col = 1
    worksheet.write(3, col, f'List Type: {list_type.title()}')
    
    col += 1

    for key, value in filters.items():
        if value:
            worksheet.write(
                3,
                col,
                f'{key.replace("_", " ").title()}: {value}'
            )
            col += 1

    # --------------------------------------------------
    # Header Styling
    # --------------------------------------------------
    for col_idx, col_name in enumerate(df.columns):
        worksheet.write(start_row, col_idx, col_name, header_format)

    # --------------------------------------------------
    # Data Rows Styling (alternate rows)
    # --------------------------------------------------
    money_columns = [
        'Book Fine Amount',
        'Loss Fine Amount',
        'Total Fine',
        'Adjusted Fine'
    ]
    money_col_indexes = [df.columns.get_loc(c) for c in money_columns]

    for row_idx in range(len(df)):
        excel_row = start_row + 1 + row_idx
        row_format = alt_row_format if row_idx % 2 else cell_format

        for col_idx in range(total_columns):
            value = df.iloc[row_idx, col_idx]

            if col_idx in money_col_indexes:
                worksheet.write(excel_row, col_idx, value, money_format)
            else:
                worksheet.write(excel_row, col_idx, value, row_format)

    # --------------------------------------------------
    # Auto Column Width
    # --------------------------------------------------
    for col_idx, column in enumerate(df.columns):
        max_len = max(
            df[column].astype(str).map(len).max() if not df.empty else 10,
            len(column)
        )
        worksheet.set_column(col_idx, col_idx, min(max_len + 3, 50))

    # --------------------------------------------------
    # Freeze Header & Enable AutoFilter
    # --------------------------------------------------
    worksheet.freeze_panes(start_row + 1, 0)

    if not df.empty:
        worksheet.autofilter(
            start_row,
            0,
            start_row + len(df),
            total_columns - 1
        )

    # --------------------------------------------------
    # No Data Message
    # --------------------------------------------------
    if df.empty:
        worksheet.merge_range(
            start_row + 1, 0,
            start_row + 2, total_columns - 1,
            'No circulation transactions found for selected filters',
            no_data_format
        )

def export_supplier_to_excel(writer, db, book_ids, list_type, filters):
    
    # --------------------------------------------------
    # Get data (same source as UI)
    # --------------------------------------------------
    view = TabDataView()
    response = view.get_supplier_data(db, book_ids, list_type, filters)
    data = response.get('data', [])

    # --------------------------------------------------
    # Prepare Data
    # --------------------------------------------------
    rows = []
    for item in data:
        rows.append({
            'Accession No': item.get('accession_no', ''),
            'Acquisition Date': item.get('acquisition_date', ''),
            'Catalogue Ref No': item.get('catalog_ref_no', ''),
            'Book Title': item.get('book_title', ''),
            'Supplier Code': item.get('supplier_code', ''),
            'Supplier Name': item.get('supplier_name', ''),
            'Supplier Mobile': item.get('supplier_mobile', ''),
            'Supplier Email': item.get('supplier_email', ''),
            'Supplier Address': item.get('supplier_address', ''),
            'Supplier Pincode': item.get('supplier_pincode', ''),
            'Active': item.get('is_active', ''),
        })

    df = pd.DataFrame(rows)

    sheet_name = 'Suppliers'
    start_row = 6

    df.to_excel(
        writer,
        sheet_name=sheet_name,
        index=False,
        startrow=start_row
    )

    # --------------------------------------------------
    # Workbook & Worksheet
    # --------------------------------------------------
    workbook = writer.book
    worksheet = writer.sheets[sheet_name]

    # --------------------------------------------------
    # Formats
    # --------------------------------------------------
    title_format = workbook.add_format({
        'bold': True,
        'font_size': 16,
        'align': 'center',
        'valign': 'vcenter'
    })

    subtitle_format = workbook.add_format({
        'italic': True,
        'font_size': 10,
        'align': 'center'
    })

    header_format = workbook.add_format({
        'bold': True,
        'text_wrap': True,
        'border': 1,
        'align': 'center',
        'valign': 'middle',
        'bg_color': '#D9E1F2'
    })

    cell_format = workbook.add_format({
        'border': 1,
        'valign': 'top'
    })

    alt_row_format = workbook.add_format({
        'border': 1,
        'bg_color': '#F9F9F9'
    })

    filter_label_format = workbook.add_format({
        'bold': True
    })

    no_data_format = workbook.add_format({
        'align': 'center',
        'italic': True
    })

    # --------------------------------------------------
    # Report Title
    # --------------------------------------------------
    total_columns = len(df.columns)

    worksheet.merge_range(
        0, 0, 0, total_columns - 1,
        'Supplier Report',
        title_format
    )

    worksheet.merge_range(
        1, 0, 1, total_columns - 1,
        f'Generated on: {timezone.now().strftime("%d-%m-%Y %H:%M")}',
        subtitle_format
    )

    # Convert filter IDs → names (ONLY for display)
    filters = normalize_export_filters(filters)

    # --------------------------------------------------
    # Applied Filters
    # --------------------------------------------------
    worksheet.write(3, 0, 'Applied Filters:', filter_label_format)

    col = 1
    worksheet.write(3, col, f'List Type: {list_type.title()}')
    
    col += 1

    for key, value in filters.items():
        if value:
            worksheet.write(
                3,
                col,
                f'{key.replace("_", " ").title()}: {value}'
            )
            col += 1

    # --------------------------------------------------
    # Header Styling
    # --------------------------------------------------
    for col_idx, col_name in enumerate(df.columns):
        worksheet.write(start_row, col_idx, col_name, header_format)

    # --------------------------------------------------
    # Data Rows Styling (alternate rows)
    # --------------------------------------------------
    for row_idx in range(len(df)):
        excel_row = start_row + 1 + row_idx
        row_format = alt_row_format if row_idx % 2 else cell_format

        for col_idx in range(total_columns):
            worksheet.write(
                excel_row,
                col_idx,
                df.iloc[row_idx, col_idx],
                row_format
            )

    # --------------------------------------------------
    # Auto Column Width
    # --------------------------------------------------
    for col_idx, column in enumerate(df.columns):
        max_len = max(
            df[column].astype(str).map(len).max() if not df.empty else 10,
            len(column)
        )
        worksheet.set_column(col_idx, col_idx, min(max_len + 3, 50))

    # --------------------------------------------------
    # Freeze Header & Enable AutoFilter
    # --------------------------------------------------
    worksheet.freeze_panes(start_row + 1, 0)

    if not df.empty:
        worksheet.autofilter(
            start_row,
            0,
            start_row + len(df),
            total_columns - 1
        )

    # --------------------------------------------------
    # No Data Message
    # --------------------------------------------------
    if df.empty:
        worksheet.merge_range(
            start_row + 1, 0,
            start_row + 2, total_columns - 1,
            'No supplier records found for selected filters',
            no_data_format
        )

def export_review_to_excel(writer, db, book_ids, list_type, filters):
    
    # --------------------------------------------------
    # Get data (same source as UI)
    # --------------------------------------------------
    view = TabDataView()
    response = view.get_review_data(db, book_ids, list_type, filters)
    data = response.get('data', [])

    # --------------------------------------------------
    # Prepare Data
    # --------------------------------------------------
    rows = []
    for item in data:
        rows.append({
            'User': item.get('user_name', ''),
            'Member Name': item.get('member_name', ''),
            'Rating': item.get('rating', ''),
            'Review': item.get('review', ''),
            'Library Code': item.get('library_code', ''),
            'Catalogue Ref No': item.get('cat_ref_id', ''),
            'Book Title': item.get('book_title', ''),
            'Ebook Name': item.get('ebook_name', ''),
            'Created At': item.get('created_at', ''),
            'Updated At': item.get('updated_at', ''),
        })

    df = pd.DataFrame(rows)

    sheet_name = 'Reviews'
    start_row = 6

    df.to_excel(
        writer,
        sheet_name=sheet_name,
        index=False,
        startrow=start_row
    )

    # --------------------------------------------------
    # Workbook & Worksheet
    # --------------------------------------------------
    workbook = writer.book
    worksheet = writer.sheets[sheet_name]

    # --------------------------------------------------
    # Formats
    # --------------------------------------------------
    title_format = workbook.add_format({
        'bold': True,
        'font_size': 16,
        'align': 'center',
        'valign': 'vcenter'
    })

    subtitle_format = workbook.add_format({
        'italic': True,
        'font_size': 10,
        'align': 'center'
    })

    header_format = workbook.add_format({
        'bold': True,
        'text_wrap': True,
        'border': 1,
        'align': 'center',
        'valign': 'middle',
        'bg_color': '#D9E1F2'
    })

    cell_format = workbook.add_format({
        'border': 1,
        'valign': 'top'
    })

    alt_row_format = workbook.add_format({
        'border': 1,
        'bg_color': '#F9F9F9'
    })

    filter_label_format = workbook.add_format({
        'bold': True
    })

    no_data_format = workbook.add_format({
        'align': 'center',
        'italic': True
    })

    wrap_text_format = workbook.add_format({
        'border': 1,
        'text_wrap': True,
        'valign': 'top'
    })

    # --------------------------------------------------
    # Report Title
    # --------------------------------------------------
    total_columns = len(df.columns)

    worksheet.merge_range(
        0, 0, 0, total_columns - 1,
        'Book Review Report',
        title_format
    )

    worksheet.merge_range(
        1, 0, 1, total_columns - 1,
        f'Generated on: {timezone.now().strftime("%d-%m-%Y %H:%M")}',
        subtitle_format
    )

    # Convert filter IDs → names (ONLY for display)
    filters = normalize_export_filters(filters)

    # --------------------------------------------------
    # Applied Filters
    # --------------------------------------------------
    worksheet.write(3, 0, 'Applied Filters:', filter_label_format)

    col = 1
    worksheet.write(3, col, f'List Type: {list_type.title()}')
    
    col += 1

    for key, value in filters.items():
        if value:
            worksheet.write(
                3,
                col,
                f'{key.replace("_", " ").title()}: {value}'
            )
            col += 1

    # --------------------------------------------------
    # Header Styling
    # --------------------------------------------------
    for col_idx, col_name in enumerate(df.columns):
        worksheet.write(start_row, col_idx, col_name, header_format)

    # --------------------------------------------------
    # Data Rows Styling (alternate rows)
    # --------------------------------------------------
    review_col_idx = df.columns.get_loc('Review')

    for row_idx in range(len(df)):
        excel_row = start_row + 1 + row_idx
        row_format = alt_row_format if row_idx % 2 else cell_format

        for col_idx in range(total_columns):
            value = df.iloc[row_idx, col_idx]

            if col_idx == review_col_idx:
                worksheet.write(excel_row, col_idx, value, wrap_text_format)
            else:
                worksheet.write(excel_row, col_idx, value, row_format)

    # --------------------------------------------------
    # Auto Column Width
    # --------------------------------------------------
    for col_idx, column in enumerate(df.columns):
        max_len = max(
            df[column].astype(str).map(len).max() if not df.empty else 10,
            len(column)
        )
        worksheet.set_column(col_idx, col_idx, min(max_len + 3, 60))

    # --------------------------------------------------
    # Freeze Header & Enable AutoFilter
    # --------------------------------------------------
    worksheet.freeze_panes(start_row + 1, 0)

    if not df.empty:
        worksheet.autofilter(
            start_row,
            0,
            start_row + len(df),
            total_columns - 1
        )

    # --------------------------------------------------
    # No Data Message
    # --------------------------------------------------
    if df.empty:
        worksheet.merge_range(
            start_row + 1, 0,
            start_row + 2, total_columns - 1,
            'No reviews found for selected filters',
            no_data_format
        )

def export_return_log_to_excel(writer, db, book_ids, list_type, filters):

    # --------------------------------------------------
    # Get data (same source as UI)
    # --------------------------------------------------
    view = TabDataView()
    response = view.get_return_log_data(db, book_ids, list_type, filters)
    data = response.get('data', [])

    # --------------------------------------------------
    # Prepare Data
    # --------------------------------------------------
    rows = []
    for item in data:
        rows.append({
            'Barcode': item.get('barcode', ''),
            'Book Title': item.get('book_title', ''),
            'Catalogue Ref No': item.get('cat_ref_num_id', ''),
            'Shelved': item.get('is_shelved', ''),
            'Created At': item.get('created_at', ''),
            'Created By': item.get('created_by_name', ''),
            'Updated At': item.get('updated_at', ''),
            'Updated By': item.get('updated_by_name', ''),
            'EOD Log ID': item.get('eod_log_id', ''),
        })

    df = pd.DataFrame(rows)

    sheet_name = 'Return Log'
    start_row = 6  # same spacing as other reports

    df.to_excel(
        writer,
        sheet_name=sheet_name,
        index=False,
        startrow=start_row
    )

    # --------------------------------------------------
    # Workbook & Worksheet
    # --------------------------------------------------
    workbook = writer.book
    worksheet = writer.sheets[sheet_name]

    # --------------------------------------------------
    # Formats
    # --------------------------------------------------
    title_format = workbook.add_format({
        'bold': True,
        'font_size': 16,
        'align': 'center',
        'valign': 'vcenter'
    })

    subtitle_format = workbook.add_format({
        'italic': True,
        'font_size': 10,
        'align': 'center'
    })

    header_format = workbook.add_format({
        'bold': True,
        'text_wrap': True,
        'border': 1,
        'align': 'center',
        'valign': 'middle',
        'bg_color': '#D9E1F2'
    })

    cell_format = workbook.add_format({
        'border': 1,
        'valign': 'top'
    })

    alt_row_format = workbook.add_format({
        'border': 1,
        'bg_color': '#F9F9F9'
    })

    filter_label_format = workbook.add_format({
        'bold': True
    })

    no_data_format = workbook.add_format({
        'align': 'center',
        'italic': True
    })

    # --------------------------------------------------
    # Report Title
    # --------------------------------------------------
    total_columns = len(df.columns)

    worksheet.merge_range(
        0, 0, 0, total_columns - 1,
        'Return Log Report',
        title_format
    )

    worksheet.merge_range(
        1, 0, 1, total_columns - 1,
        f'Generated on: {timezone.now().strftime("%d-%m-%Y %H:%M")}',
        subtitle_format
    )

    # Convert filter IDs → names (ONLY for display)
    filters = normalize_export_filters(filters)

    # --------------------------------------------------
    # Applied Filters
    # --------------------------------------------------
    worksheet.write(3, 0, 'Applied Filters:', filter_label_format)

    col = 1
    worksheet.write(3, col, f'List Type: {list_type.title()}')
    
    col += 1

    for key, value in filters.items():
        if value:
            worksheet.write(
                3,
                col,
                f'{key.replace("_", " ").title()}: {value}'
            )
            col += 1

    # --------------------------------------------------
    # Header Styling
    # --------------------------------------------------
    for col_idx, col_name in enumerate(df.columns):
        worksheet.write(start_row, col_idx, col_name, header_format)

    # --------------------------------------------------
    # Data Rows Styling (alternate rows)
    # --------------------------------------------------
    for row_idx in range(len(df)):
        excel_row = start_row + 1 + row_idx
        row_format = alt_row_format if row_idx % 2 else cell_format

        for col_idx in range(total_columns):
            worksheet.write(
                excel_row,
                col_idx,
                df.iloc[row_idx, col_idx],
                row_format
            )

    # --------------------------------------------------
    # Auto Column Width
    # --------------------------------------------------
    for col_idx, column in enumerate(df.columns):
        max_len = max(
            df[column].astype(str).map(len).max() if not df.empty else 10,
            len(column)
        )
        worksheet.set_column(col_idx, col_idx, min(max_len + 3, 50))

    # --------------------------------------------------
    # Freeze Header & Enable AutoFilter
    # --------------------------------------------------
    worksheet.freeze_panes(start_row + 1, 0)

    if not df.empty:
        worksheet.autofilter(
            start_row,
            0,
            start_row + len(df),
            total_columns - 1
        )

    # --------------------------------------------------
    # No Data Message
    # --------------------------------------------------
    if df.empty:
        worksheet.merge_range(
            start_row + 1, 0,
            start_row + 2, total_columns - 1,
            'No return logs found for selected filters',
            no_data_format
        )

def export_google_metadata_to_excel(writer, db, book_ids, list_type, filters):

    # --------------------------------------------------
    # Get data (same source as UI)
    # --------------------------------------------------
    view = TabDataView()
    response = view.get_google_metadata_data(db, book_ids, list_type, filters)
    data = response.get('data', [])

    # --------------------------------------------------
    # Prepare Data
    # --------------------------------------------------
    rows = []
    for item in data:
        rows.append({
            'Title': item.get('title', ''),
            'ISBN': item.get('isbn', ''),
            'Created At': item.get('created_at', ''),
            'Metadata (JSON)': item.get('details', ''),
        })

    df = pd.DataFrame(rows)

    sheet_name = 'Google Metadata'
    start_row = 6

    df.to_excel(
        writer,
        sheet_name=sheet_name,
        index=False,
        startrow=start_row
    )

    # --------------------------------------------------
    # Workbook & Worksheet
    # --------------------------------------------------
    workbook = writer.book
    worksheet = writer.sheets[sheet_name]

    # --------------------------------------------------
    # Formats
    # --------------------------------------------------
    title_format = workbook.add_format({
        'bold': True,
        'font_size': 16,
        'align': 'center',
        'valign': 'vcenter'
    })

    subtitle_format = workbook.add_format({
        'italic': True,
        'font_size': 10,
        'align': 'center'
    })

    header_format = workbook.add_format({
        'bold': True,
        'text_wrap': True,
        'border': 1,
        'align': 'center',
        'valign': 'middle',
        'bg_color': '#D9E1F2'
    })

    cell_format = workbook.add_format({
        'border': 1,
        'valign': 'top'
    })

    alt_row_format = workbook.add_format({
        'border': 1,
        'bg_color': '#F9F9F9'
    })

    filter_label_format = workbook.add_format({
        'bold': True
    })

    no_data_format = workbook.add_format({
        'align': 'center',
        'italic': True
    })

    # --------------------------------------------------
    # Report Title
    # --------------------------------------------------
    total_columns = len(df.columns)

    worksheet.merge_range(
        0, 0, 0, total_columns - 1,
        'Google Metadata Report',
        title_format
    )

    worksheet.merge_range(
        1, 0, 1, total_columns - 1,
        f'Generated on: {timezone.now().strftime("%d-%m-%Y %H:%M")}',
        subtitle_format
    )

    # Convert filter IDs → names (ONLY for display)
    filters = normalize_export_filters(filters)

    # --------------------------------------------------
    # Applied Filters
    # --------------------------------------------------
    worksheet.write(3, 0, 'Applied Filters:', filter_label_format)

    col = 1
    for key, value in filters.items():
        if value:
            worksheet.write(
                3,
                col,
                f'{key.replace("_", " ").title()}: {value}'
            )
            col += 1

    # --------------------------------------------------
    # Header Styling
    # --------------------------------------------------
    for col_idx, col_name in enumerate(df.columns):
        worksheet.write(start_row, col_idx, col_name, header_format)

    # --------------------------------------------------
    # Data Rows Styling (alternate rows)
    # --------------------------------------------------
    for row_idx in range(len(df)):
        excel_row = start_row + 1 + row_idx
        row_format = alt_row_format if row_idx % 2 else cell_format

        for col_idx in range(total_columns):
            worksheet.write(
                excel_row,
                col_idx,
                df.iloc[row_idx, col_idx],
                row_format
            )

    # --------------------------------------------------
    # Auto Column Width
    # --------------------------------------------------
    for col_idx, column in enumerate(df.columns):
        max_len = max(
            df[column].astype(str).map(len).max() if not df.empty else 10,
            len(column)
        )
        worksheet.set_column(col_idx, col_idx, min(max_len + 3, 70))

    # --------------------------------------------------
    # Freeze Header & Enable AutoFilter
    # --------------------------------------------------
    worksheet.freeze_panes(start_row + 1, 0)

    if not df.empty:
        worksheet.autofilter(
            start_row,
            0,
            start_row + len(df),
            total_columns - 1
        )

    # --------------------------------------------------
    # No Data Message
    # --------------------------------------------------
    if df.empty:
        worksheet.merge_range(
            start_row + 1, 0,
            start_row + 2, total_columns - 1,
            'No Google metadata found for selected filters',
            no_data_format
        )

def export_loc_metadata_to_excel(writer, db, book_ids, list_type, filters):

    # --------------------------------------------------
    # Get data (same source as UI)
    # --------------------------------------------------
    view = TabDataView()
    response = view.get_loc_metadata_data(db, book_ids, list_type, filters)
    data = response.get('data', [])

    # --------------------------------------------------
    # Prepare Data
    # --------------------------------------------------
    rows = []
    for item in data:
        rows.append({
            'Title': item.get('title', ''),
            'ISBN': item.get('isbn', ''),
            'Created At': item.get('created_at', ''),
            'LOC Metadata (JSON)': item.get('details', ''),
        })

    df = pd.DataFrame(rows)

    sheet_name = 'LOC Metadata'
    start_row = 6

    df.to_excel(
        writer,
        sheet_name=sheet_name,
        index=False,
        startrow=start_row
    )

    # --------------------------------------------------
    # Workbook & Worksheet
    # --------------------------------------------------
    workbook = writer.book
    worksheet = writer.sheets[sheet_name]

    # --------------------------------------------------
    # Formats
    # --------------------------------------------------
    title_format = workbook.add_format({
        'bold': True,
        'font_size': 16,
        'align': 'center',
        'valign': 'vcenter'
    })

    subtitle_format = workbook.add_format({
        'italic': True,
        'font_size': 10,
        'align': 'center'
    })

    header_format = workbook.add_format({
        'bold': True,
        'text_wrap': True,
        'border': 1,
        'align': 'center',
        'valign': 'middle',
        'bg_color': '#D9E1F2'
    })

    cell_format = workbook.add_format({
        'border': 1,
        'valign': 'top'
    })

    alt_row_format = workbook.add_format({
        'border': 1,
        'bg_color': '#F9F9F9'
    })

    filter_label_format = workbook.add_format({
        'bold': True
    })

    no_data_format = workbook.add_format({
        'align': 'center',
        'italic': True
    })

    # --------------------------------------------------
    # Report Title
    # --------------------------------------------------
    total_columns = len(df.columns)

    worksheet.merge_range(
        0, 0, 0, total_columns - 1,
        'LOC Metadata Report',
        title_format
    )

    worksheet.merge_range(
        1, 0, 1, total_columns - 1,
        f'Generated on: {timezone.now().strftime("%d-%m-%Y %H:%M")}',
        subtitle_format
    )

    # Convert filter IDs → names (ONLY for display)
    filters = normalize_export_filters(filters)
    
    # --------------------------------------------------
    # Applied Filters
    # --------------------------------------------------
    worksheet.write(3, 0, 'Applied Filters:', filter_label_format)

    col = 1
    for key, value in filters.items():
        if value:
            worksheet.write(
                3,
                col,
                f'{key.replace("_", " ").title()}: {value}'
            )
            col += 1

    # --------------------------------------------------
    # Header Styling
    # --------------------------------------------------
    for col_idx, col_name in enumerate(df.columns):
        worksheet.write(start_row, col_idx, col_name, header_format)

    # --------------------------------------------------
    # Data Rows Styling (alternate rows)
    # --------------------------------------------------
    for row_idx in range(len(df)):
        excel_row = start_row + 1 + row_idx
        row_format = alt_row_format if row_idx % 2 else cell_format

        for col_idx in range(total_columns):
            worksheet.write(
                excel_row,
                col_idx,
                df.iloc[row_idx, col_idx],
                row_format
            )

    # --------------------------------------------------
    # Auto Column Width
    # --------------------------------------------------
    for col_idx, column in enumerate(df.columns):
        max_len = max(
            df[column].astype(str).map(len).max() if not df.empty else 10,
            len(column)
        )
        worksheet.set_column(col_idx, col_idx, min(max_len + 3, 70))

    # --------------------------------------------------
    # Freeze Header & Enable AutoFilter
    # --------------------------------------------------
    worksheet.freeze_panes(start_row + 1, 0)
    if not df.empty:
        worksheet.autofilter(
            start_row,
            0,
            start_row + len(df),
            total_columns - 1
        )

    # --------------------------------------------------
    # No Data Message
    # --------------------------------------------------
    if df.empty:
        worksheet.merge_range(
            start_row + 1, 0,
            start_row + 2, total_columns - 1,
            'No LOC metadata found for selected filters',
            no_data_format
        )

class ExportReportView(ReportBaseView):
    """Export book report (single tab or all tabs) to Excel"""

    def get(self, request):
        export_type = request.GET.get('type', 'all-tabs')
        book_ids = request.GET.getlist('book_ids')
        list_type = request.GET.get('list_type', 'title')

        filters_json = request.GET.get('filters', '{}')
        tab_filters_json = request.GET.get('tab_filters', '{}')

        # ----------------------------------
        # Normalize book_ids
        # ----------------------------------
        if len(book_ids) == 1 and ',' in book_ids[0]:
            book_ids = [
                int(i) for i in book_ids[0].split(',')
                if i.strip().isdigit()
            ]
        else:
            book_ids = [int(i) for i in book_ids if str(i).isdigit()]

        # ----------------------------------
        # Parse filters safely
        # ----------------------------------
        try:
            filters = json.loads(filters_json)
        except (TypeError, ValueError):
            filters = {}

        try:
            tab_filters = json.loads(tab_filters_json)
        except (TypeError, ValueError):
            tab_filters = {}

        db = self.get_library_db()

        # ----------------------------------
        # Create temp Excel file
        # ----------------------------------
        with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
            output_path = tmp.name

        try:
            with pd.ExcelWriter(output_path, engine="xlsxwriter") as writer:

                if export_type == 'all-tabs':
                    self.export_all_tabs(
                        writer=writer,
                        db=db,
                        book_ids=book_ids,
                        list_type=list_type,
                        tab_filters=tab_filters
                    )
                else:
                    self.export_single_tab(
                        writer=writer,
                        export_type=export_type,
                        db=db,
                        book_ids=book_ids,
                        list_type=list_type,
                        filters=tab_filters
                    )

            # ----------------------------------
            # Response
            # ----------------------------------
            with open(output_path, 'rb') as f:
                response = HttpResponse(
                    f.read(),
                    content_type=(
                        'application/vnd.openxmlformats-officedocument.'
                        'spreadsheetml.sheet'
                    )
                )

            if export_type == 'all-tabs':
                filename = 'book_report_all_tabs.xlsx'
            else:
                filename = f'book_report_{export_type.replace("-", "_")}.xlsx'

            response['Content-Disposition'] = (
                f'attachment; filename="{filename}"'
            )

            return response

        except Exception as e:
            return JsonResponse(
                {'error': 'Export failed', 'details': str(e)},
                status=500
            )

        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)

    # ======================================================
    # EXPORT HELPERS
    # ======================================================

    def export_all_tabs(self, writer, db, book_ids, list_type, tab_filters):
        """Export all tabs into separate sheets"""

        export_map = self.get_export_map()

        for tab_name, export_func in export_map.items():
            export_func(
                writer=writer,
                db=db,
                book_ids=book_ids,
                list_type=list_type,
                filters=tab_filters.get(tab_name, {})
            )

    def export_single_tab(self, writer, export_type, db, book_ids, list_type, filters):
        """Export a single tab"""

        export_func = self.get_export_map().get(export_type)

        if export_func:
            export_func(
                writer=writer,
                db=db,
                book_ids=book_ids,
                list_type=list_type,
                filters=filters
            )
        else:
            workbook = writer.book
            worksheet = workbook.add_worksheet(
                export_type.replace('-', ' ').title()
            )
            worksheet.write(0, 0, 'No data available')

    def get_export_map(self):
        """
        Central tab → export function mapping
        """
        return {
            'catalogue': export_catalogue_to_excel,
            'accession': export_accession_to_excel,
            'circulation': export_circulation_to_excel,
            'loan': export_loan_to_excel,
            'circulation-transaction': export_circulation_transaction_to_excel,
            'supplier': export_supplier_to_excel,
            'review': export_review_to_excel,
            'return-log': export_return_log_to_excel,
            'google-metadata': export_google_metadata_to_excel,
            'loc-metadata': export_loc_metadata_to_excel,
        }

class ExportAllDataView(ReportBaseView):
    """Export selected book report tabs to Excel"""

    def get(self, request):
        book_ids = request.GET.getlist('book_ids')
        selected_tabs = request.GET.getlist('tabs')
        filename = request.GET.get('filename', 'book_report')
        list_type = request.GET.get('list_type', 'title')

        filters_json = request.GET.get('filters', '{}')
        tab_filters_json = request.GET.get('tab_filters', '{}')

        # ----------------------------------
        # Normalize book_ids
        # ----------------------------------
        if len(book_ids) == 1 and ',' in book_ids[0]:
            book_ids = [
                int(i) for i in book_ids[0].split(',')
                if i.strip().isdigit()
            ]
        else:
            book_ids = [int(i) for i in book_ids if str(i).isdigit()]

        if not book_ids:
            return JsonResponse({'error': 'No books selected'}, status=400)

        if not selected_tabs:
            return JsonResponse({'error': 'No tabs selected'}, status=400)

        try:
            tab_filters = json.loads(tab_filters_json)
        except Exception:
            tab_filters = {}

        db = self.get_library_db()
        export_map = self.get_export_map()

        # ----------------------------------
        # Temp file
        # ----------------------------------
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp:
            output_path = tmp.name

        try:
            with pd.ExcelWriter(output_path, engine='xlsxwriter') as writer:

                for tab in selected_tabs:
                    export_func = export_map.get(tab)
                    if not export_func:
                        continue

                    export_func(
                        writer=writer,
                        db=db,
                        book_ids=book_ids,
                        list_type=list_type,
                        filters=tab_filters.get(tab, {})
                    )

            with open(output_path, 'rb') as f:
                response = HttpResponse(
                    f.read(),
                    content_type=(
                        'application/vnd.openxmlformats-officedocument.'
                        'spreadsheetml.sheet'
                    )
                )

            response['Content-Disposition'] = (
                f'attachment; filename="{filename}.xlsx"'
            )
            return response

        except Exception as e:
            import traceback
            traceback.print_exc() 
            return JsonResponse(
                {'error': 'Export failed', 'details': str(e)},
                status=500
            )

        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)

    def get_export_map(self):
        return {
            'catalogue': export_catalogue_to_excel,
            'accession': export_accession_to_excel,
            'circulation': export_circulation_to_excel,
            'loan': export_loan_to_excel,
            'circulation-transaction': export_circulation_transaction_to_excel,
            'supplier': export_supplier_to_excel,
            'review': export_review_to_excel,
            'return-log': export_return_log_to_excel,
            'google-metadata': export_google_metadata_to_excel,
            'loc-metadata': export_loc_metadata_to_excel,
        }
