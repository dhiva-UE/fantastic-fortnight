
import { useEffect, useMemo, useState } from "react";
import {
  createComponent,
  createAssignment,
  createNote,
  createPurchase,
  createSale,
  createSupplier,
  createUser,
  deleteComponent,
  deleteNote,
  deletePurchase,
  deleteSale,
  deleteSupplier,
  deleteUser,
  fetchComponents,
  fetchDashboard,
  fetchAssignments,
  fetchNotes,
  fetchPurchases,
  fetchSales,
  fetchSuppliers,
  fetchUsers,
  fetchReports,
  login,
  uploadProductImage,
  uploadPurchaseInvoice,
  updateNote,
  updateComponent,
  updatePurchase,
  updateSale,
  updateSupplier,
  updateUser
} from "./api";
import inboundOfficialLogo from "./assets/inbound-official-logo.png";

function AnimatedLogo({ compact = false }) {
  return (
    <div className={`brand-lockup ${compact ? "compact" : ""}`} role="img" aria-label="Inbound animated logo">
      <div className="brand-logo-stage" aria-hidden="true">
        <div className="brand-logo-text">
          <img src={inboundOfficialLogo} alt="" />
        </div>
        <div className="brand-logo-swoosh">
          <img src={inboundOfficialLogo} alt="" />
        </div>
      </div>
    </div>
  );
}

function MetricCard({ label, value }) {
  return (
    <div className="metric-card">
      <span className="metric-label">{label}</span>
      <strong className="metric-value">{value}</strong>
    </div>
  );
}

function getCellDisplayValue(value) {
  if (value === null || value === undefined || value === "") {
    return "-";
  }

  return String(value);
}

function escapeCsvValue(value) {
  const normalized = String(value ?? "").replace(/"/g, "\"\"");
  return `"${normalized}"`;
}

function DataCard({ title, columns, rows }) {
  const [filterColumn, setFilterColumn] = useState("all");
  const [filterValue, setFilterValue] = useState("");

  const filteredRows = useMemo(() => {
    const normalizedFilter = filterValue.trim().toLowerCase();

    if (!normalizedFilter) {
      return rows;
    }

    return rows.filter((row) => {
      const valuesToSearch = filterColumn === "all"
        ? columns.map((column) => row[column.key])
        : [row[filterColumn]];

      return valuesToSearch.some((value) => getCellDisplayValue(value).toLowerCase().includes(normalizedFilter));
    });
  }, [columns, filterColumn, filterValue, rows]);

  const downloadCsv = () => {
    if (filteredRows.length === 0) {
      return;
    }

    const headerRow = columns.map((column) => escapeCsvValue(column.label)).join(",");
    const dataRows = filteredRows.map((row) => (
      columns.map((column) => escapeCsvValue(getCellDisplayValue(row[column.key]))).join(",")
    ));
    const csvContent = [headerRow, ...dataRows].join("\n");
    const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    const fileName = `${title.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "") || "report"}.csv`;

    link.href = url;
    link.download = fileName;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  return (
    <section className="panel">
      <div className="panel-header split-header">
        <div>
          <h3>{title}</h3>
          <p className="panel-copy">Filter visible rows and export the current report as CSV.</p>
        </div>
        <button className="ghost-button slim report-download-button" type="button" onClick={downloadCsv} disabled={filteredRows.length === 0}>
          Download CSV
        </button>
      </div>
      <div className="report-toolbar">
        <div className="report-filter-row">
          <label className="report-filter-field">
            Filter By
            <select value={filterColumn} onChange={(event) => setFilterColumn(event.target.value)}>
              <option value="all">All Columns</option>
              {columns.map((column) => (
                <option key={column.key} value={column.key}>{column.label}</option>
              ))}
            </select>
          </label>
          <label className="report-filter-field report-filter-search">
            Search
            <input
              type="text"
              value={filterValue}
              onChange={(event) => setFilterValue(event.target.value)}
              placeholder="Type to filter rows"
            />
          </label>
        </div>
        <p className="report-filter-meta">
          Showing {filteredRows.length} of {rows.length} rows
        </p>
      </div>
      <div className="table-shell">
        <table>
          <thead>
            <tr>
              {columns.map((column) => (
                <th key={column.key}>{column.label}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {filteredRows.length === 0 ? (
              <tr>
                <td colSpan={columns.length} className="empty-state-cell">
                  {rows.length === 0 ? "No records available" : "No matching records found"}
                </td>
              </tr>
            ) : (
              filteredRows.map((row, index) => (
                <tr key={index}>
                  {columns.map((column) => (
                    <td key={column.key}>{getCellDisplayValue(row[column.key])}</td>
                  ))}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function LoginView({ onLogin, loading, error }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");

  const submit = async (event) => {
    event.preventDefault();
    await onLogin(username, password);
  };

  return (
    <main className="auth-page">
      <section className="auth-card">
        <AnimatedLogo />
        <h1>Inventory Control Center</h1>
        <p className="auth-copy">
          Sign in to access the new React migration preview for the inbound inventory platform.
        </p>
        <form className="auth-form" onSubmit={submit}>
          <label>
            Username
            <input value={username} onChange={(event) => setUsername(event.target.value)} />
          </label>
          <label>
            Password
            <input
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
            />
          </label>
          {error ? <div className="error-banner">{error}</div> : null}
          <button type="submit" disabled={loading}>
            {loading ? "Signing In..." : "Sign In"}
          </button>
        </form>
      </section>
    </main>
  );
}

function DashboardView({ dashboard }) {
  const metrics = dashboard?.metrics;

  return (
    <>
      <header className="hero">
        <div>
          <AnimatedLogo compact />
          <p className="eyebrow">Inbound Inventory Platform</p>
          <h1>Operational Dashboard</h1>
          <p>
            Aerospace-inspired control surface for inventory, purchasing, and internal coordination.
          </p>
        </div>
      </header>

      <section className="metrics-grid">
        <MetricCard label="Components" value={metrics?.total_components ?? 0} />
        <MetricCard label="Suppliers" value={metrics?.total_suppliers ?? 0} />
        <MetricCard label="Stock Qty" value={metrics?.total_stock_qty ?? 0} />
        <MetricCard label="Employees" value={metrics?.total_employees ?? 0} />
        <MetricCard label="Inventory Value" value={formatCurrency(metrics?.inventory_value)} />
        <MetricCard label="Purchase Value" value={formatCurrency(metrics?.total_purchase_value)} />
        <MetricCard label="Sales Revenue" value={formatCurrency(metrics?.total_sales_value)} />
      </section>

      <section className="panel-grid">
        <DataCard
          title="Current Stock"
          rows={dashboard?.stock ?? []}
          columns={[
            { key: "product_no", label: "Component No" },
            { key: "product_name", label: "Component Name" },
            { key: "quantity", label: "Stock" },
            { key: "supplier_name", label: "Supplier" }
          ]}
        />
        <DataCard
          title="Low Stock"
          rows={dashboard?.low_stock ?? []}
          columns={[
            { key: "product_no", label: "Component No" },
            { key: "product_name", label: "Component Name" },
            { key: "quantity", label: "Qty" },
            { key: "reorder_level", label: "Reorder" }
          ]}
        />
        <DataCard
          title="Recent Purchases"
          rows={dashboard?.recent_purchases ?? []}
          columns={[
            { key: "product_name", label: "Component" },
            { key: "supplier_name", label: "Supplier" },
            { key: "quantity_purchased", label: "Qty" },
            { key: "purchase_date", label: "Date" }
          ]}
        />
        <DataCard
          title="Recent Sales"
          rows={dashboard?.recent_sales ?? []}
          columns={[
            { key: "product_name", label: "Component" },
            { key: "customer_name", label: "Customer" },
            { key: "quantity_sold", label: "Qty" },
            { key: "sale_date", label: "Date" }
          ]}
        />
      </section>
    </>
  );
}

function ComponentForm({ suppliers, employees, selectedComponent, onSubmit, saving, onCancel }) {
  const [formState, setFormState] = useState(() => buildInitialComponentFormState(suppliers, selectedComponent));
  const [selectedImageFile, setSelectedImageFile] = useState(null);
  const [localPreviewUrl, setLocalPreviewUrl] = useState("");

  useEffect(() => {
    setFormState(buildInitialComponentFormState(suppliers, selectedComponent));
    setSelectedImageFile(null);
    setLocalPreviewUrl("");
  }, [suppliers, selectedComponent]);

  useEffect(() => {
    if (!selectedImageFile) {
      setLocalPreviewUrl("");
      return undefined;
    }

    const objectUrl = URL.createObjectURL(selectedImageFile);
    setLocalPreviewUrl(objectUrl);
    return () => URL.revokeObjectURL(objectUrl);
  }, [selectedImageFile]);

  const handleChange = (field, value) => {
    setFormState((current) => ({ ...current, [field]: value }));
  };

  const submit = async (event) => {
    event.preventDefault();
    let imagePath = selectedComponent?.image_path ?? "";
    if (selectedImageFile) {
      const uploadResult = await uploadProductImage(selectedImageFile);
      imagePath = uploadResult.stored_path;
    }

    await onSubmit({
      product_name: formState.product_name,
      category: formState.category,
      price: Number(formState.price),
      reorder_level: Number(formState.reorder_level),
      supplier_id: Number(formState.supplier_id),
      assigned_to: formState.assigned_to,
      image_path: imagePath
    });
  };

  return (
    <section className="panel component-form-panel">
      <div className="panel-header split-header">
        <div>
          <h3>{selectedComponent ? "Edit Component" : "Add Component"}</h3>
          <p className="panel-copy">Manage core component details in the new React module.</p>
        </div>
        {selectedComponent ? (
          <button className="ghost-button slim" type="button" onClick={onCancel}>Cancel</button>
        ) : null}
      </div>
      <form className="form-grid" onSubmit={submit}>
        <label>
          Component Name
          <input
            value={formState.product_name}
            onChange={(event) => handleChange("product_name", event.target.value)}
            required
          />
        </label>
        <label>
          Category
          <input
            value={formState.category}
            onChange={(event) => handleChange("category", event.target.value)}
          />
        </label>
        <label>
          Price
          <input
            type="number"
            min="0"
            step="0.01"
            value={formState.price}
            onChange={(event) => handleChange("price", event.target.value)}
            required
          />
        </label>
        <label>
          Reorder Level
          <input
            type="number"
            min="1"
            step="1"
            value={formState.reorder_level}
            onChange={(event) => handleChange("reorder_level", event.target.value)}
            required
          />
        </label>
        <label>
          Supplier
          <select value={formState.supplier_id} onChange={(event) => handleChange("supplier_id", event.target.value)}>
            {suppliers.map((supplier) => (
              <option key={supplier.supplier_id} value={supplier.supplier_id}>{supplier.supplier_name}</option>
            ))}
          </select>
        </label>
        <label>
          Assigned To
          <select value={formState.assigned_to} onChange={(event) => handleChange("assigned_to", event.target.value)}>
            <option value="">Not Assigned</option>
            {employees.map((employee) => (
              <option key={employee.user_id} value={employee.full_name}>{employee.full_name} ({employee.role})</option>
            ))}
          </select>
        </label>
        <label className="full-span">
          Product Image
          <input type="file" accept="image/png,image/jpeg,image/jpg" onChange={(event) => setSelectedImageFile(event.target.files?.[0] ?? null)} />
        </label>
        {localPreviewUrl || selectedComponent?.image_url ? (
          <div className="full-span media-preview-shell">
            <img
              className="media-preview-image"
              src={localPreviewUrl || selectedComponent?.image_url}
              alt="Component preview"
            />
          </div>
        ) : null}
        <div className="full-span form-actions">
          <button className="form-submit-button" type="submit" disabled={saving}>
            {saving ? "Saving..." : selectedComponent ? "Update Component" : "Create Component"}
          </button>
        </div>
      </form>
    </section>
  );
}

function ComponentsView({ componentsPayload, onRefresh }) {
  const [selectedComponentId, setSelectedComponentId] = useState(null);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  const suppliers = componentsPayload?.suppliers ?? [];
  const employees = componentsPayload?.employees ?? [];
  const items = componentsPayload?.items ?? [];

  const selectedComponent = useMemo(
    () => items.find((item) => Number(item.product_id) === Number(selectedComponentId)) || null,
    [items, selectedComponentId]
  );

  const submitComponent = async (payload) => {
    setSaving(true);
    setError("");
    try {
      if (selectedComponent) {
        await updateComponent(selectedComponent.product_id, payload);
      } else {
        await createComponent(payload);
      }
      setSelectedComponentId(null);
      await onRefresh();
    } catch (submitError) {
      setError(submitError.message);
    } finally {
      setSaving(false);
    }
  };

  const removeComponent = async (productId) => {
    const confirmed = window.confirm("Deactivate this component?");
    if (!confirmed) return;
    setError("");
    try {
      await deleteComponent(productId);
      if (Number(selectedComponentId) === Number(productId)) {
        setSelectedComponentId(null);
      }
      await onRefresh();
    } catch (deleteError) {
      setError(deleteError.message);
    }
  };

  return (
    <>
      <header className="hero compact-hero">
        <div>
          <p className="eyebrow">Component Operations</p>
          <h1>Components Module</h1>
          <p>
            Create, review, update, and remove components while keeping supplier and employee assignment context visible.
          </p>
        </div>
      </header>

      {error ? <div className="error-banner inline-banner">{error}</div> : null}

      <ComponentForm
        suppliers={suppliers}
        employees={employees}
        selectedComponent={selectedComponent}
        onSubmit={submitComponent}
        saving={saving}
        onCancel={() => setSelectedComponentId(null)}
      />

      <section className="panel">
        <div className="panel-header split-header">
          <div>
            <h3>Component Inventory</h3>
            <p className="panel-copy">Current component records from PostgreSQL via FastAPI.</p>
          </div>
        </div>
        <div className="table-shell">
          <table>
            <thead>
              <tr>
                <th>Component No</th>
                <th>Name</th>
                <th>Category</th>
                <th>Supplier</th>
                <th>Assigned To</th>
                <th>Price</th>
                <th>Stock</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {items.length === 0 ? (
                <tr>
                  <td colSpan="8" className="empty-state-cell">No components available</td>
                </tr>
              ) : items.map((item) => (
                <tr key={item.product_id}>
                  <td>{item.product_no}</td>
                  <td>{item.product_name}</td>
                  <td>{item.category || "-"}</td>
                  <td>{item.supplier_name || "-"}</td>
                  <td>{item.assigned_to || "-"}</td>
                  <td>{formatCurrency(item.price)}</td>
                  <td>{item.quantity}</td>
                  <td>
                    <div className="row-actions">
                      <button className="ghost-button slim" type="button" onClick={() => setSelectedComponentId(item.product_id)}>Edit</button>
                      <button className="danger-button slim" type="button" onClick={() => removeComponent(item.product_id)}>Deactivate</button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </>
  );
}

function PurchaseForm({ products, suppliers, selectedPurchase, onSubmit, saving, onCancel }) {
  const [formState, setFormState] = useState(() => buildInitialPurchaseFormState(products, suppliers, selectedPurchase));
  const [selectedInvoiceFile, setSelectedInvoiceFile] = useState(null);
  const [localInvoicePreviewUrl, setLocalInvoicePreviewUrl] = useState("");

  useEffect(() => {
    setFormState(buildInitialPurchaseFormState(products, suppliers, selectedPurchase));
    setSelectedInvoiceFile(null);
    setLocalInvoicePreviewUrl("");
  }, [products, suppliers, selectedPurchase]);

  useEffect(() => {
    if (!selectedInvoiceFile || !selectedInvoiceFile.type.startsWith("image/")) {
      setLocalInvoicePreviewUrl("");
      return undefined;
    }

    const objectUrl = URL.createObjectURL(selectedInvoiceFile);
    setLocalInvoicePreviewUrl(objectUrl);
    return () => URL.revokeObjectURL(objectUrl);
  }, [selectedInvoiceFile]);

  const selectedProduct = products.find((product) => Number(product.product_id) === Number(formState.product_id));
  const unitPrice = Number(selectedProduct?.price || 0);
  const totalPrice = unitPrice * Number(formState.quantity || 0);

  const handleChange = (field, value) => {
    setFormState((current) => ({ ...current, [field]: value }));
  };

  const submit = async (event) => {
    event.preventDefault();
    let invoicePath = selectedPurchase?.invoice_path ?? "";
    if (selectedInvoiceFile) {
      const uploadResult = await uploadPurchaseInvoice(selectedInvoiceFile);
      invoicePath = uploadResult.stored_path;
    }

    await onSubmit({
      product_id: Number(formState.product_id),
      supplier_id: Number(formState.supplier_id),
      quantity: Number(formState.quantity),
      purchase_date: formState.purchase_date,
      invoice_path: invoicePath
    });
  };

  return (
    <section className="panel component-form-panel">
      <div className="panel-header split-header">
        <div>
          <h3>{selectedPurchase ? "Edit Purchase" : "Add Purchase"}</h3>
          <p className="panel-copy">Record inbound purchases and keep stock values in sync.</p>
        </div>
        {selectedPurchase ? <button className="ghost-button slim" type="button" onClick={onCancel}>Cancel</button> : null}
      </div>
      <form className="form-grid" onSubmit={submit}>
        <label>
          Component
          <select value={formState.product_id} onChange={(event) => handleChange("product_id", event.target.value)} disabled={Boolean(selectedPurchase)}>
            {products.map((product) => (
              <option key={product.product_id} value={product.product_id}>
                {product.product_no} - {product.product_name}
              </option>
            ))}
          </select>
        </label>
        <label>
          Supplier
          <select value={formState.supplier_id} onChange={(event) => handleChange("supplier_id", event.target.value)}>
            {suppliers.map((supplier) => (
              <option key={supplier.supplier_id} value={supplier.supplier_id}>{supplier.supplier_name}</option>
            ))}
          </select>
        </label>
        <label>
          Quantity
          <input type="number" min="1" step="1" value={formState.quantity} onChange={(event) => handleChange("quantity", event.target.value)} required />
        </label>
        <label>
          Purchase Date
          <input type="date" value={formState.purchase_date} onChange={(event) => handleChange("purchase_date", event.target.value)} required />
        </label>
        <label>
          Unit Price
          <input value={formatCurrency(unitPrice)} disabled />
        </label>
        <label>
          Total Price
          <input value={formatCurrency(totalPrice)} disabled />
        </label>
        <label className="full-span">
          Purchase Invoice
          <input type="file" accept="application/pdf,image/png,image/jpeg,image/jpg" onChange={(event) => setSelectedInvoiceFile(event.target.files?.[0] ?? null)} />
        </label>
        {selectedInvoiceFile && !selectedInvoiceFile.type.startsWith("image/") ? (
          <div className="full-span file-chip">{selectedInvoiceFile.name}</div>
        ) : null}
        {localInvoicePreviewUrl || (selectedPurchase?.invoice_url && selectedPurchase?.invoice_url.match(/\.(png|jpe?g)$/i)) ? (
          <div className="full-span media-preview-shell">
            <img
              className="media-preview-image"
              src={localInvoicePreviewUrl || selectedPurchase?.invoice_url}
              alt="Invoice preview"
            />
          </div>
        ) : null}
        {!localInvoicePreviewUrl && selectedPurchase?.invoice_url && selectedPurchase?.invoice_url.match(/\.pdf$/i) ? (
          <div className="full-span file-chip">
            <a href={selectedPurchase.invoice_url} target="_blank" rel="noreferrer">Open current invoice PDF</a>
          </div>
        ) : null}
        <div className="full-span form-actions">
          <button className="form-submit-button" type="submit" disabled={saving}>{saving ? "Saving..." : selectedPurchase ? "Update Purchase" : "Create Purchase"}</button>
        </div>
      </form>
    </section>
  );
}

function PurchasesView({ purchasesPayload, onRefresh }) {
  const [selectedPurchaseId, setSelectedPurchaseId] = useState(null);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  const items = purchasesPayload?.items ?? [];
  const products = purchasesPayload?.products ?? [];
  const suppliers = purchasesPayload?.suppliers ?? [];

  const selectedPurchase = useMemo(
    () => items.find((item) => Number(item.purchase_id) === Number(selectedPurchaseId)) || null,
    [items, selectedPurchaseId]
  );

  const submitPurchase = async (payload) => {
    setSaving(true);
    setError("");
    try {
      if (selectedPurchase) {
        await updatePurchase(selectedPurchase.purchase_id, payload);
      } else {
        await createPurchase(payload);
      }
      setSelectedPurchaseId(null);
      await onRefresh();
    } catch (submitError) {
      setError(submitError.message);
    } finally {
      setSaving(false);
    }
  };

  const removePurchaseRecord = async (purchaseId) => {
    const confirmed = window.confirm("Delete this purchase record?");
    if (!confirmed) return;
    setError("");
    try {
      await deletePurchase(purchaseId);
      if (Number(selectedPurchaseId) === Number(purchaseId)) {
        setSelectedPurchaseId(null);
      }
      await onRefresh();
    } catch (deleteError) {
      setError(deleteError.message);
    }
  };

  return (
    <>
      <header className="hero compact-hero">
        <div>
          <p className="eyebrow">Purchase Operations</p>
          <h1>Purchases Module</h1>
          <p>
            Record inbound purchase activity, update supplier details, and keep component stock levels accurate.
          </p>
        </div>
      </header>

      {error ? <div className="error-banner inline-banner">{error}</div> : null}

      <PurchaseForm
        products={products}
        suppliers={suppliers}
        selectedPurchase={selectedPurchase}
        onSubmit={submitPurchase}
        saving={saving}
        onCancel={() => setSelectedPurchaseId(null)}
      />

      <section className="panel">
        <div className="panel-header split-header">
          <div>
            <h3>Purchase History</h3>
            <p className="panel-copy">Inbound purchase records with supplier and invoice context.</p>
          </div>
        </div>
        <div className="table-shell">
          <table>
            <thead>
              <tr>
                <th>ID</th>
                <th>Component</th>
                <th>Supplier</th>
                <th>Qty</th>
                <th>Unit Price</th>
                <th>Total</th>
                <th>Date</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {items.length === 0 ? (
                <tr>
                  <td colSpan="8" className="empty-state-cell">No purchases available</td>
                </tr>
              ) : items.map((item) => (
                <tr key={item.purchase_id}>
                  <td>{item.purchase_id}</td>
                  <td>{item.product_no} - {item.product_name}</td>
                  <td>{item.supplier_name}</td>
                  <td>{item.quantity_purchased}</td>
                  <td>{formatCurrency(item.unit_price)}</td>
                  <td>{formatCurrency(item.total_purchase_price)}</td>
                  <td>{item.purchase_date}</td>
                  <td>
                    <div className="row-actions">
                      <button className="ghost-button slim" type="button" onClick={() => setSelectedPurchaseId(item.purchase_id)}>Edit</button>
                      <button className="danger-button slim" type="button" onClick={() => removePurchaseRecord(item.purchase_id)}>Delete</button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </>
  );
}

function SaleForm({ products, selectedSale, onSubmit, saving, onCancel }) {
  const [formState, setFormState] = useState(() => buildInitialSaleFormState(products, selectedSale));

  useEffect(() => {
    setFormState(buildInitialSaleFormState(products, selectedSale));
  }, [products, selectedSale]);

  const selectedProduct = products.find((product) => Number(product.product_id) === Number(formState.product_id));
  const sellingPrice = Number(selectedProduct?.price || 0);
  const totalValue = sellingPrice * Number(formState.quantity_sold || 0);

  const handleChange = (field, value) => {
    setFormState((current) => ({ ...current, [field]: value }));
  };

  const submit = async (event) => {
    event.preventDefault();
    await onSubmit({
      product_id: Number(formState.product_id),
      quantity_sold: Number(formState.quantity_sold),
      sale_date: formState.sale_date,
      customer_name: formState.customer_name
    });
  };

  return (
    <section className="panel component-form-panel">
      <div className="panel-header split-header">
        <div>
          <h3>{selectedSale ? "Edit Sale" : "Add Sale"}</h3>
          <p className="panel-copy">Record outbound sales and protect component stock from overselling.</p>
        </div>
        {selectedSale ? <button className="ghost-button slim" type="button" onClick={onCancel}>Cancel</button> : null}
      </div>
      <form className="form-grid" onSubmit={submit}>
        <label>
          Component
          <select value={formState.product_id} onChange={(event) => handleChange("product_id", event.target.value)} disabled={Boolean(selectedSale)}>
            {products.map((product) => (
              <option key={product.product_id} value={product.product_id}>
                {product.product_no} - {product.product_name}
              </option>
            ))}
          </select>
        </label>
        <label>
          Quantity Sold
          <input
            type="number"
            min="1"
            step="1"
            value={formState.quantity_sold}
            onChange={(event) => handleChange("quantity_sold", event.target.value)}
            required
          />
        </label>
        <label>
          Sale Date
          <input type="date" value={formState.sale_date} onChange={(event) => handleChange("sale_date", event.target.value)} required />
        </label>
        <label>
          Customer Name
          <input value={formState.customer_name} onChange={(event) => handleChange("customer_name", event.target.value)} />
        </label>
        <label>
          Selling Price
          <input value={formatCurrency(sellingPrice)} disabled />
        </label>
        <label>
          Total Value
          <input value={formatCurrency(totalValue)} disabled />
        </label>
        <div className="full-span form-actions">
          <button className="form-submit-button" type="submit" disabled={saving}>{saving ? "Saving..." : selectedSale ? "Update Sale" : "Create Sale"}</button>
        </div>
      </form>
    </section>
  );
}

function SalesView({ salesPayload, onRefresh }) {
  const [selectedSaleId, setSelectedSaleId] = useState(null);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  const items = salesPayload?.items ?? [];
  const products = salesPayload?.products ?? [];

  const selectedSale = useMemo(
    () => items.find((item) => Number(item.sale_id) === Number(selectedSaleId)) || null,
    [items, selectedSaleId]
  );

  const submitSale = async (payload) => {
    setSaving(true);
    setError("");
    try {
      if (selectedSale) {
        await updateSale(selectedSale.sale_id, payload);
      } else {
        await createSale(payload);
      }
      setSelectedSaleId(null);
      await onRefresh();
    } catch (submitError) {
      setError(submitError.message);
    } finally {
      setSaving(false);
    }
  };

  const removeSaleRecord = async (saleId) => {
    const confirmed = window.confirm("Delete this sale record?");
    if (!confirmed) return;
    setError("");
    try {
      await deleteSale(saleId);
      if (Number(selectedSaleId) === Number(saleId)) {
        setSelectedSaleId(null);
      }
      await onRefresh();
    } catch (deleteError) {
      setError(deleteError.message);
    }
  };

  return (
    <>
      <header className="hero compact-hero">
        <div>
          <p className="eyebrow">Sales Operations</p>
          <h1>Sales Module</h1>
          <p>
            Track outbound component sales, customer context, and live stock impact from the React migration preview.
          </p>
        </div>
      </header>

      {error ? <div className="error-banner inline-banner">{error}</div> : null}

      <SaleForm
        products={products}
        selectedSale={selectedSale}
        onSubmit={submitSale}
        saving={saving}
        onCancel={() => setSelectedSaleId(null)}
      />

      <section className="panel">
        <div className="panel-header split-header">
          <div>
            <h3>Sales History</h3>
            <p className="panel-copy">Outbound sales records with customer details and revenue values.</p>
          </div>
        </div>
        <div className="table-shell">
          <table>
            <thead>
              <tr>
                <th>ID</th>
                <th>Component</th>
                <th>Qty</th>
                <th>Selling Price</th>
                <th>Total Value</th>
                <th>Date</th>
                <th>Customer</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {items.length === 0 ? (
                <tr>
                  <td colSpan="8" className="empty-state-cell">No sales available</td>
                </tr>
              ) : items.map((item) => (
                <tr key={item.sale_id}>
                  <td>{item.sale_id}</td>
                  <td>{item.product_no} - {item.product_name}</td>
                  <td>{item.quantity_sold}</td>
                  <td>{formatCurrency(item.selling_price)}</td>
                  <td>{formatCurrency(item.total_sales_value)}</td>
                  <td>{item.sale_date}</td>
                  <td>{item.customer_name || "-"}</td>
                  <td>
                    <div className="row-actions">
                      <button className="ghost-button slim" type="button" onClick={() => setSelectedSaleId(item.sale_id)}>Edit</button>
                      <button className="danger-button slim" type="button" onClick={() => removeSaleRecord(item.sale_id)}>Delete</button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </>
  );
}

function NoteForm({ employees, selectedNote, currentUser, onSubmit, saving, onCancel }) {
  const [formState, setFormState] = useState(() => buildInitialNoteFormState(selectedNote));

  useEffect(() => {
    setFormState(buildInitialNoteFormState(selectedNote));
  }, [selectedNote]);

  const handleChange = (field, value) => {
    setFormState((current) => ({ ...current, [field]: value }));
  };

  const submit = async (event) => {
    event.preventDefault();
    await onSubmit({
      note_title: formState.note_title,
      note_content: formState.note_content,
      note_status: formState.note_status,
      assigned_to: formState.assigned_to,
      created_by: currentUser?.full_name || "",
      created_date: new Date().toISOString().slice(0, 10)
    });
  };

  return (
    <section className="panel component-form-panel">
      <div className="panel-header split-header">
        <div>
          <h3>{selectedNote ? "Edit Note" : "Add Note"}</h3>
          <p className="panel-copy">Capture internal work notes and assign them to employees for follow-up.</p>
        </div>
        {selectedNote ? <button className="ghost-button slim" type="button" onClick={onCancel}>Cancel</button> : null}
      </div>
      <form className="form-grid" onSubmit={submit}>
        <label>
          Note Title
          <input value={formState.note_title} onChange={(event) => handleChange("note_title", event.target.value)} required />
        </label>
        <label>
          Status
          <select value={formState.note_status} onChange={(event) => handleChange("note_status", event.target.value)}>
            <option value="Open">Open</option>
            <option value="In Progress">In Progress</option>
            <option value="Completed">Completed</option>
          </select>
        </label>
        <label className="full-span">
          Assigned To
          <select value={formState.assigned_to} onChange={(event) => handleChange("assigned_to", event.target.value)}>
            <option value="">Not Assigned</option>
            {employees.map((employee) => (
              <option key={employee.user_id} value={employee.full_name}>
                {employee.full_name} ({employee.role})
              </option>
            ))}
          </select>
        </label>
        <label className="full-span">
          Note Content
          <textarea
            className="notes-textarea"
            value={formState.note_content}
            onChange={(event) => handleChange("note_content", event.target.value)}
            required
          />
        </label>
        <div className="full-span form-actions">
          <button className="form-submit-button" type="submit" disabled={saving}>{saving ? "Saving..." : selectedNote ? "Update Note" : "Create Note"}</button>
        </div>
      </form>
    </section>
  );
}

function NotesView({ notesPayload, currentUser, onRefresh }) {
  const [selectedNoteId, setSelectedNoteId] = useState(null);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  const items = notesPayload?.items ?? [];
  const employees = notesPayload?.employees ?? [];

  const selectedNote = useMemo(
    () => items.find((item) => Number(item.note_id) === Number(selectedNoteId)) || null,
    [items, selectedNoteId]
  );

  const submitNote = async (payload) => {
    setSaving(true);
    setError("");
    try {
      if (selectedNote) {
        await updateNote(selectedNote.note_id, {
          note_title: payload.note_title,
          note_content: payload.note_content,
          note_status: payload.note_status,
          assigned_to: payload.assigned_to
        });
      } else {
        await createNote(payload);
      }
      setSelectedNoteId(null);
      await onRefresh();
    } catch (submitError) {
      setError(submitError.message);
    } finally {
      setSaving(false);
    }
  };

  const removeNoteRecord = async (noteId) => {
    const confirmed = window.confirm("Delete this note?");
    if (!confirmed) return;
    setError("");
    try {
      await deleteNote(noteId);
      if (Number(selectedNoteId) === Number(noteId)) {
        setSelectedNoteId(null);
      }
      await onRefresh();
    } catch (deleteError) {
      setError(deleteError.message);
    }
  };

  return (
    <>
      <header className="hero compact-hero">
        <div>
          <p className="eyebrow">Notes Workspace</p>
          <h1>Notes Module</h1>
          <p>
            Track work notes, assign owners, and keep internal follow-ups visible inside the React migration.
          </p>
        </div>
      </header>

      {error ? <div className="error-banner inline-banner">{error}</div> : null}

      <NoteForm
        employees={employees}
        selectedNote={selectedNote}
        currentUser={currentUser}
        onSubmit={submitNote}
        saving={saving}
        onCancel={() => setSelectedNoteId(null)}
      />

      <section className="panel">
        <div className="panel-header split-header">
          <div>
            <h3>Notes List</h3>
            <p className="panel-copy">Internal notes with owner, status, and creation details.</p>
          </div>
        </div>
        <div className="table-shell">
          <table>
            <thead>
              <tr>
                <th>ID</th>
                <th>Title</th>
                <th>Status</th>
                <th>Assigned To</th>
                <th>Created By</th>
                <th>Date</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {items.length === 0 ? (
                <tr>
                  <td colSpan="7" className="empty-state-cell">No notes available</td>
                </tr>
              ) : items.map((item) => (
                <tr key={item.note_id}>
                  <td>{item.note_id}</td>
                  <td>{item.note_title}</td>
                  <td>{item.note_status}</td>
                  <td>{item.assigned_to || "-"}</td>
                  <td>{item.created_by || "-"}</td>
                  <td>{item.created_date || "-"}</td>
                  <td>
                    <div className="row-actions">
                      <button className="ghost-button slim" type="button" onClick={() => setSelectedNoteId(item.note_id)}>Edit</button>
                      <button className="danger-button slim" type="button" onClick={() => removeNoteRecord(item.note_id)}>Delete</button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </>
  );
}

function SupplierForm({ selectedSupplier, onSubmit, saving, onCancel }) {
  const [formState, setFormState] = useState(() => buildInitialSupplierFormState(selectedSupplier));

  useEffect(() => {
    setFormState(buildInitialSupplierFormState(selectedSupplier));
  }, [selectedSupplier]);

  const handleChange = (field, value) => {
    setFormState((current) => ({ ...current, [field]: value }));
  };

  const submit = async (event) => {
    event.preventDefault();
    await onSubmit(formState);
  };

  return (
    <section className="panel component-form-panel">
      <div className="panel-header split-header">
        <div>
          <h3>{selectedSupplier ? "Edit Supplier" : "Add Supplier"}</h3>
          <p className="panel-copy">Manage supplier details used across components and purchases.</p>
        </div>
        {selectedSupplier ? <button className="ghost-button slim" type="button" onClick={onCancel}>Cancel</button> : null}
      </div>
      <form className="form-grid" onSubmit={submit}>
        <label>
          Supplier Name
          <input value={formState.supplier_name} onChange={(event) => handleChange("supplier_name", event.target.value)} required />
        </label>
        <label>
          Contact Number
          <input value={formState.contact_number} onChange={(event) => handleChange("contact_number", event.target.value)} />
        </label>
        <label>
          Email
          <input value={formState.email} onChange={(event) => handleChange("email", event.target.value)} />
        </label>
        <label className="full-span">
          Address
          <textarea className="notes-textarea" value={formState.address} onChange={(event) => handleChange("address", event.target.value)} />
        </label>
        <div className="full-span form-actions">
          <button className="form-submit-button" type="submit" disabled={saving}>
            {saving ? "Saving..." : selectedSupplier ? "Update Supplier" : "Create Supplier"}
          </button>
        </div>
      </form>
    </section>
  );
}

function SuppliersView({ suppliersPayload, onRefresh }) {
  const [selectedSupplierId, setSelectedSupplierId] = useState(null);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  const items = suppliersPayload?.items ?? [];
  const selectedSupplier = useMemo(
    () => items.find((item) => Number(item.supplier_id) === Number(selectedSupplierId)) || null,
    [items, selectedSupplierId]
  );

  const submitSupplier = async (payload) => {
    setSaving(true);
    setError("");
    try {
      if (selectedSupplier) {
        await updateSupplier(selectedSupplier.supplier_id, payload);
      } else {
        await createSupplier(payload);
      }
      setSelectedSupplierId(null);
      await onRefresh();
    } catch (submitError) {
      setError(submitError.message);
    } finally {
      setSaving(false);
    }
  };

  const removeSupplierRecord = async (supplierId) => {
    const confirmed = window.confirm("Delete this supplier?");
    if (!confirmed) return;
    setError("");
    try {
      await deleteSupplier(supplierId);
      if (Number(selectedSupplierId) === Number(supplierId)) {
        setSelectedSupplierId(null);
      }
      await onRefresh();
    } catch (deleteError) {
      setError(deleteError.message);
    }
  };

  return (
    <>
      <header className="hero compact-hero">
        <div>
          <p className="eyebrow">Supplier Management</p>
          <h1>Suppliers Module</h1>
          <p>Maintain the supplier records used by purchasing and component tracking.</p>
        </div>
      </header>
      {error ? <div className="error-banner inline-banner">{error}</div> : null}
      <SupplierForm
        selectedSupplier={selectedSupplier}
        onSubmit={submitSupplier}
        saving={saving}
        onCancel={() => setSelectedSupplierId(null)}
      />
      <section className="panel">
        <div className="panel-header split-header">
          <div>
            <h3>Supplier List</h3>
            <p className="panel-copy">Available suppliers from the shared PostgreSQL database.</p>
          </div>
        </div>
        <div className="table-shell">
          <table>
            <thead>
              <tr>
                <th>ID</th>
                <th>Name</th>
                <th>Contact</th>
                <th>Email</th>
                <th>Address</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {items.length === 0 ? (
                <tr><td colSpan="6" className="empty-state-cell">No suppliers available</td></tr>
              ) : items.map((item) => (
                <tr key={item.supplier_id}>
                  <td>{item.supplier_id}</td>
                  <td>{item.supplier_name}</td>
                  <td>{item.contact_number || "-"}</td>
                  <td>{item.email || "-"}</td>
                  <td>{item.address || "-"}</td>
                  <td>
                    <div className="row-actions">
                      <button className="ghost-button slim" type="button" onClick={() => setSelectedSupplierId(item.supplier_id)}>Edit</button>
                      <button className="danger-button slim" type="button" onClick={() => removeSupplierRecord(item.supplier_id)}>Delete</button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </>
  );
}

function PermissionSelect({ label, value, onChange }) {
  return (
    <label>
      {label}
      <select value={value} onChange={(event) => onChange(Number(event.target.value))}>
        <option value={0}>0 - No</option>
        <option value={1}>1 - Yes</option>
      </select>
    </label>
  );
}

function UserForm({ selectedUser, onSubmit, saving, onCancel }) {
  const [formState, setFormState] = useState(() => buildInitialUserFormState(selectedUser));

  useEffect(() => {
    setFormState(buildInitialUserFormState(selectedUser));
  }, [selectedUser]);

  const handleChange = (field, value) => {
    setFormState((current) => ({ ...current, [field]: value }));
  };

  const submit = async (event) => {
    event.preventDefault();
    await onSubmit(formState);
  };

  return (
    <section className="panel component-form-panel">
      <div className="panel-header split-header">
        <div>
          <h3>{selectedUser ? "Edit User" : "Add User"}</h3>
          <p className="panel-copy">Manage internal users, roles, contact details, and permissions.</p>
        </div>
        {selectedUser ? <button className="ghost-button slim" type="button" onClick={onCancel}>Cancel</button> : null}
      </div>
      <form className="form-grid" onSubmit={submit}>
        <label>
          Full Name
          <input value={formState.full_name} onChange={(event) => handleChange("full_name", event.target.value)} required />
        </label>
        <label>
          Username
          <input value={formState.username} onChange={(event) => handleChange("username", event.target.value)} required />
        </label>
        <label>
          Password
          <input type="password" value={formState.password} onChange={(event) => handleChange("password", event.target.value)} placeholder={selectedUser ? "Leave blank to keep current password" : ""} required={!selectedUser} />
        </label>
        <label>
          Role
          <select value={formState.role} onChange={(event) => handleChange("role", event.target.value)}>
            <option value="Admin">Admin</option>
            <option value="Employee">Employee</option>
            <option value="CEO">CEO</option>
            <option value="CBO">CBO</option>
            <option value="CGO">CGO</option>
          </select>
        </label>
        <label>
          Department
          <input value={formState.department} onChange={(event) => handleChange("department", event.target.value)} />
        </label>
        <label>
          Date Of Joining
          <input type="date" value={formState.date_of_joining} onChange={(event) => handleChange("date_of_joining", event.target.value)} />
        </label>
        <label>
          Office Email
          <input value={formState.office_email} onChange={(event) => handleChange("office_email", event.target.value)} />
        </label>
        <label>
          Company Email
          <input value={formState.company_email} onChange={(event) => handleChange("company_email", event.target.value)} />
        </label>
        <label className="full-span">
          Contact Number
          <input value={formState.contact_number} onChange={(event) => handleChange("contact_number", event.target.value)} />
        </label>
        <PermissionSelect label="Can Edit Suppliers" value={formState.can_edit_suppliers} onChange={(value) => handleChange("can_edit_suppliers", value)} />
        <PermissionSelect label="Can Delete Suppliers" value={formState.can_delete_suppliers} onChange={(value) => handleChange("can_delete_suppliers", value)} />
        <PermissionSelect label="Can Edit Components" value={formState.can_edit_products} onChange={(value) => handleChange("can_edit_products", value)} />
        <PermissionSelect label="Can Delete Components" value={formState.can_delete_products} onChange={(value) => handleChange("can_delete_products", value)} />
        <PermissionSelect label="Can Edit Purchases" value={formState.can_edit_purchases} onChange={(value) => handleChange("can_edit_purchases", value)} />
        <PermissionSelect label="Can Delete Purchases" value={formState.can_delete_purchases} onChange={(value) => handleChange("can_delete_purchases", value)} />
        <div className="full-span form-actions">
          <button className="form-submit-button" type="submit" disabled={saving}>{saving ? "Saving..." : selectedUser ? "Update User" : "Create User"}</button>
        </div>
      </form>
    </section>
  );
}

function UsersView({ usersPayload, currentUser, onRefresh }) {
  const [selectedUserId, setSelectedUserId] = useState(null);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  const items = usersPayload?.items ?? [];
  const selectedUser = useMemo(
    () => items.find((item) => Number(item.user_id) === Number(selectedUserId)) || null,
    [items, selectedUserId]
  );

  const submitUser = async (payload) => {
    setSaving(true);
    setError("");
    try {
      if (selectedUser) {
        await updateUser(selectedUser.user_id, payload);
      } else {
        await createUser(payload);
      }
      setSelectedUserId(null);
      await onRefresh();
    } catch (submitError) {
      setError(submitError.message);
    } finally {
      setSaving(false);
    }
  };

  const removeUserRecord = async (userId, username) => {
    if (Number(userId) === Number(currentUser?.user_id)) {
      setError("You cannot delete the currently logged-in user.");
      return;
    }
    if (username === "admin") {
      setError("Default admin cannot be deleted.");
      return;
    }
    const confirmed = window.confirm("Delete this user?");
    if (!confirmed) return;
    setError("");
    try {
      await deleteUser(userId);
      if (Number(selectedUserId) === Number(userId)) {
        setSelectedUserId(null);
      }
      await onRefresh();
    } catch (deleteError) {
      setError(deleteError.message);
    }
  };

  return (
    <>
      <header className="hero compact-hero">
        <div>
          <p className="eyebrow">User Administration</p>
          <h1>Users Module</h1>
          <p>Manage people, roles, contact details, and app permissions from the React admin layer.</p>
        </div>
      </header>
      {error ? <div className="error-banner inline-banner">{error}</div> : null}
      <UserForm selectedUser={selectedUser} onSubmit={submitUser} saving={saving} onCancel={() => setSelectedUserId(null)} />
      <section className="panel">
        <div className="panel-header split-header">
          <div>
            <h3>User List</h3>
            <p className="panel-copy">Shared user accounts and permission flags from PostgreSQL.</p>
          </div>
        </div>
        <div className="table-shell">
          <table>
            <thead>
              <tr>
                <th>ID</th>
                <th>Name</th>
                <th>Username</th>
                <th>Role</th>
                <th>Department</th>
                <th>Office Email</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {items.length === 0 ? (
                <tr><td colSpan="7" className="empty-state-cell">No users available</td></tr>
              ) : items.map((item) => (
                <tr key={item.user_id}>
                  <td>{item.user_id}</td>
                  <td>{item.full_name}</td>
                  <td>{item.username}</td>
                  <td>{item.role}</td>
                  <td>{item.department || "-"}</td>
                  <td>{item.office_email || "-"}</td>
                  <td>
                    <div className="row-actions">
                      <button className="ghost-button slim" type="button" onClick={() => setSelectedUserId(item.user_id)}>Edit</button>
                      <button className="danger-button slim" type="button" onClick={() => removeUserRecord(item.user_id, item.username)}>Delete</button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </>
  );
}

function AssignmentsView({ assignmentsPayload, onRefresh }) {
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [formState, setFormState] = useState(() => buildInitialAssignmentFormState(assignmentsPayload?.products ?? [], assignmentsPayload?.employees ?? []));

  const items = assignmentsPayload?.items ?? [];
  const products = assignmentsPayload?.products ?? [];
  const employees = assignmentsPayload?.employees ?? [];

  useEffect(() => {
    setFormState(buildInitialAssignmentFormState(products, employees));
  }, [products, employees]);

  const handleChange = (field, value) => {
    setFormState((current) => ({ ...current, [field]: value }));
  };

  const submitAssignment = async (event) => {
    event.preventDefault();
    setSaving(true);
    setError("");
    try {
      await createAssignment({
        product_id: Number(formState.product_id),
        assigned_to: formState.assigned_to,
        assigned_date: formState.assigned_date,
        remarks: formState.remarks,
        status: formState.status
      });
      await onRefresh();
      setFormState(buildInitialAssignmentFormState(products, employees));
    } catch (submitError) {
      setError(submitError.message);
    } finally {
      setSaving(false);
    }
  };

  return (
    <>
      <header className="hero compact-hero">
        <div>
          <p className="eyebrow">Responsibility Tracking</p>
          <h1>Components Responsibility</h1>
          <p>Transfer ownership of components between employees and keep the full assignment history visible.</p>
        </div>
      </header>
      {error ? <div className="error-banner inline-banner">{error}</div> : null}
      <section className="panel component-form-panel">
        <div className="panel-header split-header">
          <div>
            <h3>Transfer Responsibility</h3>
            <p className="panel-copy">Create a new responsibility handoff entry and update the current owner.</p>
          </div>
        </div>
        <form className="form-grid" onSubmit={submitAssignment}>
          <label>
            Component
            <select value={formState.product_id} onChange={(event) => handleChange("product_id", event.target.value)}>
              {products.map((product) => (
                <option key={product.product_id} value={product.product_id}>
                  {product.product_no} - {product.product_name}
                </option>
              ))}
            </select>
          </label>
          <label>
            Transfer To
            <select value={formState.assigned_to} onChange={(event) => handleChange("assigned_to", event.target.value)}>
              {employees.map((employee) => (
                <option key={employee.user_id} value={employee.full_name}>
                  {employee.full_name} ({employee.role})
                </option>
              ))}
            </select>
          </label>
          <label>
            Assignment Date
            <input type="date" value={formState.assigned_date} onChange={(event) => handleChange("assigned_date", event.target.value)} required />
          </label>
          <label>
            Status
            <select value={formState.status} onChange={(event) => handleChange("status", event.target.value)}>
              <option value="In Progress">In Progress</option>
              <option value="Under Review">Under Review</option>
              <option value="Testing">Testing</option>
              <option value="Completed">Completed</option>
            </select>
          </label>
          <label className="full-span">
            Remarks
            <textarea className="notes-textarea" value={formState.remarks} onChange={(event) => handleChange("remarks", event.target.value)} />
          </label>
          <div className="full-span form-actions">
            <button className="form-submit-button" type="submit" disabled={saving}>{saving ? "Saving..." : "Update Responsibility"}</button>
          </div>
        </form>
      </section>
      <section className="panel">
        <div className="panel-header split-header">
          <div>
            <h3>Assignment History</h3>
            <p className="panel-copy">Historical transfers and status changes for component ownership.</p>
          </div>
        </div>
        <div className="table-shell">
          <table>
            <thead>
              <tr>
                <th>ID</th>
                <th>Component</th>
                <th>Assigned To</th>
                <th>Date</th>
                <th>Status</th>
                <th>Remarks</th>
              </tr>
            </thead>
            <tbody>
              {items.length === 0 ? (
                <tr><td colSpan="6" className="empty-state-cell">No assignment history available</td></tr>
              ) : items.map((item) => (
                <tr key={item.assignment_id}>
                  <td>{item.assignment_id}</td>
                  <td>{item.product_no} - {item.product_name}</td>
                  <td>{item.assigned_to}</td>
                  <td>{item.assigned_date}</td>
                  <td>{item.status}</td>
                  <td>{item.remarks || "-"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </>
  );
}

function ReportsView({ reportsPayload }) {
  const [selectedReport, setSelectedReport] = useState("products");

  const reportConfig = {
    products: {
      title: "Components Report",
      rows: reportsPayload?.products ?? [],
      columns: [
        { key: "product_no", label: "Component No" },
        { key: "product_name", label: "Name" },
        { key: "category", label: "Category" },
        { key: "quantity", label: "Stock" },
        { key: "supplier_name", label: "Supplier" }
      ]
    },
    suppliers: {
      title: "Suppliers Report",
      rows: reportsPayload?.suppliers ?? [],
      columns: [
        { key: "supplier_name", label: "Supplier" },
        { key: "contact_number", label: "Contact" },
        { key: "email", label: "Email" },
        { key: "address", label: "Address" }
      ]
    },
    purchases: {
      title: "Purchases Report",
      rows: reportsPayload?.purchases ?? [],
      columns: [
        { key: "product_name", label: "Component" },
        { key: "supplier_name", label: "Supplier" },
        { key: "quantity_purchased", label: "Qty" },
        { key: "total_purchase_price", label: "Total" },
        { key: "purchase_date", label: "Date" }
      ]
    },
    sales: {
      title: "Sales Report",
      rows: reportsPayload?.sales ?? [],
      columns: [
        { key: "product_name", label: "Component" },
        { key: "quantity_sold", label: "Qty" },
        { key: "selling_price", label: "Price" },
        { key: "total_sales_value", label: "Total" },
        { key: "sale_date", label: "Date" }
      ]
    },
    low_stock: {
      title: "Low Stock Report",
      rows: reportsPayload?.low_stock ?? [],
      columns: [
        { key: "product_no", label: "Component No" },
        { key: "product_name", label: "Name" },
        { key: "quantity", label: "Qty" },
        { key: "reorder_level", label: "Reorder" }
      ]
    },
    assignments: {
      title: "Assignment History Report",
      rows: reportsPayload?.assignments ?? [],
      columns: [
        { key: "product_name", label: "Component" },
        { key: "assigned_to", label: "Assigned To" },
        { key: "assigned_date", label: "Date" },
        { key: "status", label: "Status" }
      ]
    },
    users: {
      title: "Users Report",
      rows: reportsPayload?.users ?? [],
      columns: [
        { key: "full_name", label: "Name" },
        { key: "username", label: "Username" },
        { key: "role", label: "Role" },
        { key: "department", label: "Department" }
      ]
    },
    notes: {
      title: "Notes Report",
      rows: reportsPayload?.notes ?? [],
      columns: [
        { key: "note_title", label: "Title" },
        { key: "note_status", label: "Status" },
        { key: "assigned_to", label: "Assigned To" },
        { key: "created_date", label: "Date" }
      ]
    }
  };

  const activeReport = reportConfig[selectedReport];

  return (
    <>
      <header className="hero compact-hero">
        <div>
          <p className="eyebrow">Reporting Center</p>
          <h1>Reports Module</h1>
          <p>Review operational data across inventory, purchasing, sales, people, and assignments from one place.</p>
        </div>
      </header>
      <section className="panel">
        <div className="panel-header split-header">
          <div>
            <h3>Select Report</h3>
            <p className="panel-copy">Switch datasets to inspect the current shared-state records loaded from PostgreSQL.</p>
          </div>
        </div>
        <div className="report-tabs">
          {Object.entries(reportConfig).map(([key, config]) => (
            <button
              key={key}
              type="button"
              className={`nav-item ${selectedReport === key ? "active" : ""}`}
              onClick={() => setSelectedReport(key)}
            >
              {config.title}
            </button>
          ))}
        </div>
      </section>
      <DataCard title={activeReport.title} columns={activeReport.columns} rows={activeReport.rows} />
    </>
  );
}

function buildInitialComponentFormState(suppliers, selectedComponent) {
  const defaultSupplier = suppliers[0]?.supplier_id ?? "";
  return {
    product_name: selectedComponent?.product_name ?? "",
    category: selectedComponent?.category ?? "",
    price: selectedComponent?.price ?? 0,
    reorder_level: selectedComponent?.reorder_level ?? 5,
    supplier_id: selectedComponent?.supplier_id ?? defaultSupplier,
    assigned_to: selectedComponent?.assigned_to ?? "",
    image_path: selectedComponent?.image_path ?? ""
  };
}

function buildInitialPurchaseFormState(products, suppliers, selectedPurchase) {
  const defaultProduct = products[0]?.product_id ?? "";
  const defaultSupplier = suppliers[0]?.supplier_id ?? "";
  return {
    product_id: selectedPurchase?.product_id ?? defaultProduct,
    supplier_id: selectedPurchase?.supplier_id ?? defaultSupplier,
    quantity: selectedPurchase?.quantity_purchased ?? 1,
    purchase_date: selectedPurchase?.purchase_date ?? new Date().toISOString().slice(0, 10),
    invoice_path: selectedPurchase?.invoice_path ?? ""
  };
}

function buildInitialSaleFormState(products, selectedSale) {
  const defaultProduct = products[0]?.product_id ?? "";
  return {
    product_id: selectedSale?.product_id ?? defaultProduct,
    quantity_sold: selectedSale?.quantity_sold ?? 1,
    sale_date: selectedSale?.sale_date ?? new Date().toISOString().slice(0, 10),
    customer_name: selectedSale?.customer_name ?? ""
  };
}

function buildInitialNoteFormState(selectedNote) {
  return {
    note_title: selectedNote?.note_title ?? "",
    note_content: selectedNote?.note_content ?? "",
    note_status: selectedNote?.note_status ?? "Open",
    assigned_to: selectedNote?.assigned_to ?? ""
  };
}

function buildInitialSupplierFormState(selectedSupplier) {
  return {
    supplier_name: selectedSupplier?.supplier_name ?? "",
    contact_number: selectedSupplier?.contact_number ?? "",
    email: selectedSupplier?.email ?? "",
    address: selectedSupplier?.address ?? ""
  };
}

function buildInitialUserFormState(selectedUser) {
  return {
    full_name: selectedUser?.full_name ?? "",
    username: selectedUser?.username ?? "",
    password: "",
    role: selectedUser?.role ?? "Employee",
    department: selectedUser?.department ?? "",
    date_of_joining: selectedUser?.date_of_joining ?? "",
    office_email: selectedUser?.office_email ?? "",
    company_email: selectedUser?.company_email ?? "",
    contact_number: selectedUser?.contact_number ?? "",
    can_edit_suppliers: Number(selectedUser?.can_edit_suppliers ?? 0),
    can_delete_suppliers: Number(selectedUser?.can_delete_suppliers ?? 0),
    can_edit_products: Number(selectedUser?.can_edit_products ?? 0),
    can_delete_products: Number(selectedUser?.can_delete_products ?? 0),
    can_edit_purchases: Number(selectedUser?.can_edit_purchases ?? 0),
    can_delete_purchases: Number(selectedUser?.can_delete_purchases ?? 0)
  };
}

function buildInitialAssignmentFormState(products, employees) {
  return {
    product_id: products[0]?.product_id ?? "",
    assigned_to: employees[0]?.full_name ?? "",
    assigned_date: new Date().toISOString().slice(0, 10),
    remarks: "",
    status: "In Progress"
  };
}

function formatCurrency(value) {
  const amount = Number(value || 0);
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 2
  }).format(amount);
}

export default function App() {
  const [user, setUser] = useState(null);
  const [dashboard, setDashboard] = useState(null);
  const [suppliersPayload, setSuppliersPayload] = useState(null);
  const [componentsPayload, setComponentsPayload] = useState(null);
  const [assignmentsPayload, setAssignmentsPayload] = useState(null);
  const [purchasesPayload, setPurchasesPayload] = useState(null);
  const [salesPayload, setSalesPayload] = useState(null);
  const [notesPayload, setNotesPayload] = useState(null);
  const [reportsPayload, setReportsPayload] = useState(null);
  const [usersPayload, setUsersPayload] = useState(null);
  const [activeView, setActiveView] = useState("dashboard");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const loadDashboard = async () => {
    const payload = await fetchDashboard();
    setDashboard(payload);
  };

  const loadComponents = async () => {
    const payload = await fetchComponents();
    setComponentsPayload(payload);
  };

  const loadAssignments = async () => {
    const payload = await fetchAssignments();
    setAssignmentsPayload(payload);
  };

  const loadSuppliers = async () => {
    const payload = await fetchSuppliers();
    setSuppliersPayload(payload);
  };

  const loadPurchases = async () => {
    const payload = await fetchPurchases();
    setPurchasesPayload(payload);
  };

  const loadSales = async () => {
    const payload = await fetchSales();
    setSalesPayload(payload);
  };

  const loadNotes = async () => {
    const payload = await fetchNotes();
    setNotesPayload(payload);
  };

  const loadUsers = async () => {
    const payload = await fetchUsers();
    setUsersPayload(payload);
  };

  const loadReports = async () => {
    const payload = await fetchReports();
    setReportsPayload(payload);
  };

  const refreshOperationalData = async () => {
    await Promise.all([loadDashboard(), loadSuppliers(), loadComponents(), loadAssignments(), loadPurchases(), loadSales(), loadNotes(), loadUsers(), loadReports()]);
  };

  useEffect(() => {
    if (!user) return;
    let cancelled = false;

    async function loadData() {
      try {
        await refreshOperationalData();
      } catch (dataError) {
        if (!cancelled) {
          setError(dataError.message);
        }
      }
    }

    loadData();
    return () => {
      cancelled = true;
    };
  }, [user]);

  const handleLogin = async (username, password) => {
    setLoading(true);
    setError("");
    try {
      const payload = await login(username, password);
      setUser(payload);
    } catch (loginError) {
      setError(loginError.message);
    } finally {
      setLoading(false);
    }
  };

  if (!user) {
    return <LoginView onLogin={handleLogin} loading={loading} error={error} />;
  }

  return (
    <main className="app-shell">
      <aside className="sidebar">
        <div>
          <AnimatedLogo compact />
          <h2>Inventory OS</h2>
        </div>
        <nav className="nav-list">
          <button className={`nav-item ${activeView === "dashboard" ? "active" : ""}`} onClick={() => setActiveView("dashboard")}>Dashboard</button>
          <button className={`nav-item ${activeView === "suppliers" ? "active" : ""}`} onClick={() => setActiveView("suppliers")}>Suppliers</button>
          <button className={`nav-item ${activeView === "components" ? "active" : ""}`} onClick={() => setActiveView("components")}>Components</button>
          <button className={`nav-item ${activeView === "assignments" ? "active" : ""}`} onClick={() => setActiveView("assignments")}>Components Responsibility</button>
          <button className={`nav-item ${activeView === "purchases" ? "active" : ""}`} onClick={() => setActiveView("purchases")}>Purchases</button>
          <button className={`nav-item ${activeView === "sales" ? "active" : ""}`} onClick={() => setActiveView("sales")}>Sales</button>
          <button className={`nav-item ${activeView === "notes" ? "active" : ""}`} onClick={() => setActiveView("notes")}>Notes</button>
          <button className={`nav-item ${activeView === "users" ? "active" : ""}`} onClick={() => setActiveView("users")}>Users</button>
          <button className={`nav-item ${activeView === "reports" ? "active" : ""}`} onClick={() => setActiveView("reports")}>Reports</button>
        </nav>
        <div className="sidebar-user">
          <div>
            <strong>{user.full_name}</strong>
            <span>{user.role}</span>
          </div>
          <button className="ghost-button" onClick={() => {
            setUser(null);
            setDashboard(null);
            setSuppliersPayload(null);
            setComponentsPayload(null);
            setAssignmentsPayload(null);
            setPurchasesPayload(null);
            setSalesPayload(null);
            setNotesPayload(null);
            setReportsPayload(null);
            setUsersPayload(null);
            setError("");
            setActiveView("dashboard");
          }}>Logout</button>
        </div>
      </aside>

      <section className="content">
        {error ? <div className="error-banner inline-banner">{error}</div> : null}
        {activeView === "dashboard" ? <DashboardView dashboard={dashboard} /> : null}
        {activeView === "suppliers" ? <SuppliersView suppliersPayload={suppliersPayload} onRefresh={refreshOperationalData} /> : null}
        {activeView === "components" ? <ComponentsView componentsPayload={componentsPayload} onRefresh={refreshOperationalData} /> : null}
        {activeView === "assignments" ? <AssignmentsView assignmentsPayload={assignmentsPayload} onRefresh={refreshOperationalData} /> : null}
        {activeView === "purchases" ? <PurchasesView purchasesPayload={purchasesPayload} onRefresh={refreshOperationalData} /> : null}
        {activeView === "sales" ? <SalesView salesPayload={salesPayload} onRefresh={refreshOperationalData} /> : null}
        {activeView === "notes" ? <NotesView notesPayload={notesPayload} currentUser={user} onRefresh={refreshOperationalData} /> : null}
        {activeView === "users" ? <UsersView usersPayload={usersPayload} currentUser={user} onRefresh={refreshOperationalData} /> : null}
        {activeView === "reports" ? <ReportsView reportsPayload={reportsPayload} /> : null}
      </section>
    </main>
  );
}
