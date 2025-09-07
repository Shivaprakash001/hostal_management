// Admin UPI Settings Management
class AdminUPIManager {
    constructor() {
        this.init();
    }

    init() {
        this.addUPIButtonToHeader();
        this.showButtonForAdmin();
    }

    addUPIButtonToHeader() {
        const header = document.querySelector('header');
        if (!header) return;

        const headerDiv = header.querySelector('div');
        if (!headerDiv) return;

        // Check if button already exists
        if (document.getElementById('admin-upi-btn')) return;

        const upiButton = document.createElement('button');
        upiButton.id = 'admin-upi-btn';
        upiButton.className = 'btn secondary';
        upiButton.innerHTML = '<i data-lucide="settings"></i> UPI Settings';
        upiButton.style.display = 'none';
        upiButton.onclick = () => window.open('/admin/upi', '_blank');

        // Insert before logout button
        const logoutBtn = document.getElementById('logout-btn');
        if (logoutBtn) {
            headerDiv.insertBefore(upiButton, logoutBtn);
        } else {
            headerDiv.appendChild(upiButton);
        }

        // Re-create icons
        if (window.lucide) {
            window.lucide.createIcons();
        }
    }

    showButtonForAdmin() {
        // Check if user is admin from localStorage or auth manager
        const isAdmin = this.checkIfAdmin();
        const upiButton = document.getElementById('admin-upi-btn');

        if (upiButton) {
            upiButton.style.display = isAdmin ? 'inline-block' : 'none';
        }
    }

    checkIfAdmin() {
        // Check from localStorage
        const userRole = localStorage.getItem('user_role');
        if (userRole && userRole.toLowerCase() === 'admin') {
            return true;
        }

        // Check from auth manager if available
        if (window.authManager && window.authManager.isAdmin) {
            return window.authManager.isAdmin();
        }

        return false;
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new AdminUPIManager();
});

// Also initialize when dashboard is shown (for login scenarios)
document.addEventListener('dashboardShown', () => {
    new AdminUPIManager();
});
