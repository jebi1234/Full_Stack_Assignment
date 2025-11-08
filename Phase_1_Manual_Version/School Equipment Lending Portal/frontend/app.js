// Global state
let token = null;
let userRole = null;
const API_URL = "http://127.0.0.1:8000";

// DOM Elements
const authContainer = document.getElementById('auth-container');
const studentDashboard = document.getElementById('student-dashboard');
const adminDashboard = document.getElementById('admin-dashboard');
const logoutButton = document.getElementById('logout-button');
const globalMessage = document.getElementById('global-message');

// --- Helper Functions ---

/**
 * Shows a success or error message
 * @param {string} message The text to show
 * @param {string} type 'success' or 'error'
 */
function showMessage(message, type = 'success') {
    globalMessage.textContent = message;
    globalMessage.className = type;
}

/**
 * Hides all main "page" containers
 */
function hideAllPages() {
    authContainer.style.display = 'none';
    studentDashboard.style.display = 'none';
    adminDashboard.style.display = 'none';
    logoutButton.style.display = 'none';
}

/**
 * Shows one main "page"
 * @param {string} pageId The ID of the container to show
 */
function showPage(pageId) {
    hideAllPages();
    document.getElementById(pageId).style.display = 'block';
    if (pageId !== 'auth-container') {
        logoutButton.style.display = 'block';
    }
}

/**
 * Helper for making authenticated API calls
 * @param {string} endpoint The API endpoint (e.g., "/users/me")
 * @param {object} options The fetch options (method, body, etc.)
 */
async function apiFetch(endpoint, options = {}) {
    options.headers = {
        ...options.headers,
        'Authorization': `Bearer ${token}`
    };
    
    // Add content-type header if body exists
    if (options.body) {
        options.headers['Content-Type'] = 'application/json';
    }

    const response = await fetch(API_URL + endpoint, options);

    if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'An API error occurred');
    }
    // Don't try to parse JSON for 204 No Content responses
    if (response.status === 204) {
        return null;
    }
    return response.json();
}

// --- Auth Logic ---

document.getElementById('show-register').addEventListener('click', () => {
    document.getElementById('login-card').style.display = 'none';
    document.getElementById('register-card').style.display = 'block';
});

document.getElementById('show-login').addEventListener('click', () => {
    document.getElementById('login-card').style.display = 'block';
    document.getElementById('register-card').style.display = 'none';
});

document.getElementById('register-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const username = document.getElementById('reg-username').value;
    const password = document.getElementById('reg-password').value;
    const role = document.getElementById('reg-role').value;

    try {
        const response = await fetch(API_URL + '/register/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password, role })
        });
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.detail || 'Failed to register');
        }
        
        showMessage('Registration successful! Please log in.', 'success');
        // Toggle back to login form
        document.getElementById('show-login').click();
        document.getElementById('register-form').reset();

    } catch (error) {
        showMessage(error.message, 'error');
    }
});

document.getElementById('login-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const username = document.getElementById('login-username').value;
    const password = document.getElementById('login-password').value;
    
    // The /token endpoint needs 'x-www-form-urlencoded' data
    const formData = new URLSearchParams();
    formData.append('username', username);
    formData.append('password', password);

    try {
        const response = await fetch(API_URL + '/token', {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: formData
        });
        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || 'Failed to log in');
        }

        token = data.access_token;
        localStorage.setItem('token', token); // Save token
        
        // We have a token, now find out who the user is
        await loadUserDashboard();

    } catch (error) {
        showMessage(error.message, 'error');
    }
});

logoutButton.addEventListener('click', () => {
    token = null;
    userRole = null;
    localStorage.removeItem('token');
    showMessage('You have been logged out.', 'success');
    showPage('auth-container');
});

async function loadUserDashboard() {
    try {
        // Get user role
        const user = await apiFetch('/users/me/');
        userRole = user.role;
        
        if (userRole === 'admin') {
            showPage('admin-dashboard');
            // Load all admin data
            loadAdminData();
        } else {
            showPage('student-dashboard');
            // Load all student data
            loadStudentData();
        }
        showMessage('Login successful!', 'success');
    } catch (error) {
        showMessage(error.message, 'error');
        // If token is bad, log out
        token = null;
        localStorage.removeItem('token');
        showPage('auth-container');
    }
}

// --- Student Dashboard Logic ---

async function loadStudentData() {
    loadStudentEquipment();
    loadStudentRequests();
}

async function loadStudentEquipment() {
    try {
        const equipment = await apiFetch('/equipment/');
        const tbody = document.getElementById('equipment-list-tbody');
        tbody.innerHTML = ''; // Clear old data
        if (equipment.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5">No equipment available.</td></tr>';
            return;
        }
        
        equipment.forEach(item => {
            tbody.innerHTML += `
                <tr>
                    <td>${item.name}</td>
                    <td>${item.category}</td>
                    <td>${item.available_quantity}</td>
                    <td>${item.status}</td>
                    <td>
                        <button 
                            class="btn" 
                            onclick="requestItem(${item.equipment_id})"
                            ${item.available_quantity <= 0 || item.status !== 'available' ? 'disabled' : ''}>
                            Request
                        </button>
                    </td>
                </tr>
            `;
        });
    } catch (error) {
        showMessage(error.message, 'error');
    }
}

