# reports/views_config.py
import json
from django.http import JsonResponse, HttpResponse
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404, render
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.db.models import Q
import logging

from .models import ReportConfiguration

logger = logging.getLogger(__name__)

class ReportConfigurationListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """List all report configurations"""
    model = ReportConfiguration
    template_name = 'reports/config_list.html'
    context_object_name = 'configurations'
    paginate_by = 20
    
    def test_func(self):
        return self.request.user.has_perm('reports.manage_configurations')
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by report type
        report_type = self.request.GET.get('report_type')
        if report_type:
            queryset = queryset.filter(report_type=report_type)
        
        # Filter by search
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(description__icontains=search)
            )
        
        # Filter by status
        status = self.request.GET.get('status')
        if status == 'active':
            queryset = queryset.filter(is_active=True)
        elif status == 'inactive':
            queryset = queryset.filter(is_active=False)
        
        return queryset.order_by('report_type', 'name')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['report_types'] = ReportConfiguration.REPORT_TYPES
        context['current_filters'] = {
            'report_type': self.request.GET.get('report_type', ''),
            'search': self.request.GET.get('search', ''),
            'status': self.request.GET.get('status', ''),
        }
        return context

class ReportConfigurationCreateView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """Create new report configuration"""
    template_name = 'reports/config_form.html'
    
    def test_func(self):
        return self.request.user.has_perm('reports.manage_configurations')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['mode'] = 'create'
        context['report_types'] = ReportConfiguration.REPORT_TYPES
        context['field_types'] = ReportConfiguration.FIELD_TYPES
        context['available_models'] = self.get_available_models()
        context['default_config'] = self.get_default_config()
        return context
    
    def get_available_models(self):
        """Get available Django models"""
        # In practice, you would dynamically get all models
        # For now, return a predefined list
        return [
            {'value': 'L01.models.MembershipDetails', 'label': 'Membership Details'},
            {'value': 'L01.models.MembershipDetailsHistory', 'label': 'Membership History'},
            {'value': 'L01.models.BookCatalog', 'label': 'Book Catalog'},
            {'value': 'L01.models.CirculationTransaction', 'label': 'Circulation Transaction'},
            {'value': 'L01.models.PaymentDetails', 'label': 'Payment Details'},
            {'value': 'L01.models.MemberEntryExit', 'label': 'Member Entry/Exit'},
            {'value': 'L01.models.MemberScreenActivity', 'label': 'Member Screen Activity'},
            {'value': 'L01.models.DocumentDetails', 'label': 'Document Details'},
            {'value': 'L01.models.BookMaster', 'label': 'Book Master'},
            {'value': 'L01.models.BookDetails', 'label': 'Book Details'},
        ]
    
    def get_default_config(self):
        """Get default configuration structure"""
        return {
            'tabs': [
                {
                    'id': 'tab_1',
                    'title': 'Report Tab 1',
                    'icon': 'bi-table',
                    'description': 'Tab description',
                    'has_documents': False,
                    'exportable': True,
                    'filters': [],
                    'default_sort': {'field': 'created_at', 'direction': 'desc'}
                }
            ],
            'filters': {},
            'columns': [
                {
                    'data': 'id',
                    'title': 'ID',
                    'field_type': 'text',
                    'orderable': True,
                    'searchable': True,
                    'visible': True
                }
            ],
            'default_settings': {
                'page_length': 25,
                'responsive': True,
                'export_enabled': True,
                'print_enabled': True,
                'search_enabled': True
            }
        }

class ReportConfigurationUpdateView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """Update existing report configuration"""
    template_name = 'reports/config_form.html'
    
    def test_func(self):
        return self.request.user.has_perm('reports.manage_configurations')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        config_id = self.kwargs.get('pk')
        config = get_object_or_404(ReportConfiguration, id=config_id)
        
        context['mode'] = 'edit'
        context['config'] = config
        context['report_types'] = ReportConfiguration.REPORT_TYPES
        context['field_types'] = ReportConfiguration.FIELD_TYPES
        context['available_models'] = self.get_available_models()
        context['config_data'] = {
            'tabs': config.tabs,
            'filters': config.filters,
            'columns': config.columns,
            'default_settings': config.default_settings
        }
        
        return context
    
    def get_available_models(self):
        """Same as CreateView"""
        return [
            {'value': 'L01.models.MembershipDetails', 'label': 'Membership Details'},
            # ... same as above
        ]

