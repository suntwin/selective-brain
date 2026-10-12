-- Test Review: Siyonah logs the marks she lost on paper tests (school tests, practice papers, mocks).
-- Run once in Supabase -> SQL Editor. Safe to re-run.

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
