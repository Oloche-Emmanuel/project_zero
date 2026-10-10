const TOKEN_KEY = "rentalapp_token";

export function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token) {
  if (token) localStorage.setItem(TOKEN_KEY, token);
  else localStorage.removeItem(TOKEN_KEY);
}

export class ApiError extends Error {
  constructor(status, message) {
    super(message);
    this.status = status;
  }
}

async function request(path, { method = "GET", body, form, auth = true } = {}) {
  const headers = {};
  let payload;
  if (form) {
    headers["Content-Type"] = "application/x-www-form-urlencoded";
    payload = new URLSearchParams(form).toString();
  } else if (body !== undefined) {
    headers["Content-Type"] = "application/json";
    payload = JSON.stringify(body);
  }
  if (auth) {
    const token = getToken();
    if (token) headers["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(path, { method, headers, body: payload });

  if (res.status === 204) return null;

  const text = await res.text();
  let data = null;
  if (text) {
    try {
      data = JSON.parse(text);
    } catch {
      data = text;
    }
  }

  if (!res.ok) {
    let message = res.statusText || `Request failed (${res.status})`;
    if (data && typeof data === "object" && "detail" in data) {
      message = Array.isArray(data.detail)
        ? data.detail.map((d) => d.msg || JSON.stringify(d)).join("; ")
        : String(data.detail);
    } else if (typeof data === "string" && data) {
      message = data;
    }
    throw new ApiError(res.status, message);
  }

  return data;
}

export const api = {
  // Auth / users
  // Sends the token when present so a signed-in admin can create admin accounts.
  register: (data) => request("/api/v1/auth/register", { method: "POST", body: data }),
  login: (email, password) =>
    request("/api/v1/auth/login", { method: "POST", form: { username: email, password }, auth: false }),
  me: () => request("/api/v1/users/me"),
  listUsers: () => request("/api/v1/users"),
  getUser: (id) => request(`/api/v1/users/${id}`),
  updateUser: (id, data) => request(`/api/v1/users/${id}`, { method: "PATCH", body: data }),

  // Properties & units
  listProperties: () => request("/api/v1/properties"),
  createProperty: (data) => request("/api/v1/properties", { method: "POST", body: data }),
  getProperty: (id) => request(`/api/v1/properties/${id}`),
  updateProperty: (id, data) => request(`/api/v1/properties/${id}`, { method: "PATCH", body: data }),
  deleteProperty: (id) => request(`/api/v1/properties/${id}`, { method: "DELETE" }),
  listUnits: (propertyId) => request(`/api/v1/properties/${propertyId}/units`),
  addUnit: (propertyId, data) => request(`/api/v1/properties/${propertyId}/units`, { method: "POST", body: data }),
  getUnit: (unitId) => request(`/api/v1/properties/units/${unitId}`),
  updateUnit: (unitId, data) => request(`/api/v1/properties/units/${unitId}`, { method: "PATCH", body: data }),

  // Tenants
  listTenants: () => request("/api/v1/tenants"),
  createTenant: (data) => request("/api/v1/tenants", { method: "POST", body: data }),
  getTenant: (id) => request(`/api/v1/tenants/${id}`),
  updateTenant: (id, data) => request(`/api/v1/tenants/${id}`, { method: "PATCH", body: data }),
  deleteTenant: (id) => request(`/api/v1/tenants/${id}`, { method: "DELETE" }),

  // Leases
  createLease: (data) => request("/api/v1/leases", { method: "POST", body: data }),
  getLease: (id) => request(`/api/v1/leases/${id}`),
  leasesByUnit: (unitId) => request(`/api/v1/leases/by-unit/${unitId}`),
  leasesByTenant: (tenantId) => request(`/api/v1/leases/by-tenant/${tenantId}`),
  updateLease: (id, data) => request(`/api/v1/leases/${id}`, { method: "PATCH", body: data }),
  terminateLease: (id) => request(`/api/v1/leases/${id}/terminate`, { method: "POST" }),

  // Invoices / payments
  createInvoice: (data) => request("/api/v1/invoices", { method: "POST", body: data }),
  getInvoice: (id) => request(`/api/v1/invoices/${id}`),
  invoicesByLease: (leaseId) => request(`/api/v1/invoices/by-lease/${leaseId}`),
  recordPayment: (invoiceId, data) => request(`/api/v1/invoices/${invoiceId}/payments`, { method: "POST", body: data }),
  refreshOverdue: () => request("/api/v1/invoices/refresh-overdue", { method: "POST" }),

  // Maintenance
  createMaintenance: (data) => request("/api/v1/maintenance-requests", { method: "POST", body: data }),
  listOpenMaintenance: () => request("/api/v1/maintenance-requests/open"),
  getMaintenance: (id) => request(`/api/v1/maintenance-requests/${id}`),
  maintenanceByUnit: (unitId) => request(`/api/v1/maintenance-requests/by-unit/${unitId}`),
  updateMaintenance: (id, data) => request(`/api/v1/maintenance-requests/${id}`, { method: "PATCH", body: data }),
};
