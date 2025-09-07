import { api } from './api.js';

// Simple message display function
function showMessage(message, type = 'info') {
    // Use alert for now, can be enhanced later with a proper notification system
    alert(message);
}

// Global variables
let currentUser = null;

// Initialize Mess panel
export function initMessPanel(user) {
    currentUser = user;

    // Show/hide admin controls based on user role
    const adminControls = document.getElementById('admin-mess-controls');
    const studentFeedback = document.getElementById('student-feedback');
    const messStats = document.getElementById('mess-stats');

    if (user.role === 'admin' || user.role === 'chef') {
        if (adminControls) adminControls.style.display = 'block';
        if (messStats) messStats.style.display = 'block';
        if (studentFeedback) studentFeedback.style.display = 'none';
    } else {
        if (adminControls) adminControls.style.display = 'none';
        if (messStats) messStats.style.display = 'none';
        if (studentFeedback) studentFeedback.style.display = 'block';
    }

    // Load initial data
    loadMessStats();
    // Ensure menu data is loaded for all users
    loadTodayMenu();
    loadMenuHistory();
    loadFeedbackHistory();

    // Setup event listeners
    setupEventListeners();
}

function setupEventListeners() {
    // Admin menu form
    const menuForm = document.getElementById('form-add-menu');
    if (menuForm) {
        menuForm.addEventListener('submit', handleAddMenu);
    }

    // Student feedback form
    const feedbackForm = document.getElementById('form-submit-feedback');
    if (feedbackForm) {
        feedbackForm.addEventListener('submit', handleSubmitFeedback);
    }

    // Menu filters
    const applyFiltersBtn = document.getElementById('apply-menu-filters');
    if (applyFiltersBtn) {
        applyFiltersBtn.addEventListener('click', handleMenuFilters);
    }
}

// Load mess statistics
async function loadMessStats() {
    try {
        const statsElement = document.getElementById('mess-stats');
        if (!statsElement) return;

        // Only load stats for admins/chefs
        if (statsElement.style.display === 'none') {
            // For students, ensure menu data is loaded and visible
            console.log('Loading menu data for students...');
            await loadTodayMenu();
            await loadMenuHistory();
            return;
        }

        // Get menu count - ensure no parameters are sent
        const menusResponse = await api('/menu/');
        const totalMenus = Array.isArray(menusResponse) ? menusResponse.length : 0;

        // Get today's menu count - ensure no parameters are sent
        const todayResponse = await api('/menu/today/');
        const todayMenus = Array.isArray(todayResponse) ? todayResponse.length : 0;

        // Get feedback count (simplified - would need a dedicated endpoint for this)
        const feedbackResponse = await api('/menu/feedback/');
        const totalFeedback = Array.isArray(feedbackResponse) ? feedbackResponse.length : 0;

        // Calculate average rating
        let totalRating = 0;
        let ratedFeedbacks = 0;
        if (Array.isArray(feedbackResponse)) {
            feedbackResponse.forEach(feedback => {
                if (feedback.rating) {
                    totalRating += feedback.rating;
                    ratedFeedbacks++;
                }
            });
        }
        const avgRating = ratedFeedbacks > 0 ? (totalRating / ratedFeedbacks).toFixed(1) : '0';

        // Update stats display
        document.getElementById('total-menus').textContent = totalMenus;
        document.getElementById('total-feedback').textContent = totalFeedback;
        document.getElementById('avg-rating').textContent = avgRating;
        document.getElementById('today-menus').textContent = todayMenus;

    } catch (error) {
        console.error('Error loading mess stats:', error);
        // For students, try to load menu data even if stats fail
        if (currentUser && currentUser.role !== 'admin' && currentUser.role !== 'chef') {
            console.log('Fallback: Loading menu data for students due to error...');
            try {
                await loadTodayMenu();
                await loadMenuHistory();
            } catch (menuError) {
                console.error('Error loading menu data for students:', menuError);
            }
        }
    }
}

