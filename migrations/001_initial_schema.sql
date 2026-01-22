-- THE VAULT - Initial Database Schema
-- Migration: 001_initial_schema.sql
-- Created: 2026-01-21

-- Enable UUID extension for installment grouping
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Categories table (Fixed, Variable, Investment, Income)
CREATE TABLE categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    type VARCHAR(20) NOT NULL CHECK (type IN ('Fixed', 'Variable', 'Investment', 'Income')),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Subcategories table
CREATE TABLE subcategories (
    id SERIAL PRIMARY KEY,
    category_id INTEGER NOT NULL REFERENCES categories(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(category_id, name)
);

-- Core transactions table
CREATE TABLE transactions (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    description TEXT NOT NULL,
    amount DECIMAL(12,2) NOT NULL,
    account_type VARCHAR(50) NOT NULL CHECK (account_type IN ('checking', 'mastercard', 'visa', 'mastercard_rafa')),

    -- Categorization
    category_id INTEGER REFERENCES categories(id),
    subcategory_id INTEGER REFERENCES subcategories(id),

    -- Installment tracking
    is_installment BOOLEAN DEFAULT FALSE,
    installment_current INTEGER,
    installment_total INTEGER,
    installment_group_id UUID,

    -- Source tracking
    source_file VARCHAR(255),
    imported_at TIMESTAMP DEFAULT NOW(),

    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    -- Prevent duplicate imports
    UNIQUE(date, description, amount, account_type)
);

-- Categorization rules (temporal support)
CREATE TABLE categorization_rules (
    id SERIAL PRIMARY KEY,
    keyword TEXT NOT NULL,
    category_id INTEGER NOT NULL REFERENCES categories(id) ON DELETE CASCADE,
    subcategory_id INTEGER REFERENCES subcategories(id) ON DELETE SET NULL,
    priority INTEGER DEFAULT 0,
    valid_from DATE,
    valid_until DATE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    CHECK (valid_until IS NULL OR valid_until >= valid_from)
);

-- Recurring items template (default recurring bills)
CREATE TABLE recurring_items_template (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    category_id INTEGER NOT NULL REFERENCES categories(id),
    expected_amount DECIMAL(12,2),
    due_day INTEGER CHECK (due_day BETWEEN 1 AND 31),
    active_from DATE NOT NULL,
    active_until DATE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    CHECK (active_until IS NULL OR active_until >= active_from)
);

-- Monthly overrides for recurring items
CREATE TABLE recurring_items_overrides (
    id SERIAL PRIMARY KEY,
    template_id INTEGER NOT NULL REFERENCES recurring_items_template(id) ON DELETE CASCADE,
    month DATE NOT NULL,
    expected_amount DECIMAL(12,2),
    is_skipped BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),

    UNIQUE(template_id, month)
);

-- Installment plans (for planning future spending)
CREATE TABLE installment_plans (
    id SERIAL PRIMARY KEY,
    description TEXT NOT NULL,
    category_id INTEGER REFERENCES categories(id),
    total_installments INTEGER NOT NULL,
    installment_amount DECIMAL(12,2) NOT NULL,
    start_date DATE NOT NULL,
    installment_group_id UUID UNIQUE NOT NULL DEFAULT uuid_generate_v4(),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Account balance snapshots
CREATE TABLE account_balances (
    id SERIAL PRIMARY KEY,
    account_type VARCHAR(50) NOT NULL,
    month DATE NOT NULL,
    balance DECIMAL(12,2) NOT NULL,
    recorded_at TIMESTAMP DEFAULT NOW(),

    UNIQUE(account_type, month)
);

-- Import audit log (prevent duplicate imports)
CREATE TABLE import_log (
    id SERIAL PRIMARY KEY,
    file_name VARCHAR(255) NOT NULL,
    file_type VARCHAR(50) NOT NULL,
    file_hash VARCHAR(64) NOT NULL UNIQUE,
    records_imported INTEGER DEFAULT 0,
    import_date TIMESTAMP DEFAULT NOW()
);

-- Performance indexes
CREATE INDEX idx_transactions_date ON transactions(date);
CREATE INDEX idx_transactions_account ON transactions(account_type);
CREATE INDEX idx_transactions_category ON transactions(category_id);
CREATE INDEX idx_transactions_month ON transactions(DATE_TRUNC('month', date));
CREATE INDEX idx_transactions_installment_group ON transactions(installment_group_id) WHERE installment_group_id IS NOT NULL;

-- Full-text search for categorization rules
CREATE INDEX idx_categorization_rules_keyword ON categorization_rules USING gin(to_tsvector('portuguese', keyword));

-- Triggers for updated_at timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_categories_updated_at BEFORE UPDATE ON categories
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_subcategories_updated_at BEFORE UPDATE ON subcategories
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_transactions_updated_at BEFORE UPDATE ON transactions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_categorization_rules_updated_at BEFORE UPDATE ON categorization_rules
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_recurring_items_template_updated_at BEFORE UPDATE ON recurring_items_template
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_installment_plans_updated_at BEFORE UPDATE ON installment_plans
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Migration complete
COMMENT ON DATABASE vault_finance IS 'THE VAULT - Personal Finance Management System';
