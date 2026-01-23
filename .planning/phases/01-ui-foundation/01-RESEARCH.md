# Phase 1: UI Foundation - Research

**Researched:** 2026-01-23
**Domain:** Streamlit dashboard UI with AG Grid interactive tables
**Confidence:** MEDIUM

## Summary

This research investigated the standard architecture and patterns for building modern, consistent UIs in Streamlit using AG Grid (st-aggrid) for interactive tables with inline editing, dropdown cells, and tab-based navigation.

**Key findings:**
- st-aggrid v1.2.0 wraps AG Grid 34.3.1, providing access to enterprise-grade table features through GridOptionsBuilder patterns
- Streamlit's st.tabs() supports nested tabs for hierarchical navigation (Settings > Categories, Rules, etc.)
- AG Grid's Rich Select Cell Editor provides built-in dropdown-in-cell with search, filtering, and async data loading
- Component standardization requires OOP patterns with separate class modules to survive Streamlit's rerun model
- Critical pitfall: Streamlit reruns entire script on interaction, requiring strategic use of st.session_state and @st.cache_data

**Primary recommendation:** Use GridOptionsBuilder pattern for standardized table components, leverage AG Grid's built-in cell editors instead of custom solutions, structure tab content with nested st.tabs(), and isolate component classes in separate modules to prevent rerun issues.

## Standard Stack

The established libraries/tools for Streamlit + AG Grid dashboards:

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| streamlit | Latest (1.50.0+) | Dashboard framework | Official framework with native st.tabs, st.session_state, st.download_button |
| streamlit-aggrid (st-aggrid) | 1.2.0 | AG Grid wrapper | Only mature Streamlit wrapper for AG Grid, wraps AG Grid 34.3.1 with Python API |
| pandas | Latest | Data manipulation | Required by both Streamlit and st-aggrid for DataFrame operations |
| plotly | Latest | Charts/visualizations | Standard Streamlit charting library, integrates seamlessly |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| openpyxl | Latest | Excel file handling | Already in requirements.txt for import/export |
| watchdog | Latest | File watching | Already in requirements.txt for auto-reload |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| st-aggrid | st.data_editor (native) | st.data_editor is improving fast (2025 updates), less buggy, but lacks AG Grid's enterprise features (rich select editor, column tool panel, advanced filtering). Use st.data_editor for simple tables, st-aggrid for complex interactions. |
| st.tabs | streamlit-option-menu | Custom component with more styling but adds dependency and maintenance burden. Native st.tabs sufficient for this use case. |

**Installation:**
```bash
pip install streamlit pandas plotly streamlit-aggrid openpyxl watchdog
```

**Note:** st-aggrid 1.2.0 wraps AG Grid Community Edition. Enterprise features (Column Tool Panel, Rich Select Editor in some cases) require AG Grid Enterprise license.

## Architecture Patterns

### Recommended Project Structure
```
FinanceDashboard/
├── dashboard.py              # Main app entry point (tabs, navigation)
├── components/
│   ├── __init__.py
│   ├── base_grid.py         # Standardized GridComponent base class
│   ├── transaction_grid.py  # TransactionGrid(GridComponent)
│   ├── recurrent_grid.py    # RecurrentGrid(GridComponent)
│   └── ...                  # Other grid implementations
├── ui/
│   ├── __init__.py
│   ├── tabs.py              # Tab rendering functions
│   └── widgets.py           # Reusable UI widgets (month picker, etc.)
├── styles.py                # CSS injection via st.markdown
├── utils.py                 # Pure functions (no classes)
└── DataLoader.py            # Existing data loading
```

**Why this structure:**
- Classes in separate modules survive Streamlit reruns without redefinition
- Component standardization through inheritance (base_grid.py)
- Clear separation: UI (tabs.py, widgets.py) vs. Logic (utils.py) vs. Components (components/)

