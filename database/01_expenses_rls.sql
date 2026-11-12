-- ====================================================================
-- PocketTrack Row Level Security (RLS) Migration
-- File: 01_expenses_rls.sql
-- ====================================================================
-- Description:
-- Configures Row Level Security (RLS) on the public.expenses table so that
-- users can only SELECT, INSERT, UPDATE, and DELETE their own records.
--
-- Instructions for Supabase SQL Editor:
-- 1. Open the Supabase Dashboard -> SQL Editor.
-- 2. Paste the contents of this file into a new query tab.
-- 3. Click "Run" to apply the policies.
-- ====================================================================

-- 1. Ensure Row Level Security is enabled
ALTER TABLE public.expenses ENABLE ROW LEVEL SECURITY;

-- 2. Drop any legacy/duplicate policies if they exist
DROP POLICY IF EXISTS "Users can view their own expenses" ON public.expenses;
DROP POLICY IF EXISTS "Users can insert their own expenses" ON public.expenses;
DROP POLICY IF EXISTS "Users can update their own expenses" ON public.expenses;
DROP POLICY IF EXISTS "Users can delete their own expenses" ON public.expenses;

-- 3. Policy: SELECT (Users can only read their own expenses)
CREATE POLICY "Users can view their own expenses"
ON public.expenses
FOR SELECT
TO authenticated
USING (auth.uid() = user_id);

-- 4. Policy: INSERT (Users can only insert records with their own user_id)
CREATE POLICY "Users can insert their own expenses"
ON public.expenses
FOR INSERT
TO authenticated
WITH CHECK (auth.uid() = user_id);

-- 5. Policy: UPDATE (Users can only update their own records, and cannot reassign user_id)
CREATE POLICY "Users can update their own expenses"
ON public.expenses
FOR UPDATE
TO authenticated
USING (auth.uid() = user_id)
WITH CHECK (auth.uid() = user_id);

-- 6. Policy: DELETE (Users can only delete their own records)
CREATE POLICY "Users can delete their own expenses"
ON public.expenses
FOR DELETE
TO authenticated
USING (auth.uid() = user_id);

