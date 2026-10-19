-- Routine & Reward Shop: Siyonah's weekly timetable (ticked off, confirmed by a parent, paid in XP)
-- and a shop where XP is swapped for books, tennis treats and outings.
-- Run once in Supabase -> SQL Editor. Safe to re-run.

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
