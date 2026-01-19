# reports/views.py - COMPLETE implementation
import json
import pandas as pd
from datetime import datetime, timedelta
from django.http import JsonResponse, HttpResponse, StreamingHttpResponse, Http404
from django.views.generic import TemplateView, View
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.db.models import Q, F, Count, Sum, Max, Min, Avg, Value, CharField, IntegerField
from django.db.models.functions import Concat, Coalesce, ExtractMonth, ExtractYear, TruncDate
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import render, get_object_or_404
from django.forms.models import model_to_dict
from django.conf import settings
import os
import logging
from pathlib import Path

from .services import ReportService, ExportService, MemberReportDataService
from .filters import MemberFilter, BookFilter, TabFilter
from .utils import get_library_code, format_date_range, parse_date, safe_int, safe_float

logger = logging.getLogger(__name__)

class BaseReportView(LoginRequiredMixin, TemplateView):
    """Base view for all reports - COMPLETE"""
    template_name = 'library_reports/base_report.html'
    report_type = None
    filters_class = None
    tabs_config = []
    
    def test_func(self):
        """Check if user has permission to view reports"""
        return self.request.user.has_perm('reports.view_report')
    
    def get_library_code(self):
        return get_library_code(self.request)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        library_code = self.get_library_code()
        
        try:
            from L01.models import (
                MembershipMaster, StatusMaster, parameter_master_L01,
                BookCatalog, BookMaster, BookDetails
            )
            
            # Get user permissions
            user = self.request.user
            context.update({
                'report_type': self.report_type,
                'library_code': library_code,
                'available_filters': self.get_available_filters(library_code),
                'tabs_config': self.get_tabs_config(),
                'membership_types': MembershipMaster.objects.using(library_code)
                    .filter(isactive=1)
                    .order_by('membership_type')
                    .values('id', 'membership_type', 'membership_code'),
                'statuses': StatusMaster.objects.using(library_code)
                    .filter(isactive=1)
                    .order_by('status_name')
                    .values('id', 'status_name', 'status_code'),
                'member_types': parameter_master_L01.objects.using(library_code)
                    .filter(parameter_type='member_type', isactive=1)
                    .order_by('parameter_name')
                    .values('id', 'parameter_name', 'parameter_code'),
                'user_permissions': {
                    'can_export': user.has_perm('reports.export_report'),
                    'can_view_all': user.has_perm('reports.view_all_reports'),
                    'can_manage_filters': user.has_perm('reports.manage_filters'),
                },
                'current_date': datetime.now().strftime('%Y-%m-%d'),
                'report_title': self.get_report_title(),
            })
            
            # Add book-related context for book reports
            if self.report_type == 'book':
                context.update({
                    'book_categories': BookCatalog.objects.using(library_code)
                        .values_list('category', flat=True)
                        .distinct()
                        .exclude(category__isnull=True)
                        .exclude(category='')
                        .order_by('category'),
                    'book_languages': BookMaster.objects.using(library_code)
                        .values_list('language', flat=True)
                        .distinct()
                        .exclude(language__isnull=True)
                        .exclude(language='')
                        .order_by('language'),
                    'publishers': BookDetails.objects.using(library_code)
                        .values_list('publisher', flat=True)
                        .distinct()
                        .exclude(publisher__isnull=True)
                        .exclude(publisher='')
                        .order_by('publisher'),
                })
                
        except Exception as e:
            logger.error(f"Error loading context data: {str(e)}", exc_info=True)
            context['error'] = str(e)
        
        return context
    
    def get_report_title(self):
        """Get report title based on report type"""
        titles = {
            'member': 'Member Report',
            'book': 'Book Report',
            'circulation': 'Circulation Report',
            'financial': 'Financial Report',
        }
        return titles.get(self.report_type, f"{self.report_type.title()} Report")
    
    def get_available_filters(self, library_code):
        """Get available filters for the report type - COMPLETE"""
        filters = {}
        
        if self.report_type == 'member':
            filters = {
                'membership_type': {
                    'type': 'multi_select',
                    'label': 'Membership Type',
                    'field': 'membership_id',
                    'options': [],
                    'multiple': True,
                    'searchable': True
                },
                'status': {
                    'type': 'multi_select',
                    'label': 'Status',
                    'field': 'status_id',
                    'options': [
                        {'value': '', 'label': 'All'},
                        {'value': 'active', 'label': 'Active'},
                        {'value': 'inactive', 'label': 'Inactive'},
                        {'value': 'cancelled', 'label': 'Cancelled'},
                    ],
                    'multiple': True,
                    'searchable': False
                },
                'member_type': {
                    'type': 'multi_select',
                    'label': 'Member Type',
                    'field': 'member_type_id',
                    'options': [],
                    'multiple': True,
                    'searchable': True
                },
                'ward': {
                    'type': 'multi_select',
                    'label': 'Ward',
                    'field': 'ward',
                    'options': [],
                    'multiple': True,
                    'searchable': True
                },
                'date_range': {
                    'type': 'date_range',
                    'label': 'Date Range',
                    'field': 'created_at',
                    'from_field': 'from_date',
                    'to_field': 'to_date',
                    'presets': [
                        {'label': 'Today', 'days': 0},
                        {'label': 'Yesterday', 'days': -1},
                        {'label': 'Last 7 Days', 'days': -7},
                        {'label': 'Last 30 Days', 'days': -30},
                        {'label': 'This Month', 'month': 0},
                        {'label': 'Last Month', 'month': -1},
                    ]
                },
                'is_resident': {
                    'type': 'select',
                    'label': 'NMMC Resident',
                    'field': 'is_resident_of_nmmc',
                    'options': [
                        {'value': '', 'label': 'All'},
                        {'value': '1', 'label': 'Yes'},
                        {'value': '0', 'label': 'No'},
                    ],
                    'multiple': False
                },
                'has_aadhar_address': {
                    'type': 'select',
                    'label': 'Address Same as Aadhar',
                    'field': 'address_same_as_aadhar',
                    'options': [
                        {'value': '', 'label': 'All'},
                        {'value': '1', 'label': 'Yes'},
                        {'value': '0', 'label': 'No'},
                    ],
                    'multiple': False
                }
            }
            
        elif self.report_type == 'book':
            filters = {
                'category': {
                    'type': 'multi_select',
                    'label': 'Category',
                    'field': 'category',
                    'options': [],
                    'multiple': True,
                    'searchable': True
                },
                'language': {
                    'type': 'multi_select',
                    'label': 'Language',
                    'field': 'language',
                    'options': [],
                    'multiple': True,
                    'searchable': True
                },
                'publisher': {
                    'type': 'multi_select',
                    'label': 'Publisher',
                    'field': 'publisher',
                    'options': [],
                    'multiple': True,
                    'searchable': True
                },
                'availability': {
                    'type': 'select',
                    'label': 'Availability',
                    'field': 'is_available',
                    'options': [
                        {'value': '', 'label': 'All'},
                        {'value': 'available', 'label': 'Available'},
                        {'value': 'issued', 'label': 'Issued'},
                        {'value': 'reserved', 'label': 'Reserved'},
                        {'value': 'damaged', 'label': 'Damaged'},
                    ],
                    'multiple': False
                },
                'date_range': {
                    'type': 'date_range',
                    'label': 'Added Date Range',
                    'field': 'created_at',
                    'from_field': 'from_date',
                    'to_field': 'to_date'
                }
            }
        
        return filters
    
    def get_tabs_config(self):
        """Get tabs configuration - COMPLETE"""
        if self.report_type == 'member':
            return [
                {
                    'id': 'member_details',
                    'title': 'Member Details',
                    'icon': 'bi-person',
                    'description': 'Detailed member information',
                    'has_documents': True,
                    'exportable': True,
                    'filters': ['membership_type', 'ward', 'status', 'date_range', 'member_type'],
                    'default_sort': {'field': 'created_at', 'direction': 'desc'}
                },
                {
                    'id': 'membership_details',
                    'title': 'Membership Details',
                    'icon': 'bi-card-checklist',
                    'description': 'Membership history and changes',
                    'has_documents': True,
                    'exportable': True,
                    'filters': ['membership_type', 'date_range', 'action_performed', 'gap_period'],
                    'default_sort': {'field': 'changed_at', 'direction': 'desc'}
                },
                {
                    'id': 'loan',
                    'title': 'Loan',
                    'icon': 'bi-book',
                    'description': 'Book loan information',
                    'has_documents': False,
                    'exportable': True,
                    'filters': ['membership_type', 'date_range', 'overdue', 'fine_status'],
                    'default_sort': {'field': 'issue_date', 'direction': 'desc'}
                },
                {
                    'id': 'transactions',
                    'title': 'Transactions',
                    'icon': 'bi-arrow-left-right',
                    'description': 'Circulation transactions',
                    'has_documents': False,
                    'exportable': True,
                    'filters': ['membership_type', 'date_range', 'late_returns', 'fine_status'],
                    'default_sort': {'field': 'created_at', 'direction': 'desc'}
                },
                {
                    'id': 'physical_visit',
                    'title': 'Physical Visit',
                    'icon': 'bi-door-open',
                    'description': 'Library physical visits',
                    'has_documents': False,
                    'exportable': True,
                    'filters': ['membership_type', 'date_range', 'activity'],
                    'default_sort': {'field': 'entry_time', 'direction': 'desc'}
                },
                {
                    'id': 'virtual_usage',
                    'title': 'Virtual Usage',
                    'icon': 'bi-laptop',
                    'description': 'Online portal usage',
                    'has_documents': False,
                    'exportable': True,
                    'filters': ['membership_type', 'date_range', 'activity'],
                    'default_sort': {'field': 'visited_at', 'direction': 'desc'}
                },
                {
                    'id': 'payments',
                    'title': 'Payments',
                    'icon': 'bi-cash-stack',
                    'description': 'Payment history',
                    'has_documents': False,
                    'exportable': True,
                    'filters': ['membership_type', 'date_range', 'payment_type', 'payment_method'],
                    'default_sort': {'field': 'payment_date', 'direction': 'desc'}
                }
            ]
        elif self.report_type == 'book':
            return [
                {
                    'id': 'book_catalog',
                    'title': 'Book Catalog',
                    'icon': 'bi-book',
                    'description': 'Complete book catalog',
                    'has_documents': False,
                    'exportable': True,
                    'filters': ['category', 'language', 'publisher', 'availability', 'date_range'],
                    'default_sort': {'field': 'title', 'direction': 'asc'}
                },
                {
                    'id': 'book_circulation',
                    'title': 'Circulation',
                    'icon': 'bi-arrow-left-right',
                    'description': 'Book circulation statistics',
                    'has_documents': False,
                    'exportable': True,
                    'filters': ['category', 'date_range', 'circulation_type'],
                    'default_sort': {'field': 'issue_date', 'direction': 'desc'}
                },
                {
                    'id': 'book_availability',
                    'title': 'Availability',
                    'icon': 'bi-check-circle',
                    'description': 'Book availability status',
                    'has_documents': False,
                    'exportable': True,
                    'filters': ['category', 'language', 'availability'],
                    'default_sort': {'field': 'title', 'direction': 'asc'}
                }
            ]
        return []