### Pattern 1: Standardized Grid Component (OOP)
**What:** Base class for all AG Grid tables with consistent configuration
**When to use:** Every table/grid in the dashboard
**Example:**
```python
# Source: Streamlit custom classes best practices
# https://docs.streamlit.io/develop/concepts/design/custom-classes

# components/base_grid.py
from st_aggrid import AgGrid, GridOptionsBuilder
from abc import ABC, abstractmethod
import pandas as pd

class GridComponent(ABC):
    """Base class for all AG Grid tables in the dashboard."""

    def __init__(self, df: pd.DataFrame, key: str):
        self.df = df
        self.key = key
        self.gb = GridOptionsBuilder.from_dataframe(df)
        self._configure_base()

    def _configure_base(self):
        """Apply standard configurations to all grids."""
        # Sorting: all columns sortable
        self.gb.configure_default_column(sortable=True, resizable=False)

        # Selection: multi-select with checkboxes
        self.gb.configure_selection(
            selection_mode='multiple',
            use_checkbox=True,
            header_checkbox=True
        )

        # Pagination: infinite scroll (AG Grid handles via DOM virtualization)
        # No explicit pagination config needed

        # Quick filter: global search
        self.gb.configure_grid_options(
            quickFilterText='',
            cacheQuickFilter=True  # Performance optimization
        )

    @abstractmethod
    def configure_columns(self):
        """Subclasses implement column-specific config."""
        pass

    def render(self):
        """Render the grid with standard return mode."""
        self.configure_columns()
        grid_options = self.gb.build()

        return AgGrid(
            self.df,
            gridOptions=grid_options,
            key=self.key,
            reload_data=False,  # Performance: only reload on explicit data change
            update_mode='MODEL_CHANGED',
            allow_unsafe_jscode=True  # Required for custom cell renderers
        )

# components/transaction_grid.py
class TransactionGrid(GridComponent):
    """Transaction table with inline dropdowns and row actions."""

    def configure_columns(self):
        # Category column with Rich Select Editor (dropdown with search)
        self.gb.configure_column(
            'category',
            editable=True,
            cellEditor='agRichSelectCellEditor',
            cellEditorParams={
                'values': self._get_categories(),
                'allowTyping': True,
                'filterList': True,
                'searchType': 'matchAny'
            }
        )

        # Amount column with color formatting
        self.gb.configure_column(
            'amount',
            cellStyle={
                'color': 'expr: params.value > 0 ? "green" : "red"'
            }
        )

        # Fixed column widths
        self.gb.configure_column('date', width=120, suppressSizeToFit=True)
        self.gb.configure_column('name', width=300, suppressSizeToFit=True)

    def _get_categories(self):
        # Return list of category options
        return ['Food', 'Transport', 'Entertainment', ...]
```

**Critical:** Classes must be in separate files, not in dashboard.py, to avoid redefinition on every Streamlit rerun.

### Pattern 2: Tab-Based Navigation with Nested Tabs
**What:** Main tabs (Overview, Analytics, Settings) with nested sub-tabs in Settings
**When to use:** Phase 1 navigation structure
**Example:**
```python
# Source: Streamlit nested tabs pattern
# https://discuss.streamlit.io/t/can-i-create-tabs-inside-a-tab-on-streamlit/53751

# dashboard.py
import streamlit as st

# Main tabs
main_tabs = st.tabs(["Monthly Overview", "Analytics", "Settings"])

with main_tabs[0]:  # Monthly Overview
    # Month picker (only in this tab)
    selected_month = st.selectbox(
        "Month",
        options=available_months,
        key='month_picker'
    )

    # Render dashboard content
    render_vault_summary(filtered_data)
    render_transaction_grid(filtered_data)

with main_tabs[1]:  # Analytics
    # No month picker - all-time data
    render_analytics_dashboard(all_data)

with main_tabs[2]:  # Settings
    # Nested tabs for sub-navigation
    settings_tabs = st.tabs([
        "Categories",
        "Rules",
        "Budgets",
        "Recurrents",
        "Import"
    ])

    with settings_tabs[0]:  # Categories
        render_category_management()

    with settings_tabs[1]:  # Rules
        render_rules_config()

    # ... etc.
```

**Important:** All tab content is computed and sent to frontend regardless of which tab is selected. For heavy computations, use conditional rendering based on session state instead.

