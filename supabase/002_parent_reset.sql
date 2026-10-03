-- Lets the parent delete test data for the family's child (used by Parent Hub → Settings → Reset).
-- Run once in Supabase → SQL Editor. Safe to re-run.
do $$
declare t text;
begin
  foreach t in array array['checkins','attempts','answers','notebook','xp_events','badges'] loop
    execute format('drop policy if exists %1$s_delete on public.%1$s', t);
    execute format('create policy %1$s_delete on public.%1$s for delete using (user_id = auth.uid() or (public.is_parent() and public.in_my_family(user_id)))', t);
  end loop;
end $$;