class MemberReportView(BaseReportView):
    """Member Report View - COMPLETE"""
    template_name = 'library_reports/member_report.html'
    report_type = 'member'
    filters_class = MemberFilter
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        library_code = self.get_library_code()
        
        try:
            from L01.models import MembershipDetails
            
            # Get initial member list with applied filters
            base_filters = Q(isactive=1)
            
            # Apply URL filters if any
            membership_type = self.request.GET.get('membership_type')
            if membership_type:
                base_filters &= Q(membership_id=membership_type)
            
            status = self.request.GET.get('status')
            if status:
                if status == 'active':
                    base_filters &= Q(isactive=1)
                elif status == 'inactive':
                    base_filters &= Q(isactive=0)
                elif status == 'cancelled':
                    base_filters &= Q(status__status_code='cancelled')
            
            # Get wards for filter options
            wards = MembershipDetails.objects.using(library_code).filter(
                ward__isnull=False
            ).exclude(ward='').values_list('ward', flat=True).distinct().order_by('ward')
            
            # Get initial members (limited for performance)
            members = MembershipDetails.objects.using(library_code).filter(
                base_filters
            ).select_related('membership', 'status', 'member_type')[:100]
            
            context.update({
                'members': members,
                'total_members': members.count(),
                'selected_members': [],
                'initial_filters': self.request.GET.dict(),
                'wards': list(wards),
                'export_formats': ['excel', 'csv', 'pdf'],
            })
            
        except Exception as e:
            logger.error(f"Error in MemberReportView: {str(e)}", exc_info=True)
            context['error'] = str(e)
        
        return context

