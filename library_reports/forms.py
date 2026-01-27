# reports/forms.py
from django import forms
from django.conf import settings
from django.utils import timezone
import datetime
from L01.models import parameter_master_L01, MembershipMaster


class MemberListFilterForm(forms.Form):
    search = forms.CharField(required=False, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Search members...'
    }))
    
    membership_type = forms.MultipleChoiceField(
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'form-select'})
    )
    
    membership_status = forms.MultipleChoiceField(
        required=False,
        choices=[
            ('active', 'Active'),
            ('inactive', 'Inactive'),
            ('cancelled', 'Cancelled'),
        ],
        widget=forms.SelectMultiple(attrs={'class': 'form-select'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['membership_type'].choices = [
            (m.id, m.membership_type_en)
            for m in MembershipMaster.objects.using('L01').filter(isactive=1)
        ]

class MemberDetailsFilterForm(forms.Form):
    membership_month_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control datepicker',
            'type': 'month'
        })
    )
    
    membership_month_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control datepicker',
            'type': 'month'
        })
    )
    
    membership_type = forms.MultipleChoiceField(
        required=False,
        choices=[
            ('book_branch', 'Book Branch'),
            ('children_branch', 'Children Branch'),
            ('book_branch_nmc', 'Book Branch (NMC)'),
            ('children_branch_nmc', 'Children Branch (NMC)'),
            ('lifetime_branch', 'Lifetime Branch'),
            ('patron_branch', 'Patron Branch'),
            ('practitioner_branch', 'Practitioner Branch'),
        ],
        widget=forms.SelectMultiple(attrs={
            'class': 'form-select',
            'multiple': 'multiple',
            'data-placeholder': 'Select membership types...'
        })
    )
    
    ward = forms.CharField(required=False, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Enter ward...'
    }))
    
    status = forms.MultipleChoiceField(
        required=False,
        choices=[
            ('1', 'Active'),
            ('0', 'Inactive'),
        ],
        widget=forms.SelectMultiple(attrs={'class': 'form-select'})
    )
    
    renewal_due_month = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control datepicker',
            'type': 'month'
        })
    )
    
    member_type = forms.ModelMultipleChoiceField(
        queryset=parameter_master_L01.objects.filter(isactive=1),
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'form-select'})
    )

class MembershipDetailsFilterForm(forms.Form):
    from_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control datepicker'})
    )
    to_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control datepicker'})
    )
    
    gap_period = forms.ChoiceField(
        required=False,
        choices=[
            ('', 'Any'),
            ('has_gap', 'Has Gap Period'),
            ('no_gap', 'No Gap Period'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    action_performed = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Action performed by...'
        })
    )

