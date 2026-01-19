// static/js/reports.js
class ReportController {
    constructor() {
        this.selectedMembers = new Set();
        this.currentTab = 'member_details';
        this.filters = {};
        this.init();
    }
    
    init() {
        this.bindEvents();
        this.loadInitialData();
    }
    
    bindEvents() {
        // Member selection
        $(document).on('click', '.member-select', (e) => {
            this.handleMemberSelect(e);
        });
        
        // Tab switching
        $(document).on('click', '.report-tab', (e) => {
            this.handleTabSwitch(e);
        });
        
        // Filter changes
        $(document).on('change', '.filter-widget', (e) => {
            this.handleFilterChange(e);
        });
        
        // Export
        $('#exportAllBtn').click(() => this.exportReport());
    }
    
    async loadTabData(tabName) {
        try {
            const response = await $.ajax({
                url: API_URLS.data,
                method: 'POST',
                contentType: 'application/json',
                data: JSON.stringify({
                    report_type: REPORT_TYPE,
                    tab: tabName,
                    filters: this.filters,
                    selected_ids: Array.from(this.selectedMembers)
                })
            });
            
            if (response.success) {
                this.renderDataTable(tabName, response.data, response.columns);
            }
        } catch (error) {
            console.error('Error loading tab data:', error);
        }
    }
    
    renderDataTable(tabName, data, columns) {
        const tableId = `table-${tabName}`;
        let $container = $(`#tab-${tabName}`);
        
        if ($container.find('table').length === 0) {
            $container.html(`
                <div class="table-responsive">
                    <table class="table table-sm table-hover" id="${tableId}">
                        <thead></thead>
                        <tbody></tbody>
                    </table>
                </div>
            `);
        }
        
        // Initialize/Reinitialize DataTable
        if ($.fn.DataTable.isDataTable(`#${tableId}`)) {
            $(`#${tableId}`).DataTable().destroy();
        }
        
        const table = $(`#${tableId}`).DataTable({
            data: data,
            columns: columns,
            pageLength: 25,
            responsive: true,
            dom: '<"top"lfB>rt<"bottom"ip>',
            buttons: [
                {
                    extend: 'excel',
                    text: '<i class="bi bi-file-earmark-excel"></i> Export',
                    className: 'btn btn-sm btn-outline-success'
                }
            ]
        });
    }
    
    async exportReport() {
        try {
            const response = await fetch(API_URLS.export, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify({
                    report_type: REPORT_TYPE,
                    filters: this.filters,
                    tabs: ['member_details', 'membership_details', 'loan', 'transactions']
                })
            });
            
            if (response.ok) {
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `${REPORT_TYPE}_report_${Date.now()}.xlsx`;
                document.body.appendChild(a);
                a.click();
                a.remove();
            }
        } catch (error) {
            console.error('Export error:', error);
        }
    }
}

// Initialize when document is ready
$(document).ready(function() {
    window.reportController = new ReportController();
});