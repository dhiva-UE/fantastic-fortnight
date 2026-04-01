const headers = {
  "Content-Type": "application/json"
};

async function parseApiError(response, fallbackMessage) {
  const payload = await response.json().catch(() => ({}));
  return payload.detail || fallbackMessage;
}

export async function login(username, password) {
  let response;
  try {
    response = await fetch("/api/auth/login", {
      method: "POST",
      headers,
      body: JSON.stringify({ username, password })
    });
  } catch {
    throw new Error("Cannot reach the API server. Make sure FastAPI is running on port 8000.");
  }

  if (!response.ok) {
    throw new Error(await parseApiError(response, "Login failed"));
  }

  return response.json();
}

export async function fetchDashboard() {
  let response;
  try {
    response = await fetch("/api/dashboard");
  } catch {
    throw new Error("Cannot reach the API server. Make sure FastAPI is running on port 8000.");
  }
  if (!response.ok) {
    throw new Error("Failed to load dashboard");
  }
  return response.json();
}

export async function fetchComponents() {
  let response;
  try {
    response = await fetch("/api/components");
  } catch {
    throw new Error("Cannot reach the API server. Make sure FastAPI is running on port 8000.");
  }
  if (!response.ok) {
    throw new Error("Failed to load components");
  }
  return response.json();
}

export async function fetchSuppliers() {
  let response;
  try {
    response = await fetch("/api/suppliers");
  } catch {
    throw new Error("Cannot reach the API server. Make sure FastAPI is running on port 8000.");
  }
  if (!response.ok) {
    throw new Error("Failed to load suppliers");
  }
  return response.json();
}

export async function uploadProductImage(file) {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch("/api/uploads/product-image", {
    method: "POST",
    body: formData
  });

  if (!response.ok) {
    throw new Error(await parseApiError(response, "Failed to upload product image"));
  }

  return response.json();
}

export async function uploadPurchaseInvoice(file) {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch("/api/uploads/purchase-invoice", {
    method: "POST",
    body: formData
  });

  if (!response.ok) {
    throw new Error(await parseApiError(response, "Failed to upload purchase invoice"));
  }

  return response.json();
}

export async function createSupplier(payload) {
  const response = await fetch("/api/suppliers", {
    method: "POST",
    headers,
    body: JSON.stringify(payload)
  });

  if (!response.ok) {
    throw new Error(await parseApiError(response, "Failed to create supplier"));
  }

  return response.json();
}

export async function updateSupplier(supplierId, payload) {
  const response = await fetch(`/api/suppliers/${supplierId}`, {
    method: "PUT",
    headers,
    body: JSON.stringify(payload)
  });

  if (!response.ok) {
    throw new Error(await parseApiError(response, "Failed to update supplier"));
  }

  return response.json();
}

export async function deleteSupplier(supplierId) {
  const response = await fetch(`/api/suppliers/${supplierId}`, {
    method: "DELETE"
  });

  if (!response.ok) {
    throw new Error(await parseApiError(response, "Failed to delete supplier"));
  }

  return response.json();
}

export async function fetchAssignments() {
  let response;
  try {
    response = await fetch("/api/assignments");
  } catch {
    throw new Error("Cannot reach the API server. Make sure FastAPI is running on port 8000.");
  }
  if (!response.ok) {
    throw new Error("Failed to load assignments");
  }
  return response.json();
}

export async function createAssignment(payload) {
  const response = await fetch("/api/assignments", {
    method: "POST",
    headers,
    body: JSON.stringify(payload)
  });

  if (!response.ok) {
    throw new Error(await parseApiError(response, "Failed to update responsibility"));
  }

  return response.json();
}

export async function createComponent(payload) {
  const response = await fetch("/api/components", {
    method: "POST",
    headers,
    body: JSON.stringify(payload)
  });

  if (!response.ok) {
    throw new Error(await parseApiError(response, "Failed to create component"));
  }

  return response.json();
}

export async function updateComponent(productId, payload) {
  const response = await fetch(`/api/components/${productId}`, {
    method: "PUT",
    headers,
    body: JSON.stringify(payload)
  });

  if (!response.ok) {
    throw new Error(await parseApiError(response, "Failed to update component"));
  }

  return response.json();
}

export async function deleteComponent(productId) {
  const response = await fetch(`/api/components/${productId}`, {
    method: "DELETE"
  });

  if (!response.ok) {
    throw new Error(await parseApiError(response, "Failed to delete component"));
  }

  return response.json();
}

export async function fetchPurchases() {
  let response;
  try {
    response = await fetch("/api/purchases");
  } catch {
    throw new Error("Cannot reach the API server. Make sure FastAPI is running on port 8000.");
  }
  if (!response.ok) {
    throw new Error("Failed to load purchases");
  }
  return response.json();
}

