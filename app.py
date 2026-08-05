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
COLUMNS = ["Date", "Period", "User", "Category", "Amount", "Description"]

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
                else:
                    st.session_state.expenses[col] = ""
        st.session_state.expenses = st.session_state.expenses[COLUMNS]
    else:
        st.session_state.expenses = pd.DataFrame(columns=COLUMNS)

def save_data():
    st.session_state.expenses.to_csv(USER_FILE, index=False)

CATEGORIES = [
    "Food & Dining", "Transportation", "Shopping", "Bills & Utilities",
    "Entertainment", "Health", "Education", "Travel",
    "Type", "Family Support", "Assets", "Other"
]

# Helper: current period (YYYY-MM)
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
    description = st.text_input("Description", placeholder="e.g. Lunch, Uber...")
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
    help="Preferred columns: Date, Period, User, Category, Amount, Description"
)

if uploaded_file is not None:
    try:
        import_df = pd.read_csv(uploaded_file)
        # Normalize column names
        import_df.columns = import_df.columns.str.strip().str.title()
        
        # Required minimum columns
        min_required = {"Date", "Category", "Amount", "Description"}
        if not min_required.issubset(set(import_df.columns)):
            st.sidebar.error(
                f"Missing columns. At least required: {', '.join(min_required)}\n"
                f"Found: {', '.join(import_df.columns)}"
            )
        else:
            # Add missing optional columns with defaults
            if "Period" not in import_df.columns:
                import_df["Period"] = current_period
            if "User" not in import_df.columns:
                import_df["User"] = USER
            
            # Keep only the standard columns and clean
            import_df = import_df[COLUMNS].copy()
            import_df["Amount"] = pd.to_numeric(import_df["Amount"], errors="coerce")
            import_df = import_df.dropna(subset=["Amount"])
            import_df["Amount"] = import_df["Amount"].astype(float)
            import_df["Description"] = import_df["Description"].fillna("-").astype(str)
            import_df["Date"] = import_df["Date"].astype(str)
            import_df["Period"] = import_df["Period"].fillna(current_period).astype(str)
            import_df["User"] = import_df["User"].fillna(USER).astype(str)
            
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
    
