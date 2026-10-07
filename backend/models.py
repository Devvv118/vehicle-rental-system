from sqlalchemy import Column, Integer, String, Text, DECIMAL, Date, DateTime, Boolean, ForeignKey, TIMESTAMP, Index, text, DefaultClause
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime, date

Base = declarative_base()

class Customer(Base):
    __tablename__ = "customer"
    
    customer_id = Column(Integer, primary_key=True, autoincrement=True)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    phone = Column(String(20), nullable=False)
    address = Column(Text)
    driver_license = Column(String(20), unique=True, nullable=False)
    date_of_birth = Column(Date)
    created_at = Column(TIMESTAMP, default=func.current_timestamp())
    updated_at = Column(TIMESTAMP, default=func.current_timestamp(), onupdate=func.current_timestamp())
    
    # Relationships
    membership_profile = relationship("CustomerMembershipProfile", back_populates="customer", uselist=False, cascade="all, delete-orphan")
    vehicle_preferences = relationship("CustomerVehiclePreference", back_populates="customer", cascade="all, delete-orphan")
    reservations = relationship("Reservation", back_populates="customer", cascade="all, delete-orphan")
    rentals = relationship("Rental", back_populates="customer", cascade="all, delete-orphan")

class MembershipTier(Base):
    __tablename__ = "membership_tier"
    
    tier_name = Column(String(20), primary_key=True)
    description = Column(Text)
    monthly_fee = Column(DECIMAL(8, 2))
    free_upgrades = Column(Integer, comment="Number of free upgrades per month")
    bonus_point_rate = Column(DECIMAL(4, 2), comment="e.g., 1.25 = 25% bonus")
    
    # Relationships
    customer_profiles = relationship("CustomerMembershipProfile", back_populates="tier")

class CustomerMembershipProfile(Base):
    __tablename__ = "customer_membership_profile"
    
    profile_id = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(Integer, ForeignKey("customer.customer_id", ondelete="CASCADE"), unique=True, nullable=False)
    membership_tier = Column(String(20), ForeignKey("membership_tier.tier_name", onupdate="CASCADE"), default="Standard")
    points_balance = Column(Integer, default=0)
    tier_level = Column(String(20), default="Bronze")
    join_date = Column(Date, default=func.current_date())
    last_activity_date = Column(Date)
    lifetime_rentals = Column(Integer, default=0)
    lifetime_spending = Column(DECIMAL(10, 2), default=0.00)
    
    # Relationships
    customer = relationship("Customer", back_populates="membership_profile")
    tier = relationship("MembershipTier", back_populates="customer_profiles")

class CustomerVehiclePreference(Base):
    __tablename__ = "customer_vehicle_preference"
    
    customer_id = Column(Integer, ForeignKey("customer.customer_id", ondelete="CASCADE"), primary_key=True)
    vehicle_type = Column(String(30), primary_key=True, nullable=False)
    preference_score = Column(Integer, comment="1-10 scale")
    created_at = Column(TIMESTAMP, default=func.current_timestamp())
    
    # Relationships
    customer = relationship("Customer", back_populates="vehicle_preferences")

class Employee(Base):
    __tablename__ = "employee"
    
    employee_id = Column(Integer, primary_key=True, autoincrement=True)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    phone = Column(String(20), nullable=False)
    role = Column(String(30), nullable=False, comment="Manager, Agent, Mechanic, Admin")
    hire_date = Column(Date, nullable=False)
    salary = Column(DECIMAL(10, 2))
    location_id = Column(Integer, ForeignKey("location.location_id", ondelete="SET NULL"))
    manager_id = Column(Integer, ForeignKey("employee.employee_id", ondelete="SET NULL"))
    is_active = Column(Boolean, default=True)
    
    # Relationships
    location = relationship("Location", foreign_keys=[location_id], back_populates="employees", overlaps="employees")
    manager = relationship("Employee", remote_side=[employee_id], back_populates="subordinates")
    subordinates = relationship("Employee", back_populates="manager")
    managed_locations = relationship("Location", foreign_keys="Location.manager_id", back_populates="manager")
    rentals = relationship("Rental", back_populates="employee", overlaps="employee")
    incident_reports = relationship("IncidentReport", back_populates="reported_by_employee")
    maintenance_schedules = relationship("MaintenanceSchedule", back_populates="mechanic")