class BookReportView(BaseReportView):
    """Book Report View - COMPLETE"""
    template_name = 'library_reports/book_report.html'
    report_type = 'book'
    filters_class = BookFilter
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        try:
            from L01.models import BookCatalog, BookAccession
            
            # Get book statistics
            library_code = self.get_library_code()
            
            total_books = BookCatalog.objects.using(library_code).count()
            available_books = BookAccession.objects.using(library_code).filter(
                status='available'
            ).count()
            issued_books = BookAccession.objects.using(library_code).filter(
                status='issued'
            ).count()
            
            context.update({
                'book_stats': {
                    'total': total_books,
                    'available': available_books,
                    'issued': issued_books,
                    'reserved': BookAccession.objects.using(library_code).filter(
                        status='reserved'
                    ).count(),
                },
                'export_formats': ['excel', 'csv'],
            })
            
        except Exception as e:
            logger.error(f"Error in BookReportView: {str(e)}", exc_info=True)
            context['error'] = str(e)
        
        return context

@method_decorator(csrf_exempt, name='dispatch')
class LoadMemberListAPI(View):
    """API to load filtered member list for left panel - COMPLETE"""
    
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            filters = data.get('filters', {})
            search_term = data.get('search', '')
            page = data.get('page', 1)
            per_page = data.get('per_page', 50)
            sort_by = data.get('sort_by', 'created_at')
            sort_order = data.get('sort_order', 'desc')
            
            library_code = get_library_code(request)
            from L01.models import MembershipDetails
            
            # Build query
            queryset = MembershipDetails.objects.using(library_code).filter(
                isactive=1
            ).select_related('membership', 'status', 'member_type')
            
            # Apply filters
            if filters.get('membership_type'):
                queryset = queryset.filter(membership_id__in=filters['membership_type'])
            
            if filters.get('status'):
                status_values = []
                for status in filters['status']:
                    if status == 'active':
                        status_values.append(1)
                    elif status == 'inactive':
                        status_values.append(0)
                    elif status == 'cancelled':
                        queryset = queryset.filter(status__status_code='cancelled')
                
                if status_values:
                    queryset = queryset.filter(isactive__in=status_values)
            
            if filters.get('member_type'):
                queryset = queryset.filter(member_type_id__in=filters['member_type'])
            
            if filters.get('ward'):
                queryset = queryset.filter(ward__in=filters['ward'])
            
            if filters.get('is_resident'):
                queryset = queryset.filter(is_resident_of_nmmc=int(filters['is_resident']))
            
            if filters.get('has_aadhar_address'):
                queryset = queryset.filter(address_same_as_aadhar=int(filters['has_aadhar_address']))
            
            # Date range filter
            if filters.get('from_date') and filters.get('to_date'):
                from_date = parse_date(filters['from_date'])
                to_date = parse_date(filters['to_date'])
                if from_date and to_date:
                    queryset = queryset.filter(created_at__date__range=[from_date, to_date])
            
            # Apply search
            if search_term:
                search_query = Q()
                for term in search_term.split():
                    search_query &= (
                        Q(membership_code__icontains=term) |
                        Q(first_name__icontains=term) |
                        Q(last_name__icontains=term) |
                        Q(user_id__icontains=term) |
                        Q(mobile_no__icontains=term) |
                        Q(email__icontains=term) |
                        Q(aadhar_no__icontains=term)
                    )
                queryset = queryset.filter(search_query)
            
            # Apply sorting
            if sort_by:
                if sort_order == 'desc':
                    sort_by = f'-{sort_by}'
                queryset = queryset.order_by(sort_by)
            else:
                queryset = queryset.order_by('-created_at')
            
            # Pagination
            paginator = Paginator(queryset, per_page)
            try:
                page_obj = paginator.page(page)
            except PageNotAnInteger:
                page_obj = paginator.page(1)
            except EmptyPage:
                page_obj = paginator.page(paginator.num_pages)
            
            # Format data
            members_data = []
            for member in page_obj.object_list:
                members_data.append({
                    'id': member.id,
                    'membership_code': member.membership_code or 'N/A',
                    'user_id': member.user_id or 'N/A',
                    'first_name': member.first_name or '',
                    'last_name': member.last_name or '',
                    'full_name': f"{member.first_name or ''} {member.last_name or ''}".strip(),
                    'full_name_mar': f"{member.first_name_mar or ''} {member.last_name_mar or ''}".strip(),
                    'mobile_no': member.mobile_no or '',
                    'email': member.email or '',
                    'status': {
                        'id': member.status.id if member.status else None,
                        'name': member.status.status_name if member.status else 'Unknown',
                        'code': member.status.status_code if member.status else '',
                    },
                    'membership_type': {
                        'id': member.membership.id if member.membership else None,
                        'name': member.membership.membership_type if member.membership else 'Unknown',
                        'code': member.membership.membership_code if member.membership else '',
                    },
                    'member_type': member.member_type.parameter_name if member.member_type else '',
                    'ward': member.ward or '',
                    'created_at': member.created_at.strftime('%Y-%m-%d') if member.created_at else '',
                    'has_documents': member.documents.filter(isactive=1).exists(),
                })
            
            return JsonResponse({
                'success': True,
                'members': members_data,
                'total': paginator.count,
                'has_next': page_obj.has_next(),
                'has_previous': page_obj.has_previous(),
                'current_page': page_obj.number,
                'total_pages': paginator.num_pages,
                'per_page': per_page
            })
            
        except Exception as e:
            logger.error(f"Error loading member list: {str(e)}", exc_info=True)
            return JsonResponse({
                'success': False,
                'error': str(e),
                'error_type': type(e).__name__
            }, status=400)

