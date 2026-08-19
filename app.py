import streamlit as st
import pandas as pd
from datetime import datetime
import os
import calendar
import re
import random
import string

# Page config
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
            send_btn = st.form_submit_button("Send Verification Code", use_container_width=True, type="primary")
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
                verify_btn = st.form_submit_button("Verify & Login", use_container_width=True, type="primary")
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
        st.session_state.expenses = pd.read_csv(USER_FILE)
        for col in COLUMNS:
            if col not in st.session_state.expenses.columns:
                st.session_state.expenses[col] = ""
        st.session_state.expenses = st.session_state.expenses[COLUMNS]
    else:
        st.session_state.expenses = pd.DataFrame(columns=COLUMNS)

st.session_state.expenses["Amount"] = clean_amount(st.session_state.expenses["Amount"])

def save_data():
    st.session_state.expenses.to_csv(USER_FILE, index=False)

# ---- Income ----
if "income" not in st.session_state:
    if os.path.exists(INCOME_FILE):
        st.session_state.income = pd.read_csv(INCOME_FILE)
        for col in INCOME_COLUMNS:
            if col not in st.session_state.income.columns:
                st.session_state.income[col] = ""
        st.session_state.income = st.session_state.income[INCOME_COLUMNS]
    else:
        st.session_state.income = pd.DataFrame(columns=INCOME_COLUMNS)

st.session_state.income["Amount"] = clean_amount(st.session_state.income["Amount"])

def save_income():
    st.session_state.income.to_csv(INCOME_FILE, index=False)

# ======================
# Main Area
# ======================
st.title("💰 Expense Tracker")
st.markdown(f"Welcome, **{USER}**!")

# ===== RED REMINDER =====
st.markdown(
    '<p style="color:red; font-weight:bold; font-size:18px;">⚠️ Do remember to download the file to save your record</p>',
    unsafe_allow_html=True
)

# Metrics
col_m1, col_m2, col_m3 = st.columns(3)

total_expense = st.session_state.expenses["Amount"].sum() if not st.session_state.expenses.empty else 0.0
total_income = st.session_state.income["Amount"].sum() if not st.session_state.income.empty else 0.0
net = total_income - total_expense

with col_m1:
    st.metric("Total Spent", f"${total_expense:,.2f}")
with col_m2:
    st.metric("Total Income", f"${total_income:,.2f}")
with col_m3:
    st.metric("Net Balance", f"${net:,.2f}", delta="Surplus" if net >= 0 else "Deficit")

st.markdown("---")

# ======================
# 📥 Download Section
# ======================
st.subheader("📥 Download Records")

exp_csv = st.session_state.expenses.to_csv(index=False).encode("utf-8")
inc_csv = st.session_state.income.to_csv(index=False).encode("utf-8")

both_df = pd.concat(
    [st.session_state.expenses.assign(Type="Expense"),
     st.session_state.income.assign(Type="Income")],
    ignore_index=True
)
both_csv = both_df.to_csv(index=False).encode("utf-8")

download_choice = st.radio(
    "Select data to download:",
    options=["Both (default)", "Expenses only", "Income only"],
    index=0,
    horizontal=True
)

if download_choice == "Expenses only":
    st.download_button(
        label="💾 Download Expenses CSV",
        data=exp_csv,
        file_name="expenses.csv",
        mime="text/csv",
        use_container_width=True
    )
elif download_choice == "Income only":
    st.download_button(
        label="💾 Download Income CSV",
        data=inc_csv,
        file_name="income.csv",
        mime="text/csv",
        use_container_width=True
    )
else:
    st.download_button(
        label="💾 Download Both (Expenses + Income)",
        data=both_csv,
        file_name="expenses_income.csv",
        mime="text/csv",
        use_container_width=True
    )