async function loadStudentRequests() {
    try {
        const requests = await apiFetch('/requests/my/');
        const tbody = document.getElementById('my-requests-tbody');
        tbody.innerHTML = ''; // Clear old data
        if (requests.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5">You have no requests.</td></tr>';
            return;
        }
        
        requests.forEach(req => {
            tbody.innerHTML += `
                <tr>
                    <td>${req.request_id}</td>
                    <td>${req.equipment_id}</td>
                    <td>${req.status}</td>
                    <td>${req.expected_return_date}</td>
                    <td>
                        ${req.status === 'approved' ? 
                            `<button class="btn btn-success" onclick="returnItem(${req.request_id})">Return</button>` : ''
                        }
                        ${req.status !== 'returned' ?
                            `<button class="btn btn-danger" onclick="reportDamage(${req.equipment_id})">Report Damage</button>` : ''
                        }
                    </td>
                </tr>
            `;
        });
    } catch (error) {
        showMessage(error.message, 'error');
    }
}

async function requestItem(equipmentId) {
    // "Imperfect" date logic, just asks for 5 days from now
    const today = new Date();
    const borrowDate = today.toISOString().split('T')[0];
    today.setDate(today.getDate() + 5);
    const returnDate = today.toISOString().split('T')[0];
    
    try {
        await apiFetch('/requests/', {
            method: 'POST',
            body: JSON.stringify({
                equipment_id: equipmentId,
                borrow_date: borrowDate,
                expected_return_date: returnDate
            })
        });
        showMessage('Request submitted successfully!', 'success');
        // Refresh both lists
        loadStudentData();
    } catch (error) {
        showMessage(error.message, 'error');
    }
}

async function returnItem(requestId) {
    try {
        await apiFetch(`/requests/${requestId}/return`, { method: 'POST' });
        showMessage('Item returned successfully!', 'success');
        loadStudentData(); // Refresh both lists
    } catch (error) {
        showMessage(error.message, 'error');
    }
}

async function reportDamage(equipmentId) {
    const description = prompt("Please describe the damage:");
    if (!description) return;
    
    try {
        await apiFetch(`/equipment/${equipmentId}/report-damage`, {
            method: 'POST',
            body: JSON.stringify({
                equipment_id: equipmentId,
                description: description
            })
        });
        showMessage('Damage reported. Thank you.', 'success');
        loadStudentData();
    } catch (error) {
        showMessage(error.message, 'error');
    }
}

// --- Admin Dashboard Logic ---

// Tab switching logic
document.querySelectorAll('.admin-tab').forEach(tab => {
    tab.addEventListener('click', () => {
        // Remove 'active' from all tabs and content
        document.querySelectorAll('.admin-tab').forEach(t => t.classList.remove('active'));
        document.querySelectorAll('.admin-tab-content').forEach(c => c.classList.remove('active'));
        
        // Add 'active' to the clicked tab and its content
        tab.classList.add('active');
        document.getElementById(`tab-${tab.dataset.tab}`).classList.add('active');
        
        // Load data for the clicked tab
        switch (tab.dataset.tab) {
            case 'pending':
                loadAdminPending();
                break;
            case 'equipment':
                loadAdminInventory();
                break;
            case 'reports':
                loadAdminReports();
                break;
        }
    });
});

// This function loads ALL data for the admin dashboard at once
// This is a bit inefficient, which is "human"
function loadAdminData() {
    loadAdminPending();
    loadAdminInventory();
    loadAdminReports();
}

async function loadAdminPending() {
    try {
        const requests = await apiFetch('/requests/pending/');
        const tbody = document.getElementById('admin-pending-tbody');
        tbody.innerHTML = '';
        if (requests.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6">No pending requests.</td></tr>';
            return;
        }
        
        requests.forEach(req => {
            tbody.innerHTML += `
                <tr>
                    <td>${req.request_id}</td>
                    <td>${req.user_id}</td>
                    <td>${req.equipment_id}</td>
                    <td>${req.expected_return_date}</td>
                    <td>
                        <input type="date" class="form-input" id="return-date-${req.request_id}" value="${req.expected_return_date}">
                    </td>
                    <td>
                        <button class="btn btn-success" onclick="adminApprove(${req.request_id})">Approve</button>
                        <button class="btn btn-danger" onclick="adminReject(${req.request_id})">Reject</button>
                    </td>
                </tr>
            `;
        });
    } catch (error) {
        showMessage(error.message, 'error');
    }
}

