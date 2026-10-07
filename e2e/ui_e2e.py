#!/usr/bin/env python3
"""
End-to-end UI test: drives the real React app (http://localhost:5173) in headless Chromium against the
real FastAPI backend (http://localhost:8000) + PostgreSQL.

  * every step performs actions the way a user would (fill form, click button, accept confirm())
  * the API is only used as a read-only oracle to verify what was REALLY persisted
  * every failed HTTP call / network failure / console error / alert() is recorded per step

Usage:  python3 e2e/ui_e2e.py [--json out.json]
WARNING: wipes every table of the `car_rental` PostgreSQL database (override with E2E_DB_NAME / E2E_DB_HOST /
E2E_DB_PORT / E2E_DB_USER / E2E_DB_PASSWORD).
"""
import json
import os
import sys
import time
import traceback
import urllib.request
from datetime import date, datetime, timedelta

import psycopg2
from playwright.sync_api import sync_playwright

UI = os.getenv("E2E_UI", "http://localhost:5173")
API = os.getenv("E2E_API", "http://localhost:8000")
DB_NAME = os.getenv("E2E_DB_NAME", "car_rental")
DB_HOST = os.getenv("E2E_DB_HOST", "127.0.0.1")
DB_PORT = int(os.getenv("E2E_DB_PORT", "5432"))
DB_USER = os.getenv("E2E_DB_USER", "rental")
DB_PASS = os.getenv("E2E_DB_PASSWORD", "rental")

now = datetime.now().replace(second=0, microsecond=0)
dt = lambda d: d.strftime("%Y-%m-%dT%H:%M")  # noqa: E731  (datetime-local format)


# ------------------------------------------------------------------ db / api helpers
def _connect():
    cn = psycopg2.connect(host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASS, dbname=DB_NAME)
    cn.autocommit = True
    return cn


def reset_db():
    cn = _connect()
    cur = cn.cursor()
    cur.execute("SELECT tablename FROM pg_tables WHERE schemaname='public'")
    tables = [t for (t,) in cur.fetchall()]
    cur.execute("TRUNCATE TABLE " + ", ".join(tables) + " RESTART IDENTITY CASCADE")
    cur.execute("INSERT INTO membership_tier VALUES ('Standard','Default',0.00,0,1.00),('Premium','Premium',9.99,1,1.25)")
    cur.execute("INSERT INTO vehicle_feature (name, category) VALUES ('GPS','Convenience'),('Bluetooth','Entertainment')")
    cn.close()


def sql(q, *a):
    cn = _connect()
    cur = cn.cursor()
    cur.execute(q.replace("%s", "%s"), a)
    out = cur.fetchall() if cur.description else None
    cn.close()
    return out


def api(path):
    with urllib.request.urlopen(API + path, timeout=10) as r:
        return json.loads(r.read())


# ------------------------------------------------------------------ result tracking
results = []
events = []  # raw per-step event buffer


class Step:
    def __init__(self, name):
        self.name = name

    def __enter__(self):
        events.clear()
        self.t = time.time()
        return self

    def __exit__(self, et, ev, tb):
        problems = list(events)
        status = "PASS"
        detail = ""
        if et is not None:
            status = "FAIL"
            detail = f"{et.__name__}: {str(ev).splitlines()[0][:300] if str(ev) else ''}"
        elif problems:
            status = "WARN"
        results.append(dict(step=self.name, status=status, detail=detail, events=problems))
        icon = {"PASS": "✅", "FAIL": "❌", "WARN": "⚠️ "}[status]
        print(f"{icon} {self.name}" + (f"\n     {detail}" if detail else ""))
        for p in problems:
            print(f"     · {p}")
        return True  # keep going after a failed step


def check(cond, msg):
    if not cond:
        raise AssertionError(msg)


# ------------------------------------------------------------------ page helpers
class UIDriver:
    def __init__(self, page):
        self.p = page
        page.on("response", self._on_response)
        page.on("requestfailed", lambda r: events.append(f"NETWORK FAILURE {r.method} {r.url} -> {r.failure}"))
        page.on("console", lambda m: events.append(f"console.{m.type}: {m.text[:200]}") if m.type == "error" and "favicon" not in m.text else None)
        page.on("pageerror", lambda e: events.append(f"JS EXCEPTION: {str(e)[:200]}"))
        page.on("dialog", self._on_dialog)
        self.dialogs = []

    def _on_response(self, r):
        if r.url.startswith(API) and r.status >= 400:
            events.append(f"HTTP {r.status} {r.request.method} {r.url.replace(API, '')}")

    def _on_dialog(self, d):
        self.dialogs.append((d.type, d.message))
        events.append(f"{d.type}() shown: {d.message!r}")
        d.accept()

    def goto(self, path):
        self.p.goto(UI + path)
        self.p.wait_for_load_state("networkidle")

    def text(self):
        return self.p.inner_text("body")

    def wait_text(self, s, timeout=6000):
        self.p.wait_for_function("(s) => document.body.innerText.includes(s)", arg=s, timeout=timeout)

    def has(self, s):
        return s in self.text()

    def fill(self, **fields):
        for k, v in fields.items():
            if v is None:
                continue
            el = self.p.locator(f"#{k}")
            tag = el.evaluate("e => e.tagName")
            if tag == "SELECT":
                self.select(k, str(v))
            elif tag == "INPUT" and el.get_attribute("type") == "checkbox":
                if el.is_checked() != bool(v):
                    el.click()
            else:
                el.fill(str(v))

    def select(self, id_, text_or_value):
        opts = self.p.locator(f"#{id_} option").evaluate_all("els => els.map(e => [e.value, e.textContent])")
        for val, txt in opts:
            if val == text_or_value or text_or_value in (txt or ""):
                self.p.select_option(f"#{id_}", value=val)
                return
        raise AssertionError(f"no option matching {text_or_value!r} in #{id_}: {opts}")

    def submit(self):
        self.p.click("button[type=submit]")
        self.p.wait_for_load_state("networkidle")
        self.p.wait_for_timeout(400)

    def click_text(self, label, exact=False):
        self.p.get_by_role("button", name=label, exact=exact).first.click()
        self.p.wait_for_load_state("networkidle")
        self.p.wait_for_timeout(400)


# ------------------------------------------------------------------ the scenario
def main():
    reset_db()
    out_json = sys.argv[sys.argv.index("--json") + 1] if "--json" in sys.argv else None
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_context(viewport={"width": 1400, "height": 900}).new_page()
        ui = UIDriver(page)

        # ---------------------------------------------------------- empty app
        with Step("Dashboard loads on an empty database"):
            ui.goto("/")
            check("/dashboard" in page.url, f"did not redirect to dashboard: {page.url}")
            check(not ui.has("NaN"), "NaN on dashboard")
            check(not ui.has("Failed to load"), "dashboard shows load error")

        for path, name in [("/customers", "Customers"), ("/vehicles", "Vehicles"), ("/rentals", "Rentals"),
                           ("/reservations", "Reservations"), ("/employees", "Employees"), ("/locations", "Locations"),
                           ("/maintenance", "Maintenance"), ("/incidents", "Incidents"), ("/reports", "Reports")]:
            with Step(f"{name} list page renders (empty state)"):
                ui.goto(path)
                check(not ui.has("Failed to load"), f"{name}: shows 'Failed to load'")
                check(not ui.has("NaN"), f"{name}: NaN on page")

        # ---------------------------------------------------------- locations
        with Step("Create location via form"):
            ui.goto("/locations/new")
            ui.fill(name="Downtown Branch", address="1 Main St", city="Springfield", state="IL", zip_code="62701",
                    phone="555-1000", operating_hours="8-6")
            ui.submit()
            ui.goto("/locations")
            check(ui.has("Downtown Branch"), "new location not listed")
            check(len(api("/locations/")) == 1, "location not persisted")

        with Step("Create 2nd location via form"):
            ui.goto("/locations/new")
            ui.fill(name="Airport Branch", address="9 Air Rd", city="Chicago", state="IL", zip_code="60666")
            ui.submit()
            check(len(api("/locations/")) == 2, "2nd location not persisted")

        # ---------------------------------------------------------- employees
        for role, first in [("Manager", "Maya"), ("Agent", "Andy"), ("Mechanic", "Mo")]:
            with Step(f"Create employee ({role}) via form"):
                ui.goto("/employees/new")
                ui.fill(first_name=first, last_name="Staff", email=f"{first.lower()}@example.com", phone="555-2000",
                        role=role, hire_date="2023-03-01", salary="52000", location_id="Downtown")
                ui.submit()
                ui.goto("/employees")
                check(ui.has(first), f"{first} not listed")
        with Step("Employee list active/all filter works"):
            ui.goto("/employees")
            ui.click_text("All")
            check(ui.has("Maya") and ui.has("Mo"), "employees missing after clicking All")

        with Step("Duplicate employee email shows an error and does not crash"):
            ui.goto("/employees/new")
            ui.fill(first_name="Dup", last_name="Staff", email="maya@example.com", phone="1", role="Agent", hire_date="2023-03-01")
            ui.submit()
            check(len(api("/employees/")) == 3, "duplicate employee was created")

        # ---------------------------------------------------------- customers
        for i, (fn, ln) in enumerate([("Alice", "Anderson"), ("Bob", "Brown"), ("Carol", "Chen")]):
            with Step(f"Create customer {fn} via form"):
                ui.goto("/customers/new")
                ui.fill(first_name=fn, last_name=ln, email=f"{fn.lower()}@example.com", phone=f"555-30{i}0",
                        driver_license=f"DL-{fn[:3].upper()}-{i}", date_of_birth="1990-04-12", address=f"{i} Oak Ave")
                ui.submit()
                ui.goto("/customers")
                check(ui.has(fn), f"{fn} not listed")

        with Step("Customer search by name"):
            ui.goto("/customers")
            page.fill("input[placeholder^='Search customers']", "Brown")
            ui.click_text("Search")
            check(ui.has("Bob") and not ui.has("Alice"), "name search did not filter correctly")

        with Step("Customer search by driver license (placeholder promises license search)"):
            ui.goto("/customers")
            page.fill("input[placeholder^='Search customers']", "DL-CAR-2")
            ui.click_text("Search")
            check(ui.has("Carol") and not ui.has("Alice"), "searching by license number found nothing")

        with Step("Customer detail page"):
            cid = api("/customers/")[0]["customer_id"]
            ui.goto(f"/customers/{cid}")
            check(ui.has("Alice"), "customer detail missing name")
            check(not ui.has("NaN"), "NaN on customer detail")

        with Step("New customer has a membership profile visible on detail page"):
            ui.goto(f"/customers/{cid}")
            prof = api(f"/customers/{cid}")["membership_profile"]
            check(prof is not None, "no membership profile for newly created customer")

        with Step("Edit customer via form"):
            ui.goto(f"/customers/{cid}/edit")
            page.wait_for_function("document.querySelector('#first_name') && document.querySelector('#first_name').value !== ''")
            ui.fill(phone="555-9999")
            ui.submit()
            check(api(f"/customers/{cid}")["phone"] == "555-9999", "customer edit not persisted")

        with Step("Edit customer to a duplicate email is handled gracefully (no 500 / CORS failure)"):
            ui.goto(f"/customers/{cid}/edit")
            page.wait_for_function("document.querySelector('#first_name').value !== ''")
            ui.fill(email="bob@example.com")
            ui.submit()
            check(api(f"/customers/{cid}")["email"] == "alice@example.com", "duplicate email was saved")
            check(not any("500" in e or "NETWORK FAILURE" in e for e in events), "server crashed / CORS-blocked on duplicate email")

        with Step("Create customer with duplicate email shows an error"):
            ui.goto("/customers/new")
            ui.fill(first_name="Dup", last_name="Cust", email="alice@example.com", phone="1", driver_license="DL-DUP-1")
            ui.submit()
            check(len(api("/customers/")) == 3, "duplicate customer created")

        # ---------------------------------------------------------- vehicles
        for plate, make, model, rate, miles in [("CAR-001", "Toyota", "Corolla", "45", 12000),
                                                ("CAR-002", "Honda", "Civic", "50", 8000),
                                                ("CAR-003", "Ford", "Focus", "40", 30000),
                                                ("CAR-004", "Tesla", "Model3", "90", 500)]:
            with Step(f"Create vehicle {plate} via form"):
                ui.goto("/vehicles/new")
                ui.fill(make=make, model=model, license_plate=plate, year=2022, daily_rate=rate, mileage=miles,
                        seating_capacity=5, location_id="Downtown")
                ui.submit()
                ui.goto("/vehicles")
                check(ui.has(plate), f"{plate} not listed")

        v = {x["license_plate"]: x for x in api("/vehicles/")}

        with Step("Vehicle detail page renders (features, maintenance record present)"):
            vid = v["CAR-001"]["vehicle_id"]
            fid = sql("SELECT feature_id FROM vehicle_feature LIMIT 1")[0][0]
            sql("INSERT INTO vehicle_feature_mapping VALUES (%s,%s)", vid, fid)
            sql("INSERT INTO vehicle_maintenance_record (vehicle_id,last_service_date,next_service_due,total_maintenance_cost,current_condition) "
                "VALUES (%s,%s,%s,0,'Good')", vid, str(date.today() - timedelta(days=60)), str(date.today() - timedelta(days=1)))
            ui.goto(f"/vehicles/{vid}")
            check(ui.has("Corolla"), "vehicle detail missing model")
            check(ui.has("GPS"), "vehicle feature not shown")
            check(not ui.has("NaN"), "NaN on vehicle detail")

        with Step("Toggle vehicle availability from detail page (Mark Unavailable)"):
            ui.goto(f"/vehicles/{vid}")
            ui.click_text("Mark Unavailable")
            check(api(f"/vehicles/{vid}")["availability"] is False, "availability was NOT changed")
            check(ui.has("Mark Available"), "button did not flip")

        with Step("Toggle vehicle availability back (Mark Available)"):
            ui.click_text("Mark Available")
            check(api(f"/vehicles/{vid}")["availability"] is True, "availability was NOT restored")

        with Step("Edit vehicle via form"):
            ui.goto(f"/vehicles/{vid}/edit")
            page.wait_for_function("document.querySelector('#make').value !== ''")
            ui.fill(daily_rate="47.5")
            ui.submit()
            check(float(api(f"/vehicles/{vid}")["daily_rate"]) == 47.5, "vehicle edit not persisted")

        with Step("Vehicle with duplicate plate is rejected gracefully"):
            ui.goto("/vehicles/new")
            ui.fill(make="X", model="Y", license_plate="CAR-001", year=2022, daily_rate="10", location_id="Downtown")
            ui.submit()
            check(len(api("/vehicles/")) == 4, "duplicate plate created")

        with Step("Dashboard shows maintenance-needed + counts without NaN"):
            ui.goto("/dashboard")
            check(not ui.has("NaN"), "NaN on dashboard")

        # ---------------------------------------------------------- reservations
        alice, bob, carol = [c["customer_id"] for c in api("/customers/")]
        with Step("Create reservation via form"):
            ui.goto("/reservations/new")
            ui.fill(customer_id="Bob", vehicle_id="Civic", reserved_start_date=dt(now + timedelta(days=10)),
                    reserved_end_date=dt(now + timedelta(days=13)), pickup_location_id="Downtown",
                    return_location_id="Downtown")
            ui.submit()
            check(len(api("/reservations/")) == 1, "reservation not created")
            ui.goto("/reservations")
            check(ui.has("Bob") or ui.has("CAR-002") or ui.has("Active"), "reservation not listed")

        with Step("Overlapping reservation is rejected and user sees an error"):
            ui.goto("/reservations/new")
            ui.fill(customer_id="Carol", vehicle_id="Civic", reserved_start_date=dt(now + timedelta(days=11)),
                    reserved_end_date=dt(now + timedelta(days=12)), pickup_location_id="Downtown",
                    return_location_id="Downtown")
            ui.submit()
            check(len(api("/reservations/")) == 1, "overlapping reservation was accepted")

        with Step("Reservation list 'active' filter"):
            ui.goto("/reservations")
            ui.click_text("Active")
            check(not ui.has("Failed to load"), "active filter failed")

        # ---------------------------------------------------------- rentals
        with Step("Create rental via form (CAR-001, Alice)"):
            ui.goto("/rentals/new")
            page.wait_for_timeout(500)
            ui.fill(customer_id="Alice", vehicle_id="Corolla", start_date=dt(now - timedelta(days=1)),
                    end_date=dt(now + timedelta(days=2)), pickup_location_id="Downtown", return_location_id="Downtown",
                    employee_id="Andy", fuel_level_start="1")
            page.wait_for_timeout(300)
            ui.submit()
            check("/rentals" in page.url and "/new" not in page.url, f"stayed on form: {page.url}")
            rentals = api("/rentals/")
            check(len(rentals) == 1, "rental not created")
            check(api(f"/vehicles/{vid}")["availability"] is False, "vehicle not marked unavailable after rental")
            rid = rentals[0]["rental_id"]
            total = float(rentals[0]["total_amount"])
            check(total > 0, f"total_amount={total}")

        with Step("Rented vehicle disappears from the 'available' dropdown on the rental form"):
            ui.goto("/rentals/new")
            page.wait_for_timeout(400)
            opts = page.locator("#vehicle_id option").all_inner_texts()
            check(not any("Corolla" in o for o in opts), "rented vehicle still selectable")

        with Step("Rental list shows the rental"):
            ui.goto("/rentals")
            check(not ui.has("NaN"), "NaN on rentals list")
            check(ui.has("Customer #") and ui.has("ACTIVE"), "rental missing from list")

        # record a payment through the API (the UI has no payment form) so payments render
        import urllib.request as _u
        def post(path, body):
            req = _u.Request(API + path, data=json.dumps(body).encode(), headers={"Content-Type": "application/json"}, method="POST")
            return json.loads(_u.urlopen(req, timeout=10).read())
        post("/payments/", dict(rental_id=rid, amount="60.00", method="Credit Card", payment_type="Deposit"))
        post("/payments/", dict(rental_id=rid, amount="40.00", method="Cash", payment_type="Rental"))

        with Step("Rental detail renders totals/balance without NaN (2 payments recorded)"):
            ui.goto(f"/rentals/{rid}")
            body = ui.text()
            check(not ui.has("NaN"), "NaN shown on rental detail (balance / total paid)")
            check("Return Vehicle" in body, "no Return Vehicle button for active rental")

        # ---------------------------------------------------------- incident (needs an active rental)
        with Step("Report incident via form for the active rental"):
            ui.goto("/incidents/new")
            page.wait_for_timeout(400)
            ui.fill(rental_id=str(rid), incident_type="Damage", incident_date=dt(now), reported_by="Andy",
                    description="Scratch on rear bumper", estimated_cost="150", police_report_number="PR-77")
            ui.submit()
            check(len(api("/incidents/")) == 1, "incident not created")
            ui.goto("/incidents")
            check(ui.has("Scratch") or ui.has("Damage"), "incident not listed under 'open' filter")

        with Step("Incidents 'all' filter + rental detail shows the incident"):
            ui.goto("/incidents")
            ui.click_text("All")
            check(not ui.has("Failed to load"), "all filter failed")
            ui.goto(f"/rentals/{rid}")
            check(ui.has("Scratch") or ui.has("Damage"), "incident not shown on rental detail")

        # ---------------------------------------------------------- RETURN FLOW (the important one)
        with Step("Return vehicle via modal: mileage / fuel / damage fee must be saved"):
            ui.goto(f"/rentals/{rid}")
            ui.click_text("Return Vehicle", exact=True)
            inputs = page.locator("div[style*='position: fixed'] input[type=number], div[style*='fixed'] input[type=number]")
            check(inputs.count() >= 4, f"return modal inputs not found ({inputs.count()})")
            inputs.nth(0).fill("12480")      # ending mileage
            inputs.nth(1).fill("0.5")        # fuel
            inputs.nth(3).fill("35")         # damage fees
            ui.click_text("Complete Return")
            page.wait_for_timeout(500)
            r = api(f"/rentals/{rid}")
            check(r["status"] == "Completed", f"status={r['status']}")
            check(r["mileage_end"] == 12480, f"mileage_end saved as {r['mileage_end']!r}, expected 12480")
            check(float(r["fuel_level_end"] or 0) == 0.5, f"fuel_level_end saved as {r['fuel_level_end']!r}, expected 0.5")
            check(float(r["damage_fees"]) == 35.0, f"damage_fees saved as {r['damage_fees']!r}, expected 35.00")

        with Step("After return: vehicle available again with updated odometer"):
            veh = api(f"/vehicles/{vid}")
            check(veh["availability"] is True, "vehicle not available after return")
            check(veh["mileage"] == 12480, f"vehicle mileage is {veh['mileage']}, expected 12480")

        with Step("After return: customer's lifetime stats updated"):
            prof = api(f"/customers/{alice}")["membership_profile"]
            check(prof is not None, "customer has no membership profile")
            check(prof["lifetime_rentals"] == 1, f"lifetime_rentals={prof['lifetime_rentals']}")
            check(float(prof["lifetime_spending"]) > 0, "lifetime_spending not updated")

        with Step("Completed rental detail page renders without NaN"):
            ui.goto(f"/rentals/{rid}")
            check(not ui.has("NaN"), "NaN on completed rental page")
            check("Return Vehicle" not in ui.text(), "Return button still shown for completed rental")

        # ---------------------------------------------------------- late return
        with Step("Late return: fee for overdue days gets recorded (UI computes it on click)"):
            ui.goto("/rentals/new")
            page.wait_for_timeout(500)
            ui.fill(customer_id="Carol", vehicle_id="Focus", start_date=dt(now - timedelta(days=6)),
                    end_date=dt(now - timedelta(days=3)), pickup_location_id="Downtown", return_location_id="Downtown",
                    fuel_level_start="1")
            ui.submit()
            late = [r_ for r_ in api("/rentals/") if r_["vehicle_id"] == v["CAR-003"]["vehicle_id"]]
            check(len(late) == 1, "overdue rental could not be created via the form")
            lid = late[0]["rental_id"]
            ui.goto("/dashboard")
            check(ui.has("Overdue") or ui.has("overdue"), "dashboard doesn't mention overdue rentals")
            ui.goto(f"/rentals/{lid}")
            ui.click_text("Return Vehicle", exact=True)
            ui.click_text("Complete Return")
            page.wait_for_timeout(500)
            r = api(f"/rentals/{lid}")
            check(r["status"] == "Completed", f"status={r['status']}")
            check(float(r["late_fees"]) > 0, f"late_fees saved as {r['late_fees']!r} for a rental 3 days overdue")

        # ---------------------------------------------------------- maintenance
        with Step("Schedule maintenance via form"):
            ui.goto("/maintenance/new")
            page.wait_for_timeout(500)
            ui.fill(vehicle_id="Model3", maintenance_type="Oil Change", scheduled_date=str(date.today()),
                    assigned_mechanic="Mo", cost="79.99", notes="Synthetic")
            ui.submit()
            check(len(api("/maintenance/vehicle/" + str(v["CAR-004"]["vehicle_id"]))) == 1, "maintenance not saved")
            ui.goto("/maintenance")
            check(ui.has("Oil Change"), "scheduled maintenance not listed")

        with Step("Vehicle detail shows maintenance history"):
            ui.goto(f"/vehicles/{v['CAR-004']['vehicle_id']}")
            check(ui.has("Oil Change"), "maintenance history missing on vehicle page")
            check(not ui.has("NaN"), "NaN on vehicle page")

        with Step("Maintenance: future-dated job shows under the 'All' tab (but is not 'due' yet)"):
            ui.goto("/maintenance/new")
            page.wait_for_timeout(500)
            ui.fill(vehicle_id="Focus", maintenance_type="Brake Inspection", scheduled_date=str(date.today() + timedelta(days=20)),
                    assigned_mechanic="Mo", cost="120")
            ui.submit()
            ui.goto("/maintenance")
            check(not ui.has("Brake Inspection"), "future job should not be listed as due today")
            ui.click_text("All")
            check(ui.has("Brake Inspection") and ui.has("Oil Change"), "'All' tab does not list every maintenance entry")

        with Step("Customer detail shows rental history + reservations (rentalApi.getByCustomer / reservationApi.getByCustomer)"):
            ui.goto(f"/customers/{alice}")
            check("Rental History (1)" in ui.text(), "Alice's rental history missing")
            check(not ui.has("NaN"), "NaN on customer detail")
            prof = api(f"/customers/{alice}")["membership_profile"]
            check(prof["points_balance"] > 0, "no loyalty points awarded after return")
            ui.goto(f"/customers/{bob}")
            check(ui.has("Reservation"), "Bob's reservations section missing")

        with Step("Vehicle detail shows its rental history (rentalApi.filter)"):
            ui.goto(f"/vehicles/{vid}")
            check(ui.has("Rental") and not ui.has("NaN"), "vehicle rental history missing / NaN")
            check(not ui.has("Failed to load"), "vehicle page error")

        # ---------------------------------------------------------- reports
        with Step("Reports page: revenue for a range that includes today"):
            ui.goto("/reports")
            dates = page.locator("input[type=date]")
            dates.nth(0).fill(str(date.today() - timedelta(days=30)))
            dates.nth(1).fill(str(date.today()))
            page.get_by_role("button", name="Generate").first.click() if page.get_by_role("button", name="Generate").count() else page.locator("button.btn-primary").first.click()
            page.wait_for_load_state("networkidle")
            page.wait_for_timeout(500)
            check(not ui.has("NaN"), "NaN in revenue report")
            check(ui.has("$"), "no revenue amount rendered")
            rev = api(f"/rentals/revenue/report?start_date={date.today() - timedelta(days=30)}&end_date={date.today()}")
            check(float(rev["total_revenue"]) > 0, f"revenue report is {rev['total_revenue']} though 2 completed rentals started in range")

        # ---------------------------------------------------------- delete customer
        with Step("Delete a customer with no history from the customers page"):
            ui.goto("/customers")
            row = page.locator("tr", has_text="Carol")
            before = len(api("/customers/"))
            # Carol now has a rental -> test that on a clean one afterwards
            ui.goto("/customers/new")
            ui.fill(first_name="Temp", last_name="Person", email="temp@example.com", phone="1", driver_license="DL-TMP-1")
            ui.submit()
            ui.goto("/customers")
            page.locator("tr", has_text="Temp").get_by_role("button", name="Delete").click()
            page.wait_for_load_state("networkidle"); page.wait_for_timeout(500)
            check(len(api("/customers/")) == before, "clean customer not deleted")

        with Step("Delete a customer who HAS rentals/reservations (Bob has a reservation)"):
            ui.goto("/customers")
            page.locator("tr", has_text="Bob").get_by_role("button", name="Delete").click()
            page.wait_for_load_state("networkidle"); page.wait_for_timeout(500)
            check(not any("Failed to delete" in m for _, m in ui.dialogs), "UI reported 'Failed to delete customer'")
            check(bob not in [c["customer_id"] for c in api("/customers/")], "customer with reservation was not deleted")

        with Step("Final dashboard reflects reality"):
            ui.goto("/dashboard")
            check(not ui.has("NaN"), "NaN on dashboard")

        browser.close()

    # ------------------------------------------------------------------ summary
    n = {k: sum(1 for r in results if r["status"] == k) for k in ("PASS", "WARN", "FAIL")}
    print(f"\n==== {n['PASS']} passed, {n['WARN']} with warnings, {n['FAIL']} failed (of {len(results)}) ====")
    if out_json:
        json.dump(results, open(out_json, "w"), indent=1)
    sys.exit(1 if n["FAIL"] else 0)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
        sys.exit(2)