### Pattern 3: Inline Dropdown with Rich Select Cell Editor
**What:** AG Grid's built-in dropdown cell editor with search/filter
**When to use:** Category, subcategory, recurrent assignment columns
**Example:**
```python
# Source: AG Grid Rich Select Cell Editor
# https://www.ag-grid.com/javascript-data-grid/provided-cell-editors-rich-select/

# Dropdown with search and grouping
cellEditorParams = {
    'values': ['Option 1', 'Option 2', 'Option 3'],
    'allowTyping': True,           # Enable search
    'filterList': True,             # Enable filtering
    'highlightMatch': True,         # Highlight matching text
    'searchType': 'matchAny',       # Substring matching
    'multiSelect': False,           # Single selection
    # For async data loading:
    # 'values': fetch_categories_callback,
    # 'filterListAsync': True,
    # 'searchDebounceDelay': 300
}

# Configure column
gb.configure_column(
    'category',
    editable=True,
    cellEditor='agRichSelectCellEditor',
    cellEditorParams=cellEditorParams
)
```

**Keyboard navigation (built-in):**
- Arrow keys to navigate options
- Enter to select
- Escape to dismiss
- Search by typing

### Pattern 4: Session State for Widget Keys
**What:** Consistent widget key naming and session state integration
**When to use:** All widgets that need to persist state across reruns
**Example:**
```python
# Source: Streamlit widget behavior
# https://docs.streamlit.io/develop/concepts/architecture/widget-behavior

# Initialize session state
if 'selected_month' not in st.session_state:
    st.session_state.selected_month = default_month

# Widget with key mirrors session state
month = st.selectbox(
    "Month",
    options=months,
    key='selected_month'  # Auto-syncs with st.session_state.selected_month
)

# Access value from session state
current_month = st.session_state.selected_month
```

### Pattern 5: CSV Export with st.download_button
**What:** Native Streamlit CSV export pattern
**When to use:** Export current table view
**Example:**
```python
# Source: Streamlit download button
# https://docs.streamlit.io/knowledge-base/using-streamlit/how-download-pandas-dataframe-csv

@st.cache_data
def convert_df_to_csv(df):
    return df.to_csv(index=False).encode('utf-8')

csv_data = convert_df_to_csv(filtered_df)

st.download_button(
    label="📥 Export CSV",
    data=csv_data,
    file_name=f"transactions_{selected_month}.csv",
    mime="text/csv",
    key='download_csv'
)
```

### Anti-Patterns to Avoid

- **Defining classes in dashboard.py:** Classes redefined on every rerun cause instance comparison failures. Always use separate modules.
- **Overusing session state:** Not every variable needs session state. Use for widget values and user-specific state only.
- **Expensive computations in tab content:** Since all tabs render on every rerun, use @st.cache_data for heavy operations.
- **Global variables:** Streamlit reruns from scratch. Use session state or module-level constants only.
- **Custom cell editors without necessity:** AG Grid's Rich Select Cell Editor covers 90% of dropdown needs. Don't build custom unless required.

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Dropdown in table cell | Custom cell renderer with HTML select | AG Grid Rich Select Cell Editor (`agRichSelectCellEditor`) | Built-in search, filtering, async loading, keyboard navigation, proper event handling |
| Global search across table | Custom filter logic with text input | AG Grid Quick Filter (`quickFilterText` grid option) | Optimized with caching, splits words, case-insensitive, works with column filters |
| Column show/hide UI | Custom checkbox list | AG Grid Column Tool Panel (Enterprise) or column visibility API | Drag-drop column reordering, grouping, built-in UI |
| Row selection tracking | Custom checkbox column + state | AG Grid row selection (`configure_selection`) | Multi-select, range select with Shift, header checkbox, API for getting selected rows |
| CSV export | Manual CSV generation with Python csv module | `st.download_button` + `df.to_csv()` with @st.cache_data | Handles encoding, MIME types, caching, download triggers |
| Infinite scroll in tables | Custom pagination with page tracking | AG Grid DOM row virtualization (default) | Renders only visible rows, handles thousands of rows efficiently |
| Color-coded amounts | Custom HTML in cells with st.markdown | AG Grid cellStyle with conditional expressions | Performant, works with sorting/filtering, consistent styling |
| Month filtering | Custom date range logic | Pandas date filtering + st.selectbox for month | Leverage pandas dt.strftime for month strings, native performance |
| Tab state persistence | Custom session state tracking | Streamlit native behavior (no persistence needed per requirements) | User wants fresh start on session, no persistence = simpler code |

