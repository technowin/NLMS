from warnings import filters
from django.conf import settings
from django.shortcuts import render

# Create your views here.
# reports/views.py
import json
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.views import View
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q, F, Value, CharField
from django.db.models.functions import Concat, ExtractMonth
from django.core.paginator import Paginator
from django.utils import timezone
from httpcore import request
import pandas as pd
from io import BytesIO
import xlsxwriter

from library_reports.models import *

from .forms import *
from L01.models import *
from Account.models import CustomUser 

from datetime import date
import calendar

def parse_month_start(month_str):
    y, m = map(int, month_str.split('-'))
    return date(y, m, 1)

def parse_month_end(month_str):
    y, m = map(int, month_str.split('-'))
    last_day = calendar.monthrange(y, m)[1]
    return date(y, m, last_day)

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
    
    def get_membership_queryset(self, filters=None):
        """Get membership queryset with applied filters"""
        db = self.get_library_db()
        qs = MembershipDetails.objects.using(db).all()
        
        if filters:
            membership_types = filters.get('membership_type')

            if membership_types:
                qs = qs.filter(membership_id__in=membership_types)

            membership_statuses = filters.get('membership_status')

            if membership_statuses:
                status_q = Q()

                if 'active' in membership_statuses:
                    status_q |= Q(isactive=1)

                if 'inactive' in membership_statuses:
                    status_q |= Q(isactive=0)

                if 'cancelled' in membership_statuses:
                    status_q |= Q(
                        isactive=0,
                        status__status_name__iexact='cancelled'
                    )

                qs = qs.filter(status_q)
            
            if filters.get('search'):
                search_term = filters['search']
                qs = qs.filter(
                    Q(first_name__icontains=search_term) |
                    Q(last_name__icontains=search_term) |
                    Q(membership_code__icontains=search_term) |
                    Q(user_id__icontains=search_term) |
                    Q(aadhar_no__icontains=search_term)
                )
        
        return qs.select_related('membership', 'status', 'member_type')

class MemberReportView(ReportBaseView, TemplateView):
    """Main member report view"""
    template_name = 'library_reports/member_report.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        db = self.get_library_db()
        
        # Get all filter options for forms
        try:
            member_types = parameter_master_L01.objects.using(db).filter(isactive=1,parameter_name='MembershipForm').only('parameter_id', 'parameter_name', 'parameter_value')
            membership_types = MembershipMaster.objects.using(db).filter(isactive=1).values('id', 'membership_type_en')
            status_list = StatusMaster.objects.using(db).filter(isactive=1).values('id', 'status_name')
            ward_list = WardMaster.objects.using(db).filter(is_active=1).values('ward_name', 'ward_name')
            actionperformed_list  = MembershipDetails.objects.using(db).filter(isactive=1).exclude(actionperformed__isnull=True).values('actionperformed').distinct().order_by('actionperformed')

        except:
            member_types = []
            membership_types = []
            status_list = []
            ward_list = []
            actionperformed_list = []
        
        context['member_types'] = member_types
        context['membership_types'] = membership_types
        context['status_list'] = status_list
        context['ward_list'] = ward_list
        context['actionperformed_list'] = actionperformed_list
        # Initialize all filter forms with dynamic choices
        context['member_list_form'] = MemberListFilterForm()
        
        # Member Details Form with dynamic choices
        member_details_form = CompleteMemberDetailsFilterForm()
        # member_details_form.fields['member_type'].queryset = member_types
        context['member_details_form'] = member_details_form
        
        # Membership Details Form
        membership_details_form = MembershipDetailsFilterForm()
        context['membership_details_form'] = membership_details_form
        
        # Loan Form
        loan_form = LoanFilterForm()
        context['loan_form'] = loan_form
        
        # Transaction Form
        transaction_form = TransactionFilterForm()
        context['transaction_form'] = transaction_form
        
        # Physical Visit Form
        physical_visit_form = PhysicalVisitFilterForm()
        context['physical_visit_form'] = physical_visit_form
        
        # Virtual Usage Form
        virtual_usage_form = VirtualUsageFilterForm()
        context['virtual_usage_form'] = virtual_usage_form
        
        # Payment Form
        payment_form = PaymentFilterForm()
        context['payment_form'] = payment_form
        
        # Get initial member list (first 50 active members)
        members = MembershipDetails.objects.using(db).filter(
            isactive=1
        ).select_related('membership', 'status')[:50]
        
        context['members'] = members
        context['total_member_count'] = MembershipDetails.objects.using(db).filter(isactive=1).count()
        
        # Add library info
        context['library_db'] = self.get_library_db()
        context['current_library'] = self.request.session.get('library_name', 'Main Library')
        
        # Add user info for template
        context['user'] = self.request.user
        
        return context

class MemberListDataView(ReportBaseView):
    """AJAX endpoint for member list data"""
    
    def get(self, request):
        form = MemberListFilterForm(request.GET)
        if form.is_valid():
            filters = form.cleaned_data
            members_qs = self.get_membership_queryset(filters)
            
            # Pagination
            page = int(request.GET.get('page', 1))
            per_page = int(request.GET.get('per_page', 10))
            paginator = Paginator(members_qs, per_page)
            
            try:
                members_page = paginator.page(page)
            except:
                members_page = paginator.page(1)
            
            # Prepare response data
            data = {
                'members': [],
                'total': paginator.count,
                'pages': paginator.num_pages,
                'current_page': page
            }
            
            for member in members_page:
                data['members'].append({
                    'id': member.id,
                    'membership_code': member.membership_code or '',
                    'first_name': member.first_name or '',
                    'last_name': member.last_name or '',
                    'membership_type': member.membership.membership_type_en if member.membership else '',
                    'status': 'Active' if member.isactive == 1 else 'Inactive',
                    'user_id': member.user_id or '',
                    'email': member.email or ''
                })
            
            return JsonResponse(data)
        
        return JsonResponse({'error': 'Invalid form data'}, status=400)

