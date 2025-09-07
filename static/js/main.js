import { initTabs } from "./tabs.js?v=2";
import { loadRooms, initRooms } from "./rooms.js?v=2";
import { loadStudents, initStudents } from "./students.js?v=2";
import { initPayments } from "./payments.js?v=2";
import { authManager } from "./auth.js";
import { initAgentUI } from "./agent.js";
import { initMessPanel } from "./mess.js";

function showLoginForm() {
    document.getElementById('login-container').style.display = 'block';
    document.getElementById('dashboard').style.display = 'none';
    // Remove the line that sets the error message
}

function showDashboard() {
    document.getElementById('login-container').style.display = 'none';
    document.getElementById('dashboard').style.display = 'block';

    const isStudent = authManager.role.toLowerCase() === 'student';
    const isAdmin = authManager.isAdmin();

    // Centralize payment initialization to avoid duplicate setup
    const { loadPayments } = initPayments();

    if (isStudent) {
        // For students, load their payments immediately
        loadPayments();
    } else {
        // Initialize dashboard modules for admin/other roles
        initTabs({
            rooms: loadRooms,
            students: loadStudents,
            payments: loadPayments,
            mess: () => {
                const user = authManager.getUser();
                if (user) {
                    initMessPanel(user);
                } else {
                    console.error('User data not available for mess panel initialization');
                }
            },
            agent: initAgentUI,
        });
        // Load initial data for admin
        if (isAdmin) {
            loadRooms();
            initRooms();
            initStudents();
        }
    }

    // Configure UI based on role
    configureUIBasedOnRole(isAdmin, isStudent);
}

document.addEventListener("DOMContentLoaded", () => {
    if (authManager.isAuthenticated()) {
        const isStudent = authManager.role.toLowerCase() === 'student';
        const onStudentPage = window.location.pathname === '/student';

        if (isStudent && !onStudentPage) {
            // Student on admin page, redirect.
            window.location.href = '/student';
        } else if (!isStudent && onStudentPage) {
            // Admin on student page, redirect.
            window.location.href = '/';
        } else {
            // User is authenticated and on the correct page.
            showDashboard();
            setupLogout();
        }
    } else {
        // Not authenticated.
        showLoginForm();
        setupLoginForm();
    }
});

function configureUIBasedOnRole(isAdmin, isStudent) {
    // Show/hide admin buttons
    const adminButtons = document.getElementById('admin-buttons');
    if (adminButtons) {
        adminButtons.style.display = isAdmin ? 'inline-block' : 'none';
    }

    // Hide admin-only elements for non-admin users
    const adminElements = document.querySelectorAll('.admin-only');
    adminElements.forEach(el => {
        el.style.display = isAdmin ? 'block' : 'none';
    });

    // Hide student-only elements for non-students
    const studentElements = document.querySelectorAll('.student-only');
    studentElements.forEach(el => {
        el.style.display = isStudent ? 'block' : 'none';
    });

    // Hide tabs based on role
    const tabs = document.querySelectorAll('.tab-btn');
    tabs.forEach(tab => {
        const tabName = tab.getAttribute('data-tab');
        if (isStudent && (tabName === 'rooms' || tabName === 'students')) {
            tab.style.display = 'none';
        }
    });

    // Update header based on role
    const header = document.querySelector('header h1');
    if (isStudent) {
        header.textContent = 'Student Dashboard';
    } else if (isAdmin) {
        header.textContent = 'Admin Dashboard';
    }
}

function setupLoginForm() {
    const loginForm = document.getElementById('login-form');
    const errorElement = document.getElementById('login-error');
    loginForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const username = document.getElementById('login-username').value;
        const password = document.getElementById('login-password').value;

        // Clear previous error
        errorElement.textContent = '';

        const result = await authManager.login(username, password);
        if (result.success) {
            // After login, redirect to the correct page.
            // The DOMContentLoaded handler on the next page load will show the dashboard.
            const isStudent = authManager.role.toLowerCase() === 'student';
            if (isStudent) {
                window.location.href = '/student';
            } else {
                window.location.href = '/';
            }
        } else {
            console.error('Login failed:', result.error);
            errorElement.textContent = result.error;
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