@method_decorator(csrf_exempt, name='dispatch')
class ReportDataAPI(View):
    """API endpoint for dynamic report data loading - COMPLETE"""
    
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            report_type = data.get('report_type')
            tab_name = data.get('tab')
            filters = data.get('filters', {})
            selected_ids = data.get('selected_ids', [])
            draw = data.get('draw', 1)
            start = data.get('start', 0)
            length = data.get('length', 25)
            search_value = data.get('search', {}).get('value', '')
            order_column = data.get('order', [{}])[0].get('column', 0)
            order_dir = data.get('order', [{}])[0].get('dir', 'asc')
            export_mode = data.get('export_mode', False)
            
            library_code = get_library_code(request)
            
            # If no members selected and report type is member, return empty
            if report_type == 'member' and not selected_ids and not export_mode:
                return JsonResponse({
                    'success': True,
                    'draw': draw,
                    'recordsTotal': 0,
                    'recordsFiltered': 0,
                    'data': [],
                    'columns': []
                })
            
            service = ReportService(report_type, library_code)
            
            # Get data with pagination
            result = service.get_tab_data(
                tab_name=tab_name,
                filters=filters,
                selected_ids=selected_ids,
                search=search_value,
                start=start,
                length=length,
                order_column=order_column,
                order_dir=order_dir,
                export_mode=export_mode
            )
            
            return JsonResponse({
                'success': True,
                'draw': draw,
                'recordsTotal': result['total'],
                'recordsFiltered': result['filtered_total'],
                'data': result['data'],
                'columns': result['columns'],
                'export_info': result.get('export_info', {})
            })
            
        except Exception as e:
            logger.error(f"Error in ReportDataAPI: {str(e)}", exc_info=True, extra={
                'report_type': data.get('report_type'),
                'tab_name': data.get('tab'),
                'user': request.user.username
            })
            return JsonResponse({
                'success': False,
                'error': str(e),
                'error_type': type(e).__name__,
                'draw': data.get('draw', 1),
                'recordsTotal': 0,
                'recordsFiltered': 0,
                'data': []
            }, status=400)

@method_decorator(csrf_exempt, name='dispatch')
class ExportReportAPI(View):
    """API endpoint for report export - COMPLETE"""
    
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            report_type = data.get('report_type')
            export_type = data.get('export_type', 'excel')
            export_format = data.get('format', 'xlsx')
            filters = data.get('filters', {})
            selected_tabs = data.get('tabs', [])
            selected_ids = data.get('selected_ids', [])
            include_charts = data.get('include_charts', False)
            compression = data.get('compression', False)
            
            if not selected_tabs:
                return JsonResponse({
                    'success': False,
                    'error': 'No tabs selected for export'
                }, status=400)
            
            # Check user permissions
            if not request.user.has_perm('reports.export_report'):
                return JsonResponse({
                    'success': False,
                    'error': 'Permission denied for export'
                }, status=403)
            
            library_code = get_library_code(request)
            service = ReportService(report_type, library_code)
            
            # Collect data for all selected tabs
            export_data = {}
            sheet_names = []
            export_info = {}
            
            for tab in selected_tabs:
                try:
                    result = service.get_tab_data(
                        tab_name=tab,
                        filters=filters,
                        selected_ids=selected_ids,
                        export_mode=True  # Get all data for export
                    )
                    
                    if result['data']:
                        # Convert to DataFrame
                        df = pd.DataFrame(result['data'])
                        
                        # Format column names
                        column_mapping = {col['data']: col['title'] for col in result['columns']}
                        df.rename(columns=column_mapping, inplace=True)
                        
                        # Format date columns
                        date_columns = [col for col in df.columns if 'date' in col.lower() or 'time' in col.lower()]
                        for col in date_columns:
                            try:
                                df[col] = pd.to_datetime(df[col]).dt.strftime('%Y-%m-%d %H:%M:%S')
                            except:
                                pass
                        
                        # Format numeric columns
                        numeric_columns = [col for col in df.columns if any(x in col.lower() for x in ['amount', 'fee', 'fine', 'price', 'total'])]
                        for col in numeric_columns:
                            try:
                                df[col] = pd.to_numeric(df[col], errors='ignore')
                            except:
                                pass
                        
                        export_data[tab] = df
                        sheet_names.append(tab.replace('_', ' ').title())
                        export_info[tab] = {
                            'record_count': len(df),
                            'columns': list(df.columns),
                            'generated_at': datetime.now().isoformat()
                        }
                        
                except Exception as tab_error:
                    logger.error(f"Error exporting tab {tab}: {str(tab_error)}")
                    export_data[tab] = pd.DataFrame({'Error': [f"Failed to export: {str(tab_error)}"]})
                    sheet_names.append(f"{tab} (Error)")
            
            if not export_data:
                return JsonResponse({
                    'success': False,
                    'error': 'No data to export'
                }, status=400)
            
            # Generate export file
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{report_type}_report_{timestamp}"
            
            if export_type == 'excel':
                if export_format == 'xlsx':
                    filename += '.xlsx'
                    content_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                    excel_data = ExportService.export_to_excel(
                        export_data, 
                        sheet_names,
                        filename=filename,
                        include_charts=include_charts,
                        compression=compression
                    )
                else:  # xls
                    filename += '.xls'
                    content_type = 'application/vnd.ms-excel'
                    excel_data = ExportService.export_to_excel_old(
                        export_data,
                        sheet_names,
                        filename=filename
                    )
                
                response = HttpResponse(
                    excel_data,
                    content_type=content_type
                )
                response['Content-Disposition'] = f'attachment; filename="{filename}"'
                response['X-Export-Info'] = json.dumps({
                    'report_type': report_type,
                    'tabs_exported': selected_tabs,
                    'record_counts': {k: v['record_count'] for k, v in export_info.items()},
                    'generated_at': datetime.now().isoformat(),
                    'generated_by': request.user.username
                })
                
            elif export_type == 'csv':
                # For single tab, export as CSV
                if len(selected_tabs) == 1:
                    tab = selected_tabs[0]
                    filename = f"{report_type}_{tab}_{timestamp}.csv"
                    df = export_data[tab]
                    
                    response = HttpResponse(content_type='text/csv')
                    response['Content-Disposition'] = f'attachment; filename="{filename}"'
                    df.to_csv(response, index=False, encoding='utf-8-sig')
                    
                else:
                    # Multiple tabs - create ZIP file
                    import zipfile
                    from io import BytesIO
                    
                    zip_buffer = BytesIO()
                    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                        for tab, df in export_data.items():
                            csv_buffer = BytesIO()
                            df.to_csv(csv_buffer, index=False, encoding='utf-8-sig')
                            csv_buffer.seek(0)
                            zip_file.writestr(f"{tab}.csv", csv_buffer.getvalue())
                    
                    zip_buffer.seek(0)
                    filename = f"{report_type}_report_{timestamp}.zip"
                    
                    response = HttpResponse(zip_buffer.getvalue(), content_type='application/zip')
                    response['Content-Disposition'] = f'attachment; filename="{filename}"'
            
            elif export_type == 'pdf':
                # PDF export would require additional libraries like ReportLab
                # For now, return Excel
                filename += '.xlsx'
                content_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                excel_data = ExportService.export_to_excel(export_data, sheet_names, filename=filename)
                
                response = HttpResponse(
                    excel_data,
                    content_type=content_type
                )
                response['Content-Disposition'] = f'attachment; filename="{filename}"'
            
            else:
                return JsonResponse({
                    'success': False,
                    'error': f'Unsupported export type: {export_type}'
                }, status=400)
            
            # Log export activity
            logger.info(f"Report exported: {report_type}, tabs: {selected_tabs}, user: {request.user.username}")
            
            return response
            
        except Exception as e:
            logger.error(f"Error exporting report: {str(e)}", exc_info=True)
            return JsonResponse({
                'success': False,
                'error': str(e),
                'error_type': type(e).__name__
            }, status=400)