// Load today's menu
async function loadTodayMenu() {
    const loadingElement = document.getElementById('today-menu-loading');
    const contentElement = document.getElementById('today-menu-content');

    try {
        console.log('Loading today\'s menu...');
        loadingElement.style.display = 'block';
        contentElement.innerHTML = '';

        const response = await api('/menu/today/');
        console.log('Today\'s menu response:', response);

        if (!Array.isArray(response) || response.length === 0) {
            contentElement.innerHTML = '<p class="muted">No menu available for today.</p>';
            return;
        }

        // Group menus by meal type
        const menuByType = {};
        response.forEach(menu => {
            if (!menuByType[menu.meal_type]) {
                menuByType[menu.meal_type] = [];
            }
            menuByType[menu.meal_type].push(menu);
        });

        console.log('Grouped menus:', menuByType);

        // Display menus
        Object.keys(menuByType).forEach(mealType => {
            const mealDiv = document.createElement('div');
            mealDiv.className = 'meal-section';
            mealDiv.innerHTML = `
                <h4>${mealType.charAt(0).toUpperCase() + mealType.slice(1)}</h4>
                <ul class="menu-items">
                    ${menuByType[mealType].map(menu => `
                        <li>${menu.items}</li>
                    `).join('')}
                </ul>
            `;
            contentElement.appendChild(mealDiv);
        });

        console.log('Today\'s menu loaded successfully');

    } catch (error) {
        console.error('Error loading today\'s menu:', error);
        contentElement.innerHTML = '<p class="error">Error loading today\'s menu. Please try again later.</p>';
    } finally {
        if (loadingElement) {
            loadingElement.style.display = 'none';
        }
    }
}

