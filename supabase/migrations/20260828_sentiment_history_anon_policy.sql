-- ==========================================================================
-- Migration: Add anon SELECT policy for sentiment_history
-- ==========================================================================

CREATE POLICY "Allow anon read access on sentiment_history" 
ON public.sentiment_history 
FOR SELECT 
TO anon 
USING (true);
