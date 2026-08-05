# ======================
# Sidebar - Filters (Year + Month)
# ======================
st.sidebar.divider()
st.sidebar.header("🔍 Filters")

if not st.session_state.expenses.empty:
    # Ensure Date column is datetime
    st.session_state.expenses["Date"] = pd.to_datetime(
        st.session_state.expenses["Date"], errors="coerce"
    )
    st.session_state.expenses["Year"] = st.session_state.expenses["Date"].dt.year
    st.session_state.expenses["Month"] = st.session_state.expenses["Date"].dt.month

    # Year filter
    years = sorted(st.session_state.expenses["Year"].dropna().unique())
    selected_year = st.sidebar.selectbox("Year", options=["All"] + years)

    # Month filter
    months = sorted(st.session_state.expenses["Month"].dropna().unique())
    month_names = {i: datetime(2000, i, 1).strftime("%B") for i in months}
    month_options = ["All"] + [month_names[m] for m in months]
    selected_month = st.sidebar.selectbox("Month", options=month_options)

    # Apply filters
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
    st.metric("Total Spent", f"${total:,.2f}")  # formatted as 000,000.00
    
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
            .style.format({"Total ($)": "{:,.2f}"}),  # formatted values
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
st.subheader("All Expenses (Filtered)")

if not filtered_df.empty:
    display_df = filtered_df.copy()
    display_df.insert(0, "Select", False)

    # Format Amount column with thousands separator and 2 decimals
    display_df["Amount"] = display_df["Amount"].map(lambda x: f"{x:,.2f}")

    edited_df = st.data_editor(
        display_df,
        hide_index=True,
        use_container_width=True,
        disabled=[col for col in display_df.columns if col != "Select"],
        key="expense_editor"
    )
