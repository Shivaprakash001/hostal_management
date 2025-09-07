import { api, money } from "./api.js";

const STATUS_OPTIONS = ["Pending", "Paid", "Failed"];
const PAYMENT_METHODS = ["Cash", "Online"];
let currentlyEditing = null;
let currentUserRole = null;
let currentStudentId = null;

export function initPayments() {
  const container = document.getElementById("panel-payments");
  const paymentsList = container.querySelector("#payments-list");
  const paymentsLoading = container.querySelector("#payments-loading");
  const formAddPayment = document.getElementById("form-add-payment");
  const lookupInput = document.getElementById("lookup_student_name");
  const lookupBtn = document.getElementById("btn-lookup");

  // Initialize based on user role
  initializeUserInterface();

  // Check if elements exist before adding event listeners
  if (formAddPayment) {
    formAddPayment.addEventListener("submit", async e => {
      e.preventDefault();
      const studentName = formAddPayment.payment_student_name.value.trim();
      const amount = parseFloat(formAddPayment.payment_amount.value);
      const month = parseInt(formAddPayment.payment_month.value);
      const year = parseInt(formAddPayment.payment_year.value);
      const paymentMethod = formAddPayment.payment_method.value;
      const status = formAddPayment.payment_status.value;

      if (!studentName || Number.isNaN(amount) || !month || !year) {
        return alert("Please fill all required fields.");
      }

      try {
        // First get the student by name to retrieve the student ID
        const student = await api(`/students/by-name/${encodeURIComponent(studentName)}`);
        const studentId = student.id;

        // Prepare payment data with correct enum values
        const paymentData = {
          student_id: studentId,
          amount: amount,
          status: status, // This should match PaymentStatus enum values
          month: month,
          year: year,
          payment_method: paymentMethod // This should match PaymentMethod enum values
        };

        console.log("Sending payment data:", paymentData);

        // Now add the payment using the student ID
        const result = await api(`/payments`, { 
          method: "POST", 
          body: paymentData
        });
        
        console.log("Payment created successfully:", result);
        formAddPayment.reset();
        await loadPayments();
        await loadPaymentStats();
        alert("Payment created successfully!");
      } catch (err) {
        console.error("Payment creation error:", err);
        alert(`Error adding payment: ${err.message}`);
      }
    });
  }

      if (lookupBtn) {
        lookupBtn.addEventListener("click", async () => {
          const studentName = lookupInput.value.trim();
          if (!studentName) return alert("Enter a student name.");
      try {
          const student = await api(`/students/by-name/${encodeURIComponent(studentName)}`);
          const studentId = student.id;
          await loadPaymentsByStudent(studentId);
      } catch (err) {
        alert(`Student not found: ${err.message}`);
      }
    });
  }

  // Admin controls event listeners
  setupAdminControls();
  
  // Initial load
  loadPayments();
  if (currentUserRole === 'admin') {
    loadPaymentStats();
  }
  if (currentUserRole === 'student') {
    loadStudentPayments();
  }

  // expose loaders for tabs
  return { loadPayments, loadPaymentsByStudent };
}

