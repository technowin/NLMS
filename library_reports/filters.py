# reports/filters.py
from django_filters import FilterSet, CharFilter, ChoiceFilter, DateFilter, DateRangeFilter, NumberFilter
from django_filters.widgets import RangeWidget
import django_filters

class MemberFilter(FilterSet):
    """Filter for member reports"""
    
    membership_type = django_filters.CharFilter(
        field_name='membership__id',
        lookup_expr='in',
        label='Membership Type'
    )
    
    status = django_filters.CharFilter(
        field_name='status__id',
        lookup_expr='in',
        label='Status'
    )
    
    ward = django_filters.CharFilter(
        field_name='ward',
        lookup_expr='icontains',
        label='Ward'
    )
    
    date_range = DateRangeFilter(
        field_name='created_at',
        label='Date Range'
    )
    
    member_type = django_filters.CharFilter(
        field_name='member_type__id',
        lookup_expr='in',
        label='Member Type'
    )
    
    class Meta:
        fields = ['membership_type', 'status', 'ward', 'date_range', 'member_type']


class BookFilter(FilterSet):
    """Filter for book reports (to be implemented)"""
    pass


class TabFilter:
    """Base class for tab-specific filters"""
    
    @staticmethod
    def get_member_details_filters():
        return {
            'membership_month_from': {
                'type': 'month',
                'label': 'Membership Month From',
                'field': 'membership_start_date__month'
            },
            'membership_month_to': {
                'type': 'month',
                'label': 'Membership Month To',
                'field': 'membership_start_date__month'
            },
            'ward': {
                'type': 'select',
                'label': 'Ward',
                'field': 'ward'
            },
            'renewal_due_month': {
                'type': 'month',
                'label': 'Renewal Due Month',
                'field': 'to_date__month'
            }
        }
    
    @staticmethod
    def get_loan_filters():
        return {
            'from_date': {
                'type': 'date',
                'label': 'From Date',
                'field': 'issue_date__gte'
            },
            'to_date': {
                'type': 'date',
                'label': 'To Date',
                'field': 'issue_date__lte'
            },
            'overdue': {
                'type': 'select',
                'label': 'Overdue',
                'field': 'days_overdue_count__gt',
                'options': [
                    {'value': 'yes', 'label': 'Yes'},
                    {'value': 'no', 'label': 'No'}
                ]
            },
            'fine_status': {
                'type': 'select',
                'label': 'Fine Status',
                'field': 'fine_status',
                'options': [
                    {'value': 'paid', 'label': 'Paid'},
                    {'value': 'unpaid', 'label': 'Unpaid'},
                    {'value': 'partial', 'label': 'Partial'}
                ]
            }
        }