class TabDataView(ReportBaseView):
    """AJAX endpoint for tab data"""
    
    def get(self, request, tab_name):
        member_ids = request.GET.getlist('member_ids[]')
        filters_json = request.GET.get('filters', '{}')
        
        try:
            filters = json.loads(filters_json)
        except:
            filters = {}
        
        db = self.get_library_db()
        
        if tab_name == 'member-details':
            data = self.get_member_details_data(db, member_ids, filters)
        elif tab_name == 'membership-details':
            data = self.get_membership_details_data(db, member_ids, filters)
        elif tab_name == 'loan':
            data = self.get_loan_data(db, member_ids, filters)
        elif tab_name == 'transactions':
            data = self.get_transaction_data(db, member_ids, filters)
        elif tab_name == 'physical-visit':
            data = self.get_physical_visit_data(db, member_ids, filters)
        elif tab_name == 'virtual-usage':
            data = self.get_virtual_usage_data(db, member_ids, filters)
        elif tab_name == 'payments':
            data = self.get_payment_data(db, member_ids, filters)
        else:
            return JsonResponse({'error': 'Invalid tab'}, status=400)
        
        return JsonResponse(data)
    
    def get_member_details_data(self, db, member_ids, filters):
        qs = MembershipDetails.objects.using(db).filter(id__in=member_ids)
        
        # Apply filters
        if filters.get('membership_month_from'):
            start_date = parse_month_start(filters['membership_month_from'])
            qs = qs.filter(from_date__gte=start_date)
        if filters.get('membership_month_to'):
            end_date = parse_month_end(filters['membership_month_to'])
            qs = qs.filter(from_date__lte=end_date)
        if filters.get('membership_type'):
            qs = qs.filter(membership_id__in=filters['membership_type'])
        if filters.get('member_type'):
            qs = qs.filter(member_type_id__in=filters['member_type'])
        if filters.get('ward'):
            qs = qs.filter(ward__in=filters['ward'])
        if filters.get('status'):
            qs = qs.filter(status_id__in=filters['status'])
        if filters.get('renewal_due_month'):
            start = parse_month_start(filters['renewal_due_month'])
            end = parse_month_end(filters['renewal_due_month'])
            qs = qs.filter(to_date__range=(start, end))

        
        data = []
        for member in qs:
            data.append({
                'first_name': member.first_name,
                'middle_name': member.middle_name,
                'last_name': member.last_name,
                'first_name_mar': member.first_name_mar,
                'last_name_mar': member.last_name_mar,
                'middle_name_mar': member.middle_name_mar,
                'membershipmaster_id': member.membership.id if member.membership else '',
                'member_type': member.member_type.parameter_name if member.member_type else '',
                'membership_code': member.membership_code,
                'membership_date': member.created_at.strftime('%Y-%m-%d') if member.created_at else '',
                'renewal_from_date': member.from_date.strftime('%Y-%m-%d') if member.from_date else '',
                'renewal_to_date': member.to_date.strftime('%Y-%m-%d') if member.to_date else '',
                'user_id': member.user_id,
                'ward': member.ward,
                'pincode': member.pincode,
                'local_address': member.local_address,
                'mobile_no': member.mobile_no,
                'email': member.email,
                'occupation': member.occupation,
                'office_phone': member.office_phone,
                'education': member.education,
                'institute_name': member.institute_name,
                'recommender_details': member.recommender_details,
                'dob': member.dob.strftime('%Y-%m-%d') if member.dob else '',
                'aadhar_no': member.aadhar_no,
                'address_same_as_aadhar': 'Yes' if member.address_same_as_aadhar == 1 else 'No',
                'is_resident_of_nmmc': 'Yes' if member.is_resident_of_nmmc == 1 else 'No',
                'status': 'Active' if member.isactive == 1 else 'Inactive',
                'created_at': member.created_at.strftime('%Y-%m-%d %H:%M') if member.created_at else '',
                'created_by': member.created_by,
                'updated_at': member.updated_at.strftime('%Y-%m-%d %H:%M') if member.updated_at else '',
                'updated_by': member.updated_by,
                'approved_by': member.reviewed,
                'approved_date': member.reviewed_at.strftime('%Y-%m-%d %H:%M') if member.reviewed_at else '',
            })
        
        return {'data': data}
    
    def get_membership_details_data(self, db, member_ids, filters):
        # Combine current and historical data
        current_qs = MembershipDetails.objects.using(db).filter(id__in=member_ids)
        history_qs = MembershipDetailsHistory.objects.using(db).filter(membership_id__in=member_ids)
        
        data = []
        
        # Process current memberships
        for member in current_qs:
            data.append({
                'first_name': member.first_name,
                'middle_name': member.middle_name,
                'last_name': member.last_name,
                'first_name_mar': member.first_name_mar,
                'middle_name_mar': member.middle_name_mar,
                'last_name_mar': member.last_name_mar,
                'actionperformed': member.actionperformed,
                'from_date': member.from_date.strftime('%Y-%m-%d') if member.from_date else '',
                'to_date': member.to_date.strftime('%Y-%m-%d') if member.to_date else '',
                'deposit': float(member.deposit) if member.deposit else 0,
                'entry_fees': float(member.entry_fees) if member.entry_fees else 0,
                'subscription': float(member.subscription) if member.subscription else 0,
                'fine_calculated_at': member.fine_calculated_at.strftime('%Y-%m-%d %H:%M') if member.fine_calculated_at else '',
                'gap_fine_subscription': float(member.gap_fine) if member.gap_fine else 0,
                'gap_fine_delay': float(member.late_fee) if member.late_fee else 0,
                'gap_months': member.gap_months or 0,
                'late_fee': float(member.late_fee) if member.late_fee else 0,
                'changed_at': member.updated_at.strftime('%Y-%m-%d %H:%M') if member.updated_at else '',
                'changed_by': member.updated_by,
                'membership_type_id': member.membership_id,
            })
        
        # Process historical data
        for history in history_qs:
            data.append({
                'first_name': history.first_name,
                'middle_name': history.middle_name,
                'last_name': history.last_name,
                'first_name_mar': history.first_name_mar,
                'middle_name_mar': history.middle_name_mar,
                'last_name_mar': history.last_name_mar,
                'actionperformed': history.actionperformed,
                'from_date': history.from_date.strftime('%Y-%m-%d') if history.from_date else '',
                'to_date': history.to_date.strftime('%Y-%m-%d') if history.to_date else '',
                'deposit': float(history.deposit) if history.deposit else 0,
                'entry_fees': float(history.entry_fees) if history.entry_fees else 0,
                'subscription': float(history.subscription) if history.subscription else 0,
                'fine_calculated_at': history.fine_calculated_at.strftime('%Y-%m-%d %H:%M') if history.fine_calculated_at else '',
                'gap_fine_subscription': float(history.gap_fine) if history.gap_fine else 0,
                'gap_fine_delay': float(history.late_fee) if history.late_fee else 0,
                'gap_months': history.gap_months or 0,
                'late_fee': float(history.late_fee) if history.late_fee else 0,
                'changed_at': history.changed_at.strftime('%Y-%m-%d %H:%M') if history.changed_at else '',
                'changed_by': history.changed_by,
                'membership_type_id': history.membership_id,
            })
        
        # Apply filters to combined data
        # Date filters
        if filters.get('from_date'):
            from_dt = datetime.strptime(filters['from_date'], '%Y-%m-%d').date()
            data = [d for d in data if d['from_date'] and d['from_date'] >= from_dt]

        if filters.get('to_date'):
            to_dt = datetime.strptime(filters['to_date'], '%Y-%m-%d').date()
            data = [d for d in data if d['to_date'] and d['to_date'] <= to_dt]

        # Gap Period
        gap_filter = filters.get('gap_period')
        if gap_filter == 'no_gap':
            data = [d for d in data if d['gap_months'] == 0]
        elif gap_filter == 'with_gap':
            data = [d for d in data if d['gap_months'] > 0]
        elif gap_filter == '1_3':
            data = [d for d in data if 1 <= d['gap_months'] <= 3]
        elif gap_filter == '4_6':
            data = [d for d in data if 4 <= d['gap_months'] <= 6]
        elif gap_filter == '6_plus':
            data = [d for d in data if d['gap_months'] > 6]

        # Action Performed
        if filters.get('actionperformed'):
            actions = set(filters['actionperformed'])
            data = [d for d in data if d['actionperformed'] in actions]

        # Membership Type
        if filters.get('membership_type'):
            mt_ids = {
                int(x) for x in filters['membership_type']
                if str(x).isdigit()
            }
            data = [
                d for d in data
                if d.get('membership_type_id') in mt_ids
            ]


        
        return {'data': data}
    
    def get_loan_data(self, db, member_ids, filters):
        qs = CirculationTransaction.objects.using(db).filter(
            member_id__in=member_ids,
            transaction_type='Offline'
        ).select_related('catalog', 'accession', 'member')
        
        # Apply filters
        if filters.get('from_date'):
            qs = qs.filter(issue_date__gte=filters['from_date'])
        if filters.get('to_date'):
            qs = qs.filter(issue_date__lte=filters['to_date'])

        if filters.get('overdue') == 'overdue':
            qs = qs.filter(days_overdue_count__gt=0)
        elif filters.get('overdue') == 'not_overdue':
            qs = qs.filter(days_overdue_count=0)

        if filters.get('fine_status') == 'paid':
            qs = qs.filter(fine_status__iexact='paid')
        elif filters.get('fine_status') == 'not_paid':
            qs = qs.filter(
            Q(fine_status__isnull=True) |
            Q(fine_status__iexact='not_paid') |
            Q(fine_amount__gt=0, fine_paid_date__isnull=True)
        )
        
        membership_type = filters.get('membership_type')
        if membership_type:
            qs = qs.filter(member__member_type_id=membership_type)

        from Account.models import CustomUser 
        data = []
        for transaction in qs:
            data.append({
                'membership_code': transaction.member.membership_code if transaction.member else '',
                'barcode': transaction.barcode,
                'accession_id': transaction.accession.accession_id if transaction.accession else '',
                'cat_ref_num': transaction.catalog.cat_ref_num if transaction.catalog else '',
                'issue_date': transaction.issue_date.strftime('%Y-%m-%d') if transaction.issue_date else '',
                'due_date': transaction.due_date.strftime('%Y-%m-%d') if transaction.due_date else '',
                'return_date': transaction.return_date.strftime('%Y-%m-%d') if transaction.return_date else '',
                'days_overdue_count': transaction.days_overdue_count or 0,
                'fine_amount': float(transaction.fine_amount) if transaction.fine_amount else 0,
                'issued_by':  CustomUser.objects.using(db).filter(id=transaction.issued_by).only('full_name').first().full_name if transaction.issued_by else '',
                'remarks': transaction.remarks,
                'created_at': transaction.created_at.strftime('%Y-%m-%d %H:%M') if transaction.created_at else '',
            })
        
        return {'data': data}
    
    def get_transaction_data(self, db, member_ids, filters):
        qs = CirculationTransaction.objects.using(db).filter(
            member_id__in=member_ids
        ).select_related('catalog', 'accession', 'member')
        
        if filters.get('from_date'):
            qs = qs.filter(created_at__date__gte=filters['from_date'])
        if filters.get('to_date'):
            qs = qs.filter(created_at__date__lte=filters['to_date'])
        if filters.get('late_returns') == 'late':
            qs = qs.filter(days_overdue_count__gt=0)
        elif filters.get('late_returns') == 'on_time':
            qs = qs.filter(days_overdue_count=0)
        if filters.get('fine_status') == 'paid':
            qs = qs.filter(fine_status='paid')
        elif filters.get('fine_status') == 'not_paid':
            qs = qs.filter(fine_status__in=['unpaid', 'pending', None])
            
        data = []
        for transaction in qs:
            data.append({
                'member_name': f"{transaction.member.first_name or ''} {transaction.member.last_name or ''}".strip(),
                'membership_code': transaction.member.membership_code if transaction.member else '',
                'barcode': transaction.barcode,
                'accession_id': transaction.accession.accession_id if transaction.accession else '',
                'cat_ref_num': transaction.catalog.cat_ref_num if transaction.catalog else '',
                'issue_date': transaction.issue_date.strftime('%Y-%m-%d') if transaction.issue_date else '',
                'due_date': transaction.due_date.strftime('%Y-%m-%d') if transaction.due_date else '',
                'issued_by': CustomUser.objects.using(db).filter(id=transaction.issued_by).only('full_name').first().full_name if transaction.issued_by else '',
                'created_at': transaction.created_at.strftime('%Y-%m-%d %H:%M') if transaction.created_at else '',
                'return_date': transaction.return_date.strftime('%Y-%m-%d') if transaction.return_date else '',
                'received_by': transaction.received_by,
                'days_overdue_count': transaction.days_overdue_count or 0,
                'fine_amount': float(transaction.fine_amount) if transaction.fine_amount else 0,
                'book_fine_amount': float(transaction.book_fine_amount) if transaction.book_fine_amount else 0,
                'total_fine': float(transaction.total_fine) if transaction.total_fine else 0,
                'adjusted_fine': float(transaction.adjusted_fine) if transaction.adjusted_fine else 0,
                'fine_status': transaction.fine_status,
                'fine_paid_date': transaction.fine_paid_date.strftime('%Y-%m-%d') if transaction.fine_paid_date else '',
                'remarks': transaction.remarks,
                'updated_at': transaction.updated_at.strftime('%Y-%m-%d %H:%M') if transaction.updated_at else '',
            })
        
        return {'data': data}
    
    def get_physical_visit_data(self, db, member_ids, filters):
        """COMPLETE IMPLEMENTATION"""
        # Get membership codes first
        members = MembershipDetails.objects.using(db).filter(
            id__in=member_ids
        ).values('id', 'membership_code')
        
        member_codes = [m['membership_code'] for m in members if m['membership_code']]
        
        # Query MemberEntryExit
        qs = MemberEntryExit.objects.using(db).filter(
            membership_code__in=member_codes
        ).order_by('-entry_time')
        
        # Apply filters
        if filters.get('from_date'):
            qs = qs.filter(entry_time__date__gte=filters['from_date'])
        if filters.get('to_date'):
            qs = qs.filter(entry_time__date__lte=filters['to_date'])
        
        if filters.get('from_date'):
            qs = qs.filter(entry_time__date__gte=filters['from_date'])
        if filters.get('to_date'):
            qs = qs.filter(entry_time__date__lte=filters['to_date'])

        if filters.get('activity_type') == 'entry':
            qs = qs.filter(exit_time__isnull=True)
        elif filters.get('activity_type') == 'exit':
            qs = qs.filter(exit_time__isnull=False)
        elif filters.get('activity_type') == 'completed':
            qs = qs.filter(entry_time__isnull=False, exit_time__isnull=False)
        if filters.get('remarks_search'):
            qs = qs.filter(remark__icontains=filters['remarks_search'])
        data = []
        for visit in qs:
            # Find member name
            member = next((m for m in members if m['membership_code'] == visit.membership_code), None)
            member_name = ""
            if member:
                member_obj = MembershipDetails.objects.using(db).filter(id=member['id']).first()
                if member_obj:
                    member_name = f"{member_obj.first_name or ''} {member_obj.last_name or ''}".strip()
            
            data.append({
                'member_name': member_name,
                'membership_code': visit.membership_code,
                'entry_time': visit.entry_time.strftime('%Y-%m-%d %H:%M:%S') if visit.entry_time else '',
                'exit_time': visit.exit_time.strftime('%Y-%m-%d %H:%M:%S') if visit.exit_time else '',
                'remark': visit.remark or '',
                'created_at': visit.created_at.strftime('%Y-%m-%d %H:%M:%S') if visit.created_at else ''
            })
        
        return {'data': data}
    
    def get_virtual_usage_data(self, db, member_ids, filters):
        """COMPLETE IMPLEMENTATION"""
        # Get login sessions
        login_sessions = MemberLoginSession.objects.using(db).filter(
            member_id__in=member_ids
        ).select_related('member').order_by('-login_time')

        # Apply filters to login sessions
        if filters.get('from_date'):
            qs_login = qs_login.filter(login_time__date__gte=filters['from_date'])
        if filters.get('to_date'):
            qs_login = qs_login.filter(login_time__date__lte=filters['to_date'])
        if filters.get('activity_type') == 'login':
            count += qs_login.count()
            return count
        if filters.get('device_type'):
            qs_login = qs_login.filter(device_type__icontains=filters['device_type'])
        
        # Apply filters to screen activities
        if filters.get('from_date'):
            qs_activity = qs_activity.filter(visited_at__date__gte=filters['from_date'])
        if filters.get('to_date'):
            qs_activity = qs_activity.filter(visited_at__date__lte=filters['to_date'])
        if filters.get('activity_type') == 'screen':
            count += qs_activity.count()
            return count
        if filters.get('screen_name'):
            qs_activity = qs_activity.filter(screen_name__icontains=filters['screen_name'])
        if filters.get('device_type'):
            qs_activity = qs_activity.filter(session__device_type__icontains=filters['device_type'])

        # Apply date filters
        if filters.get('from_date'):
            login_sessions = login_sessions.filter(login_time__date__gte=filters['from_date'])
        if filters.get('to_date'):
            login_sessions = login_sessions.filter(login_time__date__lte=filters['to_date'])
        
        data = []
        for session in login_sessions:
            data.append({
                'member_name': f"{session.member.first_name or ''} {session.member.last_name or ''}".strip(),
                'membership_code': session.member.membership_code if session.member else '',
                'screen_name': 'Login Session',
                'screen_route': '/login',
                'visited_at': session.login_time.strftime('%Y-%m-%d %H:%M:%S'),
                'ip_address': session.ip_address or '',
                'device_type': session.device_type or '',
                'duration': self.calculate_session_duration(session)
            })
        
        # Get screen activities
        activities = MemberScreenActivity.objects.using(db).filter(
            session__member_id__in=member_ids
        ).select_related('session', 'session__member').order_by('-visited_at')
        
        # Apply date filters
        if filters.get('from_date'):
            activities = activities.filter(visited_at__date__gte=filters['from_date'])
        if filters.get('to_date'):
            activities = activities.filter(visited_at__date__lte=filters['to_date'])
        
        for activity in activities:
            data.append({
                'member_name': f"{activity.session.member.first_name or ''} {activity.session.member.last_name or ''}".strip(),
                'membership_code': activity.session.member.membership_code if activity.session.member else '',
                'screen_name': activity.screen_name,
                'screen_route': activity.screen_route,
                'visited_at': activity.visited_at.strftime('%Y-%m-%d %H:%M:%S'),
                'ip_address': activity.session.ip_address or '',
                'device_type': activity.session.device_type or '',
                'duration': 'N/A'
            })
        
        return {'data': data}
    
    def calculate_session_duration(self, session):
        """Calculate session duration in minutes"""
        if session.login_time and session.logout_time:
            duration = session.logout_time - session.login_time
            minutes = duration.total_seconds() / 60
            return f"{minutes:.1f} minutes"
        return 'Still active'
    
    def get_payment_data(self, db, member_ids, filters):
        """COMPLETE IMPLEMENTATION"""
        qs = PaymentDetails.objects.using(db).filter(
            membership_id__in=member_ids
        ).select_related('membership', 'status').order_by('-created_at')
        
        # Apply filters
        if filters.get('from_date'):
            qs = qs.filter(created_at__date__gte=filters['from_date'])
        if filters.get('to_date'):
            qs = qs.filter(created_at__date__lte=filters['to_date'])
        if filters.get('payment_type'):
            qs = qs.filter(payment_type__icontains=filters['payment_type'])
        
        if filters.get('from_date'):
            qs = qs.filter(payment_date__gte=filters['from_date'])
        if filters.get('to_date'):
            qs = qs.filter(payment_date__lte=filters['to_date'])
        if filters.get('payment_type'):
            qs = qs.filter(payment_type=filters['payment_type'])

        data = []
        for payment in qs:
            data.append({
                'payment_mode': payment.payment_mode or '',
                'payment_type': payment.payment_type or '',
                'payment_method': payment.payment_method or '',
                'deposit_amount': float(payment.deposit_amount) if payment.deposit_amount else 0.0,
                'entry_fee_amount': float(payment.entry_fee_amount) if payment.entry_fee_amount else 0.0,
                'monthly_subscription_amount': float(payment.monthly_subscription_amount) if payment.monthly_subscription_amount else 0.0,
                'total_subscription_amount': float(payment.total_subscription_amount) if payment.total_subscription_amount else 0.0,
                'subscription_from': payment.subscription_from.strftime('%Y-%m-%d') if payment.subscription_from else '',
                'subscription_to': payment.subscription_to.strftime('%Y-%m-%d') if payment.subscription_to else '',
                'transaction_id': payment.transaction_id or '',
                'remarks': payment.remarks or '',
                'user_id': payment.user_id or '',
                'membership_code': payment.membership_code or '',
                'created_at': payment.created_at.strftime('%Y-%m-%d %H:%M:%S') if payment.created_at else '',
                'created_by': payment.created_by or '',
                'updated_at': payment.updated_at.strftime('%Y-%m-%d %H:%M:%S') if payment.updated_at else '',
                'updated_by': payment.updated_by or '',
                'membership_id': payment.membership_id,
                'status_id': payment.status_id,
                'payment_date': payment.payment_date.strftime('%Y-%m-%d') if payment.payment_date else '',
                'circulation_transaction_id': payment.circulation_transaction_id,
                'book_fine_amount': float(payment.book_fine_amount) if payment.book_fine_amount else 0.0,
                'fine_amount': float(payment.fine_amount) if payment.fine_amount else 0.0,
                'adjusted_amount': float(payment.adjusted_amount) if payment.adjusted_amount else 0.0,
            })
        
        return {'data': data}