// Load menu history
async function loadMenuHistory(date = null, mealType = null) {
    const loadingElement = document.getElementById('menu-history-loading');
    const contentElement = document.getElementById('menu-history-content');

    try {
        console.log('Loading menu history...');
        loadingElement.style.display = 'block';
        contentElement.innerHTML = '';

        let url = '/menu/';
        const params = new URLSearchParams();
        if (date) params.append('date', date);
        if (mealType) params.append('meal_type', mealType);
        if (params.toString()) url += '?' + params.toString();

        console.log('Menu history URL:', url);
        const response = await api(url);
        console.log('Menu history response:', response);

        if (!Array.isArray(response) || response.length === 0) {
            contentElement.innerHTML = '<p class="muted">No menus found.</p>';
            return;
        }

        // Group by date
        const menusByDate = {};
        response.forEach(menu => {
            const dateKey = new Date(menu.date).toLocaleDateString();
            if (!menusByDate[dateKey]) {
                menusByDate[dateKey] = [];
            }
            menusByDate[dateKey].push(menu);
        });

        console.log('Grouped menus by date:', menusByDate);

        // Display menus grouped by date
        Object.keys(menusByDate).sort((a, b) => new Date(b) - new Date(a)).forEach(dateKey => {
            const dateDiv = document.createElement('div');
            dateDiv.className = 'date-section';
            dateDiv.innerHTML = `<h4>${dateKey}</h4>`;

            menusByDate[dateKey].forEach(menu => {
                const menuDiv = document.createElement('div');
                menuDiv.className = 'menu-item';

                // Check if student has already given feedback for this menu
                const hasUserFeedback = menu.feedbacks && menu.feedbacks.some(feedback =>
                    currentUser && currentUser.student_id && feedback.student_id === currentUser.student_id
                );

                const userFeedback = hasUserFeedback ?
                    menu.feedbacks.find(feedback =>
                        currentUser && currentUser.student_id && feedback.student_id === currentUser.student_id
                    ) : null;

                menuDiv.innerHTML = `
                    <div class="menu-header">
                        <span class="meal-type">${menu.meal_type.charAt(0).toUpperCase() + menu.meal_type.slice(1)}</span>
                        ${currentUser && (currentUser.role === 'admin' || currentUser.role === 'chef') ?
                            `<button class="btn small delete-menu-btn" data-menu-id="${menu.id}">Delete</button>` : ''}
                    </div>
                    <p class="menu-items">${menu.items}</p>
                    ${menu.feedbacks && menu.feedbacks.length > 0 ?
                        `<div class="feedback-summary">⭐ ${calculateAverageRating(menu.feedbacks).toFixed(1)} (${menu.feedbacks.length} reviews)</div>` : ''}

                    <!-- Comments Section -->
                    <div class="comments-section" data-menu-id="${menu.id}">
                        <div class="comments-header">
                            <span class="comments-toggle" onclick="toggleComments(this)">
                                💬 ${menu.feedbacks ? menu.feedbacks.length : 0} Comments
                                <span class="toggle-icon">▼</span>
                            </span>
                        </div>
                        <div class="comments-list" style="display: none;">
                            ${menu.feedbacks && menu.feedbacks.length > 0 ?
                                menu.feedbacks.map(feedback => `
                                    <div class="comment-item">
                                        <div class="comment-header">
                                            <span class="comment-author">${feedback.student_name || 'Anonymous'}</span>
                                            <span class="comment-date">${new Date(feedback.date).toLocaleDateString()}</span>
                                            ${currentUser && (currentUser.role === 'admin' || currentUser.role === 'chef' ||
                                              (currentUser.student_id && currentUser.student_id == feedback.student_id)) ?
                                                `<button class="btn small delete-comment-btn" data-feedback-id="${feedback.id}">×</button>` : ''}
                                        </div>
                                        ${feedback.rating ? `<div class="comment-rating">⭐ ${feedback.rating}/5</div>` : ''}
                                        ${feedback.comment ? `<div class="comment-text">${feedback.comment}</div>` : ''}
                                    </div>
                                `).join('') : '<div class="no-comments">No comments yet. Be the first to comment!</div>'}
                        </div>

                        <!-- Add Comment Form - Only for students -->
                        ${currentUser && currentUser.role === 'student' && currentUser.student_id ? `
                        <div class="add-comment-form">
                            <div class="rating-section">
                                <span class="rating-label">Rate this meal:</span>
                                <div class="rating-stars-input">
                                    <span class="star-input" data-rating="1">⭐</span>
                                    <span class="star-input" data-rating="2">⭐</span>
                                    <span class="star-input" data-rating="3">⭐</span>
                                    <span class="star-input" data-rating="4">⭐</span>
                                    <span class="star-input" data-rating="5">⭐</span>
                                </div>
                            </div>
                            <textarea class="new-comment-text" placeholder="Share your thoughts about this meal..." rows="2" maxlength="300"></textarea>
                            <div class="comment-form-actions">
                                <button class="btn small add-comment-btn" data-menu-id="${menu.id}">Post Comment</button>
                            </div>
                        </div>
                        ` : currentUser && currentUser.role !== 'student' ? `
                        <div class="comment-restriction-notice">
                            <p class="muted">Only students can post comments and ratings.</p>
                        </div>
                        ` : ''}
                    </div>
                `;

                // Add delete event listener for admin
                if (currentUser && (currentUser.role === 'admin' || currentUser.role === 'chef')) {
                    const deleteBtn = menuDiv.querySelector('.delete-menu-btn');
                    if (deleteBtn) {
                        deleteBtn.addEventListener('click', () => handleDeleteMenu(menu.id));
                    }
                }

                // Add comment functionality for all users
                const addCommentBtn = menuDiv.querySelector('.add-comment-btn');
                if (addCommentBtn) {
                    // Store selected rating for this menu
                    let selectedRating = 0;

                    // Add star rating event listeners
                    const starInputs = menuDiv.querySelectorAll('.star-input');
                    starInputs.forEach(star => {
                        star.addEventListener('click', (e) => {
                            selectedRating = parseInt(e.target.dataset.rating);
                            // Highlight selected stars
                            starInputs.forEach((s, index) => {
                                if (index < selectedRating) {
                                    s.classList.add('selected');
                                } else {
                                    s.classList.remove('selected');
                                }
                            });
                        });
                    });

                    addCommentBtn.addEventListener('click', () => {
                        const menuId = parseInt(addCommentBtn.dataset.menuId);
                        const commentTextarea = menuDiv.querySelector('.new-comment-text');
                        const comment = commentTextarea ? commentTextarea.value.trim() : '';

                        if (comment || selectedRating > 0) {
                            handleAddComment(menuId, comment, menu.meal_type, selectedRating);
                            commentTextarea.value = ''; // Clear the textarea
                            // Reset star selection
                            starInputs.forEach(star => star.classList.remove('selected'));
                            selectedRating = 0;
                        } else {
                            showMessage('Please enter a comment or select a rating.', 'error');
                        }
                    });
                }

                // Add delete comment event listeners
                const deleteCommentBtns = menuDiv.querySelectorAll('.delete-comment-btn');
                deleteCommentBtns.forEach(btn => {
                    btn.addEventListener('click', () => {
                        const feedbackId = parseInt(btn.dataset.feedbackId);
                        handleDeleteComment(feedbackId);
                    });
                });

                dateDiv.appendChild(menuDiv);
            });

            contentElement.appendChild(dateDiv);
        });

        console.log('Menu history loaded successfully');

    } catch (error) {
        console.error('Error loading menu history:', error);
        contentElement.innerHTML = '<p class="error">Error loading menu history. Please try again later.</p>';
    } finally {
        if (loadingElement) {
            loadingElement.style.display = 'none';
        }
    }
}

