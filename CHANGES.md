# Changes

## Migration from MySQL to PostgreSQL

* **Driver / URL**: `psycopg2-binary`; `DATABASE_URL=postgresql+psycopg2://user:password@host:5432/car_rental`
  (`postgres://` and `postgresql://` URLs are normalised). `pool_pre_ping` enabled.
* **Init scripts** (`database/`): `init_db.py` (creates the DB, tables, indexes, trigger, reference data; idempotent;
  `--create-db`, `--sample-data`, `--reset --yes`), `schema.sql` (generated from the models by `generate_schema.py`, so
  it cannot drift - a test enforces that), `seed.sql`, `sample_data.sql`.
* **Table names are now snake_case** (`customer`, `membership_tier`, `rental_insurance`, ...) instead of `Customer`,
  `MembershipTier`, ... so no double-quoting is needed in `psql`. Existing MySQL data must be copied with that mapping.
* **Real DB defaults**: Python-side defaults are mirrored as SQL `DEFAULT`s, so plain `INSERT`s behave like the API.
* **`updated_at`**: MySQL's `ON UPDATE CURRENT_TIMESTAMP` replaced by a trigger on `customer`.
* **Foreign keys**: nine FKs said `onupdate="SET NULL"` (a typo for `ondelete`); they are now `ON DELETE SET NULL`, so
  deleting an employee/location in SQL no longer fails or orphans rows.
* **Case-insensitivity**: MySQL compared text case-insensitively, Postgres does not. Email, driver licence, licence
  plate and employee email lookups are case-insensitive again, backed by unique indexes on `lower(...)`.
* **Deterministic ordering**: every list query now has an `ORDER BY` (Postgres returns physical order, and an UPDATE
  moves a row - lists used to reshuffle after an edit and `skip/limit` paging could skip/repeat rows).
* **Indexes** on the foreign keys / filters the API uses (Postgres does not index FKs automatically).
* **Errors**: constraint violations are recognised by SQLSTATE (23505 / 23503 / 23502).

Verified with 137 backend tests (real PostgreSQL) and a 60-step headless-browser run that drives the real UI
against the real API (`e2e/ui_e2e.py`). No visual/design changes were made to the frontend.

## Root causes of "works in the backend, doesn't work from the frontend"

| # | Problem | Fix |
|---|---------|-----|
| 1 | Forms request `?limit=1000`, backend capped `limit` at 100 -> HTTP 422, so every customer/vehicle/location/employee dropdown was empty (no reservation, rental, incident or maintenance could be created in the UI) | Cap raised to 1000 (default still 100) |
| 2 | Frontend sends JSON bodies for vehicle availability, rental return and loyalty points; backend only read query params (422, or fields silently dropped) | All three accept a JSON body **and** the old query params |
| 3 | Customer form sends `date_of_birth: ""` -> 422 | Blank strings for *optional* fields are treated as null project-wide (`schemas.BaseModel`) |
| 4 | Decimals were serialized as strings (`"45.50"`) -> `NaN` in the rental balance maths | Money fields are JSON numbers (`schemas.Money`) |
| 5 | 500 errors carried no CORS headers (browser showed an opaque network error); only `localhost:5173` was allowed | Catch-all middleware inside CORS; JSON `{"detail": ...}` everywhere; any `localhost`/`127.0.0.1` port allowed |

## Backend (`backend/`)

* **Errors**: FK / unique violations, business-rule violations and validation errors return 400/404/422 with a readable
  `detail` instead of 500.
* **Customers**: new customers get a Standard membership profile; update checks duplicate email/licence (400);
  delete cascades to profile, preferences, reservations, rentals, payments, incidents and releases the vehicle of an
  active rental; search also matches driver licence; `/customers/search` works without trailing slash.
* **Vehicles**: location/plate validation; delete (refused while on an active rental); attach/detach features;
  maintenance-record upsert; NULL maintenance cost no longer crashes the detail page.
* **Reservations**: end must be after start; conflicts are checked against other reservations **and** active rentals
  (back-to-back is allowed); updates are re-checked; converting works for Active/Confirmed reservations.
* **Rentals**: creation is atomic, validates references and refuses unavailable vehicles / vehicles reserved by someone
  else; a failed create no longer leaves the vehicle unavailable; date filter and revenue report include the whole end
  day; revenue includes late/damage fees; `PUT /rentals/{id}`; attach insurance.
* **Return flow** (one transaction): cannot be returned twice; ending mileage can't be below starting mileage; late fee
  calculated if none supplied; vehicle freed and odometer updated; customer's lifetime spending/rentals/points updated.
* **New routes for schemas that already existed**: update/delete for employees and locations (location delete refused
  while in use), updates for payments, incidents, maintenance, insurance plans and membership, `GET /maintenance/`.
* `requirements.txt`, `requirements-dev.txt`, `.env.example` added (README referenced a missing requirements file).

### Business rules I had to choose (change in `backend/crud.py`, top of file)
* `LATE_FEE_RATE = 0.50` - late fee per started late day = 50 % of the daily rate (the rule the UI already used).
* `POINTS_PER_CURRENCY_UNIT = 1` - points = amount charged x tier `bonus_point_rate`.
* Lifetime spending and revenue include late and damage fees.

## Frontend (`frontend/vehicle-rental/`)

* `npm run build` failed on 3 unused variables (`CustomerForm`, `RentalDetail`, `VehicleDetail`) - removed.
* `RentalDetail.handleReturnVehicle` called `setReturnData()` and then sent the *stale* state, so the late fee never
  reached the server; it now builds the payload from current values and drops blank (`NaN`) inputs.
* Maintenance "All" tab called the same endpoint as "Scheduled"; it now uses the new `maintenanceApi.getAll()`.

## Tests
* `backend/tests/` - pytest suite (`conftest.py` documents the DB setup).
* `e2e/ui_e2e.py` - Playwright end-to-end test. See README.

## Known / left alone
* ESLint reports ~16 mostly `no-explicit-any` style errors; not functional, not touched.
* Rental/Customer list pages show IDs ("Customer #1") by design - unchanged.
