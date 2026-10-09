export function qs(sel, root = document) {
  return root.querySelector(sel);
}

export function qsa(sel, root = document) {
  return [...root.querySelectorAll(sel)];
}

export function el(html) {
  const t = document.createElement("template");
  t.innerHTML = html.trim();
  return t.content.firstElementChild;
}

export function escapeHtml(str) {
  return String(str ?? "").replace(/[&<>"']/g, (c) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;",
  }[c]));
}

export function labelize(value) {
  if (!value) return "";
  return String(value)
    .split("_")
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(" ");
}

export function fmtMoney(n) {
  const num = Number(n ?? 0);
  return `$${num.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

export function fmtDate(d) {
  if (!d) return "—";
  return d;
}

export function fmtDateTime(d) {
  if (!d) return "—";
  try {
    return new Date(d).toLocaleString();
  } catch {
    return d;
  }
}

let toastHost = null;
export function toast(message, kind = "info") {
  if (!toastHost) toastHost = document.getElementById("toasts");
  const node = el(`<div class="toast toast-${kind}">${escapeHtml(message)}</div>`);
  toastHost.appendChild(node);
  setTimeout(() => node.remove(), 4000);
}

export function openModal(title, bodyHtml) {
  const overlay = el(`
    <div class="modal-overlay">
      <div class="modal">
        <div class="modal-header">
          <h2>${escapeHtml(title)}</h2>
          <button type="button" class="modal-close" aria-label="Close">&times;</button>
        </div>
        <div class="modal-body">${bodyHtml}</div>
      </div>
    </div>
  `);
  document.body.appendChild(overlay);

  const close = () => overlay.remove();
  overlay.querySelector(".modal-close").addEventListener("click", close);
  overlay.addEventListener("click", (e) => {
    if (e.target === overlay) close();
  });
  const onEsc = (e) => {
    if (e.key === "Escape") {
      close();
      document.removeEventListener("keydown", onEsc);
    }
  };
  document.addEventListener("keydown", onEsc);

  return { overlay, close };
}

/**
 * Builds a plain object from a form, skipping empty-string fields named in
 * `skipEmpty` (so PATCH payloads omit them entirely and the backend's
 * exclude_unset semantics leave those fields untouched).
 */
export function formToJson(form, { skipEmpty = [] } = {}) {
  const fd = new FormData(form);
  const obj = {};
  for (const [key, value] of fd.entries()) {
    if (value === "" && skipEmpty.includes(key)) continue;
    obj[key] = value;
  }
  return obj;
}