class LoanFilterForm(forms.Form):
    from_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control datepicker'})
    )
    to_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control datepicker'})
    )
    
    overdue = forms.ChoiceField(
        required=False,
        choices=[
            ('', 'All'),
            ('overdue', 'Overdue Only'),
            ('not_overdue', 'Not Overdue'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    fine_status = forms.ChoiceField(
        required=False,
        choices=[
            ('', 'Both'),
            ('paid', 'Paid'),
            ('not_paid', 'Not Paid'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'})
    )

# Similar forms for other tabs...
class TransactionFilterForm(forms.Form):
    from_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control datepicker',
            'type': 'month'
        })
    )
    to_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control datepicker',
            'type': 'month'
        })
    )
    
    late_returns = forms.ChoiceField(
        required=False,
        choices=[
            ('', 'All'),
            ('late', 'Late Returns Only'),
            ('on_time', 'On Time Returns'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'})
    )

# reports/forms.py - COMPLETE ALL FORMS

class PhysicalVisitFilterForm(forms.Form):
    from_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control datepicker',
            'type': 'date'
        })
    )
    to_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control datepicker',
            'type': 'date'
        })
    )
    
    membership_type = forms.MultipleChoiceField(
        required=False,
        widget=forms.SelectMultiple(attrs={
            'class': 'form-select',
            'multiple': 'multiple'
        })
    )
    
    activity_type = forms.ChoiceField(
        required=False,
        choices=[
            ('', 'All Activities'),
            ('entry', 'Entry Only'),
            ('exit', 'Exit Only'),
            ('completed', 'Completed Visits'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    remarks_search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search in remarks...'
        })
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['membership_type'].choices = self.get_membership_type_choices()
    
    def get_membership_type_choices(self):
        try:
            from L01.models import MembershipMaster
            types = MembershipMaster.objects.filter(isactive=1).values_list('id', 'membership_type')
            return [(str(t[0]), t[1]) for t in types]
        except:
            return []

class VirtualUsageFilterForm(forms.Form):
    from_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control datepicker',
            'type': 'date'
        })
    )
    to_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control datepicker',
            'type': 'date'
        })
    )
    
    membership_type = forms.MultipleChoiceField(
        required=False,
        widget=forms.SelectMultiple(attrs={
            'class': 'form-select',
            'multiple': 'multiple'
        })
    )
    
    activity_type = forms.ChoiceField(
        required=False,
        choices=[
            ('', 'All Activities'),
            ('login', 'Login Sessions Only'),
            ('screen', 'Screen Activities Only'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    screen_name = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter screen name...'
        })
    )
    
    device_type = forms.ChoiceField(
        required=False,
        choices=[
            ('', 'All Devices'),
            ('desktop', 'Desktop'),
            ('mobile', 'Mobile'),
            ('tablet', 'Tablet'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['membership_type'].choices = self.get_membership_type_choices()
    
    def get_membership_type_choices(self):
        try:
            from L01.models import MembershipMaster
            types = MembershipMaster.objects.filter(isactive=1).values_list('id', 'membership_type')
            return [(str(t[0]), t[1]) for t in types]
        except:
            return []

class PaymentFilterForm(forms.Form):
    from_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control datepicker',
            'type': 'date'
        })
    )
    to_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control datepicker',
            'type': 'date'
        })
    )
    
    membership_type = forms.MultipleChoiceField(
        required=False,
        widget=forms.SelectMultiple(attrs={
            'class': 'form-select',
            'multiple': 'multiple'
        })
    )
    
    payment_type = forms.ChoiceField(
        required=False,
        choices=[
            ('', 'All Types'),
            ('deposit', 'Deposit'),
            ('entry_fee', 'Entry Fee'),
            ('subscription', 'Subscription'),
            ('fine', 'Fine'),
            ('renewal', 'Renewal'),
            ('other', 'Other'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    payment_mode = forms.ChoiceField(
        required=False,
        choices=[
            ('', 'All Modes'),
            ('cash', 'Cash'),
            ('cheque', 'Cheque'),
            ('online', 'Online'),
            ('card', 'Card'),
            ('bank_transfer', 'Bank Transfer'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    payment_method = forms.ChoiceField(
        required=False,
        choices=[
            ('', 'All Methods'),
            ('razorpay', 'Razorpay'),
            ('paytm', 'Paytm'),
            ('google_pay', 'Google Pay'),
            ('phonepe', 'PhonePe'),
            ('bank_transfer', 'Bank Transfer'),
            ('cash', 'Cash'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    min_amount = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter minimum amount...'
        })
    )
    
    max_amount = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter maximum amount...'
        })
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['membership_type'].choices = self.get_membership_type_choices()
    
    def get_membership_type_choices(self):
        try:
            from L01.models import MembershipMaster
            types = MembershipMaster.objects.filter(isactive=1).values_list('id', 'membership_type')
            return [(str(t[0]), t[1]) for t in types]
        except:
            return []


    # reports/forms.py - ADD THESE MISSING FORM CLASSES

class CompleteMemberDetailsFilterForm(MemberDetailsFilterForm):
    """Extended form with all filter options"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add dynamic choices for member types
        self.fields['member_type'].queryset = parameter_master_L01.objects.filter(isactive=1)

class MembershipDetailsFilterForm(forms.Form):
    """Complete membership details filter form"""
    from_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control datepicker',
            'type': 'date'
        })
    )
    to_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control datepicker',
            'type': 'date'
        })
    )
    
    membership_type = forms.MultipleChoiceField(
        required=False,
        widget=forms.SelectMultiple(attrs={
            'class': 'form-select',
            'multiple': 'multiple'
        })
    )
    
    gap_period = forms.ChoiceField(
        required=False,
        choices=[
            ('', 'Any'),
            ('has_gap', 'Has Gap Period'),
            ('no_gap', 'No Gap Period'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    action_performed = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter admin username...'
        })
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Initialize membership type choices dynamically
        self.fields['membership_type'].choices = self.get_membership_type_choices()
    
    def get_membership_type_choices(self):
        """Get membership type choices from database"""
        try:
            from L01.models import MembershipMaster
            types = MembershipMaster.objects.filter(isactive=1).values_list('id', 'membership_type')
            return [(str(t[0]), t[1]) for t in types]
        except:
            return []

class LoanFilterForm(forms.Form):
    """Complete loan filter form"""
    from_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control datepicker',
            'type': 'date'
        })
    )
    to_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control datepicker',
            'type': 'date'
        })
    )
    
    membership_type = forms.MultipleChoiceField(
        required=False,
        widget=forms.SelectMultiple(attrs={
            'class': 'form-select',
            'multiple': 'multiple'
        })
    )
    
    overdue = forms.ChoiceField(
        required=False,
        choices=[
            ('', 'All'),
            ('overdue', 'Overdue Only'),
            ('not_overdue', 'Not Overdue'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    fine_status = forms.ChoiceField(
        required=False,
        choices=[
            ('', 'Both'),
            ('paid', 'Paid'),
            ('not_paid', 'Not Paid'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['membership_type'].choices = self.get_membership_type_choices()
    
    def get_membership_type_choices(self):
        """Get membership type choices from database"""
        try:
            from L01.models import MembershipMaster
            types = MembershipMaster.objects.filter(isactive=1).values_list('id', 'membership_type')
            return [(str(t[0]), t[1]) for t in types]
        except:
            return []

