// static/js/book_report.js
class BookReport extends ReportBase {
    constructor() {
        super();
        this.books = [];
        this.currentPage = 1;
        this.totalPages = 1;
        this.searchTerm = '';
        this.isLoadingBooks = false;
        
        this.initBookReport();
    }
    
    initBookReport() {
        this.bindBookEvents();
        this.loadBooks();
        this.updateSelectionSummary();
    }
    
    bindBookEvents() {
        // Search
        $('#bookSearch').on('input', _.debounce(() => this.handleSearch(), 300));
        $('#clearBookSearch').on('click', () => this.clearSearch());
        
        // Filter application
        $('#applyLeftFilters').on('click', () => this.applyLeftFilters());
        $('#resetLeftFilters').on('click', () => this.resetLeftFilters());
        
        // Book selection
        $('#selectAllBooks').on('change', (e) => this.toggleSelectAll(e));
        
        // Export selected
        $('#exportSelected').on('click', () => this.exportSelected());
    }
    
    async loadBooks(page = 1) {
        if (this.isLoadingBooks) return;
        
        this.isLoadingBooks = true;
        this.currentPage = page;
        
        $('#bookList').html(`
            <div class="loading-state text-center py-5">
                <div class="spinner-border spinner-border-sm text-primary" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
                <p class="mt-2 small text-muted">Loading books...</p>
            </div>
        `);
        
        try {
            const filters = this.buildBookFilters();
            
            // For now, we'll load a sample list
            // In production, this would call an API endpoint
            setTimeout(() => {
                // Mock data for demonstration
                this.books = this.getMockBooks();
                this.totalPages = 3;
                this.renderBookList();
                this.updateBookCount(this.books.length);
                this.updateSelectionSummary();
                this.updateExportButton();
                
                this.isLoadingBooks = false;
            }, 500);
            
        } catch (error) {
            $('#bookList').html(`
                <div class="error-state text-center py-5">
                    <i class="bi bi-exclamation-triangle display-4 text-danger"></i>
                    <p class="mt-3 text-danger">Error loading books</p>
                    <button class="btn btn-sm btn-outline-primary" onclick="bookReport.loadBooks()">
                        <i class="bi bi-arrow-clockwise me-1"></i> Retry
                    </button>
                </div>
            `);
            this.isLoadingBooks = false;
        }
    }
    
    buildBookFilters() {
        const filters = {};
        
        // Category
        const category = $('#filterCategory').val();
        if (category && category.length > 0) {
            filters.category = category;
        }
        
        // Language
        const language = $('#filterLanguage').val();
        if (language && language.length > 0) {
            filters.language = language;
        }
        
        // Publisher
        const publisher = $('#filterPublisher').val();
        if (publisher && publisher.length > 0) {
            filters.publisher = publisher;
        }
        
        // Availability
        const availability = $('#filterAvailability').val();
        if (availability) {
            filters.availability = availability;
        }
        
        // Additional filters
        const isbn = $('#filterISBN').val();
        if (isbn) {
            filters.isbn = isbn;
        }
        
        const author = $('#filterAuthor').val();
        if (author) {
            filters.author = author;
        }
        
        const addedFrom = $('#filterAddedFrom').val();
        const addedTo = $('#filterAddedTo').val();
        if (addedFrom) filters.added_from = addedFrom;
        if (addedTo) filters.added_to = addedTo;
        
        return filters;
    }
    
    getMockBooks() {
        // Mock data for demonstration
        return [
            {
                id: 1,
                title: "The Great Gatsby",
                author: "F. Scott Fitzgerald",
                category: "Fiction",
                language: "English",
                isbn: "9780743273565",
                publisher: "Scribner",
                availability: "available",
                accession_no: "ACC001",
                year: 1925,
                copies: 5,
                available_copies: 3
            },
            {
                id: 2,
                title: "To Kill a Mockingbird",
                author: "Harper Lee",
                category: "Fiction",
                language: "English",
                isbn: "9780061120084",
                publisher: "J.B. Lippincott & Co.",
                availability: "issued",
                accession_no: "ACC002",
                year: 1960,
                copies: 3,
                available_copies: 0
            },
            // Add more mock books as needed
        ];
    }
    
