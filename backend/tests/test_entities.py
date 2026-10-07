"""CRUD behaviour of the 'master data' entities: customers, vehicles, locations, employees."""
from datetime import date, timedelta


# =============================================================== root
def test_root(client):
    r = client.get("/")
    assert r.status_code == 200
    assert "message" in r.json()


def test_cors_allows_vite_dev_server(client):
    r = client.options("/customers/", headers={
        "Origin": "http://localhost:5173",
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "content-type",
    })
    assert r.status_code == 200
    assert r.headers.get("access-control-allow-origin") == "http://localhost:5173"


def test_cors_allows_127_0_0_1_dev_origin(client):
    """Vite prints http://127.0.0.1:5173 as well; opening it that way should not break the app."""
    r = client.options("/customers/", headers={
        "Origin": "http://127.0.0.1:5173",
        "Access-Control-Request-Method": "GET",
    })
    assert r.headers.get("access-control-allow-origin") == "http://127.0.0.1:5173"


# =============================================================== customers
def test_customer_create_and_get(client, make):
    c = make.customer(first_name="Ann", last_name="Lee")
    assert c["customer_id"] > 0
    r = client.get(f"/customers/{c['customer_id']}")
    assert r.status_code == 200
    body = r.json()
    assert body["first_name"] == "Ann"
    assert "vehicle_preferences" in body and "membership_profile" in body


def test_customer_new_customer_gets_membership_profile(client, make):
    """README: customers have membership tiers & points. A newly created customer should have a profile."""
    c = make.customer()
    r = client.get(f"/customers/{c['customer_id']}")
    assert r.json()["membership_profile"] is not None


def test_customer_duplicate_email_rejected(client, make):
    c = make.customer()
    r = client.post("/customers/", json=dict(first_name="x", last_name="y", email=c["email"],
                                             phone="1", driver_license="UNIQUE1"))
    assert r.status_code == 400


def test_customer_duplicate_license_rejected(client, make):
    c = make.customer()
    r = client.post("/customers/", json=dict(first_name="x", last_name="y", email="new@example.com",
                                             phone="1", driver_license=c["driver_license"]))
    assert r.status_code == 400


def test_customer_validation(client):
    assert client.post("/customers/", json={}).status_code == 422
    r = client.post("/customers/", json=dict(first_name="a", last_name="b", email="not-an-email",
                                             phone="1", driver_license="X"))
    assert r.status_code == 422


def test_customer_get_404(client):
    assert client.get("/customers/9999").status_code == 404


def test_customer_list_and_pagination(client, make):
    for _ in range(5):
        make.customer()
    assert len(client.get("/customers/").json()) == 5
    assert len(client.get("/customers/?skip=3&limit=10").json()) == 2
    assert client.get("/customers/?limit=0").status_code == 422
    assert client.get("/customers/?limit=1001").status_code == 422


def test_customer_update(client, make):
    c = make.customer()
    r = client.put(f"/customers/{c['customer_id']}", json={"first_name": "Changed", "phone": "999"})
    assert r.status_code == 200
    assert r.json()["first_name"] == "Changed"
    assert r.json()["last_name"] == c["last_name"]  # untouched


def test_customer_update_404(client):
    assert client.put("/customers/9999", json={"first_name": "x"}).status_code == 404


def test_customer_update_to_duplicate_email_is_client_error(client, make):
    a, b = make.customer(), make.customer()
    r = client.put(f"/customers/{b['customer_id']}", json={"email": a["email"]})
    assert r.status_code == 400, f"got {r.status_code}: {r.text[:120]}"


def test_customer_update_to_duplicate_license_is_client_error(client, make):
    a, b = make.customer(), make.customer()
    r = client.put(f"/customers/{b['customer_id']}", json={"driver_license": a["driver_license"]})
    assert r.status_code == 400, f"got {r.status_code}: {r.text[:120]}"


def test_customer_delete_simple(client, make):
    c = make.customer()
    assert client.delete(f"/customers/{c['customer_id']}").status_code == 200
    assert client.get(f"/customers/{c['customer_id']}").status_code == 404


def test_customer_delete_404(client):
    assert client.delete("/customers/9999").status_code == 404


