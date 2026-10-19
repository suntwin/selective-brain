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
  discuss boolean not null default false,   -- "talk about this with Papa" (Past drills)
  discuss_note text,                        -- her question, in her words
  parent_note text,                         -- Papa's notes / reply
  discussed boolean not null default false,
  discussed_at timestamptz,
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

-- ---------------------------------------------------------------
-- (004_discuss.sql adds the discuss* / parent_note columns above to an existing database)

-- ---------------------------------------------------------------
-- Mistake Map (same as 003_mistake_map.sql)
-- ---------------------------------------------------------------
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

-- ---------------------------------------------------------------
-- Test Review (same as 005_test_review.sql)
-- ---------------------------------------------------------------

create table if not exists public.tests (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.profiles(id) on delete cascade,
  title text not null,                        -- e.g. "Term 3 Test 2"
  test_date date not null default current_date,
  source text,                                -- School test | Practice paper | Mock exam | Other
  subject text not null default 'Maths',      -- Maths | Reading | Verbal | Writing | English
  score numeric,
  total numeric,
  minutes int,
  ran_out_of_time boolean not null default false,
  notes text,
  status text not null default 'in_progress' check (status in ('in_progress','done')),
  finished_at timestamptz,
  parent_checked boolean not null default false,  -- Papa looked over her tags
  parent_note text,
  exported_at timestamptz,
  created_at timestamptz default now()
);

create table if not exists public.test_mistakes (
  id uuid primary key default gen_random_uuid(),
  test_id uuid not null references public.tests(id) on delete cascade,
  user_id uuid not null references public.profiles(id) on delete cascade,
  kind text not null default 'lost' check (kind in ('lost','lucky')),  -- lost mark | right but a lucky guess
  q_ref text not null,                        -- "Q12", "Paper 2 Q5b"
  marks numeric not null default 1,           -- marks lost on this question
  topic text,
  loss_type text check (loss_type in ('method','misread','final','slip','skipped','time') or loss_type is null),
  parent_type text check (parent_type in ('method','misread','final','slip','skipped','time') or parent_type is null),
  confidence text check (confidence in ('sure','unsure','guess') or confidence is null),
  what_i_did text,
  should_do text,
  card_id uuid,                               -- notebook card made from it (if any)
  redo_box int not null default 0,            -- 0 = first redo due (3 days), 1 = second (14 days)
  redo_next date,
  redo_count int not null default 0,
  fixed boolean not null default false,       -- two clean redos in a row
  fixed_at timestamptz,
  discuss boolean not null default false,
  discuss_note text,
  parent_note text,
  discussed boolean not null default false,
  created_at timestamptz default now()
);

alter table public.tests enable row level security;
alter table public.test_mistakes enable row level security;

do $$
declare t text;
begin
  foreach t in array array['tests','test_mistakes'] loop
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

create index if not exists idx_tests_user on public.tests(user_id, test_date);
create index if not exists idx_test_mistakes_user on public.test_mistakes(user_id, redo_next);

-- ---------------------------------------------------------------
-- Routine & Reward Shop (same as 006_routine_rewards.sql)
-- ---------------------------------------------------------------

-- Her pinned shop goal (a savings bar on Home)
alter table public.profiles add column if not exists reward_goal uuid;

-- ---------------------------------------------------------------- timetable (the family edits it)
create table if not exists public.routine_blocks (
  id uuid primary key default gen_random_uuid(),
  family_id uuid not null references public.families(id) on delete cascade,
  weekday int not null check (weekday between 0 and 6),   -- 0 = Monday … 6 = Sunday
  start_time text,                                        -- 'HH:MM' 24 h; null = any time
  end_time text,
  kind text not null default 'Other',                     -- Maths, English, Writing, School work, Reading, Tennis, Tennis match, Swimming, Other
  title text not null,
  optional boolean not null default false,                -- 'only if needed': doesn't block the whole-day bonus
  active boolean not null default true,                   -- removed blocks are hidden, history stays
  updated_by uuid,
  updated_at timestamptz default now(),
  created_at timestamptz default now()
);

-- ---------------------------------------------------------------- her ticks
create table if not exists public.routine_logs (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.profiles(id) on delete cascade,
  block_id uuid references public.routine_blocks(id) on delete set null,
  day date not null,
  status text not null check (status in ('done','approved','declined','skipped','excused')),
  title text, kind text, minutes int,
  xp int not null default 0,                              -- snapshotted when ticked, paid when approved
  note text,                                              -- her skip reason
  parent_note text,
  ticked_at timestamptz,
  reviewed_at timestamptz,
  reviewed_by uuid,
  created_at timestamptz default now(),
  unique (user_id, block_id, day)
);

-- ---------------------------------------------------------------- shop
create table if not exists public.rewards (
  id uuid primary key default gen_random_uuid(),
  family_id uuid not null references public.families(id) on delete cascade,
  emoji text default '🎁',
  title text not null,
  category text not null default 'Treats',               -- Books | Tennis | Treats
  cost int not null check (cost >= 0),
  ask_book boolean not null default false,               -- ask 'which book?' on swap
  active boolean not null default true,
  sort int default 0,
  created_at timestamptz default now()
);

create table if not exists public.redemptions (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.profiles(id) on delete cascade,
  reward_id uuid references public.rewards(id) on delete set null,
  title text not null, emoji text, category text,
  cost int not null,
  status text not null default 'requested' check (status in ('requested','given','declined')),
  note text,                                              -- e.g. which book she wants
  parent_note text,
  decided_at timestamptz,
  created_at timestamptz default now()
);

create table if not exists public.book_wishlist (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.profiles(id) on delete cascade,
  title text not null,
  author text,
  status text not null default 'want',
  created_at timestamptz default now()
);

-- ---------------------------------------------------------------- security
alter table public.routine_blocks enable row level security;
alter table public.routine_logs enable row level security;
alter table public.rewards enable row level security;
alter table public.redemptions enable row level security;
alter table public.book_wishlist enable row level security;

-- the timetable: anyone in the family can read and change it (she and Mum plan it together)
drop policy if exists routine_blocks_all on public.routine_blocks;
create policy routine_blocks_all on public.routine_blocks for all
  using (family_id = public.my_family()) with check (family_id = public.my_family());

-- the shop: family reads, parents edit
drop policy if exists rewards_select on public.rewards;
create policy rewards_select on public.rewards for select using (family_id = public.my_family());
drop policy if exists rewards_write on public.rewards;
create policy rewards_write on public.rewards for all
  using (family_id = public.my_family() and public.is_parent())
  with check (family_id = public.my_family() and public.is_parent());

-- per-person rows: she writes her own; a parent can also write for the family (confirm, excuse, hand over)
do $$
declare t text;
begin
  foreach t in array array['routine_logs','redemptions','book_wishlist'] loop
    execute format('drop policy if exists %1$s_select on public.%1$s', t);
    execute format('create policy %1$s_select on public.%1$s for select using (public.in_my_family(user_id))', t);
    execute format('drop policy if exists %1$s_insert on public.%1$s', t);
    execute format('create policy %1$s_insert on public.%1$s for insert with check (user_id = auth.uid() or (public.is_parent() and public.in_my_family(user_id)))', t);
    execute format('drop policy if exists %1$s_update on public.%1$s', t);
    execute format('create policy %1$s_update on public.%1$s for update using (user_id = auth.uid() or (public.is_parent() and public.in_my_family(user_id)))', t);
    execute format('drop policy if exists %1$s_delete on public.%1$s', t);
    execute format('create policy %1$s_delete on public.%1$s for delete using (user_id = auth.uid() or (public.is_parent() and public.in_my_family(user_id)))', t);
  end loop;
end $$;

-- a parent confirming her routine pays XP into HER xp_events
drop policy if exists xp_events_parent_insert on public.xp_events;
create policy xp_events_parent_insert on public.xp_events for insert
  with check (public.is_parent() and public.in_my_family(user_id));

create index if not exists idx_routine_blocks_fam on public.routine_blocks(family_id, weekday);
create index if not exists idx_routine_logs_user on public.routine_logs(user_id, day);
create index if not exists idx_redemptions_user on public.redemptions(user_id, status);

-- ---------------------------------------------------------------- starters (only for families that have none yet)
-- Siyonah's paper timetable, worked out with Mum (19 Oct 2026). Saturday is free.
insert into public.routine_blocks (family_id, weekday, start_time, end_time, kind, title, optional)
select f.id, v.wd, v.s, v.e, v.k, v.t, v.o
from public.families f
cross join (values
  (0, '16:00', '17:00', 'School work', 'School work', false),
  (0, '17:00', '18:00', 'Tennis', 'Tennis', false),
  (0, '18:30', '20:30', 'Maths', 'Maths with Preetha''s mum', false),
  (0, '21:00', '22:30', 'English', 'English', false),
  (1, '16:30', '18:00', 'English', 'English', false),
  (1, '18:30', '19:30', 'Swimming', 'Swimming', false),
  (1, '21:00', '22:30', 'Maths', 'Maths', false),
  (2, '16:30', '18:30', 'English', 'English', false),
  (2, '19:30', '21:30', 'Maths', 'Maths', false),
  (2, '21:30', '22:00', 'School work', 'School work', false),
  (3, '16:30', '18:30', 'English', 'English', false),
  (3, '19:30', '21:30', 'Maths', 'Maths', false),
  (3, '21:30', '22:00', 'School work', 'School work (if any)', true),
  (4, '16:30', '18:30', 'English', 'English', false),
  (4, '19:30', '21:30', 'Maths', 'Maths', false),
  (4, '21:30', '22:00', 'School work', 'School work', false),
  (6, null, null, 'Tennis match', 'Tennis match', false)
) as v(wd, s, e, k, t, o)
where not exists (select 1 from public.routine_blocks b where b.family_id = f.id);

insert into public.rewards (family_id, emoji, title, category, cost, ask_book, sort)
select f.id, v.em, v.t, v.c, v.cost, v.ask, v.n
from public.families f
cross join (values
  ('🌙', '+30 min bedtime reading (one night)', 'Books', 150, false, 0),
  ('🏛️', 'Library adventure: pick 5 books', 'Books', 250, false, 1),
  ('🔖', 'Fancy bookmark or reading-notebook set', 'Books', 400, false, 2),
  ('🛋️', 'Reading night-in: blanket fort + snacks', 'Books', 500, false, 3),
  ('☕', 'Bookshop trip + hot chocolate', 'Books', 600, false, 4),
  ('📕', 'A new paperback of my choice', 'Books', 1200, true, 5),
  ('📗', 'A new hardback or special edition', 'Books', 2000, true, 6),
  ('📚', 'A whole book series box set', 'Books', 5000, true, 7),
  ('🎾', 'New tube of tennis balls', 'Tennis', 300, false, 8),
  ('🖐️', 'New overgrips for my racquet', 'Tennis', 350, false, 9),
  ('👨‍👧', 'Hitting session with Papa (I pick the drills)', 'Tennis', 400, false, 10),
  ('🎽', 'Tennis headband / wristbands', 'Tennis', 700, false, 11),
  ('🏟️', 'Watch a live pro tennis match', 'Tennis', 4000, false, 12),
  ('🍦', 'Weekend treat of my choice', 'Treats', 300, false, 13)
) as v(em, t, c, cost, ask, n)
where not exists (select 1 from public.rewards r where r.family_id = f.id);
