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
from django.db.models import Q, F, Value
from django.db.models.functions import Coalesce

from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import tempfile
import os
from django.core.files.storage import FileSystemStorage
from django.db import transaction
from django.db.models import Q

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
                'file_path': settings.MEDIA_URL + doc.file_path,
                'uploaded_at': doc.created_at.strftime('%Y-%m-%d %H:%M') if doc.created_at else ''
            })
        
        return JsonResponse({'documents': data})

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

        base_filter = Q()

        # Date filters
        if filters.get('from_date'):
            base_filter &= Q(from_date__gte=filters['from_date'])

        if filters.get('to_date'):
            base_filter &= Q(to_date__lte=filters['to_date'])

        # Action Performed
        if filters.get('action_performed'):
            base_filter &= Q(actionperformed__in=filters['action_performed'])

        # Membership Type
        if filters.get('membership_type'):
            mt_ids = [
                int(x) for x in filters['membership_type']
                if str(x).isdigit()
            ]
            base_filter &= Q(membership_id__in=mt_ids)

        # Gap Period Filter
        gap_filter = filters.get('gap_period')

        if gap_filter == 'only':
            # Only members who have gap
            base_filter &= Q(gap_months__gt=0)

        elif gap_filter == 'exclude':
            # Don’t include members with gap (i.e., no gap)
            base_filter &= Q(gap_months=0)

        # Apply filters at DB level
        # current_qs = (
        #     MembershipDetails.objects
        #     .using(db)
        #     .filter(id__in=member_ids)
        #     .filter(base_filter)
        # )

        history_qs = (
            MembershipDetailsHistory.objects
            .using(db)
            .filter(membership_id__in=member_ids)
            .filter(base_filter)
        )

        data = []

        def fmt_date(d):
            return d.strftime('%Y-%m-%d') if d else ''

        def fmt_dt(d):
            return d.strftime('%Y-%m-%d %H:%M') if d else ''

        # History data
        for history in history_qs:
            data.append({
                'first_name': history.first_name,
                'middle_name': history.middle_name,
                'last_name': history.last_name,
                'first_name_mar': history.first_name_mar,
                'middle_name_mar': history.middle_name_mar,
                'last_name_mar': history.last_name_mar,
                'actionperformed': history.actionperformed,
                'from_date': fmt_date(history.from_date),
                'to_date': fmt_date(history.to_date),
                'deposit': float(history.deposit or 0),
                'entry_fees': float(history.entry_fees or 0),
                'subscription': float(history.subscription or 0),
                'fine_calculated_at': fmt_dt(history.fine_calculated_at),
                'gap_fine_subscription': float(history.gap_fine or 0),
                'gap_fine_delay': float(history.late_fee or 0),
                'gap_months': history.gap_months or 0,
                'late_fee': float(history.late_fee or 0),
                'changed_at': fmt_dt(history.changed_at),
                'changed_by': history.changed_by,
                'membership_type_id': history.membership_id,
            })

        return {'data': data}

    def get_loan_data(self, db, member_ids, filters):
        qs = CirculationTransaction.objects.using(db).filter(
            member_id__in=member_ids,
            transaction_type__in=['Offline', 'Online'],
            return_date__isnull=True,   # only not-returned books
            due_date__isnull=False
        ).select_related('catalog', 'accession', 'member')

        from datetime import date, timedelta
        from django.db.models import Q
        
        today = date.today()

        
        # Apply filters
        if filters.get('from_date'):
            qs = qs.filter(issue_date__gte=filters['from_date'])
        if filters.get('to_date'):
            qs = qs.filter(issue_date__lte=filters['to_date'])

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

        if filters.get('fine_status') == 'paid':
            qs = qs.filter(fine_status__iexact='Paid')
        elif filters.get('fine_status') == 'not_paid':
            qs = qs.filter(
            Q(fine_status__iexact='Unpaid') |
            Q(fine_amount__gt=0, fine_paid_date__isnull=True)
        )
        
        membership_type = filters.get('membership_type')
        if membership_type:
            if not isinstance(membership_type, (list, tuple)):
                membership_type = [membership_type]

            qs = qs.filter(member__member_type_id__in=membership_type)

        from django.db.models import IntegerField, Func
        from django.db.models.functions import Now

        qs = qs.annotate(
            overdue_days=Func(
                Now(),
                F('due_date'),
                function='DATEDIFF',
                output_field=IntegerField()
            )
        )

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
                # 'days_overdue_count': transaction.days_overdue_count or 0,
                'days_overdue_count': transaction.overdue_days or 0,
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
        
        # if filters.get('from_date'):
        #     qs = qs.filter(issue_date__gte=filters['from_date'])
        # if filters.get('to_date'):
        #     qs = qs.filter(issue_date__lte=filters['to_date'])

        if filters.get('from_date'):
            start_date = parse_month_start(filters['from_date'])
            qs = qs.filter(issue_date__gte=start_date)
        if filters.get('to_date'):
            end_date = parse_month_end(filters['to_date'])
            qs = qs.filter(issue_date__lte=end_date)
        
        from datetime import timedelta
        from django.db.models import F

        late_filter = filters.get('late_returns')

        if late_filter:
            # Only returned books
            qs = qs.filter(
                return_date__isnull=False,
                due_date__isnull=False
            )

            if late_filter == '0_3':
                qs = qs.filter(
                    return_date__gt=F('due_date'),
                    return_date__lte=F('due_date') + timedelta(days=3)
                )

            elif late_filter == '4_7':
                qs = qs.filter(
                    return_date__gt=F('due_date') + timedelta(days=3),
                    return_date__lte=F('due_date') + timedelta(days=7)
                )

            elif late_filter == '1_month':
                qs = qs.filter(
                    return_date__gt=F('due_date') + timedelta(days=30)
                )

            elif late_filter == '3_month':
                qs = qs.filter(
                    return_date__gt=F('due_date') + timedelta(days=90)
                )

            elif late_filter == '6_month':
                qs = qs.filter(
                    return_date__gt=F('due_date') + timedelta(days=180)
                )


        if filters.get('fine_status') == 'paid':
            qs = qs.filter(
                Q(fine_amount__gt=0, fine_status='Paid') |
                Q(fine_amount__lte=0)
            )

        elif filters.get('fine_status') == 'not_paid':
            qs = qs.filter(
                Q(fine_amount__gt=0, fine_status__in=['Unpaid', 'Pending']) |
                Q(fine_amount__lte=0)
            )

        elif filters.get('fine_status') == 'adjusted':
            qs = qs.filter(
                Q(fine_amount__gt=0, fine_status='Adjusted') |
                Q(fine_amount__lte=0)
            )

        membership_type = filters.get('membership_type')
        if membership_type:
            if not isinstance(membership_type, (list, tuple)):
                membership_type = [membership_type]
        
            qs = qs.filter(member__member_type_id__in=membership_type)

        from django.db.models import IntegerField, Func, F
        from django.db.models.functions import Now, Cast, Coalesce
        from django.db.models import DateField


        qs = qs.annotate(
            late_days=Func(
                Coalesce(
                    F('return_date'),
                    Cast(Now(), DateField())   # today if return_date is NULL
                ),
                F('due_date'),
                function='DATEDIFF',
                output_field=IntegerField()
            )
        )



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
                # 'days_overdue_count': transaction.days_overdue_count or 0,
                'days_overdue_count': transaction.late_days or 0,
                'fine_amount': float(transaction.fine_amount) if transaction.fine_amount else 0,
                'book_fine_amount': float(transaction.book_fine_amount) if transaction.book_fine_amount else 0,
                'total_fine': float(transaction.total_fine) if transaction.total_fine else 0,
                'adjusted_fine': float(transaction.adjusted_fine) if transaction.adjusted_fine else 0,
                'fine_status': transaction.fine_status if transaction.fine_amount and transaction.fine_amount > 0 else None,
                'fine_paid_date': transaction.fine_paid_date.strftime('%Y-%m-%d') if transaction.fine_paid_date else '',
                'remarks': transaction.remarks,
                'updated_at': transaction.updated_at.strftime('%Y-%m-%d %H:%M') if transaction.updated_at else '',
            })
        
        return {'data': data}
    
    def get_physical_visit_data(self, db, member_ids, filters):

        activity = (filters.get('activity_type') or '').lower()
        membership_type = filters.get('membership_type')
        from_date = filters.get('from_date')
        to_date = filters.get('to_date')

        # -------------------------
        # Filter members first
        # -------------------------
        member_qs = MembershipDetails.objects.using(db).filter(id__in=member_ids)

        if membership_type:
            if not isinstance(membership_type, (list, tuple)):
                membership_type = [membership_type]

            member_qs = member_qs.filter(member_type_id__in=membership_type)


        members = member_qs.values(
            'id', 'membership_code', 'first_name', 'last_name'
        )

        member_ids = [m['id'] for m in members]
        member_codes = [m['membership_code'] for m in members if m['membership_code']]

        member_map = {
            m['membership_code']: f"{m['first_name'] or ''} {m['last_name'] or ''}".strip()
            for m in members
        }

        data = []

        # =========================
        # 1️⃣ Reading (MemberEntryExit)
        # =========================
        if activity in ['', 'reading']:

            visit_qs = MemberEntryExit.objects.using(db).filter(
                membership_code__in=member_codes
            )

            if from_date:
                visit_qs = visit_qs.filter(entry_time__date__gte=from_date)
            if to_date:
                visit_qs = visit_qs.filter(entry_time__date__lte=to_date)

            for visit in visit_qs:
                data.append({
                    'activity': 'Reading',
                    'member_name': member_map.get(visit.membership_code, ''),
                    'membership_code': visit.membership_code,
                    'entry_time': visit.entry_time.strftime('%Y-%m-%d %H:%M:%S') if visit.entry_time else '',
                    'exit_time': visit.exit_time.strftime('%Y-%m-%d %H:%M:%S') if visit.exit_time else '',
                    'remark': visit.remark or '',
                    'created_at': visit.created_at.strftime('%Y-%m-%d %H:%M:%S')
                })

        # =========================
        # 2️⃣ Issue / Return (Circulation)
        # =========================
        if activity in ['', 'issue', 'return']:

            trans_qs = CirculationTransaction.objects.using(db).filter(
                member_id__in=member_ids
            )

            if activity == 'issue':
                trans_qs = trans_qs.filter(transaction_type='Issue')
                if from_date:
                    trans_qs = trans_qs.filter(issue_date__gte=from_date)
                if to_date:
                    trans_qs = trans_qs.filter(issue_date__lte=to_date)

            elif activity == 'return':
                trans_qs = trans_qs.filter(transaction_type='Return')
                if from_date:
                    trans_qs = trans_qs.filter(return_date__gte=from_date)
                if to_date:
                    trans_qs = trans_qs.filter(return_date__lte=to_date)

            else:
                # All circulation
                if from_date:
                    trans_qs = trans_qs.filter(issue_date__gte=from_date)
                if to_date:
                    trans_qs = trans_qs.filter(issue_date__lte=to_date)

            for tr in trans_qs:
                data.append({
                    'activity': tr.transaction_type,
                    'member_name': f"{tr.member.first_name or ''} {tr.member.last_name or ''}".strip(),
                    'membership_code': tr.membership_code,
                    'entry_time': tr.issue_date.strftime('%Y-%m-%d') if tr.issue_date else '',
                    'exit_time': tr.return_date.strftime('%Y-%m-%d') if tr.return_date else '',
                    'remark': tr.remarks or '',
                    'created_at': tr.created_at.strftime('%Y-%m-%d %H:%M:%S')
                })

        return {'data': data}

    def get_virtual_usage_data(self, db, member_ids, filters):
        data = []

        # ------------------------------------
        # MEMBER FILTER (membership type)
        # ------------------------------------
        member_qs = MembershipDetails.objects.using(db).filter(id__in=member_ids)

        if filters.get('membership_type'):
            member_qs = member_qs.filter(member_type_id__in=filters['membership_type'])

        member_ids = member_qs.values_list('id', flat=True)

        # ------------------------------------
        # LOGIN SESSIONS
        # ------------------------------------
        if filters.get('activity_type') in (None, '', 'login'):
            login_qs = MemberLoginSession.objects.using(db).filter(
                member_id__in=member_ids
            ).select_related('member')

            if filters.get('from_date'):
                login_qs = login_qs.filter(login_time__date__gte=filters['from_date'])
            if filters.get('to_date'):
                login_qs = login_qs.filter(login_time__date__lte=filters['to_date'])
            if filters.get('device_type'):
                login_qs = login_qs.filter(device_type__icontains=filters['device_type'])

            for session in login_qs:
                data.append({
                    'member_name': f"{session.member.first_name or ''} {session.member.last_name or ''}".strip(),
                    'membership_code': session.member.membership_code,
                    'activity': 'Login',
                    'screen_name': 'Login Session',
                    'screen_route': '/login',
                    'visited_at': session.login_time.strftime('%Y-%m-%d %H:%M:%S'),
                    'ip_address': session.ip_address or '',
                    'device_type': session.device_type or '',
                    'duration': self.calculate_session_duration(session),
                })

        # ------------------------------------
        # SCREEN ACTIVITIES
        # ------------------------------------
        if filters.get('activity_type') in (None, '', 'screen'):
            activity_qs = MemberScreenActivity.objects.using(db).filter(
                session__member_id__in=member_ids
            ).select_related('session', 'session__member')

            if filters.get('from_date'):
                activity_qs = activity_qs.filter(visited_at__date__gte=filters['from_date'])
            if filters.get('to_date'):
                activity_qs = activity_qs.filter(visited_at__date__lte=filters['to_date'])
            if filters.get('screen_name'):
                activity_qs = activity_qs.filter(screen_name__icontains=filters['screen_name'])
            if filters.get('device_type'):
                activity_qs = activity_qs.filter(
                    session__device_type__icontains=filters['device_type']
                )

            for act in activity_qs:
                member = act.session.member
                data.append({
                    'member_name': f"{member.first_name or ''} {member.last_name or ''}".strip(),
                    'membership_code': member.membership_code,
                    'activity': 'Screen',
                    'screen_name': act.screen_name,
                    'screen_route': act.screen_route,
                    'visited_at': act.visited_at.strftime('%Y-%m-%d %H:%M:%S'),
                    'ip_address': act.session.ip_address or '',
                    'device_type': act.session.device_type or '',
                    'duration': 'N/A',
                })

        return {
            'total': len(data),
            'data': sorted(data, key=lambda x: x['visited_at'], reverse=True)
        }

    def calculate_session_duration(self, session):
        if session.logout_time:
            delta = session.logout_time - session.login_time
            return f"{delta.total_seconds() / 60:.1f} mins"
        return "Active"

    def get_payment_data(self, db, member_ids, filters):
        qs = PaymentDetails.objects.using(db).filter(
            membership_id__in=member_ids
        ).select_related(
            'membership',
            'membership__member_type',
            'status'
        ).order_by('-payment_date')

        # Date filters
        if filters.get('from_date'):
            qs = qs.filter(payment_date__gte=filters['from_date'])

        if filters.get('to_date'):
            qs = qs.filter(payment_date__lte=filters['to_date'])

        # Membership type
        if filters.get('membership_types'):
            qs = qs.filter(
                membership__member_type_id__in=filters['membership_types']
            )

        # Payment attributes
        payment_type = filters.get('payment_type')

        if payment_type:
            if payment_type == 'Fine':
                qs = qs.filter(payment_type__in=['Fine', 'Membership Renewed'])
            else:
                qs = qs.filter(payment_type=payment_type)


        if filters.get('payment_mode'):
            qs = qs.filter(payment_mode=filters['payment_mode'])

        if filters.get('payment_method'):
            qs = qs.filter(payment_method=filters['payment_method'])

        if filters.get('min_amount'):
            qs = qs.filter(fine_amount__gte=float(filters['min_amount']))

        if filters.get('max_amount'):
            qs = qs.filter(fine_amount__lte=float(filters['max_amount']))

        for payment in qs:
            member = payment.membership

            # ✅ Full member name
            member_name = " ".join(filter(None, [
                member.first_name if member else '',
                member.middle_name if member else '',
                member.last_name if member else '',
            ]))

        data = []
        for payment in qs:
            data.append({
                'membership_code': payment.membership_code or '',
                'member_name': member_name,
                'user_id': payment.user_id or '',
                'payment_type': payment.payment_type or '',
                'payment_date': payment.payment_date.strftime('%Y-%m-%d') if payment.payment_date else '',
                'subscription_from': payment.subscription_from.strftime('%Y-%m-%d') if payment.subscription_from else '',
                'subscription_to': payment.subscription_to.strftime('%Y-%m-%d') if payment.subscription_to else '',
                'deposit_amount': float(payment.deposit_amount) if payment.deposit_amount else 0.0,
                'entry_fee_amount': float(payment.entry_fee_amount) if payment.entry_fee_amount else 0.0,
                'monthly_subscription_amount': float(payment.monthly_subscription_amount) if payment.monthly_subscription_amount else 0.0,
                'total_subscription_amount': float(payment.total_subscription_amount) if payment.total_subscription_amount else 0.0,
                'book_fine_amount': float(payment.book_fine_amount) if payment.book_fine_amount else 0.0,
                'fine_amount': float(payment.fine_amount) if payment.fine_amount else 0.0,
                'adjusted_amount': float(payment.adjusted_amount) if payment.adjusted_amount else 0.0,
                'transaction_id': payment.transaction_id or '',
                'remarks': payment.remarks or '',
                'payment_mode': payment.payment_mode or '',
                'payment_method': payment.payment_method or '',
                'created_at': payment.created_at.strftime('%Y-%m-%d %H:%M:%S') if payment.created_at else '',
                'created_by': payment.created_by or '',
                'updated_at': payment.updated_at.strftime('%Y-%m-%d %H:%M:%S') if payment.updated_at else '',
                'updated_by': payment.updated_by or '',
                'membership_id': payment.membership_id,
                'status_id': payment.status_id,
                'circulation_transaction_id': payment.circulation_transaction_id,
            })
        
        return {'data': data}

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

