import streamlit as st
import pandas as pd
import datetime
from DataLoader import DataLoader
from styles import apply_custom_styles
from utils import get_date_filter_strategy, build_checklist_data, filter_month_data
from components import (
    render_vault_summary,
    render_recurring_grid,
    render_cards_grid,
    render_transaction_editor
)
from validation_ui import (
    render_validation_report,
    render_data_quality_metrics,
    render_reconciliation_view
)
from st_aggrid import GridOptionsBuilder, AgGrid

# --- CONFIG & STYLES ---
st.set_page_config(page_title="THE VAULT", layout="wide", page_icon="🏦")
st.markdown(apply_custom_styles(), unsafe_allow_html=True)

# Custom Title Style
st.markdown("""
<style>
    .vault-title {
        font-family: 'Outfit', sans-serif;
        font-size: 3rem;
        font-weight: 800;
        letter-spacing: 0.1rem;
        color: #fca5a5; /* Light Orange/Peach tone */
        text-shadow: 2px 2px 0px #000000;
        margin-bottom: 20px;
    }
</style>
<div class='vault-title'>THE VAULT</div>
""", unsafe_allow_html=True)

# --- DATA LOADING ---
dl_instance = DataLoader()
# We reload data on every run for simplicity with this structure, or ideally cache
dl = dl_instance
df = dl.load_all()

if df.empty:
    st.warning("No data found.")
    st.stop()

# --- VALIDATION & QUALITY CHECKS ---
# Render validation report at the top for visibility
render_validation_report(dl_instance.validator)
render_data_quality_metrics(df)
render_reconciliation_view(df, dl_instance)

# Ensure Date and Month String
df['date'] = pd.to_datetime(df['date'])
df['month_str'] = df['date'].dt.strftime('%Y-%m')

# --- NAVIGATION ---
m_list = df['month_str'].dropna().unique().tolist()
sorted_months = sorted(m_list)

start_filter, current_m_str = get_date_filter_strategy()
visible_months = [m for m in sorted_months if m >= start_filter]
if not visible_months: visible_months = sorted_months[-6:]

# Custom Tab Styling logic handled in styles.py (Generic)
# We render tabs for months
tabs = st.tabs(visible_months)

for i, month in enumerate(visible_months):
    with tabs[i]:
        m_data = filter_month_data(df, month)
        
        # 1. RESUMO
        render_vault_summary(m_data, dl_instance, month)
        
        # 2. RECORRENTES
        # Data Prep
        fixed_income_meta = {k: v for k, v in dl_instance.engine.budget.items() if v.get('type') == 'Income'}
        fixed_expenses_meta = {k: v for k, v in dl_instance.engine.budget.items() if v.get('type') == 'Fixed'}
        
        # Pools
        income_pool = m_data[m_data['amount'] > 0]
        expenses_pool = m_data[m_data['amount'] < 0]
        
        # Grids
        df_inc = build_checklist_data(fixed_income_meta, income_pool, is_expense=False)
        df_exp = build_checklist_data(fixed_expenses_meta, expenses_pool, is_expense=True)
        
        # Prepare Investment Data
        investment_meta = {k: v for k, v in dl_instance.engine.budget.items() if v.get('type') == 'Investment'}
        investment_pool = m_data  # All transactions (could be income or expense for investments)
        df_inv = build_checklist_data(investment_meta, investment_pool, is_expense=False)

        # Tabs for Recorrentes - Added INVESTIMENTOS
        t_rec1, t_rec2, t_rec3, t_rec4, t_rec5 = st.tabs(["TODOS", "ENTRADAS", "FIXOS", "VARIÁVEIS", "INVESTIMENTOS"])

        with t_rec1:
            # Combine all types for overview
            df_combined = pd.concat([df_inc, df_exp, df_inv], ignore_index=True)
            if not df_combined.empty:
                # Sort by Day
                df_combined['DueNum'] = pd.to_numeric(df_combined['Due'], errors='coerce').fillna(99)
                df_combined = df_combined.sort_values(by='DueNum')
                render_recurring_grid(df_combined, f"rec_all_{month}", "Visão Geral (Todos)")
            else:
                st.info("Nenhuma recorrência cadastrada.")

        with t_rec2:
            render_recurring_grid(df_inc, f"rec_inc_{month}", "Entradas Recorrentes")

        with t_rec3:
            render_recurring_grid(df_exp, f"rec_exp_{month}", "Gastos Fixos")

        with t_rec4:
            # Variable items (show all variable transactions)
            variable_txns = m_data[m_data['cat_type'] == 'Variable']
            if not variable_txns.empty:
                st.markdown(f"**Total Gastos Variáveis:** R$ {abs(variable_txns['amount'].sum()):,.2f}")
                st.dataframe(
                    variable_txns[['date', 'description', 'category', 'subcategory', 'amount']],
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.info("Nenhum gasto variável neste mês.")

        with t_rec5:
            render_recurring_grid(df_inv, f"rec_inv_{month}", "Investimentos Recorrentes")
            # Show investment summary
            if not m_data.empty:
                inv_txns = m_data[m_data['cat_type'] == 'Investment']
                if not inv_txns.empty:
                    st.markdown(f"**Total Investido:** R$ {abs(inv_txns[inv_txns['amount'] < 0]['amount'].sum()):,.2f}")
                    st.dataframe(
                        inv_txns[['date', 'description', 'category', 'amount']],
                        use_container_width=True,
                        hide_index=True
                    )

        # 3. CONTROLE CARTÕES
        st.markdown("### CONTROLE CARTÕES")
        t_card1, t_card2, t_card3, t_card4 = st.tabs(["TODOS", "MASTER", "VISA", "RAFA"])
        
        with t_card1:
            render_cards_grid(m_data, f"card_all_{month}")
            
        with t_card2:
            render_cards_grid(m_data[m_data['account'].str.contains("Master", case=False)], f"card_mas_{month}")
            
        with t_card3:
             render_cards_grid(m_data[m_data['account'].str.contains("Visa", case=False)], f"card_vis_{month}")

        with t_card4:
             render_cards_grid(m_data[m_data['account'] == "Mastercard - Rafa"], f"card_raf_{month}")
