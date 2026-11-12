-- ====================================================================
-- PocketTrack Database Schema
-- Supabase PostgreSQL migration for the 'expenses' table
-- ====================================================================

-- Enable UUID extension (enabled by default in Supabase)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- --------------------------------------------------------------------
-- Table: public.expenses
-- --------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.expenses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    amount NUMERIC NOT NULL CHECK (amount > 0),
    date DATE,
    category TEXT NOT NULL DEFAULT 'Uncategorized',
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

-- --------------------------------------------------------------------
-- Indexes for performance and common query patterns
-- --------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_expenses_user_id ON public.expenses(user_id);
CREATE INDEX IF NOT EXISTS idx_expenses_date ON public.expenses(date);
CREATE INDEX IF NOT EXISTS idx_expenses_user_date ON public.expenses(user_id, date);

-- --------------------------------------------------------------------
-- Row Level Security (RLS)
-- --------------------------------------------------------------------
ALTER TABLE public.expenses ENABLE ROW LEVEL SECURITY;

-- Drop existing policies if re-running
DROP POLICY IF EXISTS "Users can view their own expenses" ON public.expenses;
DROP POLICY IF EXISTS "Users can insert their own expenses" ON public.expenses;
DROP POLICY IF EXISTS "Users can update their own expenses" ON public.expenses;
DROP POLICY IF EXISTS "Users can delete their own expenses" ON public.expenses;

-- SELECT Policy
CREATE POLICY "Users can view their own expenses"
ON public.expenses
FOR SELECT
TO authenticated
USING (auth.uid() = user_id);

-- INSERT Policy
CREATE POLICY "Users can insert their own expenses"
ON public.expenses
FOR INSERT
TO authenticated
WITH CHECK (auth.uid() = user_id);

-- UPDATE Policy
CREATE POLICY "Users can update their own expenses"
ON public.expenses
FOR UPDATE
TO authenticated
USING (auth.uid() = user_id)
WITH CHECK (auth.uid() = user_id);

-- DELETE Policy
CREATE POLICY "Users can delete their own expenses"
ON public.expenses
FOR DELETE
TO authenticated
USING (auth.uid() = user_id);