class ExportReportView(ReportBaseView):
    """Export report to Excel"""
    
    def get(self, request):
        export_type = request.GET.get('type', 'all-tabs')
        member_ids = request.GET.getlist('member_ids[]')
        filters_json = request.GET.get('filters', '{}')
        tab_filters_json = request.GET.get('tab_filters', '{}')
        
        try:
            filters = json.loads(filters_json)
            tab_filters = json.loads(tab_filters_json)
        except:
            filters = {}
            tab_filters = {}
        
        db = self.get_library_db()
        
        # Create Excel file in memory
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output)
        
        # Define formats
        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#4CAF50',
            'color': 'white',
            'border': 1,
            'align': 'center',
            'valign': 'vcenter'
        })
        
        cell_format = workbook.add_format({
            'border': 1,
            'align': 'left',
            'valign': 'vcenter'
        })
        
        if export_type == 'all-tabs':
            # Export all tabs to different sheets
            self.export_all_tabs(workbook, db, member_ids, filters, tab_filters, 
                               header_format, cell_format)
        else:
            # Export specific tab
            self.export_single_tab(workbook, export_type, db, member_ids, 
                                 tab_filters.get(export_type, {}), 
                                 header_format, cell_format)
        
        workbook.close()
        output.seek(0)
        
        # Create response
        response = HttpResponse(
            output.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename="member_report.xlsx"'
        
        return response
    
    def export_all_tabs(self, workbook, db, member_ids, filters, tab_filters, header_format, cell_format):
        """Export all tabs to different sheets"""

        # Sheet 1: Member Details
        if self.should_export_tab('member-details', tab_filters):
            self.create_member_details_sheet(workbook, db, member_ids, 
                                           tab_filters.get('member-details', {}),
                                           header_format, cell_format)

        # Sheet 2: Membership Details
        if self.should_export_tab('membership-details', tab_filters):
            self.create_membership_details_sheet(workbook, db, member_ids,
                                               tab_filters.get('membership-details', {}),
                                               header_format, cell_format)

        # Sheet 3: Loan
        if self.should_export_tab('loan', tab_filters):
            self.create_loan_sheet(workbook, db, member_ids,
                                 tab_filters.get('loan', {}),
                                 header_format, cell_format)

        # Sheet 4: Transactions
        if self.should_export_tab('transactions', tab_filters):
            self.create_transactions_sheet(workbook, db, member_ids,
                                         tab_filters.get('transactions', {}),
                                         header_format, cell_format)

        # Sheet 5: Physical Visits
        if self.should_export_tab('physical-visit', tab_filters):
            self.create_physical_visits_sheet(workbook, db, member_ids,
                                            tab_filters.get('physical-visit', {}),
                                            header_format, cell_format)

        # Sheet 6: Virtual Usage
        if self.should_export_tab('virtual-usage', tab_filters):
            self.create_virtual_usage_sheet(workbook, db, member_ids,
                                          tab_filters.get('virtual-usage', {}),
                                          header_format, cell_format)

        # Sheet 7: Payments
        if self.should_export_tab('payments', tab_filters):
            self.create_payments_sheet(workbook, db, member_ids,
                                     tab_filters.get('payments', {}),
                                     header_format, cell_format)

    def should_export_tab(self, tab_name, tab_filters):
        """Check if a tab should be exported based on filters"""
        # If tab_filters contains the tab, check if it's marked for export
        # You might want to add a parameter to track which tabs to export
        return True  # For now, export all tabs
    
    def export_single_tab(self, workbook, export_type, db, member_ids, filters, header_format, cell_format):
        """Export a single tab to Excel sheet"""
        if export_type == 'member-details':
            self.export_member_details_to_excel(workbook, db, member_ids, filters, header_format, cell_format)
        elif export_type == 'membership-details':
            self.export_membership_details_to_excel(workbook, db, member_ids, filters, header_format, cell_format)
        elif export_type == 'loan':
            self.export_loan_to_excel(workbook, db, member_ids, filters, header_format, cell_format)
        elif export_type == 'transactions':
            self.export_transactions_to_excel(workbook, db, member_ids, filters, header_format, cell_format)
        elif export_type == 'physical-visit':
            self.export_physical_visits_to_excel(workbook, db, member_ids, filters, header_format, cell_format)
        elif export_type == 'virtual-usage':
            self.export_virtual_usage_to_excel(workbook, db, member_ids, filters, header_format, cell_format)
        elif export_type == 'payments':
            self.export_payments_to_excel(workbook, db, member_ids, filters, header_format, cell_format)
        else:
            # Create a placeholder sheet if tab type is unknown
            worksheet = workbook.add_worksheet(export_type.replace('-', ' ').title())
            worksheet.write(0, 0, 'No data available for this tab', header_format)
            # Add more sheets for other tabs...
    
    def create_member_details_sheet(self, workbook, db, member_ids, filters, 
                                   header_format, cell_format):
        """Create member details sheet"""
        worksheet = workbook.add_worksheet('Member Details')
        
        # Define headers
        headers = [
            'First Name', 'Middle Name', 'Last Name', 'First Name (Mar)', 
            'Last Name (Mar)', 'Middle Name (Mar)', 'Membership Type',
            'Member Type', 'Membership Code', 'Membership Date',
            'Renewal From Date', 'Renewal To Date', 'User ID', 'Ward',
            'Pincode', 'Local Address', 'Mobile No', 'Email', 'Occupation',
            'Office Phone', 'Education', 'Institute Name', 'Recommender Details',
            'Date of Birth', 'Aadhar No', 'Address Same as Aadhar',
            'Resident of NMMC', 'Status', 'Created At', 'Created By',
            'Updated At', 'Updated By', 'Approved By', 'Approved Date'
        ]
        
        # Write headers
        for col, header in enumerate(headers):
            worksheet.write(0, col, header, header_format)
            worksheet.set_column(col, col, 20)  # Set column width
        
        # Get data
        qs = MembershipDetails.objects.using(db).filter(id__in=member_ids)
        
        # Apply filters
        qs = self.apply_member_details_filters(qs, filters)
        
        # Write data
        row = 1
        for member in qs:
            worksheet.write(row, 0, member.first_name or '', cell_format)
            worksheet.write(row, 1, member.middle_name or '', cell_format)
            # ... write all other columns
            
            row += 1
    
    def apply_member_details_filters(self, qs, filters):
        """Apply filters to member details queryset"""
        if filters.get('membership_month_from'):
            qs = qs.filter(from_date__gte=filters['membership_month_from'])
        if filters.get('membership_month_to'):
            qs = qs.filter(from_date__lte=filters['membership_month_to'])
        # ... apply other filters
        
        return qs

    def create_membership_details_sheet(self, workbook, db, member_ids, filters, header_format, cell_format):
        """Create membership details sheet for export_all_tabs method"""
        # This method should use the same logic as export_membership_details_to_excel
        self.export_membership_details_to_excel(workbook, db, member_ids, filters, header_format, cell_format)
    # reports/views.py - Add these methods to ExportAllDataView class

    def create_member_details_sheet(self, workbook, db, member_ids, filters, header_format, cell_format):
        """Create member details sheet for export_all_tabs method"""
        self.export_member_details_to_excel(workbook, db, member_ids, filters, header_format, cell_format)
    
    def create_loan_sheet(self, workbook, db, member_ids, filters, header_format, cell_format):
        """Create loan sheet for export_all_tabs method"""
        self.export_loan_to_excel(workbook, db, member_ids, filters, header_format, cell_format)
    
    def create_transactions_sheet(self, workbook, db, member_ids, filters, header_format, cell_format):
        """Create transactions sheet for export_all_tabs method"""
        self.export_transactions_to_excel(workbook, db, member_ids, filters, header_format, cell_format)
    
    def create_payments_sheet(self, workbook, db, member_ids, filters, header_format, cell_format):
        """Create payments sheet for export_all_tabs method"""
        self.export_payments_to_excel(workbook, db, member_ids, filters, header_format, cell_format)
    
    def create_physical_visits_sheet(self, workbook, db, member_ids, filters, header_format, cell_format):
        """Create physical visits sheet for export_all_tabs method"""
        self.export_physical_visits_to_excel(workbook, db, member_ids, filters, header_format, cell_format)
    
    def create_virtual_usage_sheet(self, workbook, db, member_ids, filters, header_format, cell_format):
        """Create virtual usage sheet for export_all_tabs method"""
        self.export_virtual_usage_to_excel(workbook, db, member_ids, filters, header_format, cell_format)
# reports/views.py - ADD THESE MISSING VIEWS

from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import tempfile
import os
from django.core.files.storage import FileSystemStorage
from django.db import transaction

class SaveReportSessionView(ReportBaseView):
    """Save current report session"""
    
    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def post(self, request):
        try:
            data = json.loads(request.body)
            
            session = ReportSession.objects.create(
                name=data.get('name', f"Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}"),
                report_type='member',
                filters_json=data.get('filters', {}),
                selected_members_json=data.get('selected_members', []),
                created_by=request.user if request.user.is_authenticated else None
            )
            
            return JsonResponse({
                'success': True,
                'session_id': session.id,
                'message': 'Report session saved successfully'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)

class LoadReportSessionView(ReportBaseView):
    """Load saved report session"""
    
    def get(self, request, session_id):
        try:
            session = ReportSession.objects.get(id=session_id, created_by=request.user)
            
            return JsonResponse({
                'success': True,
                'session': {
                    'id': session.id,
                    'name': session.name,
                    'filters': session.filters_json,
                    'selected_members': session.selected_members_json
                }
            })
        except ReportSession.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Session not found'
            }, status=404)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)