def normalize_export_filters(filters):
    FILTER_MODEL_MAP = {
        'membership_type': {
            'model': MembershipMaster,
            'pk': 'id',
            'label': 'membership_type_en',
        },
        'member_type': {
            'model': parameter_master_L01,
            'pk': 'parameter_id',
            'label': 'parameter_value',
        },
        'status': {
            'model': StatusMaster,
            'pk': 'id',
            'label': 'status_name',
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

            ids = value if isinstance(value, (list, tuple)) else [value]

            lookup = {f"{pk_field}__in": ids}

            names = list(
                model.objects.filter(**lookup)
                .values_list(label_field, flat=True)
            )

            normalized_filters[key] = ", ".join(map(str, names))

        else:
            # Leave everything else untouched
            normalized_filters[key] = value

    return normalized_filters

def export_member_details_to_excel(writer, db, member_ids, filters):

    # --------------------------------------------------
    # Query & Filters
    # --------------------------------------------------
    qs = MembershipDetails.objects.using(db).filter(id__in=member_ids)
    qs = apply_member_details_filters(qs, filters)

    # --------------------------------------------------
    # Prepare Data
    # --------------------------------------------------
    rows = []
    for m in qs.select_related('membership', 'status', 'member_type'):
        rows.append({
            'First Name': m.first_name or '',
            'Middle Name': m.middle_name or '',
            'Last Name': m.last_name or '',
            'First Name (Marathi)': m.first_name_mar or '',
            'Middle Name (Marathi)': m.middle_name_mar or '',
            'Last Name (Marathi)': m.last_name_mar or '',
            'Membership Type': m.membership.membership_type if m.membership else '',
            'Member Type': m.member_type.parameter_value if m.member_type else '',
            'Membership Code': m.membership_code or '',
            'Membership Date': m.created_at.strftime('%d-%m-%Y') if m.created_at else '',
            'Renewal From': m.from_date.strftime('%d-%m-%Y') if m.from_date else '',
            'Renewal To': m.to_date.strftime('%d-%m-%Y') if m.to_date else '',
            'Ward': m.ward or '',
            'Pincode': m.pincode or '',
            'Mobile No': m.mobile_no or '',
            'Email': m.email or '',
            'Occupation': m.occupation or '',
            'Institute Name': m.institute_name or '',
            'DOB': m.dob.strftime('%d-%m-%Y') if m.dob else '',
            'Aadhar No': m.aadhar_no or '',
            'Resident of NMMC': 'Yes' if m.is_resident_of_nmmc else 'No',
            'Status': 'Active' if m.isactive else 'Inactive',
            'Created At': m.created_at.strftime('%d-%m-%Y %H:%M') if m.created_at else '',
            'Created By': m.created_by or '',
            'Approved By': m.reviewed or '',
            'Approved Date': m.reviewed_at.strftime('%d-%m-%Y') if m.reviewed_at else '',
        })

    df = pd.DataFrame(rows)

    sheet_name = 'Member Details'
    start_row = 6  # leave space for title + filters

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

    # --------------------------------------------------
    # Report Title
    # --------------------------------------------------
    total_columns = len(df.columns)
    worksheet.merge_range(0, 0, 0, total_columns - 1, 'Member Details Report', title_format)
    worksheet.merge_range(
        1, 0, 1, total_columns - 1,
        f'Generated on: {timezone.now().strftime("%d-%m-%Y %H:%M")}',
        subtitle_format
    )

    # Convert filter IDs → names (ONLY for display)
    filters = normalize_export_filters(filters)

    # --------------------------------------------------
    # Applied Filters Section
    # --------------------------------------------------
    filter_row = 3
    worksheet.write(filter_row, 0, 'Applied Filters:', filter_label_format)

    col = 1
    for key, value in filters.items():
        if value:
            worksheet.write(filter_row, col, f'{key.replace("_", " ").title()}: {value}')
            col += 1

    # --------------------------------------------------
    # Style Header Row
    # --------------------------------------------------
    for col_idx, col_name in enumerate(df.columns):
        worksheet.write(start_row, col_idx, col_name, header_format)

    # --------------------------------------------------
    # Apply Row Styling
    # --------------------------------------------------
    for row_idx in range(len(df)):
        excel_row = start_row + 1 + row_idx
        row_format = alt_row_format if row_idx % 2 else cell_format

        for col_idx in range(len(df.columns)):
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
        worksheet.set_column(col_idx, col_idx, max_len + 3)

    # --------------------------------------------------
    # Freeze Header
    # --------------------------------------------------
    worksheet.freeze_panes(start_row + 1, 0)

    # --------------------------------------------------
    # No Data Message
    # --------------------------------------------------
    if df.empty:
        worksheet.merge_range(
            start_row + 1, 0,
            start_row + 2, total_columns - 1,
            'No records found for selected filters',
            workbook.add_format({'align': 'center', 'italic': True})
        )

def apply_member_details_filters(qs, filters):
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
        
        return qs
    
def export_membership_details_to_excel(writer, db, member_ids, filters):

    # --------------------------------------------------
    # Query Data (History Only – authoritative source)
    # --------------------------------------------------
    history_qs = MembershipDetailsHistory.objects.using(db).filter(
        membership_id__in=member_ids
    ).select_related('membershipmaster', 'member_type').distinct()

    history_qs = apply_membership_details_filters(history_qs, filters)

    # --------------------------------------------------
    # Prepare Data
    # --------------------------------------------------
    rows = []
    for h in history_qs:
        rows.append({
            'Record Type': 'Historical',
            'First Name': h.first_name or '',
            'Middle Name': h.middle_name or '',
            'Last Name': h.last_name or '',
            'First Name (Marathi)': h.first_name_mar or '',
            'Middle Name (Marathi)': h.middle_name_mar or '',
            'Last Name (Marathi)': h.last_name_mar or '',
            'Action Performed': h.actionperformed or '',
            'Membership Type': h.membershipmaster.membership_type_en if h.membershipmaster else '',
            'Member Type': h.member_type.parameter_value if h.member_type else '',
            'Membership Code': h.membership_code or '',
            'From Date': h.from_date.strftime('%d-%m-%Y') if h.from_date else '',
            'To Date': h.to_date.strftime('%d-%m-%Y') if h.to_date else '',
            'Membership Duration (Months)': h.membership_duration or 0,
            'Deposit Amount': float(h.deposit) if h.deposit else 0.0,
            'Entry Fees': float(h.entry_fees) if h.entry_fees else 0.0,
            'Subscription Fees': float(h.subscription) if h.subscription else 0.0,
            'Gap Months': h.gap_months or 0,
            'Gap Fine (Subscription)': float(h.gap_fine) if h.gap_fine else 0.0,
            'Late Fee': float(h.late_fee) if h.late_fee else 0.0,
            'Total Membership Fine': float(h.total_fine_membership) if h.total_fine_membership else 0.0,
            'Gap Period From': h.gap_period_from or '',
            'Gap Period To': h.gap_period_to or '',
            'Fine Calculated At': h.fine_calculated_at.strftime('%d-%m-%Y %H:%M') if h.fine_calculated_at else '',
            'Changed At': h.changed_at.strftime('%d-%m-%Y %H:%M') if h.changed_at else '',
            'Changed By': h.changed_by or '',
            'User ID': h.user_id or '',
            'Status': 'Active' if h.isactive else 'Inactive',
        })

    df = pd.DataFrame(rows)

    # --------------------------------------------------
    # Sheet & Positioning
    # --------------------------------------------------
    sheet_name = 'Membership Details'
    start_row = 6

    df.to_excel(
        writer,
        sheet_name=sheet_name,
        index=False,
        startrow=start_row
    )

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
        'border': 1,
        'align': 'center',
        'valign': 'middle',
        'bg_color': '#D9E1F2',
        'text_wrap': True
    })

    cell_format = workbook.add_format({
        'border': 1,
        'valign': 'top'
    })

    alt_row_format = workbook.add_format({
        'border': 1,
        'bg_color': '#F9F9F9'
    })

    filter_label_format = workbook.add_format({'bold': True})

    # --------------------------------------------------
    # Report Header
    # --------------------------------------------------
    total_cols = len(df.columns)

    worksheet.merge_range(
        0, 0, 0, total_cols - 1,
        'Membership Details History Report',
        title_format
    )

    worksheet.merge_range(
        1, 0, 1, total_cols - 1,
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
                3, col,
                f'{key.replace("_", " ").title()}: {value}'
            )
            col += 1

    # --------------------------------------------------
    # Style Header Row
    # --------------------------------------------------
    for col_idx, col_name in enumerate(df.columns):
        worksheet.write(start_row, col_idx, col_name, header_format)

    # --------------------------------------------------
    # Style Data Rows
    # --------------------------------------------------
    for row_idx in range(len(df)):
        excel_row = start_row + 1 + row_idx
        fmt = alt_row_format if row_idx % 2 else cell_format

        for col_idx in range(len(df.columns)):
            worksheet.write(
                excel_row,
                col_idx,
                df.iloc[row_idx, col_idx],
                fmt
            )

    # --------------------------------------------------
    # Auto Column Width
    # --------------------------------------------------
    for col_idx, column in enumerate(df.columns):
        max_len = max(
            df[column].astype(str).map(len).max() if not df.empty else 10,
            len(column)
        )
        worksheet.set_column(col_idx, col_idx, max_len + 3)

    # --------------------------------------------------
    # Freeze Header Row
    # --------------------------------------------------
    worksheet.freeze_panes(start_row + 1, 0)

    # --------------------------------------------------
    # No Data Message
    # --------------------------------------------------
    if df.empty:
        worksheet.merge_range(
            start_row + 1, 0,
            start_row + 2, total_cols - 1,
            'No membership history found for selected filters',
            workbook.add_format({'align': 'center', 'italic': True})
        )

