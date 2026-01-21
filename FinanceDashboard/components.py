import streamlit as st
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, JsCode

def render_summary_cards(month_df):
    """Renders the top summary cards with defensive column checks."""
    col1, col2, col3, col4 = st.columns(4)

    income = 0.0
    total_expense = 0.0
    fixed_expenses = 0.0
    variable_expenses = 0.0
    balance = 0.0

    if not month_df.empty and 'amount' in month_df.columns:
        income = month_df[month_df['amount'] > 0]['amount'].sum()
        total_expense = month_df[month_df['amount'] < 0]['amount'].sum()
        
        if 'cat_type' in month_df.columns:
            fixed_expenses = month_df[(month_df['amount'] < 0) & (month_df['cat_type'] == 'Fixed')]['amount'].sum()
            variable_expenses = month_df[(month_df['amount'] < 0) & (month_df['cat_type'] == 'Variable')]['amount'].sum()
        else:
            # Fallback if cat_type missing
            fixed_expenses = 0.0
            variable_expenses = total_expense
            
        balance = income + total_expense

    col1.metric("Income", f"R$ {income:,.2f}")
    col2.metric("Fixed Costs", f"R$ {abs(fixed_expenses):,.2f}")
    col3.metric("Variable Costs", f"R$ {abs(variable_expenses):,.2f}")
    
    # Delta for balance (Green if positive)
    delta_color = "normal"
    if balance > 0: delta_color = "off" # Streamlit logic often inverse for balance? No.
    
    col4.metric("Balance", f"R$ {balance:,.2f}")

    st.markdown("---")

def render_fixed_management(dl_instance, month_str):
    with st.expander("⚙️ Manage Monthly Defaults"): # Changed to expander for visibility
        st.write("Edit the default list of bills.")
        
        budget_items = []
        for cat, meta in dl_instance.engine.budget.items():
            budget_items.append({
                "Category": cat,
                "Type": meta.get('type', 'Variable'),
                "Limit": meta.get('limit', 0.0),
                "Day": meta.get('day', None)
            })
        b_df = pd.DataFrame(budget_items)
        
        edited_budget = st.data_editor(
            b_df,
            num_rows="dynamic",
            use_container_width=True, # Full width!
            column_config={
                "Type": st.column_config.SelectboxColumn("Type", options=["Fixed", "Variable", "Investment"]),
                "Category": st.column_config.TextColumn("Item Name", required=True),
                "Limit": st.column_config.NumberColumn("Expected R$", format="%.2f"),
                "Day": st.column_config.NumberColumn("Due Day", min_value=1, max_value=31, step=1, format="%d")
            },
            key=f"budget_edit_{month_str}"
        )
        
        if st.button("Save Defaults", key=f"save_budget_{month_str}"):
            new_budget = {}
            for idx, row in edited_budget.iterrows():
                if row['Category']: 
                    day_val = row['Day']
                    if pd.isna(day_val) or day_val == 0: day_val = None
                    else: day_val = int(day_val)

                    new_budget[row['Category']] = {
                        "type": row['Type'],
                        "limit": float(row['Limit']),
                        "day": day_val
                    }
            dl_instance.engine.budget = new_budget
            dl_instance.engine.save_budget()
            st.success("Defaults updated!")
            st.rerun()

def render_checklist_grid(df, key_suffix, is_income=False):
    """Renders the standard AgGrid for Fixed Items with FLEX columns."""
    if df.empty:
        st.info("No items to display.")
        return None
        
    gb = GridOptionsBuilder.from_dataframe(df)
    
    # Flex configuration to fill width
    gb.configure_column("Item", pinned="left", editable=False, minWidth=150, flex=2)
    gb.configure_column("Renamed", editable=True, flex=2) 
    gb.configure_column("Original", editable=False, hide=True) # Hide original to save space
    gb.configure_column("Source", hide=True)
    gb.configure_column("Due", hide=True) 
    
    gb.configure_column("Actual", type=["numericColumn"], precision=2, cellStyle={'fontWeight': 'bold'}, flex=1)
    gb.configure_column("Expected", type=["numericColumn"], precision=2, editable=True, flex=1)
    
    gb.configure_column("Suggested Match", flex=2, cellStyle={'fontStyle': 'italic', 'color': '#6b7280'})
    
    # Status styling
    status_js = JsCode("""
    function(params) {
        if (params.value == 'Paid') return {'color': '#166534', 'backgroundColor': '#dcfce7', 'fontWeight': '600', 'borderRadius': '4px', 'textAlign': 'center'};
        if (params.value == 'Missing') return {'color': '#991b1b', 'backgroundColor': '#fee2e2', 'fontWeight': '600', 'borderRadius': '4px', 'textAlign': 'center'};
        return {'color': '#854d0e', 'backgroundColor': '#fef9c3', 'borderRadius': '4px', 'textAlign': 'center'};
    }
    """)
    gb.configure_column("Status", cellStyle=status_js, flex=1, minWidth=100)
    gb.configure_column("_raw_match", hide=True)
    
    gb.configure_selection('single')
    gb.configure_grid_options(domLayout='autoHeight') # Auto height!
    
    return AgGrid(
        df, 
        gridOptions=gb.build(), 
        fit_columns_on_grid_load=True, # Force fit
        width='100%', # explicit
        allow_unsafe_jscode=True, 
        key=key_suffix,
        update_mode=GridUpdateMode.SELECTION_CHANGED | GridUpdateMode.VALUE_CHANGED,
        theme='alpine' # Cleaner light theme
    )

