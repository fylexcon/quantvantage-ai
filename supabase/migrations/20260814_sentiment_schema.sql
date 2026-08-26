-- ==========================================================================
-- Migration: Sentiment History Table
-- Stores AI-analyzed financial sentiment data from n8n automation pipeline.
-- ==========================================================================

create table if not exists public.sentiment_history (
    id uuid primary key default gen_random_uuid(),

    -- Nullable: NULL = system-wide news (n8n ingestion), non-NULL = tenant-specific
    tenant_id uuid references public.tenants(id) on delete cascade,

    ticker text not null check (
        ticker = upper(ticker)
        and ticker ~ '^[A-Z0-9.-]{1,16}$'
    ),

    source text not null check (char_length(trim(source)) > 0),

    -- Full Gemini structured output (sentiment, score, impact_duration, summary)
    analysis jsonb not null check (jsonb_typeof(analysis) = 'object'),

    -- SHA-256 hash of the article headline for deduplication
    headline_hash text unique,

    -- The original timestamp string from the n8n payload, parsed to timestamptz
    raw_timestamp timestamptz not null,

    created_at timestamptz not null default now()
);

-- ---------------------------------------------------------------------------
-- Indexes
-- ---------------------------------------------------------------------------

-- Tenant-scoped chronological queries
create index if not exists sentiment_history_tenant_id_created_at_idx
    on public.sentiment_history (tenant_id, created_at desc);

-- Per-ticker historical lookups (primary query pattern for dashboards)
create index if not exists sentiment_history_ticker_created_at_idx
    on public.sentiment_history (ticker, created_at desc);

-- Fast deduplication lookups
create index if not exists sentiment_history_headline_hash_idx
    on public.sentiment_history (headline_hash)
    where headline_hash is not null;

-- ---------------------------------------------------------------------------
-- Row Level Security
-- ---------------------------------------------------------------------------

alter table public.sentiment_history enable row level security;

-- Service role has unrestricted access (backend n8n writes)
grant all
    on public.sentiment_history
    to service_role;

-- Authenticated users: full CRUD scoped to their tenant
grant select, insert, update, delete
    on public.sentiment_history
    to authenticated;

-- Anonymous users: read-only access to public (system-wide) sentiment
grant select
    on public.sentiment_history
    to anon;

-- ---------------------------------------------------------------------------
-- RLS Policies: Authenticated Users (Tenant-Scoped)
-- ---------------------------------------------------------------------------

drop policy if exists "Tenant members can read sentiment" on public.sentiment_history;
create policy "Tenant members can read sentiment"
on public.sentiment_history
for select
to authenticated
using (
    tenant_id is null  -- system-wide sentiment is visible to all
    or tenant_id = public.current_tenant_id()
);

drop policy if exists "Tenant members can create sentiment" on public.sentiment_history;
create policy "Tenant members can create sentiment"
on public.sentiment_history
for insert
to authenticated
with check (
    tenant_id is null
    or tenant_id = public.current_tenant_id()
);

drop policy if exists "Tenant members can update sentiment" on public.sentiment_history;
create policy "Tenant members can update sentiment"
on public.sentiment_history
for update
to authenticated
using (
    tenant_id is null
    or tenant_id = public.current_tenant_id()
)
with check (
    tenant_id is null
    or tenant_id = public.current_tenant_id()
);

drop policy if exists "Tenant members can delete sentiment" on public.sentiment_history;
create policy "Tenant members can delete sentiment"
on public.sentiment_history
for delete
to authenticated
using (
    tenant_id is null
    or tenant_id = public.current_tenant_id()
);

-- ---------------------------------------------------------------------------
-- RLS Policies: Anonymous Users (Read-Only, System-Wide Only)
-- ---------------------------------------------------------------------------

drop policy if exists "Anon can read system-wide sentiment" on public.sentiment_history;
create policy "Anon can read system-wide sentiment"
on public.sentiment_history
for select
to anon
using (tenant_id is null);
