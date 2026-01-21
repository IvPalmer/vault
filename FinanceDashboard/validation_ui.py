"""
UI Components for displaying validation results
"""
import streamlit as st
import pandas as pd
import json
import os

def render_validation_report(validator):
    """Renders validation report in Streamlit UI"""

    with st.expander("🔍 Data Validation Report", expanded=False):
        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)

        total_checks = len(validator.validation_results)
        passed = len([r for r in validator.validation_results if r['status'] == 'PASS'])
        warnings = len(validator.warnings)
        errors = len(validator.errors)

        col1.metric("Total Checks", total_checks)
        col2.metric("Passed", passed, delta=None if passed == total_checks else f"-{total_checks - passed}")
        col3.metric("Warnings", warnings, delta_color="off")
        col4.metric("Errors", errors, delta_color="inverse")

        # Overall status
        if errors > 0:
            st.error("🔴 VALIDATION FAILED - Please review errors below")
        elif warnings > 0:
            st.warning("🟡 VALIDATION PASSED WITH WARNINGS - Review recommended")
        else:
            st.success("🟢 ALL VALIDATION CHECKS PASSED")

        st.markdown("---")

        # Detailed checks
        st.markdown("### Detailed Validation Results")

        for result in validator.validation_results:
            status = result['status']

            if status == 'PASS':
                icon = "✅"
                color = "#166534"
                bg_color = "#dcfce7"
            elif status == 'WARN':
                icon = "⚠️"
                color = "#854d0e"
                bg_color = "#fef9c3"
            elif status == 'FAIL':
                icon = "❌"
                color = "#991b1b"
                bg_color = "#fee2e2"
            else:
                icon = "⏭️"
                color = "#6b7280"
                bg_color = "#f3f4f6"

            with st.container():
                st.markdown(f"""
                <div style="background: {bg_color}; padding: 12px; border-radius: 6px; margin-bottom: 10px; border-left: 4px solid {color};">
                    <h4 style="margin: 0; color: {color};">{icon} {result['check']}</h4>
                </div>
                """, unsafe_allow_html=True)

                if result.get('details'):
                    for detail in result['details']:
                        st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;{detail}")

        # Errors section
        if errors > 0:
            st.markdown("---")
            st.markdown("### ❌ Errors")
            for error in validator.errors:
                st.error(error)

        # Warnings section
        if warnings > 0:
            st.markdown("---")
            st.markdown("### ⚠️ Warnings")
            for warning in validator.warnings:
                st.warning(warning)

        # Download validation report
        st.markdown("---")
        report_path = os.path.join(os.path.dirname(__file__), "validation_report.json")
        if os.path.exists(report_path):
            with open(report_path, 'r') as f:
                report_json = f.read()

            st.download_button(
                label="📥 Download Validation Report (JSON)",
                data=report_json,
                file_name="validation_report.json",
                mime="application/json"
            )

def render_data_quality_metrics(df):
    """Renders data quality metrics"""

    with st.expander("📊 Data Quality Metrics", expanded=False):
        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown("#### Coverage")
            total = len(df)
            categorized = len(df[df['category'] != 'Uncategorized'])
            subcategorized = len(df[df['subcategory'].notna()])

            st.metric("Total Transactions", f"{total:,}")
            st.metric("Categorized", f"{categorized:,}", f"{categorized/total*100:.1f}%")
            st.metric("Subcategorized", f"{subcategorized:,}", f"{subcategorized/total*100:.1f}%")

        with col2:
            st.markdown("#### Completeness")
            accounts = df['account'].nunique()
            months = df['date'].dt.to_period('M').nunique() if not df.empty else 0
            categories = df['category'].nunique()

            st.metric("Accounts", accounts)
            st.metric("Months", months)
            st.metric("Categories", categories)

        with col3:
            st.markdown("#### Data Health")
            nulls = df.isnull().sum().sum()
            duplicates = df.duplicated().sum()

            income = len(df[df['amount'] > 0])
            expenses = len(df[df['amount'] < 0])

            st.metric("Null Values", nulls, delta_color="inverse")
            st.metric("Duplicates", duplicates, delta_color="inverse")
            st.metric("Income/Expense Ratio", f"{income}/{expenses}")

def render_reconciliation_view(df, dl_instance):
    """Renders account reconciliation view"""

    with st.expander("💰 Account Reconciliation", expanded=False):
        st.markdown("### Monthly Balance by Account")

        if df.empty:
            st.info("No data to reconcile")
            return

        # Calculate monthly totals by account
        df['month_str'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m')

        pivot = df.pivot_table(
            index='month_str',
            columns='account',
            values='amount',
            aggfunc='sum',
            fill_value=0
        ).reset_index()

        # Add total column
        account_cols = [c for c in pivot.columns if c != 'month_str']
        pivot['Total'] = pivot[account_cols].sum(axis=1)

        # Format for display
        for col in account_cols + ['Total']:
            pivot[col] = pivot[col].apply(lambda x: f"R$ {x:,.2f}")

        # Display as dataframe
        st.dataframe(
            pivot,
            use_container_width=True,
            hide_index=True,
            column_config={
                "month_str": st.column_config.TextColumn("Month", width="medium")
            }
        )

        # Show discrepancies if any
        st.markdown("---")
        st.markdown("#### Balance Overrides")
        st.caption("Compare calculated balance vs manually entered balance")

        months = sorted(df['month_str'].unique())
        discrepancies = []

        for month in months:
            month_total = df[df['month_str'] == month]['amount'].sum()
            saved_balance = dl_instance.get_balance_override(month)

            if saved_balance is not None:
                diff = saved_balance - month_total
                if abs(diff) > 0.01:  # More than 1 cent difference
                    discrepancies.append({
                        'Month': month,
                        'Calculated': f"R$ {month_total:,.2f}",
                        'Manual Override': f"R$ {saved_balance:,.2f}",
                        'Difference': f"R$ {diff:,.2f}"
                    })

        if discrepancies:
            st.warning(f"Found {len(discrepancies)} month(s) with balance discrepancies")
            st.dataframe(pd.DataFrame(discrepancies), use_container_width=True, hide_index=True)
        else:
            st.success("✅ No balance discrepancies found")