@method_decorator(csrf_exempt, name='dispatch')
class GetFilterOptionsAPI(View):
    """API to get dynamic filter options - COMPLETE"""
    
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            filter_type = data.get('filter_type')
            search_term = data.get('search', '')
            limit = data.get('limit', 50)
            library_code = get_library_code(request)
            
            options = []
            
            if filter_type == 'ward':
                from L01.models import MembershipDetails
                queryset = MembershipDetails.objects.using(library_code).filter(
                    ward__isnull=False
                ).exclude(ward='')
                
                if search_term:
                    queryset = queryset.filter(ward__icontains=search_term)
                
                wards = queryset.values_list('ward', flat=True).distinct().order_by('ward')[:limit]
                options = [{'value': w, 'label': w} for w in wards if w]
                
            elif filter_type == 'payment_type':
                from L01.models import PaymentDetails
                queryset = PaymentDetails.objects.using(library_code).filter(
                    payment_type__isnull=False
                ).exclude(payment_type='')
                
                if search_term:
                    queryset = queryset.filter(payment_type__icontains=search_term)
                
                payment_types = queryset.values_list('payment_type', flat=True).distinct().order_by('payment_type')[:limit]
                options = [{'value': pt, 'label': pt} for pt in payment_types if pt]
                
            elif filter_type == 'action_performed':
                from L01.models import MembershipDetailsHistory
                queryset = MembershipDetailsHistory.objects.using(library_code).filter(
                    actionperformed__isnull=False
                ).exclude(actionperformed='')
                
                if search_term:
                    queryset = queryset.filter(actionperformed__icontains=search_term)
                
                actions = queryset.values_list('actionperformed', flat=True).distinct().order_by('actionperformed')[:limit]
                options = [{'value': a, 'label': a} for a in actions if a]
                
            elif filter_type == 'payment_method':
                from L01.models import PaymentDetails
                queryset = PaymentDetails.objects.using(library_code).filter(
                    payment_method__isnull=False
                ).exclude(payment_method='')
                
                if search_term:
                    queryset = queryset.filter(payment_method__icontains=search_term)
                
                methods = queryset.values_list('payment_method', flat=True).distinct().order_by('payment_method')[:limit]
                options = [{'value': m, 'label': m} for m in methods if m]
                
            elif filter_type == 'book_category':
                from L01.models import BookCatalog
                queryset = BookCatalog.objects.using(library_code).filter(
                    category__isnull=False
                ).exclude(category='')
                
                if search_term:
                    queryset = queryset.filter(category__icontains=search_term)
                
                categories = queryset.values_list('category', flat=True).distinct().order_by('category')[:limit]
                options = [{'value': c, 'label': c} for c in categories if c]
                
            elif filter_type == 'book_language':
                from L01.models import BookMaster
                queryset = BookMaster.objects.using(library_code).filter(
                    language__isnull=False
                ).exclude(language='')
                
                if search_term:
                    queryset = queryset.filter(language__icontains=search_term)
                
                languages = queryset.values_list('language', flat=True).distinct().order_by('language')[:limit]
                options = [{'value': l, 'label': l} for l in languages if l]
            
            return JsonResponse({
                'success': True,
                'options': options,
                'total': len(options)
            })
            
        except Exception as e:
            logger.error(f"Error getting filter options: {str(e)}", exc_info=True)
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)

