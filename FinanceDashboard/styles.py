def apply_custom_styles():
    return """
    <style>
        /* Import Fonts */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

        /* Light Theme Variables */
        :root {
            --bg-color: #f3f4f6;
            --card-bg: #ffffff;
            --text-primary: #111827;
            --text-secondary: #6b7280;
            --accent-color: #2563eb; /* Royal Blue */
            --border-color: #e5e7eb;
            --success-bg: #dcfce7;
            --success-text: #166534;
            --danger-bg: #fee2e2;
            --danger-text: #991b1b;
            --border-radius: 12px;
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

        /* Tabs */
        .stTabs [data-baseweb="tab-list"] {
            gap: 24px;
            background-color: var(--card-bg);
            padding: 8px 16px;
            border-radius: var(--border-radius);
            box-shadow: 0 1px 2px rgba(0,0,0,0.05);
            margin-bottom: 24px;
        }

        .stTabs [data-baseweb="tab"] {
            background-color: transparent !important;
            height: auto;
            border: none;
            color: var(--text-secondary);
            font-weight: 500;
            padding-bottom: 12px;
        }

        .stTabs [aria-selected="true"] {
            color: var(--accent-color) !important;
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
