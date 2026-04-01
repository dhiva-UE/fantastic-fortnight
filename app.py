import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import plotly.express as px
import os
from datetime import date
from pathlib import Path

from database import (
    create_tables,
    generate_product_no,
    add_supplier, get_suppliers, update_supplier, delete_supplier,
    add_product, get_products, get_product_dropdown, delete_product, update_product,
    update_product_assignment, get_assignment_history,
    add_purchase, get_purchases, delete_purchase, update_purchase,
    add_sale, get_sales, delete_sale, update_sale,
    get_low_stock,
    add_user, get_users, get_user_dropdown, login_user, delete_user, update_user,
    add_note, get_notes, update_note, delete_note
)


def apply_company_theme():
    st.markdown(
        """
        <style>
        :root {
            --ia-bg: #eef4f8;
            --ia-surface: rgba(255, 255, 255, 0.92);
            --ia-surface-strong: #ffffff;
            --ia-ink: #10212f;
            --ia-muted: #587084;
            --ia-line: rgba(16, 33, 47, 0.10);
            --ia-brand: #0d2740;
            --ia-brand-soft: #123a5c;
            --ia-accent: #1fa2ff;
            --ia-accent-soft: rgba(31, 162, 255, 0.12);
            --ia-success: #138a5a;
            --ia-warn: #b36b00;
            --ia-danger: #b42318;
            --ia-shadow: 0 18px 45px rgba(13, 39, 64, 0.10);
            --ia-radius-lg: 24px;
            --ia-radius-md: 18px;
        }

        .stApp {
            background:
                radial-gradient(circle at top right, rgba(31, 162, 255, 0.14), transparent 24%),
                linear-gradient(180deg, #f8fbfd 0%, var(--ia-bg) 100%);
            color: var(--ia-ink);
        }

        [data-testid="stAppViewContainer"] > .main {
            background: transparent;
        }

        [data-testid="stSidebar"] {
            background:
                linear-gradient(180deg, rgba(13, 39, 64, 0.98) 0%, rgba(9, 28, 46, 0.98) 100%);
            border-right: 1px solid rgba(255, 255, 255, 0.08);
        }

        [data-testid="stSidebar"] * {
            color: #f5fbff !important;
        }

        [data-testid="stSidebar"] .stSelectbox label,
        [data-testid="stSidebar"] .stButton label,
        [data-testid="stSidebar"] .stRadio label {
            color: #d7e6f5 !important;
        }

        [data-testid="stSidebar"] .stSelectbox > div > div,
        [data-testid="stSidebar"] .stTextInput > div > div > input {
            background: rgba(255, 255, 255, 0.08) !important;
            border: 1px solid rgba(255, 255, 255, 0.12) !important;
            border-radius: 14px !important;
        }

        .block-container {
            padding-top: 1.4rem;
            padding-bottom: 3rem;
            max-width: 1480px;
        }

        div[data-testid="stVerticalBlock"] div[data-testid="stVerticalBlockBorderWrapper"],
        div[data-testid="stForm"],
        div[data-testid="metric-container"] {
            background: var(--ia-surface);
            border: 1px solid var(--ia-line);
            border-radius: var(--ia-radius-md);
            box-shadow: var(--ia-shadow);
            backdrop-filter: blur(12px);
        }

        div[data-testid="metric-container"] {
            padding: 0.9rem 1rem;
        }

        .ia-hero {
            position: relative;
            overflow: hidden;
            padding: 2rem 2.2rem;
            border-radius: 28px;
            background:
                linear-gradient(135deg, rgba(8, 27, 43, 0.98) 0%, rgba(15, 52, 81, 0.98) 58%, rgba(31, 162, 255, 0.9) 100%);
            box-shadow: 0 28px 54px rgba(13, 39, 64, 0.22);
            color: #f8fbfd;
            margin-bottom: 1.2rem;
        }

        .ia-hero::after {
            content: "";
            position: absolute;
            inset: auto -10% -30% auto;
            width: 320px;
            height: 320px;
            border-radius: 50%;
            background: radial-gradient(circle, rgba(255,255,255,0.18) 0%, rgba(255,255,255,0) 68%);
        }

        .ia-kicker {
            font-size: 0.78rem;
            letter-spacing: 0.18em;
            text-transform: uppercase;
            font-weight: 700;
            color: rgba(255,255,255,0.72);
            margin-bottom: 0.5rem;
        }

        .ia-title {
            font-size: 2.25rem;
            line-height: 1.05;
            font-weight: 800;
            margin: 0 0 0.45rem 0;
        }

        .ia-subtitle {
            font-size: 1rem;
            line-height: 1.6;
            color: rgba(245, 251, 255, 0.78);
            max-width: 900px;
            margin: 0;
        }

        h1, h2, h3 {
            color: var(--ia-brand);
            letter-spacing: -0.02em;
        }

        .stButton > button,
        .stDownloadButton > button,
        .stFormSubmitButton > button {
            border-radius: 999px !important;
            border: 1px solid transparent !important;
            background: linear-gradient(135deg, var(--ia-brand) 0%, var(--ia-brand-soft) 100%) !important;
            color: white !important;
            font-weight: 700 !important;
            box-shadow: 0 14px 26px rgba(13, 39, 64, 0.22);
            padding-left: 1rem !important;
            padding-right: 1rem !important;
        }

        .stButton > button:hover,
        .stDownloadButton > button:hover,
        .stFormSubmitButton > button:hover {
            transform: translateY(-1px);
            border-color: rgba(31, 162, 255, 0.4) !important;
            background: linear-gradient(135deg, var(--ia-brand-soft) 0%, #19517e 100%) !important;
        }

        .stAlert {
            border-radius: 18px;
            border: 1px solid var(--ia-line);
        }

        .stDataFrame,
        div[data-testid="stTable"] {
            border-radius: var(--ia-radius-md);
            overflow: hidden;
            border: 1px solid var(--ia-line);
        }

        [data-testid="stToolbar"] {
            right: 1rem;
        }

        .ia-section-note {
            color: var(--ia-muted);
            font-size: 0.95rem;
            margin-top: -0.35rem;
            margin-bottom: 0.9rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_brand_header():
    st.markdown(
        """
        <div class="ia-hero">
            <div class="ia-kicker">Inbound Aerospace</div>
            <div class="ia-title">Inbound Inventory Control Center</div>
            <p class="ia-subtitle">
                Aerospace-themed operations workspace for components, purchasing, sales, responsibility tracking,
                reporting, and internal coordination.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="Inventory Management Software", layout="wide")
