"""PostgreSQL-specific behaviour: schema/init scripts, case-insensitivity, triggers, DB-level defaults and FK actions."""
import importlib.util
import os
import subprocess
import sys
import time

import pytest
from sqlalchemy import inspect

import models
from conftest import NOW, TEST_DB, engine, iso, run_script

BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DB_DIR = os.path.join(BACKEND_DIR, "db")


def _generator():
    spec = importlib.util.spec_from_file_location("generate_schema", os.path.join(DB_DIR, "generate_schema.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ------------------------------------------------------------------ init scripts
def test_schema_sql_is_in_sync_with_models():
    expected = _generator().build()
    actual = open(os.path.join(DB_DIR, "schema.sql"), encoding="utf-8").read()
    assert actual == expected, "database/schema.sql is stale - run: python database/generate_schema.py"


def test_database_matches_models(client):
    insp = inspect(engine)
    assert set(insp.get_table_names()) == set(models.Base.metadata.tables)
    for name, table in models.Base.metadata.tables.items():
        assert {c["name"] for c in insp.get_columns(name)} == {c.name for c in table.columns}, name


def test_schema_sql_is_rerunnable_and_keeps_data(client, make):
    make.customer(first_name="Keepme")
    run_script(os.path.join(DB_DIR, "schema.sql"))
    run_script(os.path.join(DB_DIR, "schema.sql"))
    assert [c["first_name"] for c in client.get("/customers/").json()] == ["Keepme"]


def test_seed_is_idempotent_and_provides_standard_tier(client, sql):
    sql("TRUNCATE membership_tier CASCADE")
    run_script(os.path.join(DB_DIR, "seed.sql"))
    run_script(os.path.join(DB_DIR, "seed.sql"))
    assert {t["tier_name"] for t in client.get("/membership-tiers/").json()} == {"Standard", "Premium", "Elite"}
    assert len(client.get("/insurance-plans/").json()) == 3
    assert len(client.get("/vehicle-features/").json()) == 8


def test_sample_data_loads_once_and_works_end_to_end(client, sql):
    for f in ("seed.sql", "sample_data.sql", "sample_data.sql"):  # second load must be a no-op
        run_script(os.path.join(DB_DIR, f))
    assert len(client.get("/customers/").json()) == 3
    assert len(client.get("/vehicles/available").json()) == 4
    assert len(client.get("/locations/").json()) == 2
    # a customer from the sample data can rent a sample vehicle and return it
    cust = client.get("/customers/").json()[0]
    veh = client.get("/vehicles/available").json()[0]
    loc = client.get("/locations/").json()[0]
    r = client.post("/rentals/", json=dict(
        customer_id=cust["customer_id"], vehicle_id=veh["vehicle_id"], pickup_location_id=loc["location_id"],
        return_location_id=loc["location_id"], start_date=iso(NOW), end_date=iso(NOW.replace(year=NOW.year + 1)),
        daily_rate=veh["daily_rate"], total_amount="100.00"))
    assert r.status_code == 201, r.text
    assert client.patch(f"/rentals/{r.json()['rental_id']}/return", json={"mileage_end": veh["mileage"] + 10}).status_code == 200


def _run_cli(*args, url=TEST_DB):
    env = dict(os.environ, DATABASE_URL=url)
    return subprocess.run([sys.executable, os.path.join(DB_DIR, "init_db.py"), *args], capture_output=True, text=True, env=env, timeout=120)


def test_init_db_cli_reset_needs_confirmation_then_rebuilds(client):
    r = _run_cli("--reset")
    assert r.returncode != 0 and "--yes" in (r.stdout + r.stderr)
    r = _run_cli("--reset", "--yes", "--sample-data")
    assert r.returncode == 0, r.stderr
    assert "17 tables" in r.stdout
    assert len(client.get("/customers/").json()) == 3


def test_init_db_cli_rejects_non_postgres_url():
    r = _run_cli(url="mysql+pymysql://u:p@localhost/db")
    assert r.returncode != 0 and "PostgreSQL" in (r.stdout + r.stderr)


def test_postgres_scheme_urls_are_normalised():
    """Hosting providers hand out postgres://... URLs, which SQLAlchemy rejects unless normalised."""
    for given in ("postgres://u:p@localhost/db", "postgresql://u:p@localhost/db"):
        env = dict(os.environ, DATABASE_URL=given)
        out = subprocess.run([sys.executable, "-c", "import database; print(database.engine.url.drivername)"],
                             capture_output=True, text=True, env=env, cwd=BACKEND_DIR)
        assert out.stdout.strip() == "postgresql+psycopg2", out.stderr


# ------------------------------------------------------------------ case sensitivity (MySQL was case-insensitive)
def test_customer_email_and_license_are_case_insensitive_unique(client, make):
    c = make.customer(email="Case@Example.com", driver_license="AbC123")
    r = client.post("/customers/", json=dict(first_name="x", last_name="y", email="case@example.COM", phone="1", driver_license="Z9"))
    assert r.status_code == 400 and "Email" in r.json()["detail"]
    r = client.post("/customers/", json=dict(first_name="x", last_name="y", email="z@example.com", phone="1", driver_license="abc123"))
    assert r.status_code == 400 and "license" in r.json()["detail"]
    other = make.customer()
    assert client.put(f"/customers/{other['customer_id']}", json={"email": "CASE@example.com"}).status_code == 400


def test_vehicle_plate_and_employee_email_are_case_insensitive_unique(client, make):
    v = make.vehicle(license_plate="ab-123")
    assert client.post("/vehicles/", json=dict(model="A", make="B", license_plate="AB-123", year=2020, daily_rate="1")).status_code == 400
    e = make.employee(email="Boss@Example.com")
    assert client.post("/employees/", json=dict(first_name="a", last_name="b", email="boss@example.com", phone="1",
                                                role="Agent", hire_date="2024-01-01")).status_code == 400


def test_database_itself_rejects_case_variant_duplicates(make, sql):
    """Even a raw INSERT (bypassing the API) cannot create 'A@x.com' and 'a@x.com'."""
    make.customer(email="Dup@Example.com")
    with pytest.raises(Exception) as exc:
        sql("INSERT INTO customer (first_name,last_name,email,phone,driver_license) VALUES ('a','b','dup@example.com','1','UNIQ-X')")
    assert "unique" in str(exc.value).lower()


def test_search_and_role_lookups_are_case_insensitive(client, make):
    make.customer(first_name="Zebulon")
    assert len(client.get("/customers/search/", params={"q": "ZEBU"}).json()) == 1
    make.employee(role="Mechanic")
    assert len(client.get("/employees/role/mechanic").json()) == 1


# ------------------------------------------------------------------ database-level behaviour
def test_updated_at_trigger(make, sql):
    c = make.customer()
    before = sql("SELECT updated_at FROM customer WHERE customer_id=:i", i=c["customer_id"])[0][0]
    time.sleep(0.05)
    sql("UPDATE customer SET phone='555-0000' WHERE customer_id=:i", i=c["customer_id"])  # plain SQL, no ORM
    after = sql("SELECT updated_at FROM customer WHERE customer_id=:i", i=c["customer_id"])[0][0]
    assert after > before


def test_raw_inserts_get_the_same_defaults_as_the_api(sql, make):
    v = make.vehicle()
    sql("INSERT INTO vehicle_maintenance_record (vehicle_id) VALUES (:v)", v=v["vehicle_id"])
    row = sql("SELECT total_maintenance_cost, current_condition FROM vehicle_maintenance_record")[0]
    assert float(row[0]) == 0 and row[1] == "Good"
    sql("INSERT INTO vehicle (model, make, license_plate, year, daily_rate) VALUES ('M','K','RAW-1',2020,10)")
    row = sql("SELECT availability, mileage, fuel_type, transmission, seating_capacity, created_at FROM vehicle WHERE license_plate='RAW-1'")[0]
    assert row[0] is True and row[1] == 0 and row[2] == "Gasoline" and row[3] == "Automatic" and row[4] == 5 and row[5] is not None
    c = make.customer()
    sql("INSERT INTO customer_membership_profile (customer_id) VALUES (:c)", c=c["customer_id"]) if not sql(
        "SELECT 1 FROM customer_membership_profile WHERE customer_id=:c", c=c["customer_id"]) else None
    prof = sql("SELECT membership_tier, points_balance, lifetime_rentals, lifetime_spending, join_date FROM customer_membership_profile")[0]
    assert prof[0] == "Standard" and prof[1] == 0 and prof[2] == 0 and float(prof[3]) == 0 and prof[4] is not None


def test_deleting_employee_or_location_in_sql_nulls_references(client, make, sql):
    loc, cust, veh = make.base()
    emp = make.employee(location_id=loc["location_id"])
    rent = make.rental(cust, veh, loc, employee_id=emp["employee_id"])
    sql("DELETE FROM employee WHERE employee_id=:e", e=emp["employee_id"])      # ON DELETE SET NULL
    assert client.get(f"/rentals/{rent['rental_id']}").json()["employee_id"] is None
    v2 = make.vehicle(location_id=loc["location_id"])
    sql("DELETE FROM location WHERE location_id=:l AND NOT EXISTS (SELECT 1 FROM rental WHERE pickup_location_id=:l)", l=loc["location_id"])
    other = make.location()
    v3 = make.vehicle(location_id=other["location_id"])
    sql("DELETE FROM location WHERE location_id=:l", l=other["location_id"])
    assert client.get(f"/vehicles/{v3['vehicle_id']}").json()["location_id"] is None


def test_cascades_at_database_level(client, make, sql):
    loc, cust, veh = make.base()
    rent = make.rental(cust, veh, loc)
    client.post("/payments/", json=dict(rental_id=rent["rental_id"], amount="5", method="Cash", payment_type="Rental"))
    sql("DELETE FROM customer WHERE customer_id=:c", c=cust["customer_id"])      # ON DELETE CASCADE chain
    assert sql("SELECT COUNT(*) FROM rental")[0][0] == 0
    assert sql("SELECT COUNT(*) FROM payment")[0][0] == 0


def test_money_precision_is_exact(client, make):
    v = make.vehicle(daily_rate="19.99")
    r = make.rental(*[make.customer(), v, make.location()], total_amount="59.97", daily_rate="19.99")
    assert client.get(f"/rentals/{r['rental_id']}").json()["total_amount"] == 59.97


def test_lists_keep_a_stable_order_after_updates(client, make):
    """Postgres returns rows in physical order and an UPDATE moves the row. Lists must stay ordered (by id),
    otherwise the UI reshuffles after every edit and skip/limit pagination skips or repeats rows."""
    cs = [make.customer() for _ in range(4)]
    vs = [make.vehicle() for _ in range(4)]
    es = [make.employee() for _ in range(3)]
    ls = [make.location() for _ in range(3)]
    client.put(f"/customers/{cs[0]['customer_id']}", json={"phone": "999"})
    client.put(f"/vehicles/{vs[0]['vehicle_id']}", json={"mileage": 5})
    client.put(f"/employees/{es[0]['employee_id']}", json={"role": "Manager"})
    client.put(f"/locations/{ls[0]['location_id']}", json={"name": "Renamed"})
    for path, rows, key in (("/customers/", cs, "customer_id"), ("/vehicles/", vs, "vehicle_id"),
                            ("/vehicles/available", vs, "vehicle_id"), ("/employees/", es, "employee_id"),
                            ("/employees/active", es, "employee_id"), ("/locations/", ls, "location_id")):
        assert [r[key] for r in client.get(path).json()] == [r[key] for r in rows], path
    page1 = [c["customer_id"] for c in client.get("/customers/", params={"skip": 0, "limit": 2}).json()]
    page2 = [c["customer_id"] for c in client.get("/customers/", params={"skip": 2, "limit": 2}).json()]
    assert page1 + page2 == [c["customer_id"] for c in cs]