function initializeUserInterface() {
  // Determine user role from auth
  const userRole = getCurrentUserRole();
  currentUserRole = userRole;
  
  const adminControls = document.getElementById("admin-controls");
  const studentPortal = document.getElementById("student-payment-portal");
  const paymentStats = document.getElementById("payment-stats");
  const paymentLookup = document.getElementById("payment-lookup");
  const addPaymentForm = document.getElementById("form-add-payment");

  if (userRole === 'admin') {
    // Show admin interface
    if (adminControls) adminControls.style.display = 'block';
    if (paymentStats) paymentStats.style.display = 'block';
    if (paymentLookup) paymentLookup.style.display = 'block';
    if (addPaymentForm) addPaymentForm.style.display = 'block';
    if (studentPortal) studentPortal.style.display = 'none';
  } else if (userRole === 'student') {
    // Show student interface
    if (studentPortal) studentPortal.style.display = 'block';
    if (adminControls) adminControls.style.display = 'none';
    if (paymentStats) paymentStats.style.display = 'none';
    if (paymentLookup) paymentLookup.style.display = 'none';
    if (addPaymentForm) addPaymentForm.style.display = 'none';
    
    // Get current student ID
    currentStudentId = getCurrentStudentId();
  } else {
    // Default view (agent/other roles)
    if (adminControls) adminControls.style.display = 'none';
    if (studentPortal) studentPortal.style.display = 'none';
    if (paymentStats) paymentStats.style.display = 'none';
    if (paymentLookup) paymentLookup.style.display = 'block';
    if (addPaymentForm) addPaymentForm.style.display = 'block';
  }
}

function setupAdminControls() {
  const applyFiltersBtn = document.getElementById("apply-payment-filters");
  const clearFiltersBtn = document.getElementById("clear-payment-filters");
  const exportCsvBtn = document.getElementById("export-csv");

  if (applyFiltersBtn) {
    applyFiltersBtn.addEventListener("click", async () => {
      await loadPayments();
    });
  }

  if (clearFiltersBtn) {
    clearFiltersBtn.addEventListener("click", () => {
      document.getElementById("filter-month").value = "";
      document.getElementById("filter-year").value = "";
      document.getElementById("filter-status").value = "";
      loadPayments();
    });
  }

  if (exportCsvBtn) {
    exportCsvBtn.addEventListener("click", async () => {
      await exportPaymentsToCsv();
    });
  }
}

async function loadPaymentStats() {
  try {
    const stats = await api("/payments/stats/summary");
    
    document.getElementById("total-payments").textContent = stats.total_payments;
    document.getElementById("paid-payments").textContent = stats.paid_payments;
    document.getElementById("pending-payments").textContent = stats.pending_payments;
    document.getElementById("total-collected").textContent = money(stats.total_collected);
    document.getElementById("total-pending-amount").textContent = money(stats.total_pending);
  } catch (err) {
    console.error("Error loading payment stats:", err);
  }
}

async function loadStudentPayments() {
  if (!currentStudentId) return;
  
  try {
    const payments = await api(`/payments/student/id/${currentStudentId}`);
    renderStudentPaymentPortal(payments);
  } catch (err) {
    console.error("Error loading student payments:", err);
  }
}

function renderStudentPaymentPortal(payments) {
  const portal = document.getElementById("student-payment-portal");
  const dueInfo = document.getElementById("payment-due-info");
  
  if (!portal || !dueInfo) return;

  if (!payments || payments.length === 0) {
    dueInfo.innerHTML = "<p>No payment records found.</p>";
    return;
  }

  let html = "";
  payments.forEach(payment => {
    const isPending = payment.status === "Pending";
    const monthName = getMonthName(payment.month);
    
    html += `
      <div class="payment-due-item">
        <div class="payment-info">
          <div><strong>${monthName} ${payment.year}</strong></div>
          <div>Amount: ${money(payment.amount)}</div>
          <div>Status: <span class="status-badge status-${payment.status.toLowerCase()}">${payment.status}</span></div>
          <div class="muted">Room: ${payment.room_id || 'Not assigned'}</div>
        </div>
        <div class="payment-actions">
          ${isPending ? `
            <button class="btn btn-small primary" onclick="markPaymentAsPaid(${payment.id})">
              Pay Now
            </button>
          ` : `
            <button class="btn btn-small" onclick="downloadReceipt(${payment.id})">
              Download Receipt
            </button>
          `}
        </div>
      </div>
    `;
  });
  
  dueInfo.innerHTML = html;
}

