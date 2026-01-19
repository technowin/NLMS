// static/js/config_form.js
class ReportConfigForm {
    constructor() {
        this.currentStep = 1;
        this.totalSteps = 6;
        
        // Configuration data
        this.config = {
            tabs: [],
            filters: {},
            columns: [],
            default_settings: {}
        };
        
        // Templates
        this.tabTemplate = _.template($('#tabTemplate').html());
        this.filterTemplate = _.template($('#filterTemplate').html());
        this.columnTemplate = _.template($('#columnTemplate').html());
        this.optionTemplate = _.template($('#optionTemplate').html());
        
        this.init();
    }
    
    init() {
        this.bindEvents();
        this.initCodeMirror();
        this.loadExistingData();
        this.updateStepIndicator();
    }
    
    bindEvents() {
        // Step navigation
        $('#nextStepBtn').click(() => this.nextStep());
        $('#prevStepBtn').click(() => this.prevStep());
        $('#cancelBtn').click(() => this.cancel());
        $('#saveConfigBtn').click(() => this.saveConfig());
        
        // Load model fields
        $('#loadModelFields').click(() => this.loadModelFields());
        
        // Tab management
        $('#addTabBtn, #addFirstTabBtn').click(() => this.showTabModal());
        $(document).on('click', '.edit-tab-btn', (e) => {
            const tabId = $(e.target).closest('.edit-tab-btn').data('tab-id');
            this.editTab(tabId);
        });
        $(document).on('click', '.remove-tab-btn', (e) => {
            const tabId = $(e.target).closest('.remove-tab-btn').data('tab-id');
            this.removeTab(tabId);
        });
        
        // Filter management
        $('#addFilterBtn, #addFirstFilterBtn').click(() => this.showFilterModal());
        $(document).on('click', '.edit-filter-btn', (e) => {
            const filterKey = $(e.target).closest('.edit-filter-btn').data('filter-key');
            this.editFilter(filterKey);
        });
        $(document).on('click', '.remove-filter-btn', (e) => {
            const filterKey = $(e.target).closest('.remove-filter-btn').data('filter-key');
            this.removeFilter(filterKey);
        });
        
        // Column management
        $('#addColumnBtn, #addFirstColumnBtn').click(() => this.showColumnModal());
        $(document).on('click', '.edit-column-btn', (e) => {
            const columnField = $(e.target).closest('.edit-column-btn').data('column-field');
            this.editColumn(columnField);
        });
        $(document).on('click', '.remove-column-btn', (e) => {
            const columnField = $(e.target).closest('.remove-column-btn').data('column-field');
            this.removeColumn(columnField);
        });
        
        // Modal events
        $('#saveTabBtn').click(() => this.saveTab());
        $('#saveFilterBtn').click(() => this.saveFilter());
        $('#saveColumnBtn').click(() => this.saveColumn());
        
        // Filter type change
        $('#filterType').change(() => this.updateFilterOptionsVisibility());
        
        // Add option button
        $('#addOptionBtn').click(() => this.addOption());
        $(document).on('click', '.remove-option-btn', (e) => {
            $(e.target).closest('.option-item').remove();
        });
        
        // Initialize sortable
        this.initSortable();
    }
    
    initCodeMirror() {
        // Initialize JSON editors
        this.advancedSettingsEditor = CodeMirror.fromTextArea(
            document.getElementById('advancedSettings'), {
                mode: 'javascript',
                theme: 'dracula',
                lineNumbers: true,
                matchBrackets: true,
                indentUnit: 2,
                tabSize: 2,
                lineWrapping: true
            }
        );
        
        this.configPreviewEditor = CodeMirror.fromTextArea(
            document.getElementById('configPreview'), {
                mode: 'javascript',
                theme: 'dracula',
                lineNumbers: true,
                matchBrackets: true,
                indentUnit: 2,
                tabSize: 2,
                lineWrapping: true,
                readOnly: true
            }
        );
    }
    
    initSortable() {
        // Make tabs sortable
        if ($('#tabsContainer').length) {
            new Sortable(document.getElementById('tabsContainer'), {
                animation: 150,
                ghostClass: 'sortable-ghost',
                handle: '.sortable-handle',
                onEnd: () => {
                    // Update tabs order in config
                    this.updateTabsOrder();
                }
            });
        }
        
        // Make columns sortable
        if ($('#columnsContainer').length) {
            new Sortable(document.getElementById('columnsContainer'), {
                animation: 150,
                ghostClass: 'sortable-ghost',
                handle: '.sortable-handle',
                onEnd: () => {
                    // Update columns order in config
                    this.updateColumnsOrder();
                }
            });
        }
    }
    
    loadExistingData() {
        const mode = $('#mode').val();
        
        if (mode === 'edit') {
            // Load existing configuration data
            const configData = JSON.parse($('#configData').text() || '{}');
            
            if (configData.tabs) {
                this.config.tabs = configData.tabs;
                this.renderTabs();
            }
            
            if (configData.filters) {
                this.config.filters = configData.filters;
                this.renderFilters();
            }
            
            if (configData.columns) {
                this.config.columns = configData.columns;
                this.renderColumns();
            }
            
            if (configData.default_settings) {
                this.config.default_settings = configData.default_settings;
                this.loadSettings();
            }
        }
    }
    
    loadSettings() {
        const settings = this.config.default_settings;
        
        if (settings.page_length) {
            $('#pageLength').val(settings.page_length);
        }
        
        if (settings.default_sort) {
            $('#defaultSortField').val(settings.default_sort.field || '');
            $('#defaultSortDirection').val(settings.default_sort.direction || 'desc');
        }
        
        if (settings.export_file_name) {
            $('#exportFileName').val(settings.export_file_name);
        }
        
        if (settings.features) {
            $('#enableSearch').prop('checked', settings.features.search !== false);
            $('#enableExport').prop('checked', settings.features.export !== false);
            $('#enablePrint').prop('checked', settings.features.print !== false);
        }
        
        if (settings.advanced) {
            this.advancedSettingsEditor.setValue(JSON.stringify(settings.advanced, null, 2));
        }
    }
    
    async loadModelFields() {
        const modelPath = $('#baseModel').val();
        
        if (!modelPath) {
            alert('Please select a base model first');
            return;
        }
        
        try {
            const response = await $.ajax({
                url: '{% url "reports:get_model_fields" %}',
                method: 'POST',
                contentType: 'application/json',
                data: JSON.stringify({ model_path: modelPath })
            });
            
            if (response.success) {
                this.displayModelFields(response);
            } else {
                alert('Error loading model fields: ' + response.error);
            }
        } catch (error) {
            alert('Error loading model fields');
            console.error(error);
        }
    }
    
    displayModelFields(data) {
        const $container = $('#modelFieldsPreview');
        $container.empty();
        
        // Add regular fields
        if (data.fields && data.fields.length > 0) {
            $container.append('<div class="mb-2"><strong>Fields:</strong></div>');
            data.fields.forEach(field => {
                $container.append(`
                    <div class="field-item">
                        <span class="field-name">${field.name}</span>
                        <span class="field-type badge bg-info ms-2">${field.type}</span>
                        <div class="field-help">${field.help_text || ''}</div>
                    </div>
                `);
            });
        }
        
        // Add related fields
        if (data.related_fields && data.related_fields.length > 0) {
            $container.append('<div class="mb-2 mt-3"><strong>Related Fields:</strong></div>');
            data.related_fields.forEach(field => {
                $container.append(`
                    <div class="field-item">
                        <span class="field-name">${field.name}</span>
                        <span class="field-type badge bg-warning ms-2">related</span>
                        <div class="field-help">${field.help_text || ''}</div>
                    </div>
                `);
            });
        }
        
        $('#modelFieldsContainer').show();
    }
    
    nextStep() {
        if (!this.validateCurrentStep()) {
            return;
        }
        
        if (this.currentStep < this.totalSteps) {
            this.currentStep++;
            this.updateStepUI();
            
            if (this.currentStep === this.totalSteps) {
                this.prepareReview();
            }
        }
    }
    
    prevStep() {
        if (this.currentStep > 1) {
            this.currentStep--;
            this.updateStepUI();
        }
    }
    
    validateCurrentStep() {
        switch (this.currentStep) {
            case 1:
                // Validate basic info
                if (!$('#configName').val()) {
                    alert('Please enter a configuration name');
                    $('#configName').focus();
                    return false;
                }
                if (!$('#reportType').val()) {
                    alert('Please select a report type');
                    $('#reportType').focus();
                    return false;
                }
                if (!$('#baseModel').val()) {
                    alert('Please select a base model');
                    $('#baseModel').focus();
                    return false;
                }
                return true;
                
            case 2:
                // Validate tabs
                if (this.config.tabs.length === 0) {
                    alert('Please add at least one tab');
                    return false;
                }
                return true;
                
            case 3:
                // Filters are optional
                return true;
                
            case 4:
                // Validate columns
                if (this.config.columns.length === 0) {
                    alert('Please add at least one column');
                    return false;
                }
                return true;
                
            case 5:
                // Settings are optional
                return true;
                
            default:
                return true;
        }
    }
    
    updateStepUI() {
        // Hide all steps
        $('.form-step').removeClass('active');
        
        // Show current step
        $(`#step${this.currentStep}`).addClass('active');
        
        // Update step indicator
        this.updateStepIndicator();
        
        // Update navigation buttons
        if (this.currentStep === 1) {
            $('#prevStepBtn').hide();
        } else {
            $('#prevStepBtn').show();
        }
        
        if (this.currentStep === this.totalSteps) {
            $('#nextStepBtn').hide();
            $('#saveConfigBtn').show();
        } else {
            $('#nextStepBtn').show();
            $('#saveConfigBtn').hide();
        }
    }
    
    updateStepIndicator() {
        $('.step').removeClass('active completed');
        
        $('.step').each((index, element) => {
            const stepNumber = parseInt($(element).data('step'));
            
            if (stepNumber < this.currentStep) {
                $(element).addClass('completed');
            } else if (stepNumber === this.currentStep) {
                $(element).addClass('active');
            }
        });
    }
    
    prepareReview() {
        // Update preview data
        $('#previewName').text($('#configName').val());
        $('#previewReportType').text($('#reportType option:selected').text());
        $('#previewBaseModel').text($('#baseModel').val());
        $('#previewStatus').text($('#isActive').is(':checked') ? 'Active' : 'Inactive');
        
        $('#previewTabsCount').text(this.config.tabs.length);
        $('#previewFiltersCount').text(Object.keys(this.config.filters).length);
        $('#previewColumnsCount').text(this.config.columns.length);
        
        const features = [];
        if ($('#enableSearch').is(':checked')) features.push('Search');
        if ($('#enableExport').is(':checked')) features.push('Export');
        if ($('#enablePrint').is(':checked')) features.push('Print');
        $('#previewFeatures').text(features.join(', '));
        
        // Prepare full configuration
        const fullConfig = {
            name: $('#configName').val(),
            description: $('#configDescription').val(),
            report_type: $('#reportType').val(),
            base_model: $('#baseModel').val(),
            tabs: this.config.tabs,
            filters: this.config.filters,
            columns: this.config.columns,
            default_settings: this.getSettings(),
            is_active: $('#isActive').is(':checked'),
            is_default: $('#isDefault').is(':checked')
        };
        
        // Update JSON preview
        this.configPreviewEditor.setValue(JSON.stringify(fullConfig, null, 2));
    }
    
    getSettings() {
        let advancedSettings;
        try {
            advancedSettings = JSON.parse(this.advancedSettingsEditor.getValue());
        } catch {
            advancedSettings = {};
        }
        
        return {
            page_length: parseInt($('#pageLength').val()),
            default_sort: {
                field: $('#defaultSortField').val(),
                direction: $('#defaultSortDirection').val()
            },
            export_file_name: $('#exportFileName').val(),
            features: {
                search: $('#enableSearch').is(':checked'),
                export: $('#enableExport').is(':checked'),
                print: $('#enablePrint').is(':checked')
            },
            advanced: advancedSettings
        };
    }
    
    async saveConfig() {
        // Validate all data
        if (!this.validateCurrentStep()) {
            return;
        }
        
        // Prepare data
        const configData = {
            mode: $('#mode').val(),
            name: $('#configName').val(),
            description: $('#configDescription').val(),
            report_type: $('#reportType').val(),
            base_model: $('#baseModel').val(),
            tabs: this.config.tabs,
            filters: this.config.filters,
            columns: this.config.columns,
            default_settings: this.getSettings(),
            is_active: $('#isActive').is(':checked'),
            is_default: $('#isDefault').is(':checked')
        };
        
        if ($('#mode').val() === 'edit') {
            configData.id = $('#configId').val();
        }
        
        // Show loading
        const $saveBtn = $('#saveConfigBtn');
        const originalText = $saveBtn.html();
        $saveBtn.html('<span class="spinner-border spinner-border-sm" role="status"></span> Saving...');
        $saveBtn.prop('disabled', true);
        
        try {
            const response = await $.ajax({
                url: '{% url "reports:config_save" %}',
                method: 'POST',
                contentType: 'application/json',
                data: JSON.stringify(configData)
            });
            
            if (response.success) {
                alert('Configuration saved successfully!');
                window.location.href = '{% url "reports:config_edit" 0 %}'.replace('0', response.config_id);
            } else {
                alert('Error saving configuration: ' + response.error);
                $saveBtn.html(originalText).prop('disabled', false);
            }
        } catch (error) {
            alert('Error saving configuration');
            console.error(error);
            $saveBtn.html(originalText).prop('disabled', false);
        }
    }
    
    cancel() {
        if (confirm('Are you sure you want to cancel? Unsaved changes will be lost.')) {
            window.location.href = '{% url "reports:config_list" %}';
        }
    }
    
    // Tab Management
    showTabModal(tab = null) {
        $('#tabForm')[0].reset();
        
        if (tab) {
            // Editing existing tab
            $('#tabId').val(tab.id);
            $('#tabIdInput').val(tab.id).prop('readonly', true);
            $('#tabTitle').val(tab.title);
            $('#tabIcon').val(tab.icon || 'bi-table');
            $('#tabDescription').val(tab.description || '');
            $('#tabHasDocuments').prop('checked', tab.has_documents || false);
            $('#tabExportable').prop('checked', tab.exportable !== false);
            $('#tabSortField').val(tab.default_sort?.field || '');
            $('#tabSortDirection').val(tab.default_sort?.direction || 'desc');
            
            // Load filters
            this.loadTabFilters(tab.filters || []);
        } else {
            // Creating new tab
            $('#tabId').val('');
            $('#tabIdInput').val('').prop('readonly', false);
            $('#tabIdInput').val('tab_' + Date.now());
        }
        
        $('#tabModal').modal('show');
    }
    
    loadTabFilters(selectedFilters) {
        const $select = $('#tabFilters');
        $select.empty();
        
        Object.keys(this.config.filters).forEach(filterKey => {
            const filter = this.config.filters[filterKey];
            const selected = selectedFilters.includes(filterKey);
            
            $select.append(`
                <option value="${filterKey}" ${selected ? 'selected' : ''}>
                    ${filter.label} (${filterKey})
                </option>
            `);
        });
    }
    
    saveTab() {
        const tabData = {
            id: $('#tabIdInput').val(),
            title: $('#tabTitle').val(),
            icon: $('#tabIcon').val(),
            description: $('#tabDescription').val(),
            has_documents: $('#tabHasDocuments').is(':checked'),
            exportable: $('#tabExportable').is(':checked'),
            filters: $('#tabFilters').val() || [],
            default_sort: {
                field: $('#tabSortField').val(),
                direction: $('#tabSortDirection').val()
            }
        };
        
        // Validate
        if (!tabData.id || !tabData.title) {
            alert('Please fill in all required fields');
            return;
        }
        
        // Check for duplicate ID
        const existingIndex = this.config.tabs.findIndex(t => t.id === tabData.id);
        
        if (existingIndex >= 0 && !$('#tabId').val()) {
            // Editing
            this.config.tabs[existingIndex] = tabData;
        } else {
            // Adding new or editing with different ID
            if (existingIndex >= 0) {
                alert('A tab with this ID already exists');
                return;
            }
            this.config.tabs.push(tabData);
        }
        
        this.renderTabs();
        $('#tabModal').modal('hide');
    }
    
    editTab(tabId) {
        const tab = this.config.tabs.find(t => t.id === tabId);
        if (tab) {
            this.showTabModal(tab);
        }
    }
    
    removeTab(tabId) {
        if (confirm('Are you sure you want to remove this tab?')) {
            this.config.tabs = this.config.tabs.filter(t => t.id !== tabId);
            this.renderTabs();
        }
    }
    
    renderTabs() {
        const $container = $('#tabsContainer');
        
        if (this.config.tabs.length === 0) {
            $container.html($('#noTabsMessage').html());
            return;
        }
        
        $container.empty();
        this.config.tabs.forEach(tab => {
            $container.append(this.tabTemplate(tab));
        });
    }
    
    updateTabsOrder() {
        const tabIds = $('#tabsContainer').children().map(function() {
            return $(this).data('tab-id');
        }).get();
        
        // Reorder tabs array based on DOM order
        this.config.tabs.sort((a, b) => {
            return tabIds.indexOf(a.id) - tabIds.indexOf(b.id);
        });
    }
    
    // Filter Management
    showFilterModal(filterKey = null) {
        $('#filterForm')[0].reset();
        $('#filterOptionsContainer').empty();
        $('#filterOptionsSection').hide();
        
        if (filterKey && this.config.filters[filterKey]) {
            // Editing existing filter
            const filter = this.config.filters[filterKey];
            $('#filterKey').val(filterKey);
            $('#filterKeyInput').val(filterKey).prop('readonly', true);
            $('#filterLabel').val(filter.label);
            $('#filterType').val(filter.type);
            $('#filterField').val(filter.field);
            $('#filterPlaceholder').val(filter.placeholder || '');
            $('#filterDescription').val(filter.description || '');
            $('#filterMultiple').prop('checked', filter.multiple || false);
            $('#filterSearchable').prop('checked', filter.searchable || false);
            
            // Load options
            if (filter.options && Array.isArray(filter.options)) {
                filter.options.forEach(option => {
                    this.addOption(option.value, option.label);
                });
                this.updateFilterOptionsVisibility();
            }
        } else {
            // Creating new filter
            $('#filterKey').val('');
            $('#filterKeyInput').val('').prop('readonly', false);
            $('#filterKeyInput').val('filter_' + Date.now());
        }
        
        this.updateFilterOptionsVisibility();
        $('#filterModal').modal('show');
    }
    
    updateFilterOptionsVisibility() {
        const filterType = $('#filterType').val();
        const showOptions = ['select', 'multi_select', 'radio'].includes(filterType);
        
        if (showOptions) {
            $('#filterOptionsSection').show();
        } else {
            $('#filterOptionsSection').hide();
        }
    }
    
    addOption(value = '', label = '') {
        const $container = $('#filterOptionsContainer');
        $container.append(this.optionTemplate());
        
        const $lastOption = $container.find('.option-item').last();
        $lastOption.find('.option-value').val(value);
        $lastOption.find('.option-label').val(label);
    }
    
    saveFilter() {
        const filterKey = $('#filterKeyInput').val();
        const filterData = {
            label: $('#filterLabel').val(),
            type: $('#filterType').val(),
            field: $('#filterField').val(),
            placeholder: $('#filterPlaceholder').val(),
            description: $('#filterDescription').val(),
            multiple: $('#filterMultiple').is(':checked'),
            searchable: $('#filterSearchable').is(':checked')
        };
        
        // Validate
        if (!filterKey || !filterData.label || !filterData.type || !filterData.field) {
            alert('Please fill in all required fields');
            return;
        }
        
        // Collect options
        if (['select', 'multi_select', 'radio'].includes(filterData.type)) {
            const options = [];
            $('.option-item').each(function() {
                const value = $(this).find('.option-value').val();
                const label = $(this).find('.option-label').val();
                
                if (value && label) {
                    options.push({ value, label });
                }
            });
            
            if (options.length > 0) {
                filterData.options = options;
            }
        }
        
        // Save filter
        this.config.filters[filterKey] = filterData;
        
        this.renderFilters();
        $('#filterModal').modal('hide');
    }
    
    editFilter(filterKey) {
        this.showFilterModal(filterKey);
    }
    
