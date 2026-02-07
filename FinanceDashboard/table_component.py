"""
VaultTable - Standardized OOP table component for consistent grid behavior.

This class wraps st_aggrid's AgGrid with standardized functionality:
- Sortable columns (click headers)
- Global search box filtering
- Multi-select with checkboxes
- Fixed column widths with flex support
- Row hover highlighting
- Color-coded amounts (positive/negative/warning)
- Empty state handling with action prompts
"""

import streamlit as st
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, JsCode


class VaultTable:
    """
    Standardized table component that wraps AG Grid with consistent behavior
    across all dashboard tables.

    Usage:
        table = VaultTable(dataframe)
        table.configure_column("Amount", numeric=True, color_amounts=True)
        table.configure_selection(mode='multiple')
        result = table.render(key="my_table")
    """

    def __init__(self, dataframe, key="table", empty_message="No data to display.",
                 show_checkbox=True, show_actions=False):
        """
        Initialize VaultTable with a DataFrame.

        Args:
            dataframe: pandas DataFrame to display
            key: Unique key for the table component
            empty_message: Message to show when DataFrame is empty
            show_checkbox: Show selection checkboxes
            show_actions: Show three-dot action menu column
        """
        self.df = dataframe
        self.key = key
        self.empty_message = empty_message
        self.show_checkbox = show_checkbox
        self.show_actions = show_actions
        self.gb = None
        self.selection_mode = None
        self.height = 400
        self.enable_search = True

        if not self.df.empty:
            self.gb = GridOptionsBuilder.from_dataframe(self.df)
            # Enable sorting on all columns by default
            self.gb.configure_default_column(sortable=True, filterable=True)
            # Auto height for better UX
            self.gb.configure_grid_options(domLayout='autoHeight')

    def configure_column(self, field, header_name=None, width=None, flex=None,
                        numeric=False, editable=False, hide=False, pinned=None,
                        color_amounts=False, cell_style=None, min_width=None):
        """
        Configure a specific column with display and behavior options.

        Args:
            field: Column name in DataFrame
            header_name: Display name for column header
            width: Fixed width in pixels
            flex: Flex ratio (columns share available space proportionally)
            numeric: Format as numeric with 2 decimal places
            editable: Allow cell editing
            hide: Hide column from display
            pinned: Pin column to 'left' or 'right'
            color_amounts: Apply semantic color coding (positive=green, negative=red)
            cell_style: Custom JsCode or dict for cell styling
            min_width: Minimum width in pixels
        """
        if self.gb is None:
            return

        config = {
            'editable': editable,
            'hide': hide
        }

        if header_name:
            config['headerName'] = header_name

        if width:
            config['width'] = width

        if flex:
            config['flex'] = flex

        if min_width:
            config['minWidth'] = min_width

        if pinned:
            config['pinned'] = pinned

        if numeric:
            config['type'] = ['numericColumn']
            config['precision'] = 2

        # Color-coded amounts (semantic colors from design system)
        if color_amounts:
            amount_style_js = JsCode("""
            function(params) {
                if (params.value === null || params.value === undefined) return {};
                const val = parseFloat(params.value);
                if (val > 0) {
                    return {
                        'color': '#16a34a',  // var(--color-positive)
                        'fontWeight': '600'
                    };
                } else if (val < 0) {
                    return {
                        'color': '#dc2626',  // var(--color-negative)
                        'fontWeight': '600'
                    };
                }
                return {'color': '#6b7280'};  // var(--color-neutral)
            }
            """)
            config['cellStyle'] = amount_style_js
        elif cell_style:
            config['cellStyle'] = cell_style

        self.gb.configure_column(field, **config)

    def configure_selection(self, mode='single', use_checkbox=True):
        """
        Configure row selection behavior.

        Args:
            mode: 'single', 'multiple', or None to disable selection
            use_checkbox: Show checkbox column for multi-select
        """
        if self.gb is None:
            return

        self.selection_mode = mode

        if mode:
            self.gb.configure_selection(
                selection_mode=mode,
                use_checkbox=use_checkbox,
                rowMultiSelectWithClick=(mode == 'multiple')
            )

    def configure_search(self, enabled=True):
        """
        Enable or disable global search box.

        Args:
            enabled: Show search box above table
        """
        self.enable_search = enabled

    def configure_height(self, height=None, auto_height=True):
        """
        Configure table height behavior.

        Args:
            height: Fixed height in pixels (overrides auto_height)
            auto_height: Automatically adjust height to fit content
        """
        if height:
            self.height = height
            if self.gb:
                self.gb.configure_grid_options(domLayout='normal')
        elif auto_height and self.gb:
            self.height = None
            self.gb.configure_grid_options(domLayout='autoHeight')

    def configure_status_badge(self, field, status_map=None):
        """
        Configure a column to display status badges with semantic colors.

        Args:
            field: Column name
            status_map: Dict mapping status values to color schemes
                       Default handles common patterns: Pago, Faltando, Parcial
        """
        if self.gb is None:
            return

        # Default status styling matching design system
        default_map = {
            'Pago': {'bg': '#dcfce7', 'color': '#166534'},      # Success
            'Faltando': {'bg': '#fee2e2', 'color': '#991b1b'},  # Danger
            'Parcial': {'bg': '#fef9c3', 'color': '#854d0e'},   # Warning
        }

        status_map = status_map or default_map

        # Build JavaScript for dynamic styling
        status_js = JsCode("""
        function(params) {
            const statusMap = """ + str(status_map).replace("'", '"') + """;
            const status = params.value;
            const style = statusMap[status];

            if (style) {
                return {
                    'backgroundColor': style.bg,
                    'color': style.color,
                    'borderRadius': '4px',
                    'textAlign': 'center',
                    'fontWeight': '600',
                    'padding': '4px 8px'
                };
            }
            return {'color': '#6b7280', 'backgroundColor': '#f3f4f6'};
        }
        """)

        self.gb.configure_column(field, cellStyle=status_js)

    def configure_date_column(self, field, format='DD/MM/YYYY'):
        """
        Configure a date column with proper formatting.

        Args:
            field: Column name
            format: Date format string (default Brazilian format)
        """
        if self.gb is None:
            return

        date_formatter = JsCode(f"""
        function(params) {{
            if (!params.value) return '';
            const date = new Date(params.value);
            return date.toLocaleDateString('pt-BR');
        }}
        """)

        self.gb.configure_column(
            field,
            type=['dateColumn'],
            valueFormatter=date_formatter
        )

    def render(self, key, theme='alpine', fit_columns=True,
               update_mode=GridUpdateMode.SELECTION_CHANGED | GridUpdateMode.VALUE_CHANGED):
        """
        Render the configured table.

        Args:
            key: Unique key for Streamlit component (required)
            theme: AG Grid theme ('alpine' for clean light theme)
            fit_columns: Automatically fit columns to container width
            update_mode: When to trigger updates (selection, value changes, etc.)

        Returns:
            AgGrid response object with selection and data
        """
        # Handle empty state
        if self.df.empty:
            st.info(self.empty_message)
            return None

        # Add search box if enabled
        if self.enable_search and len(self.df) > 5:
            st.markdown("**🔍 Search:**")
            search_query = st.text_input(
                "Search across all columns",
                key=f"{key}_search",
                placeholder="Type to filter rows...",
                label_visibility="collapsed"
            )

            # Filter dataframe based on search
            if search_query:
                mask = self.df.astype(str).apply(
                    lambda row: row.str.contains(search_query, case=False, na=False).any(),
                    axis=1
                )
                filtered_df = self.df[mask]

                if filtered_df.empty:
                    st.warning(f"No results found for '{search_query}'")
                    return None

                # Rebuild GridOptionsBuilder with filtered data
                self.gb = GridOptionsBuilder.from_dataframe(filtered_df)
                self.gb.configure_default_column(sortable=True, filterable=True)

                # Re-apply selection if configured
                if self.selection_mode:
                    self.gb.configure_selection(
                        selection_mode=self.selection_mode,
                        use_checkbox=(self.selection_mode == 'multiple')
                    )
            else:
                filtered_df = self.df
        else:
            filtered_df = self.df

        # Add action column if enabled
        self._add_action_column()

        # Render AG Grid
        grid_options = self.gb.build()

        grid_response = AgGrid(
            filtered_df,
            gridOptions=grid_options,
            height=self.height,
            width='100%',
            fit_columns_on_grid_load=fit_columns,
            allow_unsafe_jscode=True,
            key=key,
            update_mode=update_mode,
            theme=theme,
            enable_enterprise_modules=False
        )

        return grid_response

    def get_selected_rows(self, grid_response):
        """
        Extract selected rows from grid response.

        Args:
            grid_response: Response object from render()

        Returns:
            DataFrame of selected rows, or empty DataFrame if none selected
        """
        if grid_response is None:
            return pd.DataFrame()

        selected = grid_response.get('selected_rows', [])

        if selected:
            return pd.DataFrame(selected)

        return pd.DataFrame()

    def _add_action_column(self):
        """Add three-dot action menu column."""
        if not self.show_actions or self.gb is None:
            return

        # Add _actions column to dataframe if not present
        if '_actions' not in self.df.columns:
            self.df = self.df.copy()
            self.df['_actions'] = ''

        # AG Grid action menu using custom cell renderer
        action_renderer = JsCode("""
        class ActionRenderer {
            init(params) {
                this.params = params;
                this.eGui = document.createElement('div');
                this.eGui.innerHTML = `
                    <button class="action-btn" style="
                        background: none;
                        border: none;
                        cursor: pointer;
                        font-size: 18px;
                        padding: 4px 8px;
                        color: #6b7280;
                    " title="Actions">&#8942;</button>
                `;
            }
            getGui() { return this.eGui; }
        }
        """)

        self.gb.configure_column(
            '_actions',
            headerName='',
            width=50,
            cellRenderer=action_renderer,
            pinned='right',
            suppressMenu=True,
            sortable=False
        )

    def render_with_export(self, key=None):
        """
        Render table with export button above.

        Args:
            key: Optional key override for the table

        Returns:
            AgGrid response object
        """
        render_key = key or self.key

        # Handle empty state
        if self.df.empty:
            st.info(self.empty_message)
            return None

        col1, col2 = st.columns([4, 1])

        with col2:
            csv = self.df.to_csv(index=False)
            st.download_button(
                label="Export CSV",
                data=csv,
                file_name=f"{render_key}_export.csv",
                mime="text/csv",
                key=f"{render_key}_download"
            )

        return self.render(key=render_key)

    def _export_csv(self):
        """Export current dataframe to CSV download."""
        csv = self.df.to_csv(index=False)
        st.download_button(
            label="Download",
            data=csv,
            file_name=f"{self.key}_export.csv",
            mime="text/csv",
            key=f"{self.key}_download"
        )