export async function createPurchase(payload) {
  const response = await fetch("/api/purchases", {
    method: "POST",
    headers,
    body: JSON.stringify(payload)
  });

  if (!response.ok) {
    throw new Error(await parseApiError(response, "Failed to create purchase"));
  }

  return response.json();
}

export async function updatePurchase(purchaseId, payload) {
  const response = await fetch(`/api/purchases/${purchaseId}`, {
    method: "PUT",
    headers,
    body: JSON.stringify(payload)
  });

  if (!response.ok) {
    throw new Error(await parseApiError(response, "Failed to update purchase"));
  }

  return response.json();
}

export async function deletePurchase(purchaseId) {
  const response = await fetch(`/api/purchases/${purchaseId}`, {
    method: "DELETE"
  });

  if (!response.ok) {
    throw new Error(await parseApiError(response, "Failed to delete purchase"));
  }

  return response.json();
}

export async function fetchSales() {
  let response;
  try {
    response = await fetch("/api/sales");
  } catch {
    throw new Error("Cannot reach the API server. Make sure FastAPI is running on port 8000.");
  }
  if (!response.ok) {
    throw new Error("Failed to load sales");
  }
  return response.json();
}

export async function createSale(payload) {
  const response = await fetch("/api/sales", {
    method: "POST",
    headers,
    body: JSON.stringify(payload)
  });

  if (!response.ok) {
    throw new Error(await parseApiError(response, "Failed to create sale"));
  }

  return response.json();
}

export async function updateSale(saleId, payload) {
  const response = await fetch(`/api/sales/${saleId}`, {
    method: "PUT",
    headers,
    body: JSON.stringify(payload)
  });

  if (!response.ok) {
    throw new Error(await parseApiError(response, "Failed to update sale"));
  }

  return response.json();
}

export async function deleteSale(saleId) {
  const response = await fetch(`/api/sales/${saleId}`, {
    method: "DELETE"
  });

  if (!response.ok) {
    throw new Error(await parseApiError(response, "Failed to delete sale"));
  }

  return response.json();
}

export async function fetchNotes() {
  let response;
  try {
    response = await fetch("/api/notes");
  } catch {
    throw new Error("Cannot reach the API server. Make sure FastAPI is running on port 8000.");
  }
  if (!response.ok) {
    throw new Error("Failed to load notes");
  }
  return response.json();
}

export async function fetchUsers() {
  let response;
  try {
    response = await fetch("/api/users");
  } catch {
    throw new Error("Cannot reach the API server. Make sure FastAPI is running on port 8000.");
  }
  if (!response.ok) {
    throw new Error("Failed to load users");
  }
  return response.json();
}

export async function createUser(payload) {
  const response = await fetch("/api/users", {
    method: "POST",
    headers,
    body: JSON.stringify(payload)
  });

  if (!response.ok) {
    throw new Error(await parseApiError(response, "Failed to create user"));
  }

  return response.json();
}

export async function updateUser(userId, payload) {
  const response = await fetch(`/api/users/${userId}`, {
    method: "PUT",
    headers,
    body: JSON.stringify(payload)
  });

  if (!response.ok) {
    throw new Error(await parseApiError(response, "Failed to update user"));
  }

  return response.json();
}

export async function deleteUser(userId) {
  const response = await fetch(`/api/users/${userId}`, {
    method: "DELETE"
  });

  if (!response.ok) {
    throw new Error(await parseApiError(response, "Failed to delete user"));
  }

  return response.json();
}

export async function fetchReports() {
  let response;
  try {
    response = await fetch("/api/reports");
  } catch {
    throw new Error("Cannot reach the API server. Make sure FastAPI is running on port 8000.");
  }
  if (!response.ok) {
    throw new Error("Failed to load reports");
  }
  return response.json();
}

export async function createNote(payload) {
  const response = await fetch("/api/notes", {
    method: "POST",
    headers,
    body: JSON.stringify(payload)
  });

  if (!response.ok) {
    throw new Error(await parseApiError(response, "Failed to create note"));
  }

  return response.json();
}

export async function updateNote(noteId, payload) {
  const response = await fetch(`/api/notes/${noteId}`, {
    method: "PUT",
    headers,
    body: JSON.stringify(payload)
  });

  if (!response.ok) {
    throw new Error(await parseApiError(response, "Failed to update note"));
  }

  return response.json();
}

export async function deleteNote(noteId) {
  const response = await fetch(`/api/notes/${noteId}`, {
    method: "DELETE"
  });

  if (!response.ok) {
    throw new Error(await parseApiError(response, "Failed to delete note"));
  }

  return response.json();
}
