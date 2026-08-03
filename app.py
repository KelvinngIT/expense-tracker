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
    "Entertainment", "Health", "Education", "Travel", "Other"
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
# Main Area
# ======================
st.title("💰 Expense Tracker")
st.markdown(f"Welcome, **{USER}**! Record and manage your daily expenses easily.")

# Summary + Table + Delete + Clear + Download (same as before)
# Just add `save_data()` after any modification