def test_customer_delete_with_membership_profile(client, make):
    c = make.customer()
    r = client.post("/membership/", json={"customer_id": c["customer_id"]})
    assert r.status_code in (201, 400)  # may already exist if auto-created
    assert client.delete(f"/customers/{c['customer_id']}").status_code == 200


def test_customer_delete_with_rentals_and_reservations(client, make):
    """FK is ON DELETE CASCADE in the models, so deleting a customer must not crash."""
    loc, cust, veh = make.base()
    make.rental(cust, veh, loc)
    r = client.delete(f"/customers/{cust['customer_id']}")
    assert r.status_code == 200, f"got {r.status_code}: {r.text[:200]}"


def test_customer_search(client, make):
    make.customer(first_name="Zebulon", email="zeb@example.com")
    make.customer(first_name="Other")
    for q in ("zebu", "ZEB", "zeb@example"):
        r = client.get("/customers/search/", params={"q": q})
        assert r.status_code == 200
        assert len(r.json()) == 1, q
    assert client.get("/customers/search/", params={"q": "nomatch"}).json() == []
    assert client.get("/customers/search/").status_code == 422


def test_customer_search_without_trailing_slash(client, make):
    make.customer(first_name="Zebulon")
    r = client.get("/customers/search", params={"q": "Zeb"})  # redirect or direct, both fine
    assert r.status_code == 200
    assert len(r.json()) == 1


def test_customer_search_by_phone(client, make):
    make.customer(phone="555-7777")
    assert len(client.get("/customers/search/", params={"q": "7777"}).json()) == 1




def test_top_customers(client, make, sql):
    a, b = make.customer(), make.customer()
    client.post("/membership/", json={"customer_id": a["customer_id"], "lifetime_spending": "10.00"})
    client.post("/membership/", json={"customer_id": b["customer_id"], "lifetime_spending": "500.00"})
    sql("UPDATE customer_membership_profile SET lifetime_spending=10 WHERE customer_id=:c", c=a["customer_id"])
    sql("UPDATE customer_membership_profile SET lifetime_spending=500 WHERE customer_id=:c", c=b["customer_id"])
    r = client.get("/customers/top/spending")
    assert r.status_code == 200
    ids = [c["customer_id"] for c in r.json()]
    assert ids[0] == b["customer_id"]


# =============================================================== vehicles
def test_vehicle_create_get(client, make):
    loc = make.location()
    v = make.vehicle(location_id=loc["location_id"])
    r = client.get(f"/vehicles/{v['vehicle_id']}")
    assert r.status_code == 200
    body = r.json()
    assert body["make"] == "Honda"
    assert body["features"] == []
    assert body["maintenance_record"] is None


def test_vehicle_duplicate_plate(client, make):
    v = make.vehicle()
    r = client.post("/vehicles/", json=dict(model="A", make="B", license_plate=v["license_plate"],
                                            year=2020, daily_rate="10"))
    assert r.status_code == 400


def test_vehicle_validation(client):
    assert client.post("/vehicles/", json={}).status_code == 422
    r = client.post("/vehicles/", json=dict(model="A", make="B", license_plate="TOOLONGPLATE123",
                                            year=2020, daily_rate="10"))
    assert r.status_code == 422


def test_vehicle_invalid_location_is_client_error(client):
    r = client.post("/vehicles/", json=dict(model="A", make="B", license_plate="X1", year=2020,
                                            daily_rate="10", location_id=9999))
    assert r.status_code in (400, 404, 422), f"got {r.status_code}"


def test_vehicle_get_404(client):
    assert client.get("/vehicles/9999").status_code == 404