async function markPaymentAsPaid(paymentId) {
  try {
    const paymentMethod = confirm("Select payment method:\nOK = Online\nCancel = Cash") ? "Online" : "Cash";
    
    await api(`/payments/${paymentId}/mark-paid`, {
      method: "POST",
      body: { payment_method: paymentMethod }
    });
    
    alert("Payment marked as paid successfully!");
    await loadStudentPayments();
  } catch (err) {
    alert(`Error marking payment as paid: ${err.message}`);
  }
}

async function downloadReceipt(paymentId) {
  try {
    const response = await fetch(`/payments/${paymentId}/receipt`);
    if (response.ok) {
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `receipt_${paymentId}.pdf`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } else {
      alert("Error downloading receipt");
    }
  } catch (err) {
    alert(`Error downloading receipt: ${err.message}`);
  }
}

async function exportPaymentsToCsv() {
  try {
    const month = document.getElementById("filter-month").value;
    const year = document.getElementById("filter-year").value;
    const status = document.getElementById("filter-status").value;
    
    let url = "/payments/export/csv?";
    if (month) url += `month=${month}&`;
    if (year) url += `year=${year}&`;
    if (status) url += `status=${status}&`;
    
    const response = await fetch(url);
    if (response.ok) {
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = "payments_export.csv";
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } else {
      alert("Error exporting CSV");
    }
  } catch (err) {
    alert(`Error exporting CSV: ${err.message}`);
  }
}

async function loadPayments() {
  const paymentsLoading = document.getElementById("payments-loading");
  const paymentsList = document.getElementById("payments-list");
  
  if (!paymentsLoading || !paymentsList) return;

  paymentsLoading.textContent = "Loading payments…";
  
  try {
    const month = document.getElementById("filter-month")?.value;
    const year = document.getElementById("filter-year")?.value;
    const status = document.getElementById("filter-status")?.value;
    
    let url = "/payments/";
    const params = new URLSearchParams();
    if (month) params.append("month", month);
    if (year) params.append("year", year);
    if (status) params.append("status", status);
    
    if (params.toString()) {
      url += "?" + params.toString();
    }
    
    const items = await api(url);
    paymentsLoading.textContent = "";
    renderPayments(items);
  } catch (err) {
    paymentsLoading.textContent = `Error loading payments: ${err.message}`;
  }
}

async function loadPaymentsByStudent(studentId) {
  if (!studentId || Number.isNaN(studentId)) return;
  
  const paymentsLoading = document.getElementById("payments-loading");
  const paymentsList = document.getElementById("payments-list");
  
  if (!paymentsLoading || !paymentsList) return;

  paymentsLoading.textContent = "Loading payments…";
  
  try {
    const items = await api(`/payments/student/id/${studentId}`);
    paymentsLoading.textContent = "";
    renderPayments(items, studentId);
  } catch (err) {
    paymentsLoading.textContent = `Error loading payments: ${err.message}`;
  }
}

  function renderPayments(items, studentId = null) {
  const paymentsList = document.getElementById("payments-list");
  if (!paymentsList) return;

    paymentsList.innerHTML = "";
  
    if (!items || !items.length) {
      paymentsList.innerHTML = "<li class='muted'>No payments found.</li>";
      return;
    }

    let total = 0;
    items.forEach(p => total += Number(p.amount || 0));

    const header = document.createElement("li");
    header.className = "muted";
    header.textContent = studentId
    ? `Payments for Student ID ${studentId} — Total: ${money(total)}`
    : `All Payments — Total: ${money(total)}`;
    paymentsList.appendChild(header);

    items.forEach(p => {
      const li = document.createElement("li");
    li.className = "payment-item";

    const monthName = getMonthName(p.month);
    const statusClass = `status-${p.status.toLowerCase()}`;

      li.innerHTML = `
      <div class="payment-header">
        <div>
          <strong>${p.student_name || `Student ${p.student_id}`}</strong>
          <span class="status-badge ${statusClass}">${p.status}</span>
        </div>
        <div class="muted">${monthName} ${p.year} - ${money(p.amount)}</div>
          </div>
      <div class="payment-details">
        <div><strong>Amount:</strong> ${money(p.amount)}</div>
        <div><strong>Room:</strong> ${p.room_no || p.room_id}</div>
        <div><strong>Method:</strong> ${p.payment_method}</div>
        <div><strong>Transaction ID:</strong> ${p.transaction_id}</div>
        <div><strong>Date:</strong> ${new Date(p.date).toLocaleString()}</div>
        </div>
        <div class="payment-actions">
        ${currentUserRole === 'admin' ? `
          <button class="btn btn-small btn-edit">Edit</button>
          <button class="btn btn-small btn-save" style="display: none;">Save</button>
          <button class="btn btn-small btn-cancel" style="display: none;">Cancel</button>
          <button class="btn btn-small btn-danger btn-delete" data-payment-id="${p.id}">Delete</button>
        ` : ''}
        ${p.status === 'Paid' ? `
          <button class="btn btn-small" onclick="downloadReceipt(${p.id})">Download Receipt</button>
        ` : ''}
        </div>
      `;

      paymentsList.appendChild(li);

    // Add click event listener to payment header for expand/collapse
    const paymentHeader = li.querySelector('.payment-header');
    if (paymentHeader) {
      paymentHeader.addEventListener('click', () => {
        li.classList.toggle('expanded');
      });
    }

    // Add event listeners for admin actions
    if (currentUserRole === 'admin') {
      setupPaymentItemEventListeners(li, p);
    }
  });
}

