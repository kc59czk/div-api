const API_BASE = "http://127.0.0.1:5000";

// --- State Management ---
let authToken = localStorage.getItem("divapi_token");
let currentUserId = localStorage.getItem("divapi_user_id");
let accounts = [];
let currentAccountId = null;

// --- DOM Elements ---
const el = {
    loginCard: document.getElementById('login-card'),
    registerCard: document.getElementById('register-card'),
    dashboardContent: document.getElementById('dashboard-content'),
    navMenu: document.getElementById('nav-menu'),
    userInfo: document.getElementById('user-info'),
    logoutBtn: document.getElementById('logout-btn'),
    notificationArea: document.getElementById('notification-area'),
    
    loginForm: document.getElementById('login-form'),
    registerForm: document.getElementById('register-form'),
    
    accountSelect: document.getElementById('account-select'),
    mainPanels: document.getElementById('main-panels'),
    transactionsPanel: document.getElementById('transactions-panel'),
    dividendsPanel: document.getElementById('dividends-panel'),
    
    // Tables
    holdingsTableBody: document.querySelector('#holdings-table tbody'),
    transactionsTableBody: document.querySelector('#transactions-table tbody'),
    dividendsTableBody: document.querySelector('#dividends-table tbody'),
    
    // Modals
    modalAccount: document.getElementById('modal-account'),
    modalTransaction: document.getElementById('modal-transaction'),
    modalDividend: document.getElementById('modal-dividend'),
    
    // Forms
    formAccount: document.getElementById('form-account'),
    formTransaction: document.getElementById('form-transaction'),
    formDividend: document.getElementById('form-dividend'),
    
    // Buttons
    btnNewAccount: document.getElementById('btn-new-account'),
    btnNewTransaction: document.getElementById('btn-new-transaction'),
    btnNewDividend: document.getElementById('btn-new-dividend'),
};

// --- Initialization ---
document.addEventListener("DOMContentLoaded", () => {
    if (authToken) {
        showDashboard();
        fetchAccounts();
    } else {
        if(el.loginCard) el.loginCard.style.display = 'block';
    }
    setupEventListeners();
});

// --- API Helpers ---
async function apiCall(endpoint, method = 'GET', body = null) {
    const headers = {
        'Content-Type': 'application/json',
    };
    if (authToken) {
        headers['Authorization'] = `Bearer ${authToken}`;
    }

    const config = { method, headers };
    if (body) config.body = JSON.stringify(body);

    try {
        const response = await fetch(`${API_BASE}${endpoint}`, config);
        const data = await response.text(); // Read as text first
        
        let parsedData = null;
        if(data) {
             try { parsedData = JSON.parse(data); } catch(e) {}
        }
        
        if (!response.ok) {
            const errorMsg = parsedData?.error || 'An error occurred';
            if (response.status === 401 && !endpoint.includes('/auth/')) {
                logout(); // Token expired or invalid
            }
            throw new Error(errorMsg);
        }
        return parsedData;
    } catch (error) {
        showNotification(error.message, 'error');
        throw error;
    }
}

function showNotification(message, type = 'success') {
    if(!el.notificationArea) return;
    const notif = document.createElement('div');
    notif.className = `notification ${type}`;
    notif.textContent = message;
    el.notificationArea.appendChild(notif);
    
    setTimeout(() => {
        notif.style.opacity = '0';
        setTimeout(() => notif.remove(), 300);
    }, 4000);
}

// --- Auth Flow ---
function showDashboard() {
    if(el.loginForm) el.loginForm.parentElement.parentElement.style.display = 'none'; // Hide auth container
    if(el.dashboardContent) el.dashboardContent.style.display = 'block';
    if(el.navMenu) el.navMenu.style.display = 'block';
    if(el.userInfo) el.userInfo.style.display = 'block';
    if(el.logoutBtn) el.logoutBtn.style.display = 'block';
}

function logout() {
    localStorage.removeItem("divapi_token");
    localStorage.removeItem("divapi_user_id");
    authToken = null;
    window.location.href = '/login';
}

// --- Data Fetching ---
async function fetchAccounts() {
    try {
        accounts = await apiCall('/accounts');
        renderAccountSelect();
        
        // Auto-select first account if exists and none selected
        if (accounts.length > 0 && !currentAccountId) {
            el.accountSelect.value = accounts[0].id;
            changeAccount();
        } else if (accounts.length === 0) {
            if(el.mainPanels) el.mainPanels.style.display = 'none';
            if(el.transactionsPanel) el.transactionsPanel.style.display = 'none';
            if(el.dividendsPanel) el.dividendsPanel.style.display = 'none';
        }
    } catch (e) { console.error('Failed to fetch accounts', e); }
}