class Location(Base):
    __tablename__ = "location"
    
    location_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    address = Column(Text, nullable=False)
    city = Column(String(50), nullable=False)
    state = Column(String(50), nullable=False)
    zip_code = Column(String(10), nullable=False)
    phone = Column(String(20))
    operating_hours = Column(String(100))
    manager_id = Column(Integer, ForeignKey("employee.employee_id", ondelete="SET NULL"))
    
    # Relationships
    manager = relationship("Employee", foreign_keys=[manager_id], back_populates="managed_locations")
    employees = relationship("Employee", foreign_keys="Employee.location_id", back_populates="location", overlaps="location")
    vehicles = relationship("Vehicle", back_populates="location")
    pickup_reservations = relationship("Reservation", foreign_keys="Reservation.pickup_location_id", overlaps="pickup_location")
    return_reservations = relationship("Reservation", foreign_keys="Reservation.return_location_id", overlaps="return_location")
    pickup_rentals = relationship("Rental", foreign_keys="Rental.pickup_location_id", overlaps="pickup_location")
    return_rentals = relationship("Rental", foreign_keys="Rental.return_location_id", overlaps="return_location")


# class Employee(Base):
#     __tablename__ = "employee"
    
#     employee_id = Column(Integer, primary_key=True, autoincrement=True)
#     first_name = Column(String(50), nullable=False)
#     last_name = Column(String(50), nullable=False)
#     email = Column(String(255), unique=True, nullable=False)
#     phone = Column(String(20), nullable=False)
#     role = Column(String(30), nullable=False, comment="Manager, Agent, Mechanic, Admin")
#     hire_date = Column(Date, nullable=False)
#     salary = Column(DECIMAL(10, 2))
#     location_id = Column(Integer, ForeignKey("location.location_id", ondelete="SET NULL"))
#     manager_id = Column(Integer, ForeignKey("employee.employee_id", ondelete="SET NULL"))
#     is_active = Column(Boolean, default=True)
    
#     # Relationships
#     location = relationship("Location", foreign_keys=[location_id])
#     manager = relationship("Employee", remote_side=[employee_id])
#     subordinates = relationship("Employee", back_populates="manager")
#     managed_locations = relationship("Location", foreign_keys="Location.manager_id", back_populates="manager")
#     rentals = relationship("Rental", back_populates="employee")
#     incident_reports = relationship("IncidentReport", back_populates="reported_by_employee")
#     maintenance_schedules = relationship("MaintenanceSchedule", back_populates="mechanic")

# class Location(Base):
#     __tablename__ = "location"
    
#     location_id = Column(Integer, primary_key=True, autoincrement=True)
#     name = Column(String(100), nullable=False)
#     address = Column(Text, nullable=False)
#     city = Column(String(50), nullable=False)
#     state = Column(String(50), nullable=False)
#     zip_code = Column(String(10), nullable=False)
#     phone = Column(String(20))
#     operating_hours = Column(String(100))
#     manager_id = Column(Integer, ForeignKey("employee.employee_id", ondelete="SET NULL"))
    
#     # Relationships
#     manager = relationship("Employee", foreign_keys=[manager_id], back_populates="managed_locations")
#     employees = relationship("Employee", foreign_keys="Employee.location_id")
#     vehicles = relationship("Vehicle", back_populates="location")
#     pickup_reservations = relationship("Reservation", foreign_keys="Reservation.pickup_location_id")
#     return_reservations = relationship("Reservation", foreign_keys="Reservation.return_location_id")
#     pickup_rentals = relationship("Rental", foreign_keys="Rental.pickup_location_id")
#     return_rentals = relationship("Rental", foreign_keys="Rental.return_location_id")