# Convenience factory functions for common table patterns

def create_transaction_table(df, key):
    """
    Factory function for transaction tables with common configuration.

    Args:
        df: Transaction DataFrame
        key: Unique key for table

    Returns:
        Configured VaultTable instance
    """
    table = VaultTable(df, empty_message="No transactions to display.")

    # Configure columns
    if 'date' in df.columns:
        table.configure_date_column('date')
        table.configure_column('date', header_name='DATA', width=110, pinned='left')

    if 'description' in df.columns:
        table.configure_column('description', header_name='DESCRIÇÃO', flex=3, editable=True)

    if 'category' in df.columns:
        table.configure_column('category', header_name='CATEGORIA', width=140, editable=True)

    if 'subcategory' in df.columns:
        table.configure_column('subcategory', header_name='SUBCATEGORIA', width=140, editable=True)

    if 'amount' in df.columns:
        table.configure_column('amount', header_name='VALOR', numeric=True,
                              color_amounts=True, width=130)

    if 'account' in df.columns:
        table.configure_column('account', header_name='CONTA', width=150)

    # Enable multi-select
    table.configure_selection(mode='multiple', use_checkbox=True)

    return table


def create_recurring_table(df, key):
    """
    Factory function for recurring items table (Fixo/Recorrentes).

    Args:
        df: Recurring items DataFrame
        key: Unique key for table

    Returns:
        Configured VaultTable instance
    """
    table = VaultTable(df, empty_message="Nenhum item recorrente.")

    # Configure columns based on expected schema
    if 'Due' in df.columns:
        table.configure_column('Due', header_name='DATA', width=70)

    if 'Item' in df.columns:
        table.configure_column('Item', header_name='DESCRIÇÃO', flex=2)

    if 'Expected' in df.columns:
        table.configure_column('Expected', header_name='VALOR', numeric=True,
                              editable=True, flex=1)

    if 'Status' in df.columns:
        table.configure_status_badge('Status')
        table.configure_column('Status', header_name='STATUS', flex=1)

    if 'Suggested Match' in df.columns:
        table.configure_column('Suggested Match', header_name='TRANSAÇÃO MAPEADA',
                              flex=3, cell_style={'fontStyle': 'italic', 'color': '#4b5563'})

    # Hide internal columns
    for col in ['Renamed', 'Original', 'Source', 'Actual', '_raw_match']:
        if col in df.columns:
            table.configure_column(col, hide=True)

    # Single selection for recurring items
    table.configure_selection(mode='single')
    table.configure_height(height=400, auto_height=False)

    return table