def apply_membership_details_filters(qs, filters):

    if filters.get('from_date'):
        qs = qs.filter(from_date__gte=filters['from_date'])

    if filters.get('to_date'):
        qs = qs.filter(to_date__lte=filters['to_date'])

    if filters.get('action_performed'):
        qs = qs.filter(actionperformed__in=filters['action_performed'])

    if filters.get('membership_type'):
        mt_ids = [
            int(x) for x in filters['membership_type']
            if str(x).isdigit()
        ]
        qs = qs.filter(membership_id__in=mt_ids)

    gap_filter = filters.get('gap_period')

    if gap_filter == 'only':
        # Only members who have gap
        qs = qs.filter(gap_months__gt=0)

    elif gap_filter == 'exclude':
        # Exclude members who have gap
        qs = qs.filter(gap_months=0)

    return qs

def export_loan_to_excel(writer, db, member_ids, filters):

    # --------------------------------------------------
    # Base Query (Outstanding Loans)
    # --------------------------------------------------
    qs = CirculationTransaction.objects.using(db).filter(
        member_id__in=member_ids,
        transaction_type__in=['Offline', 'Online'],
        return_date__isnull=True,
        due_date__isnull=False
    ).select_related(
        'catalog',
        'accession',
        'member',
        'return_condition'
    )

    qs = apply_loan_filters(qs, filters)

    # --------------------------------------------------
    # Prepare Data
    # --------------------------------------------------
    rows = []
    for t in qs:
        rows.append({
            'Membership Code': t.member.membership_code if t.member else '',
            'Member Name': (
                f"{t.member.first_name or ''} {t.member.last_name or ''}".strip()
                if t.member else ''
            ),
            'Barcode': t.barcode or '',
            'Accession No': t.accession.accession_no if t.accession else '',
            'Catalog Ref No': t.catalog.cat_ref_num if t.catalog else '',
            'Book Title': t.catalog.title if t.catalog else '',
            'Author': t.catalog.author if t.catalog else '',
            'Issue Date': t.issue_date.strftime('%d-%m-%Y') if t.issue_date else '',
            'Due Date': t.due_date.strftime('%d-%m-%Y') if t.due_date else '',
            'Days Overdue': t.days_overdue_count or 0,
            'Fine Amount': float(t.fine_amount) if t.fine_amount else 0.0,
            'Book Fine': float(t.book_fine_amount) if t.book_fine_amount else 0.0,
            'Total Fine': float(t.total_fine) if t.total_fine else 0.0,
            'Adjusted Fine': float(t.adjusted_fine) if t.adjusted_fine else 0.0,
            'Fine Status': t.fine_status or '',
            'Fine Paid Date': t.fine_paid_date.strftime('%d-%m-%Y') if t.fine_paid_date else '',
            'Transaction Type': t.transaction_type or '',
            'Transaction Status': t.transaction_status or '',
            'Issued By': t.issued_by or '',
            'Received By': t.received_by or '',
            'Return Condition': t.return_condition.status_name if t.return_condition else '',
            'Remarks': t.remarks or '',
            'Created At': t.created_at.strftime('%d-%m-%Y %H:%M') if t.created_at else '',
            'Created By': t.created_by or '',
            'Updated At': t.updated_at.strftime('%d-%m-%Y %H:%M') if t.updated_at else '',
            'Updated By': t.updated_by or '',
        })

    df = pd.DataFrame(rows)

    # --------------------------------------------------
    # Sheet & Position
    # --------------------------------------------------
    sheet_name = 'Loan Transactions'
    start_row = 6

    df.to_excel(
        writer,
        sheet_name=sheet_name,
        index=False,
        startrow=start_row
    )

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
        'border': 1,
        'align': 'center',
        'valign': 'middle',
        'text_wrap': True,
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

    filter_label_format = workbook.add_format({'bold': True})

    # --------------------------------------------------
    # Report Header
    # --------------------------------------------------
    total_cols = len(df.columns)

    worksheet.merge_range(
        0, 0, 0, total_cols - 1,
        'Outstanding Loan Transactions Report',
        title_format
    )

    worksheet.merge_range(
        1, 0, 1, total_cols - 1,
        f'Generated on: {timezone.now().strftime("%d-%m-%Y %H:%M")}',
        subtitle_format
    )

    # Convert filter IDs → names (ONLY for display)
    filters = normalize_export_filters(filters)
    # --------------------------------------------------
    # Applied Filters Section
    # --------------------------------------------------
    worksheet.write(3, 0, 'Applied Filters:', filter_label_format)

    col = 1
    for key, value in filters.items():
        if value:
            worksheet.write(
                3, col,
                f'{key.replace("_", " ").title()}: {value}'
            )
            col += 1

    # --------------------------------------------------
    # Header Styling
    # --------------------------------------------------
    for col_idx, col_name in enumerate(df.columns):
        worksheet.write(start_row, col_idx, col_name, header_format)

    # --------------------------------------------------
    # Row Styling
    # --------------------------------------------------
    for row_idx in range(len(df)):
        excel_row = start_row + 1 + row_idx
        fmt = alt_row_format if row_idx % 2 else cell_format

        for col_idx in range(len(df.columns)):
            worksheet.write(
                excel_row,
                col_idx,
                df.iloc[row_idx, col_idx],
                fmt
            )

    # --------------------------------------------------
    # Auto Column Width
    # --------------------------------------------------
    for col_idx, column in enumerate(df.columns):
        max_len = max(
            df[column].astype(str).map(len).max() if not df.empty else 10,
            len(column)
        )
        worksheet.set_column(col_idx, col_idx, max_len + 3)

    # --------------------------------------------------
    # Freeze Header Row
    # --------------------------------------------------
    worksheet.freeze_panes(start_row + 1, 0)

    # --------------------------------------------------
    # No Data Message
    # --------------------------------------------------
    if df.empty:
        worksheet.merge_range(
            start_row + 1, 0,
            start_row + 2, total_cols - 1,
            'No outstanding loan records found for selected filters',
            workbook.add_format({'align': 'center', 'italic': True})
        )

