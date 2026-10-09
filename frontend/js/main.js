import { api, getToken, setToken } from "./api.js";
import { route, resolve, navigate, currentPath } from "./router.js";
import { qs, qsa } from "./ui.js";
import { renderAuth } from "./views/auth.js";
import { renderDashboard } from "./views/dashboard.js";
import { renderProperties, renderPropertyDetail } from "./views/properties.js";
import { renderUnitDetail } from "./views/units.js";
import { renderTenants, renderTenantDetail } from "./views/tenants.js";
import { renderLeaseDetail } from "./views/leases.js";
import { renderMaintenance } from "./views/maintenance.js";
import { renderUsers } from "./views/users.js";
import { renderAccount } from "./views/account.js";

const appState = { user: null };
const appEl = qs("#app");

function isStaff() {
  return !!appState.user && appState.user.role !== "tenant";
}
function isAdmin() {
  return !!appState.user && appState.user.role === "admin";
}

async function boot() {
  const token = getToken();
  if (token) {
    try {
      appState.user = await api.me();
    } catch {
      setToken(null);
    }
  }
  registerRoutes();
  renderShell();
  await resolve();
}

async function onAuthed() {
  appState.user = await api.me();
  renderShell();
  navigate("/");
  await resolve();
}

function logout() {
  setToken(null);
  appState.user = null;
  renderShell();
  navigate("/login");
}

function renderShell() {
  if (!appState.user) {
    appEl.innerHTML = `<div id="auth-root" class="auth-page"></div>`;
    return;
  }
  appEl.innerHTML = `
    <div class="layout">
      <aside class="sidebar">
        <div class="brand">🏠 RentalHQ</div>
        <nav id="nav"></nav>
        <div class="sidebar-footer">
          <div class="user-chip">
            <div class="avatar">${appState.user.full_name.charAt(0).toUpperCase()}</div>
            <div>
              <div class="user-name">${appState.user.full_name}</div>
              <div class="user-role">${appState.user.role}</div>
            </div>
          </div>
          <button id="logout-btn" class="btn btn-ghost btn-sm">Log out</button>
        </div>
      </aside>
      <main class="content"><div id="view"></div></main>
    </div>
  `;
  renderNav();
  qs("#logout-btn").addEventListener("click", logout);
}

function renderNav() {
  const navEl = qs("#nav");
  if (!navEl) return;
  const items = [["/", "Dashboard"]];
  if (isStaff()) items.push(["/properties", "Properties"], ["/tenants", "Tenants"]);
  items.push(["/maintenance", "Maintenance"]);
  if (isAdmin()) items.push(["/users", "Users"]);
  items.push(["/account", "My Account"]);
  navEl.innerHTML = items
    .map(([href, label]) => `<a href="#${href}" class="nav-link" data-href="${href}">${label}</a>`)
    .join("");
  markActiveNav();
}

function markActiveNav() {
  const path = currentPath();
  qsa(".nav-link").forEach((a) => {
    const href = a.dataset.href;
    const active = href === "/" ? path === "/" : path === href || path.startsWith(href + "/");
    a.classList.toggle("active", active);
  });
}

function guarded(renderFn) {
  if (!appState.user) {
    navigate("/login");
    return;
  }
  markActiveNav();
  return renderFn(qs("#view"), appState);
}

function registerRoutes() {
  route("/login", () => {
    if (appState.user) {
      navigate("/");
      return;
    }
    renderAuth(qs("#auth-root"), "login", onAuthed);
  });
  route("/register", () => {
    if (appState.user) {
      navigate("/");
      return;
    }
    renderAuth(qs("#auth-root"), "register", onAuthed);
  });

  route("/", (p) => guarded((view, state) => renderDashboard(view, state)));
  route("/properties", () => guarded((view, state) => renderProperties(view, state)));
  route("/properties/:id", (p) => guarded((view, state) => renderPropertyDetail(view, state, p.id)));
  route("/units/:id", (p) => guarded((view, state) => renderUnitDetail(view, state, p.id)));
  route("/tenants", () => guarded((view, state) => renderTenants(view, state)));
  route("/tenants/:id", (p) => guarded((view, state) => renderTenantDetail(view, state, p.id)));
  route("/leases/:id", (p) => guarded((view, state) => renderLeaseDetail(view, state, p.id)));
  route("/maintenance", () => guarded((view, state) => renderMaintenance(view, state)));
  route("/users", () => guarded((view, state) => (isAdmin() ? renderUsers(view, state) : navigate("/"))));
  route("/account", () => guarded((view, state) => renderAccount(view, state)));
}

boot();
