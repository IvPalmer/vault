from CategoryEngine import CategoryEngine
import pandas as pd
import os
import io

class DataLoader:
    def __init__(self, data_dir=None):
        if data_dir is None:
            # Default to sibling SampleData folder
            base_dir = os.path.dirname(os.path.abspath(__file__))
            self.data_dir = os.path.join(base_dir, "SampleData")
        else:
            self.data_dir = data_dir
        
        self.transactions = pd.DataFrame()
        self.engine = CategoryEngine() # Initialize Engine
        
    def load_all(self):
        """Loads all CSV/TXT files from the data directory."""
        all_data = []
        files = [f for f in os.listdir(self.data_dir) if not f.startswith(".")]
        
        # Deduplication Strategy:
        # If ANY OFX files exist, they are the preferred source for Checking.
        # We generally skip all TXT/Extrato files to avoid duplicates with slightly different timestamps.
        # e.g. Extrato...1427.txt vs Extrato...1446.ofx
        
        has_checking_ofx = any(f.endswith('.ofx') for f in files)
        
        filtered_files = []
        for f in files:
            # If it's a Checking TXT/Extrato and we have OFX, skip it.
            is_checking_txt = f.endswith(".txt") or ("extrato" in f.lower() and not f.endswith(".ofx"))
            
            if has_checking_ofx and is_checking_txt:
                print(f"   ⏩ Skipping {f} (OFX available for Checking)")
                continue
            
            filtered_files.append(f)
            
        files = filtered_files
        print(f"📂 Found {len(files)} files to load")
        
        for filename in files:
            path = os.path.join(self.data_dir, filename)
            try:
                df = self._parse_file(path, filename)
                if df is not None and not df.empty:
                    # Apply Logic based on Source Type
                    if "Finanças" in filename:
                        # HISTORICAL: Kept full history as per user request
                        pass
                    else:
                        # RAW/MODERN: Only keep data AFTER/ON cutoff (to avoid older duplicates if any)
                        pass
                        
                    if not df.empty:
                        all_data.append(df)
                        print(f"   ✅ Loaded {filename}: {len(df)} rows")
            except Exception as e:
                print(f"   ❌ Failed to load {filename}: {e}")
                
        # Load Manual Transactions
        manual_path = os.path.join(self.data_dir, "../manual_transactions.csv")
        manual_df = self._parse_manual_csv(manual_path)
        if manual_df is not None and not manual_df.empty:
            all_data.append(manual_df)

        if all_data:
            self.transactions = pd.concat(all_data, ignore_index=True)
            
            # Deduplicate (Stronger Logic)
            self.transactions.drop_duplicates(subset=['date', 'description', 'amount', 'account'], inplace=True)
            
            self.transactions.sort_values(by='date', ascending=False, inplace=True)
            
            # Augment with Category Metadata (Type, Limit)
            # We apply this AFTER concatenation so we only do it once per row efficiently
            # However currently 'category' is applied during parse.
            # Let's map it now.
            
            def get_meta(cat):
                m = self.engine.get_category_metadata(cat)
                return pd.Series([m.get("type", "Variable"), m.get("limit", 0.0)])
            
            if not self.transactions.empty:
                 self.transactions[['cat_type', 'budget_limit']] = self.transactions['category'].apply(get_meta)
        
        return self.transactions

    def get_balance_override(self, month_str):
        """Retrieves manually set balance for a month."""
        path = os.path.join(self.data_dir, "../balance_overrides.json")
        if not os.path.exists(path): return None
        try:
             import json
             with open(path, 'r') as f:
                 data = json.load(f)
                 return data.get(month_str)
        except:
            return None

    def save_balance_override(self, month_str, value):
        """Saves manual balance."""
        path = os.path.join(self.data_dir, "../balance_overrides.json")
        data = {}
        import json
        if os.path.exists(path):
            try:
                with open(path, 'r') as f: data = json.load(f)
            except: pass
        
        data[month_str] = value
        with open(path, 'w') as f:
            json.dump(data, f)

    def _parse_file(self, path, filename):
        """Dispatches parsing logic based on filename/content."""
        lower_name = filename.lower()
        
        # Determine Account
        if "adicional rafa" in lower_name:
            account = "Mastercard - Rafa"
        elif "visa" in lower_name:
            account = "Visa Infinite"
        elif "master" in lower_name:
            account = "Mastercard Black"
        else:
            account = "Checking"
            
        # Strategy Dispatch
        if "finanças" in lower_name and "csv" in lower_name:
             return self._parse_historical_csv(path, account)
        elif path.endswith(".txt") or "extrato" in lower_name and not path.endswith(".ofx"):
             return self._parse_bank_txt(path, account)
        elif path.endswith(".ofx"):
             return self._parse_ofx(path, account)
        elif path.endswith(".csv"):
             return self._parse_modern_csv(path, account)
             
        return None

    def _parse_modern_csv(self, path, account):
        """Parses standard bank CSVs (data, lançamento, valor)."""
        try:
            # Try comma first
            df = pd.read_csv(path, dayfirst=False)
            if df.shape[1] < 2:
                 # Try semicolon
                 df = pd.read_csv(path, delimiter=';', dayfirst=False)
        except:
            return None
            
        # Rename Cols (Lowercase match)
        # Simplify mapping
        new_cols = {}
        for col in df.columns:
            c = col.lower()
            if 'data' in c or 'date' in c: key='date'
            elif 'lançamento' in c or 'description' in c or 'title' in c: key='description'
            elif 'valor' in c or 'amount' in c: key='amount'
            else: key = c
            new_cols[col] = key
            
        df = df.rename(columns=new_cols)
        
        if 'date' not in df.columns:
             return None
            
        # Clean Data
        df['date'] = pd.to_datetime(df['date'], errors='coerce', dayfirst=True) # Assume dayfirst generally for BR
        df = df.dropna(subset=['date'])
        
        # Clean Amount
        if 'amount' in df.columns:
            if df['amount'].dtype == 'object':
                 df['amount'] = df['amount'].astype(str).str.replace('R$', '', regex=False)
                 df['amount'] = df['amount'].str.replace('.', '', regex=False) # Thousands
                 df['amount'] = df['amount'].str.replace(',', '.', regex=False) # Decimal
                 df['amount'] = pd.to_numeric(df['amount'])
        
        # Sign Inversion
        # Modern CSVs have Positive Expenses. We need Negative.
        if "Visa" in account or "Master" in account:
             if 'amount' in df.columns:
                 df['amount'] = -df['amount'].abs()
                 # If description is a Payment/Credit, make it positive
                 if 'description' in df.columns:
                     mask_positive = df['description'].str.contains('PAGAMENTO|CREDITO|ESTORNO', case=False, na=False)
                     df.loc[mask_positive, 'amount'] = df.loc[mask_positive, 'amount'].abs()

        df['account'] = account
        
        # Apply Renaming & Categorization
        if 'description' in df.columns:
             df['description'] = df['description'].fillna("Unknown")
             # Preserve raw description for audit
             df['raw_description'] = df['description'].copy()
             
             df['description'] = df['description'].apply(self.engine.apply_renames)
             df['category'] = df['description'].apply(self.engine.categorize)
        
        df['source'] = os.path.basename(path)
        
        # PROJECTION LOGIC
        # Detect patterns like 01/05, 1/12
        import re
        
        projections = []
        
        if 'description' in df.columns:
            for idx, row in df.iterrows():
                desc = str(row['description'])
                match = re.search(r'(\d{1,2})/(\d{1,2})', desc)
                if match:
                    try:
                        current = int(match.group(1))
                        total = int(match.group(2))
                        
                        if 0 < current < total and total <= 24: # Sanity check (max 24 months)
                            # Generate future rows
                            remaining = total - current
                            base_date = row['date']
                            
                            for i in range(1, remaining + 1):
                                next_date = base_date + pd.DateOffset(months=i)
                                next_install_num = current + i
                                
                                # Replace 01/05 with 02/05
                                # Need to handle padding variations
                                old_str = match.group(0)
                                new_str = f"{next_install_num:02d}/{total:02d}"
                                new_desc = desc.replace(old_str, new_str)
                                
                                proj_row = row.copy()
                                proj_row['date'] = next_date
                                proj_row['description'] = new_desc
                                proj_row['source'] = f"Proj from {os.path.basename(path)}"
                                projections.append(proj_row)
                    except:
                        pass
                        
        if projections:
            proj_df = pd.DataFrame(projections)
            df = pd.concat([df, proj_df], ignore_index=True)
        
        # Ensure cols
        target_cols = ['date', 'description', 'amount', 'account', 'category', 'source']
        for c in target_cols:
            if c not in df.columns: df[c] = None
            
        return df[target_cols]

    def _parse_historical_csv(self, path, account):
        try:
            # Try reading with different parameters
            df = None
            encodings = ['utf-8', 'latin1', 'cp1252', 'utf-16']
            separators = [',', ';', '\t']
            
            for encoding in encodings:
                for sep in separators:
                    try:
                        temp = pd.read_csv(path, sep=sep, encoding=encoding, on_bad_lines='skip')
                        if temp.shape[1] >= 4:
                            df = temp
                            break
                    except:
                        continue
                if df is not None: break
            
            if df is None:
                 print(f"   ⚠️ Could not parse structure of {os.path.basename(path)}")
                 return pd.DataFrame()

            # Try auto-cleaning columns
            new_cols = {}
            seen_targets = set()
            for col in df.columns:
                c = str(col).upper()
                target = None
                if 'DATA' in c and 'DIA' not in c: target = 'date'
                elif 'DESC' in c: target = 'description'
                elif 'VALOR' in c: target = 'amount'
                elif 'CAT' in c and 'SUB' not in c and 'CONTROLE' not in c: target = 'category' # Exclude SUB and CONTROLE
                
                if target and target not in seen_targets:
                    new_cols[col] = target
                    seen_targets.add(target)
            
            df = df.rename(columns=new_cols)
            
            # Ensure we found essential columns
            if 'date' not in df.columns or 'amount' not in df.columns:
                 # Try fallback mapping by index if columns are suspiciously unnamed?
                 # Avoiding for now to keep it safe.
                 pass

            df['date'] = pd.to_datetime(df['date'], dayfirst=True, errors='coerce')
            
            # Clean amount
            if df['amount'].dtype == object:
                # Remove R$, handle dots/commas
                # Format "R$ 27,90" -> 27.90
                df['amount'] = df['amount'].astype(str).str.replace('R$', '', regex=False).str.strip()
                df['amount'] = df['amount'].str.replace('.', '', regex=False) # Thousands separator
                df['amount'] = df['amount'].str.replace(',', '.', regex=False) # Decimal
            
            df['amount'] = pd.to_numeric(df['amount'], errors='coerce')
            
            df['account'] = account
            
            # Identify Adicional Card (Historical)
            if "adicional" in os.path.basename(path).lower():
                 if 'description' in df.columns:
                     df['description'] = "[ADIC] " + df['description'].astype(str)
            
            # Renaming
            if 'description' in df.columns:
                 df['description'] = df['description'].fillna("Unknown")
                 df['raw_description'] = df['description'].copy() # Preserve raw
                 df['description'] = df['description'].apply(self.engine.apply_renames)
            
            # Infer Category if missing
            if 'category' not in df.columns:
                df['category'] = df['description'].apply(self.engine.categorize)
            else:
                # Fill missing
                # Safely handle Series operations
                df['category'] = df['category'].fillna('')
                # Ensure string type for comparison
                mask = (df['category'] == '')
                if mask.any():
                     df.loc[mask, 'category'] = df.loc[mask, 'description'].apply(self.engine.categorize)

            # SIGN CORRECTION
            def fix_sign(row):
                try:
                    # Safe access
                    cat = row['category'] if 'category' in row.index else ''
                    amt = row['amount']
                    if pd.isna(amt): return 0.0
                    
                    meta = self.engine.get_category_metadata(cat)
                    ctype = meta.get('type', 'Variable')
                    
                    if ctype == 'Income':
                        return abs(amt)
                    else:
                        return -abs(amt)
                except:
                    return 0.0
            
            df['amount'] = df.apply(fix_sign, axis=1)

            df['source'] = os.path.basename(path)
            
            target_cols = ['date', 'description', 'amount', 'account', 'category', 'source']
            for c in target_cols:
                if c not in df.columns: df[c] = None
            return df[target_cols]
        except Exception as e:
            print(f"   ❌ Error parsing {path}: {e}")
            return pd.DataFrame()
            
    def _parse_bank_txt(self, path, account):
        try:
            # Reads TXT (typically tab or semicolon)
            # Debug script showed failure here. Restoring read.
            # Assuming format: Date \t Description \t Doc \t Amount \t Balance
            # Or similar. Let's try flexible reading.
            
            # First try tab
            df = pd.read_csv(path, sep='\t', header=None, skiprows=1) # Skip header line if any
            if df.shape[1] < 3:
                 df = pd.read_csv(path, sep=';', header=None)
            
            # We need to identify columns by position or content.
            # Assuming standard Extrato: Date (0), Desc (1), ..., Amount (3 or 4)
            # Let's clean the columns
            # The previous code (Step 1273) had hardcoded names: ['date', 'description', 'doc', 'amount', 'balance']
            
            if df.shape[1] >= 4:
                 # Map by index
                 df = df.iloc[:, [0, 1, 3]] # Date, Desc, Amount
                 df.columns = ['date', 'description', 'amount']
            else:
                 # Fallback
                 df.columns = ['date', 'description', 'amount']
                 
            df['date'] = pd.to_datetime(df['date'], dayfirst=True, errors='coerce')
            
            # Clean Amount
            if 'amount' in df.columns:
                if df['amount'].dtype == 'object':
                     df['amount'] = df['amount'].astype(str).str.replace('.', '', regex=False)
                     df['amount'] = df['amount'].str.replace(',', '.', regex=False)
                df['amount'] = pd.to_numeric(df['amount'], errors='coerce')
            
            # Filter invalid
            df = df.dropna(subset=['date', 'amount'])
            
            # Filter standard Credit Card Payments
            mask_cc_payment = df['description'].str.contains('FATURA PAGA|INT MC BLACK|INT PERSON INFI|ITAUCARD', case=False, na=False)
            df = df[~mask_cc_payment]
            
            df['account'] = account
            
            # Renaming & Categorization
            df['raw_description'] = df['description'].copy()
            df['description'] = df['description'].apply(self.engine.apply_renames)
            df['category'] = df['description'].apply(self.engine.categorize)
    
            df['source'] = os.path.basename(path)
            return df[['date', 'description', 'amount', 'account', 'category', 'source']]
        except Exception as e:
            # print(f"TXT Parse Error: {e}")
            return pd.DataFrame()

    def _parse_ofx(self, path, account):
        """Parses OFX files using Regex (since ofxparse is not available)."""
        import re
        try:
            with open(path, 'r', encoding='latin1', errors='ignore') as f:
                content = f.read()
            
            # Extract Transactions via Regex
            # Pattern: <STMTTRN> ... </STMTTRN>
            pattern = re.compile(r'<STMTTRN>(.*?)</STMTTRN>', re.DOTALL)
            matches = pattern.findall(content)
            
            records = []
            for block in matches:
                # Extract fields
                date_match = re.search(r'<DTPOSTED>(\d+)', block)
                amount_match = re.search(r'<TRNAMT>([-0-9.]+)', block)
                memo_match = re.search(r'<MEMO>(.*)', block)
                trntype_match = re.search(r'<TRNTYPE>(.*)', block)
                
                if date_match and amount_match:
                    dt_str = date_match.group(1)[:8] # YYYYMMDD
                    amt_str = amount_match.group(1)
                    desc = memo_match.group(1).strip() if memo_match else "Unknown"
                    ttype = trntype_match.group(1).strip() if trntype_match else ""
                    
                    # Fix encoding of Description (often latin1/utf8 mixed)
                    # We opened file as latin1.
                    
                    records.append({
                        'date': pd.to_datetime(dt_str, format='%Y%m%d', errors='coerce'),
                        'description': desc,
                        'amount': float(amt_str),
                        'account': account,
                        'source': os.path.basename(path)
                    })
            
            if records:
                df = pd.DataFrame(records)
                df['category'] = df['description'].apply(self.engine.categorize)
                df['raw_description'] = df['description'].copy() # Preserve raw
                df['description'] = df['description'].apply(self.engine.apply_renames)
                # Ensure date is not null
                df = df.dropna(subset=['date'])
                return df
            else:
                 return pd.DataFrame()

        except Exception as e:
            print(f"   ❌ Error parsing OFX {path}: {e}")
            return pd.DataFrame()

    def add_manual_transaction(self, date, description, amount, category, account="Manual"):
        """Appends a manual transaction to manual_transactions.csv"""
        manual_path = os.path.join(self.data_dir, "../manual_transactions.csv")
        
        # Prepare row
        new_row = pd.DataFrame([{
            "date": pd.to_datetime(date).strftime("%Y-%m-%d"),
            "description": description,
            "amount": amount,
            "account": account,
            "category": category,
            "source": "manual_transactions.csv"
        }])
        
        # Append or Create
        if os.path.exists(manual_path) and os.path.getsize(manual_path) > 0:
            new_row.to_csv(manual_path, mode='a', header=False, index=False)
        else:
            new_row.to_csv(manual_path, mode='w', header=True, index=False)
            
    def _parse_manual_csv(self, path):
        if not os.path.exists(path) or os.path.getsize(path) == 0:
            return None
            
        try:
            df = pd.read_csv(path)
            df['date'] = pd.to_datetime(df['date'])
            # Ensure columns exist
            for col in ['description', 'amount', 'account', 'category']:
                if col not in df.columns:
                    df[col] = None
                    
            df['source'] = "manual_transactions.csv"
            return df[['date', 'description', 'amount', 'account', 'category', 'source']]
        except Exception as e:
            print(f"Error parsing manual csv: {e}")
            return None

if __name__ == "__main__":
    dl = DataLoader()
    df = dl.load_all()
    print(df.head())
    print(f"Total: {df['amount'].sum()}")
