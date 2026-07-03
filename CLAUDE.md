- At the end of every edit, provide a suitable `git commit -m` message.

## Current State

GP practice system for **Dr. Tamuka Chivonivoni** (Django 4.2, Python 3.9, Postgres in prod / SQLite local, deployed on Railway via gunicorn WSGI). A single Django service serves both the public patient website and the back-office CRM. The Django project lives in `medicaregp/`; run `manage.py` from there. GitHub repo `DevJoymanu/MediCareGP`.

### Major features (how they work now)
- **Two front doors, one service:** the public React website is served at `/`; the staff CRM dashboard is at `/app/` (login required, `LOGIN_REDIRECT_URL=/app/`). Public, no-login surfaces: website, `/api/`, patient video join, results portal, patient check-in.
- **Public website (Medical-Flow):** a React/Vite SPA in `Medical-Flow/Medical-Flow/artifacts/gp-website`, built to `medicaregp/static/website/` and served by `medicaregp/views.py:website_home` (reads the compiled `index.html`); hashed assets served by WhiteNoise. Built assets are **committed** so the Railway Python deploy needs no Node step.
- **Online booking:** website form → `POST /api/bookings` creates an `appointments.WebBooking` (status `requested`); `GET /api/availability?date=` returns bookable slots. No payment is taken — a booking is just a request.
- **Reception queue:** web bookings land in **Web Bookings** (`/appointments/web-bookings/`), where staff match/create a `Patient` and convert the booking into a real `Appointment` (statuses `requested`→`converted`/`cancelled`).
- **Double-booking prevention:** the site books discrete time slots (`settings.BOOKING_SLOT_MINUTES`/`BOOKING_HOURS`); `appointments/booking_slots.py` computes availability by merging active `Appointment`s **and** live `WebBooking`s, so website and CRM never clash. `/api/bookings` returns **409 `{slotTaken}`** on a race; the form greys out taken slots.
- **Built-in video consultation (WebRTC, no third party):** the "Online Consultation (Video call)" type gets a `VideoRoom`. Doctor joins at `/video/appointment/<pk>/` (login), patient at `/video/join/<token>/` (public). Signaling is **HTTP polling** over `VideoSignal` (`/video/<room>/signal/`) — no WebSockets. Media is peer-to-peer/encrypted; client (`templates/video/room.html`) uses perfect negotiation + ICE restart. Reception copies/sends the patient link from the appointment detail.
- **TURN/ICE:** `appointments/turn.py` `build_ice_servers()` served fresh per call at `/video/<room>/ice/`. Precedence: **Cloudflare Realtime TURN** (`CLOUDFLARE_TURN_KEY_ID`/`CLOUDFLARE_TURN_API_TOKEN`, 1 TB/mo free, **currently live & recommended**) → metered.ca API (`METERED_DOMAIN`/`METERED_API_KEY`, only 500 MB/mo free, fallback) → coturn HMAC (`TURN_URLS`+`TURN_STATIC_AUTH_SECRET`) → static creds → STUN-only. The Cloudflare fetch **must send a non-default `User-Agent`** or its edge returns 403 `error code: 1010`. Staff diagnostic at `/video/turn-test/` shows the active provider + exact fetch error.
- **Patients:** rich demographics, contact, responsible party, medical aid, allergies/chronic/meds (`patients/`); allergy banners surface on appointments.
- **Consultations:** SOAP notes, vitals, ICD-10, referrals, follow-ups (`consultations/Consultation`). **Investigation requests** feed two provider results portals; submissions land in a "Pending Results" review queue. Referral providers managed in-app.
- **Results portals (two flavours):** (1) standing, shared-password **practice portals** at `/lab/` and `/radiology/` (`portal_views.provider_portal`, password = `LAB_PORTAL_PASSWORD`/`RADIOLOGY_PORTAL_PASSWORD` env vars, default `lab-results`/`radiology-results`) — provider logs in, sees all non-confirmed requests of that kind, picks the patient and submits. This is the current model, so **no per-patient link/QR is printed on the referral form** the patient carries. (2) Legacy per-request **token portal** at `/results/<uuid token>/` still works for links already issued; staff "Copy results link" button copies one. The lab email points at `/lab/`; the radiology email (sent to the patient) just says present the form.
- **Appointments & waiting room:** scheduling, walk-ins, status flow, live waiting room (5s JSON polling), and token-based **patient self check-in** (QR flow in `appointments/checkin_*`).
- **Billing, tasks, documents, dashboard, analytics:** invoices (`billing`), reminders (`tasks`), uploaded docs (`scripts`), plus dashboard + analytics views in `medicaregp/views.py`.
- **Media storage:** Cloudflare R2 (S3-compatible) when `R2_*` env vars are set (Railway FS is ephemeral); else local disk. Patient files served via short-lived signed URLs.

### Key architecture decisions (why)
- **Consolidated on Django, single service** instead of running Medical-Flow's Express/Drizzle/Postgres layer — cheaper on Railway, one DB/deploy, bookings land natively. That Node layer is **retired but vendored** into this repo under `Medical-Flow/` (de-nested from its old embedded git repo) for reference/rebuilds; it is NOT deployed.
- **No payment gateway** — PayFast was built then fully removed; the practice settles payment directly. Simplest, least code.
- **Built-in WebRTC over HTTP-polling signaling** (no Channels/Redis/ASGI) so video runs on the existing WSGI stack with no new infra.
- **Reception-mediated booking→appointment** rather than auto-create, because the website can't collect ID number / DOB and slots are exact times needing confirmation.
- **Token-based public access** (unguessable UUIDs) is the standard pattern for patient-facing flows: check-in, results portal, video join.

### Partial / fragile
- **TURN is configured** (Cloudflare Realtime, live on Railway) so video works on mobile/firewalled networks. If `/video/turn-test/` ever shows STUN-only, a provider's creds/env broke — the diagnostics panel names the failing provider and shows its HTTP error body. STUN-only = calls hang on "Connecting…".
- **Video reconnection** (perfect negotiation) is implemented but only lightly tested; polling adds ~1s signaling latency; `VideoSignal` cleanup is opportunistic (on POST, >6h).
- **Appointment-type label coupling:** the exact string `"Online Consultation (Video call)"` must stay in sync across React (`BookingForm.tsx` APPOINTMENT_TYPES/TYPE_HINTS, `Services.tsx`, `OnlineConsultation.tsx` ONLINE_TYPE) and `settings.ONLINE_CONSULT_TYPE`. Online detection falls back to `'online' in reason`; legacy bookings used the old `"(Doxy.me)"` label.
- `railway.json` hardcodes `--bind 0.0.0.0:8000` (not `$PORT`); gunicorn runs `--workers 1 --threads 8 --timeout 120`.
- Repo root holds many one-off NAPPI-parsing / `debug*.py` scripts, plus legacy top-level `appointments/`,`consultations/`,`patients/` dirs duplicated under `medicaregp/` (the deployed copies are under `medicaregp/`) — noise, not part of the running app.
- The website brand ("Rand Medical Resources / Kwa-Thema", WhatsApp `27847564715`) differs from `settings.PRACTICE_NAME`; reconcile if needed.

### Conventions for the next session
- **Railway auto-deploys from `main` only.** Work happens on feature branches (e.g. `feature/investigation-results-portal`); nothing deploys until the branch is merged into `main` and pushed. If "nothing is deploying," check that `main` actually moved.
- **Rebuild the website with PowerShell, not Git-bash** (bash mangles `/static/...` via MSYS pathconv): `cd Medical-Flow/Medical-Flow/artifacts/gp-website; $env:NODE_ENV="production"; $env:PORT="5000"; $env:BASE_PATH="/static/website/"; npx vite build --config vite.config.ts`, then copy `dist/public/*` → `medicaregp/static/website/` and commit. Needs `pnpm` (`npm i -g pnpm@9`; `pnpm install` in `Medical-Flow/Medical-Flow` once).
- Run `python manage.py {check,makemigrations,migrate,collectstatic}` from `medicaregp/`. Typecheck the site with `npx tsc -p tsconfig.json --noEmit` before building.
- Public JSON endpoints are `@csrf_exempt` + honeypot; keep that pattern. Reuse the UUID-token pattern for new patient-facing surfaces.
- Templates use inline styles + `crm-*` classes; reusable partials are `_name.html` and `{% include %}`d.
- Keep React appointment-type labels and `settings.ONLINE_CONSULT_TYPE` in sync.
- Provide a `git commit -m` message after edits.
