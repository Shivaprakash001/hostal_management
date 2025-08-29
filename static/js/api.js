import { authManager } from "./auth.js";
import { BASE_URL } from "./config.js";

function getAuthHeaders() {
    return authManager.getAuthHeaders();
}

export async function api(path, { method = "GET", body, headers } = {}) {
  const res = await fetch(`${BASE_URL}${path}`, {
    method,
    headers: { "Content-Type": "application/json", ...getAuthHeaders(), ...(headers || {}) },
    body: body ? JSON.stringify(body) : undefined,
  });

  if (!res.ok) {
    let detail = res.statusText;
    try { const data = await res.json(); detail = data.detail || JSON.stringify(data); } catch {}
    throw new Error(`${res.status} ${detail}`);
  }

  const text = await res.text();
  return text ? JSON.parse(text) : null;
}

export const money = (n) => `₹${Number(n || 0).toFixed(2)}`;
