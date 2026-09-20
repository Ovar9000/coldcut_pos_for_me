-- ==============================================================================
-- SARI-SARI / COLDCUT POS — HARDENED SUPABASE DISASTER RECOVERY SCHEMA
-- ==============================================================================
-- Run this script in your Supabase SQL Editor:
-- https://supabase.com/dashboard/project/<your-project-id>/sql/new
-- ==============================================================================

-- 1. STORAGE BUCKET: store-backups (PRIVATE)
-- Encrypted SQLite store.db snapshot backups. Access restricted to authorized roles.
INSERT INTO storage.buckets (id, name, public)
VALUES ('store-backups', 'store-backups', false)
ON CONFLICT (id) DO UPDATE SET public = false;

-- Clean up any legacy permissive storage policies
DROP POLICY IF EXISTS "Allow public read from store-backups" ON storage.objects;
DROP POLICY IF EXISTS "Allow uploads to store-backups" ON storage.objects;
DROP POLICY IF EXISTS "Allow updates to store-backups" ON storage.objects;
DROP POLICY IF EXISTS "Allow authenticated read store-backups" ON storage.objects;
DROP POLICY IF EXISTS "Allow authenticated insert store-backups" ON storage.objects;
DROP POLICY IF EXISTS "Allow authenticated update store-backups" ON storage.objects;

-- Enforce authenticated role for storage operations (service_role bypasses RLS)
CREATE POLICY "Allow authenticated read store-backups"
ON storage.objects FOR SELECT
TO authenticated
USING (bucket_id = 'store-backups');

CREATE POLICY "Allow authenticated insert store-backups"
ON storage.objects FOR INSERT
TO authenticated
WITH CHECK (bucket_id = 'store-backups');

CREATE POLICY "Allow authenticated update store-backups"
ON storage.objects FOR UPDATE
TO authenticated
USING (bucket_id = 'store-backups');


-- 2. CLOUD MIRROR TABLES (Disaster Recovery & Remote Reporting)
-- ==============================================================================