class GetMemberOptionsView(ReportBaseView):
    """Get filter options for member types, wards, etc."""
    
    def get(self, request):
        db = self.get_library_db()
        
        # Get member types
        member_types = parameter_master_L01.objects.using(db).filter(isactive=1,parameter_name='MembershipForm').values('parameter_id', 'parameter_value')
        
        # Get unique wards
        wards = WardMaster.objects.using(db).filter(is_active=1).values('ward_name', 'ward_name').distinct()
        
        # Get membership types
        membership_types = MembershipMaster.objects.using(db).filter(
            isactive=1
        ).values('id', 'membership_type_en')
        
        actionperformed_list  = MembershipDetails.objects.using(db).filter(isactive=1).exclude(actionperformed__isnull=True).values('actionperformed').distinct().order_by('actionperformed')
        
        return JsonResponse({
            'member_types': list(member_types),
            'wards': list(wards),
            'membership_types': list(membership_types),
            'actionperformed_list': list(actionperformed_list)
        })

class GetFilterCountsView(ReportBaseView):
    """Get count of applied filters for each tab"""
    
    def post(self, request):
        try:
            data = json.loads(request.body)
            tab_name = data.get('tab_name')
            filters = data.get('filters', {})
            member_ids = data.get('member_ids', [])
            
            db = self.get_library_db()
            count = 0
            
            if tab_name == 'member-details':
                qs = MembershipDetails.objects.using(db).filter(id__in=member_ids)
                count = self.apply_member_details_filters(qs, filters).count()
            elif tab_name == 'membership-details':
                qs = MembershipDetails.objects.using(db).filter(id__in=member_ids)
                qs_history = MembershipDetailsHistory.objects.using(db).filter(
                    membership_id__in=member_ids
                )
                count = self.apply_membership_details_filters(qs, qs_history, filters)
            elif tab_name == 'loan':
                qs = CirculationTransaction.objects.using(db).filter(
                    member_id__in=member_ids,
                    transaction_type='issue'
                )
                count = self.apply_loan_filters(qs, filters).count()
            elif tab_name == 'transactions':
                qs = CirculationTransaction.objects.using(db).filter(
                    member_id__in=member_ids
                )
                count = self.apply_transaction_filters(qs, filters).count()
            elif tab_name == 'physical-visit':
                # Get membership codes
                members = MembershipDetails.objects.using(db).filter(id__in=member_ids)
                member_codes = [m.membership_code for m in members if m.membership_code]
                qs = MemberEntryExit.objects.using(db).filter(
                    membership_code__in=member_codes
                )
                count = self.apply_physical_visit_filters(qs, filters).count()
            elif tab_name == 'virtual-usage':
                qs_login = MemberLoginSession.objects.using(db).filter(
                    member_id__in=member_ids
                )
                qs_activity = MemberScreenActivity.objects.using(db).filter(
                    session__member_id__in=member_ids
                )
                count = self.apply_virtual_usage_filters(qs_login, qs_activity, filters)
            elif tab_name == 'payments':
                qs = PaymentDetails.objects.using(db).filter(
                    membership_id__in=member_ids
                )
                count = self.apply_payment_filters(qs, filters).count()
            else:
                return JsonResponse({'count': 0, 'error': 'Invalid tab name'})
            
            return JsonResponse({'count': count})
        except Exception as e:
            return JsonResponse({'count': 0, 'error': str(e)})
    
    def apply_member_details_filters(self, qs, filters):
        """Apply filters to member details data"""
        if filters.get('membership_month_from'):
            start_date = parse_month_start(filters['membership_month_from'])
            qs = qs.filter(from_date__gte=start_date)
        if filters.get('membership_month_to'):
            end_date = parse_month_end(filters['membership_month_to'])
            qs = qs.filter(from_date__lte=end_date)
        if filters.get('membership_type'):
            qs = qs.filter(membership_id__in=filters['membership_type'])
        if filters.get('member_type'):
            qs = qs.filter(member_type_id__in=filters['member_type'])
        if filters.get('ward'):
            qs = qs.filter(ward__in=filters['ward'])
        if filters.get('status'):
            qs = qs.filter(status_id__in=filters['status'])
        if filters.get('renewal_due_month'):
            start = parse_month_start(filters['renewal_due_month'])
            end = parse_month_end(filters['renewal_due_month'])
            qs = qs.filter(to_date__range=(start, end))
        
        return qs
    
    def apply_membership_details_filters(self, qs, qs_history, filters):
        """Apply filters to membership details data"""
        count = 0
        
        # Apply filters to current memberships
        filtered_qs = qs
        if filters.get('from_date'):
            filtered_qs = filtered_qs.filter(from_date__gte=filters['from_date'])
        if filters.get('to_date'):
            filtered_qs = filtered_qs.filter(to_date__lte=filters['to_date'])
        if filters.get('gap_period') == 'has_gap':
            filtered_qs = filtered_qs.filter(gap_months__gt=0)
        elif filters.get('gap_period') == 'no_gap':
            filtered_qs = filtered_qs.filter(gap_months=0)
        if filters.get('action_performed'):
            filtered_qs = filtered_qs.filter(
                actionperformed__icontains=filters['action_performed']
            )
        
        count += filtered_qs.count()
        
        # Apply filters to historical data
        filtered_history = qs_history
        if filters.get('from_date'):
            filtered_history = filtered_history.filter(from_date__gte=filters['from_date'])
        if filters.get('to_date'):
            filtered_history = filtered_history.filter(to_date__lte=filters['to_date'])
        if filters.get('gap_period') == 'has_gap':
            filtered_history = filtered_history.filter(gap_months__gt=0)
        elif filters.get('gap_period') == 'no_gap':
            filtered_history = filtered_history.filter(gap_months=0)
        if filters.get('action_performed'):
            filtered_history = filtered_history.filter(
                actionperformed__icontains=filters['action_performed']
            )
        
        count += filtered_history.count()
        
        return count
    
    def apply_loan_filters(self, qs, filters):
        """Apply filters to loan data"""
        if filters.get('from_date'):
            qs = qs.filter(issue_date__gte=filters['from_date'])
        if filters.get('to_date'):
            qs = qs.filter(issue_date__lte=filters['to_date'])
        if filters.get('overdue') == 'overdue':
            qs = qs.filter(days_overdue_count__gt=0)
        elif filters.get('overdue') == 'not_overdue':
            qs = qs.filter(days_overdue_count=0)
        if filters.get('fine_status') == 'paid':
            qs = qs.filter(fine_status='paid')
        elif filters.get('fine_status') == 'not_paid':
            qs = qs.filter(fine_status__in=['unpaid', 'pending', None])
        
        return qs
    
    def apply_transaction_filters(self, qs, filters):
        """Apply filters to transaction data"""
        if filters.get('from_date'):
            qs = qs.filter(created_at__date__gte=filters['from_date'])
        if filters.get('to_date'):
            qs = qs.filter(created_at__date__lte=filters['to_date'])
        if filters.get('late_returns') == 'late':
            qs = qs.filter(days_overdue_count__gt=0)
        elif filters.get('late_returns') == 'on_time':
            qs = qs.filter(days_overdue_count=0)
        if filters.get('fine_status') == 'paid':
            qs = qs.filter(fine_status='paid')
        elif filters.get('fine_status') == 'not_paid':
            qs = qs.filter(fine_status__in=['unpaid', 'pending', None])
        
        return qs
    
    def apply_physical_visit_filters(self, qs, filters):
        """Apply filters to physical visit data"""
        if filters.get('from_date'):
            qs = qs.filter(entry_time__date__gte=filters['from_date'])
        if filters.get('to_date'):
            qs = qs.filter(entry_time__date__lte=filters['to_date'])
        if filters.get('activity_type') == 'entry':
            qs = qs.filter(exit_time__isnull=True)
        elif filters.get('activity_type') == 'exit':
            qs = qs.filter(exit_time__isnull=False)
        elif filters.get('activity_type') == 'completed':
            qs = qs.filter(entry_time__isnull=False, exit_time__isnull=False)
        if filters.get('remarks_search'):
            qs = qs.filter(remark__icontains=filters['remarks_search'])
        
        return qs
    
    def apply_virtual_usage_filters(self, qs_login, qs_activity, filters):
        """Apply filters to virtual usage data"""
        count = 0
        
        # Apply filters to login sessions
        if filters.get('from_date'):
            qs_login = qs_login.filter(login_time__date__gte=filters['from_date'])
        if filters.get('to_date'):
            qs_login = qs_login.filter(login_time__date__lte=filters['to_date'])
        if filters.get('activity_type') == 'login':
            count += qs_login.count()
            return count
        if filters.get('device_type'):
            qs_login = qs_login.filter(device_type__icontains=filters['device_type'])
        
        # Apply filters to screen activities
        if filters.get('from_date'):
            qs_activity = qs_activity.filter(visited_at__date__gte=filters['from_date'])
        if filters.get('to_date'):
            qs_activity = qs_activity.filter(visited_at__date__lte=filters['to_date'])
        if filters.get('activity_type') == 'screen':
            count += qs_activity.count()
            return count
        if filters.get('screen_name'):
            qs_activity = qs_activity.filter(screen_name__icontains=filters['screen_name'])
        if filters.get('device_type'):
            qs_activity = qs_activity.filter(session__device_type__icontains=filters['device_type'])
        
        count += qs_login.count() + qs_activity.count()
        return count
    
    def apply_payment_filters(self, qs, filters):
        """Apply filters to payment data"""
        if filters.get('from_date'):
            qs = qs.filter(payment_date__gte=filters['from_date'])
        if filters.get('to_date'):
            qs = qs.filter(payment_date__lte=filters['to_date'])
        if filters.get('payment_type'):
            qs = qs.filter(payment_type=filters['payment_type'])
        
        return qs

