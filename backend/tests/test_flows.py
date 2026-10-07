"""Business flows: reservations -> rentals -> returns -> payments, incidents, maintenance, membership."""
from datetime import datetime, timedelta, date

from conftest import NOW, iso


def days(n):
    return NOW + timedelta(days=n)


# =============================================================== reservations
def test_reservation_create_and_read(client, make):
    loc, cust, veh = make.base()
    r = make.reservation(cust, veh, loc, days(1), days(3))
    assert r["status"] == "Active"
    assert client.get(f"/reservations/{r['reservation_id']}").json()["vehicle_id"] == veh["vehicle_id"]
    assert client.get("/reservations/9999").status_code == 404
    assert len(client.get("/reservations/").json()) == 1


def test_reservation_conflict_detection(client, make):
    loc, cust, veh = make.base()
    make.reservation(cust, veh, loc, days(10), days(15))

    def attempt(s, e):
        return client.post("/reservations/", json=make.reservation_body(cust, veh, loc, s, e)).status_code

    assert attempt(days(12), days(13)) == 400   # fully inside
    assert attempt(days(8), days(11)) == 400    # overlaps the start
    assert attempt(days(14), days(18)) == 400   # overlaps the end
    assert attempt(days(8), days(20)) == 400    # fully surrounds
    assert attempt(days(10), days(15)) == 400   # identical
    assert attempt(days(1), days(5)) == 201     # before
    assert attempt(days(20), days(25)) == 201   # after
    assert attempt(days(15), days(16)) == 201   # back-to-back is fine


def test_reservation_other_vehicle_not_blocked(client, make):
    loc, cust, veh = make.base()
    veh2 = make.vehicle()
    make.reservation(cust, veh, loc, days(1), days(3))
    r = client.post("/reservations/", json=make.reservation_body(cust, veh2, loc, days(1), days(3)))
    assert r.status_code == 201


def test_reservation_cancelled_does_not_block(client, make):
    loc, cust, veh = make.base()
    r = make.reservation(cust, veh, loc, days(1), days(3))
    assert client.put(f"/reservations/{r['reservation_id']}", json={"status": "Cancelled"}).status_code == 200
    r2 = client.post("/reservations/", json=make.reservation_body(cust, veh, loc, days(1), days(3)))
    assert r2.status_code == 201


def test_reservation_end_before_start_rejected(client, make):
    loc, cust, veh = make.base()
    r = client.post("/reservations/", json=make.reservation_body(cust, veh, loc, days(5), days(2)))
    assert r.status_code in (400, 422), f"got {r.status_code}"


def test_reservation_blocked_by_active_rental(client, make):
    """A vehicle that is currently out on a rental can't be reserved for the same dates."""
    loc, cust, veh = make.base()
    make.rental(cust, veh, loc, start_date=iso(days(0)), end_date=iso(days(5)))
    r = client.post("/reservations/", json=make.reservation_body(cust, veh, loc, days(1), days(3)))
    assert r.status_code == 400, f"got {r.status_code}"


def test_reservation_unknown_customer_vehicle_is_client_error(client, make):
    loc, cust, veh = make.base()
    body = make.reservation_body(cust, veh, loc, days(1), days(2), customer_id=9999)
    r = client.post("/reservations/", json=body)
    assert r.status_code in (400, 404, 422), f"got {r.status_code}"
    body = make.reservation_body(cust, veh, loc, days(1), days(2), vehicle_id=9999)
    r = client.post("/reservations/", json=body)
    assert r.status_code in (400, 404, 422), f"got {r.status_code}"


def test_reservation_active_list_and_customer_list(client, make):
    loc, cust, veh = make.base()
    cust2 = make.customer()
    a = make.reservation(cust, veh, loc, days(1), days(2))
    b = make.reservation(cust2, veh, loc, days(5), days(6))
    client.put(f"/reservations/{b['reservation_id']}", json={"status": "Cancelled"})
    assert [r["reservation_id"] for r in client.get("/reservations/active").json()] == [a["reservation_id"]]
    assert [r["reservation_id"] for r in client.get(f"/reservations/customer/{cust2['customer_id']}").json()] == [b["reservation_id"]]
    assert client.get("/reservations/customer/9999").json() == []


def test_reservation_update_changing_dates_rechecks_conflicts(client, make):
    loc, cust, veh = make.base()
    make.reservation(cust, veh, loc, days(1), days(3))
    other = make.reservation(cust, veh, loc, days(10), days(12))
    r = client.put(f"/reservations/{other['reservation_id']}",
                   json={"reserved_start_date": iso(days(2)), "reserved_end_date": iso(days(4))})
    assert r.status_code == 400, f"update into an occupied slot returned {r.status_code}"


def test_reservation_update_404(client):
    assert client.put("/reservations/9999", json={"status": "Cancelled"}).status_code == 404


def test_convert_confirmed_reservation_to_rental(client, make):
    loc, cust, veh = make.base()
    res = make.reservation(cust, veh, loc, days(0), days(3))
    client.put(f"/reservations/{res['reservation_id']}", json={"status": "Confirmed"})
    body = make.rental_body(cust, veh, loc)
    r = client.post(f"/reservations/{res['reservation_id']}/convert", json=body)
    assert r.status_code == 200, r.text
    assert client.get(f"/reservations/{res['reservation_id']}").json()["status"] == "Converted"
    assert client.get(f"/vehicles/{veh['vehicle_id']}").json()["availability"] is False
    assert len(client.get("/rentals/").json()) == 1


def test_convert_active_reservation_to_rental(client, make):
    """Reservations are created as 'Active' (and the UI offers no way to 'Confirm'), so converting must work."""
    loc, cust, veh = make.base()
    res = make.reservation(cust, veh, loc, days(0), days(3))
    r = client.post(f"/reservations/{res['reservation_id']}/convert", json=make.rental_body(cust, veh, loc))
    assert r.status_code == 200, f"got {r.status_code}: {r.text[:200]}"


def test_convert_cancelled_or_already_converted_rejected(client, make):
    loc, cust, veh = make.base()
    res = make.reservation(cust, veh, loc, days(0), days(3))
    client.put(f"/reservations/{res['reservation_id']}", json={"status": "Cancelled"})
    assert client.post(f"/reservations/{res['reservation_id']}/convert",
                       json=make.rental_body(cust, veh, loc)).status_code == 400


def test_convert_unknown_reservation(client, make):
    loc, cust, veh = make.base()
    r = client.post("/reservations/9999/convert", json=make.rental_body(cust, veh, loc))
    assert r.status_code in (400, 404)


# =============================================================== rentals
def test_rental_create_marks_vehicle_unavailable(client, make):
    loc, cust, veh = make.base()
    r = make.rental(cust, veh, loc)
    assert r["status"] == "Active"
    assert client.get(f"/vehicles/{veh['vehicle_id']}").json()["availability"] is False
    assert client.get(f"/rentals/{r['rental_id']}").status_code == 200


def test_rental_cannot_double_book_unavailable_vehicle(client, make):
    loc, cust, veh = make.base()
    make.rental(cust, veh, loc)
    r = client.post("/rentals/", json=make.rental_body(cust, veh, loc))
    assert r.status_code == 400, f"vehicle already rented out, but got {r.status_code}"


def test_rental_with_bad_fk_does_not_corrupt_vehicle(client, make):
    loc, cust, veh = make.base()
    body = make.rental_body(cust, veh, loc, customer_id=9999)
    r = client.post("/rentals/", json=body)
    assert r.status_code in (400, 404, 422), f"got {r.status_code}"
    assert client.get(f"/vehicles/{veh['vehicle_id']}").json()["availability"] is True, \
        "vehicle was left unavailable after a failed rental creation"


def test_rental_unknown_vehicle(client, make):
    loc, cust, veh = make.base()
    r = client.post("/rentals/", json=make.rental_body(cust, veh, loc, vehicle_id=9999))
    assert r.status_code in (400, 404, 422), f"got {r.status_code}"


def test_rental_end_before_start_rejected(client, make):
    loc, cust, veh = make.base()
    r = client.post("/rentals/", json=make.rental_body(cust, veh, loc, start_date=iso(days(5)), end_date=iso(days(1))))
    assert r.status_code in (400, 422), f"got {r.status_code}"


def test_rental_detail_includes_relations(client, make):
    loc, cust, veh = make.base()
    emp = make.employee()
    r = make.rental(cust, veh, loc, employee_id=emp["employee_id"])
    body = client.get(f"/rentals/{r['rental_id']}").json()
    assert body["customer"]["customer_id"] == cust["customer_id"]
    assert body["vehicle"]["vehicle_id"] == veh["vehicle_id"]
    assert body["employee"]["employee_id"] == emp["employee_id"]
    assert body["pickup_location"]["location_id"] == loc["location_id"]
    assert body["payments"] == [] and body["incident_reports"] == []
    assert client.get("/rentals/9999").status_code == 404


def test_rental_lists_active_overdue_customer_filter(client, make):
    loc, cust, _ = make.base()
    v1, v2, v3 = make.vehicle(), make.vehicle(), make.vehicle()
    cust2 = make.customer()
    overdue = make.rental(cust, v1, loc, start_date=iso(days(-10)), end_date=iso(days(-5)))
    ok = make.rental(cust, v2, loc)
    done = make.rental(cust2, v3, loc)
    client.patch(f"/rentals/{done['rental_id']}/return", params={"mileage_end": 1100})

    ids = lambda path, **p: sorted(x["rental_id"] for x in client.get(path, params=p).json())  # noqa: E731
    assert ids("/rentals/") == sorted([overdue["rental_id"], ok["rental_id"], done["rental_id"]])
    assert ids("/rentals/active") == sorted([overdue["rental_id"], ok["rental_id"]])
    assert ids("/rentals/overdue") == [overdue["rental_id"]]
    assert ids(f"/rentals/customer/{cust['customer_id']}") == sorted([overdue["rental_id"], ok["rental_id"]])
    assert ids("/rentals/filter/", status="Completed") == [done["rental_id"]]
    assert ids("/rentals/filter/", vehicle_id=v2["vehicle_id"]) == [ok["rental_id"]]
    assert ids("/rentals/filter/", customer_id=cust2["customer_id"]) == [done["rental_id"]]
    assert ids("/rentals/filter/", pickup_location_id=loc["location_id"]) == sorted(
        [overdue["rental_id"], ok["rental_id"], done["rental_id"]])
    assert ids("/rentals/filter/", start_date_from=str(date.today() - timedelta(days=1))) == sorted(
        [ok["rental_id"], done["rental_id"]])
    assert ids("/rentals/filter/", start_date_to=str(date.today() - timedelta(days=6))) == [overdue["rental_id"]]


def test_rental_filter_date_to_is_inclusive_of_that_day(client, make):
    """start_date_to=today should include rentals that start later today."""
    loc, cust, veh = make.base()
    r = make.rental(cust, veh, loc, start_date=iso(datetime.now().replace(hour=15, minute=0, second=0)))
    out = client.get("/rentals/filter/", params={"start_date_to": str(date.today())}).json()
    assert [x["rental_id"] for x in out] == [r["rental_id"]]


# ----------------------------------------------------------- returns
def test_return_with_query_params(client, make):
    loc, cust, veh = make.base()
    r = make.rental(cust, veh, loc)
    out = client.patch(f"/rentals/{r['rental_id']}/return",
                       params={"mileage_end": 1400, "fuel_level_end": 0.5, "late_fees": 12.5, "damage_fees": 30})
    assert out.status_code == 200, out.text
    b = out.json()
    assert b["status"] == "Completed"
    assert b["mileage_end"] == 1400
    assert b["fuel_level_end"] == 0.5
    assert b["late_fees"] == 12.5
    assert b["damage_fees"] == 30.0
    assert b["actual_return_date"] is not None
    v = client.get(f"/vehicles/{veh['vehicle_id']}").json()
    assert v["availability"] is True
    assert v["mileage"] == 1400


def test_return_with_json_body_like_the_frontend_sends(client, make):
    """frontend api.ts -> returnVehicle sends mileage/fuel/fees as a JSON BODY on PATCH."""
    loc, cust, veh = make.base()
    r = make.rental(cust, veh, loc)
    out = client.patch(f"/rentals/{r['rental_id']}/return",
                       json={"mileage_end": 1400, "fuel_level_end": 0.5, "late_fees": 12.5, "damage_fees": 30})
    assert out.status_code == 200, out.text
    b = out.json()
    assert b["mileage_end"] == 1400, "mileage from the body was silently dropped"
    assert b["late_fees"] == 12.5, "late fee from the body was silently dropped"
    assert b["damage_fees"] == 30.0, "damage fee from the body was silently dropped"
    assert client.get(f"/vehicles/{veh['vehicle_id']}").json()["mileage"] == 1400


def test_return_updates_membership_spending_and_points(client, make):
    loc, cust, veh = make.base()
    client.post("/membership/", json={"customer_id": cust["customer_id"]})  # ok if it already exists
    r = make.rental(cust, veh, loc, total_amount="150.00")
    client.patch(f"/rentals/{r['rental_id']}/return", params={"mileage_end": 1100})
    prof = client.get(f"/customers/{cust['customer_id']}").json()["membership_profile"]
    assert prof is not None
    assert prof["lifetime_rentals"] == 1
    assert float(prof["lifetime_spending"]) == 150.00
    assert prof["points_balance"] > 0, "README: return flow should update membership points"


def test_return_spending_includes_fees(client, make):
    loc, cust, veh = make.base()
    client.post("/membership/", json={"customer_id": cust["customer_id"]})
    r = make.rental(cust, veh, loc, total_amount="150.00")
    client.patch(f"/rentals/{r['rental_id']}/return", params={"mileage_end": 1100, "late_fees": 20, "damage_fees": 30})
    prof = client.get(f"/customers/{cust['customer_id']}").json()["membership_profile"]
    assert float(prof["lifetime_spending"]) == 200.00


def test_return_twice_is_rejected(client, make):
    loc, cust, veh = make.base()
    client.post("/membership/", json={"customer_id": cust["customer_id"]})
    r = make.rental(cust, veh, loc)
    assert client.patch(f"/rentals/{r['rental_id']}/return", params={"mileage_end": 1100}).status_code == 200
    again = client.patch(f"/rentals/{r['rental_id']}/return", params={"mileage_end": 1200})
    assert again.status_code == 400, f"returning an already-returned rental gave {again.status_code}"
    prof = client.get(f"/customers/{cust['customer_id']}").json()["membership_profile"]
    assert prof["lifetime_rentals"] == 1


def test_return_404(client):
    assert client.patch("/rentals/9999/return").status_code == 404


def test_return_mileage_lower_than_start_rejected(client, make):
    loc, cust, veh = make.base()
    r = make.rental(cust, veh, loc, mileage_start=1000)
    out = client.patch(f"/rentals/{r['rental_id']}/return", params={"mileage_end": 500})
    assert out.status_code in (400, 422), f"odometer going backwards was accepted ({out.status_code})"


def test_return_zero_mileage_not_treated_as_missing(client, make):
    """`if rental.mileage_end:` is falsy for 0; check we don't clobber vehicle mileage with garbage either way."""
    loc, cust, veh = make.base()
    r = make.rental(cust, veh, loc)
    client.patch(f"/rentals/{r['rental_id']}/return")  # no mileage supplied
    assert client.get(f"/vehicles/{veh['vehicle_id']}").json()["mileage"] == 1000


def test_return_without_membership_profile_does_not_crash(client, make):
    loc, cust, veh = make.base()
    r = make.rental(cust, veh, loc)
    assert client.patch(f"/rentals/{r['rental_id']}/return", params={"mileage_end": 1100}).status_code == 200


def test_return_auto_late_fee_when_overdue_and_none_given(client, make):
    """README: 'calculate late fees if its overdue'. 4 days overdue and no fee supplied => fee > 0."""
    loc, cust, veh = make.base()
    r = make.rental(cust, veh, loc, start_date=iso(days(-10)), end_date=iso(days(-4)))
    out = client.patch(f"/rentals/{r['rental_id']}/return", params={"mileage_end": 1100}).json()
    assert float(out["late_fees"]) > 0


# ----------------------------------------------------------- revenue
def test_revenue_report(client, make):
    loc, cust, _ = make.base()
    v1, v2 = make.vehicle(), make.vehicle()
    a = make.rental(cust, v1, loc, total_amount="100.00", start_date=iso(days(0)))
    b = make.rental(cust, v2, loc, total_amount="250.00", start_date=iso(days(0)))
    client.patch(f"/rentals/{a['rental_id']}/return", params={"mileage_end": 1100})
    r = client.get("/rentals/revenue/report", params={"start_date": str(date.today() - timedelta(days=1)),
                                                      "end_date": str(date.today() + timedelta(days=1))})
    assert r.status_code == 200, r.text
    assert float(r.json()["total_revenue"]) == 100.00  # only completed rentals count
    client.patch(f"/rentals/{b['rental_id']}/return", params={"mileage_end": 1100})
    r = client.get("/rentals/revenue/report", params={"start_date": str(date.today()), "end_date": str(date.today())})
    assert float(r.json()["total_revenue"]) == 350.00, "end_date is inclusive: rentals starting today count"


def test_revenue_report_empty_and_validation(client):
    r = client.get("/rentals/revenue/report", params={"start_date": "2000-01-01", "end_date": "2000-01-02"})
    assert r.status_code == 200 and float(r.json()["total_revenue"]) == 0
    assert client.get("/rentals/revenue/report").status_code == 422


def test_revenue_report_is_number_not_string(client):
    """Frontend type RevenueReport.total_revenue is `number`."""
    r = client.get("/rentals/revenue/report", params={"start_date": "2000-01-01", "end_date": "2000-01-02"})
    assert isinstance(r.json()["total_revenue"], (int, float)), repr(r.json()["total_revenue"])


# =============================================================== payments
def test_payments_flow(client, make):
    loc, cust, veh = make.base()
    rent = make.rental(cust, veh, loc)
    p = client.post("/payments/", json=dict(rental_id=rent["rental_id"], amount="150.00", method="Credit Card",
                                            payment_type="Rental"))
    assert p.status_code == 201, p.text
    assert p.json()["status"] == "Completed"
    client.post("/payments/", json=dict(rental_id=rent["rental_id"], amount="20.00", method="Cash",
                                        payment_type="Late Fee", status="Failed"))
    lst = client.get(f"/payments/rental/{rent['rental_id']}").json()
    assert len(lst) == 2
    assert [x["status"] for x in client.get("/payments/failed").json()] == ["Failed"]
    assert client.get("/payments/rental/9999").json() == []


def test_payment_validation_and_bad_fk(client, make):
    assert client.post("/payments/", json={}).status_code == 422
    r = client.post("/payments/", json=dict(rental_id=9999, amount="1", method="Cash", payment_type="Rental"))
    assert r.status_code in (400, 404, 422), f"got {r.status_code}"


def test_payment_report(client, make):
    loc, cust, veh = make.base()
    rent = make.rental(cust, veh, loc)
    client.post("/payments/", json=dict(rental_id=rent["rental_id"], amount="150.00", method="Cash", payment_type="Rental"))
    client.post("/payments/", json=dict(rental_id=rent["rental_id"], amount="99.00", method="Cash",
                                        payment_type="Rental", status="Failed"))
    r = client.get("/payments/report", params={"start_date": str(date.today() - timedelta(days=1)),
                                               "end_date": str(date.today() + timedelta(days=1))})
    assert r.status_code == 200, f"got {r.status_code}: {r.text[:200]}"
    b = r.json()
    assert b["total_payments"] == 1
    assert float(b["total_amount"]) == 150.00
    assert len(b["payments"]) == 1


