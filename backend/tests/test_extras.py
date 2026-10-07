"""Routes added to complete the API (schemas existed, routes did not) + robustness checks."""
from datetime import date, timedelta

from conftest import NOW, iso


def test_employee_update_delete(client, make):
    e = make.employee()
    r = client.put(f"/employees/{e['employee_id']}", json={"role": "Manager"})
    assert r.status_code == 200 and r.json()["role"] == "Manager"
    other = make.employee()
    assert client.put(f"/employees/{e['employee_id']}", json={"email": other["email"]}).status_code == 400
    assert client.put(f"/employees/{e['employee_id']}", json={"manager_id": e["employee_id"]}).status_code == 400
    assert client.put("/employees/9999", json={"role": "x"}).status_code == 404
    assert client.delete(f"/employees/{e['employee_id']}").status_code == 200
    assert client.delete(f"/employees/{e['employee_id']}").status_code == 404


def test_employee_delete_keeps_their_rentals(client, make):
    loc, cust, veh = make.base()
    emp = make.employee()
    rent = make.rental(cust, veh, loc, employee_id=emp["employee_id"])
    assert client.delete(f"/employees/{emp['employee_id']}").status_code == 200
    assert client.get(f"/rentals/{rent['rental_id']}").json()["employee_id"] is None


def test_location_update_delete(client, make):
    loc = make.location()
    r = client.put(f"/locations/{loc['location_id']}", json={"name": "Renamed"})
    assert r.status_code == 200 and r.json()["name"] == "Renamed"
    assert client.delete(f"/locations/{loc['location_id']}").status_code == 200


def test_location_delete_blocked_when_in_use(client, make):
    loc, cust, veh = make.base()
    make.rental(cust, veh, loc)
    r = client.delete(f"/locations/{loc['location_id']}")
    assert r.status_code == 400 and "detail" in r.json()


def test_vehicle_delete_and_active_rental_guard(client, make):
    loc, cust, veh = make.base()
    rent = make.rental(cust, veh, loc)
    assert client.delete(f"/vehicles/{veh['vehicle_id']}").status_code == 400
    client.patch(f"/rentals/{rent['rental_id']}/return", params={"mileage_end": 1100})
    assert client.delete(f"/vehicles/{veh['vehicle_id']}").status_code == 200
    assert client.get(f"/vehicles/{veh['vehicle_id']}").status_code == 404
    assert client.get(f"/rentals/{rent['rental_id']}").status_code == 404  # history removed with it


def test_customer_delete_releases_vehicle_of_active_rental(client, make):
    loc, cust, veh = make.base()
    make.rental(cust, veh, loc)
    assert client.get(f"/vehicles/{veh['vehicle_id']}").json()["availability"] is False
    assert client.delete(f"/customers/{cust['customer_id']}").status_code == 200
    assert client.get(f"/vehicles/{veh['vehicle_id']}").json()["availability"] is True


def test_customer_delete_removes_payments_and_incidents_too(client, make, sql):
    loc, cust, veh = make.base()
    rent = make.rental(cust, veh, loc)
    client.post("/payments/", json=dict(rental_id=rent["rental_id"], amount="10", method="Cash", payment_type="Rental"))
    client.post("/incidents/", json=dict(rental_id=rent["rental_id"], incident_date=iso(NOW), incident_type="Damage", description="x"))
    assert client.delete(f"/customers/{cust['customer_id']}").status_code == 200
    assert sql("SELECT COUNT(*) FROM payment")[0][0] == 0
    assert sql("SELECT COUNT(*) FROM incident_report")[0][0] == 0


def test_feature_mapping_and_maintenance_record_routes(client, make):
    v = make.vehicle()
    f = client.post("/vehicle-features/", json={"name": "GPS"}).json()
    assert client.post(f"/vehicles/{v['vehicle_id']}/features/{f['feature_id']}").status_code == 201
    assert client.post(f"/vehicles/{v['vehicle_id']}/features/{f['feature_id']}").status_code == 201  # idempotent
    assert [x["name"] for x in client.get(f"/vehicles/{v['vehicle_id']}").json()["features"]] == ["GPS"]
    assert client.delete(f"/vehicles/{v['vehicle_id']}/features/{f['feature_id']}").status_code == 200
    assert client.get(f"/vehicles/{v['vehicle_id']}").json()["features"] == []
    assert client.post(f"/vehicles/{v['vehicle_id']}/features/9999").status_code == 404

    r = client.put(f"/vehicles/{v['vehicle_id']}/maintenance-record",
                   json={"next_service_due": str(date.today() - timedelta(days=1)), "current_condition": "Fair"})
    assert r.status_code == 200
    r = client.put(f"/vehicles/{v['vehicle_id']}/maintenance-record", json={"total_maintenance_cost": 120.5})
    assert r.json()["total_maintenance_cost"] == 120.5 and r.json()["current_condition"] == "Fair"
    assert [x["vehicle_id"] for x in client.get("/vehicles/maintenance/needed").json()] == [v["vehicle_id"]]


def test_null_maintenance_cost_does_not_break_vehicle_page(client, make, sql):
    v = make.vehicle()
    sql("INSERT INTO vehicle_maintenance_record (vehicle_id) VALUES (:v)", v=v["vehicle_id"])
    r = client.get(f"/vehicles/{v['vehicle_id']}")
    assert r.status_code == 200 and r.json()["maintenance_record"] is not None


def test_rental_insurance_attach_and_rental_update(client, make):
    loc, cust, veh = make.base()
    rent = make.rental(cust, veh, loc)
    plan = client.post("/insurance-plans/", json=dict(name="Basic", daily_cost="9.99", coverage_amount="1000", deductible="100")).json()
    ins = client.post(f"/rentals/{rent['rental_id']}/insurance/{plan['plan_id']}")
    assert ins.status_code == 201 and ins.json()["premium_amount"] == 9.99 * 3  # 3-day rental
    assert client.post(f"/rentals/{rent['rental_id']}/insurance/{plan['plan_id']}").status_code == 201  # idempotent
    assert client.post(f"/rentals/{rent['rental_id']}/insurance/9999").status_code == 404
    assert client.put(f"/insurance-plans/{plan['plan_id']}", json={"is_active": False}).json()["is_active"] is False
    r = client.put(f"/rentals/{rent['rental_id']}", json={"total_amount": 175})
    assert r.status_code == 200 and r.json()["total_amount"] == 175
    assert client.put(f"/rentals/{rent['rental_id']}", json={"end_date": iso(NOW - timedelta(days=9))}).status_code == 400


def test_payment_incident_maintenance_updates(client, make):
    loc, cust, veh = make.base()
    rent = make.rental(cust, veh, loc)
    p = client.post("/payments/", json=dict(rental_id=rent["rental_id"], amount="10", method="Cash", payment_type="Rental", status="Failed")).json()
    assert client.put(f"/payments/{p['payment_id']}", json={"status": "Completed"}).json()["status"] == "Completed"
    i = client.post("/incidents/", json=dict(rental_id=rent["rental_id"], incident_date=iso(NOW), incident_type="Damage", description="x")).json()
    assert client.put(f"/incidents/{i['incident_id']}", json={"status": "Closed"}).json()["status"] == "Closed"
    m = client.post("/maintenance/", json=dict(vehicle_id=veh["vehicle_id"], maintenance_type="Oil", scheduled_date=str(date.today()))).json()
    assert client.put(f"/maintenance/{m['schedule_id']}", json={"status": "Completed"}).json()["status"] == "Completed"
    assert client.get("/maintenance/scheduled").json() == []
    for path in ("/payments/9999", "/incidents/9999", "/maintenance/9999", "/insurance-plans/9999"):
        assert client.put(path, json={}).status_code == 404


def test_membership_update_and_auto_points_on_return(client, make):
    loc, cust, veh = make.base()
    assert client.put(f"/membership/{cust['customer_id']}", json={"membership_tier": "Premium"}).json()["membership_tier"] == "Premium"
    assert client.put(f"/membership/{cust['customer_id']}", json={"membership_tier": "Nope"}).status_code == 400
    rent = make.rental(cust, veh, loc, total_amount="100.00")
    client.patch(f"/rentals/{rent['rental_id']}/return", json={"mileage_end": 1100})
    prof = client.get(f"/customers/{cust['customer_id']}").json()["membership_profile"]
    assert prof["points_balance"] == 125  # 100 * Premium bonus rate 1.25
    assert prof["lifetime_spending"] == 100.0


def test_return_late_fee_matches_ui_rule(client, make):
    loc, cust, veh = make.base()
    r = make.rental(cust, veh, loc, daily_rate="40.00", start_date=iso(NOW - timedelta(days=10)), end_date=iso(NOW - timedelta(days=2, hours=1)))
    out = client.patch(f"/rentals/{r['rental_id']}/return", json={}).json()
    assert out["late_fees"] == 3 * 40.0 * 0.5  # 3 started days late


def test_customer_preferences(client, make):
    c = make.customer()
    r = client.post(f"/customers/{c['customer_id']}/preferences", json={"vehicle_type": "SUV", "preference_score": 8})
    assert r.status_code == 201
    client.post(f"/customers/{c['customer_id']}/preferences", json={"vehicle_type": "SUV", "preference_score": 3})
    prefs = client.get(f"/customers/{c['customer_id']}").json()["vehicle_preferences"]
    assert [(p["vehicle_type"], p["preference_score"]) for p in prefs] == [("SUV", 3)]


def test_errors_are_json_detail_and_have_cors_headers(client):
    r = client.post("/customers/", json={}, headers={"Origin": "http://localhost:5173"})
    assert r.status_code == 422 and isinstance(r.json()["detail"], str)
    assert r.headers["access-control-allow-origin"] == "http://localhost:5173"
    r = client.get("/customers/9999", headers={"Origin": "http://localhost:5174"})
    assert r.headers["access-control-allow-origin"] == "http://localhost:5174"
    r = client.get("/customers/9999", headers={"Origin": "http://evil.example.com"})
    assert "access-control-allow-origin" not in r.headers


def test_unhandled_exception_still_returns_json_with_cors(client, monkeypatch):
    import crud
    monkeypatch.setattr(crud.customer, "get_multi", lambda *a, **k: 1 / 0)
    r = client.get("/customers/", headers={"Origin": "http://localhost:5173"})
    assert r.status_code == 500 and r.json()["detail"]
    assert r.headers["access-control-allow-origin"] == "http://localhost:5173"


def test_blank_optional_fields_from_html_forms_are_accepted(client):
    """The customer form sends date_of_birth: '' and address: '' when left empty."""
    r = client.post("/customers/", json=dict(first_name="A", last_name="B", email="blank@example.com", phone="1",
                                             driver_license="BLANK1", address="", date_of_birth=""))
    assert r.status_code == 201, r.text
    assert r.json()["date_of_birth"] is None
    r = client.post("/customers/", json=dict(first_name="A", last_name="B", email="", phone="1", driver_license="BLANK2"))
    assert r.status_code == 422  # required fields are still required


def test_blank_optional_numbers_and_ids_from_forms(client, make):
    loc = make.location()
    r = client.post("/employees/", json=dict(first_name="E", last_name="F", email="e@example.com", phone="1", role="Agent",
                                             hire_date="2024-01-01", salary="", location_id="", manager_id=""))
    assert r.status_code == 201, r.text


def test_maintenance_list_all_includes_future_and_completed(client, make):
    veh = make.vehicle()
    for d, st in ((date.today() + timedelta(days=20), "Scheduled"), (date.today() - timedelta(days=5), "Completed")):
        client.post("/maintenance/", json=dict(vehicle_id=veh["vehicle_id"], maintenance_type="X", scheduled_date=str(d), status=st))
    r = client.get("/maintenance/", params={"limit": 1000})
    assert r.status_code == 200 and len(r.json()) == 2
    assert r.json()[0]["scheduled_date"] > r.json()[1]["scheduled_date"]  # newest first
    assert client.get("/maintenance/scheduled").json() == []  # the future one is not "due" yet


# ------------------------------------------------------------------ demo reset (portfolio deployment)
def test_reset_demo_restores_example_data(client, make):
    make.customer(first_name="Temporary")
    r = client.post("/admin/reset-demo")
    assert r.status_code == 200, r.text
    assert len(client.get("/vehicles/", params={"limit": 1000}).json()) == 4
    names = {c["first_name"] for c in client.get("/customers/", params={"limit": 1000}).json()}
    assert names == {"Alice", "Bob", "Carol"}


def test_reset_demo_can_be_disabled(client, monkeypatch):
    monkeypatch.setenv("DEMO_RESET_ENABLED", "0")
    assert client.post("/admin/reset-demo").status_code == 403
