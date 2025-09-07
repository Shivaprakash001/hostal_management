import { BASE_URL } from "./config.js";
import { authManager } from "./auth.js";

export function initAgentUI() {
    if (!formEl()) return;

    formEl().addEventListener("submit", (e) => {
        e.preventDefault();
        const q = inputEl().value.trim();
        if (!q) return;
        // Prefer WS if connected
        if (socket && socket.readyState === WebSocket.OPEN) {
            sendViaWS(q);
        } else {
            sendViaREST(q);
        }
        inputEl().value = "";
    });

    connectBtnEl().addEventListener("click", () => connectWS());
}

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

function renderTable(rows) {
    const wrapper = document.createElement("div");
    if (!Array.isArray(rows) || rows.length === 0) {
        wrapper.textContent = "No results";
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

function appendMessage(role, text, data = null) {
    const container = messagesEl();
    const item = document.createElement("div");
    item.className = `msg ${role}`;
    
    // Handle confirmation requests
    if (data && Array.isArray(data) && data.length > 0 && data[0].confirm) {
        item.appendChild(renderConfirmationRequest(data[0], text));
    }
    // Handle disambiguation data
    else if (data && Array.isArray(data) && data.length > 0 && data[0].id) {
        item.appendChild(renderDisambiguationChoices(data, text));
    } else {
        // Try to render JSON nicely
        try {
            const json = typeof text === "string" ? JSON.parse(text) : text;
            if (Array.isArray(json)) {
                item.appendChild(renderTable(json));
            } else if (json && typeof json === "object") {
                item.appendChild(renderCard(json));
            } else {
                item.textContent = String(text);
            }
        } catch {
            item.textContent = String(text);
        }
    }
    container.appendChild(item);
    container.scrollTop = container.scrollHeight;
}

function renderConfirmationRequest(confirmData, summary) {
    const wrapper = document.createElement("div");
    wrapper.className = "confirmation-wrapper";
    
    // Show summary
    const summaryEl = document.createElement("div");
    summaryEl.className = "confirmation-summary";
    summaryEl.textContent = summary;
    wrapper.appendChild(summaryEl);
    
    // Show confirmation buttons
    const buttonsEl = document.createElement("div");
    buttonsEl.className = "confirmation-buttons";
    
    const confirmBtn = document.createElement("button");
    confirmBtn.className = "btn danger";
    confirmBtn.textContent = "Confirm Delete";
    confirmBtn.addEventListener("click", () => handleConfirmation(confirmData, true));
    
    const cancelBtn = document.createElement("button");
    cancelBtn.className = "btn";
    cancelBtn.textContent = "Cancel";
    cancelBtn.addEventListener("click", () => handleConfirmation(confirmData, false));
    
    buttonsEl.appendChild(confirmBtn);
    buttonsEl.appendChild(cancelBtn);
    wrapper.appendChild(buttonsEl);
    
    return wrapper;
}

function handleConfirmation(confirmData, confirmed) {
    // Clear confirmation UI
    const confirmEl = document.querySelector(".confirmation-wrapper");
    if (confirmEl) {
        confirmEl.remove();
    }
    
    if (confirmed) {
        // Show confirmation message
        appendMessage("user", `Confirmed: Delete student ID ${confirmData.student_id}`);
        
        // Re-run the original query with confirm=true
        const originalQuery = getLastUserQuery();
        if (originalQuery && originalQuery.toLowerCase().includes("delete")) {
            // Extract the student name from the original query
            const studentNameMatch = originalQuery.match(/delete\s+(?:user\s+)?(\w+)/i);
            if (studentNameMatch) {
                const studentName = studentNameMatch[1];
                const modifiedQuery = `delete student ${studentName} with confirmation`;
                sendViaREST(modifiedQuery);
            } else {
                // Fallback to using student ID
                const modifiedQuery = `delete student ID ${confirmData.student_id} with confirmation`;
                sendViaREST(modifiedQuery);
            }
        }
    } else {
        // Show cancellation message
        appendMessage("user", "Cancelled: Delete operation cancelled");
    }
}

function renderDisambiguationChoices(choices, summary) {
    const wrapper = document.createElement("div");
    wrapper.className = "disambiguation-wrapper";
    
    // Show summary
    const summaryEl = document.createElement("div");
    summaryEl.className = "disambiguation-summary";
    summaryEl.textContent = summary;
    wrapper.appendChild(summaryEl);
    
    // Show choices
    const choicesEl = document.createElement("div");
    choicesEl.className = "disambiguation-choices";
    
    choices.forEach((choice, index) => {
        const choiceBtn = document.createElement("button");
        choiceBtn.className = "disambiguation-choice";
        choiceBtn.textContent = `${choice.name} (ID: ${choice.id}) - Room: ${choice.room_no || 'Unassigned'}`;
        choiceBtn.dataset.choice = JSON.stringify(choice);
        choiceBtn.addEventListener("click", () => handleDisambiguationChoice(choice, summary));
        choicesEl.appendChild(choiceBtn);
    });
    
    wrapper.appendChild(choicesEl);
    return wrapper;
}

function handleDisambiguationChoice(choice, originalSummary) {
    // Clear disambiguation UI
    const disambEl = document.querySelector(".disambiguation-wrapper");
    if (disambEl) {
        disambEl.remove();
    }
    
    // Show selected choice
    appendMessage("user", `Selected: ${choice.name} (ID: ${choice.id})`);
    
    // Re-run the original query with the selected student ID
    const originalQuery = getLastUserQuery();
    if (originalQuery) {
        // Modify the query to use the specific student ID
        const modifiedQuery = originalQuery.replace(/\b(shiva|shiv)\b/gi, `student ID ${choice.id}`);
        sendViaREST(modifiedQuery);
    }
}

function getLastUserQuery() {
    const messages = document.querySelectorAll(".msg.user");
    if (messages.length > 0) {
        const lastUserMsg = messages[messages.length - 1];
        return lastUserMsg.textContent;
    }
    return null;
}

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
            if (res.status === 401) {
                appendMessage("error", "Unauthorized. Please log in.");
                return;
            }
            appendMessage("error", payload.detail || "Agent error");
            return;
        }
        // Expect { summary, data }
        if (payload.summary) appendMessage("agent", payload.summary, payload.data);
    } catch (err) {
        appendMessage("error", String(err));
    }
}

function connectWS() {
    if (socket && socket.readyState === WebSocket.OPEN) return;
    const wsUrl = BASE_URL.replace("http", "ws") + "/api/agent/ws/agent";
    socket = new WebSocket(wsUrl);

    socket.onopen = () => appendMessage("system", "WS connected");
    socket.onmessage = (event) => {
        try {
            const msg = JSON.parse(event.data);
            if (msg.summary) appendMessage("agent", msg.summary, msg.data);
            if (msg.error) appendMessage("error", msg.error);
        } catch (e) {
            appendMessage("agent", event.data);
        }
    };
    socket.onclose = () => appendMessage("system", "WS disconnected");
    socket.onerror = () => appendMessage("error", "WS error");
}

function sendViaWS(query) {
    if (!socket || socket.readyState !== WebSocket.OPEN) {
        appendMessage("error", "WS not connected. Using REST instead.");
        return sendViaREST(query);
    }
    appendMessage("user", query);
    socket.send(JSON.stringify({ query, session_id: sessionId }));
}

// Basic styles injection if not present (optional)
function ensureStyles() {
    const styleId = "agent-styles";
    if (document.getElementById(styleId)) return;
    const style = document.createElement("style");
    style.id = styleId;
    style.textContent = `
    .agent-chat { display: flex; flex-direction: column; height: 420px; }
    .agent-messages { flex: 1; overflow: auto; border: 1px solid #3333; padding: 8px; border-radius: 8px; background: var(--panel-bg, #fff); }
    .agent-form { margin-top: 8px; display: flex; }
    .agent-form input { flex: 1; margin-right: 8px; }
    .msg { padding: 6px 8px; margin: 6px 0; border-radius: 6px; }
    .msg.user { background: #e3f2fd; }
    .msg.agent { background: #f1f8e9; }
    .msg.system { background: #ede7f6; font-style: italic; }
    .msg.error { background: #ffebee; color: #b71c1c; }
    `;
    document.head.appendChild(style);
}

document.addEventListener("DOMContentLoaded", () => {
    ensureStyles();
    initAgentUI();
});
