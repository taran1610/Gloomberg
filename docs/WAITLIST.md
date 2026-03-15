# Waitlist setup & getting emails for your launch

Use this to validate your MVP: collect emails now, send your launch email when you’re ready.

---

## 1. One-time setup (if you haven’t already)

1. **Supabase**
   - Create a project at [supabase.com](https://supabase.com) (you already have one).
   - In the dashboard go to **SQL Editor** and run the contents of **`supabase/waitlist.sql`** (creates the `waitlist` table).

2. **Frontend env**
   - In **`frontend/.env.local`** (and in Vercel → Settings → Environment Variables for production) set:
     - `NEXT_PUBLIC_SUPABASE_URL` = your Supabase project URL  
     - `SUPABASE_SERVICE_ROLE_KEY` = your Supabase **service_role** key (Settings → API in Supabase).

3. **Deploy**
   - Deploy the frontend (e.g. Vercel). Add the same two env vars there so the JOIN button and `/waitlist` work in production.

After this, every time someone clicks **JOIN** and enters their email on `/waitlist`, the email is saved in Supabase.

---

## 2. Where the emails live

- **Supabase** → your project → **Table Editor** → **`waitlist`**.
- Columns: `id`, `email`, `created_at`.

---

## 3. When MVP is complete: get the emails

**Option A – Export from Supabase (easiest)**

1. Supabase → **Table Editor** → **waitlist**.
2. Use the table menu (e.g. **⋮** or “Export”) to **export as CSV** (or use the built-in export if your plan has it).
3. You get a file with one email per row (and optional `id`, `created_at`). Use the `email` column for your launch email.

**Option B – Copy with SQL**

1. Supabase → **SQL Editor**.
2. Run:
   ```sql
   select email from public.waitlist order by created_at desc;
   ```
3. Copy the results or export the result set as CSV if the UI allows it.

---

## 4. Sending the launch email

Use any tool you like; you only need the list of emails.

- **Resend / SendGrid / Mailchimp / Loops**  
  Create a campaign or “audience”, then **import the CSV** (or paste emails). Write your launch message and send.

- **Gmail (manual)**  
  Paste the emails into Bcc and send one “We’re live!” email. Fine for a small list.

- **No-code**  
  Export CSV from Supabase → import into your chosen email tool → send.

You don’t need any extra backend for sending; the “backend” for the waitlist is Supabase. This doc is the only setup you need to get emails and send them when the MVP is complete.