# apply_company_theme()  # removed: revert to Streamlit default styling
create_tables()

BASE_DIR = Path(__file__).resolve().parent


def get_storage_dir(env_var_name, default_folder_name):
    configured_path = os.getenv(env_var_name, "").strip()
    path = Path(configured_path) if configured_path else BASE_DIR / default_folder_name

    if path.exists() and not path.is_dir():
        fallback_path = BASE_DIR / "storage" / default_folder_name
        fallback_path.mkdir(parents=True, exist_ok=True)
        return fallback_path

    path.mkdir(parents=True, exist_ok=True)
    return path


def save_uploaded_file(uploaded_file, target_dir, filename):
    file_path = target_dir / filename
    with open(file_path, "wb") as file_handle:
        file_handle.write(uploaded_file.getbuffer())
    return str(file_path)


PRODUCT_IMAGES_DIR = get_storage_dir("PRODUCT_IMAGES_DIR", "product_images")
PURCHASE_INVOICES_DIR = get_storage_dir("PURCHASE_INVOICES_DIR", "purchase_invoices")

# render_brand_header()  # removed: revert to Streamlit default header styling

# ---------------- SESSION ----------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "user_role" not in st.session_state:
    st.session_state.user_role = None

if "full_name" not in st.session_state:
    st.session_state.full_name = None

if "username" not in st.session_state:
    st.session_state.username = None

if "department" not in st.session_state:
    st.session_state.department = None

if "permissions" not in st.session_state:
    st.session_state.permissions = {
        "can_edit_suppliers": 0,
        "can_delete_suppliers": 0,
        "can_edit_products": 0,
        "can_delete_products": 0,
        "can_edit_purchases": 0,
        "can_delete_purchases": 0
    }

if "flash_message" not in st.session_state:
    st.session_state.flash_message = None

if "flash_type" not in st.session_state:
    st.session_state.flash_type = "success"

# ---------------- FLASH HELPER ----------------
def force_refresh(message=None, error=None):
    if message:
        st.session_state.flash_message = message
        st.session_state.flash_type = "success"
    elif error:
        st.session_state.flash_message = error
        st.session_state.flash_type = "error"
    st.rerun()


def run_action(action, success_message):
    try:
        result = action()
        if isinstance(result, str) and result not in {"Sale added successfully", "Sale updated successfully"}:
            force_refresh(error=result)
        else:
            force_refresh(success_message if success_message else result)
    except ValueError as error:
        st.error(str(error))
    except Exception as error:
        st.error(f"Operation failed: {error}")


def mark_menu_changed():
    st.session_state.scroll_to_top = True


def render_scroll_to_top():
    components.html(
        """
        <script>
        requestAnimationFrame(() => {
          const parentDoc = window.parent.document;
          const selectors = [
            'section.main',
            '[data-testid="stAppViewContainer"]',
            '.main',
            'body'
          ];
          selectors.forEach((selector) => {
            parentDoc.querySelectorAll(selector).forEach((el) => {
              if (el) {
                el.scrollTo(0, 0);
                el.scrollTop = 0;
              }
            });
          });
          if (parentDoc.documentElement) {
            parentDoc.documentElement.scrollTop = 0;
          }
          if (parentDoc.body) {
            parentDoc.body.scrollTop = 0;
          }
          window.parent.scrollTo(0, 0);
        });
        </script>
        """,
        height=0,
    )

# ---------------- SHOW FLASH ----------------
if st.session_state.flash_message:
    if st.session_state.flash_type == "success":
        st.success(st.session_state.flash_message)
    else:
        st.error(st.session_state.flash_message)

    st.session_state.flash_message = None
    st.session_state.flash_type = "success"

# ---------------- LOGIN ----------------
if not st.session_state.logged_in:
    st.subheader("🔐 Login")

    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        login_btn = st.form_submit_button("Login")

        if login_btn:
            user = login_user(username, password)

            if user:
                st.session_state.logged_in = True
                st.session_state.full_name = user[1]
                st.session_state.username = user[2]
                st.session_state.user_role = user[3]
                st.session_state.department = user[4]

                st.session_state.permissions = {
                    "can_edit_suppliers": user[5],
                    "can_delete_suppliers": user[6],
                    "can_edit_products": user[7],
                    "can_delete_products": user[8],
                    "can_edit_purchases": user[9],
                    "can_delete_purchases": user[10]
                }

                st.session_state.flash_message = f"Welcome {user[1]}!"
                st.session_state.flash_type = "success"
                st.rerun()
            else:
                st.error("Invalid username or password")

    st.stop()

# ---------------- SIDEBAR ----------------
st.sidebar.success(f"👤 {st.session_state.full_name}")
st.sidebar.info(f"Role: {st.session_state.user_role}")
st.sidebar.caption(f"Department: {st.session_state.department if st.session_state.department else 'N/A'}")

if st.sidebar.button("🚪 Logout"):
    st.session_state.logged_in = False
    st.session_state.user_role = None
    st.session_state.full_name = None
    st.session_state.username = None
    st.session_state.department = None
    st.session_state.permissions = {
        "can_edit_suppliers": 0,
        "can_delete_suppliers": 0,
        "can_edit_products": 0,
        "can_delete_products": 0,
        "can_edit_purchases": 0,
        "can_delete_purchases": 0
    }
    st.rerun()

if st.session_state.user_role == "Admin":
    menu_options = ["Dashboard", "Users", "Suppliers", "Components", "Components Responsibility", "Purchases", "Sales", "Low Stock", "Notes", "Reports"]
else:
    menu_options = ["Dashboard", "Suppliers", "Components", "Components Responsibility", "Purchases", "Sales", "Low Stock", "Notes", "Reports"]

if "menu_select" not in st.session_state:
    st.session_state.menu_select = menu_options[0]

