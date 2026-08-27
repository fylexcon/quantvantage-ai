-- ==========================================================================
-- Migration: Sentiment History Table
-- ==========================================================================

create table if not exists public.sentiment_history (
    id uuid primary key default gen_random_uuid(),
    ticker varchar not null,
    score float not null,
    sentiment_label varchar not null,
    article_count int not null,
    dedup_hash varchar unique not null,
    created_at timestamptz not null default now()
);

-- Index on ticker and created_at for fast time-series querying
create index if not exists sentiment_history_ticker_created_at_idx
    on public.sentiment_history (ticker, created_at desc);

-- Enable Row Level Security
alter table public.sentiment_history enable row level security;

-- Policy allowing full access to the service_role
drop policy if exists "Service role has full access" on public.sentiment_history;
create policy "Service role has full access"
on public.sentiment_history
for all
to service_role
using (true)
with check (true);