def apply_loan_filters(qs, filters):
    from datetime import date, timedelta
    from django.db.models import Q
        
    today = date.today()
    # Apply filters
    if filters.get('from_date'):
        qs = qs.filter(issue_date__gte=filters['from_date'])
    if filters.get('to_date'):
        qs = qs.filter(issue_date__lte=filters['to_date'])
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
    if filters.get('fine_status') == 'paid':
        qs = qs.filter(fine_status__iexact='Paid')
    elif filters.get('fine_status') == 'not_paid':
        qs = qs.filter(
        Q(fine_status__iexact='Unpaid') |
        Q(fine_amount__gt=0, fine_paid_date__isnull=True)
    )
    
    membership_type = filters.get('membership_type')
    if membership_type:
        if not isinstance(membership_type, (list, tuple)):
            membership_type = [membership_type]
        qs = qs.filter(member__member_type_id__in=membership_type)

    return qs

def export_transactions_to_excel(writer, db, member_ids, filters):

    # --------------------------------------------------
    # Base Query
    # --------------------------------------------------
    qs = CirculationTransaction.objects.using(db).filter(
        member_id__in=member_ids
    ).select_related(
        'catalog',
        'accession',
        'member',
        'return_condition'
    ).order_by('-created_at')

    qs = apply_transaction_filters_export(qs, filters)

    # --------------------------------------------------
    # Prepare Data
    # --------------------------------------------------
    rows = []
    for t in qs:
        rows.append({
            'Member Name': (
                f"{t.member.first_name or ''} {t.member.last_name or ''}".strip()
                if t.member else ''
            ),
            'Membership Code': t.member.membership_code if t.member else '',
            'Barcode': t.barcode or '',
            'Accession No': t.accession.accession_no if t.accession else '',
            'Catalog Ref No': t.catalog.cat_ref_num if t.catalog else '',
            'Book Title': t.catalog.title if t.catalog else '',
            'Transaction Type': t.transaction_type or '',
            'Transaction Status': t.transaction_status or '',
            'Issue Date': t.issue_date.strftime('%d-%m-%Y') if t.issue_date else '',
            'Due Date': t.due_date.strftime('%d-%m-%Y') if t.due_date else '',
            'Return Date': t.return_date.strftime('%d-%m-%Y') if t.return_date else '',
            'Issued By': t.issued_by or '',
            'Received By': t.received_by or '',
            'Days Overdue': t.days_overdue_count or 0,
            'Fine Amount': float(t.fine_amount) if t.fine_amount else 0.0,
            'Book Fine': float(t.book_fine_amount) if t.book_fine_amount else 0.0,
            'Total Fine': float(t.total_fine) if t.total_fine else 0.0,
            'Adjusted Fine': float(t.adjusted_fine) if t.adjusted_fine else 0.0,
            'Fine Status': t.fine_status or '',
            'Fine Paid Date': (
                t.fine_paid_date.strftime('%d-%m-%Y')
                if t.fine_paid_date else ''
            ),
            'Return Condition': (
                t.return_condition.status_name
                if t.return_condition else ''
            ),
            'Remarks': t.remarks or '',
            'Created At': (
                t.created_at.strftime('%d-%m-%Y %H:%M')
                if t.created_at else ''
            ),
            'Updated At': (
                t.updated_at.strftime('%d-%m-%Y %H:%M')
                if t.updated_at else ''
            ),
            'Updated By': t.updated_by or '',
        })

    df = pd.DataFrame(rows)

    # --------------------------------------------------
    # Sheet & Positioning
    # --------------------------------------------------
    sheet_name = 'All Transactions'
    start_row = 6

    df.to_excel(
        writer,
        sheet_name=sheet_name,
        index=False,
        startrow=start_row
    )

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
        'border': 1,
        'align': 'center',
        'valign': 'middle',
        'text_wrap': True,
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

    filter_label_format = workbook.add_format({'bold': True})

    # --------------------------------------------------
    # Report Header
    # --------------------------------------------------
    total_cols = len(df.columns)

    worksheet.merge_range(
        0, 0, 0, total_cols - 1,
        'All Circulation Transactions Report',
        title_format
    )

    worksheet.merge_range(
        1, 0, 1, total_cols - 1,
        f'Generated on: {timezone.now().strftime("%d-%m-%Y %H:%M")}',
        subtitle_format
    )

    # Convert filter IDs → names (ONLY for display)
    filters = normalize_export_filters(filters)
    # --------------------------------------------------
    # Applied Filters Section
    # --------------------------------------------------
    worksheet.write(3, 0, 'Applied Filters:', filter_label_format)

    col = 1
    for key, value in filters.items():
        if value:
            worksheet.write(
                3, col,
                f'{key.replace("_", " ").title()}: {value}'
            )
            col += 1

    # --------------------------------------------------
    # Header Styling
    # --------------------------------------------------
    for col_idx, col_name in enumerate(df.columns):
        worksheet.write(start_row, col_idx, col_name, header_format)

    # --------------------------------------------------
    # Data Row Styling
    # --------------------------------------------------
    for row_idx in range(len(df)):
        excel_row = start_row + 1 + row_idx
        fmt = alt_row_format if row_idx % 2 else cell_format

        for col_idx in range(len(df.columns)):
            worksheet.write(
                excel_row,
                col_idx,
                df.iloc[row_idx, col_idx],
                fmt
            )

    # --------------------------------------------------
    # Auto Column Width
    # --------------------------------------------------
    for col_idx, column in enumerate(df.columns):
        max_len = max(
            df[column].astype(str).map(len).max() if not df.empty else 10,
            len(column)
        )
        worksheet.set_column(col_idx, col_idx, max_len + 3)

    # --------------------------------------------------
    # Freeze Header Row
    # --------------------------------------------------
    worksheet.freeze_panes(start_row + 1, 0)

    # --------------------------------------------------
    # No Data Message
    # --------------------------------------------------
    if df.empty:
        worksheet.merge_range(
            start_row + 1, 0,
            start_row + 2, total_cols - 1,
            'No transactions found for selected filters',
            workbook.add_format({'align': 'center', 'italic': True})
        )

