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
    for col in text_cols:
        if col in df.columns:
            s = df[col].astype(str)
            if s.str.contains(r"�|\?\?\?", regex=True, na=False).any():
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
        "currency": "Currency", "curr": "Currency", "ccy": "Currency",
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
    rename = {col: alias_map.get(col, col.replace("_", " ").title()) for col in df.columns}
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
    "Date", "User", "Category", "Amount", "Currency",
    "Vendor", "Description", "Remark", "Source"
]

INCOME_COLUMNS = [
    "Date", "User", "Category", "Amount", "Currency",
    "Customer", "Description", "Remark", "Source"
]

CURRENCIES = ["HKD", "RMB", "JPY", "USD", "EUR"]

# ---- Expenses ----
if "expenses" not in st.session_state:
    if os.path.exists(USER_FILE):
        try:
            st.session_state.expenses = read_csv_chinese_safe(USER_FILE)
            for col in COLUMNS:
                if col not in st.session_state.expenses.columns:
                    st.session_state.expenses[col] = "HKD" if col == "Currency" else ""
            st.session_state.expenses = st.session_state.expenses[COLUMNS]
        except Exception:
            st.session_state.expenses = pd.DataFrame(columns=COLUMNS)
    else:
        st.session_state.expenses = pd.DataFrame(columns=COLUMNS)

st.session_state.expenses["Amount"] = clean_amount(st.session_state.expenses["Amount"])
if "Currency" in st.session_state.expenses.columns:
    st.session_state.expenses["Currency"] = st.session_state.expenses["Currency"].fillna("HKD").astype(str)
else:
    st.session_state.expenses["Currency"] = "HKD"

def save_data():
    st.session_state.expenses.to_csv(USER_FILE, index=False, encoding="utf-8-sig")

# ---- Income ----
if "income" not in st.session_state:
    if os.path.exists(INCOME_FILE):
        try:
            st.session_state.income = read_csv_chinese_safe(INCOME_FILE)
            for col in INCOME_COLUMNS:
                if col not in st.session_state.income.columns:
                    st.session_state.income[col] = "HKD" if col == "Currency" else ""
            st.session_state.income = st.session_state.income[INCOME_COLUMNS]
        except Exception:
            st.session_state.income = pd.DataFrame(columns=INCOME_COLUMNS)
    else:
        st.session_state.income = pd.DataFrame(columns=INCOME_COLUMNS)

st.session_state.income["Amount"] = clean_amount(st.session_state.income["Amount"])
if "Currency" in st.session_state.income.columns:
    st.session_state.income["Currency"] = st.session_state.income["Currency"].fillna("HKD").astype(str)
else:
    st.session_state.income["Currency"] = "HKD"

def save_income():
    st.session_state.income.to_csv(INCOME_FILE, index=False, encoding="utf-8-sig")

# Warn about already-corrupted Chinese
if (has_corrupted_chinese(st.session_state.expenses, ["Vendor", "Description", "Remark"]) or
    has_corrupted_chinese(st.session_state.income, ["Customer", "Description", "Remark"])):
    st.error(
        "⚠️ Your saved data already contains corrupted Chinese text (????).\n\n"
        "Please delete the files inside the `data` folder and re-enter the Chinese text. "
        "New entries will work correctly."
    )

# ======================
# Categories
# ======================
CATEGORIES = [
    "Food & Dining", "Transportation", "Shopping", "Bills & Utilities",
    "Entertainment", "Health", "Education", "Travel",
    "Type", "Family Support", "Health care", "Red pocket", "Assets", "Finance",
    "Property", "Transfer", "Other",
]

INCOME_CATEGORIES = [
    "Salary", "Freelance", "Business", "Investment",
    "Gift", "Refund", "Rental", "Other", "Stock"
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
    amount = st.number_input("Amount", min_value=0.0, step=0.01, format="%.2f", key="exp_amt")
    currency = st.selectbox("Currency", CURRENCIES, index=0, key="exp_currency")
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
                "Currency": currency,
                "Vendor": vendor.strip() if vendor else "-",
                "Description": description.strip() if description else "-",
                "Remark": remark.strip() if remark else "-",
                "Source": source,
            }
            st.session_state.expenses = pd.concat(
                [st.session_state.expenses, pd.DataFrame([new_row])], ignore_index=True
            )
            save_data()
            st.success(f"Added: {category} - {currency} {amount:,.2f}")
            st.rerun()

# ======================
# Sidebar - Add Income
# ======================
st.sidebar.markdown("---")
st.sidebar.header("💵 Add New Income")

with st.sidebar.form("income_form", clear_on_submit=True):
    inc_date = st.date_input("Date", value=datetime.now(), key="inc_date")
    inc_category = st.selectbox("Category", INCOME_CATEGORIES, key="inc_cat")
    inc_amount = st.number_input("Amount", min_value=0.0, step=0.01, format="%.2f", key="inc_amt")
    inc_currency = st.selectbox("Currency", CURRENCIES, index=0, key="inc_currency")
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
                "Currency": inc_currency,
                "Customer": inc_customer.strip() if inc_customer else "-",
                "Description": inc_description.strip() if inc_description else "-",
                "Remark": inc_remark.strip() if inc_remark else "-",
                "Source": inc_source,
            }
            st.session_state.income = pd.concat(
                [st.session_state.income, pd.DataFrame([new_inc])], ignore_index=True
            )
            save_income()
            st.success(f"Income added: {inc_category} - {inc_currency} {inc_amount:,.2f}")
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
            defaults = {
                "User": USER,
                "Currency": "HKD",
                "Vendor": "-",
                "Description": "-",
                "Remark": "-",
                "Source": "Import"
            }
            for col, default in defaults.items():
                if col not in import_df.columns:
                    import_df[col] = default

            for col in COLUMNS:
                if col not in import_df.columns:
                    import_df[col] = defaults.get(col, "-")

            import_df = import_df[COLUMNS].copy()
            import_df["Amount"] = clean_amount(import_df["Amount"])
            import_df = import_df[import_df["Amount"] > 0].copy()

            for col in ["User", "Category", "Currency", "Vendor", "Description", "Remark", "Source", "Date"]:
                import_df[col] = import_df[col].fillna(defaults.get(col, "-")).astype(str).str.strip()
                import_df.loc[import_df[col] == "", col] = defaults.get(col, "-")
                if col == "Vendor":
                    import_df.loc[import_df[col].str.lower().isin(["nan", "none", "null"]), col] = "-"

            st.sidebar.markdown(f"**Preview** ({len(import_df)} rows)")
            st.sidebar.dataframe(
                import_df[["Date", "Category", "Amount", "Currency", "Vendor"]].head(5),
                use_container_width=True, hide_index=True
            )

            if st.sidebar.button("Import Expenses", use_container_width=True, type="primary", key="import_exp"):
                before = len(st.session_state.expenses)
                st.session_state.expenses = pd.concat(
                    [st.session_state.expenses, import_df], ignore_index=True
                )
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
            defaults = {
                "User": USER,
                "Currency": "HKD",
                "Customer": "-",
                "Description": "-",
                "Remark": "-",
                "Source": "Import"
            }
            for col, default in defaults.items():
                if col not in import_inc.columns:
                    import_inc[col] = default

            for col in INCOME_COLUMNS:
                if col not in import_inc.columns:
                    import_inc[col] = defaults.get(col, "-")

            import_inc = import_inc[INCOME_COLUMNS].copy()
            import_inc["Amount"] = clean_amount(import_inc["Amount"])
            import_inc = import_inc[import_inc["Amount"] > 0].copy()

            for col in ["User", "Category", "Currency", "Customer", "Description", "Remark", "Source", "Date"]:
                import_inc[col] = import_inc[col].fillna(defaults.get(col, "-")).astype(str).str.strip()
                import_inc.loc[import_inc[col] == "", col] = defaults.get(col, "-")

            st.sidebar.dataframe(
                import_inc[["Date", "Category", "Amount", "Currency", "Customer"]].head(3),
                use_container_width=True, hide_index=True
            )

            if st.sidebar.button("Import Income", use_container_width=True, type="primary", key="import_inc"):
                before = len(st.session_state.income)
                st.session_state.income = pd.concat(
                    [st.session_state.income, import_inc], ignore_index=True
                )
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

view_mode = st.sidebar.radio(
    "Show", options=["Expenses", "Income", "Both"], index=0, horizontal=True, key="view_mode"
)

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
    st.metric("Total Spent", f"{total_expense:,.2f}")
with col_m2:
    st.metric("Total Income", f"{total_income:,.2f}")
with col_m3:
    st.metric("Net Balance", f"{net:,.2f}", delta="Surplus" if net >= 0 else "Deficit")

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
    has_exp = not st.session_state.expenses.empty
    has_inc = not st.session_state.income.empty
    if has_exp or has_inc:
        frames = []
        if has_exp:
            exp = st.session_state.expenses.copy()
            exp["Type"] = "Expense"
            exp = exp.rename(columns={"Vendor": "Party"})
            frames.append(exp)
        if has_inc:
            inc = st.session_state.income.copy()
            inc["Type"] = "Income"
            inc = inc.rename(columns={"Customer": "Party"})
            frames.append(inc)

        combined = pd.concat(frames, ignore_index=True)

        # Ensure required columns exist (fix for old data)
        if "Currency" not in combined.columns:
            combined["Currency"] = "HKD"
        if "Party" not in combined.columns:
            combined["Party"] = "-"
        if "Description" not in combined.columns:
            combined["Description"] = "-"
        if "Remark" not in combined.columns:
            combined["Remark"] = "-"
        if "Source" not in combined.columns:
            combined["Source"] = "Manual"

        desired_cols = [
            "Date", "Type", "User", "Category", "Amount", "Currency",
            "Party", "Description", "Remark", "Source"
        ]
        existing_cols = [c for c in desired_cols if c in combined.columns]
        combined = combined[existing_cols]

        csv_combined = combined.to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            label="📥 Download Combined CSV",
            data=csv_combined,
            file_name=f"{safe_user}_expenses_and_income.csv",
            mime="text/csv",
            use_container_width=True,
            key="download_combined",
        )
    else:
        st.button("📥 Download Combined CSV", disabled=True, use_container_width=True)

st.markdown("---")

# ======================
# 📊 CUSTOM CHART BUILDER
# ======================
st.subheader("📊 Build Your Own Chart")

with st.expander("Create Custom Chart", expanded=False):
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        chart_source = st.selectbox("Data Source", options=["Expenses", "Income", "Both"], key="custom_source")
    with c2:
        chart_type = st.selectbox("Chart Type", options=["Bar", "Line", "Area"], key="custom_type")
    with c3:
        group_by = st.selectbox("Group By", options=["Category", "Month", "Source", "Vendor / Customer","Currency","Remark"], key="custom_group")
    with c4:
        agg_method = st.selectbox("Aggregation", options=["Sum", "Count", "Average"], key="custom_agg")

    if st.button("🚀 Generate Chart", type="primary", use_container_width=True):
        dfs = []
        if chart_source in ["Expenses", "Both"] and not filtered_expenses.empty:
            exp = filtered_expenses.copy()
            exp["Type"] = "Expense"
            exp = exp.rename(columns={"Vendor": "Party"})
            dfs.append(exp)
        if chart_source in ["Income", "Both"] and not filtered_income.empty:
            inc = filtered_income.copy()
            inc["Type"] = "Income"
            inc = inc.rename(columns={"Customer": "Party"})
            dfs.append(inc)

        if not dfs:
            st.warning("No data available for the selected source and filters.")
        else:
            combined = pd.concat(dfs, ignore_index=True)
            combined["Amount"] = clean_amount(combined["Amount"])
            combined["Date"] = pd.to_datetime(combined["Date"], errors="coerce")
            combined = combined.dropna(subset=["Date"])

            if group_by == "Category":
                combined["Group"] = combined["Category"].astype(str)
            elif group_by == "Month":
                combined["Group"] = combined["Date"].dt.to_period("M").astype(str)
            elif group_by == "Source":
                combined["Group"] = combined["Source"].astype(str)
            elif group_by == "Remark":
                combined["Group"] = combined["Remark"].astype(str)
            elif group_by == "Currency":
                combined["Group"] = combined["Currency"].astype(str)
            else:  # Vendor / Customer
                combined["Group"] = combined["Party"].astype(str)

            if agg_method == "Sum":
                chart_data = combined.groupby("Group")["Amount"].sum().sort_values(ascending=False)
                ylabel = "Total Amount"
            elif agg_method == "Count":
                chart_data = combined.groupby("Group").size().sort_values(ascending=False)
                ylabel = "Number of Records"
            else:
                chart_data = combined.groupby("Group")["Amount"].mean().sort_values(ascending=False)
                ylabel = "Average Amount"

            if chart_data.empty:
                st.warning("No data after grouping.")
            else:
                st.markdown(f"**{chart_type} Chart** — {chart_source} grouped by **{group_by}** ({agg_method})")
                if chart_type == "Bar":
                    st.bar_chart(chart_data, use_container_width=True)
                elif chart_type == "Line":
                    st.line_chart(chart_data, use_container_width=True)
                else:
                    st.area_chart(chart_data, use_container_width=True)

                with st.expander("View Chart Data"):
                    table = chart_data.reset_index()
                    table.columns = [group_by, ylabel]
                    if agg_method != "Count":
                        table[ylabel] = table[ylabel].map(lambda x: f"{x:,.2f}")
                    st.dataframe(table, use_container_width=True, hide_index=True)

st.markdown("---")

# ======================
# EXPENSES SECTION
# ======================
if view_mode in ["Expenses", "Both"]:
    st.subheader("📉 Expenses")

    if not filtered_expenses.empty:
        by_category = filtered_expenses.groupby("Category")["Amount"].sum().sort_values(ascending=False)
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Spending by Category**")
            st.dataframe(
                by_category.reset_index().rename(columns={"Amount": "Total"}).style.format({"Total": "{:,.2f}"}),
                use_container_width=True, hide_index=True,
            )
        with col2:
            st.markdown("**Category Chart**")
            st.bar_chart(by_category)
    else:
        st.info("No expenses for the selected filters.")

    st.markdown("### 📅 Monthly Expense Charts (by Category)")
    if not st.session_state.expenses.empty:
        chart_df = st.session_state.expenses.copy()
        chart_df["Amount"] = clean_amount(chart_df["Amount"])
        chart_df["Date"] = pd.to_datetime(chart_df["Date"], errors="coerce")
        chart_df = chart_df.dropna(subset=["Date"])
        if selected_year != "All":
            chart_df = chart_df[chart_df["Date"].dt.year == int(selected_year)]
        if not chart_df.empty:
            chart_df["YearMonth"] = chart_df["Date"].dt.to_period("M").astype(str)
            monthly_by_cat = (
                chart_df.groupby(["YearMonth", "Category"])["Amount"]
                .sum().unstack(fill_value=0).sort_index()
            )
            monthly_by_cat = monthly_by_cat.loc[:, (monthly_by_cat != 0).any(axis=0)]
            st.caption("Each color = one expense category")
            st.bar_chart(monthly_by_cat, use_container_width=True)
            with st.expander("View monthly totals by category"):
                display_tbl = monthly_by_cat.copy()
                display_tbl["Total"] = display_tbl.sum(axis=1)
                st.dataframe(display_tbl.style.format("{:,.2f}"), use_container_width=True)
        else:
            st.info("No expense data for charts.")
    else:
        st.info("Add some expenses to see monthly charts.")

    st.markdown("---")
    st.subheader("All Expenses (Filtered)")

    display_df = filtered_expenses.copy().reset_index(drop=True)
    if "Date" in display_df.columns:
        display_df["Date"] = (
            pd.to_datetime(display_df["Date"], errors="coerce")
            .dt.strftime("%Y-%m-%d").fillna("")
        )
    display_df["Amount"] = clean_amount(display_df["Amount"])
    for col in ["User", "Category", "Currency", "Vendor", "Description", "Remark", "Source"]:
        if col in display_df.columns:
            display_df[col] = display_df[col].fillna("").astype(str)

    display_df.insert(0, "No.", range(1, len(display_df) + 1))
    display_df.insert(1, "Select", False)

    edited_df = st.data_editor(
        display_df,
        num_rows="dynamic",
        hide_index=True,
        use_container_width=True,
        key="expense_editor",
        column_config={
            "No.": st.column_config.NumberColumn("No.", width="small", disabled=True),
            "Select": st.column_config.CheckboxColumn("Select", default=False),
            "Date": st.column_config.TextColumn("Date"),
            "User": st.column_config.TextColumn("User"),
            "Category": st.column_config.SelectboxColumn("Category", options=CATEGORIES, required=True),
            "Amount": st.column_config.NumberColumn("Amount", min_value=0.0, format="%,.2f", required=True),
            "Currency": st.column_config.SelectboxColumn("Currency", options=CURRENCIES, required=True),
            "Vendor": st.column_config.TextColumn("Vendor"),
            "Description": st.column_config.TextColumn("Description"),
            "Remark": st.column_config.TextColumn("Remark"),
            "Source": st.column_config.SelectboxColumn("Source", options=SOURCES),
        },
    )

    col_save, col_del, col_del_all, _ = st.columns([1, 1, 1, 2])
    with col_save:
        if st.button("💾 Save Changes / Add Rows", type="primary", use_container_width=True, key="save_exp"):
            clean_df = edited_df.drop(columns=["Select", "No."], errors="ignore").copy()
            clean_df["Amount"] = clean_amount(clean_df["Amount"])
            clean_df["User"] = clean_df["User"].fillna(USER).astype(str)
            clean_df["Currency"] = clean_df["Currency"].fillna("HKD").astype(str)
            clean_df["Vendor"] = clean_df["Vendor"].fillna("-").astype(str)
            clean_df["Description"] = clean_df["Description"].fillna("-").astype(str)
            clean_df["Remark"] = clean_df["Remark"].fillna("-").astype(str)
            clean_df["Source"] = clean_df["Source"].fillna("Manual").astype(str)
            clean_df["Category"] = clean_df["Category"].fillna("").astype(str)
            clean_df["Date"] = clean_df["Date"].fillna("").astype(str)
            clean_df = clean_df[(clean_df["Category"].str.strip() != "") & (clean_df["Amount"] > 0)]

            if selected_year == "All" and selected_month == "All":
                st.session_state.expenses = clean_df[COLUMNS].reset_index(drop=True)
                save_data()
                st.success("Changes and new rows saved successfully!")
                st.rerun()
            else:
                st.warning("Please set Year & Month to **All** before saving.")

    with col_del:
        if st.button("🗑️ Delete Selected", use_container_width=True, key="del_exp"):
            selected_mask = edited_df["Select"] == True
            if not selected_mask.any():
                st.warning("Please select at least one row.")
            else:
                to_delete = edited_df[selected_mask]
                original = st.session_state.expenses.copy()
                for _, row in to_delete.iterrows():
                    mask = (
                        (original["Date"].astype(str).str[:10] == str(row["Date"])[:10])
                        & (original["Category"] == row["Category"])
                        & (original["Amount"] == float(row["Amount"]))
                        & (original["Vendor"].astype(str) == str(row["Vendor"]))
                    )
                    original = original[~mask]
                st.session_state.expenses = original.reset_index(drop=True)
                save_data()
                st.success(f"Deleted {selected_mask.sum()} expense(s).")
                st.rerun()

    with col_del_all:
        if st.button("💥 Delete All Expenses", use_container_width=True, key="del_all_exp"):
            st.session_state.confirm_delete_all_exp = True

    if st.session_state.get("confirm_delete_all_exp", False):
        st.warning("⚠️ Are you sure you want to delete **ALL** expenses?")
        c1, c2, _ = st.columns([1, 1, 3])
        with c1:
            if st.button("✅ Yes, Delete Everything", type="primary", key="confirm_del_exp"):
                st.session_state.expenses = pd.DataFrame(columns=COLUMNS)
                save_data()
                st.session_state.confirm_delete_all_exp = False
                st.success("All expenses deleted.")
                st.rerun()
        with c2:
            if st.button("❌ Cancel", key="cancel_del_exp"):
                st.session_state.confirm_delete_all_exp = False
                st.rerun()

# ======================
# INCOME SECTION
# ======================
if view_mode in ["Income", "Both"]:
    st.markdown("---")
    st.subheader("📈 Income")

    if not filtered_income.empty:
        by_inc_cat = filtered_income.groupby("Category")["Amount"].sum().sort_values(ascending=False)
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Income by Category**")
            st.dataframe(
                by_inc_cat.reset_index().rename(columns={"Amount": "Total"}).style.format({"Total": "{:,.2f}"}),
                use_container_width=True, hide_index=True,
            )
        with col2:
            st.markdown("**Income Category Chart**")
            st.bar_chart(by_inc_cat)
    else:
        st.info("No income records for the selected filters.")

    st.markdown("### 📅 Monthly Income Charts (by Category)")
    if not st.session_state.income.empty:
        inc_chart = st.session_state.income.copy()
        inc_chart["Amount"] = clean_amount(inc_chart["Amount"])
        inc_chart["Date"] = pd.to_datetime(inc_chart["Date"], errors="coerce")
        inc_chart = inc_chart.dropna(subset=["Date"])
        if selected_year != "All":
            inc_chart = inc_chart[inc_chart["Date"].dt.year == int(selected_year)]
        if not inc_chart.empty:
            inc_chart["YearMonth"] = inc_chart["Date"].dt.to_period("M").astype(str)
            monthly_inc_by_cat = (
                inc_chart.groupby(["YearMonth", "Category"])["Amount"]
                .sum().unstack(fill_value=0).sort_index()
            )
            monthly_inc_by_cat = monthly_inc_by_cat.loc[:, (monthly_inc_by_cat != 0).any(axis=0)]
            st.caption("Each color = one income category")
            st.bar_chart(monthly_inc_by_cat, use_container_width=True)
            with st.expander("View monthly income by category"):
                display_tbl = monthly_inc_by_cat.copy()
                display_tbl["Total"] = display_tbl.sum(axis=1)
                st.dataframe(display_tbl.style.format("{:,.2f}"), use_container_width=True)
        else:
            st.info("No income data for charts.")
    else:
        st.info("Add some income to see monthly charts.")

    st.markdown("---")
    st.subheader("All Income (Filtered)")

    display_inc = filtered_income.copy().reset_index(drop=True)
    if "Date" in display_inc.columns:
        display_inc["Date"] = (
            pd.to_datetime(display_inc["Date"], errors="coerce")
            .dt.strftime("%Y-%m-%d").fillna("")
        )
    display_inc["Amount"] = clean_amount(display_inc["Amount"])
    for col in ["User", "Category", "Currency", "Customer", "Description", "Remark", "Source"]:
        if col in display_inc.columns:
            display_inc[col] = display_inc[col].fillna("").astype(str)

    display_inc.insert(0, "No.", range(1, len(display_inc) + 1))
    display_inc.insert(1, "Select", False)

    edited_inc = st.data_editor(
        display_inc,
        num_rows="dynamic",
        hide_index=True,
        use_container_width=True,
        key="income_editor",
        column_config={
            "No.": st.column_config.NumberColumn("No.", width="small", disabled=True),
            "Select": st.column_config.CheckboxColumn("Select", default=False),
            "Date": st.column_config.TextColumn("Date"),
            "User": st.column_config.TextColumn("User"),
            "Category": st.column_config.SelectboxColumn("Category", options=INCOME_CATEGORIES, required=True),
            "Amount": st.column_config.NumberColumn("Amount", min_value=0.0, format="%,.2f", required=True),
            "Currency": st.column_config.SelectboxColumn("Currency", options=CURRENCIES, required=True),
            "Customer": st.column_config.TextColumn("Customer"),
            "Description": st.column_config.TextColumn("Description"),
            "Remark": st.column_config.TextColumn("Remark"),
            "Source": st.column_config.SelectboxColumn("Source", options=SOURCES),
        },
    )

    col_save_i, col_del_i, col_del_all_i, _ = st.columns([1, 1, 1, 2])
    with col_save_i:
        if st.button("💾 Save Income Changes", type="primary", use_container_width=True, key="save_inc"):
            clean_inc = edited_inc.drop(columns=["Select", "No."], errors="ignore").copy()
            clean_inc["Amount"] = clean_amount(clean_inc["Amount"])
            clean_inc["User"] = clean_inc["User"].fillna(USER).astype(str)
            clean_inc["Currency"] = clean_inc["Currency"].fillna("HKD").astype(str)
            clean_inc["Customer"] = clean_inc["Customer"].fillna("-").astype(str)
            clean_inc["Description"] = clean_inc["Description"].fillna("-").astype(str)
            clean_inc["Remark"] = clean_inc["Remark"].fillna("-").astype(str)
            clean_inc["Source"] = clean_inc["Source"].fillna("Manual").astype(str)
            clean_inc["Category"] = clean_inc["Category"].fillna("").astype(str)
            clean_inc["Date"] = clean_inc["Date"].fillna("").astype(str)
            clean_inc = clean_inc[(clean_inc["Category"].str.strip() != "") & (clean_inc["Amount"] > 0)]

            if selected_year == "All" and selected_month == "All":
                st.session_state.income = clean_inc[INCOME_COLUMNS].reset_index(drop=True)
                save_income()
                st.success("Income changes saved!")
                st.rerun()
            else:
                st.warning("Please set Year & Month to **All** before saving.")

    with col_del_i:
        if st.button("🗑️ Delete Selected Income", use_container_width=True, key="del_inc"):
            selected_mask = edited_inc["Select"] == True
            if not selected_mask.any():
                st.warning("Please select at least one row.")
            else:
                to_delete = edited_inc[selected_mask]
                original = st.session_state.income.copy()
                for _, row in to_delete.iterrows():
                    mask = (
                        (original["Date"].astype(str).str[:10] == str(row["Date"])[:10])
                        & (original["Category"] == row["Category"])
                        & (original["Amount"] == float(row["Amount"]))
                        & (original["Customer"].astype(str) == str(row["Customer"]))
                    )
                    original = original[~mask]
                st.session_state.income = original.reset_index(drop=True)
                save_income()
                st.success(f"Deleted {selected_mask.sum()} income record(s).")
                st.rerun()

    with col_del_all_i:
        if st.button("💥 Delete All Income", use_container_width=True, key="del_all_inc"):
            st.session_state.confirm_delete_all_inc = True

    if st.session_state.get("confirm_delete_all_inc", False):
        st.warning("⚠️ Are you sure you want to delete **ALL** income records?")
        c1, c2, _ = st.columns([1, 1, 3])
        with c1:
            if st.button("✅ Yes, Delete All Income", type="primary", key="confirm_del_inc"):
                st.session_state.income = pd.DataFrame(columns=INCOME_COLUMNS)
                save_income()
                st.session_state.confirm_delete_all_inc = False
                st.success("All income records deleted.")
                st.rerun()
        with c2:
            if st.button("❌ Cancel", key="cancel_del_inc"):
                st.session_state.confirm_delete_all_inc = False
                st.rerun()