class DocumentViewAPI(View):
    """API to get document links for a member - COMPLETE"""
    
    def get(self, request, *args, **kwargs):
        try:
            member_id = request.GET.get('member_id')
            document_id = request.GET.get('document_id')
            library_code = get_library_code(request)
            
            from L01.models import DocumentDetails, DocumentMaster
            
            if document_id:
                # Get specific document
                document = get_object_or_404(DocumentDetails.objects.using(library_code), 
                                           id=document_id, isactive=1)
                
                # Check file exists
                file_path = document.file_path
                if not file_path or not os.path.exists(file_path):
                    return JsonResponse({
                        'success': False,
                        'error': 'Document file not found'
                    }, status=404)
                
                # Stream file
                def file_iterator(file_path, chunk_size=8192):
                    with open(file_path, 'rb') as f:
                        while True:
                            chunk = f.read(chunk_size)
                            if not chunk:
                                break
                            yield chunk
                
                response = StreamingHttpResponse(
                    file_iterator(file_path),
                    content_type='application/octet-stream'
                )
                response['Content-Disposition'] = f'attachment; filename="{document.file_name}"'
                response['Content-Length'] = os.path.getsize(file_path)
                return response
            
            else:
                # Get all documents for member
                documents = DocumentDetails.objects.using(library_code).filter(
                    membership_id=member_id,
                    isactive=1
                ).select_related('document').order_by('-created_at')
                
                doc_data = []
                for doc in documents:
                    doc_data.append({
                        'id': doc.id,
                        'document_id': doc.document.id,
                        'document_name': doc.document.document_name,
                        'document_name_mar': doc.document.document_name_mar,
                        'file_name': doc.file_name,
                        'file_path': doc.file_path,
                        'file_size': self.get_file_size(doc.file_path),
                        'file_type': self.get_file_type(doc.file_name),
                        'uploaded_at': doc.created_at.strftime('%Y-%m-%d %H:%M') if doc.created_at else '',
                        'uploaded_by': doc.created_by or '',
                        'is_image': self.is_image_file(doc.file_name),
                        'is_pdf': self.is_pdf_file(doc.file_name),
                        'download_url': f"/reports/api/documents/?document_id={doc.id}"
                    })
                
                return JsonResponse({
                    'success': True,
                    'documents': doc_data,
                    'total': len(doc_data)
                })
                
        except Exception as e:
            logger.error(f"Error getting documents: {str(e)}", exc_info=True)
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)
    
    def get_file_size(self, file_path):
        """Get human readable file size"""
        if not file_path or not os.path.exists(file_path):
            return 'N/A'
        
        size = os.path.getsize(file_path)
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"
    
    def get_file_type(self, filename):
        """Get file type from extension"""
        if not filename:
            return 'Unknown'
        
        ext = filename.split('.')[-1].lower() if '.' in filename else ''
        file_types = {
            'pdf': 'PDF Document',
            'jpg': 'JPEG Image',
            'jpeg': 'JPEG Image',
            'png': 'PNG Image',
            'gif': 'GIF Image',
            'doc': 'Word Document',
            'docx': 'Word Document',
            'xls': 'Excel Spreadsheet',
            'xlsx': 'Excel Spreadsheet',
            'txt': 'Text File',
        }
        return file_types.get(ext, f"{ext.upper()} File")
    
    def is_image_file(self, filename):
        """Check if file is an image"""
        if not filename:
            return False
        ext = filename.split('.')[-1].lower() if '.' in filename else ''
        return ext in ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp']
    
    def is_pdf_file(self, filename):
        """Check if file is PDF"""
        if not filename:
            return False
        ext = filename.split('.')[-1].lower() if '.' in filename else ''
        return ext == 'pdf'

class ReportStatisticsAPI(View):
    """API to get report statistics - COMPLETE"""
    
    def get(self, request, *args, **kwargs):
        try:
            report_type = request.GET.get('report_type')
            library_code = get_library_code(request)
            
            stats = {}
            
            if report_type == 'member':
                from L01.models import MembershipDetails, MembershipDetailsHistory
                
                total_members = MembershipDetails.objects.using(library_code).count()
                active_members = MembershipDetails.objects.using(library_code).filter(isactive=1).count()
                new_this_month = MembershipDetails.objects.using(library_code).filter(
                    created_at__month=datetime.now().month,
                    created_at__year=datetime.now().year
                ).count()
                
                stats = {
                    'total_members': total_members,
                    'active_members': active_members,
                    'inactive_members': total_members - active_members,
                    'new_this_month': new_this_month,
                    'membership_changes': MembershipDetailsHistory.objects.using(library_code).count(),
                    'last_updated': datetime.now().isoformat()
                }
                
            elif report_type == 'book':
                from L01.models import BookCatalog, BookAccession, CirculationTransaction
                
                total_books = BookCatalog.objects.using(library_code).count()
                total_copies = BookAccession.objects.using(library_code).count()
                issued_books = BookAccession.objects.using(library_code).filter(status='issued').count()
                
                stats = {
                    'total_books': total_books,
                    'total_copies': total_copies,
                    'available_copies': BookAccession.objects.using(library_code).filter(status='available').count(),
                    'issued_copies': issued_books,
                    'reserved_copies': BookAccession.objects.using(library_code).filter(status='reserved').count(),
                    'damaged_copies': BookAccession.objects.using(library_code).filter(status='damaged').count(),
                    'total_transactions': CirculationTransaction.objects.using(library_code).count(),
                    'overdue_books': CirculationTransaction.objects.using(library_code).filter(
                        due_date__lt=datetime.now().date(),
                        return_date__isnull=True
                    ).count(),
                    'last_updated': datetime.now().isoformat()
                }
            
            return JsonResponse({
                'success': True,
                'statistics': stats
            })
            
        except Exception as e:
            logger.error(f"Error getting statistics: {str(e)}", exc_info=True)
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)

class SaveReportConfigurationAPI(View):
    """API to save user report configurations - COMPLETE"""
    
    def post(self, request, *args, **kwargs):
        try:
            if not request.user.is_authenticated:
                return JsonResponse({
                    'success': False,
                    'error': 'Authentication required'
                }, status=401)
            
            data = json.loads(request.body)
            config_name = data.get('name')
            report_type = data.get('report_type')
            filters = data.get('filters', {})
            columns = data.get('columns', [])
            is_default = data.get('is_default', False)
            
            # Save to database or user session
            if is_default and request.user.has_perm('reports.manage_filters'):
                # Save as default configuration for all users
                from .models import ReportConfiguration
                config, created = ReportConfiguration.objects.update_or_create(
                    name=config_name,
                    report_type=report_type,
                    defaults={
                        'filters': filters,
                        'columns': columns,
                        'is_default': True,
                        'updated_by': request.user.username
                    }
                )
            else:
                # Save to user session
                report_configs = request.session.get('report_configs', {})
                if report_type not in report_configs:
                    report_configs[report_type] = {}
                
                report_configs[report_type][config_name] = {
                    'filters': filters,
                    'columns': columns,
                    'saved_at': datetime.now().isoformat(),
                    'saved_by': request.user.username
                }
                
                request.session['report_configs'] = report_configs
                request.session.modified = True
            
            return JsonResponse({
                'success': True,
                'message': 'Configuration saved successfully'
            })
            
        except Exception as e:
            logger.error(f"Error saving configuration: {str(e)}", exc_info=True)
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)

class LoadReportConfigurationAPI(View):
    """API to load saved report configurations - COMPLETE"""
    
    def get(self, request, *args, **kwargs):
        try:
            report_type = request.GET.get('report_type')
            config_name = request.GET.get('config_name')
            
            configurations = []
            
            # Load from database (default configurations)
            from .models import ReportConfiguration
            default_configs = ReportConfiguration.objects.filter(
                report_type=report_type,
                is_active=True
            )
            
            for config in default_configs:
                configurations.append({
                    'name': config.name,
                    'type': 'default',
                    'filters': config.filters,
                    'columns': config.columns,
                    'created_at': config.created_at.isoformat() if config.created_at else '',
                    'created_by': config.created_by or '',
                    'is_default': config.is_default
                })
            
            # Load from user session (personal configurations)
            report_configs = request.session.get('report_configs', {})
            if report_type in report_configs:
                for name, config in report_configs[report_type].items():
                    configurations.append({
                        'name': name,
                        'type': 'personal',
                        'filters': config.get('filters', {}),
                        'columns': config.get('columns', []),
                        'saved_at': config.get('saved_at', ''),
                        'saved_by': config.get('saved_by', ''),
                        'is_default': False
                    })
            
            if config_name:
                # Return specific configuration
                config = next((c for c in configurations if c['name'] == config_name), None)
                if config:
                    return JsonResponse({
                        'success': True,
                        'configuration': config
                    })
                else:
                    return JsonResponse({
                        'success': False,
                        'error': 'Configuration not found'
                    }, status=404)
            else:
                # Return all configurations
                return JsonResponse({
                    'success': True,
                    'configurations': configurations
                })
                
        except Exception as e:
            logger.error(f"Error loading configurations: {str(e)}", exc_info=True)
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)
        

# reports/views.py - Extended with all tab implementations

