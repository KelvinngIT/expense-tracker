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

    by_vendor = (
        st.session_state.expenses
        .groupby("Vendor")["Amount"]
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

    st.divider()

    col3, col4 = st.columns(2)
    with col3:
        st.subheader("Spending by Vendor")
        st.dataframe(
            by_vendor.reset_index().rename(columns={"Amount": "Total ($)"}),
            use_container_width=True,
            hide_index=True
        )
    with col4:
        st.subheader("Vendor Chart")
        st.bar_chart(by_vendor)

else:
    st.info("No expenses recorded yet. Add your first expense from the sidebar!")