    renderBookList() {
        const $container = $('#bookList');
        
        if (this.books.length === 0) {
            $container.html(`
                <div class="empty-state text-center py-5">
                    <i class="bi bi-book display-4 text-muted"></i>
                    <p class="mt-3 text-muted">No books found</p>
                    <button class="btn btn-sm btn-outline-primary" onclick="bookReport.resetLeftFilters()">
                        <i class="bi bi-funnel me-1"></i> Clear Filters
                    </button>
                </div>
            `);
            return;
        }
        
        let html = '<div class="list-group list-group-flush">';
        
        this.books.forEach(book => {
            const isSelected = this.selectedItems.has(book.id);
            const availabilityColor = {
                'available': 'success',
                'issued': 'warning',
                'reserved': 'info',
                'damaged': 'danger'
            }[book.availability] || 'secondary';
            
            html += `
                <div class="list-group-item list-group-item-action book-item p-2 ${isSelected ? 'active' : ''}" 
                     data-book-id="${book.id}">
                    <div class="d-flex align-items-start">
                        <div class="form-check flex-shrink-0 me-2 mt-1">
                            <input class="form-check-input book-checkbox" 
                                   type="checkbox" 
                                   value="${book.id}"
                                   ${isSelected ? 'checked' : ''}>
                        </div>
                        <div class="flex-grow-1">
                            <div class="d-flex justify-content-between align-items-start">
                                <div>
                                    <div class="fw-semibold book-title">${book.title}</div>
                                    <div class="small text-muted">by ${book.author}</div>
                                </div>
                                <div class="text-end">
                                    <span class="badge bg-${availabilityColor} badge-sm">
                                        ${book.availability}
                                    </span>
                                </div>
                            </div>
                            <div class="row mt-1">
                                <div class="col-6 small text-muted">
                                    <i class="bi bi-tag me-1"></i> ${book.category}
                                </div>
                                <div class="col-6 small text-muted text-end">
                                    <i class="bi bi-translate me-1"></i> ${book.language}
                                </div>
                            </div>
                            <div class="small">
                                <span class="text-muted">ISBN:</span> ${book.isbn} |
                                <span class="text-muted">Publisher:</span> ${book.publisher} |
                                <span class="text-muted">Copies:</span> ${book.copies} (${book.available_copies} available)
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
        $('.book-item').each(function() {
            const text = $(this).text().toLowerCase();
            if (text.includes(term)) {
                $(this).addClass('bg-warning bg-opacity-10');
                
                // Highlight matching text in title
                const $title = $(this).find('.book-title');
                if ($title.text().toLowerCase().includes(term)) {
                    $title.html($title.text().replace(
                        new RegExp(term, 'gi'),
                        match => `<mark class="bg-warning">${match}</mark>`
                    ));
                }
            }
        });
    }
    
    handleSearch() {
        this.searchTerm = $('#bookSearch').val().trim();
        this.loadBooks(1);
    }
    
    clearSearch() {
        $('#bookSearch').val('');
        this.searchTerm = '';
        this.loadBooks(1);
    }
    
    applyLeftFilters() {
        this.activeFilters = this.buildBookFilters();
        this.updateActiveFiltersDisplay();
        this.loadBooks(1);
        this.showToast('Filters applied', 'success');
    }
    
    resetLeftFilters() {
        $('.filter-select').val(null).trigger('change');
        $('#filterAvailability').val('');
        $('#filterISBN').val('');
        $('#filterAuthor').val('');
        $('#filterAddedFrom').val('');
        $('#filterAddedTo').val('');
        $('#bookSearch').val('');
        
        this.activeFilters = {};
        this.searchTerm = '';
        this.updateActiveFiltersDisplay();
        this.loadBooks(1);
        this.showToast('Filters reset', 'info');
    }
    
    toggleSelectAll(e) {
        const isChecked = $(e.target).is(':checked');
        
        if (isChecked) {
            this.books.forEach(book => {
                this.selectedItems.add(book.id);
            });
            $('.book-checkbox').prop('checked', true);
            $('.book-item').addClass('active');
        } else {
            this.books.forEach(book => {
                this.selectedItems.delete(book.id);
            });
            $('.book-checkbox').prop('checked', false);
            $('.book-item').removeClass('active');
        }
        
        this.updateSelectionSummary();
        this.updateExportButton();
        
        // Load data for current tab
        if (this.selectedItems.size > 0 && this.currentTab) {
            this.loadTabData(this.currentTab);
        }
    }
    
    toggleBookSelection(e) {
        const $checkbox = $(e.target);
        const bookId = parseInt($checkbox.val());
        const $item = $checkbox.closest('.book-item');
        
        if ($checkbox.is(':checked')) {
            this.selectedItems.add(bookId);
            $item.addClass('active');
        } else {
            this.selectedItems.delete(bookId);
            $item.removeClass('active');
            $('#selectAllBooks').prop('checked', false);
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
        $('#selectedCount').text(selectedCount);
        
        // Update select all checkbox
        const allVisibleSelected = this.books.length > 0 && 
                                  this.books.every(b => this.selectedItems.has(b.id));
        $('#selectAllBooks').prop('checked', allVisibleSelected);
    }
    
    updateExportButton() {
        const canExport = this.selectedItems.size > 0;
        $('#exportSelected').prop('disabled', !canExport);
        $('#exportAllBtn').prop('disabled', !canExport);
    }
    
    updateBookCount(count) {
        $('#bookCount').text(count);
    }
    
    async exportSelected() {
        if (this.selectedItems.size === 0) {
            this.showToast('No books selected for export', 'warning');
            return;
        }
        
        try {
            this.showLoading('Preparing export...');
            
            const exportData = {
                report_type: 'book',
                export_type: 'excel',
                tabs: ['book_catalog', 'book_circulation'],
                filters: this.activeFilters,
                selected_ids: Array.from(this.selectedItems),
                file_name: `selected_books_${new Date().toISOString().slice(0, 10)}`
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
                a.download = `selected_books_export.xlsx`;
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
        this.loadBooks(1);
        
        // Reload current tab data if items are selected
        if (this.selectedItems.size > 0 && this.currentTab) {
            this.loadTabData(this.currentTab);
        }
    }
}

// Initialize book report
$(document).ready(function() {
    if (REPORT_CONFIG.type === 'book') {
        window.bookReport = new BookReport();
    }
});