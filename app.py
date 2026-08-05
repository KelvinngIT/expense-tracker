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

    years = sorted(st.session_state.expenses["Year"].dropna().unique())
    selected_year = st.sidebar.selectbox("Year", options=["All"] + years)

    months = sorted(st.session_state.expenses["Month"].dropna().unique())
    month_names = {i: datetime(2000, i, 1).strftime("%B") for i in months}
    month_options = ["All"] + [month_names[m] for m in months]
    selected_month = st.sidebar.selectbox("Month", options=month_options)

    filtered_df = st.session_state.expenses.copy()
    if selected_year != "All":
        filtered_df = filtered_df[filtered_df["Year"] == selected_year]
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
# All Expenses + Deletion + Download
# ======================
st.subheader("All Expenses (Filtered)")

if not filtered_df.empty:
    display_df = filtered_df.copy()
    display_df.insert(0, "Select", False)
    display_df["Amount"] = display_df["Amount"].map(lambda x: f"{float(x):,.2f}")

    edited_df = st.data_editor(
        display_df,
        hide_index=True,
        use_container_width=True,
        disabled=[col for col in display_df.columns if col != "Select"],
        key="expense_editor"
    )

    st.markdown("### Delete / Download Options")
    col_del1, col_del2, col_del3 = st.columns([2, 2, 2])

    # Delete selected rows
    with col_del1:
        if st.button("🗑️ Delete Selected Rows", type="primary", use_container_width=True):
            selected_indices = edited_df[edited_df["Select"]].index.tolist()
            if not selected_indices:
                st.warning("No rows selected.")
            else:
                st.session_state.expenses = (
                    st.session_state.expenses.drop(selected_indices).reset_index(drop=True)
                )
                save_data()
                st.success(f"Deleted {len(selected_indices)} expense(s).")
                st.rerun()

    # Delete all rows (two-step confirmation)
    with col_del2:
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

    # Download CSV
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
    st.write("No data to display for the selected filters.")
