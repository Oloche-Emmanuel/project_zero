import { api } from "../api.js";
import { openModal, toast, fmtDateTime, labelize, formToJson, escapeHtml } from "../ui.js";

const PRIORITIES = ["low", "medium", "high", "urgent"];
const STATUSES = ["open", "in_progress", "completed", "cancelled"];

export async function renderMaintenance(view, state) {
  const staff = state.user.role !== "tenant";
  view.innerHTML = `
    <div class="view-header">
      <h1>Maintenance requests</h1>
      <button id="add-maint" class="btn btn-primary">+ New request</button>
    </div>

    <div class="card" style="margin-bottom:20px">
      <h3>Look up by unit</h3>
      <div class="jump-row">
        <input id="unit-search" placeholder="Unit ID" inputmode="numeric" />
        <button id="unit-search-btn" class="btn btn-sm">Search</button>
      </div>
      <div id="unit-search-results"></div>
    </div>

    <div class="section-header"><h2>Open requests</h2></div>
    <div id="open-list" class="card"></div>
  `;

  const rerender = () => renderMaintenance(view, state);
  view.querySelector("#add-maint").addEventListener("click", () => openMaintenanceForm(rerender, { staff }));

  view.querySelector("#unit-search-btn").addEventListener("click", async () => {
    const unitId = view.querySelector("#unit-search").value.trim();
    const results = view.querySelector("#unit-search-results");
    if (!unitId) return;
    results.innerHTML = `<p class="muted">Searching…</p>`;
    try {
      const requests = await api.maintenanceByUnit(unitId);
      results.innerHTML = renderTable(requests, rerender, { staff });
      wireTable(results, rerender);
    } catch (err) {
      results.innerHTML = `<p class="error">${err.message}</p>`;
    }
  });

  const openList = view.querySelector("#open-list");
  try {
    const requests = await api.listOpenMaintenance();
    openList.innerHTML = renderTable(requests, rerender, { emptyText: "No open maintenance requests.", staff });
    wireTable(openList, rerender);
  } catch (err) {
    openList.innerHTML = `<p class="error">${err.message}</p>`;
  }
}

function renderTable(requests, _rerender, { emptyText = "No requests found.", staff = true } = {}) {
  if (!requests.length) return `<p class="muted">${emptyText}</p>`;
  return `
    <table class="table">
      <thead><tr><th>Title</th><th>Unit</th><th>Priority</th><th>Status</th><th>Filed</th><th></th></tr></thead>
      <tbody>
        ${requests
          .map(
            (r) => `
          <tr>
            <td>
              <div>${escapeHtml(r.title)}</div>
              <div class="muted" style="font-weight:400">${escapeHtml(r.description)}</div>
            </td>
            <td>${r.unit_id}</td>
            <td><span class="badge badge-${r.priority}">${labelize(r.priority)}</span></td>
            <td><span class="badge badge-${r.status}">${labelize(r.status)}</span></td>
            <td class="muted">${fmtDateTime(r.created_at)}</td>
            <td>${staff ? `<button class="btn btn-sm" data-manage="${r.id}">Manage</button>` : ""}</td>
          </tr>`
          )
          .join("")}
      </tbody>
    </table>
  `;
}

function wireTable(container, rerender) {
  container.querySelectorAll("[data-manage]").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const id = Number(btn.dataset.manage);
      try {
        const request = await api.getMaintenance(id);
        openManageForm(request, rerender);
      } catch (err) {
        toast(err.message, "error");
      }
    });
  });
}

function openManageForm(request, onDone) {
  const { close } = openModal(`Manage: ${request.title}`, `
    <form id="maint-manage-form">
      <p class="muted">${escapeHtml(request.description)}</p>
      <div class="form-row">
        <label>Priority
          <select name="priority">
            ${PRIORITIES.map((p) => `<option value="${p}" ${request.priority === p ? "selected" : ""}>${labelize(p)}</option>`).join("")}
          </select>
        </label>
        <label>Status
          <select name="status">
            ${STATUSES.map((s) => `<option value="${s}" ${request.status === s ? "selected" : ""}>${labelize(s)}</option>`).join("")}
          </select>
        </label>
      </div>
      <div class="form-actions"><button type="submit" class="btn btn-primary">Save changes</button></div>
    </form>
  `);
  const form = document.getElementById("maint-manage-form");
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const data = formToJson(form);
    try {
      await api.updateMaintenance(request.id, data);
      toast("Request updated", "success");
      close();
      onDone();
    } catch (err) {
      toast(err.message, "error");
    }
  });
}

export function openMaintenanceForm(onDone, { presetUnitId, staff = true } = {}) {
  const { close } = openModal("New maintenance request", `
    <form id="maint-form">
      ${
        presetUnitId
          ? `<input type="hidden" name="unit_id" value="${presetUnitId}" />`
          : `<label>Unit ID<input type="number" name="unit_id" required /></label>`
      }
      ${
        staff
          ? `<label>Tenant ID <span class="muted" style="font-weight:400">(optional)</span><input type="number" name="tenant_id" /></label>`
          : ""
      }
      <label>Title<input name="title" required /></label>
      <label>Description<textarea name="description" required></textarea></label>
      <label>Priority
        <select name="priority">
          ${PRIORITIES.map((p) => `<option value="${p}" ${p === "medium" ? "selected" : ""}>${labelize(p)}</option>`).join("")}
        </select>
      </label>
      <div class="form-actions"><button type="submit" class="btn btn-primary">Submit request</button></div>
    </form>
  `);
  const form = document.getElementById("maint-form");
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const data = formToJson(form, { skipEmpty: ["tenant_id"] });
    try {
      await api.createMaintenance(data);
      toast("Maintenance request submitted", "success");
      close();
      onDone();
    } catch (err) {
      toast(err.message, "error");
    }
  });
}
