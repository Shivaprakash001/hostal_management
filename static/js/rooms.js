// js/rooms.js

import { api, money } from "./api.js";

const roomsList = document.getElementById("rooms-list");
const roomsLoading = document.getElementById("rooms-loading");
const formAddRoom = document.getElementById("form-add-room");
const filterUnpaidOnly = document.getElementById("filter-unpaid-only");
const filterMinPrice = document.getElementById("filter-min-price");
const filterMaxPrice = document.getElementById("filter-max-price");
const applyRoomFiltersBtn = document.getElementById("apply-room-filters");
const clearRoomFiltersBtn = document.getElementById("clear-room-filters");

let cachedRooms = [];
let currentlyEditingRoom = null; // Track the currently edited room

export async function loadRooms() {
  roomsLoading.textContent = "Loading rooms…";
  roomsList.innerHTML = "";
  try {
    const rooms = await api("/rooms/");
    cachedRooms = rooms;
    roomsLoading.textContent = "";
    renderRoomsList(filterRooms(cachedRooms));

  } catch (err) {
    roomsLoading.textContent = `Error loading rooms: ${err.message}`;
  }
}

function filterRooms(list) {
  const unpaidOnly = !!(filterUnpaidOnly && filterUnpaidOnly.checked);
  const minPrice = filterMinPrice ? parseFloat(filterMinPrice.value) : NaN;
  const maxPrice = filterMaxPrice ? parseFloat(filterMaxPrice.value) : NaN;

  return (list || []).filter(room => {
    const status = String(room.payment_status || "").toLowerCase();
    if (unpaidOnly && status !== "pending") return false;

    if (!Number.isNaN(minPrice) && typeof room.price === "number" && room.price < minPrice) return false;
    if (!Number.isNaN(maxPrice) && typeof room.price === "number" && room.price > maxPrice) return false;

    return true;
  });
}

function renderRoomsList(list) {
  roomsList.innerHTML = "";
  if (!list || !list.length) {
    roomsList.innerHTML = "<li class='muted'>No rooms available.</li>";
    return;
  }
  list.forEach(room => {
    const li = document.createElement("li");
    li.className = "card";
    const paidOk = room.payment_status === "Paid";
    li.innerHTML = `
      <div>
        <strong>Room ${room.room_no}</strong>
        <span class="pill ${paidOk ? "ok" : "bad"}">${room.payment_status} • ${money(room.total_payments)} / ${money(room.price)}</span>
      </div>
      <div class="muted">Capacity: ${room.students.length}/${room.capacity}</div>
      <div>Students: ${room.students.map(s => s.name).join(", ") || "<span class='muted'>None</span>"}</div>
      <div class="actions">
        <button class="btn danger" data-action="delete" data-room="${room.room_no}">Delete</button>
        <button class="btn" data-action="toggle-edit" data-room="${room.room_no}">Edit</button>
      </div>
      <form class="inline-form hidden" data-room="${room.room_no}">
        <input type="text" name="new_room_no" value="${room.room_no}" />
        <input type="number" name="price" step="0.01" value="${room.price}" />
        <input type="number" name="capacity" min="1" value="${room.capacity}" />
        <button type="submit" class="btn primary">Save</button>
        <button type="button" class="btn" data-action="cancel">Cancel</button>
      </form>`;
    roomsList.appendChild(li);
  });
}

export function initRooms() {
  if (applyRoomFiltersBtn) {
    applyRoomFiltersBtn.addEventListener("click", async () => {
      renderRoomsList(filterRooms(cachedRooms));
    });
  }

  if (clearRoomFiltersBtn) {
    clearRoomFiltersBtn.addEventListener("click", async () => {
      if (filterUnpaidOnly) filterUnpaidOnly.checked = false;
      if (filterMinPrice) filterMinPrice.value = "";
      if (filterMaxPrice) filterMaxPrice.value = "";
      renderRoomsList(filterRooms(cachedRooms));
    });
  }

  if (filterUnpaidOnly) {
    filterUnpaidOnly.addEventListener("change", () => {
      renderRoomsList(filterRooms(cachedRooms));
    });
  }
  formAddRoom.addEventListener("submit", async e => {
    e.preventDefault();
    const room_no = document.getElementById("room_no").value.trim();
    const price = parseFloat(document.getElementById("price").value);
    const capacity = parseInt(document.getElementById("capacity").value);
    if (!room_no || isNaN(price) || isNaN(capacity)) return alert("Fill all fields.");

    try {
      await api("/rooms/", { method: "POST", body: { room_no, price, capacity } });
      formAddRoom.reset();
      await loadRooms();
    } catch (err) {
      alert(err.message);
    }
  });

  roomsList.addEventListener("click", async e => {
    const btn = e.target.closest("button");
    if (!btn) return;
    const action = btn.dataset.action;
    const roomNo = btn.dataset.room;

    if (action === "delete" && confirm(`Delete room ${roomNo}?`)) {
      await api("/rooms/", { method: "DELETE", body: { room_no: roomNo } });
      await loadRooms();
    }
    if (action === "toggle-edit") {
      // If another room is already being edited, cancel it first
      if (currentlyEditingRoom && currentlyEditingRoom !== roomNo) {
        const previousCard = document.querySelector(`.card form.inline-form[data-room="${currentlyEditingRoom}"]`).closest('.card');
        previousCard.querySelector(".actions").style.display = "flex";
        previousCard.querySelector("form.inline-form").classList.add("hidden");
      }
      
      const card = btn.closest(".card");
      const act = card.querySelector(".actions")
      const form = card.querySelector("form.inline-form");
      act.style.display = "none"; // hide buttons
      form.classList.remove("hidden");
      currentlyEditingRoom = roomNo;
    }

    if (action === "cancel") {
      const card = btn.closest(".card");
      card.querySelector(".actions").style.display = "flex"; // show buttons again
      btn.closest("form.inline-form").classList.add("hidden");
      currentlyEditingRoom = null;
    }
  });

  roomsList.addEventListener("submit", async e => {
    const form = e.target.closest("form.inline-form");
    if (!form) return;
    e.preventDefault();

    const roomNo = form.dataset.room;
    const updateData = {
      new_room_no: form.elements["new_room_no"].value.trim(),
      price: parseFloat(form.elements["price"].value),
      capacity: parseInt(form.elements["capacity"].value)
    };

    try {
      await api(`/rooms/${encodeURIComponent(roomNo)}`, { method: "PUT", body: updateData });
      currentlyEditingRoom = null; // Reset editing state after successful submission
      await loadRooms();
    } catch (err) {
      alert(err.message);
    }
  });
}
