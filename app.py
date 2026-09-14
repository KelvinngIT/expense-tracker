import streamlit as st
import pandas as pd
from datetime import datetime
import os
import calendar
import re
import random
import string

st.set_page_config(
    page_title="Expense Tracker",
    page_icon="💰",
    layout="wide"
)

# ======================
# Helper Functions
# ======================
def clean_amount(series):
    if series is None or len(series) == 0:
        return series
    s = series.astype(str)
    s = s.str.replace(r"[$,€£¥\s]", "", regex=True)
    s = s.str.replace(r"[^0-9.\-]", "", regex=True)
    return pd.to_numeric(s, errors="coerce").fillna(0.0)

def is_valid_email(email: str) -> bool:
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email.strip()))

def sanitize_email(email: str) -> str:
    return re.sub(r"[^a-zA-Z0-9]", "_", email.lower().strip())

def generate_verification_code(length=6):
    return "".join(random.choices(string.digits, k=length))

def read_csv_chinese_safe(filepath_or_buffer):
    """Try common encodings used by Chinese Excel / Windows systems."""
    encodings = ["utf-8-sig", "utf-8", "gbk", "gb18030", "big5", "cp936"]
    last_error = None
    for enc in encodings:
        try:
            if hasattr(filepath_or_buffer, "seek"):
                filepath_or_buffer.seek(0)
            return pd.read_csv(filepath_or_buffer, encoding=enc)
        except Exception as e:
            last_error = e
            continue
    raise ValueError(f"Could not read CSV. Last error: {last_error}")

def has_corrupted_chinese(df: pd.DataFrame, text_cols) -> bool:
    """Detect if text already contains the replacement character or many ?"""
    for col in text_cols:
        if col in df.columns:
            s = df[col].astype(str)
            if s.str.contains("�|\?\?\?", regex=True, na=False).any():
                return True
    return False

def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = (
        df.columns.astype(str)
        .str.strip()
        .str.lower()
        .str.replace(r"[\s\-]+", "_", regex=True)
        .str.replace(r"[^\w]", "", regex=True)
    )
    alias_map = {
        "date": "Date", "transaction_date": "Date", "txn_date": "Date",
        "payment_date": "Date", "posted_date": "Date",
        "category": "Category", "nature": "Category", "type": "Category",
        "expense_type": "Category", "account": "Category",
        "amount": "Amount", "value": "Amount", "price": "Amount",
        "cost": "Amount", "total": "Amount", "debit": "Amount",
        "vendor": "Vendor", "vendor_name": "Vendor", "payee": "Vendor",
        "merchant": "Vendor", "supplier": "Vendor", "store": "Vendor",
        "company": "Vendor", "business": "Vendor", "name": "Vendor", "party": "Vendor",
        "description": "Description", "desc": "Description", "memo": "Description",
        "details": "Description", "narrative": "Description",
        "remark": "Remark", "remarks": "Remark", "note": "Remark",
        "notes": "Remark", "comment": "Remark", "comments": "Remark",
        "source": "Source", "payment_method": "Source", "method": "Source",
        "user": "User", "email": "User",
        "customer": "Customer", "customer_name": "Customer", "client": "Customer",
    }
    rename = {}
    for col in df.columns:
        if col in alias_map:
            rename[col] = alias_map[col]
        else:
            rename[col] = col.replace("_", " ").title()
    df = df.rename(columns=rename)
    df = df.loc[:, ~df.columns.duplicated()]
    return df

# ======================
# Session State Init
# ======================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user_email" not in st.session_state:
    st.session_state.user_email = None
if "verification_code" not in st.session_state:
    st.session_state.verification_code = None
if "pending_email" not in st.session_state:
    st.session_state.pending_email = None
if "code_sent" not in st.session_state:
    st.session_state.code_sent = False

# ======================
# Login + Verification UI
# ======================
st.sidebar.header("🔐 Login with Email")

if not st.session_state.logged_in:
    if not st.session_state.code_sent:
        with st.sidebar.form("email_form"):
            email = st.text_input("Email address", placeholder="you@example.com")
            send_btn = st.form_submit_button(
                "Send Verification Code", use_container_width=True, type="primary"
            )
            if send_btn:
                email = email.strip().lower()
                if not email:
                    st.error("Please enter your email.")
                elif not is_valid_email(email):
                    st.error("Please enter a valid email address.")
                else:
                    code = generate_verification_code()
                    st.session_state.verification_code = code
                    st.session_state.pending_email = email
                    st.session_state.code_sent = True
                    st.rerun()
    else:
        st.sidebar.info(f"Code sent to:\n**{st.session_state.pending_email}**")
        st.sidebar.warning(f"🧪 Demo Code: **{st.session_state.verification_code}**")
        st.sidebar.caption("In a real app this code would be sent by email.")
        with st.sidebar.form("verify_form"):
            user_code = st.text_input("Enter 6-digit verification code", max_chars=6)
            col1, col2 = st.columns(2)
            with col1:
                verify_btn = st.form_submit_button(
                    "Verify & Login", use_container_width=True, type="primary"
                )
            with col2:
                back_btn = st.form_submit_button("← Back", use_container_width=True)
            if back_btn:
                st.session_state.code_sent = False
                st.session_state.verification_code = None
                st.session_state.pending_email = None
                st.rerun()
            if verify_btn:
                if user_code.strip() == st.session_state.verification_code:
                    st.session_state.logged_in = True
                    st.session_state.user_email = st.session_state.pending_email
                    st.session_state.code_sent = False
                    st.session_state.verification_code = None
                    st.session_state.pending_email = None
                    st.success("Login successful!")
                    st.rerun()
                else:
                    st.error("Incorrect verification code. Please try again.")
else:
    st.sidebar.success(f"Logged in as:\n**{st.session_state.user_email}**")
    if st.sidebar.button("Logout", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.user_email = None
        st.session_state.pop("expenses", None)
        st.session_state.pop("income", None)
        st.rerun()

if not st.session_state.logged_in:
    st.title("💰 Expense Tracker")
    st.info("👈 Please login with your email in the sidebar to continue.")
    st.stop()

# ======================
# User Data Setup
# ======================
USER = st.session_state.user_email
safe_user = sanitize_email(USER)
DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)
USER_FILE = os.path.join(DATA_DIR, f"{safe_user}_expenses.csv")
INCOME_FILE = os.path.join(DATA_DIR, f"{safe_user}_income.csv")

COLUMNS = [
    "Date", "User", "Category", "Amount",
    "Vendor", "Description", "Remark", "Source"
]
INCOME_COLUMNS = [
    "Date", "User", "Category", "Amount",
    "Customer", "Description", "Remark", "Source"
]

# ---- Expenses ----
if "expenses" not in st.session_state:
    if os.path.exists(USER_FILE):
        try:
            st.session_state.expenses = read_csv_chinese_safe(USER_FILE)
            for col in COLUMNS:
                if col not in st.session_state.expenses.columns:
                    st.session_state.expenses[col] = ""
            st.session_state.expenses = st.session_state.expenses[COLUMNS]
        except Exception:
            st.session_state.expenses = pd.DataFrame(columns=COLUMNS)
    else:
        st.session_state.expenses = pd.DataFrame(columns=COLUMNS)

st.session_state.expenses["Amount"] = clean_amount(st.session_state.expenses["Amount"])

def save_data():
    st.session_state.expenses.to_csv(USER_FILE, index=False, encoding="utf-8-sig")

# ---- Income ----
if "income" not in st.session_state:
    if os.path.exists(INCOME_FILE):
        try:
            st.session_state.income = read_csv_chinese_safe(INCOME_FILE)
            for col in INCOME_COLUMNS:
                if col not in st.session_state.income.columns:
                    st.session_state.income[col] = ""
            st.session_state.income = st.session_state.income[INCOME_COLUMNS]
        except Exception:
            st.session_state.income = pd.DataFrame(columns=INCOME_COLUMNS)
    else:
        st.session_state.income = pd.DataFrame(columns=INCOME_COLUMNS)

st.session_state.income["Amount"] = clean_amount(st.session_state.income["Amount"])

def save_income():
    st.session_state.income.to_csv(INCOME_FILE, index=False, encoding="utf-8-sig")

# Warn user if existing data is already corrupted
if has_corrupted_chinese(st.session_state.expenses, ["Vendor", "Description", "Remark"]) or \
   has_corrupted_chinese(st.session_state.income, ["Customer", "Description", "Remark"]):
    st.error(
        "⚠️ Your saved data already contains corrupted Chinese text (????).\n\n"
        "Please delete the files inside the `data` folder and re-enter the Chinese text. "
        "New entries will work correctly."
    )

CATEGORIES = [
    "Food & Dining", "Transportation", "Shopping", "Bills & Utilities",
    "Entertainment", "Health", "Education", "Travel",
    "Type", "Family Support", "Assets", "Other"
]
INCOME_CATEGORIES = [
    "Salary", "Freelance", "Business", "Investment",
    "Gift", "Refund", "Rental", "Other"
]
SOURCES = ["Manual", "Bank", "Credit Card", "Cash", "Import", "Other"]

# ======================
# Sidebar - Add Expense
# ======================
st.sidebar.markdown("---")
st.sidebar.header("➕ Add New Expense")

with st.sidebar.form("expense_form", clear_on_submit=True):
    date = st.date_input("Date", value=datetime.now(), key="exp_date")
    category = st.selectbox("Category", CATEGORIES, key="exp_cat")
    amount = st.number_input("Amount ($)", min_value=0.0, step=0.01, format="%.2f", key="exp_amt")
    vendor = st.text_input("Vendor", placeholder="星巴克 / 星巴克, Uber, 淘宝...", key="exp_vendor")
    description = st.text_input("Description", placeholder="午餐 / 午餐, 月费...", key="exp_desc")
    remark = st.text_input("Remark", placeholder="可选备注...", key="exp_remark")
    source = st.selectbox("Source", SOURCES, index=0, key="exp_source")
    submitted = st.form_submit_button("Add Expense", use_container_width=True)
    if submitted:
        if amount <= 0:
            st.error("Please enter a valid amount (> 0)")
        else:
            new_row = {
                "Date": str(date),
                "User": USER,
                "Category": category,
                "Amount": float(amount),
                "Vendor": vendor.strip() if vendor else "-",
                "Description": description.strip() if description else "-",
                "Remark": remark.strip() if remark else "-",
                "Source": source,
            }
            st.session_state.expenses = pd.concat(
                [st.session_state.expenses, pd.DataFrame([new_row])], ignore_index=True
            )
            save_data()
            st.success(f"Added: {category} - ${amount:,.2f}")
            st.rerun()

# ======================
# Sidebar - Add Income
# ======================
st.sidebar.markdown("---")
st.sidebar.header("💵 Add New Income")

with st.sidebar.form("income_form", clear_on_submit=True):
    inc_date = st.date_input("Date", value=datetime.now(), key="inc_date")
    inc_category = st.selectbox("Category", INCOME_CATEGORIES, key="inc_cat")
    inc_amount = st.number_input("Amount ($)", min_value=0.0, step=0.01, format="%.2f", key="inc_amt")
    inc_customer = st.text_input("Customer", placeholder="客户名称 / 客戶名稱...", key="inc_customer")
    inc_description = st.text_input("Description", placeholder="月薪 / 项目款...", key="inc_desc")
    inc_remark = st.text_input("Remark", placeholder="可选备注...", key="inc_remark")
    inc_source = st.selectbox("Source", SOURCES, index=0, key="inc_source")
    inc_submitted = st.form_submit_button("Add Income", use_container_width=True, type="primary")
    if inc_submitted:
        if inc_amount <= 0:
            st.error("Please enter a valid amount (> 0)")
        else:
            new_inc = {
                "Date": str(inc_date),
                "User": USER,
                "Category": inc_category,
                "Amount": float(inc_amount),
                "Customer": inc_customer.strip() if inc_customer else "-",
                "Description": inc_description.strip() if inc_description else "-",
                "Remark": inc_remark.strip() if inc_remark else "-",
                "Source": inc_source,
            }
            st.session_state.income = pd.concat(
                [st.session_state.income, pd.DataFrame([new_inc])], ignore_index=True
            )
            save_income()
            st.success(f"Income added: {inc_category} - ${inc_amount:,.2f}")
            st.rerun()

# ======================
# Sidebar - Upload Expenses
# ======================
st.sidebar.markdown("---")
st.sidebar.header("📥 Upload Expenses")

uploaded_file = st.sidebar.file_uploader(
    "Upload Expenses CSV",
    type=["csv"],
    help="Supports Simplified & Traditional Chinese. Prefer CSV UTF-8 from Excel.",
    key="upload_expenses",
)
if uploaded_file is not None:
    try:
        import_df = read_csv_chinese_safe(uploaded_file)
        import_df.columns = import_df.columns.astype(str).str.strip()
        original_cols = list(import_df.columns)
        import_df = normalize_columns(import_df)

        min_required = {"Date", "Category", "Amount"}
        if not min_required.issubset(set(import_df.columns)):
            st.sidebar.error(
                f"Missing required columns.\nNeed at least: Date, Category, Amount\n"
                f"Found: {', '.join(original_cols)}"
            )
        else:
            defaults = {"User": USER, "Vendor": "-", "Description": "-", "Remark": "-", "Source": "Import"}
            for col, default in defaults.items():
                if col not in import_df.columns:
                    import_df[col] = default
            for col in COLUMNS:
                if col not in import_df.columns:
                    import_df[col] = defaults.get(col, "-")

            import_df = import_df[COLUMNS].copy()
            import_df["Amount"] = clean_amount(import_df["Amount"])
            import_df = import_df[import_df["Amount"] > 0].copy()

            for col in ["User", "Category", "Vendor", "Description", "Remark", "Source", "Date"]:
                import_df[col] = import_df[col].fillna(defaults.get(col, "-")).astype(str).str.strip()
                import_df.loc[import_df[col] == "", col] = defaults.get(col, "-")
                if col == "Vendor":
                    import_df.loc[import_df[col].str.lower().isin(["nan", "none", "null"]), col] = "-"

            st.sidebar.markdown(f"**Preview** ({len(import_df)} rows)")
            st.sidebar.dataframe(import_df[["Date", "Category", "Amount", "Vendor"]].head(5), use_container_width=True, hide_index=True)

            if st.sidebar.button("Import Expenses", use_container_width=True, type="primary", key="import_exp"):
                before = len(st.session_state.expenses)
                st.session_state.expenses = pd.concat([st.session_state.expenses, import_df], ignore_index=True)
                st.session_state.expenses["Amount"] = clean_amount(st.session_state.expenses["Amount"])
                save_data()
                st.sidebar.success(f"✅ Imported {len(st.session_state.expenses) - before} expenses!")
                st.rerun()
    except Exception as e:
        st.sidebar.error(f"Error reading file: {e}")

# ======================
# Sidebar - Upload Income
# ======================
st.sidebar.markdown("---")
st.sidebar.header("📥 Upload Income")

uploaded_income = st.sidebar.file_uploader(
    "Upload Income CSV",
    type=["csv"],
    help="Supports Simplified & Traditional Chinese. Prefer CSV UTF-8 from Excel.",
    key="upload_income",
)
if uploaded_income is not None:
    try:
        import_inc = read_csv_chinese_safe(uploaded_income)
        import_inc.columns = import_inc.columns.astype(str).str.strip()
        import_inc = normalize_columns(import_inc)

        if "Vendor" in import_inc.columns and "Customer" not in import_inc.columns:
            import_inc = import_inc.rename(columns={"Vendor": "Customer"})

        min_required = {"Date", "Category", "Amount"}
        if not min_required.issubset(set(import_inc.columns)):
            st.sidebar.error(f"Missing required columns. Found: {', '.join(import_inc.columns)}")
        else:
            defaults = {"User": USER, "Customer": "-", "Description": "-", "Remark": "-", "Source": "Import"}
            for col, default in defaults.items():
                if col not in import_inc.columns:
                    import_inc[col] = default
            for col in INCOME_COLUMNS:
                if col not in import_inc.columns:
                    import_inc[col] = defaults.get(col, "-")

            import_inc = import_inc[INCOME_COLUMNS].copy()
            import_inc["Amount"] = clean_amount(import_inc["Amount"])
            import_inc = import_inc[import_inc["Amount"] > 0].copy()

            for col in ["User", "Category", "Customer", "Description", "Remark", "Source", "Date"]:
                import_inc[col] = import_inc[col].fillna(defaults.get(col, "-")).astype(str).str.strip()
                import_inc.loc[import_inc[col] == "", col] = defaults.get(col, "-")

            st.sidebar.dataframe(import_inc[["Date", "Category", "Amount", "Customer"]].head(3), use_container_width=True, hide_index=True)

            if st.sidebar.button("Import Income", use_container_width=True, type="primary", key="import_inc"):
                before = len(st.session_state.income)
                st.session_state.income = pd.concat([st.session_state.income, import_inc], ignore_index=True)
                st.session_state.income["Amount"] = clean_amount(st.session_state.income["Amount"])
                save_income()
                st.sidebar.success(f"Successfully imported {len(st.session_state.income) - before} income records!")
                st.rerun()
    except Exception as e:
        st.sidebar.error(f"Error reading income file: {e}")

# ======================
# Sidebar - Filters
# ======================
st.sidebar.markdown("---")
st.sidebar.header("🔍 Filters")

view_mode = st.sidebar.radio("Show", options=["Expenses", "Income", "Both"], index=0, horizontal=True, key="view_mode")

all_dates = []
if not st.session_state.expenses.empty:
    all_dates.extend(pd.to_datetime(st.session_state.expenses["Date"], errors="coerce").dropna().tolist())
if not st.session_state.income.empty:
    all_dates.extend(pd.to_datetime(st.session_state.income["Date"], errors="coerce").dropna().tolist())

if all_dates:
    all_dates = pd.Series(all_dates)
    years = sorted(all_dates.dt.year.dropna().astype(int).unique())
    months = sorted(all_dates.dt.month.dropna().astype(int).unique())
    month_names = {m: calendar.month_name[m] for m in months}
    month_options = ["All"] + [month_names[m] for m in months]
else:
    years = []
    month_options = ["All"]
    month_names = {}

selected_year = st.sidebar.selectbox("Year", options=["All"] + list(years) if years else ["All"])
selected_month = st.sidebar.selectbox("Month", options=month_options)

# Filter Expenses
filtered_expenses = st.session_state.expenses.copy()
if not filtered_expenses.empty:
    filtered_expenses["Date"] = pd.to_datetime(filtered_expenses["Date"], errors="coerce")
    filtered_expenses["Year"] = filtered_expenses["Date"].dt.year
    filtered_expenses["Month"] = filtered_expenses["Date"].dt.month
    if selected_year != "All":
        filtered_expenses = filtered_expenses[filtered_expenses["Year"] == int(selected_year)]
    if selected_month != "All":
        month_num = [k for k, v in month_names.items() if v == selected_month][0]
        filtered_expenses = filtered_expenses[filtered_expenses["Month"] == month_num]
    filtered_expenses["Amount"] = clean_amount(filtered_expenses["Amount"])

# Filter Income
filtered_income = st.session_state.income.copy()
if not filtered_income.empty:
    filtered_income["Date"] = pd.to_datetime(filtered_income["Date"], errors="coerce")
    filtered_income["Year"] = filtered_income["Date"].dt.year
    filtered_income["Month"] = filtered_income["Date"].dt.month
    if selected_year != "All":
        filtered_income = filtered_income[filtered_income["Year"] == int(selected_year)]
    if selected_month != "All":
        month_num = [k for k, v in month_names.items() if v == selected_month][0]
        filtered_income = filtered_income[filtered_income["Month"] == month_num]
    filtered_income["Amount"] = clean_amount(filtered_income["Amount"])

# ======================
# Main Area
# ======================
st.title("💰 Expense Tracker")
st.markdown(f"Welcome, **{USER}**!")
st.markdown(
    '<p style="color:red; font-weight:bold; font-size:18px;">'
    "⚠️ Do remember to download the file to save your record</p>",
    unsafe_allow_html=True,
)

col_m1, col_m2, col_m3 = st.columns(3)
total_expense = filtered_expenses["Amount"].sum() if not filtered_expenses.empty else 0.0
total_income = filtered_income["Amount"].sum() if not filtered_income.empty else 0.0
net = total_income - total_expense

with col_m1:
    st.metric("Total Spent", f"${total_expense:,.2f}")
with col_m2:
    st.metric("Total Income", f"${total_income:,.2f}")
with col_m3:
    st.metric("Net Balance", f"${net:,.2f}", delta="Surplus" if net >= 0 else "Deficit")

# ======================
# DOWNLOAD BUTTONS
# ======================
st.markdown("### 📥 Download Your Data")
col_dl1, col_dl2, col_dl3 = st.columns(3)

with col_dl1:
    if not st.session_state.expenses.empty:
        csv_exp = st.session_state.expenses.to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            label="📥 Download Expenses CSV",
            data=csv_exp,
            file_name=f"{safe_user}_expenses.csv",
            mime="text/csv",
            use_container_width=True,
            key="download_expenses",
        )
    else:
        st.button("📥 Download Expenses CSV", disabled=True, use_container_width=True)

with col_dl2:
    if not st.session_state.income.empty:
        csv_inc = st.session_state.income.to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            label="📥 Download Income CSV",
            data=csv_inc,
            file_name=f"{safe_user}_income.csv",
            mime="text/csv",
            use_container_width=True,
            key="download_income",
        )
    else:
        st.button("📥 Download Income CSV", disabled=True, use_container_width=True)

with col_dl3:
    if not st.session_state.expenses.empty or not st.session_state.income.empty:
        exp = st.session_state.expenses.copy()
        exp["Type"] = "Expense"
        exp = exp.rename(columns={"Vendor": "Party"})
        inc
