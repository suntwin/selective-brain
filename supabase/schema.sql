-- Selective Brain — Supabase schema
-- Run once in Supabase → SQL Editor. Safe to re-run (idempotent where possible).

create extension if not exists "pgcrypto";

-- ---------------------------------------------------------------
-- Families & profiles
-- ---------------------------------------------------------------
create table if not exists public.families (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  created_at timestamptz default now()
);

create table if not exists public.profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  family_id uuid not null references public.families(id) on delete cascade,
  display_name text not null,
  role text not null check (role in ('child','parent')),
  avatar text default '🦄',
  exam_date date default '2027-06-19',
  created_at timestamptz default now()
);

-- Helper: the caller's family (security definer so policies don't recurse)
create or replace function public.my_family() returns uuid
language sql stable security definer set search_path = public as $$
  select family_id from public.profiles where id = auth.uid()
$$;

create or replace function public.is_parent() returns boolean
language sql stable security definer set search_path = public as $$
  select coalesce((select role = 'parent' from public.profiles where id = auth.uid()), false)
$$;

create or replace function public.in_my_family(uid uuid) returns boolean
language sql stable security definer set search_path = public as $$
  select exists (select 1 from public.profiles p
                 where p.id = uid and p.family_id = public.my_family())
$$;

-- ---------------------------------------------------------------
-- Drills (published by parent / Claude)
-- ---------------------------------------------------------------
create table if not exists public.drills (
  id text primary key,                      -- e.g. 2026-10-04_mixed_priorities
  family_id uuid not null references public.families(id) on delete cascade,
  title text not null,
  drill_date date not null,
  minutes int not null default 40,
  pace_seconds int not null default 90,     -- target seconds per question (exam pace)
  subject text not null default 'Maths',
  focus jsonb default '[]'::jsonb,
  questions jsonb not null,                 -- list of question objects (see drills/README)
  source_note text,
  status text not null default 'published' check (status in ('draft','published','archived')),
  created_at timestamptz default now()
);

-- ---------------------------------------------------------------
-- Daily check-in
-- ---------------------------------------------------------------
create table if not exists public.checkins (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.profiles(id) on delete cascade,
  day date not null,
  energy int check (energy between 1 and 5),
  mood text,
  minutes_available int,
  session_size text check (session_size in ('Full','Normal','Light','Rest')),
  created_at timestamptz default now(),
  unique (user_id, day)
);

-- ---------------------------------------------------------------
-- Drill attempts and per-question answers
-- ---------------------------------------------------------------
create table if not exists public.attempts (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.profiles(id) on delete cascade,
  drill_id text not null references public.drills(id) on delete cascade,
  session_size text,
  started_at timestamptz not null default now(),
  finished_at timestamptz,
  time_limit_sec int,
  score int default 0,
  total int default 0,
  xp_earned int default 0,
  beat_clock boolean default false,
  overtime boolean default false,
  question_ids jsonb,                       -- the questions served in this session
  status text not null default 'in_progress' check (status in ('in_progress','finished','reviewed')),
  exported_at timestamptz
);

create table if not exists public.answers (
  id uuid primary key default gen_random_uuid(),
  attempt_id uuid not null references public.attempts(id) on delete cascade,
  user_id uuid not null references public.profiles(id) on delete cascade,
  question_id text not null,
  topic text,
  chosen text,
  correct boolean,
  seconds int,
  reason text check (reason in ('concept','careless','time','misread') or reason is null),
  fix_note text,
  created_at timestamptz default now(),
  unique (attempt_id, question_id)
);

-- ---------------------------------------------------------------
-- Mistake & Technique Notebook (spaced recall)
-- ---------------------------------------------------------------
create table if not exists public.notebook (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.profiles(id) on delete cascade,
  kind text not null check (kind in ('mistake','technique','pattern')),
  topic text,
  title text not null,
  question jsonb,                -- snapshot of the question for mistake cards
  my_fix text,                   -- in her words
  technique text,                -- the method to remember
  reason text,
  source text,                   -- drill id / test name
  box int not null default 0,    -- Leitner box 0..5
  next_review date not null default current_date,
  reviews int not null default 0,
  mastered boolean not null default false,
  created_at timestamptz default now()
);

-- ---------------------------------------------------------------
-- Gamification
-- ---------------------------------------------------------------
create table if not exists public.xp_events (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.profiles(id) on delete cascade,
  amount int not null,
  reason text not null,
  created_at timestamptz default now()
);

create table if not exists public.badges (
  user_id uuid not null references public.profiles(id) on delete cascade,
  badge_key text not null,
  earned_at timestamptz default now(),
  primary key (user_id, badge_key)
);

-- ---------------------------------------------------------------
-- Row Level Security: everyone sees their own family's rows.
-- Children write their own rows; parents can also write drills.
-- ---------------------------------------------------------------
alter table public.families  enable row level security;
alter table public.profiles  enable row level security;
alter table public.drills    enable row level security;
alter table public.checkins  enable row level security;
alter table public.attempts  enable row level security;
alter table public.answers   enable row level security;
alter table public.notebook  enable row level security;
alter table public.xp_events enable row level security;
alter table public.badges    enable row level security;

drop policy if exists fam_select on public.families;
create policy fam_select on public.families for select using (id = public.my_family());

drop policy if exists prof_select on public.profiles;
create policy prof_select on public.profiles for select using (family_id = public.my_family());
drop policy if exists prof_update on public.profiles;
create policy prof_update on public.profiles for update using (id = auth.uid());

drop policy if exists drills_select on public.drills;
create policy drills_select on public.drills for select using (family_id = public.my_family());
drop policy if exists drills_write on public.drills;
create policy drills_write on public.drills for all
  using (family_id = public.my_family() and public.is_parent())
  with check (family_id = public.my_family() and public.is_parent());

-- Generic per-user tables: read family, write own
do $$
declare t text;
begin
  foreach t in array array['checkins','attempts','answers','notebook','xp_events','badges'] loop
    execute format('drop policy if exists %1$s_select on public.%1$s', t);
    execute format('create policy %1$s_select on public.%1$s for select using (public.in_my_family(user_id))', t);
    execute format('drop policy if exists %1$s_insert on public.%1$s', t);
    execute format('create policy %1$s_insert on public.%1$s for insert with check (user_id = auth.uid())', t);
    execute format('drop policy if exists %1$s_update on public.%1$s', t);
    execute format('create policy %1$s_update on public.%1$s for update using (user_id = auth.uid() or (public.is_parent() and public.in_my_family(user_id)))', t);
    execute format('drop policy if exists %1$s_delete on public.%1$s', t);
    execute format('create policy %1$s_delete on public.%1$s for delete using (user_id = auth.uid() or (public.is_parent() and public.in_my_family(user_id)))', t);
  end loop;
end $$;

create index if not exists idx_answers_user on public.answers(user_id, created_at);
create index if not exists idx_attempts_user on public.attempts(user_id, started_at);
create index if not exists idx_notebook_review on public.notebook(user_id, next_review);
create index if not exists idx_xp_user on public.xp_events(user_id);
