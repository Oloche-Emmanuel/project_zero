import { api } from "../api.js";
import { openModal, toast, fmtDateTime, labelize, formToJson } from "../ui.js";

const ROLES = ["admin", "landlord", "tenant"];

export async function renderUsers(view) {
  view.innerHTML = `
    <div class="view-header">
      <h1>Users</h1>
      <button id="add-user" class="btn btn-primary">+ Add user</button>
    </div>
    <div id="user-list" class="card"><p class="muted">Loading…</p></div>
  `;
  const rerender = () => renderUsers(view);
  view.querySelector("#add-user").addEventListener("click", () => openUserCreateForm(rerender));

  const list = view.querySelector("#user-list");
  try {
    const users = await api.listUsers();
    list.innerHTML = `
      <table class="table">
        <thead><tr><th>Name</th><th>Email</th><th>Role</th><th>Status</th><th>Joined</th><th></th></tr></thead>
        <tbody>
          ${users
            .map(
              (u) => `
            <tr>
              <td>${u.full_name}</td>
              <td>${u.email}</td>
              <td><span class="badge">${labelize(u.role)}</span></td>
              <td><span class="badge ${u.is_active ? "badge-active" : "badge-cancelled"}">${u.is_active ? "Active" : "Inactive"}</span></td>
              <td class="muted">${fmtDateTime(u.created_at)}</td>
              <td><button class="btn btn-sm" data-edit="${u.id}">Edit</button></td>
            </tr>`
            )
            .join("")}
        </tbody>
      </table>
    `;
    list.querySelectorAll("[data-edit]").forEach((btn) => {
      btn.addEventListener("click", async () => {
        const user = users.find((u) => u.id === Number(btn.dataset.edit));
        openUserEditForm(user, rerender);
      });
    });
  } catch (err) {
    list.innerHTML = `<p class="error">${err.message}</p>`;
  }
}

function openUserEditForm(user, onDone) {
  const { close } = openModal(`Edit ${user.full_name}`, `
    <form id="user-edit-form">
      <label>Full name<input name="full_name" required value="${user.full_name}" /></label>
      <label>Status
        <select name="is_active">
          <option value="true" ${user.is_active ? "selected" : ""}>Active</option>
          <option value="false" ${!user.is_active ? "selected" : ""}>Inactive</option>
        </select>
      </label>
      <p class="muted">Email and role cannot be changed here.</p>
      <div class="form-actions"><button type="submit" class="btn btn-primary">Save changes</button></div>
    </form>
  `);
  const form = document.getElementById("user-edit-form");
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const data = formToJson(form);
    data.is_active = data.is_active === "true";
    try {
      await api.updateUser(user.id, data);
      toast("User updated", "success");
      close();
      onDone();
    } catch (err) {
      toast(err.message, "error");
    }
  });
}

function openUserCreateForm(onDone) {
  const { close } = openModal("Add user", `
    <form id="user-create-form">
      <label>Full name<input name="full_name" required /></label>
      <label>Email<input type="email" name="email" required /></label>
      <label>Temporary password<input type="password" name="password" required minlength="8" /></label>
      <label>Role
        <select name="role">
          ${ROLES.map((r) => `<option value="${r}" ${r === "tenant" ? "selected" : ""}>${labelize(r)}</option>`).join("")}
        </select>
      </label>
      <div class="form-actions"><button type="submit" class="btn btn-primary">Create user</button></div>
    </form>
  `);
  const form = document.getElementById("user-create-form");
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const data = formToJson(form);
    try {
      await api.register(data);
      toast("User created", "success");
      close();
      onDone();
    } catch (err) {
      toast(err.message, "error");
    }
  });
}
