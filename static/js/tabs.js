export function initTabs(loadCallbacks = {}) {
  const tabsEl = document.getElementById("tabs");
  const panels = {
    rooms: document.getElementById("panel-rooms"),
    students: document.getElementById("panel-students"),
    payments: document.getElementById("panel-payments"),
    agent: document.getElementById("panel-agent"),
  };

  tabsEl.addEventListener("click", (e) => {
    const btn = e.target.closest(".tab-btn");
    if (!btn) return;

    document.querySelectorAll(".tab-btn").forEach(b => b.classList.remove("active"));
    btn.classList.add("active");

    const tab = btn.dataset.tab;
    Object.entries(panels).forEach(([k, el]) => el.classList.toggle("active", k === tab));

    if (loadCallbacks[tab]) loadCallbacks[tab]();
  });
}