**Key insight:** AG Grid is a mature enterprise grid with 10+ years of edge case handling. Features like dropdown editors, keyboard navigation, and accessibility are production-tested. Custom solutions will hit edge cases (keyboard traps, screen reader issues, mobile touch events, etc.).

## Common Pitfalls

### Pitfall 1: Streamlit Rerun Model Breaking Component State
**What goes wrong:** Custom components or classes defined in main script lose state across reruns because they're redefined, causing instance comparison failures (e.g., widget value from previous run doesn't match current run's options).
**Why it happens:** Streamlit executes entire script top-to-bottom on every interaction. Python compares object identity, not values, so redefined classes create "different" instances.
**How to avoid:**
- Move all class definitions to separate module files (components/base_grid.py, not dashboard.py)
- Use @st.cache_data for expensive data transformations
- Use @st.cache_resource for persistent resources (database connections, ML models)
- Initialize session state with `if 'key' not in st.session_state:` pattern
**Warning signs:** DuplicateWidgetID errors, widget values resetting unexpectedly, "value not in options" errors

### Pitfall 2: All Tabs Render on Every Interaction
**What goes wrong:** Dashboard becomes slow because all tab content (transaction tables, charts, analytics) computes and renders even when viewing a single tab.
**Why it happens:** Streamlit's st.tabs() doesn't support lazy/conditional rendering. All tabs execute on every rerun per documentation: "All content within every tab is computed and sent to the frontend, regardless of which tab is selected."
**How to avoid:**
- Use @st.cache_data for data loading and transformations
- Use @st.cache_resource for model/resource initialization
- For truly slow tabs, consider st.segmented_control with conditional rendering instead of st.tabs
- Limit tab count (3 main tabs per requirements is reasonable)
**Warning signs:** App slows down as more tabs are added, CPU spikes on tab switch

### Pitfall 3: Widget in Cached Function Memory Explosion
**What goes wrong:** Putting widgets inside @st.cache_data functions causes cache to grow infinitely, eventually crashing with out-of-memory errors.
**Why it happens:** Each widget interaction creates a new cache entry because widget state changes, but cached function sees it as different input.
**How to avoid:** Never put widgets (st.selectbox, st.button, etc.) inside cached functions. Structure: widget → cached function → display result.
**Warning signs:** Memory usage growing over time, cache warnings in console, app becoming slower with use

### Pitfall 4: AG Grid Enterprise Features Without License
**What goes wrong:** Features like Column Tool Panel, Rich Select Cell Editor (in some configurations), and advanced filtering don't work or show license warnings.
**Why it happens:** st-aggrid wraps AG Grid Community by default. Some features are Enterprise-only and disabled unless licensed.
**How to avoid:**
- Check AG Grid documentation for feature availability (Community vs Enterprise)
- For Phase 1: Rich Select Cell Editor is in Community Edition (safe to use)
- Column Tool Panel requires Enterprise (use programmatic column visibility API instead)
- If using Enterprise features, purchase AG Grid license
**Warning signs:** "Enterprise feature" console warnings, features not rendering, grid showing license nag

### Pitfall 5: Session State Widget Conflicts
**What goes wrong:** StreamlitAPIException when trying to modify widget value via session state after widget is instantiated, or warnings about value parameter conflicts.
**Why it happens:** Streamlit restricts modifying widget state after creation to prevent race conditions.
**How to avoid:**
- Don't set widget value via `st.session_state.key = value` after widget exists in current run
- Don't use both `value` parameter and session state `key` for same widget
- Initialize session state before widget creation: `if 'key' not in st.session_state: st.session_state.key = default`
- Use on_change callbacks for widget interactions
**Warning signs:** StreamlitAPIException, warnings about value parameter, widgets not updating

