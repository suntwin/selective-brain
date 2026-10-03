-- Run AFTER creating the two users in Supabase → Authentication → Users → "Add user"
-- (tick "Auto Confirm User"). Replace the two e-mails below, then run in SQL Editor.

with fam as (
  insert into public.families (name) values ('Chawla family') returning id
)
insert into public.profiles (id, family_id, display_name, role, avatar)
select u.id, fam.id,
       case when u.email = 'siyonah@example.com' then 'Siyonah' else 'Papa' end,
       case when u.email = 'siyonah@example.com' then 'child' else 'parent' end,
       case when u.email = 'siyonah@example.com' then '🦄' else '🧭' end
from auth.users u, fam
where u.email in ('siyonah@example.com', 'nitesh.chawla@atturra.com');

select p.display_name, p.role, u.email from public.profiles p join auth.users u on u.id = p.id;