async function fetchDashboardData() {
    if (!currentAccountId) return;
    try {
        const [holdings, transactions, dividends] = await Promise.all([
            apiCall(`/holdings?account_id=${currentAccountId}`),
            apiCall(`/transactions?account_id=${currentAccountId}`),
            apiCall(`/dividends?account_id=${currentAccountId}`)
        ]);
        
        renderHoldings(holdings);
        renderTransactions(transactions);
        renderDividends(dividends);
    } catch (e) { console.error('Failed to fetch dashboard data', e); }
}

function changeAccount() {
    currentAccountId = el.accountSelect.value;
    if (currentAccountId) {
        if(el.mainPanels) el.mainPanels.style.display = 'grid';
        if(el.transactionsPanel) el.transactionsPanel.style.display = 'block';
        if(el.dividendsPanel) el.dividendsPanel.style.display = 'block';
        fetchDashboardData();
    } else {
        if(el.mainPanels) el.mainPanels.style.display = 'none';
        if(el.transactionsPanel) el.transactionsPanel.style.display = 'none';
        if(el.dividendsPanel) el.dividendsPanel.style.display = 'none';
    }
}

// --- Rendering ---
function renderAccountSelect() {
    if(!el.accountSelect) return;
    const defaultOption = '<option value="">Select an account...</option>';
    const options = accounts.map(a => `<option value="${a.id}">${a.name}</option>`).join('');
    el.accountSelect.innerHTML = defaultOption + options;
    if (currentAccountId) el.accountSelect.value = currentAccountId;
}

function renderHoldings(holdings) {
    if(!el.holdingsTableBody) return;
    el.holdingsTableBody.innerHTML = '';
    
    if (holdings.length === 0) {
        el.holdingsTableBody.innerHTML = '<tr><td colspan="4" class="text-center text-muted">No holdings found</td></tr>';
        return;
    }

    holdings.forEach(h => {
        const tr = document.createElement('tr');
        const totalValue = (h.quantity * h.price).toFixed(2);
        tr.innerHTML = `
            <td><strong>${h.spolka}</strong></td>
            <td>${h.quantity}</td>
            <td>${parseFloat(h.price).toFixed(2)} zł</td>
            <td>${totalValue} zł</td>
        `;
        el.holdingsTableBody.appendChild(tr);
    });
}

function renderTransactions(transactions) {
    if(!el.transactionsTableBody) return;
    el.transactionsTableBody.innerHTML = '';
    
    if (transactions.length === 0) {
        el.transactionsTableBody.innerHTML = '<tr><td colspan="6" class="text-center text-muted">No transactions found</td></tr>';
        return;
    }

    // Sort by date desc
    transactions.sort((a,b) => new Date(b.data) - new Date(a.data));

    transactions.forEach(t => {
        const tr = document.createElement('tr');
        const typeClass = t.type === 'BUY' ? 'text-success' : 'text-danger';
        tr.innerHTML = `
            <td>${t.data}</td>
            <td class="${typeClass}"><strong>${t.type}</strong></td>
            <td>${t.spolka}</td>
            <td>${t.quantity}</td>
            <td>${parseFloat(t.price).toFixed(2)} zł</td>
            <td><button class="btn btn-danger-text btn-sm" onclick="deleteTransaction(${t.id})">Del</button></td>
        `;
        el.transactionsTableBody.appendChild(tr);
    });
}