### Pitfall 6: Fixed Column Widths Without suppressSizeToFit
**What goes wrong:** Columns resize unexpectedly despite setting width, especially with sizeColumnsToFit() calls.
**Why it happens:** AG Grid's sizeColumnsToFit() overrides width unless column explicitly opts out.
**How to avoid:**
```python
gb.configure_column(
    'date',
    width=120,
    resizable=False,          # Disable manual resize
    suppressSizeToFit=True    # Ignore auto-fit operations
)
```
**Warning signs:** Column widths not respected, columns stretching to fill space

### Pitfall 7: Quick Filter Performance on Large Datasets
**What goes wrong:** Quick filter (global search) becomes sluggish on datasets with 10,000+ rows.
**Why it happens:** Without caching, Quick Filter concatenates and searches all column values on every keystroke.
**How to avoid:**
```python
gb.configure_grid_options(
    cacheQuickFilter=True,  # Cache concatenated text
    quickFilterText=''      # Initialize with empty string
)
```
**Warning signs:** Typing lag in search box, high CPU on search, slow table updates

## Code Examples

Verified patterns from official sources:

### GridOptionsBuilder Configuration Pattern
```python
# Source: st-aggrid Usage documentation
# https://streamlit-aggrid.readthedocs.io/en/docs/Usage.html

from st_aggrid import AgGrid, GridOptionsBuilder
import pandas as pd

df = pd.DataFrame({
    'date': ['2024-01-01', '2024-01-02'],
    'name': ['Transaction 1', 'Transaction 2'],
    'amount': [100.50, -50.25],
    'category': ['Income', 'Food']
})

# Build grid options
gb = GridOptionsBuilder.from_dataframe(df)

# Configure default for all columns
gb.configure_default_column(
    sortable=True,
    resizable=False,
    filterable=True
)

# Configure specific columns
gb.configure_column(
    'amount',
    type=['numericColumn', 'numberColumnFilter'],
    cellStyle={'textAlign': 'right'}
)

gb.configure_column(
    'category',
    editable=True,
    cellEditor='agRichSelectCellEditor',
    cellEditorParams={
        'values': ['Income', 'Food', 'Transport', 'Entertainment'],
        'allowTyping': True,
        'filterList': True
    }
)

# Selection
gb.configure_selection(
    selection_mode='multiple',
    use_checkbox=True
)

# Build and render
grid_options = gb.build()
grid_response = AgGrid(
    df,
    gridOptions=grid_options,
    update_mode='MODEL_CHANGED',
    reload_data=False,
    key='transactions_grid'
)

# Access edited data
edited_df = grid_response['data']
selected_rows = grid_response['selected_rows']
```

### Color-Coded Amount Display
```python
# Source: AG Grid Cell Styling
# https://www.ag-grid.com/javascript-data-grid/cell-styles/

# Approach 1: Using cellStyle (recommended)
gb.configure_column(
    'amount',
    cellStyle={
        'color': 'expr: params.value > 0 ? "green" : "red"',
        'fontWeight': 'bold'
    },
    valueFormatter='expr: (params.value > 0 ? "+" : "") + params.value.toFixed(2)'
)

# Approach 2: Using Pandas Styler (before AgGrid)
def color_amounts(val):
    color = 'green' if val > 0 else 'red'
    return f'color: {color}'

styled_df = df.style.applymap(color_amounts, subset=['amount'])
```

### Nested Tabs Navigation
```python
# Source: Streamlit nested tabs pattern
# https://discuss.streamlit.io/t/can-i-create-tabs-inside-a-tab-on-streamlit/53751

import streamlit as st

# Main tabs
main_tabs = st.tabs(["Monthly Overview", "Analytics", "Settings"])

with main_tabs[0]:
    st.header("Monthly Overview")
    # Month picker only in this tab
    month = st.selectbox("Month", months, key='month_picker')
    # Dashboard content...

with main_tabs[1]:
    st.header("Analytics")
    # All-time data, no month picker
    # Charts and reports...

with main_tabs[2]:
    st.header("Settings")

    # Nested tabs for Settings sub-sections
    settings_tabs = st.tabs([
        "Categories",
        "Rules",
        "Budgets",
        "Recurrents",
        "Import Settings"
    ])

    with settings_tabs[0]:
        st.subheader("Category Management")
        # Category configuration UI...

    with settings_tabs[1]:
        st.subheader("Categorization Rules")
        # Rules UI...

    with settings_tabs[2]:
        st.subheader("Budget Configuration")
        # Budget UI...

    # ... etc.
```

