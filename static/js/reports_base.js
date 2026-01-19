
// static/js/reports_base.js
// Base JavaScript for all reports

class ReportBase {
    constructor() {
        this.selectedItems = new Set();
        this.activeFilters = {};
        this.tabFilters = {};
        this.currentTab = null;
        this.dataTables = {};
        this.initialized = false;
        
        this.init();
    }
    
    init() {
        this.bindGlobalEvents();
        this.initSelect2();
        this.initTooltips();
        this.updateLastUpdated();
        this.hideLoading();
    }
    
    bindGlobalEvents() {
        // Theme toggle
        $('[data-bs-theme-value]').on('click', (e) => {
            const theme = $(e.target).closest('[data-bs-theme-value]').data('bs-theme-value');
            this.setTheme(theme);
        });
        
        // Library selector
        $('[data-library]').on('click', (e) => {
            const library = $(e.target).data('library');
            this.changeLibrary(library);
        });
        
        // Left panel toggle
        $('#toggleLeftPanel').on('click', () => this.toggleLeftPanel());
        
        // Refresh report
        $('#refreshReport').on('click', () => this.refreshReport());
        
        // Global filter modal
        $('#globalFilterBtn').on('click', () => this.showGlobalFilters());
        $('#applyGlobalFilters').on('click', () => this.applyGlobalFilters());
        $('#clearGlobalFilters').on('click', () => this.clearGlobalFilters());
        $('.preset-date').on('click', (e) => this.applyDatePreset(e));
        
        // Export
        $('#exportAllBtn').on('click', () => this.showExportModal());
        $('#startExport').on('click', () => this.startExport());
        $('#exportType').on('change', () => this.updateExportPreview());
        $('#exportScope').on('change', () => this.updateExportPreview());
        
        // Tab events
        $('.report-tab').on('shown.bs.tab', (e) => this.onTabChange(e));
        $('.tab-filter-btn').on('click', (e) => this.showTabFilters(e));
        $('.tab-export-btn').on('click', (e) => this.exportTab(e));
        $('.reload-tab-btn').on('click', (e) => this.reloadTab(e));
        $('.view-documents-btn').on('click', (e) => this.viewDocuments(e));
        
        // Document viewer
        $('#retryLoadDocuments').on('click', () => this.loadDocuments());
        $('#downloadAllDocuments').on('click', () => this.downloadAllDocuments());
        
        // Keyboard shortcuts
        $(document).on('keydown', (e) => this.handleKeyboardShortcuts(e));
        
        // Window resize
        $(window).on('resize', _.debounce(() => this.handleResize(), 300));
    }
    
    initSelect2() {
        $('.filter-select').select2({
            theme: 'bootstrap-5',
            width: '100%',
            placeholder: function() {
                return $(this).data('placeholder');
            },
            allowClear: true,
            closeOnSelect: false
        });
    }
    
    initTooltips() {
        const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
        [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl));
    }
    
    setTheme(theme) {
        if (theme === 'auto') {
            localStorage.removeItem('theme');
            document.documentElement.removeAttribute('data-bs-theme');
        } else {
            localStorage.setItem('theme', theme);
            document.documentElement.setAttribute('data-bs-theme', theme);
        }
        
        this.showToast(`Theme changed to ${theme}`, 'info');
    }
    
    changeLibrary(library) {
        if (!library || library === REPORT_CONFIG.library) return;
        
        this.showLoading('Changing library...');
        
        // Update session via AJAX
        $.ajax({
            url: '/api/change-library/',
            method: 'POST',
            data: { library: library },
            success: (response) => {
                if (response.success) {
                    location.reload();
                } else {
                    this.showToast('Failed to change library', 'danger');
                    this.hideLoading();
                }
            },
            error: () => {
                this.showToast('Error changing library', 'danger');
                this.hideLoading();
            }
        });
    }
    
    toggleLeftPanel() {
        const $leftPanel = $('.left-panel-wrapper');
        const $toggleBtn = $('#toggleLeftPanel i');
        
        if ($leftPanel.width() > 0) {
            $leftPanel.width(0);
            $toggleBtn.removeClass('bi-chevron-left').addClass('bi-chevron-right');
            localStorage.setItem('leftPanelCollapsed', 'true');
        } else {
            $leftPanel.width('var(--left-panel-width)');
            $toggleBtn.removeClass('bi-chevron-right').addClass('bi-chevron-left');
            localStorage.setItem('leftPanelCollapsed', 'false');
        }
    }
    
    refreshReport() {
        this.showLoading('Refreshing report...');
        
        // Clear all data
        this.selectedItems.clear();
        this.activeFilters = {};
        this.tabFilters = {};
        this.dataTables = {};
        
        // Reset UI
        this.resetUI();
        
        // Reload initial data
        setTimeout(() => {
            this.hideLoading();
            this.showToast('Report refreshed', 'success');
        }, 500);
    }
    
    resetUI() {
        // Reset left panel
        $('.filter-select').val(null).trigger('change');
        $('#memberSearch').val('');
        $('#activeFilters').empty().append('<div class="text-muted small">No filters applied</div>');
        $('#memberCount').text('0');
        $('#selectedCount').text('0');
        $('#totalFilteredCount').text('0');
        $('#exportSelected').prop('disabled', true);
        
        // Reset tabs
        $('.tab-content-container').each(function() {
            $(this).html(`
                <div class="empty-state text-center py-5">
                    <div class="empty-state-icon mb-3">
                        <i class="bi bi-table display-1 text-muted"></i>
                    </div>
                    <h5 class="empty-state-title">No Data Loaded</h5>
                    <p class="empty-state-description text-muted mb-4">
                        Select items from the left panel to load data.
                    </p>
                </div>
            `);
        });
        
        // Reset filter badges
        $('.filter-count-badge').addClass('d-none');
        
        // Reset report subtitle
        $('#reportSubtitle').text('Select items from the left panel to view data');
    }
    
    showGlobalFilters() {
        $('#globalFilterModal').modal('show');
    }
    
    applyGlobalFilters() {
        const formData = $('#globalFilterForm').serializeArray();
        const filters = {};
        
        formData.forEach(item => {
            if (item.value) {
                if (!filters[item.name]) {
                    filters[item.name] = [];
                }
                if (Array.isArray(item.value)) {
                    filters[item.name].push(...item.value);
                } else {
                    filters[item.name].push(item.value);
                }
            }
        });
        
        // Convert arrays to strings for single values
        Object.keys(filters).forEach(key => {
            if (filters[key].length === 1) {
                filters[key] = filters[key][0];
            }
        });
        
        this.activeFilters = { ...this.activeFilters, ...filters };
        this.updateActiveFiltersDisplay();
        $('#globalFilterModal').modal('hide');
        
        this.showToast('Global filters applied', 'success');
        this.loadData();
    }
    
    clearGlobalFilters() {
        $('#globalFilterForm')[0].reset();
        $('.filter-select').val(null).trigger('change');
    }
    
    applyDatePreset(e) {
        const days = parseInt($(e.target).data('days'));
        const today = new Date();
        const targetDate = new Date(today);
        targetDate.setDate(today.getDate() + days);
        
        $('#globalFromDate').val(targetDate.toISOString().split('T')[0]);
        $('#globalToDate').val(today.toISOString().split('T')[0]);
    }
    
    showExportModal() {
        this.updateExportPreview();
        $('#exportModal').modal('show');
    }
    
    updateExportPreview() {
        const exportType = $('#exportType').val();
        const exportScope = $('#exportScope').val();
        const fileName = $('#exportFileName').val();
        
        // Update file extension
        const extensions = {
            'excel': '.xlsx',
            'csv': '.csv',
            'pdf': '.pdf'
        };
        const extension = extensions[exportType] || '.xlsx';
        $('#fileExtension').text(extension);
        
        // Update preview file name
        $('#previewFileName').text(fileName + extension);
        
        // Show/hide tabs selection
        if (exportScope === 'selected_tabs') {
            $('#tabsSelectionSection').show();
        } else {
            $('#tabsSelectionSection').hide();
        }
        
        // Update tabs preview
        let tabsText = '';
        if (exportScope === 'current_tab') {
            tabsText = this.currentTab ? this.currentTab.replace('_', ' ').title() : 'Current tab';
        } else if (exportScope === 'all_tabs') {
            tabsText = 'All tabs';
        } else {
            const selectedTabs = $('.export-tab-check:checked').map(function() {
                return $(this).val().replace('_', ' ').title();
            }).get().join(', ');
            tabsText = selectedTabs || 'No tabs selected';
        }
        $('#previewTabs').text(tabsText);
    }
    
    async startExport() {
        const exportType = $('#exportType').val();
        const exportScope = $('#exportScope').val();
        const fileName = $('#exportFileName').val();
        const compression = $('#exportCompression').val();
        const includeCharts = $('#includeCharts').is(':checked');
        
        let selectedTabs = [];
        if (exportScope === 'current_tab' && this.currentTab) {
            selectedTabs = [this.currentTab];
        } else if (exportScope === 'all_tabs') {
            selectedTabs = REPORT_CONFIG.tabs.map(tab => tab.id);
        } else if (exportScope === 'selected_tabs') {
            selectedTabs = $('.export-tab-check:checked').map(function() {
                return $(this).val();
            }).get();
        }
        
        if (selectedTabs.length === 0) {
            this.showToast('Please select at least one tab to export', 'warning');
            return;
        }
        
        const exportData = {
            report_type: REPORT_CONFIG.type,
            export_type: exportType,
            format: exportType === 'excel' ? 'xlsx' : 'csv',
            filters: this.activeFilters,
            tabs: selectedTabs,
            selected_ids: Array.from(this.selectedItems),
            include_charts: includeCharts,
            compression: compression === 'zip',
            file_name: fileName
        };
        
        // Advanced options
        exportData.advanced = {
            include_filters: $('#includeFilters').is(':checked'),
            include_summary: $('#includeSummary').is(':checked'),
            format_numbers: $('#formatNumbers').is(':checked'),
            auto_size_columns: $('#autoSizeColumns').is(':checked'),
            protect_sheets: $('#protectSheets').is(':checked'),
            date_format: $('select[name="date_format"]').val(),
            number_format: $('select[name="number_format"]').val()
        };
        
        try {
            this.showLoading('Preparing export...');
            
            const response = await fetch(REPORT_CONFIG.apiUrls.export, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrftoken
                },
                body: JSON.stringify(exportData)
            });
            
            if (response.ok) {
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = response.headers.get('Content-Disposition')?.split('filename=')[1]?.replace(/"/g, '') || 
                             `${fileName}_export.${exportType === 'excel' ? 'xlsx' : exportType}`;
                document.body.appendChild(a);
                a.click();
                a.remove();
                window.URL.revokeObjectURL(url);
                
                this.showToast('Export completed successfully', 'success');
                $('#exportModal').modal('hide');
            } else {
                const error = await response.json();
                throw new Error(error.error || 'Export failed');
            }
        } catch (error) {
            this.showToast(`Export failed: ${error.message}`, 'danger');
        } finally {
            this.hideLoading();
        }
    }
    
    onTabChange(e) {
        const tabId = $(e.target).data('tab-id');
        this.currentTab = tabId;
        
        // Update document button visibility
        const tabConfig = REPORT_CONFIG.tabs.find(t => t.id === tabId);
        if (tabConfig && tabConfig.has_documents) {
            $(`.view-documents-btn[data-tab="${tabId}"]`).show();
        } else {
            $(`.view-documents-btn[data-tab="${tabId}"]`).hide();
        }
        
        // Load tab data if not already loaded
        if (this.selectedItems.size > 0 && !this.dataTables[tabId]) {
            this.loadTabData(tabId);
        }
    }
    
    async showTabFilters(e) {
        const tabId = $(e.target).closest('.tab-filter-btn').data('tab');
        const tabConfig = REPORT_CONFIG.tabs.find(t => t.id === tabId);
        
        if (!tabConfig) return;
        
        $('#tabFilterModalTitle').html(`<i class="bi bi-funnel me-1"></i> ${tabConfig.title} Filters`);
        $('#tabFilterModal').data('current-tab', tabId);
        
        // Build filter form
        let formHtml = '<div class="row">';
        tabConfig.filters.forEach((filterKey, index) => {
            const filterConfig = REPORT_CONFIG.filters[filterKey];
            if (filterConfig) {
                formHtml += `
                    <div class="col-md-${index % 2 === 0 ? '6' : '6'} mb-3">
                        ${this.getFilterFieldHtml(filterKey, filterConfig)}
                    </div>
                `;
            }
        });
        formHtml += '</div>';
        
        $('#tabFilterForm').html(formHtml);
        
        // Initialize Select2
        $('#tabFilterForm .filter-select').select2({
            theme: 'bootstrap-5',
            width: '100%'
        });
        
        // Load existing filters
        const existingFilters = this.tabFilters[tabId] || {};
        Object.entries(existingFilters).forEach(([key, value]) => {
            const $field = $(`#tabFilterForm [name="${key}"]`);
            if ($field.length) {
                if ($field.is('select[multiple]')) {
                    $field.val(value).trigger('change');
                } else {
                    $field.val(value);
                }
            }
        });
        
        $('#tabFilterModal').modal('show');
    }
    
    getFilterFieldHtml(filterKey, config) {
        let html = `<label class="form-label small fw-semibold">${config.label}</label>`;
        
        switch (config.type) {
            case 'multi_select':
                html += `
                    <select class="form-select form-select-sm filter-select" 
                            name="${filterKey}" 
                            multiple
                            data-placeholder="Select ${config.label.toLowerCase()}">
                        ${config.options ? config.options.map(opt => 
                            `<option value="${opt.value}">${opt.label}</option>`
                        ).join('') : ''}
                    </select>
                `;
                break;
                
            case 'date_range':
                html += `
                    <div class="input-group input-group-sm">
                        <input type="date" class="form-control" name="${filterKey}_from" 
                               placeholder="From date">
                        <span class="input-group-text">to</span>
                        <input type="date" class="form-control" name="${filterKey}_to" 
                               placeholder="To date">
                    </div>
                `;
                break;
                
            case 'select':
                html += `
                    <select class="form-select form-select-sm" name="${filterKey}">
                        ${config.options.map(opt => 
                            `<option value="${opt.value}">${opt.label}</option>`
                        ).join('')}
                    </select>
                `;
                break;
                
            default:
                html += `
                    <input type="text" class="form-control form-control-sm" 
                           name="${filterKey}" 
                           placeholder="Enter ${config.label.toLowerCase()}">
                `;
        }
        
        return html;
    }
    
    applyTabFilters() {
        const tabId = $('#tabFilterModal').data('current-tab');
        const formData = $('#tabFilterForm').serializeArray();
        const filters = {};
        
        formData.forEach(item => {
            if (item.value) {
                // Handle date range
                if (item.name.endsWith('_from') || item.name.endsWith('_to')) {
                    const baseName = item.name.replace(/_from$|_to$/, '');
                    if (!filters[baseName]) filters[baseName] = {};
                    filters[baseName][item.name.endsWith('_from') ? 'from' : 'to'] = item.value;
                } else {
                    if (!filters[item.name]) filters[item.name] = [];
                    if (Array.isArray(item.value)) {
                        filters[item.name].push(...item.value);
                    } else {
                        filters[item.name].push(item.value);
                    }
                }
            }
        });
        
        // Convert single-item arrays to strings
        Object.keys(filters).forEach(key => {
            if (Array.isArray(filters[key]) && filters[key].length === 1) {
                filters[key] = filters[key][0];
            }
        });
        
        this.tabFilters[tabId] = filters;
        $('#tabFilterModal').modal('hide');
        
        // Update filter badge
        const filterCount = Object.keys(filters).length;
        $(`[data-tab="${tabId}"] .filter-count-badge`)
            .text(filterCount)
            .toggleClass('d-none', filterCount === 0);
        
        // Reload tab data
        this.loadTabData(tabId);
        
        this.showToast('Tab filters applied', 'success');
    }
    
    clearTabFilters() {
        const tabId = $('#tabFilterModal').data('current-tab');
        delete this.tabFilters[tabId];
        $('#tabFilterForm')[0].reset();
        $('#tabFilterForm select').val(null).trigger('change');
        
        $(`[data-tab="${tabId}"] .filter-count-badge`)
            .text('0')
            .addClass('d-none');
    }
    
    async exportTab(e) {
        const tabId = $(e.target).closest('.tab-export-btn').data('tab');
        const tabConfig = REPORT_CONFIG.tabs.find(t => t.id === tabId);
        
        if (!tabConfig) return;
        
        try {
            this.showLoading(`Exporting ${tabConfig.title}...`);
            
            const exportData = {
                report_type: REPORT_CONFIG.type,
                export_type: 'excel',
                tabs: [tabId],
                filters: this.activeFilters,
                selected_ids: Array.from(this.selectedItems),
                file_name: `${REPORT_CONFIG.type}_${tabId}_${new Date().toISOString().slice(0, 10)}`
            };
            
            const response = await fetch(REPORT_CONFIG.apiUrls.export, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrftoken
                },
                body: JSON.stringify(exportData)
            });
            
            if (response.ok) {
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `${tabConfig.title}_export.xlsx`;
                document.body.appendChild(a);
                a.click();
                a.remove();
                window.URL.revokeObjectURL(url);
                
                this.showToast(`${tabConfig.title} exported successfully`, 'success');
            } else {
                const error = await response.json();
                throw new Error(error.error || 'Export failed');
            }
        } catch (error) {
            this.showToast(`Export failed: ${error.message}`, 'danger');
        } finally {
            this.hideLoading();
        }
    }
    
    async reloadTab(e) {
        const tabId = $(e.target).closest('.reload-tab-btn').data('tab');
        
        if (this.dataTables[tabId]) {
            this.dataTables[tabId].destroy();
            delete this.dataTables[tabId];
        }
        
        if (this.selectedItems.size > 0) {
            this.loadTabData(tabId);
        } else {
            $(`#content-${tabId}`).html(`
                <div class="empty-state text-center py-5">
                    <div class="empty-state-icon mb-3">
                        <i class="bi bi-table display-1 text-muted"></i>
                    </div>
                    <h5 class="empty-state-title">No Data Loaded</h5>
                    <p class="empty-state-description text-muted mb-4">
                        Select items from the left panel to load data.
                    </p>
                </div>
            `);
        }
        
        this.showToast('Tab reloaded', 'info');
    }
    
    async loadTabData(tabId) {
        if (this.selectedItems.size === 0) return;
        
        const $container = $(`#content-${tabId}`);
        $container.html(`
            <div class="text-center py-5">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
                <p class="mt-3">Loading ${tabId.replace('_', ' ')} data...</p>
            </div>
        `);
        
        try {
            const response = await $.ajax({
                url: REPORT_CONFIG.apiUrls.data,
                method: 'POST',
                contentType: 'application/json',
                data: JSON.stringify({
                    report_type: REPORT_CONFIG.type,
                    tab: tabId,
                    filters: { ...this.activeFilters, ...(this.tabFilters[tabId] || {}) },
                    selected_ids: Array.from(this.selectedItems),
                    draw: 1,
                    start: 0,
                    length: 25
                })
            });
            
            if (response.success) {
                this.renderTabData(tabId, response);
            } else {
                throw new Error(response.error);
            }
        } catch (error) {
            $container.html(`
                <div class="alert alert-danger">
                    <i class="bi bi-exclamation-triangle me-2"></i>
                    Error loading data: ${error.message}
                    <button class="btn btn-sm btn-outline-primary ms-2 reload-tab-btn" data-tab="${tabId}">
                        <i class="bi bi-arrow-clockwise"></i> Retry
                    </button>
                </div>
            `);
        }
    }
    
    renderTabData(tabId, response) {
        const $container = $(`#content-${tabId}`);
        
        if (response.data.length === 0) {
            $container.html(`
                <div class="empty-state text-center py-5">
                    <div class="empty-state-icon mb-3">
                        <i class="bi bi-table display-1 text-muted"></i>
                    </div>
                    <h5 class="empty-state-title">No Data Found</h5>
                    <p class="empty-state-description text-muted">
                        No records found for the selected criteria.
                    </p>
                </div>
            `);
            return;
        }
        
        // Create table
        const tableId = `table-${tabId}`;
        $container.html(`
            <div class="table-responsive">
                <table class="table table-sm table-hover table-striped" id="${tableId}" width="100%">
                    <thead></thead>
                    <tbody></tbody>
                </table>
            </div>
        `);
        
        // Prepare DataTable columns
        const columns = response.columns.map(col => ({
            data: col.data,
            title: col.title,
            className: col.className || '',
            render: col.render ? $.fn.dataTable.render.text() : undefined,
            orderable: col.orderable !== false,
            searchable: col.searchable !== false
        }));
        
        // Initialize DataTable
        this.dataTables[tabId] = $(`#${tableId}`).DataTable({
            data: response.data,
            columns: columns,
            pageLength: 25,
            responsive: true,
            dom: '<"top"lfB>rt<"bottom"ip>',
            buttons: [
                {
                    extend: 'excel',
                    text: '<i class="bi bi-file-earmark-excel"></i> Excel',
                    className: 'btn btn-sm btn-outline-success',
                    title: `${REPORT_CONFIG.title} - ${tabId.replace('_', ' ').title()}`,
                    exportOptions: {
                        columns: ':visible'
                    }
                },
                {
                    extend: 'print',
                    text: '<i class="bi bi-printer"></i> Print',
                    className: 'btn btn-sm btn-outline-secondary',
                    exportOptions: {
                        columns: ':visible'
                    }
                }
            ],
            language: {
                search: '_INPUT_',
                searchPlaceholder: 'Search...',
                lengthMenu: '_MENU_ records per page',
                info: 'Showing _START_ to _END_ of _TOTAL_ records',
                infoEmpty: 'Showing 0 to 0 of 0 records',
                infoFiltered: '(filtered from _MAX_ total records)'
            }
        });
        
        // Update report subtitle
        $('#reportSubtitle').text(`${response.recordsFiltered} records found`);
    }
    
    async viewDocuments(e) {
        const tabId = $(e.target).closest('.view-documents-btn').data('tab');
        
        // For now, show first selected member's documents
        if (this.selectedItems.size === 0) {
            this.showToast('Please select at least one member', 'warning');
            return;
        }
        
        const firstMemberId = Array.from(this.selectedItems)[0];
        $('#documentViewerModal').data('member-id', firstMemberId);
        $('#documentViewerModal').modal('show');
        
        this.loadDocuments();
    }
    
    async loadDocuments() {
        const memberId = $('#documentViewerModal').data('member-id');
        
        $('#documentLoading').show();
        $('#documentList').hide();
        $('#noDocuments').hide();
        $('#documentError').hide();
        
        try {
            const response = await $.ajax({
                url: REPORT_CONFIG.apiUrls.documents,
                method: 'GET',
                data: { member_id: memberId }
            });
            
            if (response.success) {
                if (response.documents.length > 0) {
                    this.renderDocuments(response.documents);
                    $('#documentCount').text(`${response.documents.length} document(s)`);
                    $('#downloadAllDocuments').prop('disabled', false);
                } else {
                    $('#noDocuments').show();
                    $('#documentCount').text('0 documents');
                    $('#downloadAllDocuments').prop('disabled', true);
                }
            } else {
                throw new Error(response.error);
            }
        } catch (error) {
            $('#documentErrorMsg').text(error.message || 'Error loading documents');
            $('#documentError').show();
        } finally {
            $('#documentLoading').hide();
        }
    }
    
    renderDocuments(documents) {
        const $grid = $('#documentGrid');
        $grid.empty();
        
        documents.forEach(doc => {
            const icon = doc.is_image ? 'bi-image' : 
                        doc.is_pdf ? 'bi-file-pdf' : 'bi-file-text';
            const color = doc.is_image ? 'success' : 
                         doc.is_pdf ? 'danger' : 'primary';
            
            $grid.append(`
                <div class="col-md-4 col-lg-3 mb-3">
                    <div class="card h-100 document-card" data-doc-id="${doc.id}">
                        <div class="card-body text-center">
                            <div class="mb-3">
                                <i class="bi ${icon} display-4 text-${color}"></i>
                            </div>
                            <h6 class="card-title" title="${doc.document_name}">
                                ${doc.document_name.length > 30 ? 
                                 doc.document_name.substring(0, 30) + '...' : 
                                 doc.document_name}
                            </h6>
                            <p class="card-text small text-muted">
                                <span class="d-block" title="${doc.file_name}">
                                    ${doc.file_name.length > 20 ? 
                                     doc.file_name.substring(0, 20) + '...' : 
                                     doc.file_name}
                                </span>
                                <span class="d-block">${doc.file_size}</span>
                                <span class="d-block">${doc.uploaded_at}</span>
                            </p>
                        </div>
                        <div class="card-footer bg-transparent border-top-0">
                            <div class="d-grid gap-2">
                                <button class="btn btn-sm btn-outline-primary preview-document" 
                                        data-doc-id="${doc.id}"
                                        data-doc-url="${doc.download_url}">
                                    <i class="bi bi-eye me-1"></i> Preview
                                </button>
                                <a href="${doc.download_url}" 
                                   class="btn btn-sm btn-outline-success" 
                                   download>
                                    <i class="bi bi-download me-1"></i> Download
                                </a>
                            </div>
                        </div>
                    </div>
                </div>
            `);
        });
        
        // Bind preview events
        $('.preview-document').on('click', (e) => {
            const docId = $(e.target).closest('.preview-document').data('doc-id');
            const docUrl = $(e.target).closest('.preview-document').data('doc-url');
            this.previewDocument(docId, docUrl);
        });
        
        $('#documentList').show();
    }
    
    previewDocument(docId, docUrl) {
        $('#documentPreviewTitle').text('Document Preview');
        $('#documentPreviewFrame').attr('src', docUrl);
        $('#downloadDocumentBtn').attr('href', docUrl);
        $('#documentPreviewModal').modal('show');
    }
    
    async downloadAllDocuments() {
        const memberId = $('#documentViewerModal').data('member-id');
        
        try {
            this.showLoading('Preparing documents download...');
            
            // Create zip of all documents
            // This would require server-side implementation
            this.showToast('Bulk download not yet implemented', 'info');
            
        } catch (error) {
            this.showToast(`Download failed: ${error.message}`, 'danger');
        } finally {
            this.hideLoading();
        }
    }
    
    updateActiveFiltersDisplay() {
        const $container = $('#activeFilters');
        $container.empty();
        
        if (Object.keys(this.activeFilters).length === 0) {
            $container.append('<div class="text-muted small">No filters applied</div>');
            return;
        }
        
        Object.entries(this.activeFilters).forEach(([key, value]) => {
            if (value && (Array.isArray(value) ? value.length > 0 : value !== '')) {
                const displayValue = Array.isArray(value) ? value.join(', ') : value;
                $container.append(`
                    <span class="badge bg-primary me-1 mb-1 d-inline-flex align-items-center">
                        ${key}: ${displayValue}
                        <button type="button" class="btn-close btn-close-white ms-1" 
                                style="font-size: 0.5rem;"
                                data-filter="${key}" 
                                aria-label="Remove"></button>
                    </span>
                `);
            }
        });
        
        // Bind remove events
        $container.find('.btn-close').on('click', (e) => {
            const filter = $(e.target).data('filter');
            delete this.activeFilters[filter];
            this.updateActiveFiltersDisplay();
            this.loadData();
        });
    }
    
    updateLastUpdated() {
        const now = new Date();
        $('#lastUpdated').text(now.toLocaleTimeString());
        
        // Update every minute
        setInterval(() => {
            const now = new Date();
            $('#lastUpdated').text(now.toLocaleTimeString());
        }, 60000);
    }
    
    showLoading(message = 'Loading...') {
        $('#globalLoading').show().find('p').text(message);
    }
    
    hideLoading() {
        $('#globalLoading').hide();
    }
    
    showToast(message, type = 'info') {
        const toastId = 'toast-' + Date.now();
        const icon = {
            'success': 'bi-check-circle',
            'danger': 'bi-exclamation-triangle',
            'warning': 'bi-exclamation-circle',
            'info': 'bi-info-circle'
        }[type] || 'bi-info-circle';
        
        const toastHtml = `
            <div class="toast" id="${toastId}" role="alert" aria-live="assertive" aria-atomic="true">
                <div class="toast-header bg-${type} text-white">
                    <i class="bi ${icon} me-2"></i>
                    <strong class="me-auto">${type.charAt(0).toUpperCase() + type.slice(1)}</strong>
                    <small>Just now</small>
                    <button type="button" class="btn-close btn-close-white" data-bs-dismiss="toast"></button>
                </div>
                <div class="toast-body">
                    ${message}
                </div>
            </div>
        `;
        
        $('#toastContainer').append(toastHtml);
        const toast = new bootstrap.Toast(document.getElementById(toastId));
        toast.show();
        
        // Remove after hide
        $(`#${toastId}`).on('hidden.bs.toast', function () {
            $(this).remove();
        });
    }
    
    handleKeyboardShortcuts(e) {
        // Ctrl + F: Focus search
        if (e.ctrlKey && e.key === 'f') {
            e.preventDefault();
            $('#memberSearch').focus();
        }
        
        // Ctrl + R: Refresh
        if (e.ctrlKey && e.key === 'r') {
            e.preventDefault();
            this.refreshReport();
        }
        
        // Ctrl + E: Export
        if (e.ctrlKey && e.key === 'e') {
            e.preventDefault();
            this.showExportModal();
        }
        
        // Escape: Clear search
        if (e.key === 'Escape' && $('#memberSearch').is(':focus')) {
            $('#memberSearch').val('').trigger('input');
        }
    }
    
    handleResize() {
        // Adjust DataTables on resize
        Object.values(this.dataTables).forEach(table => {
            if (table) {
                table.columns.adjust().responsive.recalc();
            }
        });
    }
}

// Initialize when document is ready
$(document).ready(function() {
    window.reportBase = new ReportBase();
});