menu = st.sidebar.selectbox("Select Module", menu_options, key="menu_select", on_change=mark_menu_changed)

if st.session_state.get("scroll_to_top"):
    render_scroll_to_top()
    st.session_state.scroll_to_top = False

# ---------------- HELPER ----------------
def format_inr(value):
    try:
        return f"₹ {float(value):,.2f}"
    except:
        return "₹ 0.00"

# ---------------- FILTER HELPER ----------------
def apply_period_filter(df, date_column, key_prefix):
    if df.empty or date_column not in df.columns:
        return df

    filter_type = st.selectbox(
        "Filter By",
        ["All", "Day", "Week", "Month", "Year"],
        key=f"{key_prefix}_filter_type"
    )

    working_df = df.copy()
    working_df[date_column] = pd.to_datetime(working_df[date_column], errors="coerce")
    working_df = working_df.dropna(subset=[date_column])

    if filter_type == "All":
        return working_df

    if filter_type == "Day":
        selected_day = st.date_input("Select Day", key=f"{key_prefix}_day")
        return working_df[working_df[date_column].dt.date == selected_day]

    if filter_type == "Week":
        selected_day = st.date_input("Select Any Date in Week", key=f"{key_prefix}_week")
        selected_timestamp = pd.Timestamp(selected_day)
        week_start = selected_timestamp - pd.Timedelta(days=selected_timestamp.weekday())
        week_end = week_start + pd.Timedelta(days=6)
        return working_df[
            (working_df[date_column] >= week_start.normalize()) &
            (working_df[date_column] < (week_end + pd.Timedelta(days=1)).normalize())
        ]

    if filter_type == "Month":
        selected_month = st.date_input("Select Month", key=f"{key_prefix}_month")
        return working_df[
            (working_df[date_column].dt.year == selected_month.year) &
            (working_df[date_column].dt.month == selected_month.month)
        ]

    year_options = sorted(working_df[date_column].dt.year.dropna().astype(int).unique(), reverse=True)
    selected_year = st.selectbox("Select Year", year_options, key=f"{key_prefix}_year")
    return working_df[working_df[date_column].dt.year == selected_year]


# ---------------- DASHBOARD ----------------
if menu == "Dashboard":
    st.header("📊 Dashboard Overview")

    products_df = get_products()
    suppliers_df = get_suppliers()
    purchases_df = get_purchases()
    sales_df = get_sales()
    users_df = get_users()

    total_products = len(products_df)
    total_suppliers = len(suppliers_df)
    total_stock_qty = products_df["quantity"].sum() if not products_df.empty else 0
    total_employees = len(users_df)

    inventory_value = (products_df["quantity"] * products_df["price"]).sum() if not products_df.empty else 0
    total_purchase_value = purchases_df["total_purchase_price"].sum() if not purchases_df.empty else 0
    total_sales_value = sales_df["total_sales_value"].sum() if not sales_df.empty else 0

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Components", total_products)
    col2.metric("Total Suppliers", total_suppliers)
    col3.metric("Total Stock Qty", int(total_stock_qty))
    col4.metric("Total Employees", total_employees)

    col5, col6, col7 = st.columns(3)
    col5.metric("Inventory Value", format_inr(inventory_value))
    col6.metric("Purchase Value", format_inr(total_purchase_value))
    col7.metric("Sales Revenue", format_inr(total_sales_value))

    st.subheader("📦 Current Stock")
    if not products_df.empty:
        display_df = products_df.copy()
        display_df["price"] = display_df["price"].apply(format_inr)
        st.dataframe(display_df, use_container_width=True)
    else:
        st.info("No products available yet.")

    st.subheader("Purchase Trend")
    if not purchases_df.empty:
        chart_scope = st.selectbox("Purchase View", ["Monthly", "Quarterly", "Yearly"], key="dashboard_purchase_chart")
        chart_df = purchases_df.copy()
        chart_df["purchase_date"] = pd.to_datetime(chart_df["purchase_date"], errors="coerce")
        chart_df = chart_df.dropna(subset=["purchase_date"])

        if not chart_df.empty:
            if chart_scope == "Monthly":
                chart_df["period"] = chart_df["purchase_date"].dt.to_period("M").astype(str)
            elif chart_scope == "Quarterly":
                chart_df["period"] = chart_df["purchase_date"].dt.to_period("Q").astype(str)
            else:
                chart_df["period"] = chart_df["purchase_date"].dt.year.astype(str)

            grouped_chart_df = chart_df.groupby("period", as_index=False)["total_purchase_price"].sum()
            purchase_chart = px.bar(
                grouped_chart_df,
                x="period",
                y="total_purchase_price",
                labels={"period": "Period", "total_purchase_price": "Purchase Value"},
            )
            st.plotly_chart(purchase_chart, use_container_width=True)
        else:
            st.info("No dated purchase records available for charting.")
    else:
        st.info("No purchase data available for charting yet.")