def apply_transaction_filters_export(qs, filters):
    if filters.get('from_date'):
            start_date = parse_month_start(filters['from_date'])
            qs = qs.filter(issue_date__gte=start_date)
    if filters.get('to_date'):
            end_date = parse_month_end(filters['to_date'])
            qs = qs.filter(issue_date__lte=end_date)
        
    from datetime import timedelta
    from django.db.models import F
    late_filter = filters.get('late_returns')
    if late_filter:
        # Only returned books
        qs = qs.filter(
            return_date__isnull=False,
            due_date__isnull=False
        )
        if late_filter == '0_3':
            qs = qs.filter(
                return_date__gt=F('due_date'),
                return_date__lte=F('due_date') + timedelta(days=3)
            )
        elif late_filter == '4_7':
            qs = qs.filter(
                return_date__gt=F('due_date') + timedelta(days=3),
                return_date__lte=F('due_date') + timedelta(days=7)
            )
        elif late_filter == '1_month':
            qs = qs.filter(
                return_date__gt=F('due_date') + timedelta(days=30)
            )
        elif late_filter == '3_month':
            qs = qs.filter(
                return_date__gt=F('due_date') + timedelta(days=90)
            )
        elif late_filter == '6_month':
            qs = qs.filter(
                return_date__gt=F('due_date') + timedelta(days=180)
            )
    if filters.get('fine_status') == 'paid':
        qs = qs.filter(
            Q(fine_amount__gt=0, fine_status='Paid') |
            Q(fine_amount__lte=0)
        )
    elif filters.get('fine_status') == 'not_paid':
        qs = qs.filter(
            Q(fine_amount__gt=0, fine_status__in=['Unpaid', 'Pending']) |
            Q(fine_amount__lte=0)
        )
    elif filters.get('fine_status') == 'adjusted':
        qs = qs.filter(
            Q(fine_amount__gt=0, fine_status='Adjusted') |
            Q(fine_amount__lte=0)
        )
    membership_type = filters.get('membership_type')
    if membership_type:
        if not isinstance(membership_type, (list, tuple)):
            membership_type = [membership_type]
    
        qs = qs.filter(member__member_type_id__in=membership_type)
    
    return qs

