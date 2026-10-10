import { api } from "../api.js";
import { openModal, toast, fmtMoney, fmtDate, labelize, formToJson, escapeHtml } from "../ui.js";
import { navigate } from "../router.js";
import { openLeaseForm } from "./leases.js";

export async function renderTenants(view) {
  view.innerHTML = `
    <div class="view-header">
      <h1>Tenants</h1>
      <button id="add-tenant" class="btn btn-primary">+ Add tenant</button>
    </div>
    <div id="tenant-list" class="card"><p class="muted">Loading…</p></div>
  `;
  view.querySelector("#add-tenant").addEventListener("click", () => openTenantForm(() => renderTenants(view)));

  const list = view.querySelector("#tenant-list");
  try {
    const tenants = await api.listTenants();
    if (!tenants.length) {
      list.innerHTML = `<p class="muted">No tenants yet. Add your first one.</p>`;
      return;
    }
    list.innerHTML = `
      <table class="table">
        <thead><tr><th>Name</th><th>Email</th><th>Phone</th><th></th></tr></thead>
        <tbody>
          ${tenants
            .map(
              (t) => `
            <tr class="row-link" data-href="/tenants/${t.id}">
              <td>${escapeHtml(t.first_name)} ${escapeHtml(t.last_name)}</td>
              <td>${escapeHtml(t.email)}</td>
              <td>${escapeHtml(t.phone ?? "—")}</td>
              <td><a href="#/tenants/${t.id}">View →</a></td>
            </tr>`
            )
            .join("")}
        </tbody>
      </table>
    `;
    list.querySelectorAll(".row-link").forEach((tr) =>
      tr.addEventListener("click", (e) => {
        if (e.target.tagName === "A") return;
        navigate(tr.dataset.href);
      })
    );
  } catch (err) {
    list.innerHTML = `<p class="error">${err.message}</p>`;
  }
}

export async function renderTenantDetail(view, state, idStr) {
  const id = Number(idStr);
  view.innerHTML = `<p class="muted">Loading…</p>`;

  let tenant, leases;
  try {
    tenant = await api.getTenant(id);
  } catch (err) {
    view.innerHTML = `<p class="error">${err.message}</p>`;
    return;
  }
  leases = await api.leasesByTenant(id).catch(() => []);

  const rerender = () => renderTenantDetail(view, state, idStr);

  view.innerHTML = `
    <div class="view-header">
      <div>
        <a href="#/tenants" class="back-link">← Tenants</a>
        <h1>${escapeHtml(tenant.first_name)} ${escapeHtml(tenant.last_name)}</h1>
        <p class="muted">${escapeHtml(tenant.email)}${tenant.phone ? ` · ${escapeHtml(tenant.phone)}` : ""}</p>
      </div>
      <div class="header-actions">
        <button id="edit-tenant" class="btn">Edit</button>
        <button id="delete-tenant" class="btn btn-danger">Delete</button>
      </div>
    </div>

    <div class="card" style="margin-bottom:20px">
      <h3>Emergency contact</h3>
      <p class="muted">
        ${tenant.emergency_contact_name ? `${escapeHtml(tenant.emergency_contact_name)}${tenant.emergency_contact_phone ? " · " + escapeHtml(tenant.emergency_contact_phone) : ""}` : "Not on file"}
      </p>
    </div>

    <div class="section-header">
      <h2>Leases</h2>
      <button id="add-lease" class="btn btn-primary btn-sm">+ New lease</button>
    </div>
    <div id="leases-list" class="card"></div>
  `;

  view.querySelector("#edit-tenant").addEventListener("click", () => openTenantForm(rerender, tenant));
  view.querySelector("#delete-tenant").addEventListener("click", async () => {
    if (!confirm(`Delete tenant "${tenant.first_name} ${tenant.last_name}"?`)) return;
    try {
      await api.deleteTenant(id);
      toast("Tenant deleted", "success");
      navigate("/tenants");
    } catch (err) {
      toast(err.message, "error");
    }
  });
  view.querySelector("#add-lease").addEventListener("click", () => {
    openLeaseForm(rerender, { presetTenantId: id });
  });

  const leasesList = view.querySelector("#leases-list");
  if (!leases.length) {
    leasesList.innerHTML = `<p class="muted">No leases for this tenant yet.</p>`;
    return;
  }
  leasesList.innerHTML = `
    <table class="table">
      <thead><tr><th>Lease</th><th>Unit</th><th>Dates</th><th>Rent</th><th>Status</th></tr></thead>
      <tbody>
        ${leases
          .map(
            (l) => `
          <tr class="row-link" data-href="/leases/${l.id}">
            <td>#${l.id}</td>
            <td>Unit ${l.unit_id}</td>
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

function openTenantForm(onDone, existing) {
  const isEdit = !!existing;
  const { close } = openModal(isEdit ? "Edit tenant" : "Add tenant", `
    <form id="tenant-form">
      <div class="form-row">
        <label>First name<input name="first_name" required value="${escapeHtml(existing?.first_name ?? "")}" /></label>
        <label>Last name<input name="last_name" required value="${escapeHtml(existing?.last_name ?? "")}" /></label>
      </div>
      <label>Email<input type="email" name="email" required value="${escapeHtml(existing?.email ?? "")}" /></label>
      <label>Phone<input name="phone" value="${escapeHtml(existing?.phone ?? "")}" /></label>
      <label>Date of birth<input type="date" name="date_of_birth" value="${existing?.date_of_birth ?? ""}" /></label>
      <div class="form-row">
        <label>Emergency contact name<input name="emergency_contact_name" value="${escapeHtml(existing?.emergency_contact_name ?? "")}" /></label>
        <label>Emergency contact phone<input name="emergency_contact_phone" value="${escapeHtml(existing?.emergency_contact_phone ?? "")}" /></label>
      </div>
      <div class="form-actions">
        <button type="submit" class="btn btn-primary">${isEdit ? "Save changes" : "Add tenant"}</button>
      </div>
    </form>
  `);

  const form = document.getElementById("tenant-form");
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const data = formToJson(form, {
      skipEmpty: ["phone", "date_of_birth", "emergency_contact_name", "emergency_contact_phone"],
    });
    try {
      if (isEdit) await api.updateTenant(existing.id, data);
      else await api.createTenant(data);
      toast(isEdit ? "Tenant updated" : "Tenant added", "success");
      close();
      onDone();
    } catch (err) {
      toast(err.message, "error");
    }
  });
}
