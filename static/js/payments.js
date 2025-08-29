import { api, money } from "./api.js";

const STATUS_OPTIONS = ["Pending", "Paid", "Failed"];
let currentlyEditing = null; // Track the currently edited <li>

export function initPayments() {
  const container = document.getElementById("panel-payments");
  const paymentsList = container.querySelector("#payments-list");
  const paymentsLoading = container.querySelector("#payments-loading");
  const formAddPayment = document.getElementById("form-add-payment");
  const lookupInput = document.getElementById("lookup_student_name");
  const lookupBtn = document.getElementById("btn-lookup");

  // Check if elements exist before adding event listeners
  if (formAddPayment) {
    formAddPayment.addEventListener("submit", async e => {
      e.preventDefault();
      const studentName = formAddPayment.payment_student_name.value.trim();
      const amount = parseFloat(formAddPayment.payment_amount.value);
      if (!studentName || Number.isNaN(amount)) return alert("Please fill all fields.");

      try {
        // First get the student by name to retrieve the student ID
        const student = await api(`/students/by-name/${encodeURIComponent(studentName)}`);
        const studentId = student.id;

        // Now add the payment using the student ID
        await api(`/payments`, { 
          method: "POST", 
          body: { 
            student_id: studentId,
            amount, 
            status: "Pending" // or any other default status you want to set
          } 
        });
        formAddPayment.reset();
        await loadPaymentsByStudent(studentId);
      } catch (err) {
        alert(`Error adding payment: ${err.message}`);
      }
    });
  }

      if (lookupBtn) {
        lookupBtn.addEventListener("click", async () => {
          const studentName = lookupInput.value.trim();
          if (!studentName) return alert("Enter a student name.");
          // Update to use the new endpoint
          const student = await api(`/students/by-name/${encodeURIComponent(studentName)}`);
          const studentId = student.id;
          await loadPaymentsByStudent(studentId);
        });
      }

  // --- Render a list of payments ---
  function renderPayments(items, studentId = null) {
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
      ? `Payments for ${studentId} — Total: ${money(total)}`
      : `Recent Payments — Total: ${money(total)}`;
    paymentsList.appendChild(header);

    items.forEach(p => {
      const li = document.createElement("li");
      li.className = "card";
      li.innerHTML = `
        <div class="payment-content">
          <div>Student: ${p.student_name || p.student_id}</div>
          <div>Amount: <input type="number" step="0.01" value="${p.amount}" class="edit-amount" disabled/></div>
          <div>Status: 
            <select class="edit-status" disabled>
              ${STATUS_OPTIONS.map(s => `<option value="${s}" ${s === p.status ? "selected" : ""}>${s}</option>`).join("")}
            </select>
          </div>
          <div class="muted">Date: ${new Date(p.date).toLocaleString()}</div>
        </div>
        <div class="payment-actions">
          <button class="btn btn-small btn-edit">Edit</button>
          <button class="btn btn-small btn-save" disabled style="display: none;">Save</button>
          <button class="btn btn-small btn-cancel" disabled style="display: none;">Cancel</button>
          <button class="btn btn-small btn-danger btn-delete" data-payment-id="${p.id}">Delete</button>
        </div>
      `;
      paymentsList.appendChild(li);

      const editBtn = li.querySelector(".btn-edit");
      const saveBtn = li.querySelector(".btn-save");
      const cancelBtn = li.querySelector(".btn-cancel");
      const amountInput = li.querySelector(".edit-amount");
      const statusSelect = li.querySelector(".edit-status");
      const deleteBtn = li.querySelector(".btn-delete");

      // --- Edit ---
      editBtn.addEventListener("click", () => {
        if (currentlyEditing) return; // Only one row in edit mode
        currentlyEditing = li;
        li.classList.add("editing");

        document.querySelectorAll(".btn-edit").forEach(btn => btn.disabled = true);

        amountInput.disabled = false;
        statusSelect.disabled = false;
        saveBtn.disabled = false;
        saveBtn.style.display = "inline-block";
        cancelBtn.disabled = false;
        cancelBtn.style.display = "inline-block";
        editBtn.disabled = true;
        editBtn.style.display = "none";
        deleteBtn.disabled = true;
        deleteBtn.style.display = "none";
      });

      // --- Save ---
      saveBtn.addEventListener("click", async () => {
        const newAmount = parseFloat(amountInput.value);
        const newStatus = statusSelect.value;
        if (Number.isNaN(newAmount)) return alert("Amount must be a number.");

        try {
          await api(`/payments/${p.id}`, {
            method: "PUT",
            body: { amount: newAmount, status: newStatus }
          });
          alert("Payment updated!");
          currentlyEditing = null;
          li.classList.remove("editing");
          
          // Hide Save and Cancel buttons, show Edit and Delete buttons
          saveBtn.style.display = "none";
          cancelBtn.style.display = "none";
          editBtn.style.display = "inline-block";
          deleteBtn.style.display = "inline-block";
          
          document.querySelectorAll(".btn-edit").forEach(btn => btn.disabled = false);
          if (studentId) await loadPaymentsByStudent(studentId);
          else await loadRecentPayments();
        } catch (err) {
          alert(`Error updating payment: ${err.message}`);
        }
      });

      // --- Cancel ---
      cancelBtn.addEventListener("click", () => {
        amountInput.value = p.amount;
        statusSelect.value = p.status;
        amountInput.disabled = true;
        statusSelect.disabled = true;
        saveBtn.disabled = true;
        saveBtn.style.display = "none";
        cancelBtn.disabled = true;
        cancelBtn.style.display = "none";
        editBtn.disabled = false;
        editBtn.style.display = "inline-block";
        deleteBtn.disabled = false;
        deleteBtn.style.display = "inline-block";
        currentlyEditing = null;
        li.classList.remove("editing");
        document.querySelectorAll(".btn-edit").forEach(btn => btn.disabled = false);
      });

      // --- Delete ---
      deleteBtn.addEventListener("click", async () => {
        if (!confirm(`Delete payment ID ${p.id}?`)) return;
        try {
          await api(`/payments/${p.id}`, { method: "DELETE" });
          alert("Payment deleted.");
          if (studentId) await loadPaymentsByStudent(studentId);
          else await loadRecentPayments();
        } catch (err) {
          alert(`Error deleting payment: ${err.message}`);
        }
      });
    });
  }

  // --- Loaders ---
  async function loadRecentPayments() {
    paymentsLoading.textContent = "Loading recent payments…";
    try {
      const items = await api("/payments/with-student-names/");
      paymentsLoading.textContent = "";
      renderPayments(items);
    } catch (err) {
      paymentsLoading.textContent = `Error loading payments: ${err.message}`;
    }
  }

  async function loadPaymentsByStudent(studentId) {
    if (!studentId || Number.isNaN(studentId)) return;
    paymentsLoading.textContent = "Loading payments…";
    try {
      const items = await api(`/payments/student/${encodeURIComponent(studentId)}`);
      paymentsLoading.textContent = "";
      renderPayments(items, studentId);
    } catch (err) {
      paymentsLoading.textContent = `Error loading payments: ${err.message}`;
    }
  }

  async function loadPaymentsByStudentName(studentName) {
    if (!studentName) return;
    paymentsLoading.textContent = "Loading payments…";
    try {
      // First get the student by name to retrieve the student ID
      const studentResponse = await api(`/students?name=${encodeURIComponent(studentName)}`);
      if (studentResponse.length === 0) {
        paymentsLoading.textContent = "Student not found.";
        return;
      }
      const studentId = studentResponse[0].id; // Get the first matching student
      
      // Now load payments by student ID
      const items = await api(`/payments/student/${encodeURIComponent(studentId)}`);
      paymentsLoading.textContent = "";
      renderPayments(items, studentId);
    } catch (err) {
      paymentsLoading.textContent = `Error loading payments: ${err.message}`;
    }
  }

  // --- Initial load ---
  loadRecentPayments();

  // expose loaders for tabs
  return { loadRecentPayments, loadPaymentsByStudent };
}
