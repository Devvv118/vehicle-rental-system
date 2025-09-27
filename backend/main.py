from fastapi import FastAPI, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, date
from decimal import Decimal

import models as models, schemas as schema, crud as crud
from database import SessionLocal, engine

# Create database tables
models.Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title="Car Rental Management System",
    description="A comprehensive car rental management system with customer management, vehicle tracking, reservations, and rentals.",
    version="1.0.0"
)

origins = [
    "http://localhost:5173",  # your Vite React dev server
    # add more allowed origins if needed
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
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

# Exception handlers
@app.exception_handler(ValueError)
async def value_error_handler(request, exc):
    return JSONResponse(
        status_code=400,
        content={"message": str(exc)}
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
# CUSTOMER ENDPOINTS
# =============================================================================

@app.post("/customers/", response_model=schema.Customer, status_code=status.HTTP_201_CREATED)
def create_customer(customer: schema.CustomerCreate, db: Session = Depends(get_db)):
    """Create a new customer"""
    # Check if email already exists
    db_customer = crud.customer.get_by_email(db, email=customer.email)
    if db_customer:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Check if driver license already exists
    db_customer = crud.customer.get_by_driver_license(db, driver_license=customer.driver_license)
    if db_customer:
        raise HTTPException(status_code=400, detail="Driver license already registered")
    
    return crud.customer.create(db=db, obj_in=customer)

@app.get("/customers/", response_model=List[schema.Customer])
def read_customers(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get all customers with pagination"""
    customers = crud.customer.get_multi(db, skip=skip, limit=limit)
    return customers

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
    
    return crud.customer.update(db=db, db_obj=db_customer, obj_in=customer)

@app.delete("/customers/{customer_id}")
def delete_customer(customer_id: int, db: Session = Depends(get_db)):
    """Delete a customer"""
    db_customer = crud.customer.delete(db=db, id=customer_id)
    if db_customer is None:
        raise HTTPException(status_code=404, detail="Customer not found")
    return {"message": "Customer deleted successfully"}

@app.get("/customers/search/", response_model=List[schema.Customer])
def search_customers(
    q: str = Query(..., min_length=1),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Search customers by name, email, or phone"""
    return crud.customer.search_customers(db, search_term=q, skip=skip, limit=limit)

@app.get("/customers/top/spending", response_model=List[schema.Customer])
def get_top_customers(limit: int = Query(10, ge=1, le=50), db: Session = Depends(get_db)):
    """Get top customers by lifetime spending"""
    return crud.customer.get_top_customers(db, limit=limit)

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
    
    return crud.vehicle.create(db=db, obj_in=vehicle)

@app.get("/vehicles/", response_model=List[schema.Vehicle])
def read_vehicles(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get all vehicles with pagination"""
    return crud.vehicle.get_multi(db, skip=skip, limit=limit)

@app.get("/vehicles/available", response_model=List[schema.Vehicle])
def get_available_vehicles(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get all available vehicles"""
    return crud.vehicle.get_available_vehicles(db, skip=skip, limit=limit)

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
    
    return crud.vehicle.update(db=db, db_obj=db_vehicle, obj_in=vehicle)

@app.patch("/vehicles/{vehicle_id}/availability")
def update_vehicle_availability(
    vehicle_id: int,
    available: bool,
    db: Session = Depends(get_db)
):
    """Update vehicle availability status"""
    db_vehicle = crud.vehicle.update_availability(db, vehicle_id=vehicle_id, available=available)
    if db_vehicle is None:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    return {"message": f"Vehicle availability updated to {available}"}

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
    limit: int = Query(100, ge=1, le=100),
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

# =============================================================================
# RESERVATION ENDPOINTS
# =============================================================================

@app.post("/reservations/", response_model=schema.Reservation, status_code=status.HTTP_201_CREATED)
def create_reservation(reservation: schema.ReservationCreate, db: Session = Depends(get_db)):
    """Create a new reservation"""
    # Check vehicle availability
    is_available = crud.reservation.check_vehicle_availability(
        db,
        vehicle_id=reservation.vehicle_id,
        start_date=reservation.reserved_start_date,
        end_date=reservation.reserved_end_date
    )
    if not is_available:
        raise HTTPException(status_code=400, detail="Vehicle is not available for the selected dates")
    
    return crud.reservation.create(db=db, obj_in=reservation)

@app.get("/reservations/", response_model=List[schema.Reservation])
def read_reservations(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get all reservations"""
    return crud.reservation.get_multi(db, skip=skip, limit=limit)

@app.get("/reservations/active", response_model=List[schema.Reservation])
def get_active_reservations(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get active reservations"""
    return crud.reservation.get_active_reservations(db, skip=skip, limit=limit)

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
    """Update reservation"""
    db_reservation = crud.reservation.get(db, id=reservation_id)
    if db_reservation is None:
        raise HTTPException(status_code=404, detail="Reservation not found")
    
    return crud.reservation.update(db=db, db_obj=db_reservation, obj_in=reservation)

@app.get("/reservations/customer/{customer_id}", response_model=List[schema.Reservation])
def get_customer_reservations(customer_id: int, db: Session = Depends(get_db)):
    """Get customer's reservations"""
    return crud.reservation.get_customer_reservations(db, customer_id=customer_id)

@app.post("/reservations/{reservation_id}/convert", response_model=schema.Rental)
def convert_reservation_to_rental(
    reservation_id: int,
    rental_data: schema.RentalCreate,
    db: Session = Depends(get_db)
):
    """Convert a reservation to a rental"""
    rental = crud.reservation.convert_to_rental(db, reservation_id=reservation_id, rental_data=rental_data)
    if rental is None:
        raise HTTPException(status_code=400, detail="Cannot convert reservation to rental")
    return rental

# =============================================================================
# RENTAL ENDPOINTS
# =============================================================================

@app.post("/rentals/", response_model=schema.Rental, status_code=status.HTTP_201_CREATED)
def create_rental(rental: schema.RentalCreate, db: Session = Depends(get_db)):
    """Create a new rental"""
    # Update vehicle availability
    crud.vehicle.update_availability(db, vehicle_id=rental.vehicle_id, available=False)
    return crud.rental.create(db=db, obj_in=rental)

@app.get("/rentals/", response_model=List[schema.Rental])
def read_rentals(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get all rentals"""
    return crud.rental.get_multi(db, skip=skip, limit=limit)

@app.get("/rentals/active", response_model=List[schema.Rental])
def get_active_rentals(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get active rentals"""
    return crud.rental.get_active_rentals(db, skip=skip, limit=limit)

@app.get("/rentals/overdue", response_model=List[schema.Rental])
def get_overdue_rentals(db: Session = Depends(get_db)):
    """Get overdue rentals"""
    return crud.rental.get_overdue_rentals(db)

@app.get("/rentals/{rental_id}", response_model=schema.RentalWithDetails)
def read_rental(rental_id: int, db: Session = Depends(get_db)):
    """Get rental by ID with full details"""
    db_rental = crud.rental.get_with_details(db, rental_id=rental_id)
    if db_rental is None:
        raise HTTPException(status_code=404, detail="Rental not found")
    return db_rental

@app.get("/rentals/customer/{customer_id}", response_model=List[schema.Rental])
def get_customer_rentals(
    customer_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get customer's rental history"""
    return crud.rental.get_customer_rentals(db, customer_id=customer_id, skip=skip, limit=limit)

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
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Filter rentals by various criteria"""
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

@app.patch("/rentals/{rental_id}/return", response_model=schema.Rental)
def return_rental_vehicle(
    rental_id: int,
    mileage_end: Optional[int] = None,
    fuel_level_end: Optional[Decimal] = None,
    late_fees: Optional[Decimal] = None,
    damage_fees: Optional[Decimal] = None,
    db: Session = Depends(get_db)
):
    """Return a rental vehicle"""
    return_data = {
        "actual_return_date": datetime.now(),
        "mileage_end": mileage_end,
        "fuel_level_end": fuel_level_end,
        "late_fees": late_fees or Decimal('0.00'),
        "damage_fees": damage_fees or Decimal('0.00')
    }
    
    rental = crud.rental.return_vehicle(db, rental_id=rental_id, return_data=return_data)
    if rental is None:
        raise HTTPException(status_code=404, detail="Rental not found")
    
    # Update customer membership spending
    crud.membership_profile.update_spending(db, customer_id=rental.customer_id, amount=rental.total_amount)
    
    return rental

@app.get("/rentals/revenue/report")
def get_rental_revenue(
    start_date: date = Query(..., description="Start date for revenue report"),
    end_date: date = Query(..., description="End date for revenue report"),
    db: Session = Depends(get_db)
):
    """Get rental revenue for a date range"""
    revenue = crud.rental.get_rental_revenue(db, start_date=start_date, end_date=end_date)
    return {
        "start_date": start_date,
        "end_date": end_date,
        "total_revenue": revenue
    }

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
    
    return crud.employee.create(db=db, obj_in=employee)

@app.get("/employees/", response_model=List[schema.Employee])
def read_employees(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get all employees"""
    return crud.employee.get_multi(db, skip=skip, limit=limit)

@app.get("/employees/active", response_model=List[schema.Employee])
def get_active_employees(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get active employees"""
    return crud.employee.get_active_employees(db, skip=skip, limit=limit)

@app.get("/employees/{employee_id}", response_model=schema.Employee)
def read_employee(employee_id: int, db: Session = Depends(get_db)):
    """Get employee by ID"""
    db_employee = crud.employee.get(db, id=employee_id)
    if db_employee is None:
        raise HTTPException(status_code=404, detail="Employee not found")
    return db_employee

@app.get("/employees/role/{role}", response_model=List[schema.Employee])
def get_employees_by_role(role: str, db: Session = Depends(get_db)):
    """Get employees by role"""
    return crud.employee.get_by_role(db, role=role)

@app.get("/employees/location/{location_id}", response_model=List[schema.Employee])
def get_employees_by_location(location_id: int, db: Session = Depends(get_db)):
    """Get employees by location"""
    return crud.employee.get_by_location(db, location_id=location_id)

# =============================================================================
# LOCATION ENDPOINTS
# =============================================================================

@app.post("/locations/", response_model=schema.Location, status_code=status.HTTP_201_CREATED)
def create_location(location: schema.LocationCreate, db: Session = Depends(get_db)):
    """Create a new location"""
    return crud.location.create(db=db, obj_in=location)

@app.get("/locations/", response_model=List[schema.Location])
def read_locations(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get all locations"""
    return crud.location.get_multi(db, skip=skip, limit=limit)

@app.get("/locations/{location_id}", response_model=schema.LocationWithEmployees)
def read_location(location_id: int, db: Session = Depends(get_db)):
    """Get location by ID with employees and vehicles"""
    db_location = crud.location.get_with_details(db, location_id=location_id)
    if db_location is None:
        raise HTTPException(status_code=404, detail="Location not found")
    return db_location

@app.get("/locations/city/{city}", response_model=List[schema.Location])
def get_locations_by_city(city: str, db: Session = Depends(get_db)):
    """Get locations by city"""
    return crud.location.get_by_city(db, city=city)

# =============================================================================
# PAYMENT ENDPOINTS
# =============================================================================

@app.post("/payments/", response_model=schema.Payment, status_code=status.HTTP_201_CREATED)
def create_payment(payment: schema.PaymentCreate, db: Session = Depends(get_db)):
    """Create a new payment"""
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
    total_amount = sum(payment.amount for payment in payments)
    return {
        "start_date": start_date,
        "end_date": end_date,
        "total_payments": len(payments),
        "total_amount": total_amount,
        "payments": payments
    }

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

# =============================================================================
# INCIDENT REPORT ENDPOINTS
# =============================================================================

@app.post("/incidents/", response_model=schema.IncidentReport, status_code=status.HTTP_201_CREATED)
def create_incident_report(incident: schema.IncidentReportCreate, db: Session = Depends(get_db)):
    """Create a new incident report"""
    return crud.incident_report.create(db=db, obj_in=incident)

@app.get("/incidents/", response_model=List[schema.IncidentReport])
def read_incident_reports(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get all incident reports"""
    return crud.incident_report.get_multi(db, skip=skip, limit=limit)

@app.get("/incidents/rental/{rental_id}", response_model=List[schema.IncidentReport])
def get_rental_incidents(rental_id: int, db: Session = Depends(get_db)):
    """Get incidents for a rental"""
    return crud.incident_report.get_rental_incidents(db, rental_id=rental_id)

@app.get("/incidents/open", response_model=List[schema.IncidentReport])
def get_open_incidents(db: Session = Depends(get_db)):
    """Get open incident reports"""
    return crud.incident_report.get_open_incidents(db)

# =============================================================================
# MAINTENANCE ENDPOINTS
# =============================================================================

@app.post("/maintenance/", response_model=schema.MaintenanceSchedule, status_code=status.HTTP_201_CREATED)
def create_maintenance_schedule(maintenance: schema.MaintenanceScheduleCreate, db: Session = Depends(get_db)):
    """Create a new maintenance schedule"""
    return crud.maintenance_schedule.create(db=db, obj_in=maintenance)

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

# =============================================================================
# MEMBERSHIP ENDPOINTS
# =============================================================================

@app.post("/membership/", response_model=schema.CustomerMembershipProfile, status_code=status.HTTP_201_CREATED)
def create_membership_profile(profile: schema.CustomerMembershipProfileCreate, db: Session = Depends(get_db)):
    """Create a customer membership profile"""
    return crud.membership_profile.create(db=db, obj_in=profile)

@app.patch("/membership/{customer_id}/points")
def update_customer_points(
    customer_id: int,
    points_to_add: int,
    db: Session = Depends(get_db)
):
    """Update customer points balance"""
    profile = crud.membership_profile.update_points(db, customer_id=customer_id, points_to_add=points_to_add)
    if profile is None:
        raise HTTPException(status_code=404, detail="Customer membership profile not found")
    return {"message": f"Added {points_to_add} points to customer {customer_id}"}

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