def export_physical_visits_to_excel(writer, db, member_ids, filters):

    activity = (filters.get('activity_type') or '').lower()
    membership_type = filters.get('membership_type')
    from_date = filters.get('from_date')
    to_date = filters.get('to_date')

    # --------------------------------------------------
    # Filter Members
    # --------------------------------------------------
    member_qs = MembershipDetails.objects.using(db).filter(id__in=member_ids)

    if membership_type:
        if not isinstance(membership_type, (list, tuple)):
            membership_type = [membership_type]
        member_qs = member_qs.filter(member_type_id__in=membership_type)

    members = list(member_qs.values(
        'id', 'membership_code', 'first_name', 'last_name'
    ))

    member_ids = [m['id'] for m in members]
    member_codes = [m['membership_code'] for m in members if m['membership_code']]

    member_map = {
        m['membership_code']: f"{m['first_name'] or ''} {m['last_name'] or ''}".strip()
        for m in members
    }

    rows = []

    # --------------------------------------------------
    # 1️⃣ Reading Room Visits
    # --------------------------------------------------
    if activity in ['', 'reading']:
        visit_qs = MemberEntryExit.objects.using(db).filter(
            membership_code__in=member_codes
        )

        if from_date:
            visit_qs = visit_qs.filter(entry_time__date__gte=from_date)
        if to_date:
            visit_qs = visit_qs.filter(entry_time__date__lte=to_date)

        for v in visit_qs:
            rows.append({
                'Activity Type': 'Reading',
                'Member Name': member_map.get(v.membership_code, ''),
                'Membership Code': v.membership_code,
                'Entry Date & Time': (
                    v.entry_time.strftime('%d-%m-%Y %H:%M')
                    if v.entry_time else ''
                ),
                'Exit Date & Time': (
                    v.exit_time.strftime('%d-%m-%Y %H:%M')
                    if v.exit_time else ''
                ),
                'Remarks': v.remark or '',
                'Recorded At': (
                    v.created_at.strftime('%d-%m-%Y %H:%M')
                    if v.created_at else ''
                )
            })

    # --------------------------------------------------
    # 2️⃣ Issue / Return Circulation
    # --------------------------------------------------
    if activity in ['', 'issue', 'return']:
        trans_qs = CirculationTransaction.objects.using(db).filter(
            member_id__in=member_ids
        )

        if activity == 'issue':
            trans_qs = trans_qs.filter(transaction_type='Issue')
            if from_date:
                trans_qs = trans_qs.filter(issue_date__gte=from_date)
            if to_date:
                trans_qs = trans_qs.filter(issue_date__lte=to_date)

        elif activity == 'return':
            trans_qs = trans_qs.filter(transaction_type='Return')
            if from_date:
                trans_qs = trans_qs.filter(return_date__gte=from_date)
            if to_date:
                trans_qs = trans_qs.filter(return_date__lte=to_date)

        else:
            if from_date:
                trans_qs = trans_qs.filter(issue_date__gte=from_date)
            if to_date:
                trans_qs = trans_qs.filter(issue_date__lte=to_date)

        for t in trans_qs:
            rows.append({
                'Activity Type': t.transaction_type,
                'Member Name': (
                    f"{t.member.first_name or ''} {t.member.last_name or ''}".strip()
                    if t.member else ''
                ),
                'Membership Code': t.membership_code,
                'Entry Date & Time': (
                    t.issue_date.strftime('%d-%m-%Y')
                    if t.issue_date else ''
                ),
                'Exit Date & Time': (
                    t.return_date.strftime('%d-%m-%Y')
                    if t.return_date else ''
                ),
                'Remarks': t.remarks or '',
                'Recorded At': (
                    t.created_at.strftime('%d-%m-%Y %H:%M')
                    if t.created_at else ''
                )
            })

    # --------------------------------------------------
    # Create DataFrame
    # --------------------------------------------------
    df = pd.DataFrame(rows)

    sheet_name = 'Physical Visits'
    start_row = 6

    df.to_excel(
        writer,
        sheet_name=sheet_name,
        index=False,
        startrow=start_row
    )

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
        'border': 1,
        'align': 'center',
        'valign': 'middle',
        'text_wrap': True,
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

    filter_label_format = workbook.add_format({'bold': True})

    # --------------------------------------------------
    # Report Header
    # --------------------------------------------------
    total_cols = len(df.columns)

    worksheet.merge_range(
        0, 0, 0, total_cols - 1,
        'Physical Visits & Circulation Activity Report',
        title_format
    )

    worksheet.merge_range(
        1, 0, 1, total_cols - 1,
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
                3, col,
                f'{key.replace("_", " ").title()}: {value}'
            )
            col += 1

    # --------------------------------------------------
    # Header Styling
    # --------------------------------------------------
    for col_idx, col_name in enumerate(df.columns):
        worksheet.write(start_row, col_idx, col_name, header_format)

    # --------------------------------------------------
    # Row Styling
    # --------------------------------------------------
    for row_idx in range(len(df)):
        excel_row = start_row + 1 + row_idx
        fmt = alt_row_format if row_idx % 2 else cell_format

        for col_idx in range(len(df.columns)):
            worksheet.write(
                excel_row,
                col_idx,
                df.iloc[row_idx, col_idx],
                fmt
            )

    # --------------------------------------------------
    # Auto Column Width
    # --------------------------------------------------
    for col_idx, column in enumerate(df.columns):
        max_len = max(
            df[column].astype(str).map(len).max() if not df.empty else 10,
            len(column)
        )
        worksheet.set_column(col_idx, col_idx, max_len + 3)

    # --------------------------------------------------
    # Freeze Header Row
    # --------------------------------------------------
    worksheet.freeze_panes(start_row + 1, 0)

    # --------------------------------------------------
    # No Data Message
    # --------------------------------------------------
    if df.empty:
        worksheet.merge_range(
            start_row + 1, 0,
            start_row + 2, total_cols - 1,
            'No physical visit or circulation activity found for selected filters',
            workbook.add_format({'align': 'center', 'italic': True})
        )

def calculate_visit_duration(visit):
    """Calculate visit duration"""
    if visit.entry_time and visit.exit_time:
        duration = visit.exit_time - visit.entry_time
        hours = duration.total_seconds() / 3600
        return f"{hours:.2f} hours"
    return 'Still in library'

