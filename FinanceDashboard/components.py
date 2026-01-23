import streamlit as st
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, JsCode
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from table_component import VaultTable, create_recurring_table, create_cards_table

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
            fixed_expenses = month_df[(month_df['amount'] < 0) & (month_df['cat_type'] == 'Fixo')]['amount'].sum()
            variable_expenses = month_df[(month_df['amount'] < 0) & (month_df['cat_type'] == 'Variável')]['amount'].sum()
        else:
            # Fallback if cat_type missing
            fixed_expenses = 0.0
            variable_expenses = total_expense
            
        balance = income + total_expense

    col1.metric("Income", f"R$ {income:,.2f}")
    col2.metric("Fixo Costs", f"R$ {abs(fixed_expenses):,.2f}")
    col3.metric("Variável Costs", f"R$ {abs(variable_expenses):,.2f}")
    
    # Delta for balance (Green if positive)
    delta_color = "normal"
    if balance > 0: delta_color = "off" # Streamlit logic often inverse for balance? No.
    
    col4.metric("Balance", f"R$ {balance:,.2f}")

    st.markdown("---")

def render_fixed_management(dl_instance, month_str):
    with st.expander("Manage Monthly Defaults"): # Changed to expander for visibility
        st.write("Edit the default list of bills.")
        
        budget_items = []
        for cat, meta in dl_instance.engine.budget.items():
            budget_items.append({
                "Category": cat,
                "Type": meta.get('type', 'Variável'),
                "Limit": meta.get('limit', 0.0),
                "Day": meta.get('day', None)
            })
        b_df = pd.DataFrame(budget_items)
        
        edited_budget = st.data_editor(
            b_df,
            num_rows="dynamic",
            use_container_width=True, # Full width!
            column_config={
                "Type": st.column_config.SelectboxColumn("Type", options=["Fixo", "Variável", "Investimento"]),
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
    """Renders the standard table for Fixo Items using VaultTable."""
    if df.empty:
        st.info("No items to display.")
        return None

    # Create VaultTable instance
    table = VaultTable(df, empty_message="No items to display.")

    # Configure columns
    table.configure_column("Item", header_name="Item", pinned="left", min_width=150, flex=2)
    table.configure_column("Renamed", editable=True, flex=2)
    table.configure_column("Original", hide=True)
    table.configure_column("Source", hide=True)
    table.configure_column("Due", hide=True)

    # Numeric columns
    actual_style = JsCode("function(params) { return {'fontWeight': 'bold'}; }")
    table.configure_column("Actual", numeric=True, cell_style=actual_style, flex=1)
    table.configure_column("Expected", numeric=True, editable=True, flex=1)

    # Suggested Match column
    match_style = JsCode("function(params) { return {'fontStyle': 'italic', 'color': '#6b7280'}; }")
    table.configure_column("Suggested Match", flex=2, cell_style=match_style)

    # Status column with badge styling
    table.configure_status_badge("Status")
    table.configure_column("Status", flex=1, min_width=100)

    # Hide internal columns
    table.configure_column("_raw_match", hide=True)

    # Single selection
    table.configure_selection(mode='single')

    # Render
    return table.render(key=key_suffix)

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

    # Calculate Flows - EXCLUDE INTERNAL TRANSFERS
    income = 0.0
    parcelas = 0.0 # Installments
    fixed_exp = 0.0
    variable_exp = 0.0
    investments = 0.0

    if not month_df.empty:
        # Filter out internal transfers for accurate metrics
        # Check if column exists (new normalized data)
        if 'is_internal_transfer' in month_df.columns:
            real_df = month_df[~month_df['is_internal_transfer']].copy()
        else:
            # Fallback: no filtering (legacy data)
            real_df = month_df.copy()

        # REAL income (excluding transfers)
        income = real_df[real_df['amount'] > 0]['amount'].sum()

        # REAL expenses (excluding transfers)
        expenses = real_df[real_df['amount'] < 0]

        # Parcelas: use is_installment flag if available
        if 'is_installment' in real_df.columns:
            parcelas = expenses[expenses['is_installment'] == True]['amount'].sum()
        else:
            # Fallback: pattern matching
            mask_parcelas = expenses['description'].str.contains(r'\d{1,2}/\d{1,2}', regex=True, na=False)
            parcelas = expenses[mask_parcelas]['amount'].sum()

        # Fixo, Variável, Investimento
        fixed_exp = expenses[(expenses['cat_type'] == 'Fixo')]['amount'].sum()
        variable_exp = expenses[(expenses['cat_type'] == 'Variável')]['amount'].sum()

        # Investimento transactions (could be positive or negative)
        investments = real_df[real_df['cat_type'] == 'Investimento']['amount'].sum()

    # Layout
    st.markdown("### RESUMO")

    # CSS to hide +/- buttons on number input - use more aggressive selectors
    st.markdown("""
    <style>
    /* Hide stepper buttons in number inputs */
    input[type="number"]::-webkit-inner-spin-button,
    input[type="number"]::-webkit-outer-spin-button {
        -webkit-appearance: none !important;
        margin: 0 !important;
        display: none !important;
    }
    input[type="number"] {
        -moz-appearance: textfield !important;
    }
    /* Also hide Streamlit's custom stepper buttons */
    button[kind="stepperUp"],
    button[kind="stepperDown"],
    button[data-testid*="step"],
    .step-up,
    .step-down {
        display: none !important;
        visibility: hidden !important;
    }
    </style>
    """, unsafe_allow_html=True)

    # Balance Input Row with additional context
    col_bal, col_info = st.columns([1, 3])
    with col_bal:
        current_val = saved_bal if saved_bal is not None else 0.0
        # Use text_input instead of number_input to avoid +/- buttons
        bal_str = st.text_input(
            "SALDO EM CONTA:",
            value=f"{current_val:.2f}",
            key=f"bal_{month_str}",
            help="Enter your current bank balance to track against calculated flow"
        )
        try:
            new_bal = float(bal_str.replace(',', '.'))
            if new_bal != current_val:
                dl_instance.save_balance_override(month_str, new_bal)
        except ValueError:
            new_bal = current_val  # Keep old value if invalid input
            st.toast("[OK] Saldo atualizado!")

    with col_info:
        # Calculate percentages vs income
        if income > 0:
            fixed_pct = (abs(fixed_exp) / income) * 100
            variable_pct = (abs(variable_exp) / income) * 100
            investment_pct = (abs(investments) / income) * 100 if investments < 0 else 0

    # st.caption(f"**Alocação de Orçamento:** Fixo {fixed_pct:.1f}% | Variável {variable_pct:.1f}% | Investimento {investment_pct:.1f}% (Target: 50/30/20)")

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

def render_recurring_grid(df, key_suffix, title="RECORRENTES", show_export=True):
    """
    Renders recurring items table using VaultTable.
    Structure: DATA | DESCRIÇÃO | VALOR | STATUS | TRANSAÇÃO MAPEADA

    Args:
        df: DataFrame with recurring items
        key_suffix: Unique key for table
        title: Section title (empty string to skip)
        show_export: Show CSV export button
    """
    # Only show title if provided
    if title:
        st.markdown(f"### {title}")

    if df.empty:
        st.info("Nenhum item.")
        return

    # Use factory function for recurring tables
    table = create_recurring_table(df, key=key_suffix)

    # Render with or without export
    if show_export:
        table.render_with_export(key=key_suffix)
    else:
        table.render(key=key_suffix)

def render_cards_grid(df, key_suffix, show_export=True):
    """
    Renders credit card transactions table using VaultTable.
    Structure: DATA | CARTÃO | CATEGORIA | SUBCATEGORIA | DESCRIÇÃO | VALOR | PARCELA
    Fixed height container with internal scroll (500px)

    Args:
        df: DataFrame with card transactions
        key_suffix: Unique key for table
        show_export: Show CSV export button
    """
    if df.empty:
        st.info("Sem transações de cartão.")
        return

    # Use factory function for card tables
    table = create_cards_table(df, key=key_suffix)

    # Render with or without export
    if show_export:
        table.render_with_export(key=key_suffix)
    else:
        table.render(key=key_suffix)

def render_transaction_mapper(df, dl_instance, key_suffix):
    """
    Interactive transaction mapping interface for categorizing and subcategorizing transactions.
    Allows users to:
    - Map transactions to categories and subcategories
    - Mark transactions as investments
    - Save mapping rules for future use
    """
    st.markdown("### MAPEAMENTO DE TRANSAÇÕES")

    if df.empty:
        st.info("Sem transações para mapear.")
        return

    # Get all available categories and subcategories
    categories = list(dl_instance.engine.budget.keys())

    # Filter for uncategorized or need review transactions
    unmapped = df[df['category'].isin(['Não categorizado', 'Unknown', None])].copy()

    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown(f"**Total Transações Não Mapeadas:** {len(unmapped)}")

    with col2:
        show_all = st.checkbox("Mostrar Todas as Transações", value=False, key=f"show_all_{key_suffix}")

    display_df = df.copy() if show_all else unmapped.copy()

    if display_df.empty:
        st.success("[OK] Todas as transações estão mapeadas!")
        return

    # Add mapping controls
    with st.expander("🔧 Mapear Transação", expanded=len(unmapped) > 0):
        # Select transaction to map
        transaction_options = [
            f"{row['date'].strftime('%d/%m/%Y')} - {row['description']} (R$ {row['amount']:,.2f})"
            for idx, row in display_df.iterrows()
        ]

        if transaction_options:
            selected_txn = st.selectbox(
                "Selecione uma transação:",
                range(len(transaction_options)),
                format_func=lambda x: transaction_options[x],
                key=f"txn_select_{key_suffix}"
            )

            selected_row = display_df.iloc[selected_txn]

            # Mapping form
            col_cat, col_sub = st.columns(2)

            with col_cat:
                new_category = st.selectbox(
                    "Categoria:",
                    categories,
                    index=categories.index(selected_row['category']) if selected_row['category'] in categories else 0,
                    key=f"cat_{key_suffix}"
                )

            with col_sub:
                # Get available subcategories for selected category
                available_subcats = []
                if new_category in dl_instance.engine.subcategory_rules:
                    available_subcats = list(set(dl_instance.engine.subcategory_rules[new_category].values()))

                # Add option to create new subcategory
                subcategory_options = ["(Nova Subcategoria)"] + available_subcats

                subcategory_choice = st.selectbox(
                    "Subcategoria:",
                    subcategory_options,
                    key=f"subcat_{key_suffix}"
                )

                if subcategory_choice == "(Nova Subcategoria)":
                    new_subcategory = st.text_input(
                        "Nome da Nova Subcategoria:",
                        key=f"new_subcat_{key_suffix}"
                    )
                else:
                    new_subcategory = subcategory_choice

            # Keyword extraction for rule creation
            st.markdown("---")
            keyword = st.text_input(
                "Palavra-chave para criar regra automática (opcional):",
                value=selected_row['description'][:20].strip(),
                help="Esta palavra-chave será usada para categorizar automaticamente transações futuras similares",
                key=f"keyword_{key_suffix}"
            )

            save_as_rule = st.checkbox(
                "Salvar como regra automática",
                value=True,
                help="Se marcado, transações futuras com esta palavra-chave serão categorizadas automaticamente",
                key=f"save_rule_{key_suffix}"
            )

            # Action buttons
            col_save, col_skip = st.columns(2)

            with col_save:
                if st.button("Salvar Mapeamento", key=f"save_map_{key_suffix}", type="primary"):
                    # Save category rule
                    if save_as_rule and keyword:
                        dl_instance.engine.add_rule(keyword, new_category)

                        # Save subcategory rule if provided
                        if new_subcategory and subcategory_choice != "(Nova Subcategoria)":
                            dl_instance.engine.add_subcategory_rule(new_category, keyword, new_subcategory)
                        elif new_subcategory:
                            # New subcategory - create the rule
                            dl_instance.engine.add_subcategory_rule(new_category, keyword, new_subcategory)

                        st.success(f"[OK] Regra criada: '{keyword}' → {new_category}" +
                                 (f" → {new_subcategory}" if new_subcategory else ""))
                    else:
                        st.info("Mapeamento salvo apenas para esta transação (sem regra automática)")

                    st.rerun()

            with col_skip:
                if st.button("Pular", key=f"skip_{key_suffix}"):
                    st.info("Transação ignorada")

    # Display transaction table for reference
    st.markdown("---")
    st.markdown("#### Transações")

    display_cols = ['date', 'description', 'category', 'subcategory', 'amount']
    display_cols = [c for c in display_cols if c in display_df.columns]

    st.dataframe(
        display_df[display_cols],
        use_container_width=True,
        hide_index=True,
        column_config={
            "date": st.column_config.DateColumn("Data", format="DD/MM/YYYY"),
            "description": st.column_config.TextColumn("Descrição", width="large"),
            "category": st.column_config.TextColumn("Categoria"),
            "subcategory": st.column_config.TextColumn("Subcategoria"),
            "amount": st.column_config.NumberColumn("Valor", format="R$ %.2f")
        }
    )

def render_installment_tracker(df, key_suffix):
    """
    Tracks and visualizes installment payments (parcelas).
    Shows progress bars and summaries for recurring installment transactions.
    """
    import re

    st.markdown("### ACOMPANHAMENTO DE PARCELAS")

    if df.empty:
        st.info("Sem transações de parcelas.")
        return

    # Extract installment information from descriptions
    installments_data = []

    for idx, row in df.iterrows():
        desc = str(row['description'])
        # Match pattern like "1/12", "03/24", etc.
        match = re.search(r'(\d{1,2})/(\d{1,2})', desc)

        if match:
            current = int(match.group(1))
            total = int(match.group(2))

            # Extract base description (remove installment part)
            base_desc = re.sub(r'\s*\d{1,2}/\d{1,2}\s*', '', desc).strip()

            installments_data.append({
                'description': base_desc,
                'current': current,
                'total': total,
                'amount': row['amount'],
                'date': row['date'],
                'category': row.get('category', 'Não categorizado'),
                'full_description': desc
            })

    if not installments_data:
        st.info("Nenhuma parcela identificada neste mês.")
        return

    # Create dataframe from installments
    inst_df = pd.DataFrame(installments_data)

    # Group by base description to get unique installment series
    grouped = inst_df.groupby('description').agg({
        'current': 'first',
        'total': 'first',
        'amount': 'first',
        'category': 'first',
        'date': 'max'
    }).reset_index()

    # Calculate progress percentage
    grouped['progress'] = (grouped['current'] / grouped['total'] * 100).round(1)
    grouped['remaining'] = grouped['total'] - grouped['current']
    grouped['paid_total'] = grouped['amount'] * grouped['current']
    grouped['future_total'] = grouped['amount'] * grouped['remaining']

    # Summary metrics
    st.markdown("#### Resumo de Parcelas")
    col1, col2, col3, col4 = st.columns(4)

    total_installments = len(grouped)
    total_paid = grouped['paid_total'].sum()
    total_future = grouped['future_total'].sum()
    avg_progress = grouped['progress'].mean()

    col1.metric("Total de Parcelas", total_installments)
    col2.metric("Já Pago", f"R$ {abs(total_paid):,.2f}")
    col3.metric("A Pagar", f"R$ {abs(total_future):,.2f}")
    col4.metric("Progresso Médio", f"{avg_progress:.1f}%")

    st.markdown("---")

    # Display installment cards with progress bars
    st.markdown("#### Detalhamento")

    for idx, row in grouped.iterrows():
        with st.container():
            col_info, col_progress = st.columns([3, 1])

            with col_info:
                st.markdown(f"**{row['description']}**")
                st.caption(f"Categoria: {row['category']} | Parcela {row['current']}/{row['total']}")

                # Progress bar
                progress_value = row['progress'] / 100
                st.progress(progress_value)

            with col_progress:
                st.metric("Valor", f"R$ {abs(row['amount']):,.2f}")
                st.caption(f"{row['remaining']} restantes")

            # Additional details in expander
            with st.expander(f"Detalhes - {row['description']}"):
                det_col1, det_col2 = st.columns(2)

                with det_col1:
                    st.markdown(f"**Já Pago:** R$ {abs(row['paid_total']):,.2f}")
                    st.markdown(f"**Parcela Atual:** {row['current']}/{row['total']}")

                with det_col2:
                    st.markdown(f"**A Pagar:** R$ {abs(row['future_total']):,.2f}")
                    st.markdown(f"**Última Parcela:** {row['date'].strftime('%d/%m/%Y')}")

            st.markdown("---")

    # Detailed table view
    with st.expander("📋 Visualização Tabular"):
        display_df = grouped[['description', 'category', 'current', 'total', 'progress', 'amount', 'paid_total', 'future_total']].copy()
        display_df.columns = ['Descrição', 'Categoria', 'Atual', 'Total', 'Progresso %', 'Valor Parcela', 'Já Pago', 'A Pagar']

        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Valor Parcela": st.column_config.NumberColumn(format="R$ %.2f"),
                "Já Pago": st.column_config.NumberColumn(format="R$ %.2f"),
                "A Pagar": st.column_config.NumberColumn(format="R$ %.2f"),
                "Progresso %": st.column_config.ProgressColumn(
                    min_value=0,
                    max_value=100,
                    format="%.1f%%"
                )
            }
        )

