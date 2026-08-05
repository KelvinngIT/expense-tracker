# ======================
# All Expenses + Deletion + Download
# ======================
st.subheader("All Expenses (Filtered)")

if not filtered_df.empty:
    display_df = filtered_df.copy()
    display_df.insert(0, "Select", False)

    # Format Amount column with thousands separator and 2 decimals
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
