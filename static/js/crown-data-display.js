/**
 * MINA CROWN+ DATA DISPLAY COMPONENTS
 * Premium data tables, pagination, search, and filters
 * - Responsive tables with data management
 * - Client-side pagination
 * - Search with highlighting
 * - Advanced filters
 * - Sort columns
 */

class CrownTable {
    constructor(tableElement, options = {}) {
        this.table = tableElement;
        this.data = [];
        this.filteredData = [];
        this.currentPage = 1;
        this.sortColumn = null;
        this.sortDirection = 'asc';
        this.searchQuery = '';
        this.activeFilters = {};
        this.options = {
            itemsPerPage: 10,
            searchable: true,
            sortable: true,
            paginated: true,
            ...options
        };
        this.init();
    }

    init() {
        if (!this.table) return;

        this.table.classList.add('crown-table');
        this.wrapper = this.createWrapper();
        
        this.loadData();
        
        if (this.options.searchable) {
            this.createSearchBar();
        }
        
        if (this.options.sortable) {
            this.initSorting();
        }
        
        if (this.options.paginated) {
            this.createPagination();
        }

        this.render();
    }

    createWrapper() {
        const wrapper = document.createElement('div');
        wrapper.className = 'crown-table-wrapper';
        this.table.parentNode.insertBefore(wrapper, this.table);
        wrapper.appendChild(this.table);
        return wrapper;
    }

    loadData() {
        const tbody = this.table.querySelector('tbody');
        if (!tbody) return;

        const rows = Array.from(tbody.querySelectorAll('tr'));
        this.data = rows.map(row => {
            const cells = Array.from(row.cells);
            return {
                element: row,
                values: cells.map(cell => cell.textContent.trim()),
                columns: cells.map(cell => cell.dataset.column || ''),
                html: cells.map(cell => cell.innerHTML)
            };
        });

        this.filteredData = [...this.data];
    }

    createSearchBar() {
        const searchContainer = document.createElement('div');
        searchContainer.className = 'crown-table-search';
        searchContainer.innerHTML = `
            <div class="input-group">
                <i class="fas fa-search"></i>
                <input type="text" 
                       class="input" 
                       placeholder="Search..." 
                       aria-label="Search table">
            </div>
        `;
        
        this.wrapper.insertBefore(searchContainer, this.table);
        
        const searchInput = searchContainer.querySelector('input');
        searchInput.addEventListener('input', (e) => {
            this.search(e.target.value);
        });
    }

    initSorting() {
        const headers = this.table.querySelectorAll('th[data-sortable]');
        headers.forEach((header, index) => {
            header.classList.add('crown-table-sortable');
            header.innerHTML += ' <i class="fas fa-sort sort-icon"></i>';
            header.addEventListener('click', () => {
                this.sort(index);
            });
        });
    }

    createPagination() {
        this.paginationContainer = document.createElement('div');
        this.paginationContainer.className = 'crown-pagination';
        this.wrapper.appendChild(this.paginationContainer);
        this.renderPagination();
    }

    search(query) {
        this.searchQuery = query.toLowerCase();
        this.currentPage = 1;
        this.applyFiltersAndSearch();
    }

    highlightTextNodes(element, query) {
        if (!query) return;
        
        const escapedQuery = query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
        const regex = new RegExp(escapedQuery, 'gi');
        
        const walk = (node) => {
            if (node.nodeType === Node.TEXT_NODE) {
                const text = node.textContent;
                if (regex.test(text)) {
                    const span = document.createElement('span');
                    span.innerHTML = text.replace(regex, '<mark>$&</mark>');
                    node.parentNode.replaceChild(span, node);
                }
            } else if (node.nodeType === Node.ELEMENT_NODE && node.tagName !== 'MARK') {
                Array.from(node.childNodes).forEach(walk);
            }
        };
        
        walk(element);
    }

    sort(columnIndex) {
        if (this.sortColumn === columnIndex) {
            this.sortDirection = this.sortDirection === 'asc' ? 'desc' : 'asc';
        } else {
            this.sortColumn = columnIndex;
            this.sortDirection = 'asc';
        }

        this.filteredData.sort((a, b) => {
            const aValue = a.values[columnIndex] || '';
            const bValue = b.values[columnIndex] || '';
            
            const comparison = aValue.localeCompare(bValue, undefined, { numeric: true });
            return this.sortDirection === 'asc' ? comparison : -comparison;
        });

        const headers = this.table.querySelectorAll('th[data-sortable]');
        headers.forEach((header, index) => {
            const icon = header.querySelector('.sort-icon');
            if (icon) {
                if (index === columnIndex) {
                    icon.className = this.sortDirection === 'asc' 
                        ? 'fas fa-sort-up sort-icon' 
                        : 'fas fa-sort-down sort-icon';
                } else {
                    icon.className = 'fas fa-sort sort-icon';
                }
            }
        });

        this.render();
    }

