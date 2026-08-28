-- ==========================================================================
-- Migration: Add model_prediction to Sentiment History Table
-- ==========================================================================

ALTER TABLE public.sentiment_history ADD COLUMN IF NOT EXISTS model_prediction FLOAT;
NOTIFY pgrst, 'reload schema';
