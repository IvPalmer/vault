"""
Control Metrics Component
Implements the control dashboard showing:
- A PAGAR (To Pay)
- A ENTRAR (Expected Income)
- GASTO MAX ATUAL (Current Max Spend)
- DIAS ATÉ FECHAMENTO (Days to Closing)
- GASTO DIÁRIO RECOMENDADO (Recommended Daily Spend)
"""
import pandas as pd
import streamlit as st
from datetime import datetime, timedelta
from typing import Dict, Tuple

class ControlMetrics:
    def __init__(self, month_df: pd.DataFrame, dl_instance, month_str: str):
        self.month_df = month_df
        self.dl_instance = dl_instance
        self.month_str = month_str
        self.budget = dl_instance.engine.budget

        # Parse month
        self.year = int(month_str[:4])
        self.month = int(month_str[5:7])

    def calculate_a_pagar(self) -> Tuple[float, list]:
        """
        Calculate A PAGAR (To Pay) - unpaid recurring fixed items
        Returns: (total_amount, list_of_items)
        """
        unpaid_items = []
        total = 0.0

        # Get all fixed and income items from budget
        recurring_items = {k: v for k, v in self.budget.items()
                          if v.get('type') in ['Fixo', 'Income']}

        for category, meta in recurring_items.items():
            # Check if this category appears in month's transactions
            cat_txns = self.month_df[self.month_df['category'] == category]

            if len(cat_txns) == 0:
                # Not paid yet
                expected_amount = meta.get('limit', 0.0)
                if expected_amount > 0:
                    unpaid_items.append({
                        'category': category,
                        'amount': expected_amount,
                        'due_day': meta.get('day', 'N/A'),
                        'type': meta.get('type')
                    })
                    if meta.get('type') == 'Fixo':
                        total += expected_amount

        return total, unpaid_items

    def calculate_a_entrar(self) -> Tuple[float, list]:
        """
        Calculate A ENTRAR (Expected Income) - expected income not yet received
        Returns: (total_amount, list_of_items)
        """
        pending_income = []
        total = 0.0

        # Get all income items from budget
        income_items = {k: v for k, v in self.budget.items()
                       if v.get('type') == 'Income'}

        for category, meta in income_items.items():
            # Check if income received
            cat_txns = self.month_df[
                (self.month_df['category'] == category) &
                (self.month_df['amount'] > 0)
            ]

            expected_amount = meta.get('limit', 0.0)
            received_amount = cat_txns['amount'].sum() if len(cat_txns) > 0 else 0.0

            if received_amount < expected_amount:
                pending = expected_amount - received_amount
                pending_income.append({
                    'category': category,
                    'expected': expected_amount,
                    'received': received_amount,
                    'pending': pending,
                    'due_day': meta.get('day', 'N/A')
                })
                total += pending

        return total, pending_income

    def calculate_days_to_closing(self, closing_day: int = 10) -> int:
        """
        Calculate days until credit card closing
        Default closing day: 10th of next month
        """
        today = datetime.now()

        # Credit card closing is typically on the Xth of next month
        if today.day <= closing_day:
            # Closing is this month
            closing_date = datetime(today.year, today.month, closing_day)
        else:
            # Closing is next month
            if today.month == 12:
                closing_date = datetime(today.year + 1, 1, closing_day)
            else:
                closing_date = datetime(today.year, today.month + 1, closing_day)

        days_to_close = (closing_date - today).days
        return max(0, days_to_close)

    def calculate_current_spend(self) -> Dict:
        """Calculate current month spending vs budget"""
        expenses = self.month_df[self.month_df['amount'] < 0]

        total_spent = abs(expenses['amount'].sum())
        fixed_spent = abs(expenses[expenses['cat_type'] == 'Fixo']['amount'].sum())
        variable_spent = abs(expenses[expenses['cat_type'] == 'Variável']['amount'].sum())

        # Calculate budget limits
        fixed_budget = sum([v.get('limit', 0) for k, v in self.budget.items()
                           if v.get('type') == 'Fixo'])
        variable_budget = sum([v.get('limit', 0) for k, v in self.budget.items()
                              if v.get('type') == 'Variável'])

        return {
            'total_spent': total_spent,
            'fixed_spent': fixed_spent,
            'variable_spent': variable_spent,
            'fixed_budget': fixed_budget,
            'variable_budget': variable_budget,
            'fixed_remaining': max(0, fixed_budget - fixed_spent),
            'variable_remaining': max(0, variable_budget - variable_spent)
        }

    def calculate_recommended_daily_spend(self) -> float:
        """
        Calculate recommended daily spend based on:
        - Variável budget remaining
        - Days left in month
        """
        spend_data = self.calculate_current_spend()
        variable_remaining = spend_data['variable_remaining']

        # Days left in month
        today = datetime.now()

        # Only calculate if we're in the current month
        if (today.year == self.year and today.month == self.month):
            # Calculate last day of month
            if self.month == 12:
                next_month = datetime(self.year + 1, 1, 1)
            else:
                next_month = datetime(self.year, self.month + 1, 1)

            last_day_of_month = next_month - timedelta(days=1)
            days_remaining = (last_day_of_month - today).days + 1  # Include today

            if days_remaining > 0:
                return variable_remaining / days_remaining
            else:
                return 0.0
        else:
            # For past/future months, use average per day
            if self.month == 12:
                next_month = datetime(self.year + 1, 1, 1)
            else:
                next_month = datetime(self.year, self.month + 1, 1)

            last_day = next_month - timedelta(days=1)
            days_in_month = last_day.day

            variable_budget = spend_data['variable_budget']
            return variable_budget / days_in_month if days_in_month > 0 else 0.0

    def render_control_panel(self):
        """Renders the complete control metrics panel"""
        st.markdown("### CONTROLE GASTOS")

        # Calculate all metrics
        a_pagar_total, a_pagar_items = self.calculate_a_pagar()
        a_entrar_total, a_entrar_items = self.calculate_a_entrar()
        days_to_close = self.calculate_days_to_closing()
        spend_data = self.calculate_current_spend()
        daily_rec = self.calculate_recommended_daily_spend()

        # Layout: 2 rows x 3 columns
        row1_col1, row1_col2, row1_col3 = st.columns(3)
        row2_col1, row2_col2, row2_col3 = st.columns(3)

        def _control_metric(label, value, subtitle="", color="#6b7280"):
            return f"""
            <div style="background: white; padding: 14px; border-radius: 8px; border: 1px solid #e5e7eb; text-align: center;">
                <div style="font-size: 0.7rem; color: #9ca3af; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 4px;">{label}</div>
                <div style="font-size: 1.6rem; font-weight: 800; color: {color};">{value}</div>
                {f'<div style="font-size: 0.65rem; color: #9ca3af; margin-top: 2px;">{subtitle}</div>' if subtitle else ''}
            </div>
            """

        with row1_col1:
            st.markdown(_control_metric(
                "A PAGAR",
                f"R$ {a_pagar_total:,.0f}",
                f"{len(a_pagar_items)} itens pendentes",
                "#dc2626"
            ), unsafe_allow_html=True)

        with row1_col2:
            st.markdown(_control_metric(
                "A ENTRAR",
                f"R$ {a_entrar_total:,.0f}",
                f"{len(a_entrar_items)} receitas pendentes",
                "#16a34a"
            ), unsafe_allow_html=True)

        with row1_col3:
            st.markdown(_control_metric(
                "GASTO MAX ATUAL",
                f"R$ {spend_data['total_spent']:,.0f}",
                f"de R$ {spend_data['fixed_budget'] + spend_data['variable_budget']:,.0f}",
                "#ea580c"
            ), unsafe_allow_html=True)

        with row2_col1:
            st.markdown(_control_metric(
                "PRÓXIMO FECHAMENTO",
                f"{days_to_close} dias",
                "até o fechamento",
                "#6366f1"
            ), unsafe_allow_html=True)

        with row2_col2:
            st.markdown(_control_metric(
                "GASTO DIÁRIO RECOMENDADO",
                f"R$ {daily_rec:,.0f}",
                "gastos variáveis",
                "#10b981"
            ), unsafe_allow_html=True)

        with row2_col3:
            # Additional metric: Budget health
            fixed_pct = (spend_data['fixed_spent'] / spend_data['fixed_budget'] * 100) if spend_data['fixed_budget'] > 0 else 0
            variable_pct = (spend_data['variable_spent'] / spend_data['variable_budget'] * 100) if spend_data['variable_budget'] > 0 else 0

            health_color = "#16a34a" if variable_pct < 100 else "#dc2626"
            st.markdown(_control_metric(
                "SAÚDE ORÇAMENTO",
                f"{variable_pct:.0f}%",
                "variável usado",
                health_color
            ), unsafe_allow_html=True)

        # Expandable details - REMOVED per user request
        # User requested removal of "[Detalhes] Detalhes A PAGAR" and "[Receitas] Detalhes A ENTRAR" menus
        st.markdown("---")

def render_control_metrics(month_df, dl_instance, month_str):
    """Main function to render control metrics panel"""
    controller = ControlMetrics(month_df, dl_instance, month_str)
    controller.render_control_panel()