def render_transaction_editor(dataframe, key_suffix, budget_keys):
    """Renders the interactive transaction editor."""
    if dataframe.empty:
        st.info("No transactions found.")
        return None, None

    # Filter columns defensive
    available_cols = [c for c in ['date', 'description', 'amount', 'category', 'account'] if c in dataframe.columns]
    show_df = dataframe[available_cols].copy()
    
    edited_txns = st.data_editor(
        show_df,
        column_config={
            "amount": st.column_config.NumberColumn(format="R$ %.2f", disabled=True), 
            "date": st.column_config.DateColumn(format="DD/MM/YYYY", disabled=True),
            "description": st.column_config.TextColumn("Description", required=True, width="large"),
            "category": st.column_config.SelectboxColumn("Category", options=list(budget_keys), required=True),
            "account": st.column_config.TextColumn("Account", disabled=True),
        },
        use_container_width=True, # Critical for full width
        hide_index=True, 
        num_rows="fixed",
        key=key_suffix
    )
    return show_df, edited_txns

def render_vault_summary(month_df, dl_instance, month_str):
    """Renders the specific VAULT summary with editable balance - ENHANCED VERSION."""
    # Load persisted balance for this month
    saved_bal = dl_instance.get_balance_override(month_str)

    # Calculate Flows
    income = 0.0
    parcelas = 0.0 # Installments
    fixed_exp = 0.0
    variable_exp = 0.0
    investments = 0.0

    if not month_df.empty:
        income = month_df[month_df['amount'] > 0]['amount'].sum()

        expenses = month_df[month_df['amount'] < 0]

        # Parcelas: transactions with installment pattern
        mask_parcelas = expenses['description'].str.contains(r'\d{1,2}/\d{1,2}', regex=True, na=False)
        parcelas = expenses[mask_parcelas]['amount'].sum()

        # Fixed, Variable, Investment
        fixed_exp = expenses[(expenses['cat_type'] == 'Fixed')]['amount'].sum()
        variable_exp = expenses[(expenses['cat_type'] == 'Variable')]['amount'].sum()

        # Investment transactions (could be positive or negative)
        investments = month_df[month_df['cat_type'] == 'Investment']['amount'].sum()

    # Layout
    st.markdown("### RESUMO")

    # Balance Input Row with additional context
    col_bal, col_info = st.columns([1, 3])
    with col_bal:
        current_val = saved_bal if saved_bal is not None else 0.0
        new_bal = st.number_input(
            "SALDO EM CONTA:",
            value=float(current_val),
            step=100.0,
            format="%.2f",
            key=f"bal_{month_str}",
            help="Enter your current bank balance to track against calculated flow"
        )
        if new_bal != current_val:
            dl_instance.save_balance_override(month_str, new_bal)
            st.toast("✅ Saldo atualizado!")

    with col_info:
        # Calculate percentages vs income
        if income > 0:
            fixed_pct = (abs(fixed_exp) / income) * 100
            variable_pct = (abs(variable_exp) / income) * 100
            investment_pct = (abs(investments) / income) * 100 if investments < 0 else 0

            st.caption(f"**Budget Allocation:** Fixed {fixed_pct:.1f}% | Variable {variable_pct:.1f}% | Investment {investment_pct:.1f}% (Target: 50/30/20)")

    st.markdown("")  # Spacing

    # Net calculation
    net_result = income + fixed_exp + variable_exp + (investments if investments < 0 else 0)

    # 5-Column Metrics Row (matching mockup exactly)
    gm1, gm2, gm3, gm4, gm5 = st.columns(5)

    def _metric_html(label, value, color):
        return f"""
        <div style="background: white; padding: 12px; border-radius: 8px; border: 2px solid #e5e7eb; text-align: center; min-height: 85px; display: flex; flex-direction: column; justify-content: center;">
            <div style="font-size: 1.75rem; font-weight: 800; color: {color}; margin-bottom: 4px;">{value:,.0f}</div>
            <div style="font-size: 0.75rem; color: #6b7280; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;">{label}</div>
        </div>
        """

    gm1.markdown(_metric_html("ENTRADAS", income, "#16a34a"), unsafe_allow_html=True)
    gm2.markdown(_metric_html("PARCELAS", abs(parcelas), "#ea580c"), unsafe_allow_html=True)
    gm3.markdown(_metric_html("GASTOS FIXOS", abs(fixed_exp), "#dc2626"), unsafe_allow_html=True)
    gm4.markdown(_metric_html("GASTOS VARIÁVEIS", abs(variable_exp), "#dc2626"), unsafe_allow_html=True)
    gm5.markdown(_metric_html("SALDO", net_result, "#16a34a" if net_result >= 0 else "#dc2626"), unsafe_allow_html=True)

    st.markdown("---")