@method_decorator(csrf_exempt, name='dispatch')
class ReportConfigurationSaveAPI(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """API endpoint to save report configuration"""
    
    def test_func(self):
        return self.request.user.has_perm('reports.manage_configurations')
    
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            mode = data.get('mode')  # 'create' or 'edit'
            config_id = data.get('id')
            
            # Basic validation
            required_fields = ['name', 'report_type', 'base_model', 'tabs', 'filters', 'columns']
            for field in required_fields:
                if field not in data or not data[field]:
                    return JsonResponse({
                        'success': False,
                        'error': f'Missing required field: {field}'
                    }, status=400)
            
            if mode == 'edit' and config_id:
                # Update existing configuration
                config = get_object_or_404(ReportConfiguration, id=config_id)
                config.name = data['name']
                config.description = data.get('description', '')
                config.report_type = data['report_type']
                config.base_model = data['base_model']
                config.tabs = data['tabs']
                config.filters = data['filters']
                config.columns = data['columns']
                config.default_settings = data.get('default_settings', {})
                config.is_active = data.get('is_active', True)
                config.is_default = data.get('is_default', False)
                config.updated_by = request.user.username
                
                # Validate configuration
                errors = config.validate_configuration()
                if errors:
                    return JsonResponse({
                        'success': False,
                        'error': 'Configuration validation failed',
                        'details': errors
                    }, status=400)
                
                config.save()
                
                return JsonResponse({
                    'success': True,
                    'message': 'Configuration updated successfully',
                    'config_id': config.id
                })
                
            else:
                # Create new configuration
                config = ReportConfiguration(
                    name=data['name'],
                    description=data.get('description', ''),
                    report_type=data['report_type'],
                    base_model=data['base_model'],
                    tabs=data['tabs'],
                    filters=data['filters'],
                    columns=data['columns'],
                    default_settings=data.get('default_settings', {}),
                    is_active=data.get('is_active', True),
                    is_default=data.get('is_default', False),
                    created_by=request.user.username,
                    updated_by=request.user.username
                )
                
                # Validate configuration
                errors = config.validate_configuration()
                if errors:
                    return JsonResponse({
                        'success': False,
                        'error': 'Configuration validation failed',
                        'details': errors
                    }, status=400)
                
                config.save()
                
                return JsonResponse({
                    'success': True,
                    'message': 'Configuration created successfully',
                    'config_id': config.id
                })
                
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'Invalid JSON data'
            }, status=400)
        except Exception as e:
            logger.error(f"Error saving report configuration: {str(e)}", exc_info=True)
            return JsonResponse({
                'success': False,
                'error': f'Server error: {str(e)}'
            }, status=500)

