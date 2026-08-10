create extension if not exists pgcrypto;

create table if not exists public.tenants (
    id uuid primary key default gen_random_uuid(),
    name text not null check (char_length(trim(name)) > 0),
    created_at timestamptz not null default now(),
    subscription_tier text not null default 'starter'
        check (subscription_tier in ('starter', 'growth', 'enterprise'))
);

create table if not exists public.profiles (
    id uuid primary key references auth.users(id) on delete cascade,
    tenant_id uuid not null references public.tenants(id) on delete cascade,
    role text not null default 'member'
        check (role in ('owner', 'admin', 'member'))
);

create table if not exists public.api_keys (
    id uuid primary key default gen_random_uuid(),
    tenant_id uuid not null references public.tenants(id) on delete cascade,
    key_hash text not null unique,
    created_at timestamptz not null default now(),
    is_active boolean not null default true
);

create table if not exists public.predictions (
    id uuid primary key default gen_random_uuid(),
    tenant_id uuid not null references public.tenants(id) on delete cascade,
    ticker text not null check (
        ticker = upper(ticker)
        and ticker ~ '^[A-Z0-9.-]{1,16}$'
    ),
    forecast_data jsonb not null check (jsonb_typeof(forecast_data) = 'object'),
    created_at timestamptz not null default now()
);

create index if not exists profiles_tenant_id_idx on public.profiles (tenant_id);
create index if not exists api_keys_tenant_id_idx on public.api_keys (tenant_id);
create index if not exists predictions_tenant_id_created_at_idx
    on public.predictions (tenant_id, created_at desc);
create index if not exists predictions_tenant_id_ticker_idx
    on public.predictions (tenant_id, ticker);

create or replace function public.current_tenant_id()
returns uuid
language sql
stable
security definer
set search_path = public
as $$
    select tenant_id
    from public.profiles
    where id = auth.uid()
$$;

revoke all on function public.current_tenant_id() from public;
grant execute on function public.current_tenant_id() to authenticated;

alter table public.tenants enable row level security;
alter table public.profiles enable row level security;
alter table public.api_keys enable row level security;
alter table public.predictions enable row level security;

grant select, insert, update, delete
    on public.tenants, public.profiles, public.predictions
    to authenticated;

revoke all on public.api_keys from authenticated;
grant select (id, tenant_id, created_at, is_active)
    on public.api_keys
    to authenticated;
grant insert (tenant_id, key_hash, is_active)
    on public.api_keys
    to authenticated;
grant update (key_hash, is_active)
    on public.api_keys
    to authenticated;
grant delete
    on public.api_keys
    to authenticated;

grant all
    on public.tenants, public.profiles, public.api_keys, public.predictions
    to service_role;

drop policy if exists "Tenant members can read their tenant" on public.tenants;
create policy "Tenant members can read their tenant"
on public.tenants
for select
to authenticated
using (id = public.current_tenant_id());

drop policy if exists "Tenant members can update their tenant" on public.tenants;
create policy "Tenant members can update their tenant"
on public.tenants
for update
to authenticated
using (id = public.current_tenant_id())
with check (id = public.current_tenant_id());

drop policy if exists "Tenant members can read tenant profiles" on public.profiles;
create policy "Tenant members can read tenant profiles"
on public.profiles
for select
to authenticated
using (tenant_id = public.current_tenant_id());

drop policy if exists "Tenant members can create tenant profiles" on public.profiles;
create policy "Tenant members can create tenant profiles"
on public.profiles
for insert
to authenticated
with check (tenant_id = public.current_tenant_id());

drop policy if exists "Tenant members can update tenant profiles" on public.profiles;
create policy "Tenant members can update tenant profiles"
on public.profiles
for update
to authenticated
using (tenant_id = public.current_tenant_id())
with check (tenant_id = public.current_tenant_id());

drop policy if exists "Tenant members can delete tenant profiles" on public.profiles;
create policy "Tenant members can delete tenant profiles"
on public.profiles
for delete
to authenticated
using (tenant_id = public.current_tenant_id());

drop policy if exists "Tenant members can read tenant API keys" on public.api_keys;
create policy "Tenant members can read tenant API keys"
on public.api_keys
for select
to authenticated
using (tenant_id = public.current_tenant_id());

drop policy if exists "Tenant members can create tenant API keys" on public.api_keys;
create policy "Tenant members can create tenant API keys"
on public.api_keys
for insert
to authenticated
with check (tenant_id = public.current_tenant_id());

drop policy if exists "Tenant members can update tenant API keys" on public.api_keys;
create policy "Tenant members can update tenant API keys"
on public.api_keys
for update
to authenticated
using (tenant_id = public.current_tenant_id())
with check (tenant_id = public.current_tenant_id());

drop policy if exists "Tenant members can delete tenant API keys" on public.api_keys;
create policy "Tenant members can delete tenant API keys"
on public.api_keys
for delete
to authenticated
using (tenant_id = public.current_tenant_id());

drop policy if exists "Tenant members can read tenant predictions" on public.predictions;
create policy "Tenant members can read tenant predictions"
on public.predictions
for select
to authenticated
using (tenant_id = public.current_tenant_id());

drop policy if exists "Tenant members can create tenant predictions" on public.predictions;
create policy "Tenant members can create tenant predictions"
on public.predictions
for insert
to authenticated
with check (tenant_id = public.current_tenant_id());

drop policy if exists "Tenant members can update tenant predictions" on public.predictions;
create policy "Tenant members can update tenant predictions"
on public.predictions
for update
to authenticated
using (tenant_id = public.current_tenant_id())
with check (tenant_id = public.current_tenant_id());

drop policy if exists "Tenant members can delete tenant predictions" on public.predictions;
create policy "Tenant members can delete tenant predictions"
on public.predictions
for delete
to authenticated
using (tenant_id = public.current_tenant_id());