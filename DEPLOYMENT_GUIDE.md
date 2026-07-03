# 🚀 Deployment Guide

**MediCareGP** runs on Railway, deployed from the `main` branch. This guide covers setup, configuration, and troubleshooting.

---

## Quick Start (5 minutes)

### Prerequisites
- GitHub repo: `DevJoymanu/MediCareGP`
- Railway account at [railway.app](https://railway.app)
- Domain name (optional; Railway assigns a default `*.railway.app` subdomain)

### 1. Create Railway Project

1. Go to [railway.app/dashboard](https://railway.app/dashboard)
2. Click **"New Project"** → **"Deploy from GitHub repo"**
3. Authenticate with GitHub
4. Select **`DevJoymanu/MediCareGP`**
5. Railway auto-detects the Python/Django app

### 2. Set Environment Variables

In Railway project **Variables** (Settings → Variables), add:

```
DATABASE_URL=postgresql://user:pass@host/dbname
SECRET_KEY=your-django-secret-key-here
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,yourapp.railway.app

# Optional: Cloudflare R2 (file storage)
R2_ACCOUNT_ID=your-account-id
R2_ACCESS_KEY_ID=your-key-id
R2_SECRET_ACCESS_KEY=your-secret
R2_BUCKET_NAME=medicaregp
R2_ENDPOINT_URL=https://your-account.r2.cloudflarestorage.com

# Optional: TURN servers for video calls
CLOUDFLARE_TURN_KEY_ID=your-key-id
CLOUDFLARE_TURN_API_TOKEN=your-token
METERED_DOMAIN=your-domain.metered.ca
METERED_API_KEY=your-api-key
TURN_URLS=turn:turnserver1.com,turn:turnserver2.com
TURN_STATIC_AUTH_SECRET=shared-secret

# Medical-aid gateway (optional)
# Store env var names here; actual credentials go in Railway secrets
LAB_PORTAL_PASSWORD=lab-results
RADIOLOGY_PORTAL_PASSWORD=radiology-results
```

### 3. Deploy

Push to `main`:
```bash
git push origin main
```

Railway auto-deploys. Check **Deployments** tab for progress.

### 4. Run Migrations

After first deploy, run migrations in Railway shell:

```bash
railway run python manage.py migrate
```

### 5. Create Superuser

```bash
railway run python manage.py createsuperuser
```

Or use the demo setup command:
```bash
railway run python manage.py setup_demo
```

---

## Environment Variables Reference

| Variable | Required | Purpose | Example |
|----------|----------|---------|---------|
| `DATABASE_URL` | ✅ | PostgreSQL connection | `postgresql://user:pass@host/dbname` |
| `SECRET_KEY` | ✅ | Django secret (generate with `openssl rand -base64 32`) | `abc123...` |
| `DEBUG` | ✅ | Set to `False` in production | `False` |
| `ALLOWED_HOSTS` | ✅ | Comma-separated domains | `yourdomain.com,app.railway.app` |
| `R2_*` | ❌ | Cloudflare R2 file storage (falls back to local disk) | See above |
| `CLOUDFLARE_TURN_KEY_ID` | ❌ | Cloudflare Realtime TURN (recommended for video) | `abc123...` |
| `CLOUDFLARE_TURN_API_TOKEN` | ❌ | Cloudflare token | `abc123...` |
| `METERED_DOMAIN` | ❌ | Fallback TURN provider | `mydomain.metered.ca` |
| `METERED_API_KEY` | ❌ | Metered.ca API key | `abc123...` |
| `TURN_URLS` | ❌ | Static TURN URLs (fallback) | `turn:server1.com,turn:server2.com` |
| `TURN_STATIC_AUTH_SECRET` | ❌ | Static auth secret | `shared-secret-string` |
| `LAB_PORTAL_PASSWORD` | ❌ | Lab results portal password | `lab-results` |
| `RADIOLOGY_PORTAL_PASSWORD` | ❌ | Radiology results portal password | `radiology-results` |

---

## Local Development Setup

### 1. Clone & Install

```bash
git clone https://github.com/DevJoymanu/MediCareGP.git
cd MediCareGP/medicaregp
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Local Database

SQLite by default. For PostgreSQL locally, update `.env`:

```bash
DATABASE_URL=postgresql://user:pass@localhost/medicaregp
```

### 3. Setup Demo Data

```bash
python manage.py migrate
python manage.py setup_demo
```

### 4. Run Dev Server

```bash
python manage.py runserver
# Visit http://localhost:8000/app/
# Doctor: doctor / doctor123
# Receptionist: receptionist / reception123
```

### 5. Build React Website (if needed)

```bash
cd ../Medical-Flow/Medical-Flow/artifacts/gp-website
$env:NODE_ENV="production"
$env:PORT="5000"
$env:BASE_PATH="/static/website/"
npx vite build --config vite.config.ts
# Copy dist/public/* to medicaregp/static/website/
```

---

## Railway Configuration Details

### Procfile

Not needed; Railway auto-detects Django and runs:
```
gunicorn medicaregp.wsgi --bind 0.0.0.0:$PORT --workers 1 --threads 8 --timeout 120
```

(See `railway.json` for exact config.)

### Database Migrations

Railway **does NOT auto-run migrations**. After deploy, manually run:

```bash
railway run python manage.py migrate
```

Or add a pre-deploy hook in `railway.json`:
```json
{
  "builder": "nixpacks",
  "buildCommand": "python manage.py migrate"
}
```

### Static Files

Collected during build via `python manage.py collectstatic`. Served by WhiteNoise (no separate storage needed).

The compiled React website is **committed** to the repo, so Railway's Python-only deploy needs no Node.js step.

---

## Troubleshooting

### "502 Bad Gateway"

**Likely cause:** Gunicorn crash.
- Check Railway logs: **Logs** tab
- Run `railway logs --follow` locally
- Ensure all env vars are set (esp. `SECRET_KEY`, `DATABASE_URL`)

### "Static files not loading" (CSS/JS broken)

**Likely cause:** WhiteNoise not serving assets.
- Confirm `STATIC_ROOT` and `STATIC_URL` in `settings.py`
- Ensure assets were collected: `railway run python manage.py collectstatic --noinput`
- Check that compiled website exists at `medicaregp/static/website/index.html`

### "Video calls not working" (stuck on "Connecting…")

**Likely cause:** TURN server misconfigured or down.
- Visit `/video/turn-test/` (staff only) to diagnose
- Check TURN provider status:
  - Cloudflare Realtime: verify `CLOUDFLARE_TURN_KEY_ID` and `CLOUDFLARE_TURN_API_TOKEN`
  - Metered.ca: verify `METERED_DOMAIN` and `METERED_API_KEY`
- If all TURN providers down, video falls back to STUN-only (works on same network, fails over firewalls)

### "Database connection timeout"

**Likely cause:** PostgreSQL isn't running or URL is wrong.
- Check `DATABASE_URL` in Railway **Variables**
- Ensure PostgreSQL database exists
- Test connection: `railway run python manage.py dbshell`

### "ModuleNotFoundError: No module named 'diagnosis'"

**Likely cause:** New app not in `INSTALLED_APPS`.
- Check `medicaregp/settings.py` includes `'diagnosis'` and other new apps
- Rerun migrations: `railway run python manage.py migrate`

---

## Backup & Recovery

### Backup Database

```bash
railway run python manage.py dumpdata > backup.json
# Or use PostgreSQL tools:
pg_dump $DATABASE_URL > backup.sql
```

### Restore Database

```bash
railway run python manage.py loaddata backup.json
# Or:
psql $DATABASE_URL < backup.sql
```

### Backup Files (R2)

Cloudflare R2 is S3-compatible. Use AWS CLI or boto3:
```bash
aws s3 sync s3://your-bucket-name /local/backup --endpoint-url https://your-account.r2.cloudflarestorage.com
```

---

## Monitoring & Logging

### Railway Logs

In Railway dashboard:
- **Logs** tab shows deployment and runtime logs
- Filter by date/severity
- Click **Follow** for real-time tail

### Application Errors

Django logs to stdout (captured by Railway). Check:
- `django.log` if you configure file logging (optional)
- Railway **Metrics** tab for CPU/memory usage

### Health Endpoint

Create a simple health check:
```python
# medicaregp/urls.py
path('health/', lambda r: HttpResponse('OK'), name='health')
```

Then configure Railway health checks to ping `/health/`.

---

## Scaling

### Horizontal Scaling

Railway supports multiple replicas (if on paid plan):
- Increase **RAM** and **CPU** in Railway dashboard
- Set `--workers` and `--threads` in `gunicorn` command (see `railway.json`)

### Database Scaling

Switch from Railway PostgreSQL (shared) to a dedicated instance for production. See Railway docs.

---

## Security Checklist

Before going live:

- [ ] `DEBUG=False` in production
- [ ] `SECRET_KEY` is long, random, and not committed to git
- [ ] `ALLOWED_HOSTS` includes only your domain
- [ ] Database password is strong
- [ ] HTTPS enabled (Railway auto-enables via CloudFlare or Let's Encrypt)
- [ ] Superuser password is strong
- [ ] Run `python manage.py check --deploy`
- [ ] File uploads are scanned for malware (optional, third-party service)
- [ ] Backup strategy in place
- [ ] SSL/TLS certificate auto-renews

---

## Rollback

If a deploy breaks production:

1. **Revert code:**
   ```bash
   git revert HEAD
   git push origin main
   ```
   Railway auto-redeploys the previous commit.

2. **Restore database (if data corruption):**
   ```bash
   # From backup
   railway run python manage.py loaddata backup.json
   ```

3. **Check deployment history:** Railway **Deployments** tab shows all versions.

---

## Support

- Django docs: [docs.djangoproject.com](https://docs.djangoproject.com)
- Railway docs: [docs.railway.app](https://docs.railway.app)
- Medical-Flow docs: See `Medical-Flow/` folder (legacy, for reference)
- Bug tracker: [GitHub Issues](https://github.com/DevJoymanu/MediCareGP/issues)

---

**Last updated:** 2026-07-03  
**Deployment target:** Railway (gunicorn WSGI)  
**Django version:** 4.2  
**Python version:** 3.9+