function renderDividends(dividends) {
    if(!el.dividendsTableBody) return;
    el.dividendsTableBody.innerHTML = '';
    
    if (dividends.length === 0) {
        el.dividendsTableBody.innerHTML = '<tr><td colspan="4" class="text-center text-muted">No dividends found</td></tr>';
        return;
    }

    dividends.sort((a,b) => new Date(b.data) - new Date(a.data));

    dividends.forEach(d => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${d.data}</td>
            <td>${d.spolka}</td>
            <td class="text-success">+${parseFloat(d.amount).toFixed(2)} zł</td>
            <td><button class="btn btn-danger-text btn-sm" onclick="deleteDividend(${d.id})">Del</button></td>
        `;
        el.dividendsTableBody.appendChild(tr);
    });
}

// --- Deletions ---
async function deleteTransaction(id) {
    if(!confirm("Delete this transaction? This will also affect your holdings.")) return;
    try {
        await apiCall(`/transactions/${id}`, 'DELETE');
        showNotification('Transaction deleted');
        fetchDashboardData(); // Refresh all to get updated holdings
    } catch(e) {}
}

async function deleteDividend(id) {
    if(!confirm("Delete this dividend record?")) return;
    try {
        await apiCall(`/dividends/${id}`, 'DELETE');
        showNotification('Dividend deleted');
        fetchDashboardData();
    } catch(e) {}
}

// --- Event Listeners Setup ---
function setupEventListeners() {
    
    // Auth Forms
    if (el.loginForm) {
        el.loginForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const username = document.getElementById('login-username').value;
            const password = document.getElementById('login-password').value;
            try {
                const res = await apiCall('/auth/login', 'POST', { username, password });
                localStorage.setItem("divapi_token", res.access_token);
                localStorage.setItem("divapi_user_id", res.user_id);
                window.location.href = '/';
            } catch (error) { /* Handled in apiCall */ }
        });
    }

    if (el.registerForm) {
        el.registerForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const username = document.getElementById('reg-username').value;
            const email = document.getElementById('reg-email').value;
            const password = document.getElementById('reg-password').value;
            try {
                await apiCall('/auth/register', 'POST', { username, email, password });
                showNotification('Registration successful! Please login.');
                document.getElementById('show-login').click();
            } catch (error) { }
        });
    }

    if (el.logoutBtn) {
        el.logoutBtn.addEventListener('click', logout);
    }
    
    // Dashboard Controls
    if (el.accountSelect) {
        el.accountSelect.addEventListener('change', changeAccount);
    }

    // Modal Triggers
    const setupModal = (btnElem, modalElem) => {
        if(!btnElem || !modalElem) return;
        btnElem.addEventListener('click', () => { modalElem.classList.add('show'); });
        const closeBtn = modalElem.querySelector('.close-modal');
        if(closeBtn) {
            closeBtn.addEventListener('click', () => { modalElem.classList.remove('show'); });
        }
        window.addEventListener('click', (e) => {
            if (e.target === modalElem) modalElem.classList.remove('show');
        });
    };

    setupModal(el.btnNewAccount, el.modalAccount);
    setupModal(el.btnNewTransaction, el.modalTransaction);
    setupModal(el.btnNewDividend, el.modalDividend);

    // Form Submissions
    if (el.formAccount) {
        el.formAccount.addEventListener('submit', async (e) => {
            e.preventDefault();
            const name = document.getElementById('input-account-name').value;
            try {
                const newAcc = await apiCall('/accounts', 'POST', { name });
                showNotification('Account created successfully');
                el.modalAccount.classList.remove('show');
                el.formAccount.reset();
                await fetchAccounts();
                el.accountSelect.value = newAcc.id;
                changeAccount();
            } catch(e) {}
        });
    }

    if (el.formTransaction) {
        el.formTransaction.addEventListener('submit', async (e) => {
            e.preventDefault();
            if(!currentAccountId) { showNotification('Please select an account first', 'error'); return; }
            
            const payload = {
                account_id: parseInt(currentAccountId),
                type: document.getElementById('input-tx-type').value,
                spolka: document.getElementById('input-tx-symbol').value.toUpperCase(),
                data: document.getElementById('input-tx-date').value,
                quantity: parseInt(document.getElementById('input-tx-quantity').value),
                price: parseFloat(document.getElementById('input-tx-price').value),
            };

            try {
                await apiCall('/transactions', 'POST', payload);
                showNotification('Transaction recorded');
                el.modalTransaction.classList.remove('show');
                el.formTransaction.reset();
                fetchDashboardData();
            } catch(e) {}
        });
    }

    if (el.formDividend) {
        el.formDividend.addEventListener('submit', async (e) => {
            e.preventDefault();
            if(!currentAccountId) { showNotification('Please select an account first', 'error'); return; }
            
            const payload = {
                account_id: parseInt(currentAccountId),
                spolka: document.getElementById('input-div-symbol').value.toUpperCase(),
                data: document.getElementById('input-div-date').value,
                amount: parseFloat(document.getElementById('input-div-amount').value),
            };

            try {
                await apiCall('/dividends', 'POST', payload);
                showNotification('Dividend recorded');
                el.modalDividend.classList.remove('show');
                el.formDividend.reset();
                fetchDashboardData();
            } catch(e) {}
        });
    }
}