def export_virtual_usage_to_excel(writer, db, member_ids, filters):
    """Export virtual usage (Login + Screen) to Excel with formatting"""

    workbook = writer.book

    # -------------------------
    # FORMATS
    # -------------------------
    title_format = workbook.add_format({
        'bold': True,
        'font_size': 14,
        'align': 'center',
        'valign': 'vcenter'
    })

    filter_format = workbook.add_format({
        'italic': True,
        'font_size': 10,
        'align': 'left'
    })

    header_format = workbook.add_format({
        'bold': True,
        'bg_color': '#D9E1F2',
        'border': 1,
        'align': 'center',
        'valign': 'vcenter'
    })

    row_format_1 = workbook.add_format({
        'border': 1,
        'align': 'left'
    })

    row_format_2 = workbook.add_format({
        'border': 1,
        'bg_color': '#F7F7F7',
        'align': 'left'
    })
    
    # -------------------------
    # DATA COLLECTION
    # -------------------------
    data = []

    member_qs = MembershipDetails.objects.using(db).filter(id__in=member_ids)

    membership_type = filters.get('membership_type')
    if membership_type:
        if not isinstance(membership_type, (list, tuple)):
            membership_type = [membership_type]
        member_qs = member_qs.filter(member_type_id__in=membership_type)

    member_ids = list(member_qs.values_list('id', flat=True))
    activity_type = (filters.get('activity_type') or '').lower()

    # LOGIN
    if activity_type in ('', 'login'):
        login_qs = MemberLoginSession.objects.using(db).filter(
            member_id__in=member_ids
        ).select_related('member')

        if filters.get('from_date'):
            login_qs = login_qs.filter(login_time__date__gte=filters['from_date'])
        if filters.get('to_date'):
            login_qs = login_qs.filter(login_time__date__lte=filters['to_date'])

        for s in login_qs:
            m = s.member
            data.append([
                f"{m.first_name or ''} {m.last_name or ''}".strip(),
                m.membership_code or '',
                'Login',
                'Login Session',
                '/login',
                s.login_time.strftime('%Y-%m-%d %H:%M:%S') if s.login_time else '',
                s.ip_address or '',
                s.device_type or '',
                calculate_session_duration_excel(s) or ''
            ])

    # SCREEN
    if activity_type in ('', 'screen'):
        activity_qs = MemberScreenActivity.objects.using(db).filter(
            session__member_id__in=member_ids
        ).select_related('session__member')

        if filters.get('from_date'):
            activity_qs = activity_qs.filter(visited_at__date__gte=filters['from_date'])
        if filters.get('to_date'):
            activity_qs = activity_qs.filter(visited_at__date__lte=filters['to_date'])

        for a in activity_qs:
            m = a.session.member
            data.append([
                f"{m.first_name or ''} {m.last_name or ''}".strip(),
                m.membership_code or '',
                'Screen',
                a.screen_name or '',
                a.screen_route or '',
                a.visited_at.strftime('%Y-%m-%d %H:%M:%S') if a.visited_at else '',
                a.session.ip_address or '',
                a.session.device_type or '',
                'N/A'
            ])

    # SORT
    data.sort(key=lambda x: x[5] or '', reverse=True)

    # -------------------------
    # WORKSHEET SETUP
    # -------------------------
    sheet_name = 'Virtual Usage'
    worksheet = workbook.add_worksheet(sheet_name)
    writer.sheets[sheet_name] = worksheet

    # -------------------------
    # REPORT HEADER
    # -------------------------
    worksheet.merge_range('A1:I1', 'Virtual Usage Report', title_format)

    filter_label_format = workbook.add_format({
        'bold': True,
        'font_size': 10,
        'align': 'left'
    })

    # Convert filter IDs → names (ONLY for display)
    filters = normalize_export_filters(filters)
    # -------------------------
    # APPLIED FILTERS (DYNAMIC)
    # -------------------------
    filter_row = 1  # Excel row 3 (0-based)

    worksheet.write(filter_row, 0, 'Applied Filters:', filter_label_format)

    col = 1
    for key, value in filters.items():
        if value:
            display_value = (
                ", ".join(value) if isinstance(value, (list, tuple)) else value
            )
            worksheet.write(
                filter_row,
                col,
                f"{key.replace('_', ' ').title()}: {display_value}",
                filter_format
            )
            col += 1


    # -------------------------
    # TABLE HEADER
    # -------------------------
    headers = [
        'Member Name', 'Membership Code', 'Activity',
        'Screen Name', 'Screen Route', 'Visited At',
        'IP Address', 'Device Type', 'Duration'
    ]

    start_row = 3
    for col, header in enumerate(headers):
        worksheet.write(start_row, col, header, header_format)

    # -------------------------
    # DATA ROWS (ZEBRA STYLE)
    # -------------------------
    for row_idx, row in enumerate(data, start=start_row + 1):
        fmt = row_format_1 if row_idx % 2 == 0 else row_format_2
        for col_idx, value in enumerate(row):
            worksheet.write(row_idx, col_idx, value, fmt)

    # -------------------------
    # COLUMN WIDTHS
    # -------------------------
    for col_idx, header in enumerate(headers):
        max_len = max(
            [len(str(r[col_idx])) for r in data] + [len(header)]
        )
        worksheet.set_column(col_idx, col_idx, max_len + 2)

    # -------------------------
    # FREEZE & FILTER
    # -------------------------
    worksheet.freeze_panes(start_row + 1, 0)
    worksheet.autofilter(start_row, 0, start_row + len(data), len(headers) - 1)

def export_payments_to_excel(writer, db, member_ids, filters):
    """Export payment data to Excel with full formatting"""

    workbook = writer.book

    # =====================================================
    # FORMATS
    # =====================================================
    title_format = workbook.add_format({
        'bold': True,
        'font_size': 14,
        'align': 'center',
        'valign': 'vcenter'
    })

    filter_format = workbook.add_format({
        'italic': True,
        'font_size': 10,
        'align': 'left'
    })

    header_format = workbook.add_format({
        'bold': True,
        'bg_color': '#D9E1F2',
        'border': 1,
        'align': 'center',
        'valign': 'vcenter',
        'text_wrap': True
    })

    row_format_1 = workbook.add_format({
        'border': 1,
        'align': 'left'
    })

    row_format_2 = workbook.add_format({
        'border': 1,
        'bg_color': '#F7F7F7',
        'align': 'left'
    })

    amount_format = workbook.add_format({
        'border': 1,
        'align': 'right',
        'num_format': '#,##0.00'
    })

    # =====================================================
    # QUERY
    # =====================================================
    qs = PaymentDetails.objects.using(db).filter(
        membership_id__in=member_ids
    ).select_related(
        'membership', 'status', 'circulation_transaction'
    ).order_by('-created_at')

    qs = apply_payment_filters_export(qs, filters)

    # =====================================================
    # DATA PREPARATION (LIST for XlsxWriter)
    # =====================================================
    data = []

    for p in qs:
        data.append([
            p.payment_mode or '',
            p.payment_type or '',
            p.payment_method or '',
            float(p.deposit_amount or 0),
            float(p.entry_fee_amount or 0),
            float(p.monthly_subscription_amount or 0),
            float(p.total_subscription_amount or 0),
            p.subscription_from.strftime('%Y-%m-%d') if p.subscription_from else '',
            p.subscription_to.strftime('%Y-%m-%d') if p.subscription_to else '',
            float(p.fine_amount or 0),
            float(p.book_fine_amount or 0),
            float(p.adjusted_amount or 0),
            p.status.status_name if p.status else '',
            p.transaction_id or '',
            p.remarks or '',
            p.user_id or '',
            p.membership_code or '',
            p.created_at.strftime('%Y-%m-%d %H:%M:%S') if p.created_at else '',
            p.created_by or '',
            p.updated_at.strftime('%Y-%m-%d %H:%M:%S') if p.updated_at else '',
            p.updated_by or '',
            p.payment_date.strftime('%Y-%m-%d') if p.payment_date else '',
            f"{p.membership.first_name or ''} {p.membership.last_name or ''}".strip()
            if p.membership else ''
        ])

    # =====================================================
    # WORKSHEET
    # =====================================================
    sheet_name = 'Payment Details'
    worksheet = workbook.add_worksheet(sheet_name)
    writer.sheets[sheet_name] = worksheet

    # =====================================================
    # REPORT HEADER
    # =====================================================
    worksheet.merge_range('A1:W1', 'Payment Details Report', title_format)

    filter_label_format = workbook.add_format({
        'bold': True,
        'font_size': 10,
        'align': 'left'
    })

    # Convert filter IDs → names (ONLY for display)
    filters = normalize_export_filters(filters)
    # =====================================================
    # APPLIED FILTERS (DYNAMIC)
    # =====================================================
    filter_row = 1  # Row index (0-based) → Excel row 3

    worksheet.write(filter_row, 0, 'Applied Filters:', filter_label_format)

    col = 1
    for key, value in filters.items():
        if value:
            worksheet.write(
                filter_row,
                col,
                f"{key.replace('_', ' ').title()}: {value}",
                filter_format
            )
            col += 1


    # =====================================================
    # TABLE HEADER
    # =====================================================
    headers = [
        'Payment Mode', 'Payment Type', 'Payment Method',
        'Deposit Amount', 'Entry Fee Amount',
        'Monthly Subscription Amount', 'Total Subscription Amount',
        'Subscription From', 'Subscription To',
        'Fine Amount', 'Book Fine Amount', 'Adjusted Amount',
        'Status', 'Transaction ID', 'Remarks', 'User ID',
        'Membership Code', 'Created At', 'Created By',
        'Updated At', 'Updated By', 'Payment Date', 'Member Name'
    ]

    start_row = 3

    for col_idx, header in enumerate(headers):
        worksheet.write(start_row, col_idx, header, header_format)

    # =====================================================
    # DATA ROWS (ZEBRA + AMOUNT FORMATS)
    # =====================================================
    amount_cols = {3, 4, 5, 6, 9, 10, 11}

    for row_idx, row in enumerate(data, start=start_row + 1):
        base_fmt = row_format_1 if row_idx % 2 == 0 else row_format_2

        for col_idx, value in enumerate(row):
            if col_idx in amount_cols:
                worksheet.write(row_idx, col_idx, value, amount_format)
            else:
                worksheet.write(row_idx, col_idx, value, base_fmt)

    # =====================================================
    # COLUMN WIDTHS
    # =====================================================
    for col_idx, header in enumerate(headers):
        max_len = max(
            [len(str(r[col_idx])) for r in data] + [len(header)]
        )
        worksheet.set_column(col_idx, col_idx, max_len + 2)

    # =====================================================
    # FREEZE HEADER + FILTER
    # =====================================================
    worksheet.freeze_panes(start_row + 1, 0)
    worksheet.autofilter(
        start_row, 0,
        start_row + len(data),
        len(headers) - 1
    )

