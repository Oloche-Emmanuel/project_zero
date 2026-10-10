import { api } from "../api.js";
import { openModal, toast, fmtMoney, labelize, formToJson, escapeHtml } from "../ui.js";
import { navigate } from "../router.js";

const PROPERTY_TYPES = ["single_family", "multi_family", "apartment", "condo", "commercial"];
const UNIT_STATUSES = ["vacant", "occupied", "maintenance"];

export async function renderProperties(view, state) {
  const canEdit = state.user.role !== "tenant";
  view.innerHTML = `
    <div class="view-header">
      <h1>Properties</h1>
      ${canEdit ? `<button id="add-property" class="btn btn-primary">+ Add property</button>` : ""}
    </div>
    <div id="prop-list" class="card"><p class="muted">Loading…</p></div>
  `;
  if (canEdit) {
    view.querySelector("#add-property").addEventListener("click", () => {
      openPropertyForm(() => renderProperties(view, state));
    });
  }

  const list = view.querySelector("#prop-list");
  try {
    const properties = await api.listProperties();
    if (!properties.length) {
      list.innerHTML = `<p class="muted">No properties yet${canEdit ? ". Add your first one." : "."}</p>`;
      return;
    }
    list.innerHTML = `
      <table class="table">
        <thead><tr><th>Name</th><th>Address</th><th>Type</th><th></th></tr></thead>
        <tbody>
          ${properties
            .map(
              (p) => `
            <tr class="row-link" data-href="/properties/${p.id}">
              <td>${escapeHtml(p.name)}</td>
              <td>${escapeHtml(p.address_line1)}, ${escapeHtml(p.city)}, ${escapeHtml(p.state)} ${escapeHtml(p.zip_code)}</td>
              <td><span class="badge">${labelize(p.property_type)}</span></td>
              <td><a href="#/properties/${p.id}">View units →</a></td>
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

export async function renderPropertyDetail(view, state, idStr) {
  const id = Number(idStr);
  const canEdit = state.user.role !== "tenant";
  view.innerHTML = `<p class="muted">Loading…</p>`;

  let prop, units;
  try {
    [prop, units] = await Promise.all([api.getProperty(id), api.listUnits(id)]);
  } catch (err) {
    view.innerHTML = `<p class="error">${err.message}</p>`;
    return;
  }

  const rerender = () => renderPropertyDetail(view, state, idStr);

  view.innerHTML = `
    <div class="view-header">
      <div>
        <a href="#/properties" class="back-link">← Properties</a>
        <h1>${escapeHtml(prop.name)}</h1>
        <p class="muted">${escapeHtml(prop.address_line1)}, ${escapeHtml(prop.city)}, ${escapeHtml(prop.state)} ${escapeHtml(prop.zip_code)} · ${labelize(prop.property_type)}</p>
      </div>
      ${
        canEdit
          ? `<div class="header-actions">
              <button id="edit-prop" class="btn">Edit</button>
              <button id="delete-prop" class="btn btn-danger">Delete</button>
            </div>`
          : ""
      }
    </div>

    <div class="section-header">
      <h2>Units</h2>
      ${canEdit ? `<button id="add-unit" class="btn btn-primary btn-sm">+ Add unit</button>` : ""}
    </div>
    <div id="units-list" class="card"></div>
  `;

  if (canEdit) {
    view.querySelector("#edit-prop").addEventListener("click", () => {
      openPropertyForm(rerender, prop);
    });
    view.querySelector("#delete-prop").addEventListener("click", async () => {
      if (!confirm(`Delete "${prop.name}"? This also removes its units.`)) return;
      try {
        await api.deleteProperty(id);
        toast("Property deleted", "success");
        navigate("/properties");
      } catch (err) {
        toast(err.message, "error");
      }
    });
    view.querySelector("#add-unit").addEventListener("click", () => {
      openUnitForm(id, rerender);
    });
  }

  const unitsList = view.querySelector("#units-list");
  if (!units.length) {
    unitsList.innerHTML = `<p class="muted">No units yet.</p>`;
    return;
  }
  unitsList.innerHTML = `
    <table class="table">
      <thead><tr><th>Unit</th><th>Beds / Baths</th><th>Rent</th><th>Status</th><th></th></tr></thead>
      <tbody>
        ${units
          .map(
            (u) => `
          <tr class="row-link" data-href="/units/${u.id}">
            <td>${escapeHtml(u.unit_number)}</td>
            <td>${u.bedrooms} bd / ${u.bathrooms} ba</td>
            <td>${fmtMoney(u.rent_amount)}</td>
            <td><span class="badge badge-${u.status}">${labelize(u.status)}</span></td>
            <td><a href="#/units/${u.id}">Manage →</a></td>
          </tr>`
          )
          .join("")}
      </tbody>
    </table>
  `;
  unitsList.querySelectorAll(".row-link").forEach((tr) =>
    tr.addEventListener("click", (e) => {
      if (e.target.tagName === "A") return;
      navigate(tr.dataset.href);
    })
  );
}

function openPropertyForm(onDone, existing) {
  const isEdit = !!existing;
  const { close } = openModal(isEdit ? "Edit property" : "Add property", `
    <form id="property-form">
      <label>Name<input name="name" required value="${escapeHtml(existing?.name ?? "")}" /></label>
      <label>Address<input name="address_line1" required value="${escapeHtml(existing?.address_line1 ?? "")}" /></label>
      <div class="form-row">
        <label>City<input name="city" required value="${escapeHtml(existing?.city ?? "")}" /></label>
        <label>State<input name="state" required value="${escapeHtml(existing?.state ?? "")}" /></label>
        <label>ZIP<input name="zip_code" required value="${escapeHtml(existing?.zip_code ?? "")}" /></label>
      </div>
      <label>Type
        <select name="property_type">
          ${PROPERTY_TYPES.map(
            (t) => `<option value="${t}" ${existing?.property_type === t ? "selected" : ""}>${labelize(t)}</option>`
          ).join("")}
        </select>
      </label>
      <div class="form-actions">
        <button type="submit" class="btn btn-primary">${isEdit ? "Save changes" : "Create property"}</button>
      </div>
    </form>
  `);

  const form = document.getElementById("property-form");
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const data = formToJson(form);
    try {
      if (isEdit) await api.updateProperty(existing.id, data);
      else await api.createProperty(data);
      toast(isEdit ? "Property updated" : "Property created", "success");
      close();
      onDone();
    } catch (err) {
      toast(err.message, "error");
    }
  });
}