def create_cards_table(df, key):
    """
    Factory function for credit card transactions table.

    Args:
        df: Card transactions DataFrame
        key: Unique key for table

    Returns:
        Configured VaultTable instance
    """
    import re

    # Extract installment info
    df = df.copy()

    def extract_parcela(desc):
        m = re.search(r'(\d{1,2}/\d{1,2})', str(desc))
        return m.group(1) if m else "-"

    if 'description' in df.columns:
        df['Parcela'] = df['description'].apply(extract_parcela)

    table = VaultTable(df, empty_message="Sem transações de cartão.")

    # Configure columns
    if 'date' in df.columns:
        table.configure_date_column('date')
        table.configure_column('date', header_name='DATA', width=110, pinned='left')

    if 'account' in df.columns:
        table.configure_column('account', header_name='CARTÃO', width=150)

    if 'category' in df.columns:
        table.configure_column('category', header_name='CATEGORIA', width=140, editable=True)

    if 'subcategory' in df.columns:
        table.configure_column('subcategory', header_name='SUBCATEGORIA', width=140, editable=True)

    if 'description' in df.columns:
        table.configure_column('description', header_name='DESCRIÇÃO', flex=3,
                              min_width=250, editable=True)

    if 'amount' in df.columns:
        table.configure_column('amount', header_name='VALOR', numeric=True, width=130)

    if 'Parcela' in df.columns:
        parcela_style = JsCode("""
        function(params) {
            return {
                'textAlign': 'center',
                'fontWeight': 'bold',
                'color': '#ea580c'  // var(--color-warning)
            };
        }
        """)
        table.configure_column('Parcela', header_name='PARCELA', width=100,
                              cell_style=parcela_style)

    # Hide internal/metadata columns that shouldn't be user-facing
    visible_cols = {'date', 'description', 'amount', 'account', 'category', 'subcategory', 'Parcela'}
    for col in df.columns:
        if col not in visible_cols:
            table.configure_column(col, hide=True)

    # Multi-select with sidebar for filtering
    table.configure_selection(mode='multiple', use_checkbox=True)
    table.configure_height(height=500, auto_height=False)

    return table