# =============================================================== insurance / features / tiers
def test_insurance_plans(client):
    r = client.post("/insurance-plans/", json=dict(name="Basic", daily_cost="9.99", coverage_amount="10000", deductible="500"))
    assert r.status_code == 201
    client.post("/insurance-plans/", json=dict(name="Old", daily_cost="1", coverage_amount="1", deductible="1", is_active=False))
    assert len(client.get("/insurance-plans/").json()) == 2
    assert [p["name"] for p in client.get("/insurance-plans/active").json()] == ["Basic"]
    assert client.post("/insurance-plans/", json={"name": "x"}).status_code == 422


def test_vehicle_features(client):
    r = client.post("/vehicle-features/", json={"name": "Bluetooth", "category": "Entertainment"})
    assert r.status_code == 201
    assert [f["name"] for f in client.get("/vehicle-features/").json()] == ["Bluetooth"]
    assert client.post("/vehicle-features/", json={}).status_code == 422


def test_membership_tiers_list(client):
    r = client.get("/membership-tiers/")
    assert r.status_code == 200
    assert {t["tier_name"] for t in r.json()} == {"Standard", "Premium", "Elite"}


# =============================================================== membership
def test_membership_profile_create(client, make):
    c = make.customer()
    r = client.post("/membership/", json={"customer_id": c["customer_id"], "membership_tier": "Premium"})
    assert r.status_code in (201, 400), r.text
    prof = client.get(f"/customers/{c['customer_id']}").json()["membership_profile"]
    assert prof["membership_tier"] == "Premium" or r.status_code == 400


def test_membership_duplicate_profile_is_client_error(client, make):
    c = make.customer()
    client.post("/membership/", json={"customer_id": c["customer_id"]})
    r = client.post("/membership/", json={"customer_id": c["customer_id"]})
    assert r.status_code == 400, f"got {r.status_code}: {r.text[:100]}"


def test_membership_bad_tier_or_customer_is_client_error(client, make):
    c = make.customer()
    r = client.post("/membership/", json={"customer_id": c["customer_id"], "membership_tier": "Nope"})
    assert r.status_code in (400, 404, 422), f"got {r.status_code}"
    r = client.post("/membership/", json={"customer_id": 9999})
    assert r.status_code in (400, 404, 422), f"got {r.status_code}"


def test_membership_points_query_param(client, make):
    c = make.customer()
    client.post("/membership/", json={"customer_id": c["customer_id"]})
    r = client.patch(f"/membership/{c['customer_id']}/points", params={"points_to_add": 50})
    assert r.status_code == 200, r.text
    assert client.get(f"/customers/{c['customer_id']}").json()["membership_profile"]["points_balance"] == 50
    assert client.patch("/membership/9999/points", params={"points_to_add": 5}).status_code == 404


def test_membership_points_json_body_like_the_frontend_sends(client, make):
    """api.ts -> updatePoints sends {"points_to_add": n} as a JSON body."""
    c = make.customer()
    client.post("/membership/", json={"customer_id": c["customer_id"]})
    r = client.patch(f"/membership/{c['customer_id']}/points", json={"points_to_add": 50})
    assert r.status_code == 200, f"got {r.status_code}: {r.text[:200]}"


# =============================================================== incidents
def test_incident_flow(client, make):
    loc, cust, veh = make.base()
    emp = make.employee()
    rent = make.rental(cust, veh, loc)
    body = dict(rental_id=rent["rental_id"], reported_by=emp["employee_id"], incident_date=iso(NOW),
                incident_type="Damage", description="Scratch on door", estimated_cost="120.00")
    r = client.post("/incidents/", json=body)
    assert r.status_code == 201, r.text
    client.post("/incidents/", json={**body, "status": "Closed"})
    assert len(client.get("/incidents/").json()) == 2
    assert len(client.get(f"/incidents/rental/{rent['rental_id']}").json()) == 2
    assert [i["status"] for i in client.get("/incidents/open").json()] == ["Open"]
    assert client.get("/incidents/rental/9999").json() == []