class ExportAllDataView(ReportBaseView):
    """Export all tabs data to Excel with multiple sheets"""
    
    def get(self, request):
        member_ids = request.GET.getlist('member_ids[]')
        filters_json = request.GET.get('filters', '{}')
        tab_filters_json = request.GET.get('tab_filters', '{}')
        
        try:
            filters = json.loads(filters_json)
            tab_filters = json.loads(tab_filters_json)
        except:
            filters = {}
            tab_filters = {}
        
        db = self.get_library_db()
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
            output_path = tmp.name
        
        try:
            # Create Excel writer
            with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                # Export each tab to separate sheet
                self.export_member_details_to_excel(writer, db, member_ids, 
                                                   tab_filters.get('member-details', {}))
                self.export_membership_details_to_excel(writer, db, member_ids,
                                                       tab_filters.get('membership-details', {}))
                self.export_loan_to_excel(writer, db, member_ids,
                                         tab_filters.get('loan', {}))
                self.export_transactions_to_excel(writer, db, member_ids,
                                                tab_filters.get('transactions', {}))
                self.export_payments_to_excel(writer, db, member_ids,
                                            tab_filters.get('payments', {}))
                self.export_physical_visits_to_excel(writer, db, member_ids,
                                                   tab_filters.get('physical-visit', {}))
                self.export_virtual_usage_to_excel(writer, db, member_ids,
                                                 tab_filters.get('virtual-usage', {}))
            
            # Read file and prepare response
            with open(output_path, 'rb') as f:
                response = HttpResponse(
                    f.read(),
                    content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                )
                response['Content-Disposition'] = 'attachment; filename="member_complete_report.xlsx"'
            
            # Clean up
            os.unlink(output_path)
            
            # Log export
            if request.user.is_authenticated:
                ReportExport.objects.create(
                    export_type='complete_report',
                    file_path='exported_to_client',
                    filters_applied={'filters': filters, 'tab_filters': tab_filters},
                    exported_by=request.user
                )
            
            return response
            
        except Exception as e:
            # Clean up on error
            if os.path.exists(output_path):
                os.unlink(output_path)
            return JsonResponse({'error': str(e)}, status=500)
    
    # reports/views.py - Complete this method

