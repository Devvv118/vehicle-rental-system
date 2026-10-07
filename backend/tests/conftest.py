"""
Backend test harness.

Runs the real FastAPI app against a real PostgreSQL database (NOT sqlite), so Postgres behaviour
(FK enforcement, NUMERIC, case-sensitive text, triggers, ...) is exercised. The schema is created by
executing database/schema.sql, so every test also validates the init script.

Set TEST_DATABASE_URL to point at a throwaway database, e.g.
    postgresql+psycopg2://rental:rental@127.0.0.1:5432/car_rental_test
WARNING: the whole `public` schema of that database is dropped at the start and every table is wiped between tests.
"""
import os
import sys
from datetime import datetime, timedelta

import pytest

TEST_DB = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+psycopg2://rental:rental@127.0.0.1:5432/car_rental_test",
)
os.environ["DATABASE_URL"] = TEST_DB  # must be set before `database` is imported
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import text  # noqa: E402

import models  # noqa: E402
from database import engine  # noqa: E402
from main import app  # noqa: E402


SCHEMA_SQL = os.path.join(os.path.dirname(__file__), "..", "db", "schema.sql")


def run_script(path):
    """Execute a multi-statement SQL file (psycopg2 handles that when no parameters are passed)."""
    raw = engine.raw_connection()
    try:
        with raw.cursor() as cur, open(path, encoding="utf-8") as f:
            cur.execute(f.read())
        raw.commit()
    finally:
        raw.close()


def _reset_schema():
    with engine.begin() as c:
        c.execute(text("DROP SCHEMA public CASCADE"))
        c.execute(text("CREATE SCHEMA public"))
    run_script(SCHEMA_SQL)


def _truncate_all():
    names = ", ".join(t for t in models.Base.metadata.tables)
    with engine.begin() as c:
        c.execute(text(f"TRUNCATE TABLE {names} RESTART IDENTITY CASCADE"))


def _seed_tiers():
    with engine.begin() as c:
        c.execute(text(
            "INSERT INTO membership_tier (tier_name, description, monthly_fee, free_upgrades, bonus_point_rate) VALUES "
            "('Standard','Default tier',0.00,0,1.00),"
            "('Premium','Premium tier',9.99,1,1.25),"
            "('Elite','Elite tier',19.99,3,1.50)"
        ))


@pytest.fixture(scope="session", autouse=True)
def _schema():
    _reset_schema()
    yield


@pytest.fixture(autouse=True)
def _clean_db():
    _truncate_all()
    _seed_tiers()
    yield


@pytest.fixture()
def client():
    # raise_server_exceptions=False => a crash shows up as a 500 response (like in production)
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture()
def sql():
    """Raw SQL helper for state that has no API endpoint."""
    def run(query, **params):
        with engine.begin() as c:
            res = c.execute(text(query), params)
            return res.fetchall() if res.returns_rows else None
    return run


# --------------------------------------------------------------------------- factories
_counter = {"n": 0}


def _n():
    _counter["n"] += 1
    return _counter["n"]


def iso(dt):
    return dt.strftime("%Y-%m-%dT%H:%M:%S")


NOW = datetime.now().replace(microsecond=0)


@pytest.fixture()
def make(client):
    class F:
        def location(self, **kw):
            n = _n()
            body = dict(name=f"Branch {n}", address=f"{n} Main St", city="Springfield",
                        state="IL", zip_code="62701", phone="555-0100", operating_hours="9-5")
            body.update(kw)
            r = client.post("/locations/", json=body)
            assert r.status_code == 201, r.text
            return r.json()

        def employee(self, **kw):
            n = _n()
            body = dict(first_name="Emp", last_name=f"N{n}", email=f"emp{n}@example.com",
                        phone="555-0111", role="Agent", hire_date="2024-01-15", salary="50000.00")
            body.update(kw)
            r = client.post("/employees/", json=body)
            assert r.status_code == 201, r.text
            return r.json()

        def customer(self, **kw):
            n = _n()
            body = dict(first_name="Cust", last_name=f"N{n}", email=f"cust{n}@example.com",
                        phone="555-0122", address="1 Elm St", driver_license=f"DL{n:08d}",
                        date_of_birth="1990-05-20")
            body.update(kw)
            r = client.post("/customers/", json=body)
            assert r.status_code == 201, r.text
            return r.json()

        def vehicle(self, **kw):
            n = _n()
            body = dict(model="Civic", make="Honda", license_plate=f"PL{n:05d}", year=2022,
                        daily_rate="50.00", mileage=1000, fuel_type="Gasoline",
                        transmission="Automatic", seating_capacity=5)
            body.update(kw)
            r = client.post("/vehicles/", json=body)
            assert r.status_code == 201, r.text
            return r.json()

        def rental_body(self, customer, vehicle, loc, **kw):
            body = dict(customer_id=customer["customer_id"], vehicle_id=vehicle["vehicle_id"],
                        pickup_location_id=loc["location_id"], return_location_id=loc["location_id"],
                        start_date=iso(NOW), end_date=iso(NOW + timedelta(days=3)),
                        daily_rate="50.00", total_amount="150.00", security_deposit="200.00",
                        mileage_start=1000, fuel_level_start="1.00")
            body.update(kw)
            return body

        def rental(self, customer, vehicle, loc, **kw):
            r = client.post("/rentals/", json=self.rental_body(customer, vehicle, loc, **kw))
            assert r.status_code == 201, r.text
            return r.json()

        def reservation_body(self, customer, vehicle, loc, start, end, **kw):
            body = dict(customer_id=customer["customer_id"], vehicle_id=vehicle["vehicle_id"],
                        pickup_location_id=loc["location_id"], return_location_id=loc["location_id"],
                        reserved_start_date=iso(start), reserved_end_date=iso(end),
                        estimated_total="150.00")
            body.update(kw)
            return body

        def reservation(self, customer, vehicle, loc, start, end, **kw):
            r = client.post("/reservations/", json=self.reservation_body(customer, vehicle, loc, start, end, **kw))
            assert r.status_code == 201, r.text
            return r.json()

        def base(self):
            """location + customer + vehicle, the usual starting point"""
            return self.location(), self.customer(), self.vehicle()

    return F()
