import streamlit as st
from typing import List, Dict, Optional, Callable, Union


class InlineDropdown:
    """
    Reusable inline dropdown component for cell-level editing.

    Provides searchable, keyboard-navigable dropdown for inline editing with:
    - Click anywhere in cell to open
    - Search box filters options as user types
    - Keyboard navigation (arrows, Enter, Escape)
    - Grouped options under section headers
    - Clear option (None)
    - Immediate save on selection

    Usage:
        dropdown = InlineDropdown(
            key="category_selector",
            options={"Income": ["Salary", "Bonus"], "Expenses": ["Food", "Rent"]},
            on_select=lambda value: save_to_db(value)
        )
        selected = dropdown.render(current_value="Salary")
    """

    def __init__(
        self,
        key: str,
        options: Union[List[str], Dict[str, List[str]]],
        on_select: Optional[Callable[[Optional[str]], None]] = None,
        placeholder: str = "Select an option...",
        allow_clear: bool = True,
        clear_label: str = "None"
    ):
        """
        Initialize InlineDropdown component.

        Args:
            key: Unique key for the component (required for Streamlit state)
            options: Either a flat list of options or a dict of {group_name: [options]}
            on_select: Callback function to execute when selection is made
            placeholder: Placeholder text for search box
            allow_clear: Whether to show a clear/None option
            clear_label: Label for the clear option (default: "None")
        """
        self.key = key
        self.on_select = on_select
        self.placeholder = placeholder
        self.allow_clear = allow_clear
        self.clear_label = clear_label

        # Normalize options to grouped format
        if isinstance(options, list):
            self.options = {"Options": options}
        else:
            self.options = options

        # Flatten for search/selection
        self.flat_options = []
        for group, items in self.options.items():
            self.flat_options.extend(items)

        # Add clear option if enabled
        if self.allow_clear and self.clear_label not in self.flat_options:
            self.flat_options.insert(0, self.clear_label)

    def render(
        self,
        current_value: Optional[str] = None,
        disabled: bool = False,
        help_text: Optional[str] = None
    ) -> Optional[str]:
        """
        Render the dropdown component.

        Args:
            current_value: Currently selected value
            disabled: Whether the dropdown is disabled
            help_text: Optional help text to display

        Returns:
            Selected value or None
        """
        # Use Streamlit's built-in selectbox with search capability
        # Streamlit selectbox natively supports:
        # - Click to open
        # - Keyboard navigation (arrows, Enter, Escape)
        # - Search/filter by typing

        # Prepare options list
        display_options = self.flat_options.copy()

        # Set default index
        default_index = 0
        if current_value and current_value in display_options:
            default_index = display_options.index(current_value)

        # Render selectbox
        selected = st.selectbox(
            label="",  # No label for inline use
            options=display_options,
            index=default_index,
            key=f"{self.key}_select",
            disabled=disabled,
            help=help_text,
            placeholder=self.placeholder
        )

        # Handle selection change
        if selected != current_value:
            # Convert clear label to None
            result = None if selected == self.clear_label else selected

            # Execute callback
            if self.on_select:
                self.on_select(result)

            return result

        return selected if selected != self.clear_label else None

    def render_grouped(
        self,
        current_value: Optional[str] = None,
        disabled: bool = False,
        help_text: Optional[str] = None
    ) -> Optional[str]:
        """
        Render dropdown with visual group headers (fallback to standard render).

        Note: Streamlit's selectbox doesn't natively support grouped options with
        visible headers, so this falls back to standard rendering with all options.
        For a future enhancement, could use custom component with st-aggrid or HTML.

        Args:
            current_value: Currently selected value
            disabled: Whether the dropdown is disabled
            help_text: Optional help text to display

        Returns:
            Selected value or None
        """
        # For now, use standard render
        # In future, could implement custom HTML component with groups
        return self.render(current_value, disabled, help_text)