function openUnitForm(propertyId, onDone, existing) {
  const isEdit = !!existing;
  const { close } = openModal(isEdit ? `Edit unit ${existing.unit_number}` : "Add unit", `
    <form id="unit-form">
      <label>Unit number<input name="unit_number" required value="${escapeHtml(existing?.unit_number ?? "")}" /></label>
      <div class="form-row">
        <label>Bedrooms<input type="number" min="0" name="bedrooms" value="${existing?.bedrooms ?? 1}" /></label>
        <label>Bathrooms<input type="number" min="0" step="0.5" name="bathrooms" value="${existing?.bathrooms ?? 1}" /></label>
      </div>
      <div class="form-row">
        <label>Square feet<input type="number" min="0" name="square_feet" value="${existing?.square_feet ?? ""}" /></label>
        <label>Rent / month<input type="number" min="0" step="0.01" name="rent_amount" required value="${existing?.rent_amount ?? ""}" /></label>
      </div>
      ${
        isEdit
          ? `<label>Status
              <select name="status">
                ${UNIT_STATUSES.map(
                  (s) => `<option value="${s}" ${existing.status === s ? "selected" : ""}>${labelize(s)}</option>`
                ).join("")}
              </select>
            </label>`
          : ""
      }
      <div class="form-actions">
        <button type="submit" class="btn btn-primary">${isEdit ? "Save changes" : "Add unit"}</button>
      </div>
    </form>
  `);

  const form = document.getElementById("unit-form");
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const data = formToJson(form, { skipEmpty: ["square_feet"] });
    try {
      if (isEdit) await api.updateUnit(existing.id, data);
      else await api.addUnit(propertyId, data);
      toast(isEdit ? "Unit updated" : "Unit added", "success");
      close();
      onDone();
    } catch (err) {
      toast(err.message, "error");
    }
  });
}

export { openUnitForm };