// Load feedback history
async function loadFeedbackHistory() {
    const loadingElement = document.getElementById('feedback-history-loading');
    const contentElement = document.getElementById('feedback-history-content');

    try {
        loadingElement.style.display = 'block';
        contentElement.innerHTML = '';

        let url = '/menu/feedback/';
        if (currentUser && currentUser.role === 'student' && currentUser.student_id) {
            url += `?student_id=${currentUser.student_id}`;
        }

        const response = await api(url);

        if (!Array.isArray(response) || response.length === 0) {
            contentElement.innerHTML = '<p class="muted">No feedback found.</p>';
            return;
        }

        // Display feedback
        response.forEach(feedback => {
            const feedbackDiv = document.createElement('div');
            feedbackDiv.className = 'feedback-item';
            feedbackDiv.innerHTML = `
                <div class="feedback-header">
                    <span class="student-name">${feedback.student_name || 'Anonymous'}</span>
                    <span class="rating">⭐ ${feedback.rating}/5</span>
                    <span class="date">${new Date(feedback.date).toLocaleDateString()}</span>
                    ${currentUser && (currentUser.role === 'admin' || currentUser.role === 'chef' ||
                      (currentUser.student_id && currentUser.student_id == feedback.student_id)) ?
                        `<button class="btn small delete-feedback-btn" data-feedback-id="${feedback.id}">Delete</button>` : ''}
                </div>
                <p class="meal-info">${feedback.meal_type.charAt(0).toUpperCase() + feedback.meal_type.slice(1)}</p>
                ${feedback.comment ? `<p class="comment">${feedback.comment}</p>` : ''}
            `;

            // Add delete event listener
            if (currentUser && (currentUser.role === 'admin' || currentUser.role === 'chef' ||
                (currentUser.student_id && currentUser.student_id == feedback.student_id))) {
                const deleteBtn = feedbackDiv.querySelector('.delete-feedback-btn');
                if (deleteBtn) {
                    deleteBtn.addEventListener('click', () => handleDeleteFeedback(feedback.id));
                }
            }

            contentElement.appendChild(feedbackDiv);
        });

    } catch (error) {
        console.error('Error loading feedback history:', error);
        contentElement.innerHTML = '<p class="error">Error loading feedback history.</p>';
    } finally {
        if (loadingElement) {
            loadingElement.style.display = 'none';
        }
    }
}



