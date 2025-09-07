import { authManager } from "./auth.js";
import { api } from "./api.js";
import { initMessPanel, loadTodayMenu, loadMenuHistory, loadFeedbackHistory } from "./mess.js";

class StudentDashboard {
    constructor() {
        this.studentData = null;
        this.paymentsData = null;
    }

    async init() {
        // Check if user is authenticated and is a student
        if (!authManager.isAuthenticated() || authManager.role !== 'student') {
            window.location.href = '/';
            return;
        }

        // Load student data
        await this.loadStudentInfo();
        await this.loadPaymentData();

        // Initialize mess panel for students
        const user = authManager.getUser();
        if (user) {
            await initMessPanel(user);
        }

        this.displayData();
    }

    async loadStudentInfo() {
        try {
            const students = await api("/students/");
            if (students && students.length > 0) {
                this.studentData = students[0]; // Should only return one student for student role
            }
        } catch (error) {
            console.error("Error loading student info:", error);
            this.showError("Failed to load student information");
        }
    }

    async loadPaymentData() {
        try {
            this.paymentsData = await api("/payments/");
        } catch (error) {
            console.error("Error loading payment data:", error);
            this.showError("Failed to load payment information");
        }
    }

    displayData() {
        this.displayStudentInfo();
        this.displayPaymentSummary();
        this.displayPaymentHistory();
    }

    displayStudentInfo() {
        const loadingEl = document.getElementById("student-info-loading");
        const infoEl = document.getElementById("student-info");

        if (!this.studentData) {
            loadingEl.textContent = "No student information found.";
            return;
        }

        // Hide loading, show info
        loadingEl.style.display = "none";
        infoEl.style.display = "block";

        // Fill in student data
        document.getElementById("student-name").textContent = this.studentData.name || "-";
        document.getElementById("student-room").textContent = this.studentData.room_no || "Unassigned";
        document.getElementById("student-phone").textContent = this.studentData.phone_no || "-";
        document.getElementById("student-status").textContent = this.studentData.active ? "Active" : "Inactive";
    }

    displayPaymentSummary() {
        const loadingEl = document.getElementById("payment-summary-loading");
        const statsEl = document.getElementById("payment-stats");

        if (!this.paymentsData || this.paymentsData.length === 0) {
            loadingEl.textContent = "No payment records found.";
            return;
        }

        // Hide loading, show stats
        loadingEl.style.display = "none";
        statsEl.style.display = "grid";

        // Calculate summary
        let totalPaid = 0;
        let totalPending = 0;
        let paidCount = 0;
        let pendingCount = 0;

        this.paymentsData.forEach(payment => {
            if (payment.status === "Paid") {
                totalPaid += payment.amount;
                paidCount++;
            } else if (payment.status === "Pending") {
                totalPending += payment.amount;
                pendingCount++;
            }
        });

        // Update display
        document.getElementById("total-paid").textContent = `₹${totalPaid.toLocaleString()}`;
        document.getElementById("total-pending").textContent = `₹${totalPending.toLocaleString()}`;
        document.getElementById("paid-count").textContent = paidCount;
        document.getElementById("pending-count").textContent = pendingCount;
    }

    displayPaymentHistory() {
        const loadingEl = document.getElementById("payment-history-loading");
        const tableEl = document.getElementById("payment-history-table");
        const tbodyEl = document.getElementById("payment-history-body");

        if (!this.paymentsData || this.paymentsData.length === 0) {
            loadingEl.textContent = "No payment history found.";
            return;
        }

        // Hide loading, show table
        loadingEl.style.display = "none";
        tableEl.style.display = "block";

        // Clear existing rows
        tbodyEl.innerHTML = "";

        // Sort payments by date (newest first)
        const sortedPayments = [...this.paymentsData].sort((a, b) =>
            new Date(b.date) - new Date(a.date)
        );

        // Add payment rows
        sortedPayments.forEach(payment => {
            const row = document.createElement("tr");

            // Format month/year
            const monthNames = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                              "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
            const monthYear = `${monthNames[payment.month - 1]}/${payment.year}`;

            // Format date
            const paymentDate = new Date(payment.date).toLocaleDateString();

            // Status badge with verification info
            let statusText = payment.status;
            let statusClass = payment.status === "Paid" ? "success" :
                            payment.status === "Pending" ? "warning" : "danger";

            // Add verification status for online payments
            if (payment.payment_method === "Online" && payment.status === "Pending") {
                statusText = "Pending Verification";
                statusClass = "info";
            }

            const statusBadge = `<span class="badge ${statusClass}">${statusText}</span>`;

            // Actions based on payment status
            let actions = "";
            if (payment.status === "Paid") {
                actions = `<button class="btn success" onclick="downloadReceipt(${payment.id})">Download Receipt</button>`;
            } else if (payment.status === "Pending" && payment.payment_method === "Online") {
                actions = `<span class="text-muted">Awaiting Admin Verification</span>`;
            } else if (payment.status === "Pending") {
                actions = `<button class="btn primary" onclick="markAsPaid(${payment.id})">Mark as Paid</button>`;
            } else {
                actions = "N/A";
            }

            row.innerHTML = `
                <td>${monthYear}</td>
                <td>₹${payment.amount.toLocaleString()}</td>
                <td>${statusBadge}</td>
                <td>${payment.payment_method}</td>
                <td>${paymentDate}</td>
                <td>${actions}</td>
            `;

            tbodyEl.appendChild(row);
        });
    }

    showError(message) {
        // Simple error display - could be enhanced
        alert(message);
    }
}

// Global functions for button actions
window.markAsPaid = async function(paymentId) {
    if (!confirm("Mark this payment as paid?")) return;

    try {
        const result = await api(`/payments/${paymentId}/mark-paid`, {
            method: "POST",
            body: { payment_method: "Online" } // Default method
        });

        if (result) {
            alert("Payment marked as paid successfully!");
            // Reload the dashboard
            window.location.reload();
        }
    } catch (error) {
        alert("Failed to mark payment as paid: " + error.message);
    }
};

window.downloadReceipt = async function(paymentId) {
    try {
        // Create a temporary link to download the receipt
        const link = document.createElement("a");
        link.href = `/payments/${paymentId}/receipt`;
        link.download = `receipt_${paymentId}.pdf`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    } catch (error) {
        alert("Failed to download receipt: " + error.message);
    }
};

// Initialize dashboard when DOM is loaded
document.addEventListener("DOMContentLoaded", () => {
    const dashboard = new StudentDashboard();
    dashboard.init();
});
