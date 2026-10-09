import { api } from "../api.js";
import { navigate } from "../router.js";

export async function renderDashboard(view, state) {
  const staff = state.user.role !== "tenant";
  view.innerHTML = `
    <div class="view-header"><h1>Welcome back, ${escapeFirstName(state.user.full_name)}</h1></div>
    <div id="dash-body" class="grid"><div class="card muted">Loading…</div></div>
  `;
  const body = view.querySelector("#dash-body");
  try {
    const [properties, openMaint] = await Promise.all([
      staff ? api.listProperties() : Promise.resolve(null),
      api.listOpenMaintenance(),
    ]);
    body.innerHTML = `
      ${staff ? statCard("Properties", properties.length, "#/properties") : ""}
      ${statCard("Open maintenance requests", openMaint.length, "#/maintenance")}
      ${staff ? jumpCard() : ""}
    `;
    if (staff) wireJumpCard(body);
  } catch (err) {
    body.innerHTML = `<div class="card error">${err.message}</div>`;
  }
}

function escapeFirstName(fullName) {
  return (fullName || "").split(" ")[0] || "there";
}

function statCard(label, value, href) {
  return `
    <a class="card stat-card" href="${href}">
      <div class="stat-value">${value}</div>
      <div class="stat-label">${label}</div>
    </a>
  `;
}

function jumpCard() {
  return `
    <div class="card">
      <h3>Jump to a record</h3>
      <div class="jump-row">
        <input id="jump-unit" placeholder="Unit ID" inputmode="numeric" />
        <button class="btn btn-sm" data-jump="units">Go</button>
      </div>
      <div class="jump-row">
        <input id="jump-lease" placeholder="Lease ID" inputmode="numeric" />
        <button class="btn btn-sm" data-jump="leases">Go</button>
      </div>
    </div>
  `;
}

function wireJumpCard(body) {
  body.querySelectorAll("[data-jump]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const kind = btn.dataset.jump;
      const input = body.querySelector(kind === "units" ? "#jump-unit" : "#jump-lease");
      const val = input.value.trim();
      if (!val) return;
      navigate(`/${kind}/${val}`);
    });
  });
}
