def apply_custom_styles():
    return """
    <style>
        /* Import Fonts */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

        /* Design System Tokens */
        :root {
            /* Colors - Base */
            --bg-color: #f3f4f6;
            --card-bg: #ffffff;
            --text-primary: #111827;
            --text-secondary: #6b7280;
            --accent-color: #2563eb; /* Royal Blue */
            --border-color: #e5e7eb;

            /* Colors - Semantic */
            --color-positive: #16a34a;     /* Green - income, success */
            --color-positive-bg: #dcfce7;
            --color-negative: #dc2626;     /* Red - expenses, errors */
            --color-negative-bg: #fee2e2;
            --color-warning: #ea580c;      /* Orange - installments, alerts */
            --color-warning-bg: #ffedd5;
            --color-neutral: #6b7280;      /* Gray - secondary info */
            --color-neutral-bg: #f3f4f6;

            /* Legacy semantic colors (for backward compatibility) */
            --success-bg: #dcfce7;
            --success-text: #166534;
            --danger-bg: #fee2e2;
            --danger-text: #991b1b;

            /* Spacing Scale */
            --spacing-xs: 4px;
            --spacing-sm: 8px;
            --spacing-md: 16px;
            --spacing-lg: 24px;
            --spacing-xl: 32px;
            --spacing-2xl: 48px;

            /* Typography - Font Sizes */
            --font-size-xs: 0.75rem;   /* 12px - labels */
            --font-size-sm: 0.875rem;  /* 14px - secondary text */
            --font-size-base: 1rem;    /* 16px - body */
            --font-size-lg: 1.125rem;  /* 18px - subheadings */
            --font-size-xl: 1.25rem;   /* 20px - section titles */
            --font-size-2xl: 1.5rem;   /* 24px - page titles */
            --font-size-3xl: 2rem;     /* 32px - hero */

            /* Typography - Font Weights */
            --font-weight-normal: 400;
            --font-weight-medium: 500;
            --font-weight-semibold: 600;
            --font-weight-bold: 700;

            /* Typography - Line Heights */
            --line-height-tight: 1.25;
            --line-height-normal: 1.5;
            --line-height-relaxed: 1.75;

            /* Shadows */
            --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.05);
            --shadow-md: 0 4px 6px rgba(0, 0, 0, 0.05);
            --shadow-lg: 0 10px 15px rgba(0, 0, 0, 0.1);

            /* Border Radius */
            --border-radius: 12px;
            --border-radius-sm: 8px;

            /* Font Family */
            --font-main: 'Inter', sans-serif;
        }

        /* Global App Styling */
        .stApp {
            background-color: var(--bg-color);
            font-family: var(--font-main);
            color: var(--text-primary);
        }

        h1, h2, h3, h4 {
            font-family: var(--font-main) !important;
            font-weight: 600;
            color: var(--text-primary);
            letter-spacing: -0.02em;
        }
        
        h1 {
            font-weight: 700;
            background: linear-gradient(135deg, #1e40af 0%, #3b82f6 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        /* Card Styling (Metrics & content containers) */
        .stMetric, .element-container .stMarkdown, .stDataFrame {
            border-radius: var(--border-radius);
        }
        
        .stMetric {
            background-color: var(--card-bg);
            padding: 16px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
            border: 1px solid var(--border-color);
        }

        [data-testid="stMetricValue"] {
            font-size: 1.8rem !important;
            font-weight: 700 !important;
            color: var(--text-primary) !important;
        }
        
        [data-testid="stMetricLabel"] {
            font-size: 0.9rem !important;
            color: var(--text-secondary) !important;
            font-weight: 500 !important;
        }

        /* Tabs - Main Navigation */
        .stTabs [data-baseweb="tab-list"] {
            gap: var(--spacing-xl);
            background-color: var(--card-bg);
            padding: 12px 20px;
            border-radius: var(--border-radius);
            box-shadow: var(--shadow-sm);
            margin-bottom: var(--spacing-lg);
        }

        .stTabs [data-baseweb="tab"] {
            background-color: transparent !important;
            height: auto;
            border: none;
            color: var(--text-secondary);
            font-weight: var(--font-weight-medium);
            font-size: var(--font-size-base);
            padding-bottom: 12px;
            transition: color 0.2s ease;
        }

        .stTabs [data-baseweb="tab"]:hover {
            color: var(--text-primary);
        }

        .stTabs [aria-selected="true"] {
            color: var(--accent-color) !important;
            font-weight: var(--font-weight-semibold) !important;
            border-bottom: 3px solid var(--accent-color) !important;
        }

        /* Nested Tabs (inside main tabs) - visually subordinate */
        .stTabs .stTabs [data-baseweb="tab-list"] {
            gap: var(--spacing-md);
            padding: 6px 12px;
            margin-bottom: var(--spacing-md);
            box-shadow: 0 1px 1px rgba(0,0,0,0.03);
        }

        .stTabs .stTabs [data-baseweb="tab"] {
            font-size: var(--font-size-sm);
            font-weight: var(--font-weight-normal);
            padding-bottom: 8px;
        }

        .stTabs .stTabs [aria-selected="true"] {
            font-weight: var(--font-weight-medium) !important;
            border-bottom: 2px solid var(--accent-color) !important;
        }

        /* Buttons */
        .stButton button {
            border-radius: 8px;
            font-weight: 500;
            border: none;
            box-shadow: 0 1px 2px rgba(0,0,0,0.05);
            transition: transform 0.1s;
        }
        
        .stButton button:hover {
             transform: translateY(-1px);
        }

        /* Dataframe Headers */
        .stDataFrame div[data-testid="stHorizontalBlock"] {
            background: red; 
        }

        div[data-testid="stExpander"] {
            background-color: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: var(--border-radius);
            box-shadow: 0 1px 2px rgba(0,0,0,0.02);
        }
        
        /* Input Fields */
        .stTextInput input, .stNumberInput input, .stSelectbox div[data-baseweb="select"] {
            background-color: var(--card-bg);
            border: 1px solid var(--border-color);
            color: var(--text-primary);
            border-radius: 8px;
        }

    </style>
    """
