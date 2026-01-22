import pandas as pd
from datetime import date
from difflib import get_close_matches

def get_date_filter_strategy():
    """Returns the start filter string (YYYY-MM) for the last 6 months strategy."""
    today = date.today()
    y = today.year
    m = today.month
    
    m_start = m - 6
    y_start = y
    if m_start <= 0:
        m_start += 12
        y_start -= 1
        
    start_filter = f"{y_start:04d}-{m_start:02d}"
    current_m_str = today.strftime("%Y-%m")
    
    return start_filter, current_m_str

def build_checklist_data(meta_dict, transaction_pool, is_expense=True):
    """
    Builds the checklist DataFrame with robust matching and suggestions.
    """
    rows = []
    
    # Defensive: Ensure transaction_pool is a DataFrame
    if transaction_pool is None or transaction_pool.empty:
        # We still return rows for the checklist items (all missing)
        display_pool = pd.DataFrame() 
    else:
        display_pool = transaction_pool.copy()

    for name, meta in meta_dict.items():
        limit = meta.get('limit', 0.0)
        due_day = meta.get('day', '')
        
        # 1. Direct Match (Categorized)
        matches = pd.DataFrame()
        if not display_pool.empty and 'category' in display_pool.columns:
            matches = display_pool[display_pool['category'] == name]
        
        # Safe Sum
        if not matches.empty and 'amount' in matches.columns:
            actual = matches['amount'].abs().sum() if is_expense else matches['amount'].sum()
        else:
            actual = 0.0
            
        # Status Logic
        status = "Pago" if actual >= (limit * 0.9) else "Pending" 
        if actual == 0: status = "Faltando"
        
        # Details from PRIMARY match
        renamed_desc = ""
        original_desc = ""
        source_str = "-"
        
        if not matches.empty and 'amount' in matches.columns:
            # Sort by amount desc
            matches = matches.sort_values(by='amount', key=abs, ascending=False)
            primary = matches.iloc[0]
            renamed_desc = primary.get('description', '')
            original_desc = primary.get('raw_description', '')
            if 'account' in matches.columns:
                sources = matches['account'].unique()
                source_str = ", ".join(sources)
        
        # 2. SUGGESTION LOGIC (If Faltando)
        suggested_desc = ""
        suggested_match_raw = ""
        
        if status == "Faltando" and not display_pool.empty and 'description' in display_pool.columns:
            # A. Name Similarity
            # Use all available descriptions in the pool that are NOT already categorized as this item
            # Only look at items that are either Não categorizado OR Categorized as something else (potential miscategory?)
            # Usually we filter for Não categorizado or just search everything.
            
            candidates = display_pool[display_pool['category'] != name] if 'category' in display_pool.columns else display_pool
            
            if not candidates.empty:
                unique_descs = candidates['description'].unique().astype(str).tolist()
                
                # Close match to the Category Name (Rule name)
                # Cutoff 0.6 is loose, 0.8 is strict.
                close = get_close_matches(name.lower(), [d.lower() for d in unique_descs], n=1, cutoff=0.5)
                
                found_match = None
                
                if close:
                    # Find the row(s) corresponding to this description
                    # Case insensitive match back
                    mask = candidates['description'].str.lower() == close[0]
                    match_rows = candidates[mask]
                    if not match_rows.empty:
                        found_match = match_rows.iloc[0]
                
                # B. Amount Match (Secondary)
                # If no text match, check if there's a transaction with very similar amount (+- 2%)
                if found_match is None and limit > 0:
                    # Filter by amount roughly
                    # Check ABS amount
                    if 'amount' in candidates.columns:
                        tol = limit * 0.05
                        amt_mask = (candidates['amount'].abs() >= limit - tol) & (candidates['amount'].abs() <= limit + tol)
                        amt_cands = candidates[amt_mask]
                        if not amt_cands.empty:
                             found_match = amt_cands.iloc[0] # Take first
                
                if found_match is not None:
                     d_txt = found_match.get('description', '')
                     a_val = found_match.get('amount', 0)
                     suggested_desc = f"{d_txt} ({a_val:.2f})"
                     suggested_match_raw = d_txt
        
        rows.append({
            "Item": name,
            "Due": due_day,
            "Renamed": renamed_desc,
            "Original": original_desc,
            "Expected": limit,
            "Actual": actual,
            "Status": status,
            "Source": source_str,
            "Suggested Match": suggested_desc,
            "_raw_match": suggested_match_raw
        })
        
    return pd.DataFrame(rows)

def filter_month_data(df, month_str):
    if df.empty or 'month_str' not in df.columns: return df
    return df[df['month_str'] == month_str].copy()
