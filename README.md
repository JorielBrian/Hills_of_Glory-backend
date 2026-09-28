# Hills of Glory MIS — API (FastAPI)

Python/FastAPI replacement for the original NestJS API. Built to serve the
existing Next.js frontend (`apps/web` in the original monorepo) and add real
data behind its currently-static pages.

## Stack

- FastAPI + Pydantic v2
- SQLAlchemy 2.0 (typed models) + Alembic (migrations)
- PostgreSQL
- JWT auth (python-jose) + bcrypt password hashing (passlib)

## Domain model

One `people` table holds everyone the system tracks — staff who log in,
approved adult members, kids, and visitors — because kids and walk-in
visitors still need a QR badge for attendance even though they never get
login credentials. Login fields (`username`, `email`, `password_hash`) are
nullable for that reason.

- **Global `role`**: `admin`, `head_pastor`, `network_leader`, `life_guide`,
  `member`, `visitor`. Controls dashboard-wide permissions.
- **Ministry Director / Lifegroup Leader are NOT roles.** They're per-entity
  assignments (see `ministry_memberships` / `lifegroup_memberships`), so any
  approved person can direct one ministry and be a plain member of another.
- **`member_type`**: `adult` / `kid`. Kids link to a guardian via
  `guardian_id` and never get login credentials, but do get a `qr_code` for
  children's ministry check-in.
- **Attendance**: every person has one permanent `qr_code` (their badge).
  Scanning posts `{qr_code, event_instance_id}` to `/api/attendance/scan`.
  A DB unique constraint on `(event_instance_id, person_id)` blocks
  duplicate scans — the API returns `409` with a friendly message.
- **Events**: `event_templates` hold the recurrence rule (weekly / monthly
  nth-weekday / one-off); `event_instances` are the concrete calendar
  entries. A template can `suppresses_template_id` another template — e.g.
  Prayer & Fasting suppresses Prayer Encounter. When you create a Prayer &
  Fasting instance, any Prayer Encounter instance in the same calendar week
  is automatically flipped to `cancelled` with `suppressed_by_instance_id`
  pointing at the instance that replaced it. Any instance can also be
  independently rescheduled (date/time/location) via `PATCH
  /api/events/instances/{id}` without touching the template.

## Local setup

```bash
# 1. Start Postgres (matches docker-compose.yml credentials)
docker compose up -d

# 2. Create venv + install deps
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# edit .env if your DB isn't on localhost:5432

# 4. Run migrations
alembic upgrade head

# 5. Run the dev server
uvicorn app.main:app --reload --port 4000
```

API docs: `http://localhost:4000/docs`

## Creating the first admin

There's no seed script yet — registration always creates a `pending`
`visitor`. To bootstrap your first admin, either:

- Register normally through `/api/auth/register`, then flip that row's
  `role` to `admin` and `status` to `approved` directly in Postgres, or
- Run a one-off Python script using `app.core.security.hash_password` and
  insert a `Person` row.

After that, the admin can approve/reject/role-manage everyone else through
`/api/users`.

## Project layout

```
app/
  core/       settings, JWT + password hashing
  db/         SQLAlchemy engine/session
  models/     SQLAlchemy ORM models (one file per domain concept)
  schemas/    Pydantic request/response models
  api/
    deps.py     auth dependencies (get_current_person, require_roles, ...)
    routes/     one router per domain concept
  main.py     FastAPI app + router wiring + CORS
alembic/      migrations
```

## What's implemented vs. still open

Implemented and smoke-tested: registration + approval workflow, login,
role/status management, ministries + per-ministry membership, lifegroups +
networks + per-group membership, event templates/instances with the
suppression rule, QR attendance scanning with duplicate protection, public +
members-only announcements, and basic dashboard/report aggregates.

Not yet built (next steps): image upload handling for announcements (current
`image_url` field expects a URL — wire up S3/Cloudinary/local storage),
recurring-instance auto-generation (right now staff create each instance;
a scheduled job to generate the next N weeks from templates would help),
and the public-site content models for sermons/services/leadership (those
pages are still hardcoded in the frontend).
# Hills_of_Glory-backend
