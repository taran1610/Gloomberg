# Redis Setup for Gloomberg

Redis caches market data (dashboard, indices, asset info, history) so repeat requests load **much faster**. It also survives Render cold starts—when your backend spins back up, cached data can still be served.

---

## Option 1: Upstash (Recommended — Free Tier)

Upstash is serverless Redis with a generous free tier. Works well with Render.

### Steps

1. **Sign up** at [upstash.com](https://upstash.com) (free account).

2. **Create a Redis database**
   - Dashboard → **Create Database**
   - Name: `gloomberg`
   - Type: **Regional** (or Global if you prefer)
   - Region: choose one close to your Render region (e.g. `us-east-1`)
   - Click **Create**

3. **Get the connection URL**
   - Open your database → **REST API** or **Connect** tab
   - Copy the **Redis URL** (starts with `rediss://` for TLS)
   - Example: `rediss://default:AXyz123...@us1-xxx.upstash.io:6379`

4. **Add to Render**
   - Render → your **Gloomberg-backend** service → **Environment**
   - Add variable:
     - **Key:** `REDIS_URL`
     - **Value:** paste the Upstash Redis URL
   - **Save Changes** (Render will redeploy)

5. **Verify**
   - After deploy, open `https://YOUR-BACKEND-URL/api/health`
   - Response should include `"redis": true`

---

## Option 2: Redis Cloud (Free Tier)

Redis Cloud offers a free 30MB database.

### Steps

1. **Sign up** at [redis.com/try-free](https://redis.com/try-free/).

2. **Create a subscription**
   - Create a free subscription
   - Create a database (e.g. `gloomberg`)
   - Choose a cloud provider/region close to Render

3. **Get the connection string**
   - Database → **Connect** → copy the connection string
   - Format: `redis://default:PASSWORD@HOST:PORT` or `rediss://` for TLS

4. **Add to Render**
   - Same as Upstash: add `REDIS_URL` with the connection string
   - Save and redeploy

---

## Local Development

For local development, either:

**A) Use Docker:**
```bash
docker run -d -p 6379:6379 redis:7-alpine
```
Then your `.env` already has `REDIS_URL=redis://localhost:6379`.

**B) Install Redis locally (macOS):**
```bash
brew install redis
redis-server
```

---

## Cache TTLs (Already Configured)

| Data           | TTL   |
|----------------|-------|
| Dashboard      | 5 min |
| Ticker/Asset   | 15 min|
| History        | 1 hr  |
| News           | 30 min|

These are set in `backend/config.py`. No changes needed.

---

## Troubleshooting

**`"redis": false` in /api/health**
- Check `REDIS_URL` is set correctly in Render
- Upstash/Redis Cloud URLs often use `rediss://` (TLS)—ensure the full URL is copied
- Verify the database is running and not paused

**Connection timeout**
- Ensure the Redis region is close to your Render region
- Check firewall/allowlist if your Redis provider has one
