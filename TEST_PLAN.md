# THE VAULT - Comprehensive Test Plan

## Testing Strategy

This document outlines the comprehensive testing approach for THE VAULT, ensuring all functionality works as expected from a user perspective.

---

## Phase 1: Current Application Testing (Legacy FinanceDashboard)

### 1.1 Data Loading & Import

**Test Cases:**
- [ ] Load OFX files from checking account
- [ ] Load CSV files from Master Black credit card
- [ ] Load CSV files from Visa Black credit card
- [ ] Load CSV files from Rafa's Master card
- [ ] Load Google Sheets export CSVs (historical data)
- [ ] Verify duplicate detection works
- [ ] Verify data consolidation across sources
- [ ] Check date parsing for all formats
- [ ] Check amount parsing (R$ format with commas)
- [ ] Verify account type assignment

**Expected Files:**
```
FinanceDashboard/SampleData/
├── Extrato Conta Corrente-*.ofx (checking - OFX)
├── master-*.csv (credit card statements)
├── visa-*.csv (credit card statements)
├── Finanças - CONTROLE MASTER BLACK.csv (Google Sheets export)
├── Finanças - CONTROLE VISA BLACK.csv (Google Sheets export)
└── Finanças - CONTROLE MASTER BLACK ADICIONAL RAFA.csv (Google Sheets export)
```

### 1.2 Categorization & Rules

**Test Cases:**
- [ ] Load rules.json and verify keyword matching
- [ ] Load budget.json and verify category structure
- [ ] Load subcategory_rules.json and verify subcategory assignment
- [ ] Test auto-categorization on import
- [ ] Test manual category override
- [ ] Test category persistence after reload
- [ ] Verify category types: Fixed, Variable, Investment, Income
- [ ] Test temporal rules (if implemented)

**Files to Review:**
- `FinanceDashboard/rules.json` - Keyword → Category mapping
- `FinanceDashboard/budget.json` - Category definitions with types and limits
- `FinanceDashboard/subcategory_rules.json` - Subcategory mappings

### 1.3 UI Components

**Test Cases:**

#### Monthly View Tabs
- [ ] Verify all months are displayed as tabs
- [ ] Test month navigation (click different tabs)
- [ ] Verify current month is highlighted/selected by default
- [ ] Test visibility of 6 months window
- [ ] Test navigation left/right if implemented

#### Vault Summary
- [ ] Total income displayed correctly
- [ ] Total fixed expenses displayed correctly
- [ ] Total variable expenses displayed correctly
- [ ] Total investments displayed correctly
- [ ] Balance calculation correct (income - expenses)
- [ ] Month-over-month comparison working
- [ ] Visual indicators (colors) working

#### Recurring Grid (Fixed Income & Expenses)
- [ ] Fixed income items listed
- [ ] Fixed expenses items listed
- [ ] Expected amounts shown
- [ ] Actual amounts matched correctly
- [ ] Status indicators (paid/unpaid/missing)
- [ ] Visual formatting working
- [ ] Edit functionality (if available)

#### Cards Grid
- [ ] Credit card balances shown
- [ ] Card-specific transactions grouped
- [ ] Card limits displayed (if available)
- [ ] Available credit calculated

#### Transaction Editor
- [ ] Transaction list loads correctly
- [ ] Sorting works (date, amount, category)
- [ ] Filtering works (account, category, date range)
- [ ] Edit transaction category
- [ ] Edit transaction description
- [ ] Delete transaction (if available)
- [ ] Bulk operations (if available)

#### Transaction Mapper
- [ ] Uncategorized transactions displayed
- [ ] Category dropdown populated
- [ ] Subcategory dropdown populated
- [ ] Assign category to transaction
- [ ] Bulk category assignment
- [ ] Create new categorization rule

#### Installment Tracker
- [ ] Installment detection working (1/3, 2/3 pattern)
- [ ] Installment groups identified
- [ ] Progress tracking displayed
- [ ] Remaining installments calculated
- [ ] Future commitment total shown
- [ ] Visual progress bars working

#### Analytics Dashboard
- [ ] Monthly spending chart loads
- [ ] Category breakdown pie chart loads
- [ ] Trend analysis working
- [ ] Comparison charts working
- [ ] Export functionality (if available)

### 1.4 Validation & Quality

**Test Cases:**
- [ ] Validation report renders
- [ ] Data quality metrics displayed
- [ ] Reconciliation view working
- [ ] Missing transactions flagged
- [ ] Duplicate detection reported
- [ ] Amount mismatches highlighted

### 1.5 Performance & UX

**Test Cases:**
- [ ] Initial load time acceptable (< 5s)
- [ ] Month switching responsive (< 1s)
- [ ] Transaction filtering responsive
- [ ] No visual glitches
- [ ] Mobile responsiveness (if applicable)
- [ ] Error messages clear and helpful

---

## Phase 2: New Architecture Testing (vault/ module)

### 2.1 Database Layer

**Test Cases:**
- [x] Connection pooling working
- [x] Transaction model CRUD
- [x] Category model CRUD
- [x] Subcategory model CRUD
- [x] Duplicate prevention working
- [x] Installment tracking working
- [x] Monthly summaries accurate
- [x] Bulk operations efficient