class Vehicle(Base):
    __tablename__ = "vehicle"
    
    vehicle_id = Column(Integer, primary_key=True, autoincrement=True)
    model = Column(String(50), nullable=False)
    make = Column(String(50), nullable=False)
    license_plate = Column(String(10), unique=True, nullable=False)
    year = Column(Integer, nullable=False)
    availability = Column(Boolean, default=True)
    daily_rate = Column(DECIMAL(8, 2), nullable=False)
    mileage = Column(Integer, default=0)
    fuel_type = Column(String(20), default="Gasoline", comment="Gasoline, Diesel, Electric, Hybrid")
    transmission = Column(String(20), default="Automatic", comment="Manual, Automatic")
    seating_capacity = Column(Integer, default=5)
    location_id = Column(Integer, ForeignKey("location.location_id", ondelete="SET NULL"))
    created_at = Column(TIMESTAMP, default=func.current_timestamp())
    
    # Relationships
    location = relationship("Location", back_populates="vehicles")
    features = relationship("VehicleFeature", secondary="vehicle_feature_mapping", back_populates="vehicles")
    maintenance_record = relationship("VehicleMaintenanceRecord", back_populates="vehicle", uselist=False, cascade="all, delete-orphan")
    reservations = relationship("Reservation", back_populates="vehicle", cascade="all, delete-orphan")
    rentals = relationship("Rental", back_populates="vehicle", cascade="all, delete-orphan")
    maintenance_schedules = relationship("MaintenanceSchedule", back_populates="vehicle", cascade="all, delete-orphan")

class VehicleFeature(Base):
    __tablename__ = "vehicle_feature"
    
    feature_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False, comment="GPS, Bluetooth, Backup Camera, etc.")
    description = Column(Text)
    category = Column(String(30), comment="Safety, Entertainment, Convenience, etc.")
    
    # Relationships
    vehicles = relationship("Vehicle", secondary="vehicle_feature_mapping", back_populates="features")

class VehicleFeatureMapping(Base):
    __tablename__ = "vehicle_feature_mapping"
    
    vehicle_id = Column(Integer, ForeignKey("vehicle.vehicle_id", ondelete="CASCADE"), primary_key=True)
    feature_id = Column(Integer, ForeignKey("vehicle_feature.feature_id", ondelete="CASCADE"), primary_key=True)

class VehicleMaintenanceRecord(Base):
    __tablename__ = "vehicle_maintenance_record"
    
    maintenance_id = Column(Integer, primary_key=True, autoincrement=True)
    vehicle_id = Column(Integer, ForeignKey("vehicle.vehicle_id", ondelete="CASCADE"), unique=True, nullable=False)
    last_service_date = Column(Date)
    next_service_due = Column(Date)
    total_maintenance_cost = Column(DECIMAL(10, 2), default=0.00)
    service_history = Column(Text)
    current_condition = Column(String(20), default="Good", comment="Excellent, Good, Fair, Poor")
    maintenance_alerts = Column(Text)
    
    # Relationships
    vehicle = relationship("Vehicle", back_populates="maintenance_record")

class Reservation(Base):
    __tablename__ = "reservation"
    
    reservation_id = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(Integer, ForeignKey("customer.customer_id", ondelete="CASCADE"), nullable=False)
    vehicle_id = Column(Integer, ForeignKey("vehicle.vehicle_id", ondelete="CASCADE"), nullable=False)
    pickup_location_id = Column(Integer, ForeignKey("location.location_id"), nullable=False)
    return_location_id = Column(Integer, ForeignKey("location.location_id"), nullable=False)
    reserved_start_date = Column(DateTime, nullable=False)
    reserved_end_date = Column(DateTime, nullable=False)
    reservation_date = Column(TIMESTAMP, default=func.current_timestamp())
    status = Column(String(20), default="Active", comment="Active, Confirmed, Cancelled, Converted")
    special_requests = Column(Text)
    estimated_total = Column(DECIMAL(10, 2))
    
    # Relationships
    customer = relationship("Customer", back_populates="reservations")
    vehicle = relationship("Vehicle", back_populates="reservations")
    pickup_location = relationship("Location", foreign_keys=[pickup_location_id], overlaps="pickup_reservations,pickup_rentals")
    return_location = relationship("Location", foreign_keys=[return_location_id], overlaps="return_reservations,return_rentals")


class Rental(Base):
    __tablename__ = "rental"
    
    rental_id = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(Integer, ForeignKey("customer.customer_id", ondelete="CASCADE"), nullable=False)
    vehicle_id = Column(Integer, ForeignKey("vehicle.vehicle_id", ondelete="CASCADE"), nullable=False)
    employee_id = Column(Integer, ForeignKey("employee.employee_id", ondelete="SET NULL"))
    pickup_location_id = Column(Integer, ForeignKey("location.location_id"), nullable=False)
    return_location_id = Column(Integer, ForeignKey("location.location_id"), nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    actual_return_date = Column(DateTime)
    daily_rate = Column(DECIMAL(8, 2), nullable=False)
    total_amount = Column(DECIMAL(10, 2), nullable=False)
    security_deposit = Column(DECIMAL(8, 2), default=200.00)
    mileage_start = Column(Integer)
    mileage_end = Column(Integer)
    fuel_level_start = Column(DECIMAL(3, 2), comment="0.00 to 1.00 (percentage)")
    fuel_level_end = Column(DECIMAL(3, 2))
    status = Column(String(20), default="Active", comment="Active, Completed, Cancelled")
    discount_applied = Column(DECIMAL(8, 2), default=0.00)
    late_fees = Column(DECIMAL(8, 2), default=0.00)
    damage_fees = Column(DECIMAL(8, 2), default=0.00)
    created_at = Column(TIMESTAMP, default=func.current_timestamp())
    
    # Relationships
    customer = relationship("Customer", back_populates="rentals")
    vehicle = relationship("Vehicle", back_populates="rentals")
    employee = relationship("Employee", back_populates="rentals", overlaps="rentals,employee")
    pickup_location = relationship("Location", foreign_keys=[pickup_location_id], overlaps="pickup_rentals,pickup_reservations")
    return_location = relationship("Location", foreign_keys=[return_location_id], overlaps="return_rentals,return_reservations")
    payments = relationship("Payment", back_populates="rental", cascade="all, delete-orphan")
    insurance_plans = relationship("InsurancePlan", secondary="rental_insurance", back_populates="rentals")
    incident_reports = relationship("IncidentReport", back_populates="rental", cascade="all, delete-orphan")


# class Reservation(Base):
#     __tablename__ = "reservation"
    
#     reservation_id = Column(Integer, primary_key=True, autoincrement=True)
#     customer_id = Column(Integer, ForeignKey("customer.customer_id", ondelete="CASCADE"), nullable=False)
#     vehicle_id = Column(Integer, ForeignKey("vehicle.vehicle_id", ondelete="CASCADE"), nullable=False)
#     pickup_location_id = Column(Integer, ForeignKey("location.location_id"), nullable=False)
#     return_location_id = Column(Integer, ForeignKey("location.location_id"), nullable=False)
#     reserved_start_date = Column(DateTime, nullable=False)
#     reserved_end_date = Column(DateTime, nullable=False)
#     reservation_date = Column(TIMESTAMP, default=func.current_timestamp())
#     status = Column(String(20), default="Active", comment="Active, Confirmed, Cancelled, Converted")
#     special_requests = Column(Text)
#     estimated_total = Column(DECIMAL(10, 2))
    
#     # Relationships
#     customer = relationship("Customer", back_populates="reservations")
#     vehicle = relationship("Vehicle", back_populates="reservations")
#     pickup_location = relationship("Location", foreign_keys=[pickup_location_id])
#     return_location = relationship("Location", foreign_keys=[return_location_id])

# class Rental(Base):
#     __tablename__ = "rental"
    
#     rental_id = Column(Integer, primary_key=True, autoincrement=True)
#     customer_id = Column(Integer, ForeignKey("customer.customer_id", ondelete="CASCADE"), nullable=False)
#     vehicle_id = Column(Integer, ForeignKey("vehicle.vehicle_id", ondelete="CASCADE"), nullable=False)
#     employee_id = Column(Integer, ForeignKey("employee.employee_id", ondelete="SET NULL"))
#     pickup_location_id = Column(Integer, ForeignKey("location.location_id"), nullable=False)
#     return_location_id = Column(Integer, ForeignKey("location.location_id"), nullable=False)
#     start_date = Column(DateTime, nullable=False)
#     end_date = Column(DateTime, nullable=False)
#     actual_return_date = Column(DateTime)
#     daily_rate = Column(DECIMAL(8, 2), nullable=False)
#     total_amount = Column(DECIMAL(10, 2), nullable=False)
#     security_deposit = Column(DECIMAL(8, 2), default=200.00)
#     mileage_start = Column(Integer)
#     mileage_end = Column(Integer)
#     fuel_level_start = Column(DECIMAL(3, 2), comment="0.00 to 1.00 (percentage)")
#     fuel_level_end = Column(DECIMAL(3, 2))
#     status = Column(String(20), default="Active", comment="Active, Completed, Cancelled")
#     discount_applied = Column(DECIMAL(8, 2), default=0.00)
#     late_fees = Column(DECIMAL(8, 2), default=0.00)
#     damage_fees = Column(DECIMAL(8, 2), default=0.00)
#     created_at = Column(TIMESTAMP, default=func.current_timestamp())
    
#     # Relationships
#     customer = relationship("Customer", back_populates="rentals")
#     vehicle = relationship("Vehicle", back_populates="rentals")
#     employee = relationship("Employee", back_populates="rentals")
#     pickup_location = relationship("Location", foreign_keys=[pickup_location_id])
#     return_location = relationship("Location", foreign_keys=[return_location_id])
#     payments = relationship("Payment", back_populates="rental")
#     insurance_plans = relationship("InsurancePlan", secondary="rental_insurance", back_populates="rentals")
#     incident_reports = relationship("IncidentReport", back_populates="rental")

class Payment(Base):
    __tablename__ = "payment"
    
    payment_id = Column(Integer, primary_key=True, autoincrement=True)
    rental_id = Column(Integer, ForeignKey("rental.rental_id", ondelete="CASCADE"), nullable=False)
    payment_date = Column(DateTime, default=func.current_timestamp())
    amount = Column(DECIMAL(10, 2), nullable=False)
    method = Column(String(20), nullable=False, comment="Credit Card, Debit Card, Cash, Bank Transfer")
    transaction_id = Column(String(100))
    status = Column(String(20), default="Completed", comment="Pending, Completed, Failed, Refunded")
    payment_type = Column(String(20), nullable=False, comment="Rental, Deposit, Late Fee, Damage Fee")
    
    # Relationships
    rental = relationship("Rental", back_populates="payments")

class InsurancePlan(Base):
    __tablename__ = "insurance_plan"
    
    plan_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    daily_cost = Column(DECIMAL(6, 2), nullable=False)
    coverage_amount = Column(DECIMAL(12, 2), nullable=False)
    deductible = Column(DECIMAL(8, 2), nullable=False)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    rentals = relationship("Rental", secondary="rental_insurance", back_populates="insurance_plans")

class RentalInsurance(Base):
    __tablename__ = "rental_insurance"
    
    rental_id = Column(Integer, ForeignKey("rental.rental_id", ondelete="CASCADE"), primary_key=True)
    plan_id = Column(Integer, ForeignKey("insurance_plan.plan_id", ondelete="CASCADE"), primary_key=True)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    premium_amount = Column(DECIMAL(8, 2), nullable=False)

class IncidentReport(Base):
    __tablename__ = "incident_report"
    
    incident_id = Column(Integer, primary_key=True, autoincrement=True)
    rental_id = Column(Integer, ForeignKey("rental.rental_id", ondelete="CASCADE"), nullable=False)
    reported_by = Column(Integer, ForeignKey("employee.employee_id", ondelete="SET NULL"))
    incident_date = Column(DateTime, nullable=False)
    incident_type = Column(String(30), nullable=False, comment="Accident, Damage, Theft, etc.")
    description = Column(Text, nullable=False)
    estimated_cost = Column(DECIMAL(10, 2))
    status = Column(String(20), default="Open", comment="Open, Under Review, Resolved, Closed")
    photos = Column(Text, comment="JSON array of photo URLs")
    police_report_number = Column(String(50))
    
    # Relationships
    rental = relationship("Rental", back_populates="incident_reports")
    reported_by_employee = relationship("Employee", back_populates="incident_reports")

class MaintenanceSchedule(Base):
    __tablename__ = "maintenance_schedule"
    
    schedule_id = Column(Integer, primary_key=True, autoincrement=True)
    vehicle_id = Column(Integer, ForeignKey("vehicle.vehicle_id", ondelete="CASCADE"), nullable=False)
    maintenance_type = Column(String(50), nullable=False, comment="Oil Change, Tire Rotation, Inspection, etc.")
    scheduled_date = Column(Date, nullable=False)
    completed_date = Column(Date)
    assigned_mechanic = Column(Integer, ForeignKey("employee.employee_id", ondelete="SET NULL"))
    cost = Column(DECIMAL(8, 2))
    notes = Column(Text)
    status = Column(String(20), default="Scheduled", comment="Scheduled, In Progress, Completed, Cancelled")
    
    # Relationships
    vehicle = relationship("Vehicle", back_populates="maintenance_schedules")
    mechanic = relationship("Employee", back_populates="maintenance_schedules")


# PostgreSQL schema details

def _apply_server_defaults():
    """The models declare defaults Python-side (default=...). Mirror them as real DEFAULTs in the generated DDL so that
    rows inserted with plain SQL (psql, seed files, data imports) behave exactly like rows created through the API."""
    for table in Base.metadata.tables.values():
        for col in table.columns:
            d = col.default
            if col.primary_key or col.server_default is not None or d is None:
                continue
            if d.is_scalar:
                v = d.arg
                if isinstance(v, bool):
                    lit = "true" if v else "false"
                elif isinstance(v, (int, float)) or v.__class__.__name__ == "Decimal":
                    lit = str(v)
                else:
                    lit = "'" + str(v).replace("'", "''") + "'"
                col.server_default = DefaultClause(text(lit))
            elif d.is_clause_element:       # func.current_timestamp(), func.current_date()
                col.server_default = DefaultClause(d.arg)

_apply_server_defaults()

# index foreign keys
Index("ix_employee_location_id", Employee.location_id)
Index("ix_vehicle_location_id", Vehicle.location_id)
Index("ix_vehicle_availability", Vehicle.availability)
Index("ix_reservation_vehicle_status", Reservation.vehicle_id, Reservation.status)
Index("ix_reservation_customer_id", Reservation.customer_id)
Index("ix_rental_customer_id", Rental.customer_id)
Index("ix_rental_vehicle_status", Rental.vehicle_id, Rental.status)
Index("ix_rental_status_start_date", Rental.status, Rental.start_date)
Index("ix_payment_rental_id", Payment.rental_id)
Index("ix_incident_report_rental_id", IncidentReport.rental_id)
Index("ix_maintenance_schedule_vehicle_id", MaintenanceSchedule.vehicle_id)
Index("ix_maintenance_schedule_status_date", MaintenanceSchedule.status, MaintenanceSchedule.scheduled_date)

# case sensitivity handling
Index("uq_customer_email_lower", func.lower(Customer.email), unique=True)
Index("uq_customer_driver_license_lower", func.lower(Customer.driver_license), unique=True)
Index("uq_employee_email_lower", func.lower(Employee.email), unique=True)
Index("uq_vehicle_license_plate_lower", func.lower(Vehicle.license_plate), unique=True)