def apply_payment_filters_export(qs, filters):
    # Date filters
    if filters.get('from_date'):
        qs = qs.filter(payment_date__gte=filters['from_date'])
    if filters.get('to_date'):
        qs = qs.filter(payment_date__lte=filters['to_date'])
    # Membership type
    if filters.get('membership_types'):
        qs = qs.filter(
            membership__member_type_id__in=filters['membership_types']
        )
    # Payment attributes
    payment_type = filters.get('payment_type')

    if payment_type:
        if payment_type == 'Fine':
            qs = qs.filter(payment_type__in=['Fine', 'Membership Renewed'])
        else:
            qs = qs.filter(payment_type=payment_type)
    if filters.get('payment_mode'):
        qs = qs.filter(payment_mode=filters['payment_mode'])
    if filters.get('payment_method'):
        qs = qs.filter(payment_method=filters['payment_method'])
    if filters.get('min_amount'):
        qs = qs.filter(fine_amount__gte=float(filters['min_amount']))
    if filters.get('max_amount'):
        qs = qs.filter(fine_amount__lte=float(filters['max_amount']))
    
    return qs

def calculate_session_duration_excel(session):
    """Calculate session duration for Excel export"""
    if session.login_time and session.logout_time:
        duration = session.logout_time - session.login_time
        minutes = duration.total_seconds() / 60
        return f"{minutes:.1f} minutes"
    return 'Still active'

class ExportReportView(ReportBaseView):
    """Export member report (single tab or all tabs) to Excel"""

    def get(self, request):
        export_type = request.GET.get('type', 'all-tabs')
        member_ids = request.GET.getlist('member_ids')
        filters_json = request.GET.get('filters', '{}')
        tab_filters_json = request.GET.get('tab_filters', '{}')

        # --------------------------------------------------
        # Normalize member_ids
        # --------------------------------------------------
        if len(member_ids) == 1 and ',' in member_ids[0]:
            member_ids = [
                int(i) for i in member_ids[0].split(',')
                if i.strip().isdigit()
            ]
        else:
            member_ids = [int(i) for i in member_ids if str(i).isdigit()]

        # --------------------------------------------------
        # Parse filters safely
        # --------------------------------------------------
        try:
            filters = json.loads(filters_json)
        except (TypeError, ValueError):
            filters = {}

        try:
            tab_filters = json.loads(tab_filters_json)
        except (TypeError, ValueError):
            tab_filters = {}

        db = self.get_library_db()

        # --------------------------------------------------
        # Create temp Excel file
        # --------------------------------------------------
        with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
            output_path = tmp.name

        try:
            # --------------------------------------------------
            # Excel Writer (pandas + xlsxwriter)
            # --------------------------------------------------
            with pd.ExcelWriter(output_path, engine="xlsxwriter") as writer:

                if export_type == 'all-tabs':
                    self.export_all_tabs(
                        writer=writer,
                        db=db,
                        member_ids=member_ids,
                        filters=filters,
                        tab_filters=tab_filters
                    )
                else:
                    self.export_single_tab(
                        writer=writer,
                        export_type=export_type,
                        db=db,
                        member_ids=member_ids,
                        filters=tab_filters
                    )

            # --------------------------------------------------
            # Prepare HTTP response
            # --------------------------------------------------
            with open(output_path, 'rb') as f:
                response = HttpResponse(
                    f.read(),
                    content_type=(
                        'application/vnd.openxmlformats-officedocument.'
                        'spreadsheetml.sheet'
                    )
                )
            
            if export_type == 'all-tabs':
                file_name = 'member_report_all_tabs.xlsx'
            else:
                safe_tab_name = export_type.replace('-', '_')
                file_name = f'member_report_{safe_tab_name}.xlsx'
            
            response['Content-Disposition'] = (
                f'attachment; filename="{file_name}"'
            )


            return response

        except Exception as e:
            return JsonResponse(
                {'error': 'Export failed', 'details': str(e)},
                status=500
            )

        finally:
            # --------------------------------------------------
            # Cleanup temp file
            # --------------------------------------------------
            if os.path.exists(output_path):
                os.unlink(output_path)

    # ======================================================
    # EXPORT HELPERS
    # ======================================================

    def export_all_tabs(self, writer, db, member_ids, filters, tab_filters):
        """Export all tabs to separate sheets"""

        export_map = {
            'member-details': export_member_details_to_excel,
            'membership-details': export_membership_details_to_excel,
            'loan': export_loan_to_excel,
            'transactions': export_transactions_to_excel,
            'physical-visit': export_physical_visits_to_excel,
            'virtual-usage': export_virtual_usage_to_excel,
            'payments': export_payments_to_excel,
        }

        for tab_name, export_func in export_map.items():
            export_func(
                writer,
                db,
                member_ids,
                tab_filters.get(tab_name, {})
            )

    def export_single_tab(self, writer, export_type, db, member_ids, filters):
        """Export a single tab"""

        export_map = {
            'member-details': export_member_details_to_excel,
            'membership-details': export_membership_details_to_excel,
            'loan': export_loan_to_excel,
            'transactions': export_transactions_to_excel,
            'physical-visit': export_physical_visits_to_excel,
            'virtual-usage': export_virtual_usage_to_excel,
            'payments': export_payments_to_excel,
        }

        export_func = export_map.get(export_type)

        if export_func:
            export_func(
                writer,
                db,
                member_ids,
                filters
            )
        else:
            # Fallback sheet
            workbook = writer.book
            worksheet = workbook.add_worksheet(
                export_type.replace('-', ' ').title()
            )
            worksheet.write(0, 0, 'No data available')
            
class ExportAllDataView(ReportBaseView):
    """Export selected tabs data to Excel"""

    def get(self, request):
        # --------------------------------
        # Parse inputs
        # --------------------------------
        member_ids = request.GET.getlist('member_ids')
        selected_tabs = request.GET.getlist('tabs')
        filename = request.GET.get('filename', 'member_report')
        format_type = request.GET.get('format', 'excel')

        filters_json = request.GET.get('filters', '{}')
        tab_filters_json = request.GET.get('tab_filters', '{}')

        member_ids = [int(i) for i in member_ids if str(i).isdigit()]

        try:
            filters = json.loads(filters_json)
        except Exception:
            filters = {}

        try:
            tab_filters = json.loads(tab_filters_json)
        except Exception:
            tab_filters = {}

        if not member_ids:
            return JsonResponse({'error': 'No members selected'}, status=400)

        if not selected_tabs:
            return JsonResponse({'error': 'No tabs selected'}, status=400)

        db = self.get_library_db()

        # --------------------------------
        # Export function map
        # --------------------------------
        export_map = {
            'member-details': export_member_details_to_excel,
            'membership-details': export_membership_details_to_excel,
            'loan': export_loan_to_excel,
            'transactions': export_transactions_to_excel,
            'physical-visit': export_physical_visits_to_excel,
            'virtual-usage': export_virtual_usage_to_excel,
            'payments': export_payments_to_excel,
        }

        # --------------------------------
        # Create temp Excel
        # --------------------------------
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
            output_path = tmp.name

        try:
            with pd.ExcelWriter(output_path, engine='xlsxwriter') as writer:

                for tab in selected_tabs:
                    export_func = export_map.get(tab)
                    if not export_func:
                        continue  # skip unknown tabs

                    export_func(
                        writer=writer,
                        db=db,
                        member_ids=member_ids,
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
            return JsonResponse(
                {'error': 'Export failed', 'details': str(e)},
                status=500
            )

        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)