async function adminApprove(requestId) {
    const returnDate = document.getElementById(`return-date-${requestId}`).value;
    if (!returnDate) {
        showMessage('Please set a return date.', 'error');
        return;
    }
    
    try {
        await apiFetch(`/requests/${requestId}/approve`, {
            method: 'POST',
            body: JSON.stringify({ expected_return_date: returnDate })
        });
        showMessage('Request approved.', 'success');
        loadAdminPending(); // Refresh list
    } catch (error) {
        showMessage(error.message, 'error');
    }
}

async function adminReject(requestId) {
    try {
        await apiFetch(`/requests/${requestId}/reject`, { method: 'POST' });
        showMessage('Request rejected.', 'success');
        loadAdminPending(); // Refresh list
    } catch (error) {
        showMessage(error.message, 'error');
    }
}

async function loadAdminInventory() {
    try {
        const equipment = await apiFetch('/equipment/');
        const tbody = document.getElementById('admin-inventory-tbody');
        tbody.innerHTML = '';
        
        equipment.forEach(item => {
            tbody.innerHTML += `
                <tr>
                    <td>${item.equipment_id}</td>
                    <td>${item.name}</td>
                    <td>${item.available_quantity} / ${item.total_quantity}</td>
                    <td>${item.status}</td>
                    <td>
                        <button class="btn btn-danger" onclick="adminDeleteItem(${item.equipment_id})">Delete</button>
                    </td>
                </tr>
            `;
        });
    } catch (error) {
        showMessage(error.message, 'error');
    }
}

document.getElementById('add-equipment-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const name = document.getElementById('add-name').value;
    const category = document.getElementById('add-category').value;
    const total_quantity = parseInt(document.getElementById('add-quantity').value, 10);
    
    try {
        await apiFetch('/equipment/', {
            method: 'POST',
            body: JSON.stringify({
                name: name,
                category: category,
                condition: "New", // Default to "New" for simplicity
                total_quantity: total_quantity
            })
        });
        showMessage('Equipment added.', 'success');
        loadAdminInventory(); // Refresh
        document.getElementById('add-equipment-form').reset();
    } catch (error) {
        showMessage(error.message, 'error');
    }
});

async function adminDeleteItem(equipmentId) {
    if (!confirm('Are you sure you want to delete this item?')) return;
    
    try {
        await apiFetch(`/equipment/${equipmentId}`, { method: 'DELETE' });
        showMessage('Equipment deleted.', 'success');
        loadAdminInventory(); // Refresh
    } catch (error) {
        showMessage(error.message, 'error');
    }
}

async function loadAdminReports() {
    // This is a bit "clunky" - it loads all 3 reports.
    // A "human" developer might do this to save time.
    try {
        const [overdue, repairs, analytics] = await Promise.all([
            apiFetch('/requests/overdue/'),
            apiFetch('/repairs/'),
            apiFetch('/analytics/usage')
        ]);

        // 1. Overdue
        const overdueTbody = document.getElementById('overdue-tbody');
        overdueTbody.innerHTML = '';
        overdue.forEach(item => {
            overdueTbody.innerHTML += `<tr><td>${item.request_id}</td><td>${item.user_id}</td><td>${item.equipment_id}</td><td>${item.status}</td></tr>`;
        });
        
        // 2. Repairs
        const repairsTbody = document.getElementById('repairs-tbody');
        repairsTbody.innerHTML = '';
        repairs.forEach(item => {
            repairsTbody.innerHTML += `
                <tr>
                    <td>${item.repair_id}</td>
                    <td>${item.equipment_id}</td>
                    <td>${item.description}</td>
                    <td>${item.repair_status}</td>
                    <td>
                        ${item.repair_status === 'pending' ? 
                            `<button class="btn" onclick="adminCompleteRepair(${item.repair_id})">Complete</button>` : ''
                        }
                    </td>
                </tr>
            `;
        });

        // 3. Analytics
        const analyticsTbody = document.getElementById('analytics-tbody');
        analyticsTbody.innerHTML = '';
        analytics.forEach(item => {
            analyticsTbody.innerHTML += `<tr><td>${item.equipment_id}</td><td>${item.name}</td><td>${item.request_count}</td></tr>`;
        });

    } catch (error) {
         showMessage(error.message, 'error');
    }
}

document.getElementById('check-overdue-btn').addEventListener('click', async () => {
    try {
        const data = await apiFetch('/requests/check-overdue/', { method: 'POST' });
        showMessage(`${data.length} item(s) marked as overdue.`, 'success');
        loadAdminReports(); // Refresh
    } catch (error) {
        showMessage(error.message, 'error');
    }
});

async function adminCompleteRepair(repairId) {
    try {
        await apiFetch(`/repairs/${repairId}/complete`, { method: 'POST' });
        showMessage('Repair marked as complete.', 'success');
        loadAdminReports(); // Refresh
    } catch (error) {
        showMessage(error.message, 'error');
    }
}

// --- Initial App Load ---
function init() {
    // Check if we have a token from a previous session
    const savedToken = localStorage.getItem('token');
    if (savedToken) {
        token = savedToken;
        loadUserDashboard();
    } else {
        // If no token, show the login page
        showPage('auth-container');
    }
}

// Run the app!
init();