def create_category_dropdown(
    key: str,
    budget_categories: Dict[str, dict],
    current_category: Optional[str] = None,
    on_select: Optional[Callable[[Optional[str]], None]] = None
) -> Optional[str]:
    """
    Helper to create category dropdown from budget configuration.

    Groups categories by type (Fixo, Variável, Investimento).

    Args:
        key: Unique key for the dropdown
        budget_categories: Budget dict from CategoryEngine (category -> {type, limit, day})
        current_category: Currently selected category
        on_select: Callback when category is selected

    Returns:
        Selected category or None

    Example:
        selected = create_category_dropdown(
            key="txn_123",
            budget_categories=engine.budget,
            current_category="Alimentação",
            on_select=lambda cat: save_mapping(txn_id, cat)
        )
    """
    # Group categories by type
    grouped = {
        "Fixo": [],
        "Variável": [],
        "Investimento": []
    }

    for category, meta in budget_categories.items():
        cat_type = meta.get('type', 'Variável')
        if cat_type in grouped:
            grouped[cat_type].append(category)

    # Remove empty groups
    grouped = {k: v for k, v in grouped.items() if v}

    # Create dropdown
    dropdown = InlineDropdown(
        key=key,
        options=grouped,
        on_select=on_select,
        placeholder="Select category...",
        allow_clear=True,
        clear_label="Não categorizado"
    )

    return dropdown.render(current_value=current_category)


def create_subcategory_dropdown(
    key: str,
    category: str,
    subcategory_rules: Dict[str, Dict[str, str]],
    current_subcategory: Optional[str] = None,
    on_select: Optional[Callable[[Optional[str]], None]] = None,
    allow_new: bool = True
) -> Optional[str]:
    """
    Helper to create subcategory dropdown for a given category.

    Args:
        key: Unique key for the dropdown
        category: Parent category to get subcategories for
        subcategory_rules: Subcategory rules dict from CategoryEngine
        current_subcategory: Currently selected subcategory
        on_select: Callback when subcategory is selected
        allow_new: Whether to show "(Nova Subcategoria)" option

    Returns:
        Selected subcategory or None

    Example:
        selected = create_subcategory_dropdown(
            key="txn_123_sub",
            category="Alimentação",
            subcategory_rules=engine.subcategory_rules,
            current_subcategory="Restaurantes",
            on_select=lambda sub: save_subcategory(txn_id, sub)
        )
    """
    # Get subcategories for this category
    subcategories = []
    if category in subcategory_rules:
        # Extract unique subcategories from rules
        subcategories = list(set(subcategory_rules[category].values()))

    # Add "new" option if enabled
    if allow_new:
        subcategories.insert(0, "(Nova Subcategoria)")

    # Create dropdown
    dropdown = InlineDropdown(
        key=key,
        options=subcategories if subcategories else ["(None available)"],
        on_select=on_select,
        placeholder="Select subcategory...",
        allow_clear=True,
        clear_label="None"
    )

    return dropdown.render(current_value=current_subcategory)


def create_transaction_dropdown(
    key: str,
    transactions: List[Dict],
    current_transaction_id: Optional[str] = None,
    on_select: Optional[Callable[[Optional[str]], None]] = None,
    format_func: Optional[Callable[[Dict], str]] = None
) -> Optional[str]:
    """
    Helper to create dropdown for selecting from a list of transactions.

    Args:
        key: Unique key for the dropdown
        transactions: List of transaction dicts with 'id', 'description', 'amount', 'date'
        current_transaction_id: Currently selected transaction ID
        on_select: Callback when transaction is selected
        format_func: Custom function to format transaction display

    Returns:
        Selected transaction ID or None

    Example:
        selected = create_transaction_dropdown(
            key="map_to_txn",
            transactions=unmapped_transactions,
            on_select=lambda txn_id: map_recurring_to_transaction(rule_id, txn_id)
        )
    """
    # Default format function
    if format_func is None:
        def format_func(txn):
            date_str = txn.get('date', '').strftime('%d/%m/%Y') if hasattr(txn.get('date'), 'strftime') else str(txn.get('date', ''))
            desc = txn.get('description', 'No description')[:40]
            amount = txn.get('amount', 0)
            return f"{date_str} - {desc} (R$ {amount:,.2f})"

    # Create options dict: {transaction_id: formatted_string}
    options = [format_func(txn) for txn in transactions]
    txn_ids = [txn.get('id', idx) for idx, txn in enumerate(transactions)]

    # Map display strings to IDs
    id_map = dict(zip(options, txn_ids))

    # Find current display value
    current_display = None
    if current_transaction_id:
        for txn in transactions:
            if txn.get('id', None) == current_transaction_id:
                current_display = format_func(txn)
                break

    # Create dropdown
    dropdown = InlineDropdown(
        key=key,
        options=options if options else ["(No transactions available)"],
        on_select=lambda val: on_select(id_map.get(val)) if on_select and val else None,
        placeholder="Select transaction...",
        allow_clear=True,
        clear_label="None"
    )

    selected_display = dropdown.render(current_value=current_display)

    # Return transaction ID
    return id_map.get(selected_display) if selected_display else None