CREATE TABLE IF NOT EXISTS public.products (
    id                  BIGINT PRIMARY KEY,
    barcode             TEXT,
    pack_barcode        TEXT,
    jar_code            TEXT,
    name                TEXT NOT NULL,
    category            TEXT DEFAULT 'General',
    unit                TEXT NOT NULL DEFAULT 'pc',
    cost_price          NUMERIC(12, 2) NOT NULL DEFAULT 0,
    selling_price       NUMERIC(12, 2) NOT NULL DEFAULT 0,
    stock_qty           NUMERIC(12, 3) NOT NULL DEFAULT 0,
    low_stock_threshold NUMERIC(12, 3) NOT NULL DEFAULT 5,
    updated_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS public.transactions (
    id                  BIGINT PRIMARY KEY,
    receipt_number      TEXT,
    transaction_type    TEXT NOT NULL DEFAULT 'SALE',
    total_amount        NUMERIC(12, 2) NOT NULL DEFAULT 0,
    total_cost          NUMERIC(12, 2) NOT NULL DEFAULT 0,
    payment_method      TEXT DEFAULT 'CASH',
    amount_tendered     NUMERIC(12, 2) NOT NULL DEFAULT 0,
    change_amount       NUMERIC(12, 2) NOT NULL DEFAULT 0,
    customer_name       TEXT,
    notes               TEXT,
    created_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS public.transaction_items (
    id                  BIGINT PRIMARY KEY,
    transaction_id      BIGINT REFERENCES public.transactions(id) ON DELETE CASCADE,
    product_name        TEXT NOT NULL,
    quantity            NUMERIC(12, 3) NOT NULL DEFAULT 1,
    unit_price          NUMERIC(12, 2) NOT NULL DEFAULT 0,
    cost_price          NUMERIC(12, 2) NOT NULL DEFAULT 0,
    subtotal            NUMERIC(12, 2) NOT NULL DEFAULT 0,
    pack_label          TEXT
);

CREATE TABLE IF NOT EXISTS public.customer_debts (
    id                  BIGINT PRIMARY KEY,
    customer_name       TEXT NOT NULL UNIQUE,
    total_debt          NUMERIC(12, 2) NOT NULL DEFAULT 0,
    phone_number        TEXT,
    notes               TEXT,
    updated_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS public.debt_transactions (
    id                  BIGINT PRIMARY KEY,
    debt_id             BIGINT REFERENCES public.customer_debts(id) ON DELETE CASCADE,
    sale_id             BIGINT,
    type                TEXT NOT NULL,
    amount              NUMERIC(12, 2) NOT NULL,
    balance_after       NUMERIC(12, 2) NOT NULL,
    notes               TEXT,
    created_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS public.gcash_transactions (
    id                  BIGINT PRIMARY KEY,
    transaction_id      BIGINT REFERENCES public.transactions(id) ON DELETE CASCADE,
    flow_type           TEXT NOT NULL,
    input_amount        NUMERIC(12, 2) NOT NULL,
    principal_amount    NUMERIC(12, 2) NOT NULL,
    fee                 NUMERIC(12, 2) NOT NULL,
    total_collected     NUMERIC(12, 2) NOT NULL,
    reference_number    TEXT,
    mobile_number       TEXT,
    created_at          TIMESTAMPTZ DEFAULT NOW()
);

-- Performance Indexes
CREATE INDEX IF NOT EXISTS idx_cloud_products_barcode ON public.products(barcode);
CREATE INDEX IF NOT EXISTS idx_cloud_txns_created_at ON public.transactions(created_at);
CREATE INDEX IF NOT EXISTS idx_cloud_txn_items_txnid ON public.transaction_items(transaction_id);
CREATE INDEX IF NOT EXISTS idx_cloud_debts_customer ON public.customer_debts(customer_name);


-- 3. ROW LEVEL SECURITY (RLS) & ACCESS HARDENING
-- ==============================================================================

ALTER TABLE public.products ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.transactions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.transaction_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.customer_debts ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.debt_transactions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.gcash_transactions ENABLE ROW LEVEL SECURITY;

-- Drop all legacy permissive policies
DROP POLICY IF EXISTS "Allow public read on products" ON public.products;
DROP POLICY IF EXISTS "Allow public read on transactions" ON public.transactions;
DROP POLICY IF EXISTS "Allow public read on transaction_items" ON public.transaction_items;
DROP POLICY IF EXISTS "Allow public read on customer_debts" ON public.customer_debts;
DROP POLICY IF EXISTS "Allow public read on debt_transactions" ON public.debt_transactions;
DROP POLICY IF EXISTS "Allow public read on gcash_transactions" ON public.gcash_transactions;

DROP POLICY IF EXISTS "Allow write on products" ON public.products;
DROP POLICY IF EXISTS "Allow write on transactions" ON public.transactions;
DROP POLICY IF EXISTS "Allow write on transaction_items" ON public.transaction_items;
DROP POLICY IF EXISTS "Allow write on customer_debts" ON public.customer_debts;
DROP POLICY IF EXISTS "Allow write on debt_transactions" ON public.debt_transactions;
DROP POLICY IF EXISTS "Allow write on gcash_transactions" ON public.gcash_transactions;

DROP POLICY IF EXISTS "Allow authenticated write products" ON public.products;
DROP POLICY IF EXISTS "Allow authenticated access transactions" ON public.transactions;
DROP POLICY IF EXISTS "Allow authenticated access transaction_items" ON public.transaction_items;
DROP POLICY IF EXISTS "Allow authenticated access customer_debts" ON public.customer_debts;
DROP POLICY IF EXISTS "Allow authenticated access debt_transactions" ON public.debt_transactions;
DROP POLICY IF EXISTS "Allow authenticated access gcash_transactions" ON public.gcash_transactions;

-- Products: Anonymous users can only read the catalog; authenticated users can manage products
CREATE POLICY "Allow public read on products"
ON public.products FOR SELECT
TO anon, authenticated
USING (true);

CREATE POLICY "Allow authenticated write products"
ON public.products FOR ALL
TO authenticated
USING (true)
WITH CHECK (true);

-- Transactions & Items: Authenticated-only access (financial records)
CREATE POLICY "Allow authenticated access transactions"
ON public.transactions FOR ALL
TO authenticated
USING (true)
WITH CHECK (true);

CREATE POLICY "Allow authenticated access transaction_items"
ON public.transaction_items FOR ALL
TO authenticated
USING (true)
WITH CHECK (true);

-- Customer Debt (Utang) & Ledger: Authenticated-only access (privacy & PII protection)
CREATE POLICY "Allow authenticated access customer_debts"
ON public.customer_debts FOR ALL
TO authenticated
USING (true)
WITH CHECK (true);

CREATE POLICY "Allow authenticated access debt_transactions"
ON public.debt_transactions FOR ALL
TO authenticated
USING (true)
WITH CHECK (true);

-- GCash Financial Ledger: Authenticated-only access
CREATE POLICY "Allow authenticated access gcash_transactions"
ON public.gcash_transactions FOR ALL
TO authenticated
USING (true)
WITH CHECK (true);

-- Revoke all table rights from anonymous users except read-only on product catalog
REVOKE ALL ON ALL TABLES IN SCHEMA public FROM anon;
GRANT USAGE ON SCHEMA public TO anon, authenticated;
GRANT SELECT ON public.products TO anon;
GRANT ALL ON ALL TABLES IN SCHEMA public TO authenticated;