    render() {
        const tbody = this.table.querySelector('tbody');
        if (!tbody) return;

        tbody.innerHTML = '';

        const startIndex = (this.currentPage - 1) * this.options.itemsPerPage;
        const endIndex = startIndex + this.options.itemsPerPage;
        const pageData = this.filteredData.slice(startIndex, endIndex);

        pageData.forEach(row => {
            const tr = document.createElement('tr');
            row.html.forEach((cellHtml, index) => {
                const td = document.createElement('td');
                if (row.columns[index]) {
                    td.dataset.column = row.columns[index];
                }
                
                td.innerHTML = cellHtml;
                
                if (this.searchQuery) {
                    this.highlightTextNodes(td, this.searchQuery);
                }
                
                tr.appendChild(td);
            });
            tbody.appendChild(tr);
        });

        this.renderPagination();
    }

    renderPagination() {
        if (!this.paginationContainer) return;
        
        const totalPages = Math.ceil(this.filteredData.length / this.options.itemsPerPage) || 1;
        
        this.paginationContainer.innerHTML = `
            <button class="crown-pagination-btn" data-action="prev" ${this.currentPage === 1 ? 'disabled' : ''} aria-label="Previous page">
                <i class="fas fa-chevron-left"></i>
            </button>
            <span class="crown-pagination-info" aria-live="polite">
                Page ${this.currentPage} of ${totalPages} (${this.filteredData.length} items)
            </span>
            <button class="crown-pagination-btn" data-action="next" ${this.currentPage === totalPages ? 'disabled' : ''} aria-label="Next page">
                <i class="fas fa-chevron-right"></i>
            </button>
        `;
        
        this.paginationContainer.querySelectorAll('button').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const action = e.currentTarget.dataset.action;
                if (action === 'prev' && this.currentPage > 1) {
                    this.currentPage--;
                    this.render();
                }
                if (action === 'next' && this.currentPage < totalPages) {
                    this.currentPage++;
                    this.render();
                }
            });
        });
    }

    applyFiltersAndSearch() {
        let result = [...this.data];

        if (Object.keys(this.activeFilters).length > 0) {
            result = result.filter(row => {
                return Object.entries(this.activeFilters).every(([key, value]) => {
                    const columnIndex = row.columns.indexOf(key);
                    if (columnIndex === -1) return true;
                    return row.values[columnIndex].includes(value);
                });
            });
        }

        if (this.searchQuery) {
            result = result.filter(row => {
                return row.values.some(value => value.toLowerCase().includes(this.searchQuery));
            });
        }

        this.filteredData = result;
        this.render();
    }

    applyFilters(filters) {
        this.activeFilters = { ...filters };
        this.currentPage = 1;
        this.applyFiltersAndSearch();
    }
}

class CrownFilters {
    constructor(containerElement, options = {}) {
        this.container = containerElement;
        this.filters = new Map();
        this.options = {
            table: null,
            onChange: null,
            ...options
        };
        this.init();
    }

    init() {
        if (!this.container) return;
        this.container.classList.add('crown-filters');
    }

    addFilter(name, type, options = {}) {
        const filterElement = this.createFilter(name, type, options);
        this.container.appendChild(filterElement);
        this.filters.set(name, { type, element: filterElement, value: null });
    }

    createFilter(name, type, options) {
        const filter = document.createElement('div');
        filter.className = 'crown-filter-item';
        
        switch (type) {
            case 'select':
                filter.innerHTML = `
                    <label class="input-label">${options.label || name}</label>
                    <select class="input" data-filter="${name}" aria-label="${options.label || name}">
                        <option value="">All</option>
                        ${(options.options || []).map(opt => 
                            `<option value="${opt.value}">${opt.label}</option>`
                        ).join('')}
                    </select>
                `;
                break;
            case 'date':
                filter.innerHTML = `
                    <label class="input-label">${options.label || name}</label>
                    <input type="date" class="input" data-filter="${name}" aria-label="${options.label || name}">
                `;
                break;
            case 'range':
                filter.innerHTML = `
                    <label class="input-label">${options.label || name}</label>
                    <input type="range" class="input" data-filter="${name}" 
                           min="${options.min || 0}" max="${options.max || 100}"
                           aria-label="${options.label || name}">
                `;
                break;
        }

        const input = filter.querySelector('[data-filter]');
        input.addEventListener('change', (e) => {
            this.updateFilter(name, e.target.value);
        });

        return filter;
    }

    updateFilter(name, value) {
        const filterData = this.filters.get(name);
        if (filterData) {
            filterData.value = value;
            const activeFilters = this.getActiveFilters();
            
            if (this.options.table) {
                this.options.table.applyFilters(activeFilters);
            }
            
            if (this.options.onChange) {
                this.options.onChange(activeFilters);
            }
        }
    }

    getActiveFilters() {
        const active = {};
        this.filters.forEach((data, name) => {
            if (data.value) {
                active[name] = data.value;
            }
        });
        return active;
    }

    reset() {
        this.filters.forEach((data) => {
            const input = data.element.querySelector('[data-filter]');
            if (input) {
                input.value = '';
                data.value = null;
            }
        });
        
        if (this.options.table) {
            this.options.table.applyFilters({});
        }
        
        if (this.options.onChange) {
            this.options.onChange({});
        }
    }
}

const CrownDataDisplay = {
    tables: new Map(),
    filters: new Map(),

    initTable(tableElement, options = {}) {
        const table = new CrownTable(tableElement, options);
        this.tables.set(tableElement.id || `table-${Date.now()}`, table);
        return table;
    },

    initFilters(containerElement, options = {}) {
        const filters = new CrownFilters(containerElement, options);
        this.filters.set(containerElement.id || `filters-${Date.now()}`, filters);
        return filters;
    },

    addStyles() {
        const style = document.createElement('style');
        style.textContent = `
            .crown-table-wrapper {
                background: var(--surface-primary);
                border: 1px solid var(--border-primary);
                border-radius: var(--radius-xl);
                overflow: hidden;
            }

            .crown-table-search {
                padding: var(--space-4);
                border-bottom: 1px solid var(--border-primary);
            }

            .crown-table-search .input-group {
                position: relative;
                margin: 0;
            }

            .crown-table-search i {
                position: absolute;
                left: 16px;
                top: 50%;
                transform: translateY(-50%);
                color: var(--text-tertiary);
            }

            .crown-table-search input {
                padding-left: 48px;
            }

            .crown-table {
                width: 100%;
                border-collapse: collapse;
            }

            .crown-table thead {
                background: var(--surface-secondary);
                border-bottom: 2px solid var(--border-primary);
            }

            .crown-table th {
                padding: var(--space-4);
                text-align: left;
                font-weight: var(--font-weight-semibold);
                color: var(--text-primary);
                font-size: var(--font-size-sm);
                text-transform: uppercase;
                letter-spacing: 0.05em;
            }

            .crown-table-sortable {
                cursor: pointer;
                user-select: none;
                position: relative;
            }

            .crown-table-sortable:hover {
                background: var(--surface-elevated);
            }

            .crown-table-sortable .sort-icon {
                margin-left: var(--space-2);
                font-size: 0.75em;
                opacity: 0.5;
            }

            .crown-table td {
                padding: var(--space-4);
                border-bottom: 1px solid var(--border-secondary);
                color: var(--text-secondary);
            }

            .crown-table tbody tr:hover {
                background: var(--surface-secondary);
            }

            .crown-table mark {
                background: rgba(102, 126, 234, 0.3);
                color: var(--text-primary);
                padding: 2px 4px;
                border-radius: 3px;
            }

            .crown-pagination {
                display: flex;
                align-items: center;
                justify-content: center;
                gap: var(--space-4);
                padding: var(--space-4);
                border-top: 1px solid var(--border-primary);
            }

            .crown-pagination-btn {
                background: var(--surface-secondary);
                border: 1px solid var(--border-primary);
                color: var(--text-primary);
                padding: var(--space-2) var(--space-3);
                border-radius: var(--radius-md);
                cursor: pointer;
                transition: all 0.2s ease;
            }

            .crown-pagination-btn:hover:not(:disabled) {
                background: var(--surface-elevated);
                border-color: var(--color-brand-500);
            }

            .crown-pagination-btn:focus {
                outline: 2px solid var(--color-brand-500);
                outline-offset: 2px;
            }

            .crown-pagination-btn:disabled {
                opacity: 0.5;
                cursor: not-allowed;
            }

            .crown-pagination-info {
                font-size: var(--font-size-sm);
                color: var(--text-secondary);
            }

            .crown-filters {
                display: flex;
                gap: var(--space-4);
                padding: var(--space-4);
                background: var(--surface-secondary);
                border-radius: var(--radius-lg);
                flex-wrap: wrap;
            }

            .crown-filter-item {
                flex: 1;
                min-width: 200px;
            }
        `;
        document.head.appendChild(style);
    }
};

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        CrownDataDisplay.addStyles();
        console.log('✨ Crown+ Data Display initialized');
    });
} else {
    CrownDataDisplay.addStyles();
    console.log('✨ Crown+ Data Display initialized');
}

window.CrownDataDisplay = CrownDataDisplay;
window.CrownTable = CrownTable;
window.CrownFilters = CrownFilters;