### Custom CSS Styling Pattern
```python
# Source: Streamlit custom CSS
# https://medium.com/@ericdennis7/beautify-streamlit-with-custom-css-0500b44449cb

# styles.py
def apply_custom_styles():
    return """
    <style>
        /* AG Grid row hover - override default */
        .ag-row-hover {
            background-color: #f0f0f0 !important;
        }

        /* Streamlit tabs styling */
        .stTabs [data-baseweb="tab-list"] {
            gap: 24px;
            background-color: var(--card-bg);
            padding: 8px 16px;
            border-radius: 12px;
            box-shadow: 0 1px 2px rgba(0,0,0,0.05);
            margin-bottom: 24px;
        }

        .stTabs [aria-selected="true"] {
            color: var(--accent-color) !important;
            border-bottom: 2px solid var(--accent-color) !important;
        }

        /* Custom button styling */
        .stButton button {
            border-radius: 8px;
            font-weight: 500;
            transition: transform 0.1s;
        }

        .stButton button:hover {
            transform: translateY(-1px);
        }
    </style>
    """

# dashboard.py
st.markdown(apply_custom_styles(), unsafe_allow_html=True)
```

### Empty State Pattern
```python
# Source: Streamlit st.empty() documentation
# https://docs.streamlit.io/develop/api-reference/layout/st.empty

import streamlit as st

if df.empty:
    # Empty state with call-to-action
    placeholder = st.empty()

    with placeholder.container():
        st.info("📊 No data yet — import transactions to get started")

        if st.button("Import Transactions", key='import_cta'):
            # Trigger import flow
            st.session_state.show_import = True
            placeholder.empty()  # Clear empty state
else:
    # Render normal grid
    AgGrid(df, ...)
```

