import logging
import os
from fastapi import FastAPI, Depends, HTTPException, Query, Body, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, date
from decimal import Decimal

import models as models, schemas as schema, crud as crud
from crud import BusinessRuleError, require
from database import SessionLocal, engine

logger = logging.getLogger("car_rental")

# Create database tables
models.Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title="Car Rental Management System",
    description="A comprehensive car rental management system with customer management, vehicle tracking, reservations, and rentals.",
    version="1.0.0"
)

# NOTE on middleware order: the LAST middleware added is the OUTERMOST one.
# The catch-all below is added first so CORS wraps it => even a 500 carries CORS headers and the browser
# shows the real error instead of an opaque "CORS / network error".
@app.middleware("http")
async def catch_unhandled_errors(request: Request, call_next):
    try:
        return await call_next(request)
    except Exception:  # pragma: no cover - last-resort safety net
        logger.exception("Unhandled error on %s %s", request.method, request.url.path)
        return JSONResponse(status_code=500, content={"detail": "Internal server error"})

# Allowed browser origins:
#   * any localhost / 127.0.0.1 port (Vite falls back to 5174, 5175, ... if 5173 is taken)
#   * every origin listed in ALLOWED_ORIGINS (comma separated), e.g. https://my-app.vercel.app
#   * optionally any *.vercel.app origin (preview deployments) when ALLOW_VERCEL_PREVIEWS=1
ALLOWED_ORIGINS = [o.strip().rstrip("/") for o in os.getenv("ALLOWED_ORIGINS", "").split(",") if o.strip()]
_origin_regex = r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$"
if os.getenv("ALLOW_VERCEL_PREVIEWS") == "1":
    _origin_regex = r"^(https?://(localhost|127\.0\.0\.1)(:\d+)?|https://[a-z0-9-]+\.vercel\.app)$"
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_origin_regex=_origin_regex,
    allow_credentials=True,
    allow_methods=["*"],  # allows GET, POST, PUT, PATCH, DELETE, OPTIONS...
    allow_headers=["*"],  # allows Content-Type, Authorization, etc.
)

# Dependency: get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Exception handlers (all return {"detail": "..."} like HTTPException does, so the frontend sees one shape)
@app.exception_handler(BusinessRuleError)
async def business_rule_handler(request, exc: BusinessRuleError):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})

@app.exception_handler(IntegrityError)
async def integrity_error_handler(request, exc: IntegrityError):
    # PostgreSQL SQLSTATE codes: 23505 unique, 23503 foreign key, 23502 not-null, 23514 check
    code = getattr(getattr(exc, "orig", None), "pgcode", None)
    raw = str(getattr(exc, "orig", exc)).lower()
    if code == "23505" or "duplicate key" in raw:
        msg = "A record with the same unique value already exists"
    elif code == "23503" or "foreign key" in raw:
        msg = "This record references a record that does not exist, or is still referenced by other records"
    elif code == "23502" or "null value" in raw:
        msg = "A required value is missing"
    else:
        msg = "The data conflicts with existing records"
    return JSONResponse(status_code=400, content={"detail": msg})

@app.exception_handler(RequestValidationError)
async def validation_error_handler(request, exc: RequestValidationError):
    parts = []
    for err in exc.errors():
        loc = ".".join(str(p) for p in err.get("loc", []) if p not in ("body", "query", "path"))
        msg = err.get("msg", "invalid value").replace("Value error, ", "")
        parts.append(f"{loc}: {msg}" if loc else msg)
    return JSONResponse(status_code=422, content={"detail": "; ".join(parts) or "Invalid request"})

@app.exception_handler(ValueError)
async def value_error_handler(request, exc):
    return JSONResponse(
        status_code=400,
        content={"detail": str(exc), "message": str(exc)}
    )

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "Welcome to Car Rental Management System API",
        "version": "1.0.0",
        # "docs": "/docs"
    }

# =============================================================================
# DEMO ADMIN
# =============================================================================

@app.post("/admin/reset-demo")
def reset_demo():
    """Wipe EVERYTHING and reload the schema, reference data and demo data (portfolio demo only).

    Disable on a real deployment by setting DEMO_RESET_ENABLED=0.
    """
    if os.getenv("DEMO_RESET_ENABLED", "1") == "0":
        raise HTTPException(status_code=403, detail="Demo reset is disabled")
    from db.demo_reset import reset_demo_data  # local import: only needed here
    engine.dispose()  # drop pooled connections so nothing holds locks on the tables we are about to drop
    conn = engine.raw_connection()
    try:
        reset_demo_data(conn, sample_data=True)
        conn.commit()
    except Exception:
        conn.rollback()
        logger.exception("Demo reset failed")
        raise HTTPException(status_code=500, detail="Demo reset failed")
    finally:
        conn.close()
    return {"detail": "Demo data restored"}

# =============================================================================
# CUSTOMER ENDPOINTS
# =============================================================================