// Event handlers
async function handleAddMenu(event) {
    event.preventDefault();

    const formData = new FormData(event.target);
    const date = formData.get('menu_date');
    const mealType = formData.get('menu_meal_type');
    const items = formData.get('menu_items');

    // Validate required fields
    if (!date || !mealType || !items || !items.trim()) {
        showMessage('Please fill all fields correctly.', 'error');
        return;
    }

    // Normalize and validate data
    const menuData = {
        date: new Date(date).toISOString().split('T')[0], // ensure YYYY-MM-DD format
        meal_type: mealType.toLowerCase(), // ensure lowercase for enum
        items: items.trim()
    };

    try {
        await api('/menu/', { method: 'POST', body: menuData });
        showMessage('Menu added successfully!', 'success');
        event.target.reset();
        loadMessStats();
        loadMenuHistory();
        loadTodayMenu();
    } catch (error) {
        console.error('Menu creation error:', error);
        showMessage('Error adding menu: ' + error.message, 'error');
    }
}

async function handleSubmitFeedback(event) {
    event.preventDefault();

    if (!currentUser || !currentUser.student_id) {
        showMessage('Student information not found. Please contact admin.', 'error');
        return;
    }

    const formData = new FormData(event.target);
    const menuId = parseInt(formData.get('feedback_menu_id'));
    const rating = parseInt(formData.get('feedback_rating'));

    if (!menuId || isNaN(menuId)) {
        showMessage('Please select a valid menu item.', 'error');
        return;
    }

    if (!rating || rating < 1 || rating > 5) {
        showMessage('Please provide a valid rating between 1 and 5.', 'error');
        return;
    }

    // Get the selected menu to determine meal type
    let mealType = 'lunch'; // default
    try {
        const selectedMenu = await api(`/menu/${menuId}`);
        if (selectedMenu && selectedMenu.meal_type) {
            mealType = selectedMenu.meal_type;
        }
    } catch (error) {
        console.warn('Could not fetch menu details, using default meal type:', error);
    }

    const feedbackData = {
        student_id: currentUser.student_id,
        menu_id: menuId,
        date: new Date().toISOString(),
        meal_type: mealType.toLowerCase(), // ensure lowercase for enum
        rating: rating,
        comment: formData.get('feedback_comment') || null
    };

    try {
        await api('/menu/feedback', { method: 'POST', body: feedbackData });
        showMessage('Feedback submitted successfully!', 'success');
        event.target.reset();
        loadFeedbackHistory();
        loadMessStats();
    } catch (error) {
        console.error('Feedback submission error:', error);
        showMessage('Error submitting feedback: ' + error.message, 'error');
    }
}

function handleMenuFilters() {
    const dateFilter = document.getElementById('menu-date-filter').value;
    const typeFilter = document.getElementById('menu-type-filter').value;

    loadMenuHistory(dateFilter || null, typeFilter || null);
}

async function handleDeleteMenu(menuId) {
    if (!confirm('Are you sure you want to delete this menu?')) return;

    try {
        await api(`/menu/${menuId}`, { method: 'DELETE' });
        showMessage('Menu deleted successfully!', 'success');
        loadMessStats();
        loadMenuHistory();
        loadTodayMenu();
    } catch (error) {
        showMessage('Error deleting menu: ' + error.message, 'error');
    }
}

async function handleDeleteFeedback(feedbackId) {
    if (!confirm('Are you sure you want to delete this feedback?')) return;

    try {
        await api(`/menu/feedback/${feedbackId}`, { method: 'DELETE' });
        showMessage('Feedback deleted successfully!', 'success');
        loadFeedbackHistory();
        loadMessStats();
    } catch (error) {
        showMessage('Error deleting feedback: ' + error.message, 'error');
    }
}

// Toggle comments visibility
function toggleComments(element) {
    const commentsSection = element.closest('.comments-section');
    const commentsList = commentsSection.querySelector('.comments-list');
    const toggleIcon = element.querySelector('.toggle-icon');

    if (commentsList.style.display === 'none' || commentsList.style.display === '') {
        commentsList.style.display = 'block';
        toggleIcon.textContent = '▲';
    } else {
        commentsList.style.display = 'none';
        toggleIcon.textContent = '▼';
    }
}

// Handle adding new comments
async function handleAddComment(menuId, comment, mealType, rating = null) {
    if (!currentUser) {
        showMessage('Please log in to comment.', 'error');
        return;
    }

    // Only allow students to post comments (backend requires student_id)
    if (!currentUser.student_id) {
        showMessage('Only students can post comments.', 'error');
        return;
    }

    if ((!comment || !comment.trim()) && !rating) {
        showMessage('Please enter a comment or select a rating.', 'error');
        return;
    }

    // Rating is required by backend schema
    if (!rating || rating < 1 || rating > 5) {
        showMessage('Please select a rating between 1 and 5 stars.', 'error');
        return;
    }

    // Prepare comment data matching backend schema
    const commentData = {
        student_id: currentUser.student_id, // Required integer
        menu_id: menuId,
        date: new Date().toISOString(), // ISO string for datetime
        meal_type: mealType.toLowerCase(), // Must be enum value
        rating: rating, // Required integer 1-5
        comment: comment && comment.trim() ? comment.trim() : null
    };

    try {
        await api('/menu/feedback', { method: 'POST', body: commentData });
        showMessage('Comment posted successfully!', 'success');

        // Reload menu history to show the new comment
        loadMenuHistory();
        loadFeedbackHistory();
        loadMessStats();
    } catch (error) {
        console.error('Comment submission error:', error);
        showMessage('Error posting comment: ' + error.message, 'error');
    }
}

// Handle deleting comments
async function handleDeleteComment(feedbackId) {
    if (!confirm('Are you sure you want to delete this comment?')) return;

    try {
        await api(`/menu/feedback/${feedbackId}`, { method: 'DELETE' });
        showMessage('Comment deleted successfully!', 'success');

        // Reload menu history to reflect the deletion
        loadMenuHistory();
        loadFeedbackHistory();
        loadMessStats();
    } catch (error) {
        console.error('Comment deletion error:', error);
        showMessage('Error deleting comment: ' + error.message, 'error');
    }
}

// Handle quick feedback from inline rating stars
async function handleQuickFeedback(menuId, rating, mealType, comment = null) {
    if (!currentUser || !currentUser.student_id) {
        showMessage('Student information not found. Please contact admin.', 'error');
        return;
    }

    // Show confirmation with comment preview if provided
    let confirmMessage = `Rate this meal ${rating} star${rating !== 1 ? 's' : ''}?`;
    if (comment && comment.trim()) {
        confirmMessage += `\n\nComment: "${comment.trim()}"`;
    }

    const confirmSubmit = confirm(confirmMessage);
    if (!confirmSubmit) return;

    const feedbackData = {
        student_id: currentUser.student_id,
        menu_id: menuId,
        date: new Date().toISOString(),
        meal_type: mealType.toLowerCase(),
        rating: rating,
        comment: comment && comment.trim() ? comment.trim() : null
    };

    try {
        await api('/menu/feedback', { method: 'POST', body: feedbackData });
        showMessage('Feedback submitted successfully!', 'success');

        // Reload menu history to show the updated feedback
        loadMenuHistory();
        loadFeedbackHistory();
        loadMessStats();
    } catch (error) {
        console.error('Quick feedback submission error:', error);
        showMessage('Error submitting feedback: ' + error.message, 'error');
    }
}

// Utility functions
function calculateAverageRating(feedbacks) {
    if (!feedbacks || feedbacks.length === 0) return 0;
    const sum = feedbacks.reduce((total, feedback) => total + feedback.rating, 0);
    return sum / feedbacks.length;
}

// Export functions for use in main.js
export { loadTodayMenu, loadMenuHistory, loadFeedbackHistory };
