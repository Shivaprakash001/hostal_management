import { initTabs } from "./tabs.js?v=2";
import { loadRooms, initRooms } from "./rooms.js?v=2";
import { loadStudents, initStudents } from "./students.js?v=2";
import { initPayments } from "./payments.js?v=2";
import { authManager } from "./auth.js";

function showLoginForm() {
    document.getElementById('login-container').style.display = 'block';
    document.getElementById('dashboard').style.display = 'none';
    // Remove the line that sets the error message
}

function showDashboard() {
    document.getElementById('login-container').style.display = 'none';
    document.getElementById('dashboard').style.display = 'block';
    
    // Initialize dashboard modules
    const { loadRecentPayments } = initPayments();
    initTabs({
        rooms: loadRooms,
        students: loadStudents, // Change back to students
        payments: loadRecentPayments,
        agent: () => {},
    });

    // Load data
    loadRooms();
    initRooms();
    initStudents();
}

function setupLoginForm() {
    const loginForm = document.getElementById('login-form');
    loginForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const username = document.getElementById('login-username').value;
        const password = document.getElementById('login-password').value;
        // const errorElement = document.getElementById('login-error');

        const result = await authManager.login(username, password);
        if (result.success) {
            showDashboard();
        } else {
            console.error('Login failed:', result.error);
            // You can add error display logic here if needed
        }
    });
}

function setupLogout() {
    const logoutBtn = document.getElementById('logout-btn');
    logoutBtn.addEventListener('click', () => {
        authManager.logout();
        showLoginForm();
    });
}

document.addEventListener("DOMContentLoaded", () => {
    // Check if user is already authenticated
    if (authManager.isAuthenticated()) {
        showDashboard();
    } else {
        showLoginForm();
    }
    
    setupLoginForm();
    setupLogout();
});
