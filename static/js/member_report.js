// static/js/member_report.js
class MemberReport extends ReportBase {
    constructor() {
        super();
        this.members = [];
        this.currentPage = 1;
        this.totalPages = 1;
        this.searchTerm = '';
        this.isLoadingMembers = false;
        
        this.initMemberReport();
    }
    
    initMemberReport() {
        this.bindMemberEvents();
        this.loadMembers();
        this.updateSelectionSummary();
    }
    
    bindMemberEvents() {
        // Search
        $('#memberSearch').on('input', _.debounce(() => this.handleSearch(), 300));
        $('#clearSearch').on('click', () => this.clearSearch());
        
        // Filter application
        $('#applyLeftFilters').on('click', () => this.applyLeftFilters());
        $('#resetLeftFilters').on('click', () => this.resetLeftFilters());
        
        // Member selection
        $('#selectAllMembers').on('change', (e) => this.toggleSelectAll(e));
        
        // Export selected
        $('#exportSelected').on('click', () => this.exportSelected());
        
        // Pagination
        $('#prevPage').on('click', () => this.prevPage());
        $('#nextPage').on('click', () => this.nextPage());
        
        // Member list events (delegated)
        $('#memberList').on('change', '.member-checkbox', (e) => this.toggleMemberSelection(e));
        $('#memberList').on('click', '.member-item', (e) => {
            if (!$(e.target).is('input') && !$(e.target).is('a')) {
                this.toggleMemberItem($(e.currentTarget));
            }
        });
    }
    
    async loadMembers(page = 1) {
        if (this.isLoadingMembers) return;
        
        this.isLoadingMembers = true;
        this.currentPage = page;
        
        $('#memberList').html(`
            <div class="loading-state text-center py-5">
                <div class="spinner-border spinner-border-sm text-primary" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
                <p class="mt-2 small text-muted">Loading members...</p>
            </div>
        `);
        
        try {
            const filters = this.buildMemberFilters();
            
            const response = await $.ajax({
                url: REPORT_CONFIG.apiUrls.members,
                method: 'POST',
                contentType: 'application/json',
                data: JSON.stringify({
                    filters: filters,
                    search: this.searchTerm,
                    page: page,
                    per_page: 50,
                    sort_by: 'created_at',
                    sort_order: 'desc'
                })
            });
            
            if (response.success) {
                this.members = response.members;
                this.totalPages = response.total_pages;
                this.renderMemberList();
                this.updateMemberCount(response.total);
                this.updatePagination(response);
                this.updateExportButton();
            } else {
                throw new Error(response.error);
            }
        } catch (error) {
            $('#memberList').html(`
                <div class="error-state text-center py-5">
                    <i class="bi bi-exclamation-triangle display-4 text-danger"></i>
                    <p class="mt-3 text-danger">Error loading members</p>
                    <button class="btn btn-sm btn-outline-primary" onclick="memberReport.loadMembers()">
                        <i class="bi bi-arrow-clockwise me-1"></i> Retry
                    </button>
                </div>
            `);
        } finally {
            this.isLoadingMembers = false;
        }
    }
    
    buildMemberFilters() {
        const filters = {};
        
        // Membership type
        const membershipType = $('#filterMembershipType').val();
        if (membershipType && membershipType.length > 0) {
            filters.membership_type = membershipType;
        }
        
        // Status
        const status = $('#filterStatus').val();
        if (status && status.length > 0) {
            filters.status = status;
        }
        
        // Member type
        const memberType = $('#filterMemberType').val();
        if (memberType && memberType.length > 0) {
            filters.member_type = memberType;
        }
        
        // Ward
        const ward = $('#filterWard').val();
        if (ward && ward.length > 0) {
            filters.ward = ward;
        }
        
        // Additional filters
        const resident = $('#filterResident').val();
        if (resident !== '') {
            filters.is_resident = resident;
        }
        
        const aadharAddress = $('#filterAadharAddress').val();
        if (aadharAddress !== '') {
            filters.has_aadhar_address = aadharAddress;
        }
        
        const dateFrom = $('#filterDateFrom').val();
        const dateTo = $('#filterDateTo').val();
        if (dateFrom) filters.from_date = dateFrom;
        if (dateTo) filters.to_date = dateTo;
        
        return filters;
    }
    
