# Make Gloomberg live — quick checklist

Follow these in order. When done, anyone can open your Vercel URL and use the site.

---

## 1. Push to GitHub

```bash
cd /Users/sonal/gloomberg
git init
git add .
git commit -m "Gloomberg MVP"
```

Create a new repo on [github.com](https://github.com/new) (e.g. name: `gloomberg`), then:

```bash
git remote add origin https://github.com/YOUR_USERNAME/gloomberg.git
git branch -M main
git push -u origin main
```

---

## 2. Deploy backend (Render)

1. Go to [render.com](https://render.com) → **New +** → **Web Service**.
2. Connect GitHub → choose the **gloomberg** repo.
3. Settings:
   - **Root Directory:** `backend`
   - **Runtime:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`
4. **Environment** (Add Environment Variable):
   - `OPENAI_API_KEY` = your OpenAI key
   - `FINANCIAL_DATASETS_API_KEY` = your key (if you have one)
   - `FRONTEND_URL` = leave blank for now
   - `EDGAR_IDENTITY` = your email (SEC requires this for ownership/insider data)
   - `REDIS_URL` = **recommended** for faster loads — see [docs/REDIS_SETUP.md](docs/REDIS_SETUP.md) (Upstash free tier, ~2 min)
5. Click **Create Web Service**. Wait for the first deploy to finish.
6. Copy your backend URL, e.g. `https://gloomberg-xxxx.onrender.com`.
7. Test: open `https://YOUR-BACKEND-URL/api/health` in a browser. You should see `{"status":"ok",...}`.

---

## 3. Deploy frontend (Vercel)

1. Go to [vercel.com](https://vercel.com) → **Add New** → **Project**.
2. Import your **gloomberg** repo from GitHub.
3. Settings:
   - **Root Directory:** click **Edit** → set to `frontend` → **Continue**.
   - **Framework Preset:** Next.js (should be auto-detected).
4. **Environment Variables** → Add:
   - **Name:** `NEXT_PUBLIC_API_URL`  
   - **Value:** your Render backend URL from step 2 (e.g. `https://gloomberg-xxxx.onrender.com`)  
   - **Environment:** Production (and Preview if you want).
   - Add waitlist vars so JOIN works:
     - `NEXT_PUBLIC_SUPABASE_URL` = your Supabase project URL
     - `SUPABASE_SERVICE_ROLE_KEY` = your Supabase service_role key
5. Click **Deploy**. Wait for the build to finish.
6. Copy your frontend URL, e.g. `https://gloomberg-xxxx.vercel.app`.

---

## 4. Connect backend to frontend (CORS)

1. In **Render** → your backend service → **Environment**.
2. Set `FRONTEND_URL` = your **exact** Vercel URL (e.g. `https://gloomberg-xxxx.vercel.app`).
3. **Save Changes**. Render will redeploy automatically.

---

## 5. You’re live

- Share the **Vercel URL** with anyone. They can use the dashboard, assets, chat, research, waitlist, etc.
- Backend (Render) and waitlist (Supabase) are already wired; no extra steps unless you add a custom domain.

**Custom domain (optional):** In Vercel → Project → Settings → Domains, add your domain. Then set `FRONTEND_URL` on Render to that domain and redeploy the backend.

- **Redis** (faster loads): See [docs/REDIS_SETUP.md](docs/REDIS_SETUP.md) for Upstash/Redis Cloud setup.
- For more detail (Stripe, etc.), see **DEPLOY.md**.