# ---------------- USERS ----------------
elif menu == "Users":
    st.header("👥 User Management")

    if st.session_state.user_role != "Admin":
        st.error("Access denied. Only Admin can manage users.")
        st.stop()

    with st.form("user_form", clear_on_submit=True):
        full_name = st.text_input("Full Name")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        role = st.selectbox("Role", ["Admin", "Employee", "CEO", "CBO", "CGO"])
        department = st.text_input("Department")
        date_of_joining = st.date_input("Date of Joining")
        office_email = st.text_input("Office Email ID")
        company_email = st.text_input("Company Email ID")
        contact_number = st.text_input("Contact Number")

        st.markdown("### Permissions")
        can_edit_suppliers = st.selectbox("Can Edit Suppliers", [1, 0], format_func=lambda value: "Yes" if value == 1 else "No")
        can_delete_suppliers = st.selectbox("Can Delete Suppliers", [1, 0], format_func=lambda value: "Yes" if value == 1 else "No")
        can_edit_products = st.selectbox("Can Edit Components", [1, 0], format_func=lambda value: "Yes" if value == 1 else "No")
        can_delete_products = st.selectbox("Can Delete Components", [1, 0], format_func=lambda value: "Yes" if value == 1 else "No")
        can_edit_purchases = st.selectbox("Can Edit Purchases", [1, 0], format_func=lambda value: "Yes" if value == 1 else "No")
        can_delete_purchases = st.selectbox("Can Delete Purchases", [1, 0], format_func=lambda value: "Yes" if value == 1 else "No")

        submitted = st.form_submit_button("Add User")

        if submitted:
            if full_name.strip() and username.strip() and password.strip():
                try:
                    result = add_user(
                        full_name, username, password, role, department,
                        str(date_of_joining), office_email, company_email, contact_number,
                        int(can_edit_suppliers), int(can_delete_suppliers),
                        int(can_edit_products), int(can_delete_products),
                        int(can_edit_purchases), int(can_delete_purchases)
                    )

                    if result == "User added successfully":
                        force_refresh(result)
                    else:
                        force_refresh(error=result)
                except ValueError as error:
                    st.error(str(error))
            else:
                st.error("All fields are required.")

    st.subheader("📋 Existing Users")
    users_df = get_users()
    st.dataframe(users_df, use_container_width=True)

    if not users_df.empty:
        st.subheader("✏ Edit User")

        edit_user_options = {
            f"{row['user_id']} - {row['full_name']} ({row['role']})": row["user_id"]
            for _, row in users_df.iterrows()
        }

        selected_edit_user = st.selectbox("Select User to Edit", list(edit_user_options.keys()))
        selected_user_id = edit_user_options[selected_edit_user]
        selected_user_row = users_df[users_df["user_id"] == selected_user_id].iloc[0]

        with st.form("edit_user_form"):
            edit_full_name = st.text_input("Full Name", value=selected_user_row["full_name"])
            edit_username = st.text_input("Username", value=selected_user_row["username"])
            edit_password = st.text_input("Password", type="password")
            role_options = ["Admin", "Employee", "CEO", "CBO", "CGO"]
            edit_role = st.selectbox(
                "Role",
                role_options,
                index=role_options.index(selected_user_row["role"]) if selected_user_row["role"] in role_options else 1
            )
            edit_department = st.text_input("Department", value=selected_user_row["department"] if pd.notna(selected_user_row["department"]) else "")
            edit_joining_date = st.date_input(
                "Date of Joining",
                value=pd.to_datetime(selected_user_row["date_of_joining"]).date() if pd.notna(selected_user_row["date_of_joining"]) and str(selected_user_row["date_of_joining"]).strip() else date.today(),
                key="edit_joining_date"
            )
            edit_office_email = st.text_input("Office Email ID", value=selected_user_row["office_email"] if pd.notna(selected_user_row["office_email"]) else "")
            edit_company_email = st.text_input("Company Email ID", value=selected_user_row["company_email"] if pd.notna(selected_user_row["company_email"]) else "")
            edit_contact_number = st.text_input("Contact Number", value=selected_user_row["contact_number"] if pd.notna(selected_user_row["contact_number"]) else "")

            st.markdown("### Permissions")
            edit_can_edit_suppliers = st.selectbox("Can Edit Suppliers", [1, 0], index=0 if int(selected_user_row["can_edit_suppliers"]) == 1 else 1, format_func=lambda value: "Yes" if value == 1 else "No", key="e1")
            edit_can_delete_suppliers = st.selectbox("Can Delete Suppliers", [1, 0], index=0 if int(selected_user_row["can_delete_suppliers"]) == 1 else 1, format_func=lambda value: "Yes" if value == 1 else "No", key="e2")
            edit_can_edit_products = st.selectbox("Can Edit Components", [1, 0], index=0 if int(selected_user_row["can_edit_products"]) == 1 else 1, format_func=lambda value: "Yes" if value == 1 else "No", key="e3")
            edit_can_delete_products = st.selectbox("Can Delete Components", [1, 0], index=0 if int(selected_user_row["can_delete_products"]) == 1 else 1, format_func=lambda value: "Yes" if value == 1 else "No", key="e4")
            edit_can_edit_purchases = st.selectbox("Can Edit Purchases", [1, 0], index=0 if int(selected_user_row["can_edit_purchases"]) == 1 else 1, format_func=lambda value: "Yes" if value == 1 else "No", key="e5")
            edit_can_delete_purchases = st.selectbox("Can Delete Purchases", [1, 0], index=0 if int(selected_user_row["can_delete_purchases"]) == 1 else 1, format_func=lambda value: "Yes" if value == 1 else "No", key="e6")

            update_user_btn = st.form_submit_button("Update User")

            if update_user_btn:
                try:
                    update_user(
                        selected_user_id,
                        edit_full_name,
                        edit_username,
                        edit_password,
                        edit_role,
                        edit_department,
                        str(edit_joining_date),
                        edit_office_email,
                        edit_company_email,
                        edit_contact_number,
                        int(edit_can_edit_suppliers),
                        int(edit_can_delete_suppliers),
                        int(edit_can_edit_products),
                        int(edit_can_delete_products),
                        int(edit_can_edit_purchases),
                        int(edit_can_delete_purchases)
                    )
                    force_refresh("User updated successfully!")
                except ValueError as error:
                    st.error(str(error))

        st.subheader("🗑 Delete User")
        selected_delete_user = st.selectbox("Select User to Delete", list(edit_user_options.keys()), key="delete_user")

        if st.button("Delete User"):
            selected_delete_user_id = edit_user_options[selected_delete_user]
            selected_delete_row = users_df[users_df["user_id"] == selected_delete_user_id].iloc[0]

            if selected_delete_row["username"] == "admin":
                st.error("Default Admin cannot be deleted.")
            elif selected_delete_row["username"] == st.session_state.username:
                st.error("You cannot delete the currently logged-in user.")
            else:
                run_action(
                    lambda: delete_user(selected_delete_user_id),
                    "User deleted successfully!"
                )

