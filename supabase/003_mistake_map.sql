-- Mistake Map storage (Parent Hub -> Mistake Map, and Notebook -> My focus).
-- Run once in Supabase -> SQL Editor. Safe to re-run.
create table if not exists public.insights (
  id text primary key,                       -- mistake_map_<family id>: one current map per family
  family_id uuid not null references public.families(id) on delete cascade,
  kind text not null default 'mistake_map',
  title text,
  updated date,
  data jsonb not null,                       -- the whole map JSON built by Claude from the vault
  created_at timestamptz default now()
);

alter table public.insights enable row level security;

drop policy if exists insights_select on public.insights;
create policy insights_select on public.insights for select using (family_id = public.my_family());

drop policy if exists insights_write on public.insights;
create policy insights_write on public.insights for all
  using (family_id = public.my_family() and public.is_parent())
  with check (family_id = public.my_family() and public.is_parent());