def export_member_details_to_excel(self, writer, db, member_ids, filters, header_format=None, cell_format=None):
    """Export member details to Excel sheet"""
    qs = MembershipDetails.objects.using(db).filter(id__in=member_ids)
    qs = self.apply_member_details_filters(qs, filters)
    
    data = []
    for member in qs.select_related('membership', 'status', 'member_type'):
        data.append({
            'First Name': member.first_name or '',
            'Middle Name': member.middle_name or '',
            'Last Name': member.last_name or '',
            'First Name (Marathi)': member.first_name_mar or '',
            'Last Name (Marathi)': member.last_name_mar or '',
            'Middle Name (Marathi)': member.middle_name_mar or '',
            'Membership Type': member.membership.membership_type if member.membership else '',
            'Member Type': member.member_type.name if member.member_type else '',
            'Membership Code': member.membership_code or '',
            'Membership Date': member.created_at.strftime('%Y-%m-%d') if member.created_at else '',
            'Renewal From Date': member.from_date.strftime('%Y-%m-%d') if member.from_date else '',
            'Renewal To Date': member.to_date.strftime('%Y-%m-%d') if member.to_date else '',
            'User ID': member.user_id or '',
            'Ward': member.ward or '',
            'Pincode': member.pincode or '',
            'Local Address': member.local_address or '',
            'Mobile No': member.mobile_no or '',
            'Email': member.email or '',
            'Occupation': member.occupation or '',
            'Office Phone': member.office_phone or '',
            'Education': member.education or '',
            'Institute Name': member.institute_name or '',
            'Recommender Details': member.recommender_details or '',
            'Date of Birth': member.dob.strftime('%Y-%m-%d') if member.dob else '',
            'Aadhar No': member.aadhar_no or '',
            'Address Same as Aadhar': 'Yes' if member.address_same_as_aadhar == 1 else 'No',
            'Resident of NMMC': 'Yes' if member.is_resident_of_nmmc == 1 else 'No',
            'Status': 'Active' if member.isactive == 1 else 'Inactive',
            'Created At': member.created_at.strftime('%Y-%m-%d %H:%M') if member.created_at else '',
            'Created By': member.created_by or '',
            'Updated At': member.updated_at.strftime('%Y-%m-%d %H:%M') if member.updated_at else '',
            'Updated By': member.updated_by or '',
            'Approved By': member.reviewed or '',
            'Approved Date': member.reviewed_at.strftime('%Y-%m-%d %H:%M') if member.reviewed_at else '',
        })
    
    df = pd.DataFrame(data)
    df.to_excel(writer, sheet_name='Member Details', index=False)
    
    # Auto-adjust column widths
    if 'Member Details' in writer.sheets:
        worksheet = writer.sheets['Member Details']
        for column in df:
            column_width = max(df[column].astype(str).map(len).max(), len(column)) + 2
            col_idx = df.columns.get_loc(column)
            worksheet.column_dimensions[chr(65 + col_idx)].width = column_width
    
    def export_membership_details_to_excel(self, writer, db, member_ids, filters):
        """Export membership details to Excel sheet"""
        # Current memberships
        current_qs = MembershipDetails.objects.using(db).filter(
            id__in=member_ids
        ).select_related('membership', 'member_type')
        
        # Historical data
        history_qs = MembershipDetailsHistory.objects.using(db).filter(
            membership_id__in=member_ids
        ).select_related('membershipmaster', 'member_type')
        
        # Apply filters to both querysets
        current_qs = self.apply_membership_details_filters_export(current_qs, filters)
        history_qs = self.apply_membership_details_filters_export_history(history_qs, filters)
        
        data = []
        
        # Current memberships
        for member in current_qs:
            data.append({
                'Record Type': 'Current',
                'First Name': member.first_name or '',
                'Middle Name': member.middle_name or '',
                'Last Name': member.last_name or '',
                'First Name (Marathi)': member.first_name_mar or '',
                'Middle Name (Marathi)': member.middle_name_mar or '',
                'Last Name (Marathi)': member.last_name_mar or '',
                'Action Performed': member.actionperformed or '',
                'From Date': member.from_date.strftime('%Y-%m-%d') if member.from_date else '',
                'To Date': member.to_date.strftime('%Y-%m-%d') if member.to_date else '',
                'Membership Duration': member.membership_duration or 0,
                'Deposit': float(member.deposit) if member.deposit else 0.0,
                'Entry Fees': float(member.entry_fees) if member.entry_fees else 0.0,
                'Subscription': float(member.subscription) if member.subscription else 0.0,
                'Fine Calculated At': member.fine_calculated_at.strftime('%Y-%m-%d %H:%M:%S') if member.fine_calculated_at else '',
                'Gap Fine (Subscription)': float(member.gap_fine) if member.gap_fine else 0.0,
                'Gap Fine (Delay)': float(member.late_fee) if member.late_fee else 0.0,
                'Gap Months': member.gap_months or 0,
                'Late Fee': float(member.late_fee) if member.late_fee else 0.0,
                'Total Fine Membership': float(member.total_fine_membership) if member.total_fine_membership else 0.0,
                'Gap Period From': member.gap_period_from or '',
                'Gap Period To': member.gap_period_to or '',
                'Gap Subscription Delay': float(member.gap_subscription_delay) if member.gap_subscription_delay else 0.0,
                'Changed At': member.updated_at.strftime('%Y-%m-%d %H:%M:%S') if member.updated_at else '',
                'Changed By': member.updated_by or '',
                'Membership Type': member.membership.membership_type if member.membership else '',
                'Member Type': member.member_type.name if member.member_type else '',
                'Membership Code': member.membership_code or '',
                'User ID': member.user_id or '',
                'Status': 'Active' if member.isactive == 1 else 'Inactive',
            })
        
        # Historical data
        for history in history_qs:
            data.append({
                'Record Type': 'Historical',
                'First Name': history.first_name or '',
                'Middle Name': history.middle_name or '',
                'Last Name': history.last_name or '',
                'First Name (Marathi)': history.first_name_mar or '',
                'Middle Name (Marathi)': history.middle_name_mar or '',
                'Last Name (Marathi)': history.last_name_mar or '',
                'Action Performed': history.actionperformed or '',
                'From Date': history.from_date.strftime('%Y-%m-%d') if history.from_date else '',
                'To Date': history.to_date.strftime('%Y-%m-%d') if history.to_date else '',
                'Membership Duration': history.membership_duration or 0,
                'Deposit': float(history.deposit) if history.deposit else 0.0,
                'Entry Fees': float(history.entry_fees) if history.entry_fees else 0.0,
                'Subscription': float(history.subscription) if history.subscription else 0.0,
                'Fine Calculated At': history.fine_calculated_at.strftime('%Y-%m-%d %H:%M:%S') if history.fine_calculated_at else '',
                'Gap Fine (Subscription)': float(history.gap_fine) if history.gap_fine else 0.0,
                'Gap Fine (Delay)': float(history.late_fee) if history.late_fee else 0.0,
                'Gap Months': history.gap_months or 0,
                'Late Fee': float(history.late_fee) if history.late_fee else 0.0,
                'Total Fine Membership': float(history.total_fine_membership) if history.total_fine_membership else 0.0,
                'Gap Period From': history.gap_period_from or '',
                'Gap Period To': history.gap_period_to or '',
                'Gap Subscription Delay': float(history.gap_subscription_delay) if history.gap_subscription_delay else 0.0,
                'Changed At': history.changed_at.strftime('%Y-%m-%d %H:%M:%S') if history.changed_at else '',
                'Changed By': history.changed_by or '',
                'Membership Type': history.membershipmaster.membership_type if history.membershipmaster else '',
                'Member Type': history.member_type.name if history.member_type else '',
                'Membership Code': history.membership_code or '',
                'User ID': history.user_id or '',
                'Status': 'Active' if history.isactive == 1 else 'Inactive',
            })
        
        df = pd.DataFrame(data)
        df.to_excel(writer, sheet_name='Membership Details', index=False)
        
        # Auto-adjust column widths
        if 'Membership Details' in writer.sheets:
            worksheet = writer.sheets['Membership Details']
            for column in df:
                column_width = max(df[column].astype(str).map(len).max(), len(column)) + 2
                col_idx = df.columns.get_loc(column)
                worksheet.column_dimensions[chr(65 + col_idx)].width = column_width
    
    def apply_membership_details_filters_export(self, qs, filters):
        """Apply filters for current membership export"""
        if filters.get('from_date'):
            qs = qs.filter(from_date__gte=filters['from_date'])
        if filters.get('to_date'):
            qs = qs.filter(to_date__lte=filters['to_date'])
        
        if filters.get('gap_period') == 'has_gap':
            qs = qs.filter(gap_months__gt=0)
        elif filters.get('gap_period') == 'no_gap':
            qs = qs.filter(gap_months=0)
        
        if filters.get('action_performed'):
            qs = qs.filter(actionperformed__icontains=filters['action_performed'])
        
        return qs
    
    def apply_membership_details_filters_export_history(self, qs, filters):
        """Apply filters for historical membership export"""
        if filters.get('from_date'):
            qs = qs.filter(from_date__gte=filters['from_date'])
        if filters.get('to_date'):
            qs = qs.filter(to_date__lte=filters['to_date'])
        
        if filters.get('gap_period') == 'has_gap':
            qs = qs.filter(gap_months__gt=0)
        elif filters.get('gap_period') == 'no_gap':
            qs = qs.filter(gap_months=0)
        
        if filters.get('action_performed'):
            qs = qs.filter(actionperformed__icontains=filters['action_performed'])
        
        return qs

    def export_loan_to_excel(self, writer, db, member_ids, filters):
        """Export loan data to Excel sheet"""
        qs = CirculationTransaction.objects.using(db).filter(
            member_id__in=member_ids,
            transaction_type='issue'
        ).select_related('catalog', 'accession', 'member').order_by('-issue_date')
        
        # Apply filters
        qs = self.apply_loan_filters_export(qs, filters)
        
        data = []
        for transaction in qs:
            data.append({
                'Membership Code': transaction.member.membership_code if transaction.member else '',
                'Barcode': transaction.barcode or '',
                'Accession ID': transaction.accession.accession_no if transaction.accession else '',
                'Catalog Ref Number': transaction.catalog.cat_ref_num if transaction.catalog else '',
                'Book Title': transaction.catalog.title if transaction.catalog else '',
                'Author': transaction.catalog.author1 if transaction.catalog else '',
                'Issue Date': transaction.issue_date.strftime('%Y-%m-%d') if transaction.issue_date else '',
                'Due Date': transaction.due_date.strftime('%Y-%m-%d') if transaction.due_date else '',
                'Return Date': transaction.return_date.strftime('%Y-%m-%d') if transaction.return_date else '',
                'Days Overdue': transaction.days_overdue_count or 0,
                'Fine Amount': float(transaction.fine_amount) if transaction.fine_amount else 0.0,
                'Book Fine Amount': float(transaction.book_fine_amount) if transaction.book_fine_amount else 0.0,
                'Total Fine': float(transaction.total_fine) if transaction.total_fine else 0.0,
                'Adjusted Fine': float(transaction.adjusted_fine) if transaction.adjusted_fine else 0.0,
                'Fine Status': transaction.fine_status or '',
                'Fine Paid Date': transaction.fine_paid_date.strftime('%Y-%m-%d') if transaction.fine_paid_date else '',
                'Transaction Type': transaction.transaction_type or '',
                'Transaction Status': transaction.transaction_status or '',
                'Issued By': transaction.issued_by or '',
                'Received By': transaction.received_by or '',
                'Membership Code (Transaction)': transaction.membership_code or '',
                'Return Condition': transaction.return_condition.status_name if transaction.return_condition else '',
                'Remarks': transaction.remarks or '',
                'Created At': transaction.created_at.strftime('%Y-%m-%d %H:%M:%S') if transaction.created_at else '',
                'Created By': transaction.created_by or '',
                'Updated At': transaction.updated_at.strftime('%Y-%m-%d %H:%M:%S') if transaction.updated_at else '',
                'Updated By': transaction.updated_by or '',
            })
        
        df = pd.DataFrame(data)
        df.to_excel(writer, sheet_name='Loan Transactions', index=False)
        
        # Auto-adjust column widths
        if 'Loan Transactions' in writer.sheets:
            worksheet = writer.sheets['Loan Transactions']
            for column in df:
                column_width = max(df[column].astype(str).map(len).max(), len(column)) + 2
                col_idx = df.columns.get_loc(column)
                worksheet.column_dimensions[chr(65 + col_idx)].width = column_width
    
    def apply_loan_filters_export(self, qs, filters):
        """Apply filters for loan export"""
        if filters.get('from_date'):
            qs = qs.filter(issue_date__gte=filters['from_date'])
        if filters.get('to_date'):
            qs = qs.filter(issue_date__lte=filters['to_date'])
        
        if filters.get('overdue') == 'overdue':
            qs = qs.filter(days_overdue_count__gt=0)
        elif filters.get('overdue') == 'not_overdue':
            qs = qs.filter(days_overdue_count=0)
        
        if filters.get('fine_status') == 'paid':
            qs = qs.filter(fine_status='paid')
        elif filters.get('fine_status') == 'not_paid':
            qs = qs.filter(fine_status__in=['unpaid', 'pending', None])
        
        return qs
    
    def export_transactions_to_excel(self, writer, db, member_ids, filters):
        """Export all transactions to Excel sheet"""
        qs = CirculationTransaction.objects.using(db).filter(
            member_id__in=member_ids
        ).select_related('catalog', 'accession', 'member', 'return_condition').order_by('-created_at')
        
        # Apply filters
        qs = self.apply_transaction_filters_export(qs, filters)
        
        data = []
        for transaction in qs:
            data.append({
                'Member Name': f"{transaction.member.first_name or ''} {transaction.member.last_name or ''}".strip(),
                'Membership Code': transaction.member.membership_code if transaction.member else '',
                'Barcode': transaction.barcode or '',
                'Accession ID': transaction.accession.accession_no if transaction.accession else '',
                'Catalog Ref Number': transaction.catalog.cat_ref_num if transaction.catalog else '',
                'Book Title': transaction.catalog.title if transaction.catalog else '',
                'Transaction Type': transaction.transaction_type or '',
                'Transaction Status': transaction.transaction_status or '',
                'Issue Date': transaction.issue_date.strftime('%Y-%m-%d') if transaction.issue_date else '',
                'Due Date': transaction.due_date.strftime('%Y-%m-%d') if transaction.due_date else '',
                'Issued By': transaction.issued_by or '',
                'Created At': transaction.created_at.strftime('%Y-%m-%d %H:%M:%S') if transaction.created_at else '',
                'Return Date': transaction.return_date.strftime('%Y-%m-%d') if transaction.return_date else '',
                'Received By': transaction.received_by or '',
                'Days Overdue': transaction.days_overdue_count or 0,
                'Fine Amount': float(transaction.fine_amount) if transaction.fine_amount else 0.0,
                'Book Fine Amount': float(transaction.book_fine_amount) if transaction.book_fine_amount else 0.0,
                'Total Fine': float(transaction.total_fine) if transaction.total_fine else 0.0,
                'Adjusted Fine': float(transaction.adjusted_fine) if transaction.adjusted_fine else 0.0,
                'Fine Status': transaction.fine_status or '',
                'Fine Paid Date': transaction.fine_paid_date.strftime('%Y-%m-%d') if transaction.fine_paid_date else '',
                'Return Condition': transaction.return_condition.status_name if transaction.return_condition else '',
                'Remarks': transaction.remarks or '',
                'Updated At': transaction.updated_at.strftime('%Y-%m-%d %H:%M:%S') if transaction.updated_at else '',
                'Updated By': transaction.updated_by or '',
            })
        
        df = pd.DataFrame(data)
        df.to_excel(writer, sheet_name='All Transactions', index=False)
        
        # Auto-adjust column widths
        if 'All Transactions' in writer.sheets:
            worksheet = writer.sheets['All Transactions']
            for column in df:
                column_width = max(df[column].astype(str).map(len).max(), len(column)) + 2
                col_idx = df.columns.get_loc(column)
                worksheet.column_dimensions[chr(65 + col_idx)].width = column_width
    
    def apply_transaction_filters_export(self, qs, filters):
        """Apply filters for transaction export"""
        if filters.get('from_date'):
            qs = qs.filter(created_at__date__gte=filters['from_date'])
        if filters.get('to_date'):
            qs = qs.filter(created_at__date__lte=filters['to_date'])
        
        if filters.get('late_returns') == 'late':
            qs = qs.filter(days_overdue_count__gt=0)
        elif filters.get('late_returns') == 'on_time':
            qs = qs.filter(days_overdue_count=0)
        
        if filters.get('fine_status') == 'paid':
            qs = qs.filter(fine_status='paid')
        elif filters.get('fine_status') == 'not_paid':
            qs = qs.filter(fine_status__in=['unpaid', 'pending', None])
        
        return qs
    
    def export_physical_visits_to_excel(self, writer, db, member_ids, filters):
        """Export physical visits to Excel sheet"""
        # Get membership codes
        members = MembershipDetails.objects.using(db).filter(
            id__in=member_ids
        ).values('id', 'membership_code', 'first_name', 'last_name')
        
        member_map = {m['membership_code']: m for m in members if m['membership_code']}
        member_codes = list(member_map.keys())
        
        qs = MemberEntryExit.objects.using(db).filter(
            membership_code__in=member_codes
        ).order_by('-entry_time')
        
        # Apply filters
        if filters.get('from_date'):
            qs = qs.filter(entry_time__date__gte=filters['from_date'])
        if filters.get('to_date'):
            qs = qs.filter(entry_time__date__lte=filters['to_date'])
        
        data = []
        for visit in qs:
            member = member_map.get(visit.membership_code, {})
            data.append({
                'Member Name': f"{member.get('first_name', '')} {member.get('last_name', '')}".strip(),
                'Membership Code': visit.membership_code,
                'Entry Time': visit.entry_time.strftime('%Y-%m-%d %H:%M:%S') if visit.entry_time else '',
                'Exit Time': visit.exit_time.strftime('%Y-%m-%d %H:%M:%S') if visit.exit_time else '',
                'Duration': self.calculate_visit_duration(visit),
                'Remark': visit.remark or '',
                'Created At': visit.created_at.strftime('%Y-%m-%d %H:%M:%S') if visit.created_at else '',
                'Role ID': visit.role_id or ''
            })
        
        df = pd.DataFrame(data)
        df.to_excel(writer, sheet_name='Physical Visits', index=False)
        
        # Auto-adjust column widths
        if 'Physical Visits' in writer.sheets:
            worksheet = writer.sheets['Physical Visits']
            for column in df:
                column_width = max(df[column].astype(str).map(len).max(), len(column)) + 2
                col_idx = df.columns.get_loc(column)
                worksheet.column_dimensions[chr(65 + col_idx)].width = column_width
    
    def calculate_visit_duration(self, visit):
        """Calculate visit duration"""
        if visit.entry_time and visit.exit_time:
            duration = visit.exit_time - visit.entry_time
            hours = duration.total_seconds() / 3600
            return f"{hours:.2f} hours"
        return 'Still in library'
    
    def export_virtual_usage_to_excel(self, writer, db, member_ids, filters):
        """Export virtual usage to Excel sheet"""
        # Get login sessions
        login_sessions = MemberLoginSession.objects.using(db).filter(
            member_id__in=member_ids
        ).select_related('member').order_by('-login_time')
        
        # Apply filters
        if filters.get('from_date'):
            login_sessions = login_sessions.filter(login_time__date__gte=filters['from_date'])
        if filters.get('to_date'):
            login_sessions = login_sessions.filter(login_time__date__lte=filters['to_date'])
        
        data = []
        for session in login_sessions:
            data.append({
                'Member Name': f"{session.member.first_name or ''} {session.member.last_name or ''}".strip(),
                'Membership Code': session.member.membership_code if session.member else '',
                'Activity Type': 'Login Session',
                'Screen Name': 'Login',
                'Screen Route': '/login',
                'Visited At': session.login_time.strftime('%Y-%m-%d %H:%M:%S'),
                'Logout Time': session.logout_time.strftime('%Y-%m-%d %H:%M:%S') if session.logout_time else '',
                'Duration': self.calculate_session_duration_excel(session),
                'IP Address': session.ip_address or '',
                'Device Type': session.device_type or ''
            })
        
        # Get screen activities
        activities = MemberScreenActivity.objects.using(db).filter(
            session__member_id__in=member_ids
        ).select_related('session', 'session__member').order_by('-visited_at')
        
        # Apply filters
        if filters.get('from_date'):
            activities = activities.filter(visited_at__date__gte=filters['from_date'])
        if filters.get('to_date'):
            activities = activities.filter(visited_at__date__lte=filters['to_date'])
        
        for activity in activities:
            data.append({
                'Member Name': f"{activity.session.member.first_name or ''} {activity.session.member.last_name or ''}".strip(),
                'Membership Code': activity.session.member.membership_code if activity.session.member else '',
                'Activity Type': 'Screen Visit',
                'Screen Name': activity.screen_name,
                'Screen Route': activity.screen_route,
                'Visited At': activity.visited_at.strftime('%Y-%m-%d %H:%M:%S'),
                'Logout Time': '',
                'Duration': '',
                'IP Address': activity.session.ip_address or '',
                'Device Type': activity.session.device_type or ''
            })
        
        df = pd.DataFrame(data)
        df.to_excel(writer, sheet_name='Virtual Usage', index=False)
        
        # Auto-adjust column widths
        if 'Virtual Usage' in writer.sheets:
            worksheet = writer.sheets['Virtual Usage']
            for column in df:
                column_width = max(df[column].astype(str).map(len).max(), len(column)) + 2
                col_idx = df.columns.get_loc(column)
                worksheet.column_dimensions[chr(65 + col_idx)].width = column_width
    
    def export_payments_to_excel(self, writer, db, member_ids, filters):
        """Export payment data to Excel sheet"""
        qs = PaymentDetails.objects.using(db).filter(
            membership_id__in=member_ids
        ).select_related('membership', 'status', 'circulation_transaction').order_by('-created_at')
        
        # Apply filters
        qs = self.apply_payment_filters_export(qs, filters)
        
        data = []
        for payment in qs:
            data.append({
                'Payment Mode': payment.payment_mode or '',
                'Payment Type': payment.payment_type or '',
                'Payment Method': payment.payment_method or '',
                'Deposit Amount': float(payment.deposit_amount) if payment.deposit_amount else 0.0,
                'Entry Fee Amount': float(payment.entry_fee_amount) if payment.entry_fee_amount else 0.0,
                'Monthly Subscription Amount': float(payment.monthly_subscription_amount) if payment.monthly_subscription_amount else 0.0,
                'Total Subscription Amount': float(payment.total_subscription_amount) if payment.total_subscription_amount else 0.0,
                'Subscription From': payment.subscription_from.strftime('%Y-%m-%d') if payment.subscription_from else '',
                'Subscription To': payment.subscription_to.strftime('%Y-%m-%d') if payment.subscription_to else '',
                'Fine Amount': float(payment.fine_amount) if payment.fine_amount else 0.0,
                'Book Fine Amount': float(payment.book_fine_amount) if payment.book_fine_amount else 0.0,
                'Adjusted Amount': float(payment.adjusted_amount) if payment.adjusted_amount else 0.0,
                'Status': payment.status.status_name if payment.status else '',
                'Transaction ID': payment.transaction_id or '',
                'Remarks': payment.remarks or '',
                'User ID': payment.user_id or '',
                'Membership Code': payment.membership_code or '',
                'Created At': payment.created_at.strftime('%Y-%m-%d %H:%M:%S') if payment.created_at else '',
                'Created By': payment.created_by or '',
                'Updated At': payment.updated_at.strftime('%Y-%m-%d %H:%M:%S') if payment.updated_at else '',
                'Updated By': payment.updated_by or '',
                'Membership ID': payment.membership_id,
                'Status ID': payment.status_id,
                'Payment Date': payment.payment_date.strftime('%Y-%m-%d') if payment.payment_date else '',
                'Circulation Transaction ID': payment.circulation_transaction_id,
                'Member Name': f"{payment.membership.first_name or ''} {payment.membership.last_name or ''}".strip() if payment.membership else '',
                'Member User ID': payment.membership.user_id if payment.membership else '',
            })
        
        df = pd.DataFrame(data)
        df.to_excel(writer, sheet_name='Payment Details', index=False)
        
        # Auto-adjust column widths
        if 'Payment Details' in writer.sheets:
            worksheet = writer.sheets['Payment Details']
            for column in df:
                column_width = max(df[column].astype(str).map(len).max(), len(column)) + 2
                col_idx = df.columns.get_loc(column)
                worksheet.column_dimensions[chr(65 + col_idx)].width = column_width
    
    def apply_payment_filters_export(self, qs, filters):
        """Apply filters for payment export"""
        if filters.get('from_date'):
            qs = qs.filter(payment_date__gte=filters['from_date'])
        if filters.get('to_date'):
            qs = qs.filter(payment_date__lte=filters['to_date'])
        
        if filters.get('payment_type'):
            qs = qs.filter(payment_type__icontains=filters['payment_type'])
        
        if filters.get('payment_mode'):
            qs = qs.filter(payment_mode=filters['payment_mode'])
        
        if filters.get('payment_method'):
            qs = qs.filter(payment_method=filters['payment_method'])
        
        if filters.get('min_amount'):
            qs = qs.filter(total_subscription_amount__gte=float(filters['min_amount']))
        
        if filters.get('max_amount'):
            qs = qs.filter(total_subscription_amount__lte=float(filters['max_amount']))
        
        return qs
    
    def calculate_session_duration_excel(self, session):
        """Calculate session duration for Excel export"""
        if session.login_time and session.logout_time:
            duration = session.logout_time - session.login_time
            minutes = duration.total_seconds() / 60
            return f"{minutes:.1f} minutes"
        return 'Still active'
# reports/views.py - ADD THESE ADDITIONAL VIEWS

class ListReportSessionsView(ReportBaseView):
    """List all saved report sessions for current user"""
    
    def get(self, request):
        sessions = ReportSession.objects.filter(
            created_by=request.user,
            report_type='member'
        ).order_by('-created_at')[:50]
        
        data = []
        for session in sessions:
            data.append({
                'id': session.id,
                'name': session.name,
                'report_type': session.report_type,
                'created_at': session.created_at.strftime('%Y-%m-%d %H:%M'),
                'filters_count': len(session.filters_json) if session.filters_json else 0
            })
        
        return JsonResponse({'sessions': data})

class DeleteReportSessionView(ReportBaseView):
    """Delete a saved report session"""
    
    def delete(self, request, session_id):
        try:
            session = ReportSession.objects.get(id=session_id, created_by=request.user)
            session.delete()
            
            return JsonResponse({
                'success': True,
                'message': 'Session deleted successfully'
            })
        except ReportSession.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Session not found'
            }, status=404)

class MemberDocumentsView(ReportBaseView):
    """Get documents for a specific member"""
    
    def get(self, request, member_id):
        db = self.get_library_db()
        
        documents = DocumentDetails.objects.using(db).filter(
            membership_id=member_id,
            isactive=1
        ).select_related('document')
        
        data = []
        for doc in documents:
            data.append({
                'id': doc.id,
                'document_name': doc.document.document_name if doc.document else 'Unknown',
                'file_name': doc.file_name,
                'file_path': doc.file_path,
                'uploaded_at': doc.created_at.strftime('%Y-%m-%d %H:%M') if doc.created_at else ''
            })
        
        return JsonResponse({'documents': data})

class ExportPDFView(ReportBaseView):
    """Export tab data to PDF"""
    
    def get(self, request, tab_name):
        # This would require reportlab or similar PDF generation library
        # Implementation depends on your PDF generation requirements
        pass

class ExportCompletePDFView(ReportBaseView):
    """Export complete report to PDF"""
    
    def get(self, request):
        # Implementation for complete PDF export
        pass