const JSON_HEADERS = {
  "Content-Type": "application/json"
};

const AUTH_STORAGE_KEY = "inventory_auth";

function getApiBaseUrl() {
  return (import.meta.env.VITE_API_BASE_URL || "").replace(/\/$/, "");
}

function buildApiUrl(path) {
  return `${getApiBaseUrl()}${path}`;
}

function readStoredAuthSession() {
  if (typeof window === "undefined") {
    return null;
  }

  try {
    const rawValue = window.localStorage.getItem(AUTH_STORAGE_KEY);
    if (!rawValue) {
      return null;
    }
    return JSON.parse(rawValue);
  } catch {
    return null;
  }
}

let authSession = readStoredAuthSession();

export function getStoredAuthSession() {
  return authSession;
}

export function saveAuthSession(session) {
  authSession = session;
  if (typeof window !== "undefined") {
    window.localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify(session));
  }
}

export function clearAuthSession() {
  authSession = null;
  if (typeof window !== "undefined") {
    window.localStorage.removeItem(AUTH_STORAGE_KEY);
  }
}

function withAuthorizationHeader(headers = {}) {
  if (!authSession?.access_token) {
    return headers;
  }

  return {
    ...headers,
    Authorization: `Bearer ${authSession.access_token}`
  };
}

function appendAccessToken(url) {
  if (!url || !authSession?.access_token || /^blob:/i.test(url)) {
    return url;
  }

  try {
    const resolvedUrl = new URL(url, window.location.origin);
    resolvedUrl.searchParams.set("access_token", authSession.access_token);

    if (!getApiBaseUrl() && resolvedUrl.origin === window.location.origin) {
      return `${resolvedUrl.pathname}${resolvedUrl.search}`;
    }

    return resolvedUrl.toString();
  } catch {
    return url;
  }
}

function enrichMediaUrls(value) {
  if (Array.isArray(value)) {
    return value.map(enrichMediaUrls);
  }

  if (!value || typeof value !== "object") {
    return value;
  }

  const nextValue = {};
  for (const [key, nestedValue] of Object.entries(value)) {
    if (key === "image_url" || key === "invoice_url" || key === "public_url") {
      nextValue[key] = appendAccessToken(nestedValue);
    } else {
      nextValue[key] = enrichMediaUrls(nestedValue);
    }
  }

  return nextValue;
}

async function parseApiError(response, fallbackMessage) {
  const payload = await response.json().catch(() => ({}));
  return payload.detail || fallbackMessage;
}

async function apiRequest(
  path,
  {
    method = "GET",
    body,
    isFormData = false,
    fallbackMessage = "Request failed",
    clearSessionOnUnauthorized = true
  } = {}
) {
  const requestHeaders = isFormData ? withAuthorizationHeader() : withAuthorizationHeader(JSON_HEADERS);
  let response;

  try {
    response = await fetch(buildApiUrl(path), {
      method,
      headers: requestHeaders,
      body: isFormData ? body : body ? JSON.stringify(body) : undefined
    });
  } catch {
    throw new Error("Cannot reach the API server. Make sure the backend is running and reachable.");
  }

  if (!response.ok) {
    if (response.status === 401 && clearSessionOnUnauthorized) {
      clearAuthSession();
      throw new Error("Your session expired. Please sign in again.");
    }

    throw new Error(await parseApiError(response, fallbackMessage));
  }

  if (response.status === 204) {
    return null;
  }

  const payload = await response.json();
  return enrichMediaUrls(payload);
}

export async function login(username, password) {
  const payload = await apiRequest("/api/auth/login", {
    method: "POST",
    body: { username, password },
    fallbackMessage: "Login failed",
    clearSessionOnUnauthorized: false
  });
  saveAuthSession(payload);
  return payload;
}

export function withAuthenticatedMediaUrl(url) {
  return appendAccessToken(url);
}

export async function fetchDashboard() {
  return apiRequest("/api/dashboard", { fallbackMessage: "Failed to load dashboard" });
}

export async function fetchComponents() {
  return apiRequest("/api/components", { fallbackMessage: "Failed to load components" });
}

export async function fetchSuppliers() {
  return apiRequest("/api/suppliers", { fallbackMessage: "Failed to load suppliers" });
}

export async function uploadProductImage(file) {
  const formData = new FormData();
  formData.append("file", file);
  return apiRequest("/api/uploads/product-image", {
    method: "POST",
    body: formData,
    isFormData: true,
    fallbackMessage: "Failed to upload product image"
  });
}

export async function uploadPurchaseInvoice(file) {
  const formData = new FormData();
  formData.append("file", file);
  return apiRequest("/api/uploads/purchase-invoice", {
    method: "POST",
    body: formData,
    isFormData: true,
    fallbackMessage: "Failed to upload purchase invoice"
  });
}

export async function createSupplier(payload) {
  return apiRequest("/api/suppliers", { method: "POST", body: payload, fallbackMessage: "Failed to create supplier" });
}

export async function updateSupplier(supplierId, payload) {
  return apiRequest(`/api/suppliers/${supplierId}`, { method: "PUT", body: payload, fallbackMessage: "Failed to update supplier" });
}

export async function deleteSupplier(supplierId) {
  return apiRequest(`/api/suppliers/${supplierId}`, { method: "DELETE", fallbackMessage: "Failed to delete supplier" });
}

export async function fetchAssignments() {
  return apiRequest("/api/assignments", { fallbackMessage: "Failed to load assignments" });
}

export async function createAssignment(payload) {
  return apiRequest("/api/assignments", { method: "POST", body: payload, fallbackMessage: "Failed to update responsibility" });
}

export async function createComponent(payload) {
  return apiRequest("/api/components", { method: "POST", body: payload, fallbackMessage: "Failed to create component" });
}

export async function updateComponent(productId, payload) {
  return apiRequest(`/api/components/${productId}`, { method: "PUT", body: payload, fallbackMessage: "Failed to update component" });
}

export async function deleteComponent(productId) {
  return apiRequest(`/api/components/${productId}`, { method: "DELETE", fallbackMessage: "Failed to delete component" });
}

export async function fetchPurchases() {
  return apiRequest("/api/purchases", { fallbackMessage: "Failed to load purchases" });
}

export async function createPurchase(payload) {
  return apiRequest("/api/purchases", { method: "POST", body: payload, fallbackMessage: "Failed to create purchase" });
}

export async function updatePurchase(purchaseId, payload) {
  return apiRequest(`/api/purchases/${purchaseId}`, { method: "PUT", body: payload, fallbackMessage: "Failed to update purchase" });
}

export async function deletePurchase(purchaseId) {
  return apiRequest(`/api/purchases/${purchaseId}`, { method: "DELETE", fallbackMessage: "Failed to delete purchase" });
}

export async function fetchSales() {
  return apiRequest("/api/sales", { fallbackMessage: "Failed to load sales" });
}

export async function createSale(payload) {
  return apiRequest("/api/sales", { method: "POST", body: payload, fallbackMessage: "Failed to create sale" });
}

export async function updateSale(saleId, payload) {
  return apiRequest(`/api/sales/${saleId}`, { method: "PUT", body: payload, fallbackMessage: "Failed to update sale" });
}

export async function deleteSale(saleId) {
  return apiRequest(`/api/sales/${saleId}`, { method: "DELETE", fallbackMessage: "Failed to delete sale" });
}

export async function fetchNotes() {
  return apiRequest("/api/notes", { fallbackMessage: "Failed to load notes" });
}

export async function fetchUsers() {
  return apiRequest("/api/users", { fallbackMessage: "Failed to load users" });
}

export async function createUser(payload) {
  return apiRequest("/api/users", { method: "POST", body: payload, fallbackMessage: "Failed to create user" });
}

export async function updateUser(userId, payload) {
  return apiRequest(`/api/users/${userId}`, { method: "PUT", body: payload, fallbackMessage: "Failed to update user" });
}

export async function deleteUser(userId) {
  return apiRequest(`/api/users/${userId}`, { method: "DELETE", fallbackMessage: "Failed to delete user" });
}

export async function fetchReports() {
  return apiRequest("/api/reports", { fallbackMessage: "Failed to load reports" });
}

export async function createNote(payload) {
  return apiRequest("/api/notes", { method: "POST", body: payload, fallbackMessage: "Failed to create note" });
}

export async function updateNote(noteId, payload) {
  return apiRequest(`/api/notes/${noteId}`, { method: "PUT", body: payload, fallbackMessage: "Failed to update note" });
}

export async function deleteNote(noteId) {
  return apiRequest(`/api/notes/${noteId}`, { method: "DELETE", fallbackMessage: "Failed to delete note" });
}
