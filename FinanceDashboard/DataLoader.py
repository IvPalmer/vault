from CategoryEngine import CategoryEngine
from ValidationEngine import ValidationEngine
from DataNormalizer import DataNormalizer
import pandas as pd
import os
import io

class DataLoader:
    # ========== CUTOFF DATE CONFIGURATION ==========
    # Historical Google Sheets data goes until Oct 3, 2025
    # Card CSV exports start from various dates in 2024 (containing installments)
    # Cutoff set to Sept 30, 2025 to avoid overlap and duplication
    #
    # RULE:
    #   - Google Sheets: Use transactions BEFORE Sept 30, 2025 (no projections)
    #   - Card CSVs: Use all transactions (they already contain real installments from bank)
    #   - OFX files: Use all (checking account, no overlap issue)
    HISTORICAL_CUTOFF = pd.Timestamp('2025-09-30')

    def __init__(self, data_dir=None, profile_name=None):
        if data_dir is not None:
            self.data_dir = data_dir
        else:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            if profile_name:
                # Per-profile data directory: SampleData/Palmer/, SampleData/Rafa/, etc.
                self.data_dir = os.path.join(base_dir, "SampleData", profile_name)
            else:
                self.data_dir = os.path.join(base_dir, "SampleData")

        self.transactions = pd.DataFrame()
        self.engine = CategoryEngine() # Initialize Engine
        self.validator = ValidationEngine() # Initialize Validator
        self.normalizer = DataNormalizer(self.engine) # Initialize Normalizer
        self.source_files = []  # Track loaded files for validation
        
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
                print(f"   [Pulando] Skipping {f} (OFX available for Checking)")
                continue
            
            filtered_files.append(f)
            
        files = filtered_files
        print(f"[Arquivos] Found {len(files)} files to load")
        
        for filename in files:
            path = os.path.join(self.data_dir, filename)
            self.source_files.append(path)  # Track for validation
            try:
                df = self._parse_file(path, filename)
                if df is not None and not df.empty:
                    # Apply cutoff to avoid overlap between historical and modern sources.
                    # Only apply to CSVs whose invoice_month is ON or BEFORE the cutoff.
                    # Post-cutoff invoices keep ALL rows (installments from older purchases
                    # have earlier dates but are real charges on the bill).
                    if "finanças" not in filename.lower() and 'date' in df.columns:
                        fn_lower = filename.lower()
                        if fn_lower.startswith('master-') or fn_lower.startswith('visa-'):
                            # Extract invoice_month from filename (e.g. master-0126 → 2026-01)
                            import re as _re
                            _inv_match = _re.search(r'(master|visa)-(\d{2})(\d{2})\.csv', fn_lower)
                            if _inv_match:
                                _inv_month = int(_inv_match.group(2))
                                _inv_year = 2000 + int(_inv_match.group(3))
                                _inv_date = pd.Timestamp(_inv_year, _inv_month, 1)
                                if _inv_date <= self.HISTORICAL_CUTOFF:
                                    # Old invoice — apply cutoff to avoid overlap with Google Sheets
                                    before = len(df)
                                    df = df[df['date'] >= self.HISTORICAL_CUTOFF].copy()
                                    if len(df) < before:
                                        print(f"   [Cutoff] Old invoice ({_inv_year}-{_inv_month:02d}): {before} → {len(df)} transactions (from {self.HISTORICAL_CUTOFF.date()})")
                                else:
                                    # Post-cutoff invoice — keep ALL rows (installments
                                    # from older purchases are real charges on this bill)
                                    print(f"   [No cutoff] Post-cutoff invoice ({_inv_year}-{_inv_month:02d}): keeping all {len(df)} rows")

                    if not df.empty:
                        all_data.append(df)
                        print(f"   [OK] Loaded {filename}: {len(df)} rows")
            except Exception as e:
                print(f"   [Erro] Failed to load {filename}: {e}")
                
        # Load Manual Transactions
        manual_path = os.path.join(self.data_dir, "../manual_transactions.csv")
        manual_df = self._parse_manual_csv(manual_path)
        if manual_df is not None and not manual_df.empty:
            all_data.append(manual_df)

        if all_data:
            self.transactions = pd.concat(all_data, ignore_index=True)

            # Deduplicate (Stronger Logic)
            # Use description_original if available, otherwise description
            dedup_cols = ['date', 'amount', 'account']
            if 'description_original' in self.transactions.columns:
                dedup_cols.append('description_original')
            else:
                dedup_cols.append('description')

            self.transactions.drop_duplicates(subset=dedup_cols, inplace=True)

            self.transactions.sort_values(by='date', ascending=False, inplace=True)

            # APPLY FULL NORMALIZATION using DataNormalizer
            # This adds: description_original, is_installment, is_recurring,
            # installment_info, is_internal_transfer, cat_type, etc.
            if not self.transactions.empty:
                # Get source account from 'account' column (set during parse)
                # We normalize per-group to preserve source information
                normalized_dfs = []

                for source in self.transactions['account'].unique():
                    source_df = self.transactions[self.transactions['account'] == source].copy()
                    is_nubank = source.startswith('NuBank')
                    normalized_df = self.normalizer.normalize(source_df, source, is_nubank=is_nubank)
                    normalized_dfs.append(normalized_df)

                self.transactions = pd.concat(normalized_dfs, ignore_index=True)
                self.transactions.sort_values(by='date', ascending=False, inplace=True)

        # Run validation
        validation_report = self.validator.validate_all(self.transactions, self.source_files, self)

        # Print validation summary
        self.validator.print_validation_summary()

        # Save validation report
        self.validator.generate_validation_report()

        return self.transactions

    def get_balance_override(self, month_str):
        """Retrieves manually set balance for a month."""
        import json
        path = os.path.join(self.data_dir, "../balance_overrides.json")
        if not os.path.exists(path): return None
        try:
            with open(path, 'r') as f:
                data = json.load(f)
                return data.get(month_str)
        except (json.JSONDecodeError, IOError, OSError) as e:
            print(f"   [Aviso] Could not read balance overrides: {e}")
            return None

    def save_balance_override(self, month_str, value):
        """Saves manual balance."""
        import json
        path = os.path.join(self.data_dir, "../balance_overrides.json")
        data = {}
        if os.path.exists(path):
            try:
                with open(path, 'r') as f: data = json.load(f)
            except (json.JSONDecodeError, IOError, OSError):
                data = {}
        
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
        elif lower_name.startswith("nubank_") and lower_name.endswith(".ofx"):
            account = "NuBank Cartão"   # NuBank credit card OFX (Nubank_YYYY-MM-DD.ofx)
        elif lower_name.startswith("nu_") and lower_name.endswith(".ofx"):
            account = "NuBank Conta"    # NuBank checking OFX (NU_730386301_*.ofx)
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
        except (pd.errors.EmptyDataError, pd.errors.ParserError, ValueError, OSError) as e:
            print(f"   [Erro] CSV parse error {path}: {e}")
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
        # CC CSVs: positive = charges (money owed), negative = refunds/credits (money back)
        # DB convention: negative = expenses, positive = income/credits
        # Simple negation preserves refund signs correctly.
        if "Visa" in account or "Master" in account:
             if 'amount' in df.columns:
                 df['amount'] = -df['amount']

                 # FILTER OUT PAYMENT ENTRIES
                 # Credit card CSVs include the previous month's payment as multiple entries:
                 # 1. PAGAMENTO EFETUADO: -30,200 (payment from checking)
                 # 2. DEVOLUCAO SALDO CREDOR: +30,200 (credit applied to card)
                 # 3. EST DEVOL SALDO CREDOR: -30,200 (reversal/adjustment)
                 # Net effect: -30,200 (inflates the invoice total)
                 # These are already captured in checking account, so we filter ALL of them
                 if 'description' in df.columns:
                     # Remove payment-related transactions (duplicates from checking)
                     payment_mask = df['description'].str.contains(
                         'PAGAMENTO EFETUADO|DEVOLUCAO SALDO CREDOR|EST DEVOL SALDO CREDOR',
                         case=False, na=False
                     )
                     original_count = len(df)
                     df = df[~payment_mask].copy()
                     filtered_count = original_count - len(df)

                     if filtered_count > 0:
                         print(f"   [Payment Filter] {os.path.basename(path)}: Removed {filtered_count} payment entries (already in checking)")

                     # Note: real refunds/credits (negative CSV values) are now correctly
                     # positive in the DB thanks to simple negation (no abs()).

        df['account'] = account
        
        # Apply Renaming & Categorization
        if 'description' in df.columns:
             df['description'] = df['description'].fillna("Unknown")
             # Preserve raw description for audit
             df['raw_description'] = df['description'].copy()
             
             df['description'] = df['description'].apply(self.engine.apply_renames)
             df['category'] = df['description'].apply(self.engine.categorize)
        
        df['source'] = os.path.basename(path)

        # INSTALLMENT FILTERING LOGIC
        #
        # Problem: Each card CSV contains installments from PREVIOUS purchases.
        # Example: master-0126.csv contains:
        #   - "Netflix 01/12" (1st installment)
        #   - "Geladeira 06/10" (6th installment of purchase from months ago)
        #
        # If we load ALL CSVs, we get DUPLICATES:
        #   - master-0126.csv has "Netflix 01/12"
        #   - master-0226.csv has "Netflix 02/12" (SAME purchase, next installment)
        #   - master-0326.csv has "Netflix 03/12" (SAME purchase, next installment)
        #
        # SOLUTION: Extract invoice month from filename and filter installments.
        # Rule: Keep ONLY installments where current_installment matches the invoice month offset.
        #
        # For card files (master-MMYY.csv or visa-MMYY.csv):
        # - Extract MM (invoice month number)
        # - For installments "XX/YY", keep only if this is the file that should contain it
        # - Non-installment transactions: always keep (new purchases)

        import re

        # Extract invoice month from filename (e.g., "master-0126.csv" -> 01)
        filename = os.path.basename(path).lower()
        invoice_month_match = re.search(r'(master|visa)-(\d{2})(\d{2})\.csv', filename)

        if invoice_month_match and ('master' in filename or 'visa' in filename):
            invoice_month = int(invoice_month_match.group(2))  # 01, 02, 03, etc.
            invoice_year = int('20' + invoice_month_match.group(3))  # 2025, 2026

            # INVOICE PERIOD METADATA
            # The CSV filename indicates the INVOICE month (when bill closes and gets paid)
            # Example: master-0126.csv = January 2026 invoice
            #   - Contains December 2025 purchases (close date: Dec 30, 2025)
            #   - Payment date: Jan 5, 2026
            #
            # Invoice closes on day 30 of the PREVIOUS month
            # So January invoice (0126) contains purchases from Dec 1-30

            invoice_date = pd.Timestamp(year=invoice_year, month=invoice_month, day=1)

            # Calculate close date: Last day of PREVIOUS month (day 30)
            # For January invoice (0126), close date is Dec 30, 2025
            if invoice_month == 1:
                close_year = invoice_year - 1
                close_month = 12
            else:
                close_year = invoice_year
                close_month = invoice_month - 1

            close_date = pd.Timestamp(year=close_year, month=close_month, day=30)

            # Payment date: 5th day of invoice month
            payment_date = pd.Timestamp(year=invoice_year, month=invoice_month, day=5)

            # Add invoice metadata to each transaction
            df['invoice_month'] = invoice_date.strftime('%Y-%m')
            df['invoice_close_date'] = close_date
            df['invoice_payment_date'] = payment_date

            print(f"   [Invoice Period] {filename}: Invoice {invoice_date.strftime('%Y-%m')} | Close: {close_date.date()} | Payment: {payment_date.date()}")

            # INSTALLMENT FILTERING DISABLED
            #
            # Previous logic filtered installments by number (01/XX in Jan, 02/XX in Feb, etc.)
            # This was INCORRECT because:
            #   - "01/XX" means "1st installment of XX", not "belongs to invoice month 01"
            #   - Bank CSVs already contain the correct transactions for that invoice
            #   - A January invoice includes ALL installments due in January (01/12, 02/12, 03/12, etc.)
            #
            # The bank CSV export is already filtered correctly by invoice period.
            # We should trust it and NOT filter further by installment number.
        
        # Ensure cols
        target_cols = ['date', 'description', 'amount', 'account', 'category', 'source']

        # Add invoice metadata if present (from card CSV files)
        if 'invoice_month' in df.columns:
            target_cols.extend(['invoice_month', 'invoice_close_date', 'invoice_payment_date'])

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
                 print(f"   [Aviso] Could not parse structure of {os.path.basename(path)}")
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
                elif c == 'ANO/MES': target = 'invoice_month_raw'

                if target and target not in seen_targets:
                    new_cols[col] = target
                    seen_targets.add(target)

            df = df.rename(columns=new_cols)

            # Convert ANO/MES (YYYYMM integer) to invoice_month (YYYY-MM string)
            if 'invoice_month_raw' in df.columns:
                def _convert_anomes(val):
                    try:
                        val = int(val)
                        year = val // 100
                        month = val % 100
                        return f'{year}-{month:02d}'
                    except (ValueError, TypeError):
                        return ''
                df['invoice_month'] = df['invoice_month_raw'].apply(_convert_anomes)
                df = df.drop(columns=['invoice_month_raw'])
            
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

            # Normalize historical category names to match current conventions
            # Historical Google Sheets used UPPERCASE; current rules use mixed case
            category_normalize = {
                'CASA': 'Casa',
                'SAUDE': 'Saúde',
                'LAZER': 'Lazer',
                'TRANSPORTE': 'Transporte',
                'ALIMENTACAO': 'Alimentação',
                'SERVICOS': 'Serviços',
                'CONTAS': 'Contas',
                'COMPRAS GERAIS': 'Compras',
                'MUSICA': 'Lazer',
                'ANIMAIS': 'OUTROS',
                'VIAGEM': 'Lazer',
                'Plano de Saude': 'Saúde',
            }
            df['category'] = df['category'].replace(category_normalize)

            # SIGN CORRECTION
            def fix_sign(row):
                try:
                    # Safe access
                    cat = row['category'] if 'category' in row.index else ''
                    amt = row['amount']
                    if pd.isna(amt): return 0.0

                    meta = self.engine.get_category_metadata(cat)
                    ctype = meta.get('type', 'Variável')

                    if ctype == 'Income':
                        return abs(amt)
                    else:
                        return -abs(amt)
                except (KeyError, TypeError, ValueError):
                    return 0.0
            
            df['amount'] = df.apply(fix_sign, axis=1)

            df['source'] = os.path.basename(path)

            # ===== APPLY CUTOFF DATE FOR HISTORICAL DATA =====
            # Google Sheets historical data should only be used BEFORE the cutoff
            # to avoid duplication with card CSV exports that contain real installments
            if "finanças" in os.path.basename(path).lower():
                original_count = len(df)
                df = df[df['date'] < self.HISTORICAL_CUTOFF].copy()
                filtered_count = len(df)
                print(f"   [Cutoff] Google Sheets: {original_count} → {filtered_count} transactions (before {self.HISTORICAL_CUTOFF.date()})")

            target_cols = ['date', 'description', 'amount', 'account', 'category', 'source']
            if 'invoice_month' in df.columns:
                target_cols.append('invoice_month')
            for c in target_cols:
                if c not in df.columns: df[c] = None
            return df[target_cols]
        except Exception as e:
            print(f"   [Erro] Error parsing {path}: {e}")
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

    @staticmethod
    def _clean_nubank_description(desc):
        """
        Simplify verbose NuBank descriptions.
        - PIX transfers: keep only direction + recipient name
        - Boletos: shorten prefix
        - Everything else: keep as-is
        """
        import re

        def _strip_cnpj_prefix(name):
            """Remove leading CNPJ fragment like '49.092.478 ' from name."""
            return re.sub(r'^[\d.]+\s+', '', name).strip()

        # "Transferência Enviada Pelo Pix - NAME - CPF/CNPJ - BANK ..."
        m = re.match(
            r'Transferência Enviada Pelo Pix - (.+?) - (?:•|[\d./])',
            desc, re.IGNORECASE,
        )
        if m:
            return f'PIX Enviado - {_strip_cnpj_prefix(m.group(1))}'

        # "Transferência Recebida Pelo Pix - NAME - CPF/CNPJ - BANK ..."
        m = re.match(
            r'Transferência Recebida Pelo Pix - (.+?) - (?:•|[\d./])',
            desc, re.IGNORECASE,
        )
        if m:
            return f'PIX Recebido - {_strip_cnpj_prefix(m.group(1))}'

        # "Transferência Recebida - CNPJ NAME - CPF/CNPJ - BANK ..."
        m = re.match(
            r'Transferência Recebida - (.+?) - (?:•|[\d./])',
            desc, re.IGNORECASE,
        )
        if m:
            return f'PIX Recebido - {_strip_cnpj_prefix(m.group(1))}'

        # "Pagamento De Boleto Efetuado - BANK - CITY"
        m = re.match(
            r'Pagamento De Boleto Efetuado - (.+)',
            desc, re.IGNORECASE,
        )
        if m:
            return f'Boleto - {m.group(1).strip()}'

        return desc

    def _parse_ofx(self, path, account):
        """Parses OFX files using Regex (since ofxparse is not available)."""
        import re
        try:
            # Detect encoding: try UTF-8 first (NuBank), fall back to Latin-1 (Itaú)
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()
            except UnicodeDecodeError:
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

                    # Strip closing XML tags from description (e.g. </MEMO>, </Memo>)
                    desc = re.sub(r'</\w+>\s*$', '', desc).strip()

                    # Clean up verbose NuBank PIX/transfer descriptions
                    desc = self._clean_nubank_description(desc)

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

                # INVOICE METADATA for NuBank credit card OFX files
                # Filename pattern: Nubank_YYYY-MM-DD.ofx where date = closing date
                # Extract invoice_month as YYYY-MM from the filename closing date
                if 'Cartão' in account or 'Cartao' in account:
                    filename = os.path.basename(path)
                    nubank_date_match = re.search(r'Nubank_(\d{4})-(\d{2})-(\d{2})\.ofx', filename, re.IGNORECASE)
                    if nubank_date_match:
                        inv_year = int(nubank_date_match.group(1))
                        inv_month = int(nubank_date_match.group(2))
                        inv_day = int(nubank_date_match.group(3))

                        df['invoice_month'] = f'{inv_year}-{inv_month:02d}'

                        # Close date = the date in the filename
                        df['invoice_close_date'] = pd.Timestamp(year=inv_year, month=inv_month, day=inv_day)

                        # Payment date: use due_day (7) of the NEXT month after closing
                        # e.g. closing 2026-01-22 -> payment 2026-02-07
                        if inv_month == 12:
                            pay_year = inv_year + 1
                            pay_month = 1
                        else:
                            pay_year = inv_year
                            pay_month = inv_month + 1
                        df['invoice_payment_date'] = pd.Timestamp(year=pay_year, month=pay_month, day=7)

                        print(f"   [Invoice Period] {filename}: Invoice {inv_year}-{inv_month:02d} | Close: {inv_year}-{inv_month:02d}-{inv_day:02d} | Payment: {pay_year}-{pay_month:02d}-07")

                return df
            else:
                 return pd.DataFrame()

        except Exception as e:
            print(f"   [Erro] Error parsing OFX {path}: {e}")
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
