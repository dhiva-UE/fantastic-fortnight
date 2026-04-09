from pydantic import BaseModel


class LoginRequest(BaseModel):
    username: str
    password: str


class UserSummary(BaseModel):
    user_id: int
    full_name: str
    username: str
    role: str
    department: str | None = None
    permissions: dict[str, int]


class AuthResponse(UserSummary):
    access_token: str
    token_type: str = "bearer"


class DashboardMetrics(BaseModel):
    total_components: int
    total_suppliers: int
    total_stock_qty: int
    total_employees: int
    inventory_value: float
    total_purchase_value: float
    total_sales_value: float


class DashboardResponse(BaseModel):
    metrics: DashboardMetrics
    stock: list[dict]
    low_stock: list[dict]
    recent_purchases: list[dict]
    recent_sales: list[dict]


class SupplierOption(BaseModel):
    supplier_id: int
    supplier_name: str


class EmployeeOption(BaseModel):
    user_id: int
    full_name: str
    username: str
    role: str


class ComponentCreateRequest(BaseModel):
    product_name: str
    category: str | None = ""
    price: float
    reorder_level: int
    supplier_id: int
    assigned_to: str | None = ""
    image_path: str | None = ""


class ComponentUpdateRequest(BaseModel):
    product_name: str
    category: str | None = ""
    price: float
    reorder_level: int
    supplier_id: int
    assigned_to: str | None = ""
    image_path: str | None = None


class ComponentListResponse(BaseModel):
    items: list[dict]
    suppliers: list[SupplierOption]
    employees: list[EmployeeOption]


class ProductOption(BaseModel):
    product_id: int
    product_no: str
    product_name: str
    price: float
    assigned_to: str | None = ""


class PurchaseCreateRequest(BaseModel):
    product_id: int
    supplier_id: int
    quantity: int
    purchase_date: str
    invoice_path: str | None = ""


class PurchaseUpdateRequest(BaseModel):
    quantity: int
    supplier_id: int
    purchase_date: str
    invoice_path: str | None = ""


class PurchaseListResponse(BaseModel):
    items: list[dict]
    products: list[ProductOption]
    suppliers: list[SupplierOption]


class SaleCreateRequest(BaseModel):
    product_id: int
    quantity_sold: int
    sale_date: str
    customer_name: str | None = ""


class SaleUpdateRequest(BaseModel):
    quantity_sold: int
    sale_date: str
    customer_name: str | None = ""


class SaleListResponse(BaseModel):
    items: list[dict]
    products: list[ProductOption]


class NoteCreateRequest(BaseModel):
    note_title: str
    note_content: str
    created_by: str
    created_date: str
    note_status: str = "Open"
    assigned_to: str | None = ""


class NoteUpdateRequest(BaseModel):
    note_title: str
    note_content: str
    note_status: str
    assigned_to: str | None = ""


class NoteListResponse(BaseModel):
    items: list[dict]
    employees: list[EmployeeOption]


class SupplierCreateRequest(BaseModel):
    supplier_name: str
    contact_number: str | None = ""
    email: str | None = ""
    address: str | None = ""


class SupplierUpdateRequest(BaseModel):
    supplier_name: str
    contact_number: str | None = ""
    email: str | None = ""
    address: str | None = ""


class SupplierListResponse(BaseModel):
    items: list[dict]


class UserCreateRequest(BaseModel):
    full_name: str
    username: str
    password: str
    role: str
    department: str | None = ""
    date_of_joining: str | None = ""
    office_email: str | None = ""
    company_email: str | None = ""
    contact_number: str | None = ""
    can_edit_suppliers: int = 0
    can_delete_suppliers: int = 0
    can_edit_products: int = 0
    can_delete_products: int = 0
    can_edit_purchases: int = 0
    can_delete_purchases: int = 0


class UserUpdateRequest(BaseModel):
    full_name: str
    username: str
    password: str | None = ""
    role: str
    department: str | None = ""
    date_of_joining: str | None = ""
    office_email: str | None = ""
    company_email: str | None = ""
    contact_number: str | None = ""
    can_edit_suppliers: int = 0
    can_delete_suppliers: int = 0
    can_edit_products: int = 0
    can_delete_products: int = 0
    can_edit_purchases: int = 0
    can_delete_purchases: int = 0


class UserListResponse(BaseModel):
    items: list[dict]


class AssignmentCreateRequest(BaseModel):
    product_id: int
    assigned_to: str
    assigned_date: str
    remarks: str | None = ""
    status: str = "In Progress"


class AssignmentListResponse(BaseModel):
    items: list[dict]
    products: list[ProductOption]
    employees: list[EmployeeOption]


class TestingProjectCreateRequest(BaseModel):
    project_name: str
    description: str | None = ""


class TestingChecklistCreateRequest(BaseModel):
    project_id: int
    checklist_name: str
    test_date: str
    remarks: str | None = ""
    source_checklist_id: int | None = None


class TestingChecklistItemCreateRequest(BaseModel):
    checklist_id: int
    component_id: int
    issued_to: str | None = ""
    status: str = "Out for Testing"
    remarks: str | None = ""


class TestingChecklistItemUpdateRequest(BaseModel):
    issued_to: str | None = ""
    status: str
    remarks: str | None = ""


class TestingListResponse(BaseModel):
    projects: list[dict]
    checklists: list[dict]
    items: list[dict]
    components: list[ProductOption]
    employees: list[EmployeeOption]


class ReportsResponse(BaseModel):
    products: list[dict]
    suppliers: list[dict]
    purchases: list[dict]
    sales: list[dict]
    low_stock: list[dict]
    assignments: list[dict]
    users: list[dict]
    notes: list[dict]
