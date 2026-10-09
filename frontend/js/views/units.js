import { api } from "../api.js";
import { fmtMoney, fmtDate, labelize } from "../ui.js";
import { navigate } from "../router.js";
import { openUnitForm } from "./properties.js";
import { openLeaseForm } from "./leases.js";
import { openMaintenanceForm } from "./maintenance.js";

export async function renderUnitDetail(view, state, idStr) {
  const unitId = Number(idStr);
  const staff = state.user.role !== "tenant";
  view.innerHTML = `<p class="muted">Loading…</p>`;

  let unit, leases, requests;
  try {
    unit = await api.getUnit(unitId);
  } catch (err) {
    view.innerHTML = `<p class="error">${err.message}</p>`;
    return;
  }
  [leases, requests] = await Promise.all([
    api.leasesByUnit(unitId).catch(() => []),
    api.maintenanceByUnit(unitId).catch(() => []),
  ]);

  const rerender = () => renderUnitDetail(view, state, idStr);

  view.innerHTML = `
    <div class="view-header">
      <div>
        <a href="#/properties/${unit.property_id}" class="back-link">← Property ${unit.property_id}</a>
        <h1>Unit ${unit.unit_number}</h1>
        <p class="muted">${unit.bedrooms} bd / ${unit.bathrooms} ba${unit.square_feet ? ` · ${unit.square_feet} sqft` : ""} · ${fmtMoney(unit.rent_amount)}/mo</p>
      </div>
      <div class="header-actions">
        <span class="badge badge-${unit.status}">${labelize(unit.status)}</span>
        ${staff ? `<button id="edit-unit" class="btn">Edit</button>` : ""}
      </div>
    </div>

    ${
      staff
        ? `<div class="section-header">
            <h2>Leases</h2>
            <button id="add-lease" class="btn btn-primary btn-sm">+ New lease</button>
          </div>
          <div id="leases-list" class="card"></div>`
        : ""
    }

    <div class="section-header">
      <h2>Maintenance requests</h2>
      <button id="add-maint" class="btn btn-primary btn-sm">+ New request</button>
    </div>
    <div id="maint-list" class="card"></div>
  `;

  if (staff) {
    view.querySelector("#edit-unit").addEventListener("click", () => openUnitForm(unit.property_id, rerender, unit));
    view.querySelector("#add-lease").addEventListener("click", () => {
      openLeaseForm(rerender, { presetUnitId: unitId });
    });

    const leasesList = view.querySelector("#leases-list");
    if (!leases.length) {
      leasesList.innerHTML = `<p class="muted">No leases for this unit yet.</p>`;
    } else {
      leasesList.innerHTML = `
        <table class="table">
          <thead><tr><th>Lease</th><th>Tenant</th><th>Dates</th><th>Rent</th><th>Status</th></tr></thead>
          <tbody>
            ${leases
              .map(
                (l) => `
              <tr class="row-link" data-href="/leases/${l.id}">
                <td>#${l.id}</td>
                <td>Tenant ${l.tenant_id}</td>
                <td>${fmtDate(l.start_date)} → ${fmtDate(l.end_date)}</td>
                <td>${fmtMoney(l.rent_amount)}</td>
                <td><span class="badge badge-${l.status}">${labelize(l.status)}</span></td>
              </tr>`
              )
              .join("")}
          </tbody>
        </table>
      `;
      leasesList.querySelectorAll(".row-link").forEach((tr) => tr.addEventListener("click", () => navigate(tr.dataset.href)));
    }
  }

  view.querySelector("#add-maint").addEventListener("click", () => {
    openMaintenanceForm(rerender, { presetUnitId: unitId });
  });

  const maintList = view.querySelector("#maint-list");
  if (!requests.length) {
    maintList.innerHTML = `<p class="muted">No maintenance requests for this unit.</p>`;
    return;
  }
  maintList.innerHTML = `
    <table class="table">
      <thead><tr><th>Title</th><th>Priority</th><th>Status</th><th>Filed</th></tr></thead>
      <tbody>
        ${requests
          .map(
            (r) => `
          <tr>
            <td>${r.title}</td>
            <td><span class="badge badge-${r.priority}">${labelize(r.priority)}</span></td>
            <td><span class="badge badge-${r.status}">${labelize(r.status)}</span></td>
            <td class="muted">${fmtDate(r.created_at?.slice(0, 10))}</td>
          </tr>`
          )
          .join("")}
      </tbody>
    </table>
  `;
}