def render_analytics_dashboard(df, month_str, dl_instance):
    """
    Interactive analytics dashboard with various charts and insights.
    Provides visualizations for spending patterns, category breakdown, and trends.
    """
    st.markdown("### ANÁLISE E INSIGHTS")

    if df.empty:
        st.info("Sem dados para análise.")
        return

    # Create tabs for different analytics views
    tab1, tab2, tab3, tab4 = st.tabs(["Visão Geral", "Categorias", "Tendências", "Comparativo"])

    with tab1:
        st.markdown("#### Visão Geral do Mês")

        # Calculate key metrics
        income = df[df['amount'] > 0]['amount'].sum()
        expenses = abs(df[df['amount'] < 0]['amount'].sum())
        balance = income - expenses

        # Summary metrics in columns
        col1, col2, col3 = st.columns(3)

        col1.metric("Total de Receitas", f"R$ {income:,.2f}", delta=None)
        col2.metric("Total de Despesas", f"R$ {expenses:,.2f}", delta=None)
        col3.metric("Saldo do Mês", f"R$ {balance:,.2f}",
                   delta=f"R$ {balance:,.2f}",
                   delta_color="normal" if balance >= 0 else "inverse")

        st.markdown("---")

        # Income vs Expenses Chart
        col_chart1, col_chart2 = st.columns(2)

        with col_chart1:
            # Pie chart for expense distribution
            expense_data = df[df['amount'] < 0].copy()
            if not expense_data.empty and 'category' in expense_data.columns:
                category_totals = expense_data.groupby('category')['amount'].sum().abs().reset_index()
                category_totals = category_totals.sort_values('amount', ascending=False)

                fig_pie = px.pie(
                    category_totals,
                    values='amount',
                    names='category',
                    title='Distribuição de Despesas por Categoria',
                    color_discrete_sequence=px.colors.qualitative.Set3
                )
                fig_pie.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig_pie, use_container_width=True)

        with col_chart2:
            # Bar chart for top categories
            if not expense_data.empty and 'category' in expense_data.columns:
                top_categories = category_totals.head(10)

                fig_bar = px.bar(
                    top_categories,
                    x='category',
                    y='amount',
                    title='Top 10 Categorias de Despesas',
                    labels={'amount': 'Valor (R$)', 'category': 'Categoria'},
                    color='amount',
                    color_continuous_scale='Reds'
                )
                fig_bar.update_layout(xaxis_tickangle=-45)
                st.plotly_chart(fig_bar, use_container_width=True)

    with tab2:
        st.markdown("#### Análise por Categoria")

        # Category breakdown with subcategories
        if 'category' in df.columns:
            # Filter expenses
            expense_df = df[df['amount'] < 0].copy()

            if not expense_df.empty:
                # Sunburst chart for category hierarchy
                if 'subcategory' in expense_df.columns:
                    # Prepare data for sunburst
                    sunburst_data = expense_df.groupby(['category', 'subcategory'])['amount'].sum().abs().reset_index()

                    fig_sunburst = px.sunburst(
                        sunburst_data,
                        path=['category', 'subcategory'],
                        values='amount',
                        title='Hierarquia de Categorias e Subcategorias',
                        color='amount',
                        color_continuous_scale='RdYlGn_r'
                    )
                    st.plotly_chart(fig_sunburst, use_container_width=True)

                # Category type breakdown (Fixo vs Variável vs Investimento)
                if 'cat_type' in expense_df.columns:
                    type_totals = expense_df.groupby('cat_type')['amount'].sum().abs().reset_index()

                    col_type1, col_type2 = st.columns(2)

                    with col_type1:
                        fig_type = px.pie(
                            type_totals,
                            values='amount',
                            names='cat_type',
                            title='Distribuição por Tipo',
                            color_discrete_map={
                                'Fixo': '#dc2626',
                                'Variável': '#ea580c',
                                'Investimento': '#16a34a'
                            }
                        )
                        st.plotly_chart(fig_type, use_container_width=True)

                    with col_type2:
                        # Budget compliance per category
                        st.markdown("**Aderência ao Orçamento**")

                        budget_data = []
                        for category, meta in dl_instance.engine.budget.items():
                            limit = meta.get('limit', 0)
                            if limit > 0:
                                actual = abs(expense_df[expense_df['category'] == category]['amount'].sum())
                                budget_data.append({
                                    'category': category,
                                    'actual': actual,
                                    'limit': limit,
                                    'variance': actual - limit,
                                    'compliance': (actual / limit * 100) if limit > 0 else 0
                                })

                        if budget_data:
                            budget_df = pd.DataFrame(budget_data)

                            fig_budget = go.Figure()

                            fig_budget.add_trace(go.Bar(
                                name='Realizado',
                                x=budget_df['category'],
                                y=budget_df['actual'],
                                marker_color='lightblue'
                            ))

                            fig_budget.add_trace(go.Bar(
                                name='Orçado',
                                x=budget_df['category'],
                                y=budget_df['limit'],
                                marker_color='coral'
                            ))

                            fig_budget.update_layout(
                                title='Realizado vs Orçado',
                                barmode='group',
                                xaxis_tickangle=-45
                            )

                            st.plotly_chart(fig_budget, use_container_width=True)

    with tab3:
        st.markdown("#### Tendências e Padrões")

        # Daily spending trend
        if 'date' in df.columns:
            daily_df = df.copy()
            daily_df['date'] = pd.to_datetime(daily_df['date'])

            # Daily expense trend
            daily_expenses = daily_df[daily_df['amount'] < 0].groupby(
                daily_df['date'].dt.date
            )['amount'].sum().abs().reset_index()

            daily_expenses.columns = ['date', 'total']

            fig_trend = px.line(
                daily_expenses,
                x='date',
                y='total',
                title='Evolução Diária de Despesas',
                labels={'total': 'Despesas (R$)', 'date': 'Data'},
                markers=True
            )
            fig_trend.update_traces(line_color='#dc2626')
            st.plotly_chart(fig_trend, use_container_width=True)

            # Cumulative spending
            daily_expenses['cumulative'] = daily_expenses['total'].cumsum()

            fig_cumulative = px.area(
                daily_expenses,
                x='date',
                y='cumulative',
                title='Despesas Acumuladas no Mês',
                labels={'cumulative': 'Acumulado (R$)', 'date': 'Data'},
                color_discrete_sequence=['#ea580c']
            )
            st.plotly_chart(fig_cumulative, use_container_width=True)

            # Weekly comparison
            daily_df['week'] = daily_df['date'].dt.isocalendar().week
            weekly_expenses = daily_df[daily_df['amount'] < 0].groupby('week')['amount'].sum().abs().reset_index()
            weekly_expenses.columns = ['week', 'total']

            if not weekly_expenses.empty:
                fig_weekly = px.bar(
                    weekly_expenses,
                    x='week',
                    y='total',
                    title='Despesas por Semana',
                    labels={'total': 'Total (R$)', 'week': 'Semana'},
                    color='total',
                    color_continuous_scale='Oranges'
                )
                st.plotly_chart(fig_weekly, use_container_width=True)

    with tab4:
        st.markdown("#### Análise Comparativa")

        # Compare with budget targets
        st.markdown("**Meta vs Realizado**")

        if 'category' in df.columns:
            expense_df = df[df['amount'] < 0].copy()

            comparison_data = []
            for category, meta in dl_instance.engine.budget.items():
                limit = meta.get('limit', 0)
                cat_type = meta.get('type', 'Variável')

                if limit > 0:
                    actual = abs(expense_df[expense_df['category'] == category]['amount'].sum())
                    comparison_data.append({
                        'Categoria': category,
                        'Tipo': cat_type,
                        'Meta': limit,
                        'Realizado': actual,
                        'Diferença': actual - limit,
                        'Status': '[OK] Dentro' if actual <= limit else '[Aviso] Acima'
                    })

            if comparison_data:
                comp_df = pd.DataFrame(comparison_data)

                st.dataframe(
                    comp_df,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "Meta": st.column_config.NumberColumn(format="R$ %.2f"),
                        "Realizado": st.column_config.NumberColumn(format="R$ %.2f"),
                        "Diferença": st.column_config.NumberColumn(
                            format="R$ %.2f",
                            help="Positivo = Acima do orçamento, Negativo = Abaixo do orçamento"
                        )
                    }
                )

                # Variance chart
                fig_variance = px.bar(
                    comp_df,
                    x='Categoria',
                    y='Diferença',
                    color='Diferença',
                    title='Variação do Orçamento por Categoria',
                    labels={'Diferença': 'Variação (R$)', 'Categoria': 'Categoria'},
                    color_continuous_scale=['green', 'yellow', 'red'],
                    color_continuous_midpoint=0
                )
                fig_variance.update_layout(xaxis_tickangle=-45)
                st.plotly_chart(fig_variance, use_container_width=True)