    removeFilter(filterKey) {
        if (confirm('Are you sure you want to remove this filter?')) {
            delete this.config.filters[filterKey];
            
            // Remove filter from all tabs
            this.config.tabs.forEach(tab => {
                if (tab.filters) {
                    tab.filters = tab.filters.filter(f => f !== filterKey);
                }
            });
            
            this.renderFilters();
        }
    }
    
    renderFilters() {
        const $container = $('#filtersContainer');
        
        if (Object.keys(this.config.filters).length === 0) {
            $container.html($('#noFiltersMessage').html());
            return;
        }
        
        $container.empty();
        Object.entries(this.config.filters).forEach(([key, filter]) => {
            $container.append(this.filterTemplate({ ...filter, key }));
        });
    }
    
    // Column Management
    showColumnModal(field = null) {
        $('#columnForm')[0].reset();
        
        if (field && this.config.columns.find(c => c.data === field)) {
            // Editing existing column
            const column = this.config.columns.find(c => c.data === field);
            $('#columnField').val(field);
            $('#columnFieldInput').val(field).prop('readonly', true);
            $('#columnTitle').val(column.title);
            $('#columnClass').val(column.className || '');
            $('#columnDefault').val(column.default || '');
            $('#columnRender').val(column.render || 'text');
            $('#columnDescription').val(column.description || '');
            $('#columnOrderable').prop('checked', column.orderable !== false);
            $('#columnSearchable').prop('checked', column.searchable !== false);
            $('#columnVisible').prop('checked', column.visible !== false);
            $('#columnExportable').prop('checked', column.exportable !== false);
            $('#columnRenderFunction').val(column.render || '');
        } else {
            // Creating new column
            $('#columnField').val('');
            $('#columnFieldInput').val('').prop('readonly', false);
        }
        
        $('#columnModal').modal('show');
    }
    
    saveColumn() {
        const field = $('#columnFieldInput').val();
        const columnData = {
            data: field,
            title: $('#columnTitle').val(),
            className: $('#columnClass').val() || undefined,
            default: $('#columnDefault').val() || undefined,
            render: $('#columnRender').val() !== 'text' ? $('#columnRender').val() : undefined,
            description: $('#columnDescription').val(),
            orderable: $('#columnOrderable').is(':checked'),
            searchable: $('#columnSearchable').is(':checked'),
            visible: $('#columnVisible').is(':checked'),
            exportable: $('#columnExportable').is(':checked')
        };
        
        // Validate
        if (!field || !columnData.title) {
            alert('Please fill in all required fields');
            return;
        }
        
        // Custom render function
        const renderFunction = $('#columnRenderFunction').val().trim();
        if (renderFunction && renderFunction !== 'function(data, type, row) { return data; }') {
            columnData.render = renderFunction;
        }
        
        // Check for duplicate field
        const existingIndex = this.config.columns.findIndex(c => c.data === field);
        
        if (existingIndex >= 0 && !$('#columnField').val()) {
            // Editing
            this.config.columns[existingIndex] = columnData;
        } else {
            // Adding new or editing with different field
            if (existingIndex >= 0) {
                alert('A column with this field already exists');
                return;
            }
            this.config.columns.push(columnData);
        }
        
        this.renderColumns();
        $('#columnModal').modal('hide');
    }
    
    editColumn(field) {
        this.showColumnModal(field);
    }
    
    removeColumn(field) {
        if (confirm('Are you sure you want to remove this column?')) {
            this.config.columns = this.config.columns.filter(c => c.data !== field);
            this.renderColumns();
        }
    }
    
    renderColumns() {
        const $container = $('#columnsContainer');
        
        if (this.config.columns.length === 0) {
            $container.html($('#noColumnsMessage').html());
            return;
        }
        
        $container.empty();
        this.config.columns.forEach(column => {
            $container.append(this.columnTemplate(column));
        });
    }
    
    updateColumnsOrder() {
        const columnFields = $('#columnsContainer').children().map(function() {
            return $(this).data('column-field');
        }).get();
        
        // Reorder columns array based on DOM order
        this.config.columns.sort((a, b) => {
            return columnFields.indexOf(a.data) - columnFields.indexOf(b.data);
        });
    }
}

// Initialize the form when document is ready
$(document).ready(function() {
    window.configForm = new ReportConfigForm();
});