    renderMemberList() {
        const $container = $('#memberList');
        
        if (this.members.length === 0) {
            $container.html(`
                <div class="empty-state text-center py-5">
                    <i class="bi bi-people display-4 text-muted"></i>
                    <p class="mt-3 text-muted">No members found</p>
                    <button class="btn btn-sm btn-outline-primary" onclick="memberReport.resetLeftFilters()">
                        <i class="bi bi-funnel me-1"></i> Clear Filters
                    </button>
                </div>
            `);
            return;
        }
        
        let html = '<div class="list-group list-group-flush">';
        
        this.members.forEach(member => {
            const isSelected = this.selectedItems.has(member.id);
            const hasDocuments = member.has_documents ? 'text-info' : 'text-muted';
            
            html += `
                <div class="list-group-item list-group-item-action member-item p-2 ${isSelected ? 'active' : ''}" 
                     data-member-id="${member.id}">
                    <div class="d-flex align-items-start">
                        <div class="form-check flex-shrink-0 me-2 mt-1">
                            <input class="form-check-input member-checkbox" 
                                   type="checkbox" 
                                   value="${member.id}"
                                   ${isSelected ? 'checked' : ''}>
                        </div>
                        <div class="flex-grow-1">
                            <div class="d-flex justify-content-between align-items-start">
                                <div>
                                    <div class="fw-semibold member-code">${member.membership_code}</div>
                                    <div class="small member-name">${member.full_name}</div>
                                    ${member.full_name_mar ? `<div class="small text-muted member-name-mar">${member.full_name_mar}</div>` : ''}
                                </div>
                                <div class="text-end">
                                    <span class="badge bg-${member.status.name === 'Active' ? 'success' : 'secondary'} badge-sm">
                                        ${member.status.name}
                                    </span>
                                    <div class="mt-1">
                                        <i class="bi bi-file-text ${hasDocuments}" 
                                           title="${member.has_documents ? 'Has documents' : 'No documents'}"></i>
                                    </div>
                                </div>
                            </div>
                            <div class="row mt-1">
                                <div class="col-6 small text-muted">
                                    <i class="bi bi-telephone me-1"></i> ${member.mobile_no || 'N/A'}
                                </div>
                                <div class="col-6 small text-muted text-end">
                                    ${member.created_at}
                                </div>
                            </div>
                            <div class="small text-muted">
                                ${member.membership_type.name} • ${member.ward || 'No ward'}
                            </div>
                        </div>
                    </div>
                </div>
            `;
        });
        
        html += '</div>';
        $container.html(html);
        
        // Highlight search term
        if (this.searchTerm) {
            this.highlightSearchTerm();
        }
    }
    
    highlightSearchTerm() {
        const term = this.searchTerm.toLowerCase();
        $('.member-item').each(function() {
            const text = $(this).text().toLowerCase();
            if (text.includes(term)) {
                $(this).addClass('bg-warning bg-opacity-10');
                
                // Highlight matching text in member code and name
                const $code = $(this).find('.member-code');
                const $name = $(this).find('.member-name');
                
                if ($code.text().toLowerCase().includes(term)) {
                    $code.html($code.text().replace(
                        new RegExp(term, 'gi'),
                        match => `<mark class="bg-warning">${match}</mark>`
                    ));
                }
                
                if ($name.text().toLowerCase().includes(term)) {
                    $name.html($name.text().replace(
                        new RegExp(term, 'gi'),
                        match => `<mark class="bg-warning">${match}</mark>`
                    ));
                }
            }
        });
    }
    
    handleSearch() {
        this.searchTerm = $('#memberSearch').val().trim();
        this.loadMembers(1);
    }
    
    clearSearch() {
        $('#memberSearch').val('');
        this.searchTerm = '';
        this.loadMembers(1);
    }
    
    applyLeftFilters() {
        this.activeFilters = this.buildMemberFilters();
        this.updateActiveFiltersDisplay();
        this.loadMembers(1);
        this.showToast('Filters applied', 'success');
    }
    
    resetLeftFilters() {
        $('.filter-select').val(null).trigger('change');
        $('#filterResident').val('');
        $('#filterAadharAddress').val('');
        $('#filterDateFrom').val('');
        $('#filterDateTo').val('');
        $('#memberSearch').val('');
        
        this.activeFilters = {};
        this.searchTerm = '';
        this.updateActiveFiltersDisplay();
        this.loadMembers(1);
        this.showToast('Filters reset', 'info');
    }
    