### 2.2 Parsers

**Test Cases:**
- [ ] OFX parser extracts transactions correctly
- [ ] OFX parser handles dates correctly
- [ ] OFX parser handles amounts correctly
- [ ] CSV bank parser works with all card formats
- [ ] CSV Google Sheets parser preserves categories
- [ ] All parsers handle encoding correctly (UTF-8, Latin-1)
- [ ] Error handling for malformed files
- [ ] Performance with large files (10k+ transactions)

### 2.3 Import Service

**Test Cases:**
- [ ] SHA256 hashing prevents duplicate imports
- [ ] Import log tracks file history
- [ ] Rollback on partial failure
- [ ] Progress reporting during import
- [ ] Validation before import
- [ ] Category mapping during import

### 2.4 Categorization Engine

**Test Cases:**
- [ ] Keyword matching works
- [ ] Priority ordering respected
- [ ] Temporal rules applied correctly
- [ ] Learn from manual categorizations
- [ ] Subcategory assignment working
- [ ] Rule conflict resolution

### 2.5 New UI (When Implemented)

**Test Cases:**
- [ ] Minimal 4-tab design renders
- [ ] No emojis anywhere
- [ ] Earthly color palette applied
- [ ] Snapshot widget always visible
- [ ] Monthly view accessible
- [ ] Actions tab functional
- [ ] Analysis tab working
- [ ] Settings tab functional

---

## Phase 3: Integration Testing

### 3.1 End-to-End Workflows

**Workflow 1: Import New Statement**
1. [ ] Upload OFX file from bank
2. [ ] System detects file type
3. [ ] Parse and validate data
4. [ ] Check for duplicates
5. [ ] Auto-categorize transactions
6. [ ] Display uncategorized items
7. [ ] User assigns categories
8. [ ] Save to database
9. [ ] Update monthly summary
10. [ ] Verify data in UI

**Workflow 2: Monthly Reconciliation**
1. [ ] Select current month
2. [ ] Review fixed expenses checklist
3. [ ] Mark items as paid/unpaid
4. [ ] Identify missing payments
5. [ ] Flag anomalies
6. [ ] Generate reconciliation report

**Workflow 3: Installment Tracking**
1. [ ] System detects installment pattern
2. [ ] Group installments by UUID
3. [ ] Display progress (2/12 paid)
4. [ ] Calculate remaining commitment
5. [ ] Show impact on future months
6. [ ] Alert when installment completes

**Workflow 4: Category Analysis**
1. [ ] Select analysis tab
2. [ ] Choose date range
3. [ ] View spending by category
4. [ ] Compare month-over-month
5. [ ] Identify trends
6. [ ] Export report

### 3.2 Data Migration Testing

**Test Cases:**
- [ ] Export data from old system
- [ ] Import into new PostgreSQL database
- [ ] Verify all transactions preserved
- [ ] Verify all categories preserved
- [ ] Verify all rules preserved
- [ ] No data loss
- [ ] Rollback capability works

---

## Phase 4: Regression Testing

After any changes, verify:
- [ ] All previous tests still pass
- [ ] No performance degradation
- [ ] No UI regressions
- [ ] No data corruption

---

## Test Data Inventory

### Available Sample Files:
1. **OFX Files (Checking Account)**
   - Extrato Conta Corrente-190120261427.txt
   - Extrato Conta Corrente-190120261446.ofx
   - Extrato Conta Corrente-190120261448.ofx
   - Extrato Conta Corrente-190120261450.ofx

2. **CSV Credit Card Statements**
   - master-1125.csv
   - master-1225.csv
   - master-0126.csv
   - master-0226.csv
   - visa-1225.csv
   - visa-0126.csv
   - visa-0226.csv

3. **Google Sheets Exports (Historical)**
   - Finanças - CONTROLE MASTER BLACK.csv (~350KB)
   - Finanças - CONTROLE VISA BLACK.csv (~45KB)
   - Finanças - CONTROLE MASTER BLACK ADICIONAL RAFA.csv (~20KB)

---

## Test Execution Log

### Session 1: 2026-01-21

**Phase 1.1: Data Loading**
- [ ] TODO: Test OFX import
- [ ] TODO: Test CSV import
- [ ] TODO: Test Google Sheets import

**Phase 1.2: Categorization**
- [ ] TODO: Review rules.json
- [ ] TODO: Test auto-categorization

**Phase 1.3: UI Components**
- [ ] TODO: Test all UI components systematically

---

## Bug Tracking

### Known Issues:
1. TBD after testing

### Fixed Issues:
1. None yet

---

## Success Criteria

### Phase 1 (Legacy App):
- All data files load without errors
- All UI components render correctly
- All user workflows complete successfully
- No critical bugs

### Phase 2 (New Architecture):
- All models pass tests
- All parsers handle sample data
- Import service prevents duplicates
- UI meets design requirements (minimal, clean, no emojis)

### Phase 3 (Integration):
- End-to-end workflows work
- Data migration successful
- Performance acceptable

---

Next Steps: Execute Phase 1 testing systematically
