-- Run this in Supabase SQL Editor (Dashboard → SQL Editor) to create the waitlist table.

create table if not exists public.waitlist (
  id uuid primary key default gen_random_uuid(),
  email text not null unique,
  created_at timestamptz not null default now()
);

-- Optional: enable RLS and allow anonymous insert (if you ever call Supabase from client with anon key).
-- For now the app uses a Next.js API route with the service role key, so RLS is not required.
-- alter table public.waitlist enable row level security;
-- create policy "Allow anonymous insert" on public.waitlist for insert with (true);

-- Optional: index for listing by date.
create index if not exists waitlist_created_at_idx on public.waitlist (created_at desc);

comment on table public.waitlist is 'Email signups for Gloomberg waitlist';
