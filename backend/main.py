import os
import re
import uuid
from pathlib import Path
import sys

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from database import (  # noqa: E402
    add_note,
    add_purchase,
    add_product,
    add_sale,
    add_supplier,
    add_user,
    create_tables,
    delete_note,
    delete_purchase,
    delete_product,
    delete_sale,
    delete_supplier,
    delete_user,
    generate_product_no,
    get_assignment_history,
    get_low_stock,
    get_notes,
    get_product_dropdown,
    get_products,
    get_purchases,
    get_sales,
    get_supplier_dropdown,
    get_suppliers,
    get_user_dropdown,
    get_users,
    login_user,
    update_product_assignment,
    update_note,
    update_purchase,
    update_product,
    update_sale,
    update_supplier,
    update_user,
)
try:
    from backend.schemas import (  # noqa: E402
        AssignmentCreateRequest,
        AssignmentListResponse,
        ComponentCreateRequest,
        ComponentListResponse,
        ComponentUpdateRequest,
        DashboardMetrics,
        DashboardResponse,
        EmployeeOption,
        LoginRequest,
        NoteCreateRequest,
        NoteListResponse,
        NoteUpdateRequest,
        ProductOption,
        PurchaseCreateRequest,
        PurchaseListResponse,
        PurchaseUpdateRequest,
        ReportsResponse,
        SaleCreateRequest,
        SaleListResponse,
        SaleUpdateRequest,
        SupplierCreateRequest,
        SupplierListResponse,
        SupplierOption,
        SupplierUpdateRequest,
        UserCreateRequest,
        UserListResponse,
        UserSummary,
        UserUpdateRequest,
    )
except ModuleNotFoundError:
    from schemas import (  # noqa: E402
        AssignmentCreateRequest,
        AssignmentListResponse,
        ComponentCreateRequest,
        ComponentListResponse,
        ComponentUpdateRequest,
        DashboardMetrics,
        DashboardResponse,
        EmployeeOption,
        LoginRequest,
        NoteCreateRequest,
        NoteListResponse,
        NoteUpdateRequest,
        ProductOption,
        PurchaseCreateRequest,
        PurchaseListResponse,
        PurchaseUpdateRequest,
        ReportsResponse,
        SaleCreateRequest,
        SaleListResponse,
        SaleUpdateRequest,
        SupplierCreateRequest,
        SupplierListResponse,
        SupplierOption,
        SupplierUpdateRequest,
        UserCreateRequest,
        UserListResponse,
        UserSummary,
        UserUpdateRequest,
    )

