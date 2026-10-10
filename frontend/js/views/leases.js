import { api } from "../api.js";
import { openModal, toast, fmtMoney, fmtDate, labelize, formToJson, escapeHtml } from "../ui.js";

export async function renderLeaseDetail(view, state, idStr) {
  const id = Number(idStr);
  const staff = state.user.role !== "tenant";
  view.innerHTML = `<p class="muted">Loading…</p>`;

  let lease, invoices;
  try {
    lease = await api.getLease(id);
    invoices = await api.invoicesByLease(id).catch(() => []);
  } catch (err) {
    view.innerHTML = `<p class="error">${err.message}</p>`;
    return;
  }

  const rerender = () => renderLeaseDetail(view, state, idStr);

  view.innerHTML = `
    <div class="view-header">
      <div>
        <a href="#/units/${lease.unit_id}" class="back-link">← Unit ${lease.unit_id}</a>
        <h1>Lease #${lease.id}</h1>
        <p class="muted">Unit ${lease.unit_id} · Tenant ${lease.tenant_id} · ${fmtDate(lease.start_date)} → ${fmtDate(lease.end_date)}</p>
      </div>
      <div class="header-actions">
        <span class="badge badge-${lease.status}">${labelize(lease.status)}</span>
        ${staff ? `<button id="edit-lease" class="btn">Edit</button>` : ""}
        ${staff && lease.status === "active" ? `<button id="terminate-lease" class="btn btn-danger">Terminate</button>` : ""}
      </div>
    </div>

    <div class="grid" style="margin-bottom:8px">
      <div class="card"><div class="stat-label">Rent</div><div class="stat-value" style="font-size:20px">${fmtMoney(lease.rent_amount)}</div></div>
      <div class="card"><div class="stat-label">Security deposit</div><div class="stat-value" style="font-size:20px">${fmtMoney(lease.security_deposit)}</div></div>
    </div>

    <div class="section-header">
      <h2>Invoices</h2>
      ${
        staff
          ? `<div class="header-actions">
              <button id="refresh-overdue" class="btn btn-sm">Refresh overdue</button>
              <button id="add-invoice" class="btn btn-primary btn-sm">+ New invoice</button>
            </div>`
          : ""
      }
    </div>
    <div id="invoices-list" class="card"></div>
  `;

  if (staff) {
    view.querySelector("#edit-lease").addEventListener("click", () => openLeaseEditForm(lease, rerender));
    const termBtn = view.querySelector("#terminate-lease");
    if (termBtn) {
      termBtn.addEventListener("click", async () => {
        if (!confirm("Terminate this lease?")) return;
        try {
          await api.terminateLease(id);
          toast("Lease terminated", "success");
          rerender();
        } catch (err) {
          toast(err.message, "error");
        }
      });
    }
    view.querySelector("#add-invoice").addEventListener("click", () => openInvoiceForm(id, rerender));
    view.querySelector("#refresh-overdue").addEventListener("click", async () => {
      try {
        await api.refreshOverdue();
        toast("Overdue statuses refreshed", "success");
        rerender();
      } catch (err) {
        toast(err.message, "error");
      }
    });
  }

  const invoicesList = view.querySelector("#invoices-list");
  if (!invoices.length) {
    invoicesList.innerHTML = `<p class="muted">No invoices yet.</p>`;
    return;
  }
  invoicesList.innerHTML = `
    <table class="table">
      <thead><tr><th>Due</th><th>Amount due</th><th>Paid</th><th>Status</th><th>Notes</th>${staff ? "<th></th>" : ""}</tr></thead>
      <tbody>
        ${invoices
          .map(
            (inv) => `
          <tr>
            <td>${fmtDate(inv.due_date)}</td>
            <td>${fmtMoney(inv.amount_due)}</td>
            <td>${fmtMoney(inv.amount_paid)}</td>
            <td><span class="badge badge-${inv.status}">${labelize(inv.status)}</span></td>
            <td class="muted">${escapeHtml(inv.notes ?? "—")}</td>
            ${
              staff
                ? `<td>${
                    inv.status !== "paid"
                      ? `<button class="btn btn-sm" data-pay="${inv.id}">Record payment</button>`
                      : ""
                  }</td>`
                : ""
            }
          </tr>`
          )
          .join("")}
      </tbody>
    </table>
  `;
  if (staff) {
    invoicesList.querySelectorAll("[data-pay]").forEach((btn) => {
      btn.addEventListener("click", () => openPaymentForm(Number(btn.dataset.pay), rerender));
    });
  }
}

function openLeaseEditForm(lease, onDone) {
  const { close } = openModal("Edit lease", `
    <form id="lease-edit-form">
      <div class="form-row">
        <label>End date<input type="date" name="end_date" value="${lease.end_date}" /></label>
        <label>Rent amount<input type="number" step="0.01" name="rent_amount" value="${lease.rent_amount}" /></label>
      </div>
      <label>Security deposit<input type="number" step="0.01" name="security_deposit" value="${lease.security_deposit}" /></label>
      <label>Status
        <select name="status">
          ${["active", "expired", "terminated"]
            .map((s) => `<option value="${s}" ${lease.status === s ? "selected" : ""}>${labelize(s)}</option>`)
            .join("")}
        </select>
      </label>
      <div class="form-actions"><button type="submit" class="btn btn-primary">Save changes</button></div>
    </form>
  `);
  const form = document.getElementById("lease-edit-form");
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const data = formToJson(form);
    try {
      await api.updateLease(lease.id, data);
      toast("Lease updated", "success");
      close();
      onDone();
    } catch (err) {
      toast(err.message, "error");
    }
  });
}

