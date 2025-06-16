let allTransactions = [];
let currentPage = 1;
const ITEMS_PER_PAGE = 10;
let typeChart, monthlyChart;

document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('applyFilters').addEventListener('click', applyTransactionFilters);
    setupDashboard();
});

// Sets up the dashboard by loading transaction types and initial data
async function setupDashboard() {
    showLoading(true);
    try {
        await populateTransactionTypes();
        await applyTransactionFilters();
    } catch (error) {
        console.error('Dashboard Setup Error:', error);
        showErrorMessage('Failed to set up the dashboard. See console for details.');
    } finally {
        showLoading(false);
    }
}

// Applies filters based on type and date range, updating dashboard data
async function applyTransactionFilters() {
    showLoading(true);
    currentPage = 1;

    const type = document.getElementById('transactionType').value;
    const dateFrom = document.getElementById('dateFrom').value;
    const dateTo = document.getElementById('dateTo').value;

    const params = new URLSearchParams();
    if (type) params.append('type', type);
    if (dateFrom) params.append('start_date', dateFrom);
    if (dateTo) params.append('end_date', dateTo);

    console.log(`Applying filters with params: ${params.toString()}`);

    try {
        const [summaryData, transactionsData] = await Promise.all([
            fetchApiData(`http://localhost:5000/api/summary?${params.toString()}`),
            fetchApiData(`http://localhost:5000/api/transactions?${params.toString()}`)
        ]);

        if (summaryData.success) {
            updateSummaryMetrics(summaryData.summary);
            updateTransactionTypeChart(summaryData.summary.by_type || []);
            updateMonthlyVolumeChart(summaryData.summary.by_month || []);
        } else {
            throw new Error(summaryData.error || 'Failed to load summary data');
        }

        if (transactionsData.success) {
            allTransactions = transactionsData.transactions || [];
            console.log(`Successfully loaded ${allTransactions.length} transactions.`);
            displayTransactions();
            setupPagination();
        } else {
            throw new Error(transactionsData.error || 'Failed to load transactions');
        }

    } catch (error) {
        console.error('Error applying filters:', error);
        showErrorMessage(error.message);
        document.getElementById('transactionsTable').innerHTML = `<tr><td colspan="5" class="text-center text-danger">Error loading data.</td></tr>`;
    } finally {
        showLoading(false);
    }
}

// Fetches JSON data from a specified API endpoint
async function fetchApiData(url) {
    const response = await fetch(url);
    if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`HTTP error! Status: ${response.status}, Message: ${errorText}`);
    }
    return response.json();
}

// Toggles the visibility of the loading spinner
function showLoading(isLoading) {
    const spinner = document.getElementById('tableLoading');
    if (spinner) {
        spinner.style.display = isLoading ? 'flex' : 'none';
    }
}

// Displays an error message at the top of the page for 5 seconds
function showErrorMessage(message) {
    const errorElement = document.getElementById('error-message');
    errorElement.textContent = message;
    errorElement.style.display = 'block';
    setTimeout(() => {
        errorElement.style.display = 'none';
    }, 5000);
}

// Populates the transaction type dropdown with options from the API
async function populateTransactionTypes() {
    try {
        const data = await fetchApiData('http://localhost:5000/api/transactions/types');
        if (data.success) {
            const typeSelect = document.getElementById('transactionType');
            while (typeSelect.options.length > 1) {
                typeSelect.remove(1);
            }
            data.types.forEach(type => {
                const option = document.createElement('option');
                option.value = type;
                option.textContent = type;
                typeSelect.appendChild(option);
            });
        } else {
            throw new Error(data.error);
        }
    } catch (error) {
        console.error('Error loading transaction types:', error);
        showErrorMessage('Could not load transaction types.');
    }
}

// Updates the summary cards with total transactions, amount, and average
function updateSummaryMetrics(summary) {
    document.getElementById('totalTransactions').textContent = (summary.total_transactions || 0).toLocaleString();
    document.getElementById('totalAmount').textContent = `${Math.round(summary.total_amount || 0).toLocaleString()} RWF`;
    document.getElementById('avgAmount').textContent = `${Math.round(summary.average_amount || 0).toLocaleString()} RWF`;
}

// Renders the transactions table with paginated data
function displayTransactions() {
    const tableBody = document.getElementById('transactionsTable');
    tableBody.innerHTML = '';

    if (allTransactions.length === 0) {
        tableBody.innerHTML = '<tr><td colspan="5" class="text-center">No transactions found for the selected filters.</td></tr>';
        return;
    }

    const startIndex = (currentPage - 1) * ITEMS_PER_PAGE;
    const paginatedItems = allTransactions.slice(startIndex, startIndex + ITEMS_PER_PAGE);

    paginatedItems.forEach(t => {
        const row = document.createElement('tr');
        const senderReceiver = t.sender || t.receiver || t.agent || 'N/A';
        row.innerHTML = `
            <td>${new Date(t.date).toLocaleDateString('en-CA', { month: 'short', day: '2-digit', year: 'numeric' })}</td>
            <td>${t.transaction_type}</td>
            <td>${Math.round(t.amount || 0).toLocaleString()}</td>
            <td>${senderReceiver}</td>
            <td><button class="btn btn-sm btn-outline-secondary">Details</button></td>
        `;
        row.querySelector('button').addEventListener('click', () => showTransactionDetails(t));
        tableBody.appendChild(row);
    });
}