@app.post("/customers/", response_model=schema.Customer, status_code=status.HTTP_201_CREATED)
def create_customer(customer: schema.CustomerCreate, db: Session = Depends(get_db)):
    """Create a new customer (a Standard-tier membership profile is created automatically)"""
    # Check if email already exists
    db_customer = crud.customer.get_by_email(db, email=customer.email)
    if db_customer:
        raise HTTPException(status_code=400, detail="Email already registered")

    # Check if driver license already exists
    db_customer = crud.customer.get_by_driver_license(db, driver_license=customer.driver_license)
    if db_customer:
        raise HTTPException(status_code=400, detail="Driver license already registered")

    new_customer = crud.customer.create(db=db, obj_in=customer)
    crud.membership_profile.ensure_for_customer(db, customer_id=new_customer.customer_id)
    db.refresh(new_customer)
    return new_customer

@app.get("/customers/", response_model=List[schema.Customer])
def read_customers(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """Get all customers with pagination"""
    customers = crud.customer.get_multi(db, skip=skip, limit=limit)
    return customers

# NOTE: static paths (search, top/spending) must be declared BEFORE "/customers/{customer_id}"
@app.get("/customers/search", response_model=List[schema.Customer], include_in_schema=False)
@app.get("/customers/search/", response_model=List[schema.Customer])
def search_customers(
    q: str = Query(..., min_length=1),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """Search customers by name, email, phone or driver license"""
    return crud.customer.search_customers(db, search_term=q, skip=skip, limit=limit)

@app.get("/customers/top/spending", response_model=List[schema.Customer])
def get_top_customers(limit: int = Query(10, ge=1, le=50), db: Session = Depends(get_db)):
    """Get top customers by lifetime spending"""
    return crud.customer.get_top_customers(db, limit=limit)

@app.get("/customers/{customer_id}", response_model=schema.CustomerWithProfile)
def read_customer(customer_id: int, db: Session = Depends(get_db)):
    """Get customer by ID with profile information"""
    db_customer = crud.customer.get_with_profile(db, customer_id=customer_id)
    if db_customer is None:
        raise HTTPException(status_code=404, detail="Customer not found")
    return db_customer

@app.put("/customers/{customer_id}", response_model=schema.Customer)
def update_customer(
    customer_id: int,
    customer: schema.CustomerUpdate,
    db: Session = Depends(get_db)
):
    """Update customer information"""
    db_customer = crud.customer.get(db, id=customer_id)
    if db_customer is None:
        raise HTTPException(status_code=404, detail="Customer not found")
    if customer.email is not None:
        other = crud.customer.get_by_email(db, email=customer.email)
        if other and other.customer_id != customer_id:
            raise HTTPException(status_code=400, detail="Email already registered")
    if customer.driver_license is not None:
        other = crud.customer.get_by_driver_license(db, driver_license=customer.driver_license)
        if other and other.customer_id != customer_id:
            raise HTTPException(status_code=400, detail="Driver license already registered")
    return crud.customer.update(db=db, db_obj=db_customer, obj_in=customer)

@app.delete("/customers/{customer_id}")
def delete_customer(customer_id: int, db: Session = Depends(get_db)):
    """Delete a customer together with their profile, reservations, rentals (and the rentals' payments/incidents).
    Vehicles that are out on one of the customer's active rentals are released first."""
    db_customer = crud.customer.get(db, id=customer_id)
    if db_customer is None:
        raise HTTPException(status_code=404, detail="Customer not found")
    for rental in db_customer.rentals:
        if rental.status == "Active":
            vehicle = db.query(models.Vehicle).filter(models.Vehicle.vehicle_id == rental.vehicle_id).first()
            if vehicle:
                vehicle.availability = True
    db.delete(db_customer)
    db.commit()
    return {"message": "Customer deleted successfully"}

@app.post("/customers/{customer_id}/preferences", response_model=schema.CustomerVehiclePreference,
          status_code=status.HTTP_201_CREATED)
def set_customer_vehicle_preference(customer_id: int, pref: schema.CustomerVehiclePreferenceBase,
                                    db: Session = Depends(get_db)):
    """Add (or update) a vehicle-type preference for a customer"""
    require(db, models.Customer, customer_id, "Customer", 404)
    existing = db.query(models.CustomerVehiclePreference).filter_by(
        customer_id=customer_id, vehicle_type=pref.vehicle_type).first()
    if existing:
        existing.preference_score = pref.preference_score
        db.commit(); db.refresh(existing)
        return existing
    obj = models.CustomerVehiclePreference(customer_id=customer_id, **pref.model_dump())
    db.add(obj); db.commit(); db.refresh(obj)
    return obj

# =============================================================================
# VEHICLE ENDPOINTS
# =============================================================================

@app.post("/vehicles/", response_model=schema.Vehicle, status_code=status.HTTP_201_CREATED)
def create_vehicle(vehicle: schema.VehicleCreate, db: Session = Depends(get_db)):
    """Create a new vehicle"""
    # Check if license plate already exists
    db_vehicle = crud.vehicle.get_by_license_plate(db, license_plate=vehicle.license_plate)
    if db_vehicle:
        raise HTTPException(status_code=400, detail="License plate already exists")
    require(db, models.Location, vehicle.location_id, "Location")
    return crud.vehicle.create(db=db, obj_in=vehicle)

@app.get("/vehicles/", response_model=List[schema.Vehicle])
def read_vehicles(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """Get all vehicles with pagination"""
    return crud.vehicle.get_multi(db, skip=skip, limit=limit)

@app.get("/vehicles/available", response_model=List[schema.Vehicle])
def get_available_vehicles(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """Get all available vehicles"""
    return crud.vehicle.get_available_vehicles(db, skip=skip, limit=limit)

@app.get("/vehicles/filter", response_model=List[schema.Vehicle], include_in_schema=False)
@app.get("/vehicles/filter/", response_model=List[schema.Vehicle])
def filter_vehicles(
    make: Optional[str] = None,
    model: Optional[str] = None,
    fuel_type: Optional[str] = None,
    transmission: Optional[str] = None,
    min_year: Optional[int] = None,
    max_year: Optional[int] = None,
    availability: Optional[bool] = None,
    location_id: Optional[int] = None,
    min_daily_rate: Optional[Decimal] = None,
    max_daily_rate: Optional[Decimal] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """Filter vehicles by various criteria"""
    filters = schema.VehicleFilters(
        make=make,
        model=model,
        fuel_type=fuel_type,
        transmission=transmission,
        min_year=min_year,
        max_year=max_year,
        availability=availability,
        location_id=location_id,
        min_daily_rate=min_daily_rate,
        max_daily_rate=max_daily_rate
    )
    return crud.vehicle.filter_vehicles(db, filters=filters, skip=skip, limit=limit)

@app.get("/vehicles/maintenance/needed", response_model=List[schema.Vehicle])
def get_vehicles_needing_maintenance(db: Session = Depends(get_db)):
    """Get vehicles that need maintenance"""
    return crud.vehicle.get_vehicles_needing_maintenance(db)

@app.get("/vehicles/{vehicle_id}", response_model=schema.VehicleWithFeatures)
def read_vehicle(vehicle_id: int, db: Session = Depends(get_db)):
    """Get vehicle by ID with features and maintenance info"""
    db_vehicle = crud.vehicle.get_with_features(db, vehicle_id=vehicle_id)
    if db_vehicle is None:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    return db_vehicle

@app.put("/vehicles/{vehicle_id}", response_model=schema.Vehicle)
def update_vehicle(
    vehicle_id: int,
    vehicle: schema.VehicleUpdate,
    db: Session = Depends(get_db)
):
    """Update vehicle information"""
    db_vehicle = crud.vehicle.get(db, id=vehicle_id)
    if db_vehicle is None:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    if vehicle.license_plate is not None:
        other = crud.vehicle.get_by_license_plate(db, license_plate=vehicle.license_plate)
        if other and other.vehicle_id != vehicle_id:
            raise HTTPException(status_code=400, detail="License plate already exists")
    if vehicle.location_id is not None:
        require(db, models.Location, vehicle.location_id, "Location")
    return crud.vehicle.update(db=db, db_obj=db_vehicle, obj_in=vehicle)

@app.patch("/vehicles/{vehicle_id}/availability")
def update_vehicle_availability(
    vehicle_id: int,
    available: Optional[bool] = Query(None, description="New availability (query-param form)"),
    body: Optional[schema.VehicleAvailabilityBody] = Body(None),
    db: Session = Depends(get_db)
):
    """Update vehicle availability status. Accepts `{"available": true}` as JSON body (used by the frontend)
    or `?available=true` as query parameter."""
    if body is not None:
        available = body.available
    if available is None:
        raise HTTPException(status_code=422, detail="'available' is required (JSON body or query parameter)")
    db_vehicle = crud.vehicle.update_availability(db, vehicle_id=vehicle_id, available=available)
    if db_vehicle is None:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    return {"message": f"Vehicle availability updated to {available}"}

@app.delete("/vehicles/{vehicle_id}")
def delete_vehicle(vehicle_id: int, db: Session = Depends(get_db)):
    """Delete a vehicle (and its reservations, rentals, maintenance). Refused while it is out on an active rental."""
    db_vehicle = crud.vehicle.get(db, id=vehicle_id)
    if db_vehicle is None:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    if any(r.status == "Active" for r in db_vehicle.rentals):
        raise HTTPException(status_code=400, detail="Vehicle is on an active rental and cannot be deleted")
    db.delete(db_vehicle)
    db.commit()
    return {"message": "Vehicle deleted successfully"}

@app.post("/vehicles/{vehicle_id}/features/{feature_id}", status_code=status.HTTP_201_CREATED)
def add_vehicle_feature(vehicle_id: int, feature_id: int, db: Session = Depends(get_db)):
    """Attach a feature to a vehicle"""
    vehicle = require(db, models.Vehicle, vehicle_id, "Vehicle", 404)
    feature = require(db, models.VehicleFeature, feature_id, "Feature", 404)
    if feature not in vehicle.features:
        vehicle.features.append(feature)
        db.commit()
    return {"message": "Feature attached to vehicle"}

@app.delete("/vehicles/{vehicle_id}/features/{feature_id}")
def remove_vehicle_feature(vehicle_id: int, feature_id: int, db: Session = Depends(get_db)):
    """Detach a feature from a vehicle"""
    vehicle = require(db, models.Vehicle, vehicle_id, "Vehicle", 404)
    feature = require(db, models.VehicleFeature, feature_id, "Feature", 404)
    if feature in vehicle.features:
        vehicle.features.remove(feature)
        db.commit()
    return {"message": "Feature removed from vehicle"}

@app.put("/vehicles/{vehicle_id}/maintenance-record", response_model=schema.VehicleMaintenanceRecord)
def upsert_vehicle_maintenance_record(vehicle_id: int, record: schema.VehicleMaintenanceRecordUpdate,
                                      db: Session = Depends(get_db)):
    """Create or update the long-term maintenance record of a vehicle"""
    require(db, models.Vehicle, vehicle_id, "Vehicle", 404)
    rec = db.query(models.VehicleMaintenanceRecord).filter_by(vehicle_id=vehicle_id).first()
    data = record.model_dump(exclude_unset=True)
    if rec is None:
        rec = models.VehicleMaintenanceRecord(vehicle_id=vehicle_id, **data)
        db.add(rec)
    else:
        for k, v in data.items():
            setattr(rec, k, v)
    db.commit(); db.refresh(rec)
    return rec

# =============================================================================
# RESERVATION ENDPOINTS
# =============================================================================

@app.post("/reservations/", response_model=schema.Reservation, status_code=status.HTTP_201_CREATED)
def create_reservation(reservation: schema.ReservationCreate, db: Session = Depends(get_db)):
    """Create a new reservation (checks references and date conflicts with other reservations and rentals)"""
    return crud.reservation.create_checked(db, obj_in=reservation)

@app.get("/reservations/", response_model=List[schema.Reservation])
def read_reservations(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """Get all reservations"""
    return crud.reservation.get_multi(db, skip=skip, limit=limit)

@app.get("/reservations/active", response_model=List[schema.Reservation])
def get_active_reservations(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """Get active reservations"""
    return crud.reservation.get_active_reservations(db, skip=skip, limit=limit)

@app.get("/reservations/customer/{customer_id}", response_model=List[schema.Reservation])
def get_customer_reservations(customer_id: int, db: Session = Depends(get_db)):
    """Get customer's reservations"""
    return crud.reservation.get_customer_reservations(db, customer_id=customer_id)

@app.get("/reservations/{reservation_id}", response_model=schema.Reservation)
def read_reservation(reservation_id: int, db: Session = Depends(get_db)):
    """Get reservation by ID"""
    db_reservation = crud.reservation.get(db, id=reservation_id)
    if db_reservation is None:
        raise HTTPException(status_code=404, detail="Reservation not found")
    return db_reservation

@app.put("/reservations/{reservation_id}", response_model=schema.Reservation)
def update_reservation(
    reservation_id: int,
    reservation: schema.ReservationUpdate,
    db: Session = Depends(get_db)
):
    """Update reservation (dates/vehicle changes are re-checked for conflicts)"""
    db_reservation = crud.reservation.get(db, id=reservation_id)
    if db_reservation is None:
        raise HTTPException(status_code=404, detail="Reservation not found")
    return crud.reservation.update_checked(db, db_obj=db_reservation, obj_in=reservation)

@app.post("/reservations/{reservation_id}/convert", response_model=schema.Rental)
def convert_reservation_to_rental(
    reservation_id: int,
    rental_data: schema.RentalCreate,
    db: Session = Depends(get_db)
):
    """Convert an Active/Confirmed reservation to a rental"""
    return crud.reservation.convert_to_rental(db, reservation_id=reservation_id, rental_data=rental_data)

# =============================================================================
# RENTAL ENDPOINTS
# =============================================================================

@app.post("/rentals/", response_model=schema.Rental, status_code=status.HTTP_201_CREATED)
def create_rental(rental: schema.RentalCreate, db: Session = Depends(get_db)):
    """Create a new rental. Validates references, refuses vehicles that are not available, and marks the
    vehicle as rented out - all in one transaction."""
    return crud.rental.create_checked(db, obj_in=rental)

@app.get("/rentals/", response_model=List[schema.Rental])
def read_rentals(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """Get all rentals"""
    return crud.rental.get_multi(db, skip=skip, limit=limit)

@app.get("/rentals/active", response_model=List[schema.Rental])
def get_active_rentals(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """Get active rentals"""
    return crud.rental.get_active_rentals(db, skip=skip, limit=limit)

@app.get("/rentals/overdue", response_model=List[schema.Rental])
def get_overdue_rentals(db: Session = Depends(get_db)):
    """Get overdue rentals"""
    return crud.rental.get_overdue_rentals(db)

@app.get("/rentals/filter", response_model=List[schema.Rental], include_in_schema=False)
@app.get("/rentals/filter/", response_model=List[schema.Rental])
def filter_rentals(
    customer_id: Optional[int] = None,
    vehicle_id: Optional[int] = None,
    status: Optional[str] = None,
    start_date_from: Optional[date] = None,
    start_date_to: Optional[date] = None,
    pickup_location_id: Optional[int] = None,
    return_location_id: Optional[int] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """Filter rentals by various criteria (start_date_to is inclusive of that whole day)"""
    filters = schema.RentalFilters(
        customer_id=customer_id,
        vehicle_id=vehicle_id,
        status=status,
        start_date_from=start_date_from,
        start_date_to=start_date_to,
        pickup_location_id=pickup_location_id,
        return_location_id=return_location_id
    )
    return crud.rental.filter_rentals(db, filters=filters, skip=skip, limit=limit)

@app.get("/rentals/revenue/report")
def get_rental_revenue(
    start_date: date = Query(..., description="Start date for revenue report"),
    end_date: date = Query(..., description="End date for revenue report"),
    db: Session = Depends(get_db)
):
    """Get rental revenue (completed rentals, incl. late/damage fees) for a date range, end date inclusive"""
    revenue = crud.rental.get_rental_revenue(db, start_date=start_date, end_date=end_date)
    return {
        "start_date": start_date,
        "end_date": end_date,
        "total_revenue": float(revenue)
    }

@app.get("/rentals/customer/{customer_id}", response_model=List[schema.Rental])
def get_customer_rentals(
    customer_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """Get customer's rental history"""
    return crud.rental.get_customer_rentals(db, customer_id=customer_id, skip=skip, limit=limit)

@app.get("/rentals/{rental_id}", response_model=schema.RentalWithDetails)
def read_rental(rental_id: int, db: Session = Depends(get_db)):
    """Get rental by ID with full details"""
    db_rental = crud.rental.get_with_details(db, rental_id=rental_id)
    if db_rental is None:
        raise HTTPException(status_code=404, detail="Rental not found")
    return db_rental

@app.put("/rentals/{rental_id}", response_model=schema.Rental)
def update_rental(rental_id: int, rental: schema.RentalUpdate, db: Session = Depends(get_db)):
    """Update rental details (use the /return endpoint to complete a rental)"""
    db_rental = crud.rental.get(db, id=rental_id)
    if db_rental is None:
        raise HTTPException(status_code=404, detail="Rental not found")
    changes = rental.model_dump(exclude_unset=True)
    start = changes.get("start_date", db_rental.start_date)
    end = changes.get("end_date", db_rental.end_date)
    if end <= start:
        raise BusinessRuleError("end_date must be after start_date")
    require(db, models.Employee, changes.get("employee_id"), "Employee")
    require(db, models.Location, changes.get("pickup_location_id"), "Pickup location")
    require(db, models.Location, changes.get("return_location_id"), "Return location")
    return crud.rental.update(db=db, db_obj=db_rental, obj_in=rental)

@app.post("/rentals/{rental_id}/insurance/{plan_id}", response_model=schema.RentalInsurance,
          status_code=status.HTTP_201_CREATED)
def add_rental_insurance(rental_id: int, plan_id: int, db: Session = Depends(get_db)):
    """Attach an insurance plan to a rental. Coverage dates follow the rental; premium = daily cost x rental days."""
    rental = require(db, models.Rental, rental_id, "Rental", 404)
    plan = require(db, models.InsurancePlan, plan_id, "Insurance plan", 404)
    existing = db.query(models.RentalInsurance).filter_by(rental_id=rental_id, plan_id=plan_id).first()
    if existing:
        return existing
    days = max((rental.end_date.date() - rental.start_date.date()).days, 1)
    link = models.RentalInsurance(
        rental_id=rental_id, plan_id=plan_id,
        start_date=rental.start_date.date(), end_date=rental.end_date.date(),
        premium_amount=crud.money(Decimal(str(plan.daily_cost)) * days))
    db.add(link)
    db.commit()
    db.refresh(link)
    return link

@app.patch("/rentals/{rental_id}/return", response_model=schema.Rental)
def return_rental_vehicle(
    rental_id: int,
    mileage_end: Optional[int] = Query(None, ge=0),
    fuel_level_end: Optional[Decimal] = Query(None, ge=0),
    late_fees: Optional[Decimal] = Query(None, ge=0),
    damage_fees: Optional[Decimal] = Query(None, ge=0),
    body: Optional[schema.RentalReturnBody] = Body(None),
    db: Session = Depends(get_db)
):
    """Return a rental vehicle. Return details can be sent as JSON body (used by the frontend) or query params.
    If no late fee is supplied and the rental is overdue, it is calculated (50% of the daily rate per late day).
    Frees the vehicle, updates its odometer and credits the customer's lifetime spending/points."""
    data = {
        "mileage_end": mileage_end, "fuel_level_end": fuel_level_end,
        "late_fees": late_fees, "damage_fees": damage_fees, "actual_return_date": None,
    }
    if body is not None:
        data.update({k: v for k, v in body.model_dump().items() if v is not None})
    rental = crud.rental.return_vehicle(db, rental_id=rental_id, return_data=data)
    if rental is None:
        raise HTTPException(status_code=404, detail="Rental not found")
    return rental

# =============================================================================
# EMPLOYEE ENDPOINTS
# =============================================================================

@app.post("/employees/", response_model=schema.Employee, status_code=status.HTTP_201_CREATED)
def create_employee(employee: schema.EmployeeCreate, db: Session = Depends(get_db)):
    """Create a new employee"""
    # Check if email already exists
    db_employee = crud.employee.get_by_email(db, email=employee.email)
    if db_employee:
        raise HTTPException(status_code=400, detail="Email already registered")
    require(db, models.Location, employee.location_id, "Location")
    require(db, models.Employee, employee.manager_id, "Manager")
    return crud.employee.create(db=db, obj_in=employee)

@app.get("/employees/", response_model=List[schema.Employee])
def read_employees(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """Get all employees"""
    return crud.employee.get_multi(db, skip=skip, limit=limit)

@app.get("/employees/active", response_model=List[schema.Employee])
def get_active_employees(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """Get active employees"""
    return crud.employee.get_active_employees(db, skip=skip, limit=limit)

@app.get("/employees/role/{role}", response_model=List[schema.Employee])
def get_employees_by_role(role: str, db: Session = Depends(get_db)):
    """Get employees by role"""
    return crud.employee.get_by_role(db, role=role)

@app.get("/employees/location/{location_id}", response_model=List[schema.Employee])
def get_employees_by_location(location_id: int, db: Session = Depends(get_db)):
    """Get employees by location"""
    return crud.employee.get_by_location(db, location_id=location_id)

@app.get("/employees/{employee_id}", response_model=schema.Employee)
def read_employee(employee_id: int, db: Session = Depends(get_db)):
    """Get employee by ID"""
    db_employee = crud.employee.get(db, id=employee_id)
    if db_employee is None:
        raise HTTPException(status_code=404, detail="Employee not found")
    return db_employee

@app.put("/employees/{employee_id}", response_model=schema.Employee)
def update_employee(employee_id: int, employee: schema.EmployeeUpdate, db: Session = Depends(get_db)):
    """Update an employee"""
    db_employee = crud.employee.get(db, id=employee_id)
    if db_employee is None:
        raise HTTPException(status_code=404, detail="Employee not found")
    if employee.email is not None:
        other = crud.employee.get_by_email(db, email=employee.email)
        if other and other.employee_id != employee_id:
            raise HTTPException(status_code=400, detail="Email already registered")
    if employee.manager_id == employee_id:
        raise HTTPException(status_code=400, detail="An employee cannot be their own manager")
    require(db, models.Location, employee.location_id, "Location")
    require(db, models.Employee, employee.manager_id, "Manager")
    return crud.employee.update(db=db, db_obj=db_employee, obj_in=employee)

@app.delete("/employees/{employee_id}")
def delete_employee(employee_id: int, db: Session = Depends(get_db)):
    """Delete an employee (rentals/incidents/maintenance they were linked to simply lose the link)"""
    db_employee = crud.employee.get(db, id=employee_id)
    if db_employee is None:
        raise HTTPException(status_code=404, detail="Employee not found")
    db.delete(db_employee)
    db.commit()
    return {"message": "Employee deleted successfully"}

# =============================================================================
# LOCATION ENDPOINTS
# =============================================================================

@app.post("/locations/", response_model=schema.Location, status_code=status.HTTP_201_CREATED)
def create_location(location: schema.LocationCreate, db: Session = Depends(get_db)):
    """Create a new location"""
    require(db, models.Employee, location.manager_id, "Manager")
    return crud.location.create(db=db, obj_in=location)

@app.get("/locations/", response_model=List[schema.Location])
def read_locations(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """Get all locations"""
    return crud.location.get_multi(db, skip=skip, limit=limit)

@app.get("/locations/city/{city}", response_model=List[schema.Location])
def get_locations_by_city(city: str, db: Session = Depends(get_db)):
    """Get locations by city"""
    return crud.location.get_by_city(db, city=city)

@app.get("/locations/{location_id}", response_model=schema.LocationWithEmployees)
def read_location(location_id: int, db: Session = Depends(get_db)):
    """Get location by ID with employees and vehicles"""
    db_location = crud.location.get_with_details(db, location_id=location_id)
    if db_location is None:
        raise HTTPException(status_code=404, detail="Location not found")
    return db_location

@app.put("/locations/{location_id}", response_model=schema.Location)
def update_location(location_id: int, location: schema.LocationUpdate, db: Session = Depends(get_db)):
    """Update a location"""
    db_location = crud.location.get(db, id=location_id)
    if db_location is None:
        raise HTTPException(status_code=404, detail="Location not found")
    require(db, models.Employee, location.manager_id, "Manager")
    return crud.location.update(db=db, db_obj=db_location, obj_in=location)

@app.delete("/locations/{location_id}")
def delete_location(location_id: int, db: Session = Depends(get_db)):
    """Delete a location. Refused while reservations or rentals still use it as pickup/return point."""
    db_location = crud.location.get(db, id=location_id)
    if db_location is None:
        raise HTTPException(status_code=404, detail="Location not found")
    in_use = (
        db.query(models.Rental).filter(or_(models.Rental.pickup_location_id == location_id,
                                           models.Rental.return_location_id == location_id)).first()
        or db.query(models.Reservation).filter(or_(models.Reservation.pickup_location_id == location_id,
                                                   models.Reservation.return_location_id == location_id)).first()
    )
    if in_use:
        raise HTTPException(status_code=400, detail="Location is used by existing rentals/reservations and cannot be deleted")
    db.delete(db_location)
    db.commit()
    return {"message": "Location deleted successfully"}

# =============================================================================
# PAYMENT ENDPOINTS
# =============================================================================

@app.post("/payments/", response_model=schema.Payment, status_code=status.HTTP_201_CREATED)
def create_payment(payment: schema.PaymentCreate, db: Session = Depends(get_db)):
    """Create a new payment"""
    require(db, models.Rental, payment.rental_id, "Rental", 404)
    return crud.payment.create(db=db, obj_in=payment)

@app.get("/payments/rental/{rental_id}", response_model=List[schema.Payment])
def get_rental_payments(rental_id: int, db: Session = Depends(get_db)):
    """Get payments for a rental"""
    return crud.payment.get_rental_payments(db, rental_id=rental_id)

@app.get("/payments/failed", response_model=List[schema.Payment])
def get_failed_payments(db: Session = Depends(get_db)):
    """Get failed payments"""
    return crud.payment.get_failed_payments(db)

@app.get("/payments/report")
def get_payments_report(
    start_date: date = Query(..., description="Start date for payments report"),
    end_date: date = Query(..., description="End date for payments report"),
    db: Session = Depends(get_db)
):
    """Get payments report for a date range"""
    payments = crud.payment.get_payments_by_date_range(db, start_date=start_date, end_date=end_date)
    total_amount = sum((payment.amount for payment in payments), Decimal("0.00"))
    return {
        "start_date": start_date,
        "end_date": end_date,
        "total_payments": len(payments),
        "total_amount": float(total_amount),
        "payments": [schema.Payment.model_validate(p).model_dump(mode="json") for p in payments]
    }

@app.put("/payments/{payment_id}", response_model=schema.Payment)
def update_payment(payment_id: int, payment: schema.PaymentUpdate, db: Session = Depends(get_db)):
    """Update a payment (e.g. mark a failed payment as completed)"""
    db_payment = crud.payment.get(db, id=payment_id)
    if db_payment is None:
        raise HTTPException(status_code=404, detail="Payment not found")
    return crud.payment.update(db=db, db_obj=db_payment, obj_in=payment)

# =============================================================================
# INSURANCE ENDPOINTS
# =============================================================================

@app.post("/insurance-plans/", response_model=schema.InsurancePlan, status_code=status.HTTP_201_CREATED)
def create_insurance_plan(plan: schema.InsurancePlanCreate, db: Session = Depends(get_db)):
    """Create a new insurance plan"""
    return crud.insurance_plan.create(db=db, obj_in=plan)

@app.get("/insurance-plans/", response_model=List[schema.InsurancePlan])
def read_insurance_plans(db: Session = Depends(get_db)):
    """Get all insurance plans"""
    return crud.insurance_plan.get_multi(db)

@app.get("/insurance-plans/active", response_model=List[schema.InsurancePlan])
def get_active_insurance_plans(db: Session = Depends(get_db)):
    """Get active insurance plans"""
    return crud.insurance_plan.get_active_plans(db)

@app.put("/insurance-plans/{plan_id}", response_model=schema.InsurancePlan)
def update_insurance_plan(plan_id: int, plan: schema.InsurancePlanUpdate, db: Session = Depends(get_db)):
    """Update an insurance plan"""
    db_plan = crud.insurance_plan.get(db, id=plan_id)
    if db_plan is None:
        raise HTTPException(status_code=404, detail="Insurance plan not found")
    return crud.insurance_plan.update(db=db, db_obj=db_plan, obj_in=plan)

# =============================================================================
# INCIDENT REPORT ENDPOINTS
# =============================================================================

@app.post("/incidents/", response_model=schema.IncidentReport, status_code=status.HTTP_201_CREATED)
def create_incident_report(incident: schema.IncidentReportCreate, db: Session = Depends(get_db)):
    """Create a new incident report"""
    require(db, models.Rental, incident.rental_id, "Rental", 404)
    require(db, models.Employee, incident.reported_by, "Employee")
    return crud.incident_report.create(db=db, obj_in=incident)

@app.get("/incidents/", response_model=List[schema.IncidentReport])
def read_incident_reports(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """Get all incident reports"""
    return crud.incident_report.get_multi(db, skip=skip, limit=limit)

@app.get("/incidents/open", response_model=List[schema.IncidentReport])
def get_open_incidents(db: Session = Depends(get_db)):
    """Get open incident reports"""
    return crud.incident_report.get_open_incidents(db)

@app.get("/incidents/rental/{rental_id}", response_model=List[schema.IncidentReport])
def get_rental_incidents(rental_id: int, db: Session = Depends(get_db)):
    """Get incidents for a rental"""
    return crud.incident_report.get_rental_incidents(db, rental_id=rental_id)

@app.put("/incidents/{incident_id}", response_model=schema.IncidentReport)
def update_incident_report(incident_id: int, incident: schema.IncidentReportUpdate, db: Session = Depends(get_db)):
    """Update an incident report (status, cost, resolution, ...)"""
    db_incident = crud.incident_report.get(db, id=incident_id)
    if db_incident is None:
        raise HTTPException(status_code=404, detail="Incident report not found")
    return crud.incident_report.update(db=db, db_obj=db_incident, obj_in=incident)

# =============================================================================
# MAINTENANCE ENDPOINTS
# =============================================================================

@app.post("/maintenance/", response_model=schema.MaintenanceSchedule, status_code=status.HTTP_201_CREATED)
def create_maintenance_schedule(maintenance: schema.MaintenanceScheduleCreate, db: Session = Depends(get_db)):
    """Create a new maintenance schedule"""
    require(db, models.Vehicle, maintenance.vehicle_id, "Vehicle", 404)
    require(db, models.Employee, maintenance.assigned_mechanic, "Mechanic")
    return crud.maintenance_schedule.create(db=db, obj_in=maintenance)

@app.get("/maintenance/", response_model=List[schema.MaintenanceSchedule])
def read_maintenance_schedules(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """Get ALL maintenance entries (any status), newest scheduled date first"""
    return crud.maintenance_schedule.get_all_ordered(db, skip=skip, limit=limit)

@app.get("/maintenance/vehicle/{vehicle_id}", response_model=List[schema.MaintenanceSchedule])
def get_vehicle_maintenance(vehicle_id: int, db: Session = Depends(get_db)):
    """Get maintenance schedule for a vehicle"""
    return crud.maintenance_schedule.get_vehicle_maintenance(db, vehicle_id=vehicle_id)

@app.get("/maintenance/scheduled", response_model=List[schema.MaintenanceSchedule])
def get_scheduled_maintenance(
    target_date: Optional[date] = Query(None, description="Target date (defaults to today)"),
    db: Session = Depends(get_db)
):
    """Get scheduled maintenance for a specific date"""
    return crud.maintenance_schedule.get_scheduled_maintenance(db, target_date=target_date)

@app.get("/maintenance/mechanic/{mechanic_id}", response_model=List[schema.MaintenanceSchedule])
def get_mechanic_schedule(
    mechanic_id: int,
    start_date: date = Query(..., description="Start date for schedule"),
    end_date: date = Query(..., description="End date for schedule"),
    db: Session = Depends(get_db)
):
    """Get maintenance schedule for a mechanic"""
    return crud.maintenance_schedule.get_mechanic_schedule(
        db, mechanic_id=mechanic_id, start_date=start_date, end_date=end_date
    )

@app.put("/maintenance/{maintenance_id}", response_model=schema.MaintenanceSchedule)
def update_maintenance_schedule(maintenance_id: int, maintenance: schema.MaintenanceScheduleUpdate,
                                db: Session = Depends(get_db)):
    """Update a maintenance entry (e.g. mark it Completed)"""
    db_item = crud.maintenance_schedule.get(db, id=maintenance_id)
    if db_item is None:
        raise HTTPException(status_code=404, detail="Maintenance entry not found")
    require(db, models.Employee, maintenance.assigned_mechanic, "Mechanic")
    return crud.maintenance_schedule.update(db=db, db_obj=db_item, obj_in=maintenance)

# =============================================================================
# MEMBERSHIP ENDPOINTS
# =============================================================================

@app.post("/membership/", response_model=schema.CustomerMembershipProfile, status_code=status.HTTP_201_CREATED)
def create_membership_profile(profile: schema.CustomerMembershipProfileCreate, db: Session = Depends(get_db)):
    """Create a customer membership profile (new customers already get one automatically)"""
    return crud.membership_profile.create_checked(db, obj_in=profile)

@app.put("/membership/{customer_id}", response_model=schema.CustomerMembershipProfile)
def update_membership_profile(customer_id: int, profile: schema.CustomerMembershipProfileUpdate,
                              db: Session = Depends(get_db)):
    """Update a customer's membership profile (e.g. change tier)"""
    require(db, models.Customer, customer_id, "Customer", 404)
    db_profile = crud.membership_profile.ensure_for_customer(db, customer_id=customer_id)
    if profile.membership_tier is not None:
        crud.membership_profile.ensure_tier(db, profile.membership_tier)
    return crud.membership_profile.update(db=db, db_obj=db_profile, obj_in=profile)

@app.patch("/membership/{customer_id}/points")
def update_customer_points(
    customer_id: int,
    points_to_add: Optional[int] = Query(None, description="Points to add (query-param form)"),
    body: Optional[schema.PointsBody] = Body(None),
    db: Session = Depends(get_db)
):
    """Update customer points balance. Accepts `{"points_to_add": 50}` as JSON body (used by the frontend)
    or `?points_to_add=50` as query parameter."""
    if body is not None:
        points_to_add = body.points_to_add
    if points_to_add is None:
        raise HTTPException(status_code=422, detail="'points_to_add' is required (JSON body or query parameter)")
    profile = crud.membership_profile.update_points(db, customer_id=customer_id, points_to_add=points_to_add)
    if profile is None:
        raise HTTPException(status_code=404, detail="Customer not found")
    return {"message": f"Added {points_to_add} points to customer {customer_id}", "points_balance": profile.points_balance}

@app.get("/membership-tiers/", response_model=List[schema.MembershipTier])
def get_membership_tiers(db: Session = Depends(get_db)):
    """Get all membership tiers"""
    return crud.membership_tier.get_multi(db)

# =============================================================================
# VEHICLE FEATURES ENDPOINTS
# =============================================================================

@app.post("/vehicle-features/", response_model=schema.VehicleFeature, status_code=status.HTTP_201_CREATED)
def create_vehicle_feature(feature: schema.VehicleFeatureCreate, db: Session = Depends(get_db)):
    """Create a new vehicle feature"""
    return crud.vehicle_feature.create(db=db, obj_in=feature)

@app.get("/vehicle-features/", response_model=List[schema.VehicleFeature])
def read_vehicle_features(db: Session = Depends(get_db)):
    """Get all vehicle features"""
    return crud.vehicle_feature.get_multi(db)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