    toggleSelectAll(e) {
        const isChecked = $(e.target).is(':checked');
        
        if (isChecked) {
            this.members.forEach(member => {
                this.selectedItems.add(member.id);
            });
            $('.member-checkbox').prop('checked', true);
            $('.member-item').addClass('active');
        } else {
            this.members.forEach(member => {
                this.selectedItems.delete(member.id);
            });
            $('.member-checkbox').prop('checked', false);
            $('.member-item').removeClass('active');
        }
        
        this.updateSelectionSummary();
        this.updateExportButton();
        
        // Load data for current tab
        if (this.selectedItems.size > 0 && this.currentTab) {
            this.loadTabData(this.currentTab);
        }
    }
    
    toggleMemberSelection(e) {
        const $checkbox = $(e.target);
        const memberId = parseInt($checkbox.val());
        const $item = $checkbox.closest('.member-item');
        
        if ($checkbox.is(':checked')) {
            this.selectedItems.add(memberId);
            $item.addClass('active');
        } else {
            this.selectedItems.delete(memberId);
            $item.removeClass('active');
            $('#selectAllMembers').prop('checked', false);
        }
        
        this.updateSelectionSummary();
        this.updateExportButton();
        
        // Load data for current tab
        if (this.selectedItems.size > 0 && this.currentTab) {
            this.loadTabData(this.currentTab);
        }
    }
    
    toggleMemberItem($item) {
        const memberId = parseInt($item.data('member-id'));
        const $checkbox = $item.find('.member-checkbox');
        
        if ($checkbox.is(':checked')) {
            $checkbox.prop('checked', false);
            this.selectedItems.delete(memberId);
            $item.removeClass('active');
        } else {
            $checkbox.prop('checked', true);
            this.selectedItems.add(memberId);
            $item.addClass('active');
        }
        
        this.updateSelectionSummary();
        this.updateExportButton();
        
        // Load data for current tab
        if (this.selectedItems.size > 0 && this.currentTab) {
            this.loadTabData(this.currentTab);
        }
    }
    
    updateSelectionSummary() {
        const selectedCount = this.selectedItems.size;
        const totalCount = $('#memberCount').text();
        
        $('#selectedCount').text(selectedCount);
        $('#totalFilteredCount').text(totalCount);
        
        // Update select all checkbox
        const allVisibleSelected = this.members.length > 0 && 
                                  this.members.every(m => this.selectedItems.has(m.id));
        $('#selectAllMembers').prop('checked', allVisibleSelected);
    }
    
    updateExportButton() {
        const canExport = this.selectedItems.size > 0;
        $('#exportSelected').prop('disabled', !canExport);
        $('#exportAllBtn').prop('disabled', !canExport);
    }
    
    updateMemberCount(count) {
        $('#memberCount').text(count);
    }
    
    updatePagination(response) {
        const $pagination = $('#memberPagination');
        const $prev = $('#prevPage');
        const $next = $('#nextPage');
        const $current = $('#currentPage');
        
        if (response.total_pages > 1) {
            $pagination.show();
            $current.text(`Page ${response.current_page} of ${response.total_pages}`);
            
            $prev.toggleClass('disabled', !response.has_previous);
            $next.toggleClass('disabled', !response.has_next);
        } else {
            $pagination.hide();
        }
    }
    
    prevPage() {
        if (this.currentPage > 1) {
            this.loadMembers(this.currentPage - 1);
        }
    }
    
    nextPage() {
        if (this.currentPage < this.totalPages) {
            this.loadMembers(this.currentPage + 1);
        }
    }
    
    async exportSelected() {
        if (this.selectedItems.size === 0) {
            this.showToast('No members selected for export', 'warning');
            return;
        }
        
        try {
            this.showLoading('Preparing export...');
            
            const exportData = {
                report_type: 'member',
                export_type: 'excel',
                tabs: ['member_details', 'membership_details', 'payments'],
                filters: this.activeFilters,
                selected_ids: Array.from(this.selectedItems),
                file_name: `selected_members_${new Date().toISOString().slice(0, 10)}`
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
                a.download = `selected_members_export.xlsx`;
                document.body.appendChild(a);
                a.click();
                a.remove();
                window.URL.revokeObjectURL(url);
                
                this.showToast('Export completed successfully', 'success');
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
    
    loadData() {
        this.loadMembers(1);
        
        // Reload current tab data if items are selected
        if (this.selectedItems.size > 0 && this.currentTab) {
            this.loadTabData(this.currentTab);
        }
    }
}

// Initialize member report
$(document).ready(function() {
    if (REPORT_CONFIG.type === 'member') {
        window.memberReport = new MemberReport();
    }
});