function openInvoiceForm(leaseId, onDone) {
  const { close } = openModal("New invoice", `
    <form id="invoice-form">
      <input type="hidden" name="lease_id" value="${leaseId}" />
      <div class="form-row">
        <label>Amount due<input type="number" step="0.01" name="amount_due" required /></label>
        <label>Due date<input type="date" name="due_date" required /></label>
      </div>
      <label>Notes<textarea name="notes"></textarea></label>
      <div class="form-actions"><button type="submit" class="btn btn-primary">Create invoice</button></div>
    </form>
  `);
  const form = document.getElementById("invoice-form");
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const data = formToJson(form, { skipEmpty: ["notes"] });
    data.lease_id = Number(data.lease_id);
    try {
      await api.createInvoice(data);
      toast("Invoice created", "success");
      close();
      onDone();
    } catch (err) {
      toast(err.message, "error");
    }
  });
}

function openPaymentForm(invoiceId, onDone) {
  const { close } = openModal("Record payment", `
    <form id="payment-form">
      <label>Amount<input type="number" step="0.01" min="0.01" name="amount" required /></label>
      <label>Payment method<input name="payment_method" required placeholder="e.g. bank transfer, check" /></label>
      <label>Paid date<input type="date" name="paid_date" /></label>
      <div class="form-actions"><button type="submit" class="btn btn-primary">Record payment</button></div>
    </form>
  `);
  const form = document.getElementById("payment-form");
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const data = formToJson(form, { skipEmpty: ["paid_date"] });
    try {
      await api.recordPayment(invoiceId, data);
      toast("Payment recorded", "success");
      close();
      onDone();
    } catch (err) {
      toast(err.message, "error");
    }
  });
}

/**
 * Shared "new lease" modal, usable from either a unit page (unit preset) or
 * a tenant page (tenant preset) — the other side is picked from a dropdown.
 */
export async function openLeaseForm(onDone, { presetUnitId, presetTenantId } = {}) {
  let unitField;
  let tenantField;

  if (presetUnitId) {
    unitField = `<input type="hidden" name="unit_id" value="${presetUnitId}" />`;
  } else {
    const properties = await api.listProperties();
    unitField = `
      <label>Property
        <select id="lease-property-select">
          <option value="">Select a property</option>
          ${properties.map((p) => `<option value="${p.id}">${escapeHtml(p.name)}</option>`).join("")}
        </select>
      </label>
      <label>Unit
        <select name="unit_id" id="lease-unit-select" required disabled>
          <option value="">Select a property first</option>
        </select>
      </label>
    `;
  }

  if (presetTenantId) {
    tenantField = `<input type="hidden" name="tenant_id" value="${presetTenantId}" />`;
  } else {
    const tenants = await api.listTenants();
    tenantField = `
      <label>Tenant
        <select name="tenant_id" required>
          <option value="">Select a tenant</option>
          ${tenants.map((t) => `<option value="${t.id}">${escapeHtml(t.first_name)} ${escapeHtml(t.last_name)}</option>`).join("")}
        </select>
      </label>
    `;
  }

  const { close } = openModal("New lease", `
    <form id="lease-form">
      ${unitField}
      ${tenantField}
      <div class="form-row">
        <label>Start date<input type="date" name="start_date" required /></label>
        <label>End date<input type="date" name="end_date" required /></label>
      </div>
      <div class="form-row">
        <label>Rent amount<input type="number" step="0.01" name="rent_amount" required /></label>
        <label>Security deposit<input type="number" step="0.01" name="security_deposit" value="0" /></label>
      </div>
      <div class="form-actions"><button type="submit" class="btn btn-primary">Create lease</button></div>
    </form>
  `);

  const form = document.getElementById("lease-form");

  if (!presetUnitId) {
    const propSelect = form.querySelector("#lease-property-select");
    const unitSelect = form.querySelector("#lease-unit-select");
    propSelect.addEventListener("change", async () => {
      const pid = propSelect.value;
      if (!pid) {
        unitSelect.innerHTML = `<option value="">Select a property first</option>`;
        unitSelect.disabled = true;
        return;
      }
      unitSelect.innerHTML = `<option value="">Loading…</option>`;
      unitSelect.disabled = true;
      const units = await api.listUnits(pid);
      unitSelect.disabled = false;
      unitSelect.innerHTML =
        `<option value="">Select a unit</option>` +
        units.map((u) => `<option value="${u.id}">${escapeHtml(u.unit_number)} — ${fmtMoney(u.rent_amount)}/mo</option>`).join("");
    });
  }

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const data = formToJson(form);
    try {
      await api.createLease(data);
      toast("Lease created", "success");
      close();
      onDone();
    } catch (err) {
      toast(err.message, "error");
    }
  });
}
