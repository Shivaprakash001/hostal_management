import { BASE_URL } from "./config.js";
import { authManager } from "./auth.js";
import { api } from "./api.js";

const messagesEl = () => document.getElementById("agent-messages");
const inputEl = () => document.getElementById("agent-input");
const formEl = () => document.getElementById("agent-form");
const connectBtnEl = () => document.getElementById("agent-connect");

let socket = null;
let sessionId = localStorage.getItem("agentSessionId") || (() => {
    const id = Math.random().toString(36).slice(2);
    localStorage.setItem("agentSessionId", id);
    return id;
})();

// ---------- Rendering Helpers ----------

function renderTable(rows) {
    const wrapper = document.createElement("div");
    wrapper.className = "table-wrapper";
    if (!Array.isArray(rows) || rows.length === 0) {
        wrapper.textContent = "No results found.";
        return wrapper;
    }
    const keys = Object.keys(rows[0]);
    const table = document.createElement("table");
    const thead = document.createElement("thead");
    const trHead = document.createElement("tr");
    keys.forEach(k => {
        const th = document.createElement("th");
        th.textContent = k;
        trHead.appendChild(th);
    });
    thead.appendChild(trHead);
    table.appendChild(thead);
    const tbody = document.createElement("tbody");
    rows.forEach(row => {
        const tr = document.createElement("tr");
        keys.forEach(k => {
            const td = document.createElement("td");
            td.textContent = row[k];
            tr.appendChild(td);
        });
        tbody.appendChild(tr);
    });
    table.appendChild(tbody);
    wrapper.appendChild(table);
    return wrapper;
}

function renderCard(obj) {
    const card = document.createElement("div");
    card.className = "card";
    Object.entries(obj).forEach(([k, v]) => {
        const row = document.createElement("div");
        row.className = "row";
        row.innerHTML = `<strong>${k}</strong>: ${v}`;
        card.appendChild(row);
    });
    return card;
}

// ---------- Main message appender ----------

function appendMessage(role, summary, data = null) {
    const container = messagesEl();
    const item = document.createElement("div");
    item.className = `msg ${role}`;

    // Show human-friendly summary first
    if (summary) {
        const summaryEl = document.createElement("div");
        summaryEl.className = "summary";
        summaryEl.textContent = summary;
        item.appendChild(summaryEl);
    }

    // Handle confirmation
    if (data && Array.isArray(data) && data.length > 0 && data[0].confirm) {
        item.appendChild(renderConfirmationRequest(data[0], summary));
    }
    // Handle disambiguation
    else if (data && Array.isArray(data) && data.length > 0 && data[0].id) {
        item.appendChild(renderDisambiguationChoices(data, summary));
    }
    // Handle structured data
    else if (data) {
        if (Array.isArray(data)) {
            item.appendChild(renderTable(data));
        } else if (typeof data === "object") {
            item.appendChild(renderCard(data));
        }
    }

    container.appendChild(item);
    container.scrollTop = container.scrollHeight;
}

// ---------- Confirmation + Disambiguation ----------

function renderConfirmationRequest(confirmData, summary) {
    const wrapper = document.createElement("div");
    wrapper.className = "confirmation-wrapper";

    const summaryEl = document.createElement("div");
    summaryEl.className = "confirmation-summary";
    summaryEl.textContent = summary;
    wrapper.appendChild(summaryEl);

    const buttonsEl = document.createElement("div");
    buttonsEl.className = "confirmation-buttons";

    const confirmBtn = document.createElement("button");
    confirmBtn.className = "btn danger";
    confirmBtn.textContent = "✅ Confirm";
    confirmBtn.addEventListener("click", () => handleConfirmation(confirmData, true));

    const cancelBtn = document.createElement("button");
    cancelBtn.className = "btn";
    cancelBtn.textContent = "❌ Cancel";
    cancelBtn.addEventListener("click", () => handleConfirmation(confirmData, false));

    buttonsEl.appendChild(confirmBtn);
    buttonsEl.appendChild(cancelBtn);
    wrapper.appendChild(buttonsEl);

    return wrapper;
}

function handleConfirmation(confirmData, confirmed) {
    const confirmEl = document.querySelector(".confirmation-wrapper");
    if (confirmEl) confirmEl.remove();

    if (confirmed) {
        appendMessage("user", `Confirmed delete for student ID ${confirmData.student_id}`);
        const originalQuery = getLastUserQuery();
        if (originalQuery) {
            const modifiedQuery = `${originalQuery} with confirmation`;
            sendViaREST(modifiedQuery);
        }
    } else {
        appendMessage("user", "❌ Delete operation cancelled.");
    }
}

function renderDisambiguationChoices(choices, summary) {
    const wrapper = document.createElement("div");
    wrapper.className = "disambiguation-wrapper";

    const summaryEl = document.createElement("div");
    summaryEl.className = "disambiguation-summary";
    summaryEl.textContent = summary;
    wrapper.appendChild(summaryEl);

    const choicesEl = document.createElement("div");
    choicesEl.className = "disambiguation-choices";

    choices.forEach(choice => {
        const choiceBtn = document.createElement("button");
        choiceBtn.className = "disambiguation-choice";
        choiceBtn.textContent = `👤 ${choice.name} (ID: ${choice.id}) - Room: ${choice.room_no || 'Unassigned'}`;
        choiceBtn.addEventListener("click", () => handleDisambiguationChoice(choice));
        choicesEl.appendChild(choiceBtn);
    });

    wrapper.appendChild(choicesEl);
    return wrapper;
}

function handleDisambiguationChoice(choice) {
    const disambEl = document.querySelector(".disambiguation-wrapper");
    if (disambEl) disambEl.remove();

    appendMessage("user", `You selected: ${choice.name} (ID: ${choice.id})`);
    const originalQuery = getLastUserQuery();
    if (originalQuery) {
        const modifiedQuery = `${originalQuery} for student ID ${choice.id}`;
        sendViaREST(modifiedQuery);
    }
}

function getLastUserQuery() {
    const messages = document.querySelectorAll(".msg.user .summary");
    if (messages.length > 0) {
        return messages[messages.length - 1].textContent;
    }
    return null;
}

// ---------- Senders ----------

async function sendViaREST(query) {
    appendMessage("user", query);
    try {
        if (!authManager.isAuthenticated()) {
            appendMessage("error", "Please log in to use the agent.");
            return;
        }
        const res = await fetch(`${BASE_URL}/api/agent/query`, {
            method: "POST",
            headers: { "Content-Type": "application/json", ...authManager.getAuthHeaders() },
            body: JSON.stringify({ query, session_id: sessionId })
        });
        const payload = await res.json();
        if (!res.ok) {
            appendMessage("error", payload.detail || "Agent error");
            return;
        }
        if (payload.summary) appendMessage("agent", payload.summary, payload.data);
    } catch (err) {
        appendMessage("error", String(err));
    }
}

function connectWS() {
    if (socket && socket.readyState === WebSocket.OPEN) return;
    const wsUrl = BASE_URL.replace("http", "ws") + "/api/agent/ws/agent";
    socket = new WebSocket(wsUrl);

    socket.onopen = () => appendMessage("system", "✅ Connected to agent");
    socket.onmessage = (event) => {
        try {
            const msg = JSON.parse(event.data);
            if (msg.summary) appendMessage("agent", msg.summary, msg.data);
            if (msg.error) appendMessage("error", msg.error);
        } catch {
            appendMessage("agent", event.data);
        }
    };
    socket.onclose = () => appendMessage("system", "❌ Disconnected from agent");
    socket.onerror = () => appendMessage("error", "⚠️ WS error");
}

function sendViaWS(query) {
    if (!socket || socket.readyState !== WebSocket.OPEN) {
        appendMessage("error", "WS not connected. Using REST instead.");
        return sendViaREST(query);
    }
    appendMessage("user", query);
    socket.send(JSON.stringify({ query, session_id: sessionId }));
}

// ---------- UI Init ----------

function initAgentUI() {
    if (!formEl()) return;
    formEl().addEventListener("submit", (e) => {
        e.preventDefault();
        const q = inputEl().value.trim();
        if (!q) return;
        if (socket && socket.readyState === WebSocket.OPEN) {
            sendViaWS(q);
        } else {
            sendViaREST(q);
        }
        inputEl().value = "";
    });

    connectBtnEl().addEventListener("click", () => connectWS());
}

function ensureStyles() {
    const styleId = "agent-styles";
    if (document.getElementById(styleId)) return;
    const style = document.createElement("style");
    style.id = styleId;
    style.textContent = `
    .agent-chat { display: flex; flex-direction: column; height: 420px; }
    .agent-messages { flex: 1; overflow: auto; border: 1px solid #ddd; padding: 8px; border-radius: 8px; background: #fff; }
    .agent-form { margin-top: 8px; display: flex; }
    .agent-form input { flex: 1; margin-right: 8px; }
    .msg { padding: 6px 8px; margin: 6px 0; border-radius: 6px; }
    .msg.user { background: #e3f2fd; }
    .msg.agent { background: #f1f8e9; }
    .msg.system { background: #ede7f6; font-style: italic; }
    .msg.error { background: #ffebee; color: #b71c1c; }
    .summary { margin-bottom: 6px; font-weight: bold; }
    .table-wrapper { overflow-x: auto; margin-top: 6px; }
    table { width: 100%; border-collapse: collapse; }
    th, td { padding: 6px; border: 1px solid #ddd; text-align: left; }
    .card { padding: 6px; border: 1px solid #ddd; border-radius: 6px; margin-top: 6px; }
    .row { margin: 2px 0; }
    .confirmation-buttons, .disambiguation-choices { margin-top: 6px; display: flex; gap: 6px; flex-wrap: wrap; }
    button { cursor: pointer; padding: 4px 8px; border-radius: 4px; border: none; }
    button.btn.danger { background: #d32f2f; color: white; }
    button.disambiguation-choice { background: #f5f5f5; border: 1px solid #ccc; }
    `;
    document.head.appendChild(style);
}


export async function runAgentCommand(command) {
  const container = document.getElementById("panel-agent");
  const output = container.querySelector("#agent-output");
  const log = container.querySelector("#agent-log");

  output.textContent = "⏳ Running: " + command;
  log.innerHTML = "";

  try {
    const res = await api("/agent/run", {
      method: "POST",
      body: JSON.stringify({ command }),
    });

    // Ensure response formatting
    let userMessage = res.message || "✅ Done";
    let logs = res.logs || [];

    // If message comes tokenized like ['C','a','l','c'] → join it
    if (Array.isArray(userMessage)) {
      userMessage = userMessage.join("");
    }

    output.textContent = userMessage;

    // Show execution log steps
    if (Array.isArray(logs)) {
      logs.forEach((step, i) => {
        let cleanStep = step;
        if (Array.isArray(step)) {
          cleanStep = step.join("");
        }
        const li = document.createElement("li");
        li.textContent = `Step ${i + 1}: ${cleanStep}`;
        log.appendChild(li);
      });
    }
  } catch (err) {
    output.textContent = "❌ Error running agent";
    console.error(err);
  }
}


document.addEventListener("DOMContentLoaded", () => {
    ensureStyles();
    initAgentUI();
});
