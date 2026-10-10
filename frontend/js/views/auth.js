import { api, setToken } from "../api.js";
import { toast } from "../ui.js";

export function renderAuth(root, mode, onAuthed) {
  root.innerHTML = `
    <div class="auth-card">
      <div class="auth-brand">🏠 RentalHQ</div>
      <h1>${mode === "login" ? "Sign in" : "Create your account"}</h1>
      ${mode === "login" ? loginForm() : registerForm()}
      <p class="auth-switch">
        ${mode === "login"
          ? `New here? <a href="#/register">Create an account</a>`
          : `Already have an account? <a href="#/login">Sign in</a>`}
      </p>
    </div>
  `;

  const form = root.querySelector("form");
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const fd = new FormData(form);
    const btn = form.querySelector("button[type=submit]");
    btn.disabled = true;
    try {
      if (mode === "login") {
        const { access_token } = await api.login(fd.get("email"), fd.get("password"));
        setToken(access_token);
      } else {
        await api.register({
          email: fd.get("email"),
          password: fd.get("password"),
          full_name: fd.get("full_name"),
          role: fd.get("role"),
        });
        const { access_token } = await api.login(fd.get("email"), fd.get("password"));
        setToken(access_token);
      }
      await onAuthed();
    } catch (err) {
      toast(err.message || "Something went wrong", "error");
    } finally {
      btn.disabled = false;
    }
  });
}

function loginForm() {
  return `
    <form>
      <label>Email<input type="email" name="email" required autocomplete="username" /></label>
      <label>Password<input type="password" name="password" required autocomplete="current-password" /></label>
      <button class="btn btn-primary" type="submit">Sign in</button>
    </form>
  `;
}

function registerForm() {
  return `
    <form>
      <label>Full name<input type="text" name="full_name" required /></label>
      <label>Email<input type="email" name="email" required autocomplete="username" /></label>
      <label>Password<input type="password" name="password" required minlength="8" autocomplete="new-password" /></label>
      <label>I am a…
        <select name="role">
          <option value="landlord">Landlord</option>
          <option value="tenant">Tenant</option>
        </select>
      </label>
      <button class="btn btn-primary" type="submit">Create account</button>
    </form>
  `;
}