### Row Actions Menu (Three-Dot Menu)
```python
# Source: AG Grid Cell Renderer patterns
# https://blog.ag-grid.com/creating-popups-in-ag-grid/

# Note: Three-dot menus require custom cell renderer (JavaScript)
# For Streamlit/st-aggrid, recommended approach is buttons in grid

gb.configure_column(
    'actions',
    headerName='',
    width=100,
    cellRenderer='expr: "<button>⋮</button>"',  # Unicode three-dot
    editable=False,
    sortable=False,
    filter=False,
    pinned='right'  # Keep actions visible during scroll
)

# Alternative: Use selection + action buttons above grid
selected_rows = grid_response['selected_rows']

if selected_rows:
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("✏️ Edit", key='edit_action'):
            # Edit selected row
            pass
    with col2:
        if st.button("🗑️ Delete", key='delete_action'):
            # Delete selected rows
            pass
    with col3:
        if st.button("📋 Duplicate", key='duplicate_action'):
            # Duplicate selected row
            pass
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Manual ag-grid JSON config | GridOptionsBuilder from_dataframe | st-aggrid 0.2.0+ (2021) | Cleaner API, less boilerplate, auto-infers column types |
| st.experimental_rerun() | Automatic reruns + session state | Streamlit 1.0 (2021) | More predictable state management, no manual rerun calls |
| Base64 download links | st.download_button | Streamlit 1.4 (2022) | Native download support, simpler code, better UX |
| Custom pagination | AG Grid DOM virtualization | AG Grid 20+ (2019) | Handles 100k+ rows efficiently without custom code |
| JavaScript cell editors | Rich Select Cell Editor | AG Grid 29+ (2023) | Built-in dropdown with search, no custom JS needed |
| st.experimental_memo | @st.cache_data | Streamlit 1.18 (2023) | Clearer caching semantics, better performance |
| Tab state tracking | st.tabs native (no persistence) | Streamlit 1.11 (2022) | Simpler tab implementation, less state management code |
| Custom class serialization | Move classes to modules | Streamlit 1.29+ (2024) | Avoid rerun redefinition, simpler patterns |

**Deprecated/outdated:**
- **@st.cache:** Replaced by @st.cache_data and @st.cache_resource (Streamlit 1.18+). Old decorator causes deprecation warnings.
- **AgGrid reload_data=True default:** Changed to False in st-aggrid 1.0+. True causes unnecessary re-renders and performance issues.
- **Manual column definitions:** GridOptionsBuilder.from_dataframe auto-infers types and reduces boilerplate.
- **Custom HTML downloads:** st.download_button is now standard, safer (no XSS risks), and more accessible.

## Open Questions

Things that couldn't be fully resolved:

1. **AG Grid Enterprise License Requirement**
   - What we know: Column Tool Panel is Enterprise feature, but Rich Select Cell Editor is Community Edition. st-aggrid enables Enterprise features if licensed.
   - What's unclear: Whether user wants to purchase AG Grid Enterprise license for advanced features (Column Tool Panel for show/hide columns vs. programmatic API)
   - Recommendation: Start with Community Edition (free). Implement column visibility via programmatic API (checkboxes above grid). Upgrade to Enterprise only if drag-drop column management becomes critical user need.

2. **st-aggrid vs st.data_editor for Future**
   - What we know: st-aggrid is more feature-rich but buggier and community-maintained. st.data_editor is actively improved by Streamlit team (2025 updates added width, placeholder support).
   - What's unclear: Long-term viability of st-aggrid if Streamlit continues improving st.data_editor
   - Recommendation: Use st-aggrid for Phase 1 (meets requirements for Rich Select Editor, advanced features). Monitor st.data_editor changelog. Consider migration if it adds comparable dropdown cell editor in future.

3. **Custom Three-Dot Row Actions Menu**
   - What we know: True kebab menu (three-dot popup) requires custom cell renderer in JavaScript. st-aggrid supports custom JS via allow_unsafe_jscode=True.
   - What's unclear: Complexity vs. benefit tradeoff. Alternative: selection + action buttons above grid is simpler.
   - Recommendation: Implement selection-based actions first (edit/delete/duplicate buttons appear when rows selected). Defer in-row kebab menu unless user feedback demands it.

4. **Month Picker Implementation**
   - What we know: st.date_input doesn't support month-only selection. Community requests exist but not in core Streamlit.
   - What's unclear: Whether to use st.selectbox with month strings (simple) or custom component (streamlit-date-picker with month mode)
   - Recommendation: Use st.selectbox with month strings formatted as 'YYYY-MM' (simple, reliable, matches existing code pattern in dashboard.py). Custom component adds dependency burden.

5. **Smart/ML-Based Dropdown Suggestions**
   - What we know: User wants ML-based suggestions at top of dropdowns. AG Grid Rich Select Cell Editor supports custom value ordering.
   - What's unclear: Source of ML predictions (separate model? rule-based? existing engine has this?)
   - Recommendation: Phase 1 focus: implement dropdown structure with section headers (Recent, Suggested, All Categories). Phase 2+: integrate ML predictions if model exists, otherwise use frequency-based suggestions (most commonly used categories for user).

## Sources

### Primary (HIGH confidence)
- [st-aggrid Official Documentation](https://streamlit-aggrid.readthedocs.io/en/docs/Usage.html) - GridOptionsBuilder patterns, configuration
- [AG Grid JavaScript Documentation - Rich Select Cell Editor](https://www.ag-grid.com/javascript-data-grid/provided-cell-editors-rich-select/) - Dropdown cell editor configuration
- [AG Grid JavaScript Documentation - Quick Filter](https://www.ag-grid.com/javascript-data-grid/filter-quick/) - Global search implementation
- [Streamlit Official Docs - st.tabs](https://docs.streamlit.io/develop/api-reference/layout/st.tabs) - Tab navigation
- [Streamlit Official Docs - Custom Classes](https://docs.streamlit.io/develop/concepts/design/custom-classes) - OOP patterns and rerun handling
- [Streamlit Official Docs - Widget Behavior](https://docs.streamlit.io/develop/concepts/architecture/widget-behavior) - Widget keys and session state
- [Streamlit Official Docs - Session State](https://docs.streamlit.io/develop/concepts/architecture/session-state) - State management
- [Streamlit Official Docs - How to Download DataFrame as CSV](https://docs.streamlit.io/knowledge-base/using-streamlit/how-download-pandas-dataframe-csv) - Export pattern
- [AG Grid JavaScript Documentation - Row Selection](https://www.ag-grid.com/javascript-data-grid/row-selection-multi-row/) - Multi-select with checkboxes
- [AG Grid JavaScript Documentation - Column Sizing](https://www.ag-grid.com/javascript-data-grid/column-sizing/) - Fixed width configuration
- [AG Grid JavaScript Documentation - Keyboard Navigation](https://www.ag-grid.com/javascript-data-grid/keyboard-navigation/) - Accessibility

### Secondary (MEDIUM confidence)
- [GitHub - streamlit-aggrid](https://github.com/PablocFonseca/streamlit-aggrid) - Current version (1.2.0), maintenance status, known issues
- [Streamlit Community - Nested Tabs Discussion](https://discuss.streamlit.io/t/can-i-create-tabs-inside-a-tab-on-streamlit/53751) - Nested tabs implementation pattern
- [Medium - Beautify Streamlit with Custom CSS](https://medium.com/@ericdennis7/beautify-streamlit-with-custom-css-0500b44449cb) - CSS styling patterns
- [Streamlit Community - Best Practices](https://discuss.streamlit.io/t/streamlit-best-practices/57921) - Anti-patterns and code organization
- [Medium - Best Practices for Streamlit Development](https://medium.com/@jashuamrita360/best-practices-for-streamlit-development-structuring-code-and-managing-session-state-0bdcfb91a745) - State management patterns
- [AG Grid Blog - Creating Popups in AG Grid](https://blog.ag-grid.com/creating-popups-in-ag-grid/) - Row actions menu patterns
- [Streamlit Community - st.data_editor vs st-aggrid](https://discuss.streamlit.io/t/good-looking-table-for-a-streamlit-application-is-anyone-still-using-aggrid/63763) - Component comparison
- [AG Grid JavaScript Documentation - Row Styles](https://www.ag-grid.com/javascript-data-grid/row-styles/) - Row hover styling
- [AG Grid JavaScript Documentation - Column Tool Panel](https://www.ag-grid.com/javascript-data-grid/tool-panel-columns/) - Column visibility (Enterprise)
- [AG Grid JavaScript Documentation - CSV Export](https://www.ag-grid.com/javascript-data-grid/csv-export/) - Export configuration

### Tertiary (LOW confidence)
- [Streamlit Community - Month Picker Requests](https://discuss.streamlit.io/t/month-picker-only/7932) - Month selection workarounds
- [PyPI - streamlit-date-picker](https://pypi.org/project/streamlit-date-picker/) - Custom date picker component
- [Streamlit Community - State Management Advice](https://discuss.streamlit.io/t/seeking-advice-for-streamlit-app-state-management-and-best-practices/80025) - Community opinions

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Official documentation and maintained packages verified
- Architecture: MEDIUM - Patterns verified with official docs, but OOP approach based on community best practices not official Streamlit guidance
- Pitfalls: HIGH - Verified with official documentation and community-reported issues
- AG Grid features: HIGH - Official AG Grid documentation for all features (Rich Select, Quick Filter, Row Selection, etc.)
- st-aggrid integration: MEDIUM - Community package with good documentation but not official Streamlit component

**Research date:** 2026-01-23
**Valid until:** ~30 days (2026-02-23) for stable stack (Streamlit, AG Grid core features); ~7 days for st-aggrid (community package with active development)

**Key assumptions:**
- User has Python 3.13.1 environment (already verified in requirements.txt)
- AG Grid Community Edition features are sufficient (no Enterprise license initially)
- User prefers native Streamlit solutions where available (st.tabs, st.download_button) over custom components
- Performance requirements: tables with <10,000 rows per month (based on typical financial dashboard data volumes)