function setupPaymentItemEventListeners(li, payment) {
    const editBtn = li.querySelector(".btn-edit");
    const saveBtn = li.querySelector(".btn-save");
    const cancelBtn = li.querySelector(".btn-cancel");
    const deleteBtn = li.querySelector(".btn-delete");
    const paymentDetails = li.querySelector(".payment-details");

    if (editBtn) {
        editBtn.addEventListener("click", () => {
            if (currentlyEditing) return;
            currentlyEditing = li;
            li.classList.add("editing");

            // Create input fields for editing
            const editForm = document.createElement("div");
            editForm.className = "payment-edit-form";
            editForm.innerHTML = `
                <div class="edit-field">
                    <label>Amount:</label>
                    <input type="number" class="edit-amount" value="${payment.amount}" step="0.01" min="0">
                </div>
                <div class="edit-field">
                    <label>Month:</label>
                    <select class="edit-month">
                        ${Array.from({length: 12}, (_, i) => `
                            <option value="${i + 1}" ${i + 1 === payment.month ? 'selected' : ''}>
                                ${getMonthName(i + 1)}
                            </option>
                        `).join('')}
                    </select>
                </div>
                <div class="edit-field">
                    <label>Year:</label>
                    <input type="number" class="edit-year" value="${payment.year}" min="2020" max="2030">
                </div>
                <div class="edit-field">
                    <label>Status:</label>
                    <select class="edit-status">
                        ${STATUS_OPTIONS.map(status => `
                            <option value="${status}" ${status === payment.status ? 'selected' : ''}>
                                ${status}
                            </option>
                        `).join('')}
                    </select>
                </div>
                <div class="edit-field">
                    <label>Payment Method:</label>
                    <select class="edit-method">
                        ${PAYMENT_METHODS.map(method => `
                            <option value="${method}" ${method === payment.payment_method ? 'selected' : ''}>
                                ${method}
                            </option>
                        `).join('')}
                    </select>
                </div>
            `;

            // Hide the original details and show the edit form
            paymentDetails.style.display = "none";
            paymentDetails.parentNode.insertBefore(editForm, paymentDetails.nextSibling);

            // Enable editing mode
            editBtn.style.display = "none";
            saveBtn.style.display = "inline-block";
            cancelBtn.style.display = "inline-block";
            deleteBtn.style.display = "none";
        });
    }

    if (saveBtn) {
        saveBtn.addEventListener("click", async () => {
            try {
                const editForm = li.querySelector(".payment-edit-form");
                const amount = parseFloat(editForm.querySelector(".edit-amount").value);
                const month = parseInt(editForm.querySelector(".edit-month").value);
                const year = parseInt(editForm.querySelector(".edit-year").value);
                const status = editForm.querySelector(".edit-status").value;
                const paymentMethod = editForm.querySelector(".edit-method").value;

                // Validate inputs
                if (isNaN(amount) || amount <= 0) {
                    alert("Please enter a valid amount");
                    return;
                }
                if (isNaN(month) || month < 1 || month > 12) {
                    alert("Please enter a valid month (1-12)");
                    return;
                }
                if (isNaN(year) || year < 2020 || year > 2030) {
                    alert("Please enter a valid year (2020-2030)");
                    return;
                }

                // Update payment
                await api(`/payments/${payment.id}`, {
                    method: "PUT",
                    body: {
                        amount: amount,
                        month: month,
                        year: year,
                        status: status,
                        payment_method: paymentMethod
                    }
                });

                alert("Payment updated successfully!");
                await loadPayments();
                await loadPaymentStats();
                
                currentlyEditing = null;
                li.classList.remove("editing");
            } catch (err) {
                alert(`Error updating payment: ${err.message}`);
            }
        });
    }

    if (cancelBtn) {
        cancelBtn.addEventListener("click", () => {
            // Remove edit form and show original details
            const editForm = li.querySelector(".payment-edit-form");
            if (editForm) {
                editForm.remove();
            }
            paymentDetails.style.display = "block";
            
            currentlyEditing = null;
            li.classList.remove("editing");
            
            // Reset to view mode
            editBtn.style.display = "inline-block";
            saveBtn.style.display = "none";
            cancelBtn.style.display = "none";
            deleteBtn.style.display = "inline-block";
        });
    }

    if (deleteBtn) {
        deleteBtn.addEventListener("click", async () => {
            if (!confirm(`Delete payment ID ${payment.id}?`)) return;
            
            try {
                await api(`/payments/${payment.id}`, { method: "DELETE" });
                alert("Payment deleted.");
                await loadPayments();
                await loadPaymentStats();
            } catch (err) {
                alert(`Error deleting payment: ${err.message}`);
            }
        });
    }
}