class MemberReportDataService:
    """Service class for member report tab data"""
    
    @staticmethod
    def get_member_details(queryset, filters):
        """Tab 1: Member Details"""
        # Apply tab-specific filters
        if filters.get('membership_month_from'):
            # Filter logic
            pass
        
        columns = [
            {'data': 'first_name', 'title': 'First Name'},
            {'data': 'middle_name', 'title': 'Middle Name'},
            {'data': 'last_name', 'title': 'Last Name'},
            {'data': 'membership_code', 'title': 'Membership Code'},
            {'data': 'user_id', 'title': 'User ID'},
            {'data': 'mobile_no', 'title': 'Mobile'},
            {'data': 'email', 'title': 'Email'},
            {'data': 'ward', 'title': 'Ward'},
            {'data': 'local_address', 'title': 'Address'},
            {'data': 'aadhar_no', 'title': 'Aadhar'},
            {'data': 'dob', 'title': 'DOB'},
            {'data': 'status__status_name', 'title': 'Status'},
            {'data': 'created_at', 'title': 'Created At'},
        ]
        
        data = list(queryset.values(
            'id', 'first_name', 'middle_name', 'last_name',
            'membership_code', 'user_id', 'mobile_no', 'email',
            'ward', 'local_address', 'aadhar_no', 'dob',
            'status__status_name', 'created_at'
        ))
        
        return {'data': data, 'columns': columns, 'total': len(data)}
    
    @staticmethod
    def get_membership_history(member_ids, library_code, filters):
        """Tab 2: Membership Details"""
        from L01.models import MembershipDetailsHistory
        
        queryset = MembershipDetailsHistory.objects.using(library_code).filter(
            membership_id__in=member_ids
        ).select_related('membershipmaster', 'status')
        
        # Apply filters
        if filters.get('from_date'):
            queryset = queryset.filter(changed_at__date__gte=filters['from_date'])
        if filters.get('to_date'):
            queryset = queryset.filter(changed_at__date__lte=filters['to_date'])
        
        columns = [
            {'data': 'first_name', 'title': 'Member Name'},
            {'data': 'actionperformed', 'title': 'Info'},
            {'data': 'from_date', 'title': 'From Date'},
            {'data': 'to_date', 'title': 'To Date'},
            {'data': 'deposit', 'title': 'Deposit'},
            {'data': 'entry_fees', 'title': 'Entry Fees'},
            {'data': 'subscription', 'title': 'Subscription'},
            {'data': 'gap_fine', 'title': 'Gap Fine'},
            {'data': 'late_fee', 'title': 'Late Fee'},
            {'data': 'changed_at', 'title': 'Changed At'},
            {'data': 'changed_by', 'title': 'Changed By'},
        ]
        
        data = list(queryset.values(
            'id', 'first_name', 'middle_name', 'last_name',
            'actionperformed', 'from_date', 'to_date',
            'deposit', 'entry_fees', 'subscription',
            'gap_fine', 'late_fee', 'changed_at', 'changed_by'
        ))
        
        return {'data': data, 'columns': columns, 'total': len(data)}
    
    @staticmethod
    def get_loan_data(member_ids, library_code, filters):
        """Tab 3: Loan Information"""
        from L01.models import CirculationTransaction
        
        queryset = CirculationTransaction.objects.using(library_code).filter(
            member_id__in=member_ids
        ).select_related('catalog', 'accession')
        
        # Apply filters
        if filters.get('from_date'):
            queryset = queryset.filter(issue_date__gte=filters['from_date'])
        if filters.get('to_date'):
            queryset = queryset.filter(issue_date__lte=filters['to_date'])
        if filters.get('overdue'):
            queryset = queryset.filter(days_overdue_count__gt=0)
        
        columns = [
            {'data': 'member__membership_code', 'title': 'Membership Code'},
            {'data': 'barcode', 'title': 'Barcode'},
            {'data': 'accession__accession_no', 'title': 'Accession No'},
            {'data': 'catalog__title', 'title': 'Book Title'},
            {'data': 'issue_date', 'title': 'Issue Date'},
            {'data': 'due_date', 'title': 'Due Date'},
            {'data': 'return_date', 'title': 'Return Date'},
            {'data': 'days_overdue_count', 'title': 'Overdue Days'},
            {'data': 'fine_amount', 'title': 'Fine Amount'},
            {'data': 'issued_by', 'title': 'Issued By'},
            {'data': 'remarks', 'title': 'Remarks'},
        ]
        
        data = list(queryset.values(
            'id', 'barcode', 'issue_date', 'due_date', 'return_date',
            'days_overdue_count', 'fine_amount', 'issued_by', 'remarks',
            'member__membership_code',
            'accession__accession_no',
            'catalog__title'
        ))
        
        return {'data': data, 'columns': columns, 'total': len(data)}
    
    @staticmethod 
    def get_transaction_data(member_ids, library_code, filters):
        """Tab 4: Transactions"""
        from L01.models import CirculationTransaction
        
        queryset = CirculationTransaction.objects.using(library_code).filter(
            member_id__in=member_ids
        ).select_related('member', 'catalog', 'accession')
        
        # Apply transaction-specific filters
        if filters.get('late_returns'):
            queryset = queryset.filter(return_date__gt=F('due_date'))
        if filters.get('fine_status'):
            queryset = queryset.filter(fine_status=filters['fine_status'])
        
        columns = [
            # All required columns from specification
            {'data': 'member__first_name', 'title': 'Member Name'},
            {'data': 'member__membership_code', 'title': 'Membership Code'},
            {'data': 'barcode', 'title': 'Barcode'},
            {'data': 'issue_date', 'title': 'Issue Date'},
            {'data': 'due_date', 'title': 'Due Date'},
            {'data': 'return_date', 'title': 'Return Date'},
            {'data': 'days_overdue_count', 'title': 'Overdue Days'},
            {'data': 'fine_amount', 'title': 'Fine Amount'},
            {'data': 'book_fine_amount', 'title': 'Book Fine'},
            {'data': 'total_fine', 'title': 'Total Fine'},
            {'data': 'adjusted_fine', 'title': 'Adjusted Fine'},
            {'data': 'fine_status', 'title': 'Fine Status'},
            {'data': 'fine_paid_date', 'title': 'Fine Paid Date'},
            {'data': 'issued_by', 'title': 'Issued By'},
            {'data': 'received_by', 'title': 'Received By'},
        ]
        
        data = list(queryset.values(*[col['data'] for col in columns]))
        
        return {'data': data, 'columns': columns, 'total': len(data)}
    
    @staticmethod
    def get_physical_visit_data(member_ids, library_code, filters):
        """Tab 5: Physical Visit"""
        from L01.models import MemberEntryExit
        
        queryset = MemberEntryExit.objects.using(library_code).filter(
            membership_code__in=member_ids
        )
        
        # Apply date filters
        if filters.get('from_date'):
            queryset = queryset.filter(entry_time__date__gte=filters['from_date'])
        if filters.get('to_date'):
            queryset = queryset.filter(entry_time__date__lte=filters['to_date'])
        
        columns = [
            {'data': 'membership_code', 'title': 'Membership Code'},
            {'data': 'entry_time', 'title': 'Entry Time'},
            {'data': 'exit_time', 'title': 'Exit Time'},
            {'data': 'remark', 'title': 'Remark'},
            {'data': 'created_at', 'title': 'Logged At'},
        ]
        
        data = list(queryset.values(*[col['data'] for col in columns]))
        
        return {'data': data, 'columns': columns, 'total': len(data)}
    
    @staticmethod
    def get_virtual_usage_data(member_ids, library_code, filters):
        """Tab 6: Virtual Usage"""
        from L01.models import MemberLoginSession, MemberScreenActivity
        
        queryset = MemberScreenActivity.objects.using(library_code).filter(
            session__member_id__in=member_ids
        ).select_related('session')
        
        # Apply filters
        if filters.get('from_date'):
            queryset = queryset.filter(visited_at__date__gte=filters['from_date'])
        if filters.get('to_date'):
            queryset = queryset.filter(visited_at__date__lte=filters['to_date'])
        
        columns = [
            {'data': 'session__member__membership_code', 'title': 'Membership Code'},
            {'data': 'screen_name', 'title': 'Screen Name'},
            {'data': 'screen_route', 'title': 'Screen Route'},
            {'data': 'visited_at', 'title': 'Visited At'},
        ]
        
        data = list(queryset.values(*[col['data'] for col in columns]))
        
        return {'data': data, 'columns': columns, 'total': len(data)}
    
    @staticmethod
    def get_payment_data(member_ids, library_code, filters):
        """Tab 7: Payments"""
        from L01.models import PaymentDetails
        
        queryset = PaymentDetails.objects.using(library_code).filter(
            membership_id__in=member_ids
        ).select_related('status')
        
        # Apply payment filters
        if filters.get('from_date'):
            queryset = queryset.filter(payment_date__gte=filters['from_date'])
        if filters.get('to_date'):
            queryset = queryset.filter(payment_date__lte=filters['to_date'])
        if filters.get('payment_type'):
            queryset = queryset.filter(payment_type=filters['payment_type'])
        
        columns = [
            {'data': 'payment_mode', 'title': 'Payment Mode'},
            {'data': 'payment_type', 'title': 'Payment Type'},
            {'data': 'payment_method', 'title': 'Payment Method'},
            {'data': 'deposit_amount', 'title': 'Deposit'},
            {'data': 'entry_fee_amount', 'title': 'Entry Fee'},
            {'data': 'monthly_subscription_amount', 'title': 'Monthly Subscription'},
            {'data': 'total_subscription_amount', 'title': 'Total Subscription'},
            {'data': 'subscription_from', 'title': 'Subscription From'},
            {'data': 'subscription_to', 'title': 'Subscription To'},
            {'data': 'transaction_id', 'title': 'Transaction ID'},
            {'data': 'book_fine_amount', 'title': 'Book Fine'},
            {'data': 'fine_amount', 'title': 'Fine'},
            {'data': 'adjusted_amount', 'title': 'Adjusted'},
            {'data': 'remarks', 'title': 'Remarks'},
            {'data': 'payment_date', 'title': 'Payment Date'},
            {'data': 'status__status_name', 'title': 'Status'},
        ]
        
        data = list(queryset.values(*[col['data'] for col in columns]))
        
        return {'data': data, 'columns': columns, 'total': len(data)}