app = FastAPI(
    title="Inbound Inventory API",
    version="0.1.0",
    description="Parallel FastAPI backend for the React migration.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

create_tables()


def get_storage_dir(env_var_name: str, default_folder_name: str) -> Path:
    configured_path = os.getenv(env_var_name, "").strip()
    path = Path(configured_path) if configured_path else ROOT_DIR / default_folder_name

    if path.exists() and not path.is_dir():
        fallback_path = ROOT_DIR / "storage" / default_folder_name
        fallback_path.mkdir(parents=True, exist_ok=True)
        return fallback_path

    path.mkdir(parents=True, exist_ok=True)
    return path


PRODUCT_IMAGES_DIR = get_storage_dir("PRODUCT_IMAGES_DIR", "product_images")
PURCHASE_INVOICES_DIR = get_storage_dir("PURCHASE_INVOICES_DIR", "purchase_invoices")

app.mount("/media/product-images", StaticFiles(directory=str(PRODUCT_IMAGES_DIR)), name="product-images")
app.mount("/media/purchase-invoices", StaticFiles(directory=str(PURCHASE_INVOICES_DIR)), name="purchase-invoices")


def sanitize_filename(filename: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]", "_", filename)
    return cleaned or "file"


def save_upload_file(upload_file: UploadFile, target_dir: Path) -> tuple[str, str]:
    original_name = sanitize_filename(upload_file.filename or "file")
    suffix = Path(original_name).suffix
    stem = Path(original_name).stem
    stored_name = f"{stem}_{uuid.uuid4().hex[:8]}{suffix}"
    file_path = target_dir / stored_name

    with file_path.open("wb") as output_file:
        output_file.write(upload_file.file.read())

    return str(file_path), stored_name


def build_public_file_url(file_path: str | None) -> str | None:
    if not file_path:
        return None

    resolved = Path(file_path)
    try:
        product_relative = resolved.relative_to(PRODUCT_IMAGES_DIR)
        return f"/media/product-images/{product_relative.as_posix()}"
    except ValueError:
        pass

    try:
        invoice_relative = resolved.relative_to(PURCHASE_INVOICES_DIR)
        return f"/media/purchase-invoices/{invoice_relative.as_posix()}"
    except ValueError:
        pass

    return None


def build_dashboard_response() -> DashboardResponse:
    products_df = get_products()
    suppliers_df = get_suppliers()
    purchases_df = get_purchases()
    sales_df = get_sales()
    users_df = get_users()
    low_stock_df = get_low_stock()

    metrics = DashboardMetrics(
        total_components=len(products_df),
        total_suppliers=len(suppliers_df),
        total_stock_qty=int(products_df["quantity"].sum()) if not products_df.empty else 0,
        total_employees=len(users_df),
        inventory_value=float((products_df["quantity"] * products_df["price"]).sum()) if not products_df.empty else 0.0,
        total_purchase_value=float(purchases_df["total_purchase_price"].sum()) if not purchases_df.empty else 0.0,
        total_sales_value=float(sales_df["total_sales_value"].sum()) if not sales_df.empty else 0.0,
    )

    return DashboardResponse(
        metrics=metrics,
        stock=products_df.head(10).fillna("").to_dict(orient="records"),
        low_stock=low_stock_df.head(10).fillna("").to_dict(orient="records"),
        recent_purchases=purchases_df.head(5).fillna("").to_dict(orient="records"),
        recent_sales=sales_df.head(5).fillna("").to_dict(orient="records"),
    )


def build_component_response() -> ComponentListResponse:
    products_df = get_products().fillna("")
    suppliers_df = get_supplier_dropdown().fillna("")
    employees_df = get_user_dropdown().fillna("")

    if not products_df.empty:
        products_df["image_url"] = products_df["image_path"].apply(build_public_file_url)

    suppliers = [
        SupplierOption(
            supplier_id=int(row["supplier_id"]),
            supplier_name=str(row["supplier_name"]),
        )
        for _, row in suppliers_df.iterrows()
    ]

    employees = [
        EmployeeOption(
            user_id=int(row["user_id"]),
            full_name=str(row["full_name"]),
            username=str(row["username"]),
            role=str(row["role"]),
        )
        for _, row in employees_df.iterrows()
    ]

    return ComponentListResponse(
        items=products_df.to_dict(orient="records"),
        suppliers=suppliers,
        employees=employees,
    )


def build_purchase_response() -> PurchaseListResponse:
    purchases_df = get_purchases().fillna("")
    products_df = get_product_dropdown().fillna("")
    suppliers_df = get_supplier_dropdown().fillna("")

    if not purchases_df.empty:
        purchases_df["invoice_url"] = purchases_df["invoice_path"].apply(build_public_file_url)

    products = [
        ProductOption(
            product_id=int(row["product_id"]),
            product_no=str(row["product_no"]),
            product_name=str(row["product_name"]),
            price=float(row["price"] or 0),
            assigned_to=str(row["assigned_to"] or ""),
        )
        for _, row in products_df.iterrows()
    ]

    suppliers = [
        SupplierOption(
            supplier_id=int(row["supplier_id"]),
            supplier_name=str(row["supplier_name"]),
        )
        for _, row in suppliers_df.iterrows()
    ]

    return PurchaseListResponse(
        items=purchases_df.to_dict(orient="records"),
        products=products,
        suppliers=suppliers,
    )


def build_sale_response() -> SaleListResponse:
    sales_df = get_sales().fillna("")
    products_df = get_product_dropdown().fillna("")

    products = [
        ProductOption(
            product_id=int(row["product_id"]),
            product_no=str(row["product_no"]),
            product_name=str(row["product_name"]),
            price=float(row["price"] or 0),
            assigned_to=str(row["assigned_to"] or ""),
        )
        for _, row in products_df.iterrows()
    ]

    return SaleListResponse(
        items=sales_df.to_dict(orient="records"),
        products=products,
    )


def build_note_response() -> NoteListResponse:
    notes_df = get_notes().fillna("")
    employees_df = get_user_dropdown().fillna("")

    employees = [
        EmployeeOption(
            user_id=int(row["user_id"]),
            full_name=str(row["full_name"]),
            username=str(row["username"]),
            role=str(row["role"]),
        )
        for _, row in employees_df.iterrows()
    ]

    return NoteListResponse(
        items=notes_df.to_dict(orient="records"),
        employees=employees,
    )


def build_supplier_response() -> SupplierListResponse:
    suppliers_df = get_suppliers().fillna("")
    return SupplierListResponse(items=suppliers_df.to_dict(orient="records"))


def build_user_response() -> UserListResponse:
    users_df = get_users().fillna("")
    return UserListResponse(items=users_df.to_dict(orient="records"))


def build_assignment_response() -> AssignmentListResponse:
    assignments_df = get_assignment_history().fillna("")
    products_df = get_product_dropdown().fillna("")
    employees_df = get_user_dropdown().fillna("")

    products = [
        ProductOption(
            product_id=int(row["product_id"]),
            product_no=str(row["product_no"]),
            product_name=str(row["product_name"]),
            price=float(row["price"] or 0),
            assigned_to=str(row["assigned_to"] or ""),
        )
        for _, row in products_df.iterrows()
    ]

    employees = [
        EmployeeOption(
            user_id=int(row["user_id"]),
            full_name=str(row["full_name"]),
            username=str(row["username"]),
            role=str(row["role"]),
        )
        for _, row in employees_df.iterrows()
    ]

    return AssignmentListResponse(
        items=assignments_df.to_dict(orient="records"),
        products=products,
        employees=employees,
    )


def build_reports_response() -> ReportsResponse:
    products_df = get_products().fillna("")
    purchases_df = get_purchases().fillna("")

    if not products_df.empty:
        products_df["image_url"] = products_df["image_path"].apply(build_public_file_url)

    if not purchases_df.empty:
        purchases_df["invoice_url"] = purchases_df["invoice_path"].apply(build_public_file_url)

    return ReportsResponse(
        products=products_df.to_dict(orient="records"),
        suppliers=get_suppliers().fillna("").to_dict(orient="records"),
        purchases=purchases_df.to_dict(orient="records"),
        sales=get_sales().fillna("").to_dict(orient="records"),
        low_stock=get_low_stock().fillna("").to_dict(orient="records"),
        assignments=get_assignment_history().fillna("").to_dict(orient="records"),
        users=get_users().fillna("").to_dict(orient="records"),
        notes=get_notes().fillna("").to_dict(orient="records"),
    )


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/uploads/product-image")
def upload_product_image(file: UploadFile = File(...)):
    stored_path, stored_name = save_upload_file(file, PRODUCT_IMAGES_DIR)
    return {
        "message": "Product image uploaded successfully",
        "stored_path": stored_path,
        "public_url": f"/media/product-images/{stored_name}",
    }


@app.post("/uploads/purchase-invoice")
def upload_purchase_invoice(file: UploadFile = File(...)):
    stored_path, stored_name = save_upload_file(file, PURCHASE_INVOICES_DIR)
    return {
        "message": "Purchase invoice uploaded successfully",
        "stored_path": stored_path,
        "public_url": f"/media/purchase-invoices/{stored_name}",
    }


@app.post("/auth/login", response_model=UserSummary)
def auth_login(payload: LoginRequest):
    user = login_user(payload.username, payload.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password")

    return UserSummary(
        user_id=user[0],
        full_name=user[1],
        username=user[2],
        role=user[3],
        department=user[4],
        permissions={
            "can_edit_suppliers": int(user[5]),
            "can_delete_suppliers": int(user[6]),
            "can_edit_products": int(user[7]),
            "can_delete_products": int(user[8]),
            "can_edit_purchases": int(user[9]),
            "can_delete_purchases": int(user[10]),
        },
    )


@app.get("/dashboard", response_model=DashboardResponse)
def dashboard():
    return build_dashboard_response()


@app.get("/components", response_model=ComponentListResponse)
def list_components():
    return build_component_response()


@app.get("/suppliers", response_model=SupplierListResponse)
def list_suppliers():
    return build_supplier_response()


@app.post("/suppliers")
def create_supplier(payload: SupplierCreateRequest):
    add_supplier(
        payload.supplier_name,
        payload.contact_number or "",
        payload.email or "",
        payload.address or "",
    )
    return {"message": "Supplier added successfully"}


@app.put("/suppliers/{supplier_id}")
def edit_supplier(supplier_id: int, payload: SupplierUpdateRequest):
    update_supplier(
        supplier_id,
        payload.supplier_name,
        payload.contact_number or "",
        payload.email or "",
        payload.address or "",
    )
    return {"message": "Supplier updated successfully"}


@app.delete("/suppliers/{supplier_id}")
def remove_supplier(supplier_id: int):
    try:
        delete_supplier(supplier_id)
    except Exception as error:
        raise HTTPException(status_code=400, detail=str(error))
    return {"message": "Supplier deleted successfully"}


@app.get("/users", response_model=UserListResponse)
def list_users():
    return build_user_response()


@app.post("/users")
def create_user(payload: UserCreateRequest):
    result = add_user(
        payload.full_name,
        payload.username,
        payload.password,
        payload.role,
        payload.department or "",
        payload.date_of_joining or "",
        payload.office_email or "",
        payload.company_email or "",
        payload.contact_number or "",
        payload.can_edit_suppliers,
        payload.can_delete_suppliers,
        payload.can_edit_products,
        payload.can_delete_products,
        payload.can_edit_purchases,
        payload.can_delete_purchases,
    )
    if result != "User added successfully":
        raise HTTPException(status_code=400, detail=result)
    return {"message": result}


@app.put("/users/{user_id}")
def edit_user(user_id: int, payload: UserUpdateRequest):
    update_user(
        user_id,
        payload.full_name,
        payload.username,
        payload.password or "",
        payload.role,
        payload.department or "",
        payload.date_of_joining or "",
        payload.office_email or "",
        payload.company_email or "",
        payload.contact_number or "",
        payload.can_edit_suppliers,
        payload.can_delete_suppliers,
        payload.can_edit_products,
        payload.can_delete_products,
        payload.can_edit_purchases,
        payload.can_delete_purchases,
    )
    return {"message": "User updated successfully"}


@app.delete("/users/{user_id}")
def remove_user(user_id: int):
    delete_user(user_id)
    return {"message": "User deleted successfully"}


@app.get("/assignments", response_model=AssignmentListResponse)
def list_assignments():
    return build_assignment_response()


@app.post("/assignments")
def create_assignment(payload: AssignmentCreateRequest):
    update_product_assignment(
        payload.product_id,
        payload.assigned_to,
        payload.assigned_date,
        payload.remarks or "",
        payload.status,
    )
    return {"message": "Responsibility updated successfully"}


@app.post("/components")
def create_component(payload: ComponentCreateRequest):
    product_no = generate_product_no()
    result = add_product(
        product_no,
        payload.product_name,
        payload.category or "",
        payload.price,
        payload.reorder_level,
        payload.supplier_id,
        payload.image_path or "",
        payload.assigned_to or "",
    )
    if result != "Product added successfully":
        raise HTTPException(status_code=400, detail=result)

    return {"message": result, "product_no": product_no}


@app.put("/components/{product_id}")
def edit_component(product_id: int, payload: ComponentUpdateRequest):
    update_product(
        product_id,
        payload.product_name,
        payload.category or "",
        payload.price,
        payload.reorder_level,
        payload.supplier_id,
        payload.assigned_to or "",
        payload.image_path,
    )
    return {"message": "Component updated successfully"}


@app.delete("/components/{product_id}")
def remove_component(product_id: int):
    try:
        delete_product(product_id)
    except Exception as error:
        raise HTTPException(status_code=400, detail=str(error))
    return {"message": "Component deactivated successfully"}


@app.get("/purchases", response_model=PurchaseListResponse)
def list_purchases():
    return build_purchase_response()


@app.post("/purchases")
def create_purchase(payload: PurchaseCreateRequest):
    product_options = get_product_dropdown()
    product_row = product_options[product_options["product_id"] == payload.product_id]
    if product_row.empty:
        raise HTTPException(status_code=404, detail="Component not found")

    unit_price = float(product_row.iloc[0]["price"] or 0)
    total_purchase_price = unit_price * int(payload.quantity)

    add_purchase(
        payload.product_id,
        payload.supplier_id,
        payload.quantity,
        unit_price,
        total_purchase_price,
        payload.purchase_date,
        payload.invoice_path or "",
    )
    return {"message": "Purchase recorded successfully"}


@app.put("/purchases/{purchase_id}")
def edit_purchase(purchase_id: int, payload: PurchaseUpdateRequest):
    update_purchase(
        purchase_id,
        payload.quantity,
        payload.supplier_id,
        payload.purchase_date,
        payload.invoice_path or "",
    )
    return {"message": "Purchase updated successfully"}


@app.delete("/purchases/{purchase_id}")
def remove_purchase(purchase_id: int):
    delete_purchase(purchase_id)
    return {"message": "Purchase deleted successfully"}


@app.get("/sales", response_model=SaleListResponse)
def list_sales():
    return build_sale_response()


@app.post("/sales")
def create_sale(payload: SaleCreateRequest):
    product_options = get_product_dropdown()
    product_row = product_options[product_options["product_id"] == payload.product_id]
    if product_row.empty:
        raise HTTPException(status_code=404, detail="Component not found")

    selling_price = float(product_row.iloc[0]["price"] or 0)
    result = add_sale(
        payload.product_id,
        payload.quantity_sold,
        selling_price,
        payload.sale_date,
        payload.customer_name or "",
    )
    if result != "Sale added successfully":
        raise HTTPException(status_code=400, detail=result)

    return {"message": result}


@app.put("/sales/{sale_id}")
def edit_sale(sale_id: int, payload: SaleUpdateRequest):
    result = update_sale(
        sale_id,
        payload.quantity_sold,
        payload.sale_date,
        payload.customer_name or "",
    )
    if result != "Sale updated successfully":
        raise HTTPException(status_code=400, detail=result)

    return {"message": result}


@app.delete("/sales/{sale_id}")
def remove_sale(sale_id: int):
    delete_sale(sale_id)
    return {"message": "Sale deleted successfully"}


@app.get("/notes", response_model=NoteListResponse)
def list_notes():
    return build_note_response()


@app.post("/notes")
def create_note(payload: NoteCreateRequest):
    add_note(
        payload.note_title,
        payload.note_content,
        payload.created_by,
        payload.created_date,
        payload.note_status,
        payload.assigned_to or "",
    )
    return {"message": "Note added successfully"}


@app.put("/notes/{note_id}")
def edit_note(note_id: int, payload: NoteUpdateRequest):
    update_note(
        note_id,
        payload.note_title,
        payload.note_content,
        payload.note_status,
        payload.assigned_to or "",
    )
    return {"message": "Note updated successfully"}


@app.delete("/notes/{note_id}")
def remove_note(note_id: int):
    delete_note(note_id)
    return {"message": "Note deleted successfully"}


@app.get("/reports", response_model=ReportsResponse)
def get_reports():
    return build_reports_response()
