import streamlit as st
import pandas as pd
from datetime import datetime
import os
import calendar
import re

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
# Helper: Clean Amount (handles commas, currency symbols, etc.)
# ======================
def clean_amount(series):
    """Convert Amount column safely, even if it contains commas or $ signs."""
    if series is None or len(series) == 0:
        return series

    # Convert to string first
    s = series.astype(str)

    # Remove currency symbols, spaces, and thousand separators
    s = s.str.replace(r"[$,€£¥\s]", "", regex=True)

    # Keep only numbers, decimal point and minus
    s = s.str.replace(r"[^0-9.\-]", "", regex=True)

    # Convert to numeric
    return pd.to_numeric(s, errors="coerce").fillna(0.0)

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
    else:
        st.session_state.expenses = pd.DataFrame(columns=COLUMNS)

# Always clean Amount
st.session_state.expenses["Amount"] = clean_amount(st.session_state.expenses["Amount"])

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
            st.rerun()

# ======================
# Sidebar - Upload CSV
# ======================
st.sidebar.markdown("---")
st.sidebar.header("📥 Upload Expenses")

uploaded_file = st.sidebar.file_uploader(
    "Upload CSV file",
    type=["csv"],
    help="Preferred columns: Date, Category, Amount (others optional)"
)

if uploaded_file is not None:
    try:
        import_df = pd.read_csv(uploaded_file)
        import_df.columns = import_df.columns.str.strip().str.title()

        min_required = {"Date", "Category", "Amount"}
        if not min_required.issubset(set(import_df.columns)):
            st.sidebar.error(
                f"Missing required columns.\n"
                f"Need at least: Date, Category, Amount\n"
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

            import_df = import_df[[c for c in COLUMNS if c in import_df.columns]].copy()

            # ★★★ Clean Amount properly (handles 1,234.56) ★★★
            import_df["Amount"] = clean_amount(import_df["Amount"])
            import_df = import_df[import_df["Amount"] > 0]   # remove zero/invalid

            for col in COLUMNS:
                if col not in import_df.columns:
                    import_df[col] = defaults.get(col, "-")
                else:
                    import_df[col] = import_df[col].fillna(defaults.get(col, "-")).astype(str)

            import_df = import_df[COLUMNS]

            if st.sidebar.button("Import Data", use_container_width=True, type="primary"):
                before = len(st.session_state.expenses)
                st.session_state.expenses = pd.concat(
                    [st.session_state.expenses, import_df],
                    ignore_index=True
                )
                st.session_state.expenses["Amount"] = clean_amount(st.session_state.expenses["Amount"])
                save_data()
                added = len(st.session_state.expenses) - before
                st.sidebar.success(f"Successfully imported {added} expenses!")
                st.rerun()
    except Exception as e:
        st.sidebar.error(f"Error reading file: {e}")

# ======================
# Sidebar - Filters
# ======================
st.sidebar.markdown("---")
st.sidebar.header("🔍 Filters")

if not st.session_state.expenses.empty:
    st.session_state.expenses["Date"] = pd.to_datetime(
        st.session_state.expenses["Date"], errors="coerce"
    )
    st.session_state.expenses["Year"] = st.session_state.expenses["Date"].dt.year
    st.session_state.expenses["Month"] = st.session_state.expenses["Date"].dt.month

    years = sorted(st.session_state.expenses["Year"].dropna().astype(int).unique())
    selected_year = st.sidebar.selectbox("Year", options=["All"] + list(years))

    months = sorted(st.session_state.expenses["Month"].dropna().astype(int).unique())
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
    filtered_df["Amount"] = clean_amount(filtered_df["Amount"])
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
# All Expenses Table
# ======================
st.subheader("All Expenses (Filtered)")

display_df = filtered_df.copy().reset_index(drop=True)

# Convert Date to string
if "Date" in display_df.columns:
    display_df["Date"] = pd.to_datetime(display_df["Date"], errors="coerce").dt.strftime("%Y-%m-%d")
    display_df["Date"] = display_df["Date"].fillna("")

display_df["Amount"] = clean_amount(display_df["Amount"])

for col in ["User", "Category", "Vendor", "Description", "Remark", "Source"]:
    if col in display_df.columns:
        display_df[col] = display_df[col].fillna("").astype(str)

# Add Row Number + Select
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
        "Amount": st.column_config.NumberColumn(
            "Amount ($)",
            min_value=0.0,
            format="%,.2f",          # ← shows 1,234.56 nicely
            required=True
        ),
        "Vendor": st.column_config.TextColumn("Vendor"),
        "Description": st.column_config.TextColumn("Description"),
        "Remark": st.column_config.TextColumn("Remark"),
        "Source": st.column_config.SelectboxColumn("Source", options=SOURCES),
    }
)

# ---------- Buttons ----------
col_save, col_del, col_del_all, _ = st.columns([1, 1, 1, 2])

with col_save:
    if st.button("💾 Save Changes / Add Rows", type="primary", use_container_width=True):
        clean_df = edited_df.drop(columns=["Select", "No."], errors="ignore").copy()
        clean_df["Amount"] = clean_amount(clean_df["Amount"])
        clean_df["User"] = clean_df["User"].fillna(USER).astype(str)
        clean_df["Vendor"] = clean_df["Vendor"].fillna("-").astype(str)
        clean_df["Description"] = clean_df["Description"].fillna("-").astype(str)
        clean_df["Remark"] = clean_df["Remark"].fillna("-").astype(str)
        clean_df["Source"] = clean_df["Source"].fillna("Manual").astype(str)
        clean_df["Category"] = clean_df["Category"].fillna("").astype(str)
        clean_df["Date"] = clean_df["Date"].fillna("").astype(str)

        clean_df = clean_df[
            (clean_df["Category"].str.strip() != "") &
            (clean_df["Amount"] > 0)
        ]

        if selected_year == "All" and selected_month == "All":
            st.session_state.expenses = clean_df[COLUMNS].reset_index(drop=True)
            save_data()
            st.success("Changes and new rows saved successfully!")
            st.rerun()
        else:
            st.warning("Please set Year & Month to **All** before saving.")

with col_del:
    if st.button("🗑️ Delete Selected", use_container_width=True):
        selected_mask = edited_df["Select"] == True
        if not selected_mask.any():
            st.warning("Please select at least one row.")
        else:
            to_delete = edited_df[selected_mask]
            original = st.session_state.expenses.copy()

            for _, row in to_delete.iterrows():
                mask = (
                    (original["Date"].astype(str).str[:10] == str(row["Date"])[:10]) &
                    (original["Category"] == row["Category"]) &
                    (original["Amount"] == float(row["Amount"])) &
                    (original["Vendor"].astype(str) == str(row["Vendor"]))
                )
                original = original[~mask]

            st.session_state.expenses = original.reset_index(drop=True)
            save_data()
            st.success(f"Deleted {selected_mask.sum()} expense(s).")
            st.rerun()

with col_del_all:
    if st.button("💥 Delete All", use_container_width=True):
        st.session_state.confirm_delete_all = True

if st.session_state.get("confirm_delete_all", False):
    st.warning("⚠️ Are you sure you want to delete **ALL** expenses?")
    c1, c2, _ = st.columns([1, 1, 3])
    with c1:
        if st.button("✅ Yes, Delete Everything", type="primary"):
            st.session_state.expenses = pd.DataFrame(columns=COLUMNS)
            save_data()
            st.session_state.confirm_delete_all = False
            st.success("All expenses deleted.")
            st.rerun()
    with c2:
        if st.button("❌ Cancel"):
            st.session_state.confirm_delete_all = False
            st.rerun()