def render_recurring_grid(df, key_suffix, title="RECORRENTES"):
    """
    Simulates the structure:
    DATA | TIPO | DESCRIÇÃO | VALOR | STATUS | TRANSAÇÃO MAPEADA
    """
    st.markdown(f"### {title}")
    
    if df.empty:
        st.info("Nenhum item.")
        return

    gb = GridOptionsBuilder.from_dataframe(df)
    
    # Columns Mapping
    # We expect 'Item' (Category/Rule Name) -> DESCRIÇÃO
    # Expected -> VALOR (Target)
    # Status -> STATUS
    # Suggested Match -> TRANSAÇÃO MAPEADA
    
    gb.configure_column("Due", headerName="DIA", width=70)
    gb.configure_column("Item", headerName="DESCRIÇÃO", flex=2)
    gb.configure_column("Expected", headerName="VALOR", type=["numericColumn"], precision=2, editable=True, flex=1)
    
    # Status Badge
    status_js = JsCode("""
    function(params) {
        if (params.value == 'Paid') return {'backgroundColor': '#dcfce7', 'color': '#166534', 'borderRadius': '4px', 'textAlign': 'center', 'fontWeight': 'bold'};
        if (params.value == 'Missing') return {'backgroundColor': '#fee2e2', 'color': '#991b1b', 'borderRadius': '4px', 'textAlign': 'center', 'fontWeight': 'bold'};
        return {'backgroundColor': '#f3f4f6', 'color': '#1f2937'};
    }
    """)
    gb.configure_column("Status", headerName="STATUS", cellStyle=status_js, flex=1)
    
    # Transação Mapeada (Ideally a dropdown, but for now Text showing the match)
    gb.configure_column("Suggested Match", headerName="TRANSAÇÃO MAPEADA", flex=3, cellStyle={'fontStyle': 'italic', 'color': '#4b5563'})
    
    # Hide others
    gb.configure_column("Renamed", hide=True)
    gb.configure_column("Original", hide=True)
    gb.configure_column("Source", hide=True)
    gb.configure_column("Actual", hide=True)
    gb.configure_column("_raw_match", hide=True)

    gb.configure_selection('single')
    
    AgGrid(
        df, 
        gridOptions=gb.build(), 
        height=400, 
        width='100%', 
        fit_columns_on_grid_load=True, 
        allow_unsafe_jscode=True, 
        key=key_suffix,
        update_mode=GridUpdateMode.SELECTION_CHANGED | GridUpdateMode.VALUE_CHANGED
    )

def render_cards_grid(df, key_suffix):
    """
    Structure: DATA | CATEGORIA | SUBCATEGORIA | DESCRIÇÃO | TRANSAÇÃO MAPEADA | VALOR | PARCELA
    """
    if df.empty:
        st.info("Sem transações de cartão.")
        return
        
    # Prepare data specifically for this view
    # "Subcategoria" -> We don't have it, assume Category = Category
    # "Transação Mapeada" -> In raw transactions, this might be redundant? 
    # Or maybe user means "Matched Rule"? 
    # For now, standard transaction table with "Parcela" column.
    
    # Logic to extract Parcela
    df = df.copy()
    import re
    def extract_parcela(desc):
        m = re.search(r'(\d{1,2}/\d{1,2})', str(desc))
        return m.group(1) if m else "-"
    
    df['Parcela'] = df['description'].apply(extract_parcela)
    
    # Include subcategory if available
    display_cols = ['date', 'category', 'subcategory', 'description', 'amount', 'Parcela']
    # Filter only existing columns
    display_cols = [c for c in display_cols if c in df.columns]

    gb = GridOptionsBuilder.from_dataframe(df[display_cols])

    gb.configure_column("date", headerName="DATA", type=["dateColumn"], valueFormatter="x ? new Date(x).toLocaleDateString('pt-BR') : ''", width=110, pinned='left')
    gb.configure_column("category", headerName="CATEGORIA", editable=True, width=140)

    if 'subcategory' in df.columns:
        gb.configure_column("subcategory", headerName="SUBCATEGORIA", editable=True, width=140)

    gb.configure_column("description", headerName="DESCRIÇÃO", editable=True, flex=3, minWidth=250)
    gb.configure_column("amount", headerName="VALOR", type=["numericColumn"], precision=2, width=130, aggFunc='sum')
    gb.configure_column("Parcela", headerName="PARCELA", width=100, cellStyle={'textAlign': 'center', 'fontWeight': 'bold', 'color': '#ea580c'})
    
    gb.configure_selection('multiple', use_checkbox=True)
    gb.configure_side_bar() # Enable sidebar for filtering
    gb.configure_grid_options(domLayout='autoHeight')
    
    AgGrid(
        df, 
        gridOptions=gb.build(), 
        width='100%', 
        allow_unsafe_jscode=True,
        key=key_suffix,
        theme='alpine'
    )
