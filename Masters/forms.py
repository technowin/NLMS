from django import forms
from django.core.exceptions import ValidationError
from .models import LibraryEvent, EventImage, EventPDF
import os
from django.forms import ClearableFileInput, FileInput


class MultipleFileInput(ClearableFileInput):
    allow_multiple_selected = True


class LibraryEventForm(forms.ModelForm):
    images = forms.FileField(
        required=False,
        widget=MultipleFileInput(attrs={
            'accept': 'image/*',
            'class': 'form-control'
        })
    )

    pdfs = forms.FileField(
        required=False,
        widget=MultipleFileInput(attrs={
            'accept': '.pdf',
            'class': 'form-control'
        })
    )

    
    class Meta:
        model = LibraryEvent
        fields = [
            'scope', 'library', 'event_name', 'description',
            'event_type', 'date', 'from_date', 'to_date',
            'start_time','end_time','location'
        ]
        widgets = {
            'scope': forms.RadioSelect(attrs={'class': 'form-check-input'}),
            'library': forms.Select(attrs={'class': 'form-control'}),
            'event_name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'event_type': forms.RadioSelect(attrs={'class': 'form-check-input'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'from_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'to_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'start_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'location': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Initially hide library dropdown
        # if 'library' in self.fields:
        #     self.fields['library'].widget.attrs['style'] = 'display: none;'
        
        # # Hide appropriate date fields based on event type
        # self.fields['date'].widget.attrs['style'] = 'display: none;'
        # self.fields['from_date'].widget.attrs['style'] = 'display: none;'
        # self.fields['to_date'].widget.attrs['style'] = 'display: none;'
        pass
    
    def clean(self):
        cleaned_data = super().clean()
        event_type = cleaned_data.get('event_type')
        scope = cleaned_data.get('scope')
        
        # Validate scope and library
        if scope == 'specific' and not cleaned_data.get('library'):
            self.add_error('library', 'Please select a library for specific events.')
        
        # Validate dates based on event type
        if event_type == 'single':
            if not cleaned_data.get('date'):
                self.add_error('date', 'Date is required for single day events.')
            # Clear multiple day dates if not needed
            cleaned_data['from_date'] = None
            cleaned_data['to_date'] = None
        else:  # multiple day event
            if not cleaned_data.get('from_date') or not cleaned_data.get('to_date'):
                self.add_error('from_date', 'Both From Date and To Date are required for multiple day events.')
            if cleaned_data.get('from_date') and cleaned_data.get('to_date'):
                if cleaned_data['from_date'] > cleaned_data['to_date']:
                    self.add_error('to_date', 'To Date must be after From Date.')
            # Clear single date if not needed
            cleaned_data['date'] = None
        
        # Validate file sizes (4MB = 4 * 1024 * 1024 bytes)
        images = self.files.getlist('images')
        for image in images:
            if image.size > 4 * 1024 * 1024:
                self.add_error('images', f'{image.name} is too large. Maximum size is 4MB.')
        
        pdfs = self.files.getlist('pdfs')
        for pdf in pdfs:
            if pdf.size > 4 * 1024 * 1024:
                self.add_error('pdfs', f'{pdf.name} is too large. Maximum size is 4MB.')
        
        return cleaned_data
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        if commit:
            instance.save()
            
            # Save images
            for image in self.files.getlist('images'):
                EventImage.objects.create(event=instance, image=image)
            
            # Save PDFs
            for pdf in self.files.getlist('pdfs'):
                EventPDF.objects.create(event=instance, pdf_file=pdf)
        
        return instance