# ---------------- SUPPLIERS ----------------
elif menu == "Suppliers":
    st.header("🏢 Supplier Management")

    with st.form("supplier_form", clear_on_submit=True):
        supplier_name = st.text_input("Supplier Name")
        contact_number = st.text_input("Contact Number")
        email = st.text_input("Email")
        address = st.text_area("Address")

        submitted = st.form_submit_button("Add Supplier")

        if submitted:
            if supplier_name.strip():
                try:
                    add_supplier(supplier_name, contact_number, email, address)
                    force_refresh("Supplier added successfully!")
                except ValueError as error:
                    st.error(str(error))
            else:
                st.error("Supplier name is required.")

    st.subheader("Supplier List")
    supplier_df = get_suppliers()
    st.dataframe(supplier_df, use_container_width=True)

    if not supplier_df.empty and (st.session_state.user_role == "Admin" or st.session_state.permissions["can_edit_suppliers"] == 1):
        st.subheader("✏ Edit Supplier")

        supplier_options = {
            f"{row['supplier_id']} - {row['supplier_name']}": row["supplier_id"]
            for _, row in supplier_df.iterrows()
        }

        selected_supplier = st.selectbox("Select Supplier to Edit", list(supplier_options.keys()))
        selected_supplier_id = supplier_options[selected_supplier]
        supplier_row = supplier_df[supplier_df["supplier_id"] == selected_supplier_id].iloc[0]

        with st.form("edit_supplier_form"):
            edit_name = st.text_input("Supplier Name", value=supplier_row["supplier_name"])
            edit_contact = st.text_input("Contact Number", value=supplier_row["contact_number"] if pd.notna(supplier_row["contact_number"]) else "")
            edit_email = st.text_input("Email", value=supplier_row["email"] if pd.notna(supplier_row["email"]) else "")
            edit_address = st.text_area("Address", value=supplier_row["address"] if pd.notna(supplier_row["address"]) else "")

            if st.form_submit_button("Update Supplier"):
                try:
                    update_supplier(selected_supplier_id, edit_name, edit_contact, edit_email, edit_address)
                    force_refresh("Supplier updated successfully!")
                except ValueError as error:
                    st.error(str(error))

    if not supplier_df.empty and (st.session_state.user_role == "Admin" or st.session_state.permissions["can_delete_suppliers"] == 1):
        st.subheader("🗑 Delete Supplier")
        delete_supplier_select = st.selectbox(
            "Select Supplier to Delete",
            list({f"{row['supplier_id']} - {row['supplier_name']}": row["supplier_id"] for _, row in supplier_df.iterrows()}.keys()),
            key="delete_supplier_select"
        )

        if st.button("Delete Supplier"):
            supplier_id = int(delete_supplier_select.split(" - ")[0])
            run_action(
                lambda: delete_supplier(supplier_id),
                "Supplier deleted successfully!"
            )

# ---------------- COMPONENTS ----------------
elif menu == "Components":
    st.header("🛒 Component Management")

    suppliers_df = get_suppliers()
    users_dropdown_df = get_user_dropdown()
    employee_names = users_dropdown_df["full_name"].dropna().tolist() if not users_dropdown_df.empty else []

    if suppliers_df.empty:
        st.warning("Please add suppliers first before adding components.")
    else:
        supplier_options = {
            row["supplier_name"]: row["supplier_id"]
            for _, row in suppliers_df.iterrows()
        }

        auto_product_no = generate_product_no()
        st.info(f"Auto Product No: {auto_product_no}")

        with st.form("product_form", clear_on_submit=True):
            product_name = st.text_input("Component Name")
            category = st.text_input("Category")
            price = st.number_input("Component Price (₹)", min_value=0.0, format="%.2f")
            reorder_level = st.number_input("Reorder Level", min_value=1, value=5)
            supplier_name = st.selectbox("Supplier", list(supplier_options.keys()))
            assigned_to = st.selectbox(
                "Assigned To / Responsible Person",
                [""] + employee_names,
                format_func=lambda value: value if value else "Not Assigned"
            )
            product_image = st.file_uploader("Upload Component Image", type=["png", "jpg", "jpeg"], key="product_image")

            submitted = st.form_submit_button("Add Component")

            if submitted:
                if product_name.strip():
                    supplier_id = supplier_options[supplier_name]

                    image_path = ""
                    if product_image is not None:
                        ext = os.path.splitext(product_image.name)[1]
                        image_filename = f"{auto_product_no}{ext}"
                        image_path = save_uploaded_file(product_image, PRODUCT_IMAGES_DIR, image_filename)

                    try:
                        result = add_product(
                            auto_product_no, product_name, category, price,
                            reorder_level, supplier_id, image_path, assigned_to
                        )

                        if result == "Product added successfully":
                            force_refresh(f"{result} | Product No: {auto_product_no}")
                        else:
                            force_refresh(error=result)
                    except ValueError as error:
                        st.error(str(error))
                else:
                    st.error("Component Name is required.")

    st.subheader("🔍 Search Components")
    products_df = get_products()
    search_term = st.text_input("Search by Component No / Component Name")

    if not products_df.empty:
        if search_term:
            products_df = products_df[
                products_df["product_no"].str.contains(search_term, case=False, na=False) |
                products_df["product_name"].str.contains(search_term, case=False, na=False)
            ]

        display_df = products_df.copy()
        display_df["price"] = display_df["price"].apply(format_inr)
        st.dataframe(display_df, use_container_width=True)

        st.subheader("🖼 Component Image Preview")
        selected_product_no = st.selectbox("Select Component to Preview Image", products_df["product_no"].tolist())
        selected_row = products_df[products_df["product_no"] == selected_product_no].iloc[0]

        if selected_row["image_path"] and os.path.exists(selected_row["image_path"]):
            st.image(selected_row["image_path"], caption=selected_row["product_name"], width=550)
        else:
            st.info("No image uploaded for this component.")

        if st.session_state.user_role == "Admin" or st.session_state.permissions["can_edit_products"] == 1:
            st.subheader("✏ Edit Component")
            product_edit_options = {
                f"{row['product_id']} - {row['product_no']} - {row['product_name']}": row["product_no"]
                for _, row in products_df.iterrows()
            }
            edit_product_no = st.selectbox("Select Component to Edit", list(product_edit_options.keys()), key="edit_product")
            edit_row = products_df[products_df["product_no"] == product_edit_options[edit_product_no]].iloc[0]

            edit_supplier_name = st.selectbox(
                "Edit Supplier",
                list(supplier_options.keys()),
                index=list(supplier_options.values()).index(
                    suppliers_df[suppliers_df["supplier_name"] == edit_row["supplier_name"]]["supplier_id"].iloc[0]
                ) if edit_row["supplier_name"] in suppliers_df["supplier_name"].values else 0
            )

            with st.form("edit_product_form"):
                edit_name = st.text_input("Component Name", value=edit_row["product_name"])
                edit_category = st.text_input("Category", value=edit_row["category"] if pd.notna(edit_row["category"]) else "")
                edit_price = st.number_input("Price", min_value=0.0, value=float(edit_row["price"]))
                edit_reorder = st.number_input("Reorder Level", min_value=1, value=int(edit_row["reorder_level"]))
                current_assigned = edit_row["assigned_to"] if pd.notna(edit_row["assigned_to"]) else ""
                assigned_options = [""] + employee_names
                if current_assigned and current_assigned not in assigned_options:
                    assigned_options.append(current_assigned)
                edit_assigned = st.selectbox(
                    "Assigned To",
                    assigned_options,
                    index=assigned_options.index(current_assigned) if current_assigned in assigned_options else 0,
                    format_func=lambda value: value if value else "Not Assigned"
                )

                if st.form_submit_button("Update Component"):
                    try:
                        update_product(
                            edit_row["product_id"],
                            edit_name,
                            edit_category,
                            edit_price,
                            edit_reorder,
                            supplier_options[edit_supplier_name],
                            edit_assigned
                        )
                        force_refresh("Component updated successfully!")
                    except ValueError as error:
                        st.error(str(error))

        if st.session_state.user_role == "Admin" or st.session_state.permissions["can_delete_products"] == 1:
            st.subheader("🗑 Delete Component")
            product_delete_options = {
                f"{row['product_id']} - {row['product_no']} - {row['product_name']}": row["product_no"]
                for _, row in products_df.iterrows()
            }
            delete_product_no = st.selectbox("Select Component to Delete", list(product_delete_options.keys()), key="delete_product")
            delete_row = products_df[products_df["product_no"] == product_delete_options[delete_product_no]].iloc[0]

            if st.button("Delete Component"):
                run_action(
                    lambda: delete_product(delete_row["product_id"]),
                    f"Component {delete_row['product_no']} deleted successfully!"
                )

# ---------------- COMPONENTS RESPONSIBILITY ----------------
elif menu == "Components Responsibility":
    st.header("👤 Component Responsibility Transfer")

    products_df = get_product_dropdown()
    users_dropdown_df = get_user_dropdown()
    employee_names = users_dropdown_df["full_name"].dropna().tolist() if not users_dropdown_df.empty else []

    if products_df.empty:
        st.warning("Please add components first.")
    else:
        product_options = {
            f"{row['product_no']} - {row['product_name']}": {
                "id": row["product_id"],
                "assigned_to": row["assigned_to"]
            }
            for _, row in products_df.iterrows()
        }

        selected_product = st.selectbox("Select Component", list(product_options.keys()))
        current_person = product_options[selected_product]["assigned_to"]

        st.info(f"Current Responsible Person: {current_person if current_person else 'Not Assigned'}")

        new_person = st.selectbox(
            "Transfer Responsibility To",
            [""] + employee_names,
            format_func=lambda value: value if value else "Select Employee"
        )
        assigned_date = st.date_input("Assignment Date", format="DD/MM/YYYY")
        status = st.selectbox("Status", ["In Progress", "Under Review", "Testing", "Completed"])
        remarks = st.text_area("Remarks (Optional)", placeholder="Example: Handed over to Person 2")

        if st.button("Update Assignment"):
            if new_person.strip():
                product_id = product_options[selected_product]["id"]
                try:
                    update_product_assignment(product_id, new_person, str(assigned_date), remarks, status)
                    force_refresh("Responsibility updated successfully!")
                except ValueError as error:
                    st.error(str(error))
            else:
                st.error("Please select the responsible person.")

    st.subheader("📜 Assignment History")
    history_df = get_assignment_history()
    st.dataframe(history_df, use_container_width=True)

# ---------------- PURCHASES ----------------
elif menu == "Purchases":
    st.header("📥 Purchase Entry")

    products_df = get_product_dropdown()
    suppliers_df = get_suppliers()

    if products_df.empty or suppliers_df.empty:
        st.warning("Please add suppliers and components first.")
    else:
        product_options = {
            f"{row['product_no']} - {row['product_name']}": {
                "id": row["product_id"],
                "price": row["price"],
                "product_no": row["product_no"]
            }
            for _, row in products_df.iterrows()
        }

        supplier_options = {
            row["supplier_name"]: row["supplier_id"]
            for _, row in suppliers_df.iterrows()
        }

        selected_product = st.selectbox("Select Component", list(product_options.keys()), key="purchase_product")
        selected_supplier = st.selectbox("Select Supplier", list(supplier_options.keys()), key="purchase_supplier")
        quantity = st.number_input("Quantity Purchased", min_value=1, step=1, key="purchase_quantity")
        purchase_date = st.date_input("Purchase Date", key="purchase_date", format="DD/MM/YYYY")
        invoice_file = st.file_uploader("Upload Invoice", type=["pdf", "png", "jpg", "jpeg"], key="purchase_invoice")

        unit_price = product_options[selected_product]["price"]
        total_purchase_price = unit_price * quantity

        st.info(f"Unit Price: {format_inr(unit_price)}")
        st.success(f"Total Purchase Price: {format_inr(total_purchase_price)}")

        if invoice_file is not None:
            invoice_ext = os.path.splitext(invoice_file.name)[1].lower()
            if invoice_ext in [".png", ".jpg", ".jpeg"]:
                st.image(invoice_file, caption="Invoice Preview", width=550)
            else:
                st.info(f"Selected invoice: {invoice_file.name}")

        if st.button("Add Purchase", key="add_purchase_button"):
            product_id = product_options[selected_product]["id"]
            supplier_id = supplier_options[selected_supplier]
            product_no = product_options[selected_product]["product_no"]

            invoice_path = ""
            if invoice_file is not None:
                ext = os.path.splitext(invoice_file.name)[1]
                invoice_filename = f"INV_{product_no}_{purchase_date}{ext}"
                invoice_path = save_uploaded_file(invoice_file, PURCHASE_INVOICES_DIR, invoice_filename)

            try:
                add_purchase(
                    product_id,
                    supplier_id,
                    quantity,
                    unit_price,
                    total_purchase_price,
                    str(purchase_date),
                    invoice_path
                )
                force_refresh("Purchase recorded successfully!")
            except ValueError as error:
                st.error(str(error))

    st.subheader("📜 Purchase History")
    purchase_df = get_purchases()
    purchase_df = apply_period_filter(purchase_df, "purchase_date", "purchase_history")

    if not purchase_df.empty:
        display_df = purchase_df.copy()
        display_df["unit_price"] = display_df["unit_price"].apply(format_inr)
        display_df["total_purchase_price"] = display_df["total_purchase_price"].apply(format_inr)
        st.dataframe(display_df, use_container_width=True)

        purchase_options = {
            f"{row['purchase_id']} - {row['product_no']} - {row['product_name']}": row["purchase_id"]
            for _, row in purchase_df.iterrows()
        }

        if st.session_state.user_role == "Admin" or st.session_state.permissions["can_edit_purchases"] == 1:
            st.subheader("✏ Edit Purchase")
            selected_purchase = st.selectbox("Select Purchase to Edit", list(purchase_options.keys()))
            selected_purchase_id = purchase_options[selected_purchase]
            purchase_row = purchase_df[purchase_df["purchase_id"] == selected_purchase_id].iloc[0]

            with st.form("edit_purchase_form"):
                edit_qty = st.number_input("Quantity Purchased", min_value=1, value=int(purchase_row["quantity_purchased"]))
                edit_date = st.date_input("Purchase Date", value=pd.to_datetime(purchase_row["purchase_date"]).date(), format="DD/MM/YYYY")
                supplier_names = list(supplier_options.keys())
                current_supplier_name = purchase_row["supplier_name"] if pd.notna(purchase_row["supplier_name"]) else supplier_names[0]
                edit_supplier_name = st.selectbox(
                    "Supplier",
                    supplier_names,
                    index=supplier_names.index(current_supplier_name) if current_supplier_name in supplier_names else 0
                )
                edit_invoice_file = st.file_uploader(
                    "Replace Invoice (Optional)",
                    type=["pdf", "png", "jpg", "jpeg"],
                    key="edit_purchase_invoice"
                )

                if st.form_submit_button("Update Purchase"):
                    try:
                        edit_invoice_path = purchase_row["invoice_path"] if pd.notna(purchase_row["invoice_path"]) else ""
                        if edit_invoice_file is not None:
                            ext = os.path.splitext(edit_invoice_file.name)[1]
                            invoice_filename = f"INV_{purchase_row['product_no']}_{edit_date}{ext}"
                            edit_invoice_path = save_uploaded_file(edit_invoice_file, PURCHASE_INVOICES_DIR, invoice_filename)

                        update_purchase(
                            selected_purchase_id,
                            edit_qty,
                            supplier_options[edit_supplier_name],
                            str(edit_date),
                            edit_invoice_path
                        )
                        force_refresh("Purchase updated successfully!")
                    except ValueError as error:
                        st.error(str(error))

        if st.session_state.user_role == "Admin" or st.session_state.permissions["can_delete_purchases"] == 1:
            st.subheader("🗑 Delete Purchase")
            delete_purchase_select = st.selectbox("Select Purchase to Delete", list(purchase_options.keys()), key="delete_purchase")

            if st.button("Delete Purchase"):
                delete_purchase_id = purchase_options[delete_purchase_select]
                run_action(
                    lambda: delete_purchase(delete_purchase_id),
                    "Purchase deleted successfully!"
                )

# ---------------- SALES ----------------
elif menu == "Sales":
    st.header("📤 Sales Entry")

    products_df = get_products()

    if products_df.empty:
        st.warning("Please add components first.")
    else:
        product_options = {
            f"{row['product_no']} - {row['product_name']}": {"id": row["product_id"], "price": row["price"]}
            for _, row in products_df.iterrows()
        }

        with st.form("sales_form", clear_on_submit=True):
            selected_product = st.selectbox("Select Component", list(product_options.keys()))
            quantity_sold = st.number_input("Quantity Sold", min_value=1, step=1)
            sale_date = st.date_input("Sale Date")
            customer_name = st.text_input("Customer Name (Optional)")

            selling_price = product_options[selected_product]["price"]
            st.info(f"Selling Price: {format_inr(selling_price)}")

            if st.form_submit_button("Add Sale"):
                product_id = product_options[selected_product]["id"]
                try:
                    result = add_sale(product_id, quantity_sold, selling_price, str(sale_date), customer_name)

                    if result == "Sale added successfully":
                        force_refresh(result)
                    else:
                        force_refresh(error=result)
                except ValueError as error:
                    st.error(str(error))

    st.subheader("Sales History")
    sales_df = get_sales()

    if not sales_df.empty:
        display_df = sales_df.copy()
        display_df["selling_price"] = display_df["selling_price"].apply(format_inr)
        display_df["total_sales_value"] = display_df["total_sales_value"].apply(format_inr)
        st.dataframe(display_df, use_container_width=True)

        sales_options = {
            f"{row['sale_id']} - {row['product_no']}": row["sale_id"]
            for _, row in sales_df.iterrows()
        }

        st.subheader("Edit Sale")
        selected_sale = st.selectbox("Select Sale to Edit", list(sales_options.keys()))
        selected_sale_id = sales_options[selected_sale]
        sale_row = sales_df[sales_df["sale_id"] == selected_sale_id].iloc[0]

        with st.form("edit_sale_form"):
            edit_sale_qty = st.number_input("Quantity Sold", min_value=1, value=int(sale_row["quantity_sold"]))
            edit_sale_date = st.date_input("Sale Date", value=pd.to_datetime(sale_row["sale_date"]).date())
            edit_customer_name = st.text_input(
                "Customer Name",
                value=sale_row["customer_name"] if pd.notna(sale_row["customer_name"]) else ""
            )

            if st.form_submit_button("Update Sale"):
                try:
                    result = update_sale(
                        selected_sale_id,
                        edit_sale_qty,
                        str(edit_sale_date),
                        edit_customer_name
                    )
                    if result == "Sale updated successfully":
                        force_refresh(result)
                    else:
                        force_refresh(error=result)
                except ValueError as error:
                    st.error(str(error))

        st.subheader("Delete Sale")
        delete_sale_select = st.selectbox("Select Sale to Delete", list(sales_options.keys()), key="delete_sale")

        if st.button("Delete Sale"):
            sale_id = sales_options[delete_sale_select]
            run_action(
                lambda: delete_sale(sale_id),
                "Sale deleted successfully!"
            )

