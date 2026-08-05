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
if "expenses" not in st.session_state:
    if os.path.exists(USER_FILE):
        st.session_state.expenses = pd.read_csv(USER_FILE)
    else:
        st.session_state.expenses = pd.DataFrame(
            columns=["Date", "Category", "Amount", "Description"]
        )

def save_data():
    st.session_state.expenses.to_csv(USER_FILE, index=False)

CATEGORIES = [
    "Food & Dining", "Transportation", "Shopping", "Bills & Utilities",
    "Entertainment", "Health", "Education", "Travel",
    "Type", "Family Support", "Assets", "Other"
]

# ======================
# Sidebar - Add Expense
# ======================
st.sidebar.header("➕ Add New Expense")
with st.sidebar.form("expense_form", clear_on_submit=True):
    date = st.date_input("Date", value=datetime.now())
    category = st.selectbox("Category", CATEGORIES)
    amount = st.number_input("Amount ($)", min_value=0.0, step=0.01, format="%.2f")
    description = st.text_input("Description", placeholder="e.g. Lunch, Uber...")
    submitted = st.form_submit_button("Add Expense", use_container_width=True)
    
    if submitted:
        if amount <= 0:
            st.error("Please enter a valid amount (> 0)")
        else:
            new_row = {
                "Date": str(date),
                "Category": category,
                "Amount": float(amount),
                "Description": description.strip() if description else "-"
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
    help="CSV must contain columns: Date, Category, Amount, Description"
)

if uploaded_file is not None:
    try:
        import_df = pd.read_csv(uploaded_file)
        # Normalize column names (case-insensitive + strip spaces)
        import_df.columns = import_df.columns.str.strip().str.title()
        
        required_cols = {"Date", "Category", "Amount", "Description"}
        if not required_cols.issubset(set(import_df.columns)):
            st.sidebar.error(
                f"Missing columns. Required: {', '.join(required_cols)}\n"
                f"Found: {', '.join(import_df.columns)}"
            )
        else:
            # Keep only required columns and clean data
            import_df = import_df[["Date", "Category", "Amount", "Description"]].copy()
            import_df["Amount"] = pd.to_numeric(import_df["Amount"], errors="coerce")
            import_df = import_df.dropna(subset=["Amount"])
            import_df["Amount"] = import_df["Amount"].astype(float)
            import_df["Description"] = import_df["Description"].fillna("-").astype(str)
            import_df["Date"] = import_df["Date"].astype(str)
            
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
    st.metric("Total Spent", f"${total:.2f}")
    
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

# All Expenses Table
st.subheader("All Expenses")
if not st.session_state.expenses.empty:
    display_df = st.session_state.expenses.copy()
    display_df.index.name = "Index"
    st.dataframe(display_df, use_container_width=True)
    
    # Delete section
    st.markdown("### Delete Expense")
    col_a, col_b = st.columns([1, 3])
    with col_a:
        delete_idx = st.number_input(
            "Index to delete",
            min_value=0,
            max_value=len(st.session_state.expenses) - 1,
            step=1
        )
    with col_b:
        if st.button("🗑️ Delete Selected", type="secondary"):
            removed = st.session_state.expenses.iloc[int(delete_idx)]
            st.session_state.expenses = (
                st.session_state.expenses
                .drop(int(delete_idx))
                .reset_index(drop=True)
            )
            save_data()
            st.success(f"Deleted: {removed['Category']} - ${removed['Amount']:.2f}")
            st.rerun()
    
    # Clear all + Download
    col_c, col_d = st.columns(2)
    with col_c:
        if st.button("🧹 Clear All Expenses", type="primary"):
            st.session_state.expenses = pd.DataFrame(
                columns=["Date", "Category", "Amount", "Description"]
            )
            save_data()
            st.success("All expenses cleared!")
            st.rerun()
    with col_d:
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
