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

current_period = datetime.now().strftime("%Y-%m")

# ======================
# Sidebar - Filters
# ======================
st.sidebar.divider()
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
# All Expenses
# ======================
st.subheader("All Expenses (Filtered)")

if not filtered_df.empty:
    display_df = filtered_df.copy()
    st.dataframe(display_df, use_container_width=True, hide_index=True)
else:
    st.write("No data to display for the selected filters.")

# Footer
st.markdown("---")
st.caption("Free to use and share")