def test_vehicle_list_available_and_filter(client, make):
    a = make.vehicle(make="Toyota", model="Corolla", fuel_type="Hybrid", daily_rate="40.00", year=2021)
    b = make.vehicle(make="Ford", model="Focus", transmission="Manual", daily_rate="80.00", year=2015)
    client.patch(f"/vehicles/{b['vehicle_id']}/availability", params={"available": False})

    assert len(client.get("/vehicles/").json()) == 2
    avail = client.get("/vehicles/available").json()
    assert [v["vehicle_id"] for v in avail] == [a["vehicle_id"]]

    def f(**p):
        r = client.get("/vehicles/filter/", params=p)
        assert r.status_code == 200, r.text
        return [v["vehicle_id"] for v in r.json()]

    assert f(make="toy") == [a["vehicle_id"]]
    assert f(model="focus") == [b["vehicle_id"]]
    assert f(fuel_type="Hybrid") == [a["vehicle_id"]]
    assert f(transmission="Manual") == [b["vehicle_id"]]
    assert f(min_year=2020) == [a["vehicle_id"]]
    assert f(max_year=2016) == [b["vehicle_id"]]
    assert f(availability="true") == [a["vehicle_id"]]
    assert f(availability="false") == [b["vehicle_id"]]
    assert f(min_daily_rate=60) == [b["vehicle_id"]]
    assert f(max_daily_rate=60) == [a["vehicle_id"]]
    assert sorted(f()) == sorted([a["vehicle_id"], b["vehicle_id"]])


def test_vehicle_filter_by_location(client, make):
    l1, l2 = make.location(), make.location()
    a = make.vehicle(location_id=l1["location_id"])
    make.vehicle(location_id=l2["location_id"])
    r = client.get("/vehicles/filter/", params={"location_id": l1["location_id"]})
    assert [v["vehicle_id"] for v in r.json()] == [a["vehicle_id"]]


def test_vehicle_update(client, make):
    v = make.vehicle()
    r = client.put(f"/vehicles/{v['vehicle_id']}", json={"daily_rate": "99.99", "mileage": 5555})
    assert r.status_code == 200
    assert r.json()["daily_rate"] == 99.99
    assert r.json()["mileage"] == 5555
    assert client.put("/vehicles/9999", json={"mileage": 1}).status_code == 404


def test_vehicle_update_to_duplicate_plate_is_client_error(client, make):
    a, b = make.vehicle(), make.vehicle()
    r = client.put(f"/vehicles/{b['vehicle_id']}", json={"license_plate": a["license_plate"]})
    assert r.status_code == 400, f"got {r.status_code}: {r.text[:120]}"


def test_vehicle_availability_query_param(client, make):
    v = make.vehicle()
    r = client.patch(f"/vehicles/{v['vehicle_id']}/availability", params={"available": False})
    assert r.status_code == 200
    assert client.get(f"/vehicles/{v['vehicle_id']}").json()["availability"] is False
    assert client.patch("/vehicles/9999/availability", params={"available": True}).status_code == 404


def test_vehicle_availability_json_body_like_the_frontend_sends(client, make):
    """frontend/src/services/api.ts -> updateAvailability sends {"available": bool} as JSON body."""
    v = make.vehicle()
    r = client.patch(f"/vehicles/{v['vehicle_id']}/availability", json={"available": False})
    assert r.status_code == 200, f"got {r.status_code}: {r.text[:200]}"
    assert client.get(f"/vehicles/{v['vehicle_id']}").json()["availability"] is False


def test_vehicle_with_features_and_maintenance_record(client, make, sql):
    v = make.vehicle()
    f = client.post("/vehicle-features/", json={"name": "GPS", "category": "Convenience"}).json()
    sql("INSERT INTO vehicle_feature_mapping (vehicle_id, feature_id) VALUES (:v,:f)", v=v["vehicle_id"], f=f["feature_id"])
    sql("INSERT INTO vehicle_maintenance_record (vehicle_id, next_service_due, current_condition) VALUES (:v,:d,'Good')",
        v=v["vehicle_id"], d=str(date.today() - timedelta(days=1)))
    body = client.get(f"/vehicles/{v['vehicle_id']}").json()
    assert [x["name"] for x in body["features"]] == ["GPS"]
    assert body["maintenance_record"]["current_condition"] == "Good"
    needed = client.get("/vehicles/maintenance/needed")
    assert needed.status_code == 200
    assert [x["vehicle_id"] for x in needed.json()] == [v["vehicle_id"]]




# =============================================================== locations
def test_location_create_get_list(client, make):
    loc = make.location(city="Peoria")
    assert client.get("/locations/").json()[0]["city"] == "Peoria"
    r = client.get(f"/locations/{loc['location_id']}")
    assert r.status_code == 200
    body = r.json()
    assert body["employees"] == [] and body["vehicles"] == [] and body["manager"] is None
    assert client.get("/locations/9999").status_code == 404


def test_location_details_include_employees_vehicles_and_manager(client, make):
    loc = make.location()
    mgr = make.employee(location_id=loc["location_id"], role="Manager")
    make.vehicle(location_id=loc["location_id"])
    make.vehicle(location_id=loc["location_id"])
    # no PUT /locations endpoint => set manager through SQL
    import models  # noqa
    from database import SessionLocal
    db = SessionLocal()
    db.query(models.Location).filter_by(location_id=loc["location_id"]).update({"manager_id": mgr["employee_id"]})
    db.commit(); db.close()
    body = client.get(f"/locations/{loc['location_id']}").json()
    assert len(body["employees"]) == 1
    assert len(body["vehicles"]) == 2
    assert body["manager"]["employee_id"] == mgr["employee_id"]


def test_location_by_city(client, make):
    make.location(city="Springfield")
    make.location(city="Chicago")
    r = client.get("/locations/city/spring")
    assert r.status_code == 200 and len(r.json()) == 1


def test_location_validation(client):
    assert client.post("/locations/", json={"name": "x"}).status_code == 422




# =============================================================== employees
def test_employee_create_get_list(client, make):
    e = make.employee(role="Mechanic")
    assert client.get(f"/employees/{e['employee_id']}").json()["role"] == "Mechanic"
    assert len(client.get("/employees/").json()) == 1
    assert client.get("/employees/9999").status_code == 404


def test_employee_duplicate_email(client, make):
    e = make.employee()
    r = client.post("/employees/", json=dict(first_name="a", last_name="b", email=e["email"], phone="1",
                                             role="Agent", hire_date="2024-01-01"))
    assert r.status_code == 400


def test_employee_validation(client):
    assert client.post("/employees/", json={"first_name": "x"}).status_code == 422
    r = client.post("/employees/", json=dict(first_name="a", last_name="b", email="a@b.com", phone="1",
                                             role="Agent", hire_date="not-a-date"))
    assert r.status_code == 422


def test_employee_invalid_fk_is_client_error(client):
    r = client.post("/employees/", json=dict(first_name="a", last_name="b", email="fk@b.com", phone="1",
                                             role="Agent", hire_date="2024-01-01", location_id=9999))
    assert r.status_code in (400, 404, 422), f"got {r.status_code}"


def test_employee_active_role_location_filters(client, make, sql):
    loc = make.location()
    a = make.employee(role="Mechanic", location_id=loc["location_id"])
    b = make.employee(role="Agent")
    c = make.employee(role="Mechanic", is_active=False)
    active = [e["employee_id"] for e in client.get("/employees/active").json()]
    assert sorted(active) == sorted([a["employee_id"], b["employee_id"]])
    mech = [e["employee_id"] for e in client.get("/employees/role/Mechanic").json()]
    assert mech == [a["employee_id"]]  # inactive excluded
    assert [e["employee_id"] for e in client.get(f"/employees/location/{loc['location_id']}").json()] == [a["employee_id"]]


def test_employee_manager_hierarchy(client, make):
    boss = make.employee(role="Manager")
    sub = make.employee(manager_id=boss["employee_id"])
    assert client.get(f"/employees/{sub['employee_id']}").json()["manager_id"] == boss["employee_id"]



def test_frontend_dropdowns_can_request_limit_1000(client, make):
    """Forms call getAll(0, 1000) for customers/vehicles/locations/employees/active lists - must not be a 422."""
    make.customer(); make.vehicle(); make.location(); make.employee()
    for path in ("/customers/", "/vehicles/", "/vehicles/available", "/locations/", "/employees/", "/employees/active",
                 "/reservations/", "/reservations/active", "/rentals/", "/rentals/active", "/incidents/"):
        r = client.get(path, params={"skip": 0, "limit": 1000})
        assert r.status_code == 200, f"{path}: {r.status_code} {r.text[:100]}"
