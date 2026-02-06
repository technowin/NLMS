# reports/forms.py
from django import forms
from django.conf import settings
from django.utils import timezone
import datetime
from L01.models import parameter_master_L01, MembershipMaster

class BookListFilterForm(forms.Form):
    """Form for filtering book list on left side"""
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search...'
        })
    )
    
    list_type = forms.ChoiceField(
        initial='title',
        choices=[
            ('title', 'Title'),
            ('author', 'Author'),
            ('category', 'Category'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    # Filters for Title tab only
    language = forms.ChoiceField(
        required=False,
        choices=[
            ('', 'All Languages'),
            ('English', 'English'),
            ('Hindi', 'हिंदी'),
            ('Marathi', 'मराठी'),
            ('Other', 'Other'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    resource_type = forms.ChoiceField(
        required=False,
        choices=[
            ('', 'All Resources'),
            ('book', 'Book'),
            ('ebook', 'Ebook'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'})
    )

class CatalogueFilterForm(forms.Form):
    """Filters for Catalogue tab"""
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
    
    language = forms.MultipleChoiceField(
        required=False,
        choices=[
            ('English', 'English'),
            ('Hindi', 'हिंदी'),
            ('Marathi', 'मराठी'),
            ('Other', 'Other'),
        ],
        widget=forms.SelectMultiple(attrs={'class': 'form-select'})
    )
    
    subject = forms.MultipleChoiceField(
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'form-select'})
    )
    
    status = forms.MultipleChoiceField(
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'form-select'})
    )
    
    ebook_available = forms.ChoiceField(
        required=False,
        choices=[
            ('', 'All'),
            ('Yes', 'Yes'),
            ('No', 'No'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # These will be populated dynamically in the view
        self.fields['subject'].choices = []
        self.fields['status'].choices = []

class AccessionFilterForm(forms.Form):
    """Filters for Accession tab"""
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
    
    condition = forms.MultipleChoiceField(
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'form-select'})
    )
    
    source = forms.MultipleChoiceField(
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'form-select'})
    )
    
    location = forms.MultipleChoiceField(
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'form-select'})
    )
    
    status = forms.MultipleChoiceField(
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'form-select'})
    )
    
    supplier = forms.MultipleChoiceField(
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'form-select'})
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # These will be populated dynamically in the view
        self.fields['condition'].choices = []
        self.fields['source'].choices = []
        self.fields['location'].choices = []
        self.fields['status'].choices = []
        self.fields['supplier'].choices = []

class CirculationFilterForm(forms.Form):
    """Filters for Circulation tab"""
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
    
    processing_status = forms.MultipleChoiceField(
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'form-select'})
    )
    
    shelf_location = forms.MultipleChoiceField(
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'form-select'})
    )
    
    current_status = forms.MultipleChoiceField(
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'form-select'})
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # These will be populated dynamically in the view
        self.fields['processing_status'].choices = []
        self.fields['shelf_location'].choices = []
        self.fields['current_status'].choices = []

class LoanFilterForm(forms.Form):
    """Filters for Loan tab"""
    issue_from_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control datepicker',
            'type': 'date'
        })
    )
    issue_to_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control datepicker',
            'type': 'date'
        })
    )
    
    due_from_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control datepicker',
            'type': 'date'
        })
    )
    due_to_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control datepicker',
            'type': 'date'
        })
    )
    
    overdue = forms.ChoiceField(
        required=False,
        choices=[
            ('', 'All'),
            ('0_3', '0-3 Days'),
            ('4_7', '4-7 Days'),
            ('1_month', 'More than 1 Month'),
            ('3_month', 'More than 3 Months'),
            ('6_month', 'More than 6 Months'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    fine_status = forms.ChoiceField(
        required=False,
        choices=[
            ('', 'All'),
            ('paid', 'Paid'),
            ('unpaid', 'Unpaid'),
            ('adjusted', 'Adjusted'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'})
    )

class CirculationTransactionFilterForm(forms.Form):
    """Filters for Circulation Transaction tab"""
    issue_from_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control datepicker',
            'type': 'date'
        })
    )
    issue_to_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control datepicker',
            'type': 'date'
        })
    )
    
    due_from_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control datepicker',
            'type': 'date'
        })
    )
    due_to_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control datepicker',
            'type': 'date'
        })
    )
    
    return_from_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control datepicker',
            'type': 'date'
        })
    )
    return_to_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control datepicker',
            'type': 'date'
        })
    )
    
    overdue = forms.ChoiceField(
        required=False,
        choices=[
            ('', 'All'),
            ('0_3', '0-3 Days'),
            ('4_7', '4-7 Days'),
            ('1_month', 'More than 1 Month'),
            ('3_month', 'More than 3 Months'),
            ('6_month', 'More than 6 Months'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    book_fine = forms.ChoiceField(
        required=False,
        choices=[
            ('', 'All'),
            ('yes', 'Yes'),
            ('no', 'No'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    book_loss_fine = forms.ChoiceField(
        required=False,
        choices=[
            ('', 'All'),
            ('yes', 'Yes'),
            ('no', 'No'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    fine_status = forms.ChoiceField(
        required=False,
        choices=[
            ('', 'All'),
            ('paid', 'Paid'),
            ('unpaid', 'Unpaid'),
            ('adjusted', 'Adjusted'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'})
    )

class SupplierFilterForm(forms.Form):
    """Filters for Supplier tab"""
    supplier = forms.MultipleChoiceField(
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'form-select'})
    )
    
    is_active = forms.ChoiceField(
        required=False,
        choices=[
            ('', 'All'),
            ('1', 'Active'),
            ('0', 'Inactive'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['supplier'].choices = []

class ReviewFilterForm(forms.Form):
    """Filters for Review tab"""
    rating = forms.MultipleChoiceField(
        required=False,
        choices=[
            ('1', '1 Star'),
            ('2', '2 Stars'),
            ('3', '3 Stars'),
            ('4', '4 Stars'),
            ('5', '5 Stars'),
        ],
        widget=forms.SelectMultiple(attrs={'class': 'form-select'})
    )
    
    library = forms.MultipleChoiceField(
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'form-select'})
    )
    
    book_title = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter book title...'
        })
    )
    
    catalogue = forms.MultipleChoiceField(
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'form-select'})
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['library'].choices = []
        self.fields['catalogue'].choices = []

class ReturnLogFilterForm(forms.Form):
    """Filters for Return Log tab"""
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
    
    is_shelved = forms.ChoiceField(
        required=False,
        choices=[
            ('', 'All'),
            ('true', 'Shelved'),
            ('false', 'Not Shelved'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    catalog = forms.MultipleChoiceField(
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'form-select'})
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['catalog'].choices = []

class GoogleMetadataFilterForm(forms.Form):
    """Filters for Google Metadata tab"""
    title = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search title...'
        })
    )
    
    isbn = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search ISBN...'
        })
    )
    
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

class LOCMetadataFilterForm(forms.Form):
    """Filters for LOC Metadata tab"""
    title = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search title...'
        })
    )
    
    isbn = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search ISBN...'
        })
    )
    
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