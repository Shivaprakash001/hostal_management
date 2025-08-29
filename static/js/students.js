// js/students.js
import { api } from "./api.js";

export async function loadStudents() {
  const container = document.getElementById("panel-students");
  const studentsList = container.querySelector("#students-list");
  const studentsLoading = container.querySelector("#students-loading");

  studentsLoading.textContent = "Loading students…";
  studentsList.innerHTML = "";

  try {
    // Load all students only
    const students = await api("/students/");
    console.log("Students loaded:", students); // Log loaded students
    
    studentsLoading.textContent = "";

    if (!students.length) {
      studentsList.innerHTML = "<li class='muted'>No students found.</li>";
      return;
    }

    // Display students
    students.forEach(s => {
      const li = document.createElement("li");
      li.className = "card";
      li.innerHTML = `
        <div><strong>${s.name}</strong> <span class="mono">(${s.id})</span></div>
        <div class="muted">Room: ${s.room_no}</div>
        <div class="muted">Phone: ${s.phone_no ?? "-"}</div>

        <!-- Actions -->
        <div class="actions">
          <button class="btn danger" data-action="delete" data-student="${s.id}">Delete</button>
          <button class="btn" data-action="toggle-edit" data-student="${s.id}">Edit</button>
          <button class="btn ${s.active ? "success" : "warning"}" 
                  data-action="toggle-status" 
                  data-student="${s.id}" 
                  data-active="${s.active}">
            ${s.active ? "Deactivate" : "Activate"}
          </button>
        </div>

        <!-- Inline Edit Form (hidden by default) -->
        <form class="inline-form hidden" data-student="${s.id}">
          <input type="text" name="name" placeholder="Student Name" value="${s.name}" />
          <input type="text" name="room_no" placeholder="Room No" value="${s.room_no}" />
          <input type="tel" name="phone_no" placeholder="Phone No" value="${s.phone_no ?? ""}" />
          <button class="btn primary" type="submit">Save</button>
          <button class="btn" type="button" data-action="cancel">Cancel</button>
        </form>
      `;
      studentsList.appendChild(li);
    });

  } catch (err) {
    console.error("Error loading students:", err);
    studentsLoading.textContent = `Error loading students: ${err.message}`;
  }
}

let currentlyEditingStudent = null;

export function initStudents() {
  const container = document.getElementById("panel-students");
  if (!container) {
    console.error("Students panel container not found");
    return;
  }

  const studentsList = container.querySelector("#students-list");
  const formAddStudent = document.getElementById("form-add-student");

  // Load students once
  loadStudents();

  // Add student (now creates user which internally creates student)
  if (formAddStudent) {
    formAddStudent.addEventListener("submit", async e => {
      e.preventDefault();
      const name = formAddStudent.student_name.value.trim();
      const password = formAddStudent.student_password.value.trim();
      const phone_no = formAddStudent.student_phone_no.value.trim();
      const room_no = formAddStudent.student_room_no.value.trim();

      if (!name || !password) return alert("Please fill name and password fields.");
      if (password.length < 4) return alert("Password must be at least 4 characters.");

      try {
        await api("/auth/signup", { 
          method: "POST", 
          body: { 
            username: name, 
            password: password,
            role: "Student", // Use capitalized role
            phone_no: phone_no ? parseInt(phone_no) : null,
            room_no: room_no || null 
          } 
        });
        formAddStudent.reset();
        await loadStudents();
      } catch (err) {
        alert(err.message);
      }
    });
  }

  if (!studentsList) {
    console.error("Students list element not found.");
    return;
  }

  // Handle actions
  studentsList.addEventListener("click", async e => {
    const btn = e.target.closest("button");
    if (!btn) return;
    const action = btn.dataset.action;
    const studentId = btn.dataset.student;

    if (action === "delete") {
      if (!confirm(`Delete student ${studentId}?`)) return;
      await api(`/students/${studentId}`, { method: "DELETE" });
      await loadStudents();
    }

    if (action === "toggle-edit") {
      const card = btn.closest(".card");
      const form = card.querySelector(`form.inline-form[data-student="${studentId}"]`);
      const actions = card.querySelector(".actions");

      if (currentlyEditingStudent === studentId) {
        form.classList.add("hidden");
        actions.style.display = "flex";
        currentlyEditingStudent = null;
        document.querySelectorAll('button[data-action="toggle-edit"]').forEach(b => (b.disabled = false));
        return;
      }

      if (currentlyEditingStudent && currentlyEditingStudent !== studentId) {
        const prevCard = document.querySelector(`.card form.inline-form[data-student="${currentlyEditingStudent}"]`).closest(".card");
        prevCard.querySelector("form.inline-form").classList.add("hidden");
        prevCard.querySelector(".actions").style.display = "flex";
      }

      form.classList.remove("hidden");
      actions.style.display = "none";
      currentlyEditingStudent = studentId;

      document.querySelectorAll('button[data-action="toggle-edit"]').forEach(b => {
        if (b.dataset.student !== studentId) b.disabled = true;
      });
    }

    if (action === "cancel") {
      const form = btn.closest("form.inline-form");
      const card = btn.closest(".card");
      const actions = card.querySelector(".actions");
      form.classList.add("hidden");
      actions.style.display = "flex";
      currentlyEditingStudent = null;
      document.querySelectorAll('button[data-action="toggle-edit"]').forEach(b => (b.disabled = false));
    }

    if (action === "toggle-status") {
      const isActive = btn.dataset.active === "true";
      const confirmMsg = isActive ? `Deactivate student ${studentId}?` : `Activate student ${studentId}?`;
      if (!confirm(confirmMsg)) return;

      await api(`/students/${studentId}/${isActive ? "deactivate" : "activate"}`, { method: "PUT" });
      await loadStudents();
    }
  });

  // Save edited student
  studentsList.addEventListener("submit", async e => {
    const form = e.target.closest("form.inline-form");
    if (!form) return;
    e.preventDefault();

    const studentId = form.dataset.student;
    const name = form.elements["name"].value.trim();
    const room_no = form.elements["room_no"].value.trim();
    const phoneStr = form.elements["phone_no"].value.trim();
    const phone_no = phoneStr ? parseInt(phoneStr, 10) : null;
    if (!name) return alert("Please fill the name field.");

    try {
      await api(`/students/${studentId}`, { method: "PUT", body: { name, room_no, phone_no } });
      await loadStudents();
      currentlyEditingStudent = null;
      document.querySelectorAll('button[data-action="toggle-edit"]').forEach(b => (b.disabled = false));
    } catch (err) {
      alert(err.message);
    }
  });
}