def test_incident_validation_and_bad_fk(client, make):
    assert client.post("/incidents/", json={}).status_code == 422
    r = client.post("/incidents/", json=dict(rental_id=9999, incident_date=iso(NOW), incident_type="Damage",
                                             description="x"))
    assert r.status_code in (400, 404, 422), f"got {r.status_code}"


def test_incident_appears_on_rental_detail(client, make):
    loc, cust, veh = make.base()
    rent = make.rental(cust, veh, loc)
    client.post("/incidents/", json=dict(rental_id=rent["rental_id"], incident_date=iso(NOW),
                                         incident_type="Accident", description="Bump"))
    assert len(client.get(f"/rentals/{rent['rental_id']}").json()["incident_reports"]) == 1


# =============================================================== maintenance
def test_maintenance_flow(client, make):
    veh = make.vehicle()
    mech = make.employee(role="Mechanic")
    today = date.today()
    mk = lambda **kw: client.post("/maintenance/", json=dict(vehicle_id=veh["vehicle_id"], maintenance_type="Oil Change",  # noqa: E731
                                                              scheduled_date=str(today), **kw))
    a = mk(assigned_mechanic=mech["employee_id"], cost="45.00")
    assert a.status_code == 201, a.text
    b = client.post("/maintenance/", json=dict(vehicle_id=veh["vehicle_id"], maintenance_type="Tires",
                                               scheduled_date=str(today + timedelta(days=30))))
    assert b.status_code == 201
    assert len(client.get(f"/maintenance/vehicle/{veh['vehicle_id']}").json()) == 2
    sched = client.get("/maintenance/scheduled").json()
    assert [m["maintenance_type"] for m in sched] == ["Oil Change"]
    far = client.get("/maintenance/scheduled", params={"target_date": str(today + timedelta(days=60))}).json()
    assert len(far) == 2
    ms = client.get(f"/maintenance/mechanic/{mech['employee_id']}",
                    params={"start_date": str(today - timedelta(days=1)), "end_date": str(today + timedelta(days=1))})
    assert ms.status_code == 200 and len(ms.json()) == 1
    assert client.get(f"/maintenance/mechanic/{mech['employee_id']}").status_code == 422


def test_maintenance_validation_and_bad_fk(client):
    assert client.post("/maintenance/", json={}).status_code == 422
    r = client.post("/maintenance/", json=dict(vehicle_id=9999, maintenance_type="x", scheduled_date="2030-01-01"))
    assert r.status_code in (400, 404, 422), f"got {r.status_code}"


def test_maintenance_scheduled_includes_today_and_overdue_but_not_completed(client, make):
    veh = make.vehicle()
    today = date.today()
    client.post("/maintenance/", json=dict(vehicle_id=veh["vehicle_id"], maintenance_type="Overdue",
                                           scheduled_date=str(today - timedelta(days=3))))
    client.post("/maintenance/", json=dict(vehicle_id=veh["vehicle_id"], maintenance_type="Done",
                                           scheduled_date=str(today), status="Completed"))
    assert [m["maintenance_type"] for m in client.get("/maintenance/scheduled").json()] == ["Overdue"]


# =============================================================== misc / robustness
def test_trailing_slash_collection_routes(client):
    for path in ("/customers", "/vehicles", "/locations", "/employees", "/rentals", "/reservations"):
        r = client.get(path)
        assert r.status_code == 200, f"{path} -> {r.status_code}"


def test_openapi_docs_available(client):
    assert client.get("/openapi.json").status_code == 200
    assert client.get("/docs").status_code == 200


def test_decimal_fields_serialize_as_numbers_for_frontend(client, make):
    """Frontend `Vehicle.daily_rate: number`, `Rental.total_amount: number`... JSON strings break `a + b` math."""
    v = make.vehicle(daily_rate="45.50")
    assert isinstance(v["daily_rate"], (int, float)), f"daily_rate came back as {type(v['daily_rate']).__name__}: {v['daily_rate']!r}"
