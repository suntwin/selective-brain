-- Past drills: "talk about this with Papa" flags and notes on each answer.
-- Run once in Supabase -> SQL Editor. Safe to re-run.
alter table public.answers add column if not exists discuss boolean not null default false;  -- flagged to talk about
alter table public.answers add column if not exists discuss_note text;                       -- her question, in her words
alter table public.answers add column if not exists parent_note text;                        -- Papa's notes / reply
alter table public.answers add column if not exists discussed boolean not null default false; -- talked it through
alter table public.answers add column if not exists discussed_at timestamptz;