class ReportConfigurationDeleteView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """Delete report configuration"""
    
    def test_func(self):
        return self.request.user.has_perm('reports.manage_configurations')
    
    def post(self, request, *args, **kwargs):
        try:
            config_id = request.POST.get('config_id')
            config = get_object_or_404(ReportConfiguration, id=config_id)
            
            # Don't allow deletion of default configurations
            if config.is_default:
                return JsonResponse({
                    'success': False,
                    'error': 'Cannot delete default configuration'
                })
            
            config.delete()
            
            return JsonResponse({
                'success': True,
                'message': 'Configuration deleted successfully'
            })
            
        except Exception as e:
            logger.error(f"Error deleting report configuration: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)

class ReportConfigurationPreviewView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """Preview report configuration"""
    template_name = 'reports/config_preview.html'
    
    def test_func(self):
        return self.request.user.has_perm('reports.manage_configurations')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        config_id = self.kwargs.get('pk')
        config = get_object_or_404(ReportConfiguration, id=config_id)
        
        context['config'] = config
        context['preview_data'] = config.get_preview_data()
        
        return context

@method_decorator(csrf_exempt, name='dispatch')
class GetModelFieldsAPI(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """API to get fields from a Django model"""
    
    def test_func(self):
        return self.request.user.has_perm('reports.manage_configurations')
    
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            model_path = data.get('model_path')
            
            if not model_path:
                return JsonResponse({
                    'success': False,
                    'error': 'Model path is required'
                }, status=400)
            
            # Dynamically import the model and get its fields
            # This is a simplified version - in production, you'd need better error handling
            try:
                # Split the model path
                app_label, model_name = model_path.split('.')[-2:]
                
                # Get the model class
                from django.apps import apps
                model_class = apps.get_model(app_label, model_name)
                
                # Get field information
                fields = []
                for field in model_class._meta.get_fields():
                    field_info = {
                        'name': field.name,
                        'verbose_name': getattr(field, 'verbose_name', field.name),
                        'type': field.get_internal_type(),
                        'help_text': getattr(field, 'help_text', ''),
                        'related_model': None
                    }
                    
                    # Check if it's a related field
                    if hasattr(field, 'related_model') and field.related_model:
                        field_info['related_model'] = f"{field.related_model._meta.app_label}.{field.related_model.__name__}"
                    
                    fields.append(field_info)
                
                # Also include related fields from related models
                related_fields = []
                for related_object in model_class._meta.related_objects:
                    related_fields.append({
                        'name': f"{related_object.related_model.__name__.lower()}__{related_object.field.name}",
                        'verbose_name': f"{related_object.related_model.__name__} ({related_object.field.name})",
                        'type': 'related',
                        'help_text': f'Related field from {related_object.related_model.__name__}'
                    })
                
                return JsonResponse({
                    'success': True,
                    'fields': fields,
                    'related_fields': related_fields,
                    'model_name': model_class.__name__
                })
                
            except Exception as e:
                logger.error(f"Error getting model fields: {str(e)}")
                return JsonResponse({
                    'success': False,
                    'error': f'Error loading model: {str(e)}'
                }, status=400)
                
        except Exception as e:
            logger.error(f"Error in GetModelFieldsAPI: {str(e)}", exc_info=True)
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class CloneReportConfigurationAPI(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """API to clone an existing report configuration"""
    
    def test_func(self):
        return self.request.user.has_perm('reports.manage_configurations')
    
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            config_id = data.get('config_id')
            new_name = data.get('new_name', '')
            
            if not config_id:
                return JsonResponse({
                    'success': False,
                    'error': 'Configuration ID is required'
                })
            
            config = get_object_or_404(ReportConfiguration, id=config_id)
            
            # Create a clone
            new_config = ReportConfiguration(
                name=new_name or f"{config.name} (Copy)",
                description=config.description,
                report_type=config.report_type,
                base_model=config.base_model,
                tabs=config.tabs,
                filters=config.filters,
                columns=config.columns,
                default_settings=config.default_settings,
                is_active=config.is_active,
                is_default=False,  # Clone should not be default
                created_by=request.user.username,
                updated_by=request.user.username
            )
            
            new_config.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Configuration cloned successfully',
                'new_config_id': new_config.id
            })
            
        except Exception as e:
            logger.error(f"Error cloning configuration: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)

class ReportConfigurationExportView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """Export report configuration as JSON"""
    
    def test_func(self):
        return self.request.user.has_perm('reports.manage_configurations')
    
    def get(self, request, *args, **kwargs):
        config_id = self.kwargs.get('pk')
        config = get_object_or_404(ReportConfiguration, id=config_id)
        
        export_data = {
            'name': config.name,
            'description': config.description,
            'report_type': config.report_type,
            'base_model': config.base_model,
            'tabs': config.tabs,
            'filters': config.filters,
            'columns': config.columns,
            'default_settings': config.default_settings,
            'is_active': config.is_active,
            'is_default': config.is_default,
            'created_at': config.created_at.isoformat(),
            'updated_at': config.updated_at.isoformat()
        }
        
        response = JsonResponse(export_data, json_dumps_params={'indent': 2})
        response['Content-Disposition'] = f'attachment; filename="{config.name.replace(" ", "_")}_config.json"'
        
        return response

@method_decorator(csrf_exempt, name='dispatch')
class ReportConfigurationImportView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """Import report configuration from JSON"""
    
    def test_func(self):
        return self.request.user.has_perm('reports.manage_configurations')
    
    def post(self, request, *args, **kwargs):
        try:
            if 'config_file' not in request.FILES:
                return JsonResponse({
                    'success': False,
                    'error': 'No file uploaded'
                })
            
            config_file = request.FILES['config_file']
            
            # Read and parse JSON file
            import_data = json.loads(config_file.read().decode('utf-8'))
            
            # Validate required fields
            required_fields = ['name', 'report_type', 'base_model', 'tabs', 'filters', 'columns']
            for field in required_fields:
                if field not in import_data:
                    return JsonResponse({
                        'success': False,
                        'error': f'Missing required field in import: {field}'
                    })
            
            # Create new configuration
            config = ReportConfiguration(
                name=import_data['name'],
                description=import_data.get('description', ''),
                report_type=import_data['report_type'],
                base_model=import_data['base_model'],
                tabs=import_data['tabs'],
                filters=import_data['filters'],
                columns=import_data['columns'],
                default_settings=import_data.get('default_settings', {}),
                is_active=import_data.get('is_active', True),
                is_default=False,  # Imported configs should not be default
                created_by=request.user.username,
                updated_by=request.user.username
            )
            
            config.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Configuration imported successfully',
                'config_id': config.id
            })
            
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'Invalid JSON file'
            })
        except Exception as e:
            logger.error(f"Error importing configuration: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            })