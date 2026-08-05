import streamlit as st
import pandas as pd
from datetime import datetime
import os

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
    "Date", "Period", "User", "Category", "Amount",
    "Vendor", "Description", "Remark", "Source"
]

if "expenses" not in st.session_state:
    if os.path.exists(USER_FILE):
        st.session_state.expenses = pd.read_csv(USER_FILE)
        # Ensure all required columns exist (for older files)
        for col in COLUMNS:
            if col not in st.session_state.expenses.columns:
                if col == "User":
                    st.session_state.expenses[col] = USER
                elif col == "Period":
                    st.session_state.expenses[col] = ""
                elif col == "Source":
                    st.session_state.expenses[col] = "Manual"
                else:
                    st.session_state.expenses[col] = ""
        st.session_state.expenses = st.session_state.expenses[COLUMNS]
        # Force Amount to numeric
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

current_period = datetime.now().strftime("%Y-%m")

# ======================
# Sidebar - Add Expense
# ======================
st.sidebar.header("➕ Add New Expense")
with st.sidebar.form("expense_form", clear_on_submit=True):
    date = st.date_input("Date", value=datetime.now())
    period = st.text_input("Period", value=current_period, help="e.g. 2026-08 or Q3-2026")
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
                "Period": period.strip() if period else current_period,
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
            st.success(f"Added: {category} - ${amount:.2f}")

# ======================
# Sidebar - Import CSV
# ======================
st.sidebar.divider()
st.sidebar.header("📥 Import Expenses")
uploaded_file = st.sidebar.file_uploader(
    "Upload CSV file",
    type=["csv"],
    help="Preferred columns: Date, Period, User, Category, Amount, Vendor, Description, Remark, Source"
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
                "Period": current_period,
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
            
            for col in ["Date", "Period", "User", "Category", "Vendor", "Description", "Remark", "Source"]:
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
# Main Area
# ======================
st.title("💰 Expense Tracker")
st.markdown(f"Welcome, **{USER}**! Record and manage your daily expenses easily.")

# Summary
if not st.session_state.expenses.empty:
    total = st.session_state.expenses["Amount"].sum()
    st.metric("Total Spent", f"${total:,.2f}")
    
    by_category = (
        st.session_state.expenses
        .groupby("Category")["Amount"]
        .sum()
        .sort_values(ascending=False)
    )
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Spending by Category")
        st.dataframe(
            by_category.reset_index().rename(columns={"Amount": "Total ($)"}),
            use_container_width=True,
            hide_index=True
        )
    with col2:
        st.subheader("Category Chart")
        st.bar_chart(by_category)
else:
    st.info("No expenses recorded yet. Add your first expense from the sidebar!")

st.divider()

# ======================
# All Expenses + Deletion
# ======================
st.subheader("All Expenses")

if not st.session_state.expenses.empty:
    # Prepare dataframe with Select checkbox
    display_df = st.session_state.expenses.copy()
    display_df.insert(0, "Select", False)

    edited_df = st.data_editor(
        display_df,
        hide_index=True,
        use_container_width=True,
        disabled=[col for col in display_df.columns if col != "Select"],
        key="expense_editor"
    )

    st.markdown("### Delete Options")

    col_del1, col_del2, col_del3 = st.columns([2, 2, 2])

    with col_del1:
        if st.button("🗑️ Delete Selected Rows", type="primary", use_container_width=True):
            selected_indices = edited_df[edited_df["Select"]].index.tolist()
            if not selected_indices:
                st.warning("No rows selected.")
            else:
                st.session_state.expenses = (
                    st.session_state.expenses
                    .drop(selected_indices)
                    .reset_index(drop=True)
                )
                save_data()
                st.success(f"Deleted {len(selected_indices)} expense(s).")
                st.rerun()

    with col_del2:
        # Two-step Delete All
        if "confirm_delete_all" not in st.session_state:
            st.session_state.confirm_delete_all = False

        if not st.session_state.confirm_delete_all:
            if st.button("🧹 Delete All Expenses", type="secondary", use_container_width=True):
                st.session_state.confirm_delete_all = True
                st.rerun()
        else:
            st.warning("⚠️ Are you sure you want to delete ALL expenses?")
            c1, c2 = st.columns(2)
            with c1:
                if st.button("✅ Yes, Delete All", type="primary", use_container_width=True):
                    st.session_state.expenses = pd.DataFrame(columns=COLUMNS)
                    save_data()
                    st.session_state.confirm_delete_all = False
                    st.success("All expenses have been deleted.")
                    st.rerun()
            with c2:
                if st.button("❌ Cancel", use_container_width=True):
                    st.session_state.confirm_delete_all = False
                    st.rerun()

    with col_del3:
        csv = st.session_state.expenses.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="⬇️ Download CSV",
            data=csv,
            file_name=f"{USER}_expenses_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            use_container_width=True
        )

else:
    st.write("No data to display.")

# Footer
st.markdown("---")
st.caption("Free to use and share")
