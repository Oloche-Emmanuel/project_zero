import { fmtDateTime, labelize } from "../ui.js";

export async function renderAccount(view, state) {
  const u = state.user;
  view.innerHTML = `
    <div class="view-header"><h1>My account</h1></div>
    <div class="card" style="max-width:420px">
      <div class="form-row" style="grid-template-columns:1fr">
        <label>Full name<input value="${u.full_name}" disabled /></label>
        <label>Email<input value="${u.email}" disabled /></label>
        <label>Role<input value="${labelize(u.role)}" disabled /></label>
        <label>Member since<input value="${fmtDateTime(u.created_at)}" disabled /></label>
      </div>
      ${u.role !== "admin"
        ? `<p class="muted" style="margin-top:8px">Profile edits are managed by an administrator.</p>`
        : `<p class="muted" style="margin-top:8px">As an admin, you can edit any account (including your own) from <a href="#/users">Users</a>.</p>`}
    </div>
  `;
}
