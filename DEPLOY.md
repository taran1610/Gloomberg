# Deploy Gloomberg so others can use it

You need **two** deployments:

1. **Backend (FastAPI)** → e.g. Render or Railway (Vercel cannot run long-lived Python backends).
2. **Frontend (Next.js)** → Vercel.

Then point the frontend at your backend URL.

---

## 1. Push code to GitHub

```bash
cd /Users/sonal/gloomberg
git init
git add .
git commit -m "Gloomberg MVP"
# Create repo on github.com, then:
git remote add origin https://github.com/YOUR_USERNAME/gloomberg.git
git push -u origin main
```

---

## 2. Deploy the backend (e.g. Render)

1. Go to [render.com](https://render.com) → **New +** → **Web Service**.
2. Connect GitHub and select the **gloomberg** repo.
3. **Root Directory:** `backend`
4. **Runtime:** Python 3
5. **Build Command:** `pip install -r requirements.txt`
6. **Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`
7. **Environment variables** (in Render dashboard):
   - `OPENAI_API_KEY` = your key
   - `FINANCIAL_DATASETS_API_KEY` = your key
   - `FRONTEND_URL` = leave empty for now; set after step 3 to your Vercel URL (e.g. `https://gloomberg.vercel.app`)
   - `REDIS_URL` = optional (app works without Redis)
8. Deploy. Note your backend URL, e.g. `https://gloomberg-xxxx.onrender.com`.

Test: open `https://gloomberg-xxxx.onrender.com/api/health` in the browser — you should see `{"status":"ok",...}`.

---

## 3. Deploy the frontend on Vercel

1. Go to [vercel.com](https://vercel.com) → **Add New** → **Project**.
2. Import your **gloomberg** GitHub repo.
3. **Root Directory:** click **Edit** and set to `frontend`.
4. **Framework Preset:** Next.js (auto).
5. **Environment Variables:**
   - Name: `NEXT_PUBLIC_API_URL`
   - Value: your backend URL from step 2, e.g. `https://gloomberg-xxxx.onrender.com`
   - Apply to Production (and Preview if you want).
6. Click **Deploy**.

Your site will be at `https://gloomberg-xxxx.vercel.app` (or your custom domain).

---

## 4. Allow CORS from Vercel

In Render, set:

- `FRONTEND_URL` = `https://gloomberg-xxxx.vercel.app` (your exact Vercel URL).

Redeploy the backend so it picks up the new env. The backend already uses `FRONTEND_URL` for CORS.

---

## 5. Share the link

Give users your Vercel URL. They use the site; the browser talks to your Render backend automatically.

---

## Waitlist (Supabase)

The waitlist page (`/waitlist`) stores emails in Supabase.

1. **Create a Supabase project** at [supabase.com](https://supabase.com).
2. **Run the table script:** In Supabase Dashboard → **SQL Editor**, run the contents of `supabase/waitlist.sql` (creates the `waitlist` table).
3. **Get credentials:** Project Settings → API. Copy **Project URL** and **service_role** key (secret).
4. **Set env vars for the frontend** (local and Vercel):
   - `NEXT_PUBLIC_SUPABASE_URL` = your Project URL
   - `SUPABASE_SERVICE_ROLE_KEY` = your service_role key  
   Add these in Vercel → Project → Settings → Environment Variables.
5. Emails are stored in the `waitlist` table; view them in Supabase → Table Editor.

**When you’re ready to launch:** see **`docs/WAITLIST.md`** for how to export emails from Supabase and send your launch email.

---

## Optional: custom domain on Vercel

In Vercel → Project → Settings → Domains, add e.g. `gloomberg.yourdomain.com`. Then set `FRONTEND_URL` on Render to that domain and redeploy the backend.