# ---------------- LOW STOCK ----------------
elif menu == "Low Stock":
    st.header("⚠️ Low Stock Alert")

    low_stock_df = get_low_stock()

    if low_stock_df.empty:
        st.success("No low stock items. Inventory looks healthy.")
    else:
        st.warning("These components need restocking:")
        st.dataframe(low_stock_df, use_container_width=True)

# ---------------- NOTES ----------------
elif menu == "Notes":
    st.header("📝 Work Notes")

    users_dropdown_df = get_user_dropdown()
    employee_names = users_dropdown_df["full_name"].dropna().tolist() if not users_dropdown_df.empty else []

    with st.form("notes_form", clear_on_submit=True):
        note_title = st.text_input("Note Title")
        note_content = st.text_area("Note Content")
        note_status = st.selectbox("Status", ["Open", "In Progress", "Completed"])
        assigned_to = st.selectbox(
            "Assigned To",
            [""] + employee_names,
            format_func=lambda value: value if value else "Not Assigned"
        )
        submitted = st.form_submit_button("Add Note")

        if submitted:
            if note_title.strip() and note_content.strip():
                try:
                    add_note(note_title, note_content, st.session_state.full_name, str(date.today()), note_status, assigned_to)
                    force_refresh("Note added successfully!")
                except ValueError as error:
                    st.error(str(error))
            else:
                st.error("Title and Note content are required.")

    notes_df = get_notes()
    st.subheader("📋 Notes List")
    st.dataframe(notes_df, use_container_width=True)

    if not notes_df.empty:
        st.subheader("✏ Edit Note")
        note_options = {
            f"{row['note_id']} - {row['note_title']}": row["note_id"]
            for _, row in notes_df.iterrows()
        }

        selected_note = st.selectbox("Select Note to Edit", list(note_options.keys()))
        selected_note_id = note_options[selected_note]
        note_row = notes_df[notes_df["note_id"] == selected_note_id].iloc[0]

        with st.form("edit_note_form"):
            edit_title = st.text_input("Edit Title", value=note_row["note_title"])
            edit_content = st.text_area("Edit Content", value=note_row["note_content"])
            edit_status = st.selectbox("Edit Status", ["Open", "In Progress", "Completed"],
                                       index=["Open", "In Progress", "Completed"].index(note_row["note_status"]))
            current_note_assigned = note_row["assigned_to"] if pd.notna(note_row["assigned_to"]) else ""
            note_assigned_options = [""] + employee_names
            if current_note_assigned and current_note_assigned not in note_assigned_options:
                note_assigned_options.append(current_note_assigned)
            edit_assigned_to = st.selectbox(
                "Assigned To",
                note_assigned_options,
                index=note_assigned_options.index(current_note_assigned) if current_note_assigned in note_assigned_options else 0,
                format_func=lambda value: value if value else "Not Assigned"
            )

            if st.form_submit_button("Update Note"):
                try:
                    update_note(selected_note_id, edit_title, edit_content, edit_status, edit_assigned_to)
                    force_refresh("Note updated successfully!")
                except ValueError as error:
                    st.error(str(error))

        st.subheader("🗑 Delete Note")
        delete_note_select = st.selectbox("Select Note to Delete", list(note_options.keys()), key="delete_note")

        if st.button("Delete Note"):
            delete_note_id = note_options[delete_note_select]
            run_action(
                lambda: delete_note(delete_note_id),
                "Note deleted successfully!"
            )

# ---------------- REPORTS ----------------
elif menu == "Reports":
    st.header("📑 Reports")

    report_type = st.selectbox(
        "Select Report",
        ["Components Report", "Suppliers Report", "Purchases Report", "Sales Report", "Low Stock Report", "Components Responsibility Report", "Users Report", "Notes Report"]
    )

    df = pd.DataFrame()

    if report_type == "Components Report":
        df = get_products()
        if not df.empty:
            df["price"] = df["price"].apply(format_inr)

    elif report_type == "Suppliers Report":
        df = get_suppliers()

    elif report_type == "Purchases Report":
        df = get_purchases()
        df = apply_period_filter(df, "purchase_date", "reports_purchase")
        if not df.empty:
            df["unit_price"] = df["unit_price"].apply(format_inr)
            df["total_purchase_price"] = df["total_purchase_price"].apply(format_inr)

    elif report_type == "Sales Report":
        df = get_sales()
        df = apply_period_filter(df, "sale_date", "reports_sales")
        if not df.empty:
            df["selling_price"] = df["selling_price"].apply(format_inr)
            df["total_sales_value"] = df["total_sales_value"].apply(format_inr)

    elif report_type == "Low Stock Report":
        df = get_low_stock()

    elif report_type == "Components Responsibility Report":
        df = get_assignment_history()
        df = apply_period_filter(df, "assigned_date", "reports_assignments")

    elif report_type == "Users Report":
        df = get_users()
        df = apply_period_filter(df, "date_of_joining", "reports_users")

    elif report_type == "Notes Report":
        df = get_notes()
        df = apply_period_filter(df, "created_date", "reports_notes")

    if not df.empty:
        st.dataframe(df, use_container_width=True)

        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="⬇ Download Report as CSV",
            data=csv,
            file_name=f"{report_type.replace(' ', '_').lower()}.csv",
            mime="text/csv"
        )
    else:
        st.info("No data available for this report.")
