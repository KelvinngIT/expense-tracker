# ======================
# Sidebar - Upload CSV
# ======================
st.sidebar.divider()
st.sidebar.header("📥 Upload Expenses")
uploaded_file = st.sidebar.file_uploader(
    "Upload CSV file",
    type=["csv"],
    help="Preferred columns: Date, Period, User, Category, Amount, Vendor, Description, Remark, Source, Agreement"
)

if uploaded_file is not None:
    try:
        import_df = pd.read_csv(uploaded_file)
        # Normalize column names
        import_df.columns = import_df.columns.str.strip().str.title()
        
        # Minimum required columns
        min_required = {"Date", "Category", "Amount"}
        if not min_required.issubset(set(import_df.columns)):
            st.sidebar.error(
                f"Missing columns. At least required: {', '.join(min_required)}\n"
                f"Found: {', '.join(import_df.columns)}"
            )
        else:
            # Fill defaults for missing columns
            defaults = {
                "Period": current_period,
                "User": USER,
                "Vendor": "-",
                "Description": "-",
                "Remark": "-",
                "Source": "Import",
                "Agreement": "-"
            }
            for col, default in defaults.items():
                if col not in import_df.columns:
                    import_df[col] = default
            
            # Align with schema
            import_df = import_df[COLUMNS].copy()
            import_df["Amount"] = pd.to_numeric(import_df["Amount"], errors="coerce")
            import_df = import_df.dropna(subset=["Amount"])
            import_df["Amount"] = import_df["Amount"].astype(float)
            
            for col in COLUMNS:
                import_df[col] = import_df[col].fillna(defaults.get(col, "-")).astype(str)
            
            # Import button
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
