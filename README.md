# Car Rental Management System

A full stack web app for managing a car rental business - customers, vehicles, rentals, reservations, maintenance, the whole thing. Built this to get more comfortable with FastAPI and React/TypeScript together, ended up being a much bigger project than I originally planned lol.

## What it does

Basically handles everything a rental company would need day to day:

- Customer management (with membership tiers and points)
- Vehicle fleet tracking, availability, maintenance history
- Reservations that check for date conflicts before booking
- Active rentals with return processing (late fees, damage fees, mileage tracking)
- Payment records
- Incident reports for accidents/damage
- Maintenance scheduling for the fleet
- A dashboard with basic revenue/stats

It's not connected to any payment gateway or anything, this was more about getting the data modeling and CRUD flows right across a decently complex schema.

## Tech stack

Backend
- FastAPI
- SQLAlchemy
- PostgreSQL
- Pydantic for validation

Frontend
- React + TypeScript (Vite)
- React Router
- Plain CSS, no UI library

## Project structure

```
backend/
  models.py       sqlalchemy models
  schemas.py      pydantic schemas  
  crud.py         db operations
  database.py     engine/session setup
  main.py         all the api routes
  tests/          pytest suite
  db/
    schema.sql         PostgreSQL tables/indexes/triggers (generated from models.py)
    seed.sql           reference data (membership tiers, insurance plans, vehicle features)
    sample_data.sql    demo data
    init_db.py         one-command database setup
    demo_reset.py      wipe + reload helper (used by init_db.py and POST /admin/reset-demo)
    generate_schema.py regenerates schema.sql after you change models.py
  start.sh             production start script (Render)

frontend/vehicle-rental/
  src/
    types/        typescript interfaces
    services/      api calls
    components/
    pages/

e2e/               browser end-to-end test
```

Database has around 15 tables - customers, vehicles, rentals, reservations, payments, employees, locations, maintenance records, insurance plans, incident reports etc, all wired together with foreign keys.

## Running it locally

You'll need PostgreSQL (12+) running somewhere and Python + Node installed.

### Database

Create the connection string first - `backend/.env`:

```
DATABASE_URL=postgresql+psycopg2://user:password@localhost:5432/car_rental
```

Then let the init script do everything (creates the database if it is missing, all tables, indexes, triggers and
the reference data such as the `Standard` membership tier the app needs):

```
pip install -r backend/requirements.txt
python backend/db/init_db.py --create-db
```

Useful options (the script is safe to re-run, it never deletes anything unless you pass `--reset --yes`):

```
python backend/db/init_db.py --sample-data     # also load a few demo locations / vehicles / customers
python backend/db/init_db.py --reset --yes     # DROP everything and rebuild from scratch (destructive!)
```

Prefer plain SQL? Run `backend/db/schema.sql` then `backend/db/seed.sql` with psql instead:

```
createdb car_rental
psql -d car_rental -f backend/db/schema.sql -f backend/db/seed.sql
```

After changing `backend/models.py` regenerate the SQL with `python backend/db/generate_schema.py`
(`--check` verifies it is up to date).

### Backend

```
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

Should be running on localhost:8000, you can check the auto generated docs at localhost:8000/docs

### Frontend

```
cd frontend/vehicle-rental
npm install
npm run dev
```

Runs on localhost:5173 by default.

Note - if you hit CORS errors, you'll need to add the CORS middleware to main.py pointing at your frontend url.

## A few things I learned / would do differently

Honestly the hardest part wasn't the CRUD stuff, it was figuring out the return flow for rentals - when a car comes back you have to calculate late fees if its overdue, log any damage, update mileage on the vehicle, mark it available again, and update the customer's membership points, all more or less at once. Getting that logic in one place instead of scattered around took a couple tries.

If I kept working on this I'd probably add:
- actual auth (right now anyone can hit any endpoint, not great)
- tests, there are none right now which is bad
- some kind of notification system for overdue rentals / upcoming maintenance
- better handling of concurrent bookings on the same vehicle

## Sample data

There's a small sql snippet in the setup docs to seed a couple customers/vehicles/locations if you want to poke around without creating everything by hand.

---

Built as a learning project, not meant for production use as is.


## Tests

Backend (real PostgreSQL; the schema is built from `backend/db/schema.sql`; **the `public` schema of the test
database is dropped**, so use a throw-away one):

```
createdb car_rental_test
cd backend
pip install -r requirements-dev.txt
export TEST_DATABASE_URL=postgresql+psycopg2://user:password@127.0.0.1:5432/car_rental_test   # Windows: set
pytest
```

End-to-end browser test (drives the real UI against the real API; **wipes the tables of the `car_rental` database**,
override with `E2E_DB_NAME`, `E2E_DB_HOST`, `E2E_DB_PORT`, `E2E_DB_USER`, `E2E_DB_PASSWORD`). Initialise the database,
then start backend (`:8000`) and frontend (`:5173`) first:

```
pip install psycopg2-binary playwright
python -m playwright install chromium
python e2e/ui_e2e.py
```

See `CHANGES.md` for everything that was fixed and why.

## Deploying (Render + Vercel + Neon)

**1. Neon** - create a project and copy the *direct* (non-pooled) connection string, e.g.
`postgresql://user:pass@ep-xxx.neon.tech/neondb?sslmode=require`.

**2. Render** (Web Service)

| Setting | Value |
|---|---|
| Root Directory | `backend` |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `bash start.sh` |

Environment variables:

| Variable | Value |
|---|---|
| `DATABASE_URL` | the Neon connection string |
| `PYTHON_VERSION` | `3.12.3` |
| `ALLOWED_ORIGINS` | your Vercel URL, e.g. `https://my-app.vercel.app` (comma separate several) |
| `ALLOW_VERCEL_PREVIEWS` | `1` to also allow every `*.vercel.app` origin (optional) |
| `RESET_DB_ON_START` | `1` = wipe the database and reload the demo data on every start (demo mode). Unset = just create missing tables and keep data |
| `DEMO_RESET_ENABLED` | `0` disables the `POST /admin/reset-demo` endpoint / "Reset demo data" button (default: enabled) |

`start.sh` runs `db/init_db.py` (schema + reference data, plus a full reset if `RESET_DB_ON_START=1`) and then starts uvicorn.
Note that on Render's free tier the service sleeps after ~15 minutes idle, so a "reset on start" only happens after a
wake-up; the **Reset demo data** button in the header restores the demo on demand. **Never set `RESET_DB_ON_START=1`
or leave the reset endpoint enabled on a database that holds real data.**

**3. Vercel** - Root Directory `frontend/vehicle-rental`, framework preset Vite, and the environment variable
`VITE_API_URL=https://your-api.onrender.com` (no trailing slash). `vercel.json` rewrites every path to `index.html`
so refreshing a page such as `/customers` works. Redeploy after changing `VITE_API_URL` (Vite bakes it in at build time).

The first request after the backend has been idle takes 30-60 s (Render cold start, plus Neon waking up).