// Configures pagination controls with page links and ellipses
function setupPagination() {
    const paginationContainer = document.getElementById('pagination');
    paginationContainer.innerHTML = '';
    const totalPages = Math.ceil(allTransactions.length / ITEMS_PER_PAGE);

    if (totalPages <= 1) return;

    const createPageLink = (page, text, disabled = false, active = false) => {
        const li = document.createElement('li');
        li.className = `page-item ${disabled ? 'disabled' : ''} ${active ? 'active' : ''}`;
        const a = document.createElement('a');
        a.className = 'page-link';
        a.href = '#';
        a.textContent = text;

        if (!disabled) {
            a.addEventListener('click', (e) => {
                e.preventDefault();
                currentPage = page;
                displayTransactions();
                setupPagination();
            });
        }
        li.appendChild(a);
        return li;
    };

    const addEllipsis = () => {
        const li = document.createElement('li');
        li.className = 'page-item disabled';
        li.innerHTML = `<span class="page-link">...</span>`;
        paginationContainer.appendChild(li);
    };

    const maxVisibleButtons = 7;
    paginationContainer.appendChild(createPageLink(currentPage - 1, 'Previous', currentPage === 1));

    if (totalPages <= maxVisibleButtons) {
        for (let i = 1; i <= totalPages; i++) {
            paginationContainer.appendChild(createPageLink(i, i, false, i === currentPage));
        }
    } else {
        const sideWidth = 1;
        let pages = [];

        pages.push(1);
        for (let i = Math.max(2, currentPage - sideWidth); i <= Math.min(totalPages - 1, currentPage + sideWidth); i++) {
            pages.push(i);
        }
        pages.push(totalPages);

        pages = [...new Set(pages)].sort((a, b) => a - b);

        let lastPage = 0;
        pages.forEach(page => {
            if (lastPage && page - lastPage > 1) {
                addEllipsis();
            }
            paginationContainer.appendChild(createPageLink(page, page, false, page === currentPage));
            lastPage = page;
        });
    }

    paginationContainer.appendChild(createPageLink(currentPage + 1, 'Next', currentPage === totalPages));
}

// Displays transaction details in a modal window
function showTransactionDetails(t) {
    const modalBody = document.getElementById('transactionDetails');
    modalBody.innerHTML = `
        <p><strong>Transaction ID:</strong> ${t.transaction_id || 'N/A'}</p>
        <p><strong>Date:</strong> ${new Date(t.date).toLocaleString()}</p>
        <p><strong>Type:</strong> ${t.transaction_type}</p>
        <p><strong>Amount:</strong> ${Math.round(t.amount || 0).toLocaleString()} RWF</p>
        <p><strong>Sender:</strong> ${t.sender || 'N/A'}</p>
        <p><strong>Receiver:</strong> ${t.receiver || 'N/A'}</p>
        <p><strong>Agent:</strong> ${t.agent || 'N/A'}</p>
        <hr>
        <p><strong>Full Message:</strong></p>
        <p class="text-muted small">${t.message || 'N/A'}</p>
    `;

    const modal = new bootstrap.Modal(document.getElementById('transactionModal'));
    modal.show();
}

// Updates the doughnut chart showing transactions by type
function updateTransactionTypeChart(typeData) {
    const ctx = document.getElementById('typeChart').getContext('2d');
    const labels = typeData.map(d => d.transaction_type);
    const data = typeData.map(d => d.total_amount);

    if (typeChart) {
        typeChart.data.labels = labels;
        typeChart.data.datasets[0].data = data;
        typeChart.update();
    } else {
        typeChart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: labels,
                datasets: [{
                    data: data,
                    backgroundColor: ['#ffcc00', '#2c3e50', '#e74c3c', '#3498db', '#9b59b6', '#f1c40f', '#1abc9c'],
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { position: 'bottom' } }
            }
        });
    }
}

// Updates the bar chart showing monthly transaction volumes
function updateMonthlyVolumeChart(monthlyData) {
    const ctx = document.getElementById('monthlyChart').getContext('2d');
    const labels = monthlyData.map(d => new Date(d.month + '-02').toLocaleString('default', { month: 'short', year: '2-digit' }));
    const data = monthlyData.map(d => d.total_amount);

    if (monthlyChart) {
        monthlyChart.data.labels = labels;
        monthlyChart.data.datasets[0].data = data;
        monthlyChart.update();
    } else {
        monthlyChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Total Amount',
                    data: data,
                    backgroundColor: '#ffcc00'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: { y: { beginAtZero: true } }
            }
        });
    }
}
