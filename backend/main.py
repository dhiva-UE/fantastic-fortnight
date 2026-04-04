import sys
import base64
import binascii
import hashlib
import hmac
import json
import os
import re
import time
import uuid
from pathlib import Path

from fastapi import Depends, FastAPI, File, HTTPException, Query, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

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
    get_user_by_id,
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
        AuthResponse,
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
        AuthResponse,
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

APP_ENV = os.getenv("APP_ENV", "development").strip().lower()
DEFAULT_DEV_CORS_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:4173",
    "http://127.0.0.1:4173",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]
PRODUCT_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}
PRODUCT_IMAGE_CONTENT_TYPES = {"image/png", "image/jpeg", "image/webp"}
PURCHASE_INVOICE_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg", ".webp"}
PURCHASE_INVOICE_CONTENT_TYPES = {"application/pdf", "image/png", "image/jpeg", "image/webp"}


def parse_csv_env(name: str) -> list[str]:
    raw_value = os.getenv(name, "")
    return [item.strip() for item in raw_value.split(",") if item.strip()]


def read_int_env(name: str, default: int) -> int:
    raw_value = os.getenv(name, "").strip()
    if not raw_value:
        return default
    try:
        return int(raw_value)
    except ValueError as error:
        raise RuntimeError(f"{name} must be an integer.") from error


CORS_ORIGINS = parse_csv_env("CORS_ORIGINS")
if not CORS_ORIGINS and APP_ENV == "development":
    CORS_ORIGINS = DEFAULT_DEV_CORS_ORIGINS

AUTH_SECRET_KEY = os.getenv("AUTH_SECRET_KEY", "").strip()
AUTH_TOKEN_TTL_MINUTES = read_int_env("AUTH_TOKEN_TTL_MINUTES", 480)
MAX_UPLOAD_BYTES = read_int_env("MAX_UPLOAD_BYTES", 5 * 1024 * 1024)

if AUTH_TOKEN_TTL_MINUTES <= 0:
    raise RuntimeError("AUTH_TOKEN_TTL_MINUTES must be greater than zero.")

if MAX_UPLOAD_BYTES <= 0:
    raise RuntimeError("MAX_UPLOAD_BYTES must be greater than zero.")

if APP_ENV in {"production", "staging"} and (not AUTH_SECRET_KEY or AUTH_SECRET_KEY == "change_me"):
    raise RuntimeError("Set a strong AUTH_SECRET_KEY before starting the API in production.")

if not AUTH_SECRET_KEY:
    AUTH_SECRET_KEY = "dev-insecure-key-change-me"

app = FastAPI(
    title="Inbound Inventory API",
    version="0.1.0",
    description="Parallel FastAPI backend for the React migration.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

create_tables()
bearer_scheme = HTTPBearer(auto_error=False)


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

def sanitize_filename(filename: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]", "_", filename)
    return cleaned or "file"


def encode_token_segment(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def decode_token_segment(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(f"{value}{padding}")


def create_access_token(user_id: int) -> str:
    payload = {
        "sub": str(user_id),
        "exp": int(time.time()) + (AUTH_TOKEN_TTL_MINUTES * 60),
    }
    payload_segment = encode_token_segment(
        json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    )
    signature = hmac.new(
        AUTH_SECRET_KEY.encode("utf-8"),
        payload_segment.encode("utf-8"),
        hashlib.sha256,
    ).digest()
    return f"{payload_segment}.{encode_token_segment(signature)}"


def decode_access_token(token: str) -> dict[str, str | int]:
    try:
        payload_segment, signature_segment = token.split(".", 1)
        expected_signature = hmac.new(
            AUTH_SECRET_KEY.encode("utf-8"),
            payload_segment.encode("utf-8"),
            hashlib.sha256,
        ).digest()
        actual_signature = decode_token_segment(signature_segment)
        if not hmac.compare_digest(actual_signature, expected_signature):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid access token")

        payload = json.loads(decode_token_segment(payload_segment).decode("utf-8"))
    except (ValueError, binascii.Error, json.JSONDecodeError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid access token")

    if int(payload.get("exp", 0)) <= int(time.time()):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Access token has expired")

    return payload


def build_user_summary(user_record) -> UserSummary:
    return UserSummary(
        user_id=int(user_record[0]),
        full_name=str(user_record[1]),
        username=str(user_record[2]),
        role=str(user_record[3]),
        department=user_record[4],
        permissions={
            "can_edit_suppliers": int(user_record[9]),
            "can_delete_suppliers": int(user_record[10]),
            "can_edit_products": int(user_record[11]),
            "can_delete_products": int(user_record[12]),
            "can_edit_purchases": int(user_record[13]),
            "can_delete_purchases": int(user_record[14]),
        },
    )


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    access_token: str | None = Query(default=None),
) -> UserSummary:
    token = credentials.credentials if credentials else access_token
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")

    payload = decode_access_token(token)
    try:
        user_id = int(payload.get("sub", 0))
    except (TypeError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid access token")

    user_record = get_user_by_id(user_id)
    if not user_record:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User account no longer exists")

    return build_user_summary(user_record)


def require_admin(current_user: UserSummary = Depends(get_current_user)) -> UserSummary:
    if current_user.role != "Admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return current_user


def require_permission(permission_name: str, current_user: UserSummary) -> UserSummary:
    if current_user.role == "Admin" or int(current_user.permissions.get(permission_name, 0)) == 1:
        return current_user
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have permission for this action")


def require_supplier_edit(current_user: UserSummary = Depends(get_current_user)) -> UserSummary:
    return require_permission("can_edit_suppliers", current_user)


def require_supplier_delete(current_user: UserSummary = Depends(get_current_user)) -> UserSummary:
    return require_permission("can_delete_suppliers", current_user)


def require_product_edit(current_user: UserSummary = Depends(get_current_user)) -> UserSummary:
    return require_permission("can_edit_products", current_user)


def require_product_delete(current_user: UserSummary = Depends(get_current_user)) -> UserSummary:
    return require_permission("can_delete_products", current_user)


def require_purchase_edit(current_user: UserSummary = Depends(get_current_user)) -> UserSummary:
    return require_permission("can_edit_purchases", current_user)


def require_purchase_delete(current_user: UserSummary = Depends(get_current_user)) -> UserSummary:
    return require_permission("can_delete_purchases", current_user)


def resolve_media_file(base_dir: Path, relative_path: str) -> Path:
    candidate = (base_dir / relative_path).resolve()
    base_path = base_dir.resolve()
    try:
        candidate.relative_to(base_path)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found") from error

    if not candidate.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")

    return candidate


def save_upload_file(
    upload_file: UploadFile,
    target_dir: Path,
    allowed_extensions: set[str],
    allowed_content_types: set[str],
) -> tuple[str, str]:
    original_name = sanitize_filename(upload_file.filename or "file")
    suffix = Path(original_name).suffix.lower()
    if suffix not in allowed_extensions:
        allowed_list = ", ".join(sorted(allowed_extensions))
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unsupported file type. Allowed: {allowed_list}")

    content_type = (upload_file.content_type or "").lower()
    if content_type and content_type not in allowed_content_types:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unexpected file content type")

    file_bytes = upload_file.file.read(MAX_UPLOAD_BYTES + 1)
    if not file_bytes:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file is empty")
    if len(file_bytes) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="Uploaded file exceeds the allowed size limit")

    stem = Path(original_name).stem
    stored_name = f"{stem}_{uuid.uuid4().hex[:8]}{suffix}"
    file_path = target_dir / stored_name

    with file_path.open("wb") as output_file:
        output_file.write(file_bytes)

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
    return {"status": "ok", "environment": APP_ENV}


@app.post("/uploads/product-image")
def upload_product_image(
    file: UploadFile = File(...),
    current_user: UserSummary = Depends(get_current_user),
):
    stored_path, stored_name = save_upload_file(
        file,
        PRODUCT_IMAGES_DIR,
        PRODUCT_IMAGE_EXTENSIONS,
        PRODUCT_IMAGE_CONTENT_TYPES,
    )
    return {
        "message": "Product image uploaded successfully",
        "stored_path": stored_path,
        "public_url": f"/media/product-images/{stored_name}",
    }


@app.post("/uploads/purchase-invoice")
def upload_purchase_invoice(
    file: UploadFile = File(...),
    current_user: UserSummary = Depends(get_current_user),
):
    stored_path, stored_name = save_upload_file(
        file,
        PURCHASE_INVOICES_DIR,
        PURCHASE_INVOICE_EXTENSIONS,
        PURCHASE_INVOICE_CONTENT_TYPES,
    )
    return {
        "message": "Purchase invoice uploaded successfully",
        "stored_path": stored_path,
        "public_url": f"/media/purchase-invoices/{stored_name}",
    }


@app.get("/media/product-images/{file_name:path}")
def get_product_image(file_name: str, current_user: UserSummary = Depends(get_current_user)):
    return FileResponse(resolve_media_file(PRODUCT_IMAGES_DIR, file_name))


@app.get("/media/purchase-invoices/{file_name:path}")
def get_purchase_invoice(file_name: str, current_user: UserSummary = Depends(get_current_user)):
    return FileResponse(resolve_media_file(PURCHASE_INVOICES_DIR, file_name))


@app.post("/auth/login", response_model=AuthResponse)
def auth_login(payload: LoginRequest):
    user = login_user(payload.username, payload.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password")

    user_summary = UserSummary(
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
    return AuthResponse(
        **(user_summary.model_dump() if hasattr(user_summary, "model_dump") else user_summary.dict()),
        access_token=create_access_token(user_summary.user_id),
    )


@app.get("/auth/me", response_model=UserSummary)
def auth_me(current_user: UserSummary = Depends(get_current_user)):
    return current_user


@app.get("/dashboard", response_model=DashboardResponse)
def dashboard(current_user: UserSummary = Depends(get_current_user)):
    return build_dashboard_response()


@app.get("/components", response_model=ComponentListResponse)
def list_components(current_user: UserSummary = Depends(get_current_user)):
    return build_component_response()


@app.get("/suppliers", response_model=SupplierListResponse)
def list_suppliers(current_user: UserSummary = Depends(get_current_user)):
    return build_supplier_response()


@app.post("/suppliers")
def create_supplier(payload: SupplierCreateRequest, current_user: UserSummary = Depends(get_current_user)):
    add_supplier(
        payload.supplier_name,
        payload.contact_number or "",
        payload.email or "",
        payload.address or "",
    )
    return {"message": "Supplier added successfully"}


@app.put("/suppliers/{supplier_id}")
def edit_supplier(
    supplier_id: int,
    payload: SupplierUpdateRequest,
    current_user: UserSummary = Depends(require_supplier_edit),
):
    update_supplier(
        supplier_id,
        payload.supplier_name,
        payload.contact_number or "",
        payload.email or "",
        payload.address or "",
    )
    return {"message": "Supplier updated successfully"}


@app.delete("/suppliers/{supplier_id}")
def remove_supplier(
    supplier_id: int,
    current_user: UserSummary = Depends(require_supplier_delete),
):
    try:
        delete_supplier(supplier_id)
    except Exception as error:
        raise HTTPException(status_code=400, detail=str(error))
    return {"message": "Supplier deleted successfully"}


@app.get("/users", response_model=UserListResponse)
def list_users(current_user: UserSummary = Depends(require_admin)):
    return build_user_response()


@app.post("/users")
def create_user(payload: UserCreateRequest, current_user: UserSummary = Depends(require_admin)):
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
def edit_user(
    user_id: int,
    payload: UserUpdateRequest,
    current_user: UserSummary = Depends(require_admin),
):
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
def remove_user(user_id: int, current_user: UserSummary = Depends(require_admin)):
    target_user = get_user_by_id(user_id)
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    if int(target_user[0]) == current_user.user_id:
        raise HTTPException(status_code=400, detail="You cannot delete the currently logged-in user")
    if str(target_user[2]).lower() == "admin":
        raise HTTPException(status_code=400, detail="Default admin account cannot be deleted")
    delete_user(user_id)
    return {"message": "User deleted successfully"}


@app.get("/assignments", response_model=AssignmentListResponse)
def list_assignments(current_user: UserSummary = Depends(get_current_user)):
    return build_assignment_response()


@app.post("/assignments")
def create_assignment(payload: AssignmentCreateRequest, current_user: UserSummary = Depends(get_current_user)):
    update_product_assignment(
        payload.product_id,
        payload.assigned_to,
        payload.assigned_date,
        payload.remarks or "",
        payload.status,
    )
    return {"message": "Responsibility updated successfully"}


@app.post("/components")
def create_component(payload: ComponentCreateRequest, current_user: UserSummary = Depends(get_current_user)):
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
def edit_component(
    product_id: int,
    payload: ComponentUpdateRequest,
    current_user: UserSummary = Depends(require_product_edit),
):
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
def remove_component(
    product_id: int,
    current_user: UserSummary = Depends(require_product_delete),
):
    try:
        delete_product(product_id)
    except Exception as error:
        raise HTTPException(status_code=400, detail=str(error))
    return {"message": "Component deactivated successfully"}


@app.get("/purchases", response_model=PurchaseListResponse)
def list_purchases(current_user: UserSummary = Depends(get_current_user)):
    return build_purchase_response()


@app.post("/purchases")
def create_purchase(payload: PurchaseCreateRequest, current_user: UserSummary = Depends(get_current_user)):
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
def edit_purchase(
    purchase_id: int,
    payload: PurchaseUpdateRequest,
    current_user: UserSummary = Depends(require_purchase_edit),
):
    update_purchase(
        purchase_id,
        payload.quantity,
        payload.supplier_id,
        payload.purchase_date,
        payload.invoice_path or "",
    )
    return {"message": "Purchase updated successfully"}


@app.delete("/purchases/{purchase_id}")
def remove_purchase(
    purchase_id: int,
    current_user: UserSummary = Depends(require_purchase_delete),
):
    delete_purchase(purchase_id)
    return {"message": "Purchase deleted successfully"}


@app.get("/sales", response_model=SaleListResponse)
def list_sales(current_user: UserSummary = Depends(get_current_user)):
    return build_sale_response()


@app.post("/sales")
def create_sale(payload: SaleCreateRequest, current_user: UserSummary = Depends(get_current_user)):
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
def edit_sale(sale_id: int, payload: SaleUpdateRequest, current_user: UserSummary = Depends(get_current_user)):
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
def remove_sale(sale_id: int, current_user: UserSummary = Depends(get_current_user)):
    delete_sale(sale_id)
    return {"message": "Sale deleted successfully"}


@app.get("/notes", response_model=NoteListResponse)
def list_notes(current_user: UserSummary = Depends(get_current_user)):
    return build_note_response()


@app.post("/notes")
def create_note(payload: NoteCreateRequest, current_user: UserSummary = Depends(get_current_user)):
    add_note(
        payload.note_title,
        payload.note_content,
        current_user.full_name,
        payload.created_date,
        payload.note_status,
        payload.assigned_to or "",
    )
    return {"message": "Note added successfully"}


@app.put("/notes/{note_id}")
def edit_note(note_id: int, payload: NoteUpdateRequest, current_user: UserSummary = Depends(get_current_user)):
    update_note(
        note_id,
        payload.note_title,
        payload.note_content,
        payload.note_status,
        payload.assigned_to or "",
    )
    return {"message": "Note updated successfully"}


@app.delete("/notes/{note_id}")
def remove_note(note_id: int, current_user: UserSummary = Depends(get_current_user)):
    delete_note(note_id)
    return {"message": "Note deleted successfully"}


@app.get("/reports", response_model=ReportsResponse)
def get_reports(current_user: UserSummary = Depends(get_current_user)):
    return build_reports_response()