function getMonthName(month) {
  const months = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
  ];
  return months[month - 1] || month;
}

function getCurrentUserRole() {
  // This should be implemented based on your auth system
  // For now, return 'admin' as default
  return 'admin';
}

function getCurrentStudentId() {
  // This should be implemented based on your auth system
  // For now, return null
  return null;
}

// UPI Payment functions
async function createOrder(student_id, amount, month, year) {
  const res = await fetch('/payments/create-order', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ student_id, amount, month, year })
  });
  return res.json();
}

async function verifyPayment(order_id, student_id, month, amount) {
  const res = await fetch('/payments/verify-payment', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      razorpay_order_id: order_id,
      razorpay_payment_id: "mock_upi_txn",
      razorpay_signature: "mock_sig",
      student_id: student_id,
      month: month,
      amount: amount
    })
  });
  return res.json();
}

// Initialize UPI payment interface
function initUPIPayment() {
  const payBtn = document.getElementById('payBtn');
  if (payBtn) {
    payBtn.addEventListener('click', async () => {
      const student_id = parseInt(document.getElementById('student_id').value);
      const month = document.getElementById('month').value;
      const amount = parseFloat(document.getElementById('amount').value);
      const payment_method = document.getElementById('payment_method').value;

      if (!student_id || !month || !amount) {
        alert("Please fill all required fields.");
        return;
      }

      try {
        const orderRes = await createOrder(student_id, amount, parseInt(month.split('-')[1]), parseInt(month.split('-')[0]));
        const area = document.getElementById('upiArea');
        area.style.display = 'block';

        // Clear previous content
        const qrCodeDiv = document.getElementById('qrCode');
        const linkContainer = document.getElementById('linkContainer');
        qrCodeDiv.innerHTML = '';
        linkContainer.innerHTML = '';

        // Display QR code from backend base64 data
        if (orderRes.qr_base64) {
          const qrImg = document.createElement('img');
          qrImg.src = `data:image/png;base64,${orderRes.qr_base64}`;
          qrImg.alt = 'UPI QR Code';
          qrImg.style.maxWidth = '200px';
          qrImg.style.height = 'auto';
          qrCodeDiv.appendChild(qrImg);
        }

        // Handle different payment methods
        if (payment_method === 'upi') {
          // Show UPI link
          linkContainer.innerHTML = `
            <p>Or click the UPI link:</p>
            <a id="upiLink" href="${orderRes.upi_url}" target="_blank" class="btn btn-secondary">Pay via UPI</a>
          `;
        } else {
          // Show app-specific deep link
          const appLink = getAppSpecificLink(payment_method, orderRes.upi_url);
          linkContainer.innerHTML = `
            <p>Click to open ${getAppName(payment_method)}:</p>
            <a id="upiLink" href="${appLink}" target="_blank" class="btn btn-secondary">
              Pay via ${getAppName(payment_method)}
            </a>
            <p class="muted">If the app doesn't open, copy this link: ${appLink}</p>
          `;
        }

        // Setup verify button
        const verifyBtn = document.getElementById('verifyBtn');
        verifyBtn.onclick = async () => {
          try {
            const verifyRes = await verifyPayment(orderRes.order_id, student_id, parseInt(month.split('-')[1]), amount);
            alert('Payment submitted for admin verification. You will be notified once verified.');
            // Clear the UPI area and show success message
            area.innerHTML = `
              <div class="payment-success">
                <h3>Payment Submitted Successfully!</h3>
                <p>Your payment has been submitted and is pending admin verification.</p>
                <p>You will receive a notification once the payment is verified.</p>
                <button class="btn btn-primary" onclick="location.reload()">Make Another Payment</button>
              </div>
            `;
          } catch (err) {
            alert('Error submitting payment: ' + err.message);
          }
        };
      } catch (err) {
        alert('Error creating order: ' + err.message);
      }
    });
  }
}

// Get app-specific deep link
function getAppSpecificLink(paymentMethod, upiUrl) {
  const appSchemes = {
    gpay: 'tez://upi/pay?pa=',
    phonepe: 'phonepe://pay?pa=',
    paytm: 'paytmmp://pay?pa=',
    amazonpay: 'amazonpay://pay?pa=',
    bhim: 'bhim://pay?pa='
  };

  if (appSchemes[paymentMethod]) {
    // Extract UPI parameters from the URL
    const url = new URL(upiUrl);
    const pa = url.searchParams.get('pa');
    const pn = url.searchParams.get('pn');
    const am = url.searchParams.get('am');
    const tn = url.searchParams.get('tn');
    const cu = url.searchParams.get('cu');

    return `${appSchemes[paymentMethod]}${pa}&pn=${encodeURIComponent(pn)}&am=${am}&tn=${encodeURIComponent(tn)}&cu=${cu}`;
  }

  return upiUrl; // Fallback to generic UPI URL
}

// Get display name for payment method
function getAppName(paymentMethod) {
  const names = {
    upi: 'UPI',
    gpay: 'Google Pay',
    phonepe: 'PhonePe',
    paytm: 'Paytm',
    amazonpay: 'Amazon Pay',
    bhim: 'BHIM UPI'
  };
  return names[paymentMethod] || 'UPI App';
}

// Initialize UPI payment when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
  if (document.getElementById('payBtn')) {
    initUPIPayment();
  }
});

// Make functions globally available for onclick handlers
window.markPaymentAsPaid = markPaymentAsPaid;
window.downloadReceipt = downloadReceipt;
