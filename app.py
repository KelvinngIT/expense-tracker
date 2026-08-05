import streamlit as st
import pandas as pd
from datetime import datetime
import os
import calendar

# Page config
st.set_page_config(
    page_title="Expense Tracker",
    page_icon="💰",
    layout="wide"
)

# ======================
# User Identification
# ======================
USER = st.sidebar.text_input("Enter your username", value="guest")
DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)
USER_FILE = os.path.join(DATA_DIR, f"{USER}_expenses.csv")

# ======================
# Load or Initialize Data
# ======================
COLUMNS = [
    "Date", "User", "Category", "Amount",
    "Vendor", "Description", "Remark", "Source"
]

if "expenses" not in st.session_state:
    if os.path.exists(USER_FILE):
        st.session_state.expenses = pd.read_csv(USER_FILE)
        for col in COLUMNS:
            if col not in st.session_state.expenses.columns:
                st.session_state.expenses[col] = ""
        st.session_state.expenses = st.session_state.expenses[COLUMNS]
        st.session_state.expenses["Amount"] = pd.to_numeric(
            st.session_state.expenses["Amount"], errors="coerce"
        ).fillna(0.0)
    else:
        st.session_state.expenses = pd.DataFrame(columns=COLUMNS)

def save_data():
    st.session_state.expenses.to_csv(USER_FILE, index=False)

CATEGORIES = [
    "Food & Dining", "Transportation", "Shopping", "Bills & Utilities",
    "Entertainment", "Health", "Education", "Travel",
    "Type", "Family Support", "Assets", "Other"
]

SOURCES = ["Manual", "Bank", "Credit Card", "Cash", "Import", "Other"]

# ======================
# Sidebar - Add Expense
# ======================
st.sidebar.header("➕ Add New Expense")

with st.sidebar.form("expense_form", clear_on_submit=True):
    date = st.date_input("Date", value=datetime.now())
    category = st.selectbox("Category", CATEGORIES)
    amount = st.number_input("Amount ($)", min_value=0.0, step=0.01, format="%.2f")
    vendor = st.text_input("Vendor", placeholder="e.g. Starbucks, Uber, Amazon...")
    description = st.text_input("Description", placeholder="e.g. Lunch, Monthly subscription...")
    remark = st.text_input("Remark", placeholder="Optional notes...")
    source = st.selectbox("Source", SOURCES, index=0)
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
                "Source": source
            }
            st.session_state.expenses = pd.concat(
                [st.session_state.expenses, pd.DataFrame([new_row])],
                ignore_index=True
            )
            save_data()
            st.success(f"Added: {category} - ${amount:,.2f}")

# ======================
# Sidebar - Upload CSV
# ======================
st.sidebar.markdown("---")
st.sidebar.header("📥 Upload Expenses")

uploaded_file = st.sidebar.file_uploader(
    "Upload CSV file",
    type=["csv"],
    help="Preferred columns: Date, User, Category, Amount, Vendor, Description, Remark, Source"
)

if uploaded_file is not None:
    try:
        import_df = pd.read_csv(uploaded_file)
        import_df.columns = import_df.columns.str.strip().str.title()

        min_required = {"Date", "Category", "Amount"}
        if not min_required.issubset(set(import_df.columns)):
            st.sidebar.error(
                f"Missing columns. At least required: {', '.join(min_required)}\n"
                f"Found: {', '.join(import_df.columns)}"
            )
        else:
            defaults = {
                "User": USER,
                "Vendor": "-",
                "Description": "-",
                "Remark": "-",
                "Source": "Import"
            }
            for col, default in defaults.items():
                if col not in import_df.columns:
                    import_df[col] = default

            import_df = import_df[COLUMNS].copy()
            import_df["Amount"] = pd.to_numeric(import_df["Amount"], errors="coerce")
            import_df = import_df.dropna(subset=["Amount"])
            import_df["Amount"] = import_df["Amount"].astype(float)

            for col in COLUMNS:
                import_df[col] = import_df[col].fillna(defaults.get(col, "-")).astype(str)

            if st.sidebar.button("Import Data", use_container_width=True, type="primary"):
                before = len(st.session_state.expenses)
                st.session_state.expenses = pd.concat(
                    [st.session_state.expenses, import_df],
                    ignore_index=True
                )
                save_data()
                added = len(st.session_state.expenses) - before
                st.sidebar.success(f"Successfully imported {added} expenses!")
                st.rerun()
    except Exception as e:
        st.sidebar.error(f"Error reading file: {e}")

# ======================
# Sidebar - Filters (Year + Month)
# ======================
st.sidebar.markdown("---")
st.sidebar.header("🔍 Filters")

if not st.session_state.expenses.empty:
    st.session_state.expenses["Date"] = pd.to_datetime(
        st.session_state.expenses["Date"], errors="coerce"
    )
    st.session_state.expenses["Year"] = st.session_state.expenses["Date"].dt.year
    st.session_state.expenses["Month"] = st.session_state.expenses["Date"].dt.month

    years = sorted(
        st.session_state.expenses["Year"].dropna().astype(int).unique()
    )
    selected_year = st.sidebar.selectbox("Year", options=["All"] + list(years))

    months = sorted(
        st.session_state.expenses["Month"].dropna().astype(int).unique()
    )
    month_names = {m: calendar.month_name[m] for m in months}
    month_options = ["All"] + [month_names[m] for m in months]
    selected_month = st.sidebar.selectbox("Month", options=month_options)

    filtered_df = st.session_state.expenses.copy()

    if selected_year != "All":
        filtered_df = filtered_df[filtered_df["Year"] == int(selected_year)]

    if selected_month != "All":
        month_num = [k for k, v in month_names.items() if v == selected_month][0]
        filtered_df = filtered_df[filtered_df["Month"] == month_num]
else:
    filtered_df = st.session_state.expenses.copy()

# ======================
# Main Area
# ======================
st.title("💰 Expense Tracker")
st.markdown(f"Welcome, **{USER}**! Record and manage your daily expenses easily.")

# Summary
if not filtered_df.empty:
    total = filtered_df["Amount"].sum()
    st.metric("Total Spent", f"${total:,.2f}")

    by_category = (
        filtered_df.groupby("Category")["Amount"]
        .sum()
        .sort_values(ascending=False)
    )

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Spending by Category")
        st.dataframe(
            by_category.reset_index()
            .rename(columns={"Amount": "Total ($)"})
            .style.format({"Total ($)": "{:,.2f}"}),
            use_container_width=True,
            hide_index=True
        )
    with col2:
        st.subheader("Category Chart")
        st.bar_chart(by_category)
else:
    st.info("No expenses recorded yet. Add your first expense from the sidebar!")

st.markdown("---")

# ======================
# All Expenses + Deletion
# ======================
st.subheader("All Expenses (Filtered)")

if not filtered_df.empty:
    # Keep original index so we can delete correctly from the main DataFrame
    display_df = filtered_df.copy()
    display_df = display_df.reset_index()  # 'index' column = original index in st.session_state.expenses
    display_df.insert(0, "Select", False)

    # Format Amount for display only
    display_df["Amount"] = display_df["Amount"].map(lambda x: f"{float(x):,.2f}")

    edited_df = st.data_editor(
        display_df,
        hide_index=True,
        use_container_width=True,
        disabled=[col for col in display_df.columns if col != "Select"],
        key="expense_editor",
        column_config={
            "Select": st.column_config.CheckboxColumn(required=True),
            "index": None,          # hide the original index column
        }
    )

    # ---------- Delete Selected ----------
    selected_rows = edited_df[edited_df["Select"] == True]

    col_del1, col_del2, _ = st.columns([1, 1, 3])

    with col_del1:
        if st.button("🗑️ Delete Selected", type="primary", use_container_width=True):
            if selected_rows.empty:
                st.warning("Please select at least one expense to delete.")
            else:
                indices_to_drop = selected_rows["index"].tolist()
                st.session_state.expenses = st.session_state.expenses.drop(indices_to_drop)
                st.session_state.expenses = st.session_state.expenses.reset_index(drop=True)
                save_data()
                st.success(f"Deleted {len(indices_to_drop)} expense(s).")
                st.rerun()

    # ---------- Delete All ----------
    with col_del2:
        if st.button("💥 Delete All", type="secondary", use_container_width=True):
            st.session_state.confirm_delete_all = True

    if st.session_state.get("confirm_delete_all", False):
        st.warning("⚠️ Are you sure you want to delete **ALL** expenses? This cannot be undone.")
        c1, c2, _ = st.columns([1, 1, 3])
        with c1:
            if st.button("✅ Yes, Delete Everything", type="primary"):
                st.session_state.expenses = pd.DataFrame(columns=COLUMNS)
                save_data()
                st.session_state.confirm_delete_all = False
                st.success("All expenses have been deleted.")
                st.rerun()
        with c2:
            if st.button("❌ Cancel"):
                st.session_state.confirm_delete_all = False
                st.rerun()

else:
    st.info("No expenses to display.")
