from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func, desc, asc
from sqlalchemy.inspection import inspect
from typing import List, Optional, Dict, Any
from datetime import datetime, date, timedelta
from decimal import Decimal, ROUND_HALF_UP
import math

import models as models
import schemas as schema

class BusinessRuleError(Exception):
    """Raised for rule violations; main.py turns it into an HTTP 400/404/409 with a readable message."""
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


LATE_FEE_RATE = Decimal("0.50") # late fee per day = 50% of the daily rate (same rule the UI used)
POINTS_PER_CURRENCY_UNIT = Decimal("1") # 1 loyalty point per 1.00 spent, multiplied by the tier bonus rate
STANDARD_TIER = "Standard"
BLOCKING_RESERVATION_STATUSES = ["Active", "Confirmed"]


def money(v) -> Decimal:
    return Decimal(str(v if v is not None else 0)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def require(db: Session, model, pk_value, label: str, status_code: int = 400):
    """Make sure a referenced row exists (gives a readable error instead of a database FK crash)."""
    if pk_value is None:
        return None
    pk = inspect(model).primary_key[0]
    obj = db.query(model).filter(pk == pk_value).first()
    if obj is None:
        raise BusinessRuleError(f"{label} {pk_value} does not exist", status_code)
    return obj


class CRUDBase:
    def __init__(self, model):
        self.model = model
        self.pk = inspect(model).primary_key[0].name
    
    def get(self, db: Session, id: Any) -> Optional[models.Base]:
        return db.query(self.model).filter(getattr(self.model, self.pk) == id).first()
    
    def get_multi(self, db: Session, *, skip: int = 0, limit: int = 100) -> List[models.Base]:
        return db.query(self.model).order_by(inspect(self.model).primary_key[0]).offset(skip).limit(limit).all()
    
    def create(self, db: Session, *, obj_in: schema.BaseModel) -> models.Base:
        obj_data = obj_in.model_dump()
        db_obj = self.model(**obj_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def update(self, db: Session, *, db_obj: models.Base, obj_in: schema.BaseModel) -> models.Base:
        obj_data = obj_in.model_dump(exclude_unset=True)
        for field, value in obj_data.items():
            setattr(db_obj, field, value)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def delete(self, db: Session, *, id: Any) -> models.Base:
        # obj = db.query(self.model).get(id)
        # if obj:
        #     db.delete(obj)
        #     db.commit()
        # return obj
        obj = db.query(self.model).filter(getattr(self.model, self.pk) == id).first()
        if obj:
            db.delete(obj)
            db.commit()
        return obj

# Customer CRUD operations
class CRUDCustomer(CRUDBase):
    def get_by_email(self, db: Session, *, email: str) -> Optional[models.Customer]:
        return db.query(models.Customer).filter(func.lower(models.Customer.email) == email.lower()).first()
    
    def get_by_driver_license(self, db: Session, *, driver_license: str) -> Optional[models.Customer]:
        return db.query(models.Customer).filter(func.lower(models.Customer.driver_license) == driver_license.lower()).first()
    
    def get_with_profile(self, db: Session, customer_id: int) -> Optional[models.Customer]:
        return db.query(models.Customer).options(
            joinedload(models.Customer.membership_profile).joinedload(models.CustomerMembershipProfile.tier),
            joinedload(models.Customer.vehicle_preferences)
        ).filter(models.Customer.customer_id == customer_id).first()
    
    def search_customers(self, db: Session, *, search_term: str, skip: int = 0, limit: int = 100) -> List[models.Customer]:
        return db.query(models.Customer).filter(
            or_(
                models.Customer.first_name.ilike(f"%{search_term}%"),
                models.Customer.last_name.ilike(f"%{search_term}%"),
                models.Customer.email.ilike(f"%{search_term}%"),
                models.Customer.phone.ilike(f"%{search_term}%"),
                models.Customer.driver_license.ilike(f"%{search_term}%")
            )
        ).order_by(models.Customer.customer_id).offset(skip).limit(limit).all()
    
    def get_top_customers(self, db: Session, *, limit: int = 10) -> List[models.Customer]:
        return db.query(models.Customer).join(models.CustomerMembershipProfile).order_by(
            desc(models.CustomerMembershipProfile.lifetime_spending), models.Customer.customer_id
        ).limit(limit).all()

# Vehicle CRUD operations
class CRUDVehicle(CRUDBase):
    def get_available_vehicles(self, db: Session, *, skip: int = 0, limit: int = 100) -> List[models.Vehicle]:
        return db.query(models.Vehicle).filter(
            models.Vehicle.availability == True
        ).order_by(models.Vehicle.vehicle_id).offset(skip).limit(limit).all()
    
    def get_by_license_plate(self, db: Session, *, license_plate: str) -> Optional[models.Vehicle]:
        return db.query(models.Vehicle).filter(
            func.lower(models.Vehicle.license_plate) == license_plate.lower()
        ).first()
    
    def filter_vehicles(self, db: Session, *, filters: schema.VehicleFilters, skip: int = 0, limit: int = 100) -> List[models.Vehicle]:
        query = db.query(models.Vehicle)
        
        if filters.make:
            query = query.filter(models.Vehicle.make.ilike(f"%{filters.make}%"))
        if filters.model:
            query = query.filter(models.Vehicle.model.ilike(f"%{filters.model}%"))
        if filters.fuel_type:
            query = query.filter(models.Vehicle.fuel_type == filters.fuel_type)
        if filters.transmission:
            query = query.filter(models.Vehicle.transmission == filters.transmission)
        if filters.min_year:
            query = query.filter(models.Vehicle.year >= filters.min_year)
        if filters.max_year:
            query = query.filter(models.Vehicle.year <= filters.max_year)
        if filters.availability is not None:
            query = query.filter(models.Vehicle.availability == filters.availability)
        if filters.location_id:
            query = query.filter(models.Vehicle.location_id == filters.location_id)
        if filters.min_daily_rate:
            query = query.filter(models.Vehicle.daily_rate >= filters.min_daily_rate)
        if filters.max_daily_rate:
            query = query.filter(models.Vehicle.daily_rate <= filters.max_daily_rate)
        
        return query.order_by(models.Vehicle.vehicle_id).offset(skip).limit(limit).all()
    
    def get_with_features(self, db: Session, vehicle_id: int) -> Optional[models.Vehicle]:
        return db.query(models.Vehicle).options(
            joinedload(models.Vehicle.features),
            joinedload(models.Vehicle.maintenance_record),
            joinedload(models.Vehicle.location)
        ).filter(models.Vehicle.vehicle_id == vehicle_id).first()
    
    def update_availability(self, db: Session, *, vehicle_id: int, available: bool) -> Optional[models.Vehicle]:
        vehicle = db.query(models.Vehicle).filter(models.Vehicle.vehicle_id == vehicle_id).first()
        if vehicle:
            vehicle.availability = available
            db.commit()
            db.refresh(vehicle)
        return vehicle
    
    def get_vehicles_needing_maintenance(self, db: Session) -> List[models.Vehicle]:
        return db.query(models.Vehicle).join(models.VehicleMaintenanceRecord).filter(
            models.VehicleMaintenanceRecord.next_service_due <= date.today()
        ).order_by(models.Vehicle.vehicle_id).all()

# Rental CRUD operations
class CRUDRental(CRUDBase):
    def get_active_rentals(self, db: Session, *, skip: int = 0, limit: int = 100) -> List[models.Rental]:
        return db.query(models.Rental).filter(
            models.Rental.status == "Active"
        ).order_by(models.Rental.rental_id).offset(skip).limit(limit).all()
    
    def get_customer_rentals(self, db: Session, *, customer_id: int, skip: int = 0, limit: int = 100) -> List[models.Rental]:
        return db.query(models.Rental).filter(
            models.Rental.customer_id == customer_id
        ).order_by(desc(models.Rental.created_at), desc(models.Rental.rental_id)).offset(skip).limit(limit).all()
    
    def get_overdue_rentals(self, db: Session) -> List[models.Rental]:
        return db.query(models.Rental).filter(
            and_(
                models.Rental.status == "Active",
                models.Rental.end_date < datetime.now(),
                models.Rental.actual_return_date.is_(None)
            )
        ).order_by(models.Rental.rental_id).all()
    
    def filter_rentals(self, db: Session, *, filters: schema.RentalFilters, skip: int = 0, limit: int = 100) -> List[models.Rental]:
        query = db.query(models.Rental)
        
        if filters.customer_id:
            query = query.filter(models.Rental.customer_id == filters.customer_id)
        if filters.vehicle_id:
            query = query.filter(models.Rental.vehicle_id == filters.vehicle_id)
        if filters.status:
            query = query.filter(models.Rental.status == filters.status)
        if filters.start_date_from:
            query = query.filter(models.Rental.start_date >= filters.start_date_from)
        if filters.start_date_to:
            query = query.filter(models.Rental.start_date < datetime.combine(filters.start_date_to, datetime.min.time()) + timedelta(days=1))
        if filters.pickup_location_id:
            query = query.filter(models.Rental.pickup_location_id == filters.pickup_location_id)
        if filters.return_location_id:
            query = query.filter(models.Rental.return_location_id == filters.return_location_id)
        
        return query.order_by(desc(models.Rental.created_at), desc(models.Rental.rental_id)).offset(skip).limit(limit).all()
    
    def get_with_details(self, db: Session, rental_id: int) -> Optional[models.Rental]:
        return db.query(models.Rental).options(
            joinedload(models.Rental.customer),
            joinedload(models.Rental.vehicle),
            joinedload(models.Rental.employee),
            joinedload(models.Rental.pickup_location),
            joinedload(models.Rental.return_location),
            joinedload(models.Rental.payments),
            joinedload(models.Rental.incident_reports)
        ).filter(models.Rental.rental_id == rental_id).first()
    
    def create_checked(self, db: Session, *, obj_in: schema.RentalCreate, commit: bool = True,
                       ignore_reservation_id: Optional[int] = None) -> models.Rental:
        """Create a rental atomically: validate references, make sure the vehicle is free, mark it as rented out."""
        require(db, models.Customer, obj_in.customer_id, "Customer")
        vehicle = require(db, models.Vehicle, obj_in.vehicle_id, "Vehicle")
        require(db, models.Employee, obj_in.employee_id, "Employee")
        require(db, models.Location, obj_in.pickup_location_id, "Pickup location")
        require(db, models.Location, obj_in.return_location_id, "Return location")

        is_active = obj_in.status == "Active"
        if is_active:
            if not vehicle.availability:
                raise BusinessRuleError("Vehicle is not available for rental")
            clash = reservation.find_conflict(
                db, vehicle_id=vehicle.vehicle_id, start_date=obj_in.start_date, end_date=obj_in.end_date,
                exclude_reservation_id=ignore_reservation_id, exclude_customer_id=obj_in.customer_id)
            if clash is not None:
                raise BusinessRuleError("Vehicle is not available for the selected dates (reserved by another customer)")

        db_obj = models.Rental(**obj_in.model_dump())
        db.add(db_obj)
        if is_active:
            vehicle.availability = False
        if commit:
            db.commit()
            db.refresh(db_obj)
        return db_obj

    @staticmethod
    def calculate_late_fee(rental: models.Rental, returned_at: datetime) -> Decimal:
        if rental.end_date is None or returned_at <= rental.end_date:
            return Decimal("0.00")
        days_late = math.ceil((returned_at - rental.end_date).total_seconds() / 86400)
        return money(Decimal(days_late) * (rental.daily_rate or 0) * LATE_FEE_RATE)

    def return_vehicle(self, db: Session, *, rental_id: int, return_data: Dict[str, Any]) -> Optional[models.Rental]:
        """Complete a rental: store the return details, free the vehicle and credit the customer's membership.
        Everything happens in ONE transaction."""
        rental = db.query(models.Rental).filter(models.Rental.rental_id == rental_id).first()
        if rental is None:
            return None
        if rental.status != "Active":
            raise BusinessRuleError(f"Rental is already {rental.status.lower()} and cannot be returned again")

        returned_at = return_data.get("actual_return_date") or datetime.now()
        mileage_end = return_data.get("mileage_end")
        if mileage_end is not None and rental.mileage_start is not None and mileage_end < rental.mileage_start:
            raise BusinessRuleError(
                f"Ending mileage ({mileage_end}) cannot be lower than the starting mileage ({rental.mileage_start})")

        late_fees = return_data.get("late_fees")
        late_fees = self.calculate_late_fee(rental, returned_at) if late_fees is None else money(late_fees)
        damage_fees = money(return_data.get("damage_fees"))

        rental.actual_return_date = returned_at
        rental.mileage_end = mileage_end
        rental.fuel_level_end = return_data.get("fuel_level_end")
        rental.status = "Completed"
        rental.late_fees = late_fees
        rental.damage_fees = damage_fees

        vehicle = db.query(models.Vehicle).filter(models.Vehicle.vehicle_id == rental.vehicle_id).first()
        if vehicle:
            vehicle.availability = True
            if mileage_end is not None:
                vehicle.mileage = mileage_end

        total_charged = money(rental.total_amount) + late_fees + damage_fees
        membership_profile.record_completed_rental(db, customer_id=rental.customer_id, amount=total_charged, commit=False)

        db.commit()
        db.refresh(rental)
        return rental

    def get_rental_revenue(self, db: Session, *, start_date: date, end_date: date) -> Decimal:
        """Revenue (rental total + late + damage fees) of completed rentals that STARTED between the two dates (inclusive)."""
        range_start = datetime.combine(start_date, datetime.min.time())
        range_end = datetime.combine(end_date, datetime.min.time()) + timedelta(days=1)
        result = db.query(
            func.sum(models.Rental.total_amount + func.coalesce(models.Rental.late_fees, 0) + func.coalesce(models.Rental.damage_fees, 0))
        ).filter(
            and_(
                models.Rental.start_date >= range_start,
                models.Rental.start_date < range_end,
                models.Rental.status == "Completed"
            )
        ).scalar()
        return result or Decimal('0.00')

# Reservation CRUD operations
class CRUDReservation(CRUDBase):
    def get_active_reservations(self, db: Session, *, skip: int = 0, limit: int = 100) -> List[models.Reservation]:
        return db.query(models.Reservation).filter(
            models.Reservation.status == "Active"
        ).order_by(models.Reservation.reservation_id).offset(skip).limit(limit).all()
    
    def get_customer_reservations(self, db: Session, *, customer_id: int) -> List[models.Reservation]:
        return db.query(models.Reservation).filter(
            models.Reservation.customer_id == customer_id
        ).order_by(desc(models.Reservation.reservation_date), desc(models.Reservation.reservation_id)).all()
    
    def find_conflict(self, db: Session, *, vehicle_id: int, start_date: datetime, end_date: datetime,
                      exclude_reservation_id: Optional[int] = None, exclude_customer_id: Optional[int] = None):
        """Return the first active/confirmed reservation overlapping [start_date, end_date) for this vehicle
        (back-to-back bookings are fine). `exclude_customer_id` ignores that customer's own reservations."""
        q = db.query(models.Reservation).filter(
            models.Reservation.vehicle_id == vehicle_id,
            models.Reservation.status.in_(BLOCKING_RESERVATION_STATUSES),
            models.Reservation.reserved_start_date < end_date,
            models.Reservation.reserved_end_date > start_date,
        )
        if exclude_reservation_id is not None:
            q = q.filter(models.Reservation.reservation_id != exclude_reservation_id)
        if exclude_customer_id is not None:
            q = q.filter(models.Reservation.customer_id != exclude_customer_id)
        return q.first()

    def find_rental_conflict(self, db: Session, *, vehicle_id: int, start_date: datetime, end_date: datetime):
        """An Active rental that overlaps the period (a rental that is overdue is still considered out)."""
        now = datetime.now()
        return db.query(models.Rental).filter(
            models.Rental.vehicle_id == vehicle_id,
            models.Rental.status == "Active",
            models.Rental.start_date < end_date,
            func.greatest(models.Rental.end_date, now) > start_date,
        ).first()

    def check_vehicle_availability(self, db: Session, *, vehicle_id: int, start_date: datetime, end_date: datetime,
                                   exclude_reservation_id: Optional[int] = None) -> bool:
        if self.find_conflict(db, vehicle_id=vehicle_id, start_date=start_date, end_date=end_date,
                              exclude_reservation_id=exclude_reservation_id) is not None:
            return False
        return self.find_rental_conflict(db, vehicle_id=vehicle_id, start_date=start_date, end_date=end_date) is None

    def create_checked(self, db: Session, *, obj_in: schema.ReservationCreate) -> models.Reservation:
        require(db, models.Customer, obj_in.customer_id, "Customer")
        require(db, models.Vehicle, obj_in.vehicle_id, "Vehicle")
        require(db, models.Location, obj_in.pickup_location_id, "Pickup location")
        require(db, models.Location, obj_in.return_location_id, "Return location")
        if obj_in.status in BLOCKING_RESERVATION_STATUSES and not self.check_vehicle_availability(
                db, vehicle_id=obj_in.vehicle_id, start_date=obj_in.reserved_start_date, end_date=obj_in.reserved_end_date):
            raise BusinessRuleError("Vehicle is not available for the selected dates")
        return self.create(db, obj_in=obj_in)

    def update_checked(self, db: Session, *, db_obj: models.Reservation, obj_in: schema.ReservationUpdate) -> models.Reservation:
        changes = obj_in.model_dump(exclude_unset=True)
        vehicle_id = changes.get("vehicle_id", db_obj.vehicle_id)
        start = changes.get("reserved_start_date", db_obj.reserved_start_date)
        end = changes.get("reserved_end_date", db_obj.reserved_end_date)
        status_ = changes.get("status", db_obj.status)
        if end <= start:
            raise BusinessRuleError("reserved_end_date must be after reserved_start_date")
        if "vehicle_id" in changes:
            require(db, models.Vehicle, vehicle_id, "Vehicle")
        for key, label in (("pickup_location_id", "Pickup location"), ("return_location_id", "Return location")):
            if key in changes:
                require(db, models.Location, changes[key], label)
        if status_ in BLOCKING_RESERVATION_STATUSES and not self.check_vehicle_availability(
                db, vehicle_id=vehicle_id, start_date=start, end_date=end, exclude_reservation_id=db_obj.reservation_id):
            raise BusinessRuleError("Vehicle is not available for the selected dates")
        return self.update(db, db_obj=db_obj, obj_in=obj_in)

    def convert_to_rental(self, db: Session, *, reservation_id: int, rental_data: schema.RentalCreate) -> models.Rental:
        reservation_ = db.query(models.Reservation).filter(models.Reservation.reservation_id == reservation_id).first()
        if reservation_ is None:
            raise BusinessRuleError("Reservation not found", 404)
        if reservation_.status not in BLOCKING_RESERVATION_STATUSES:
            raise BusinessRuleError(f"A {reservation_.status.lower()} reservation cannot be converted to a rental")
        if rental_data.customer_id != reservation_.customer_id or rental_data.vehicle_id != reservation_.vehicle_id:
            raise BusinessRuleError("Rental customer/vehicle must match the reservation")
        rental_ = rental.create_checked(db, obj_in=rental_data, commit=False, ignore_reservation_id=reservation_id)
        reservation_.status = "Converted"
        db.commit()
        db.refresh(rental_)
        return rental_

# Employee CRUD operations
class CRUDEmployee(CRUDBase):
    def get_by_email(self, db: Session, *, email: str) -> Optional[models.Employee]:
        return db.query(models.Employee).filter(func.lower(models.Employee.email) == email.lower()).first()
    
    def get_active_employees(self, db: Session, *, skip: int = 0, limit: int = 100) -> List[models.Employee]:
        return db.query(models.Employee).filter(
            models.Employee.is_active == True
        ).order_by(models.Employee.employee_id).offset(skip).limit(limit).all()
    
    def get_by_role(self, db: Session, *, role: str) -> List[models.Employee]:
        return db.query(models.Employee).filter(
            and_(func.lower(models.Employee.role) == role.lower(), models.Employee.is_active == True)
        ).order_by(models.Employee.employee_id).all()
    
    def get_by_location(self, db: Session, *, location_id: int) -> List[models.Employee]:
        return db.query(models.Employee).filter(
            and_(models.Employee.location_id == location_id, models.Employee.is_active == True)
        ).order_by(models.Employee.employee_id).all()

# Location CRUD operations
class CRUDLocation(CRUDBase):
    def get_with_details(self, db: Session, location_id: int) -> Optional[models.Location]:
        return db.query(models.Location).options(
            joinedload(models.Location.manager),
            joinedload(models.Location.employees),
            joinedload(models.Location.vehicles)
        ).filter(models.Location.location_id == location_id).first()
    
    def get_by_city(self, db: Session, *, city: str) -> List[models.Location]:
        return db.query(models.Location).filter(models.Location.city.ilike(f"%{city}%")).order_by(models.Location.location_id).all()

# Payment CRUD operations
class CRUDPayment(CRUDBase):
    def get_rental_payments(self, db: Session, *, rental_id: int) -> List[models.Payment]:
        return db.query(models.Payment).filter(
            models.Payment.rental_id == rental_id
        ).order_by(models.Payment.payment_date, models.Payment.payment_id).all()
    
    def get_failed_payments(self, db: Session) -> List[models.Payment]:
        return db.query(models.Payment).filter(models.Payment.status == "Failed").order_by(models.Payment.payment_id).all()
    
    def get_payments_by_date_range(self, db: Session, *, start_date: date, end_date: date) -> List[models.Payment]:
        return db.query(models.Payment).filter(
            and_(
                func.date(models.Payment.payment_date) >= start_date,
                func.date(models.Payment.payment_date) <= end_date,
                models.Payment.status == "Completed"
            )
        ).order_by(models.Payment.payment_date, models.Payment.payment_id).all()

# Insurance Plan CRUD operations
class CRUDInsurancePlan(CRUDBase):
    def get_active_plans(self, db: Session) -> List[models.InsurancePlan]:
        return db.query(models.InsurancePlan).filter(models.InsurancePlan.is_active == True).order_by(models.InsurancePlan.plan_id).all()

# Incident Report CRUD operations
class CRUDIncidentReport(CRUDBase):
    def get_rental_incidents(self, db: Session, *, rental_id: int) -> List[models.IncidentReport]:
        return db.query(models.IncidentReport).filter(
            models.IncidentReport.rental_id == rental_id
        ).order_by(models.IncidentReport.incident_id).all()
    
    def get_open_incidents(self, db: Session) -> List[models.IncidentReport]:
        return db.query(models.IncidentReport).filter(
            models.IncidentReport.status.in_(["Open", "Under Review"])
        ).order_by(models.IncidentReport.incident_date, models.IncidentReport.incident_id).all()

# Maintenance Schedule CRUD operations
class CRUDMaintenanceSchedule(CRUDBase):
    def get_all_ordered(self, db: Session, *, skip: int = 0, limit: int = 100) -> List[models.MaintenanceSchedule]:
        return db.query(models.MaintenanceSchedule).order_by(
            desc(models.MaintenanceSchedule.scheduled_date), desc(models.MaintenanceSchedule.schedule_id)).offset(skip).limit(limit).all()

    def get_vehicle_maintenance(self, db: Session, *, vehicle_id: int) -> List[models.MaintenanceSchedule]:
        return db.query(models.MaintenanceSchedule).filter(
            models.MaintenanceSchedule.vehicle_id == vehicle_id
        ).order_by(desc(models.MaintenanceSchedule.scheduled_date), desc(models.MaintenanceSchedule.schedule_id)).all()
    
    def get_scheduled_maintenance(self, db: Session, *, target_date: date = None) -> List[models.MaintenanceSchedule]:
        if target_date is None:
            target_date = date.today()
        return db.query(models.MaintenanceSchedule).filter(
            and_(
                models.MaintenanceSchedule.scheduled_date <= target_date,
                models.MaintenanceSchedule.status == "Scheduled"
            )
        ).order_by(models.MaintenanceSchedule.scheduled_date, models.MaintenanceSchedule.schedule_id).all()
    
    def get_mechanic_schedule(self, db: Session, *, mechanic_id: int, start_date: date, end_date: date) -> List[models.MaintenanceSchedule]:
        return db.query(models.MaintenanceSchedule).filter(
            and_(
                models.MaintenanceSchedule.assigned_mechanic == mechanic_id,
                models.MaintenanceSchedule.scheduled_date >= start_date,
                models.MaintenanceSchedule.scheduled_date <= end_date
            )
        ).order_by(models.MaintenanceSchedule.scheduled_date, models.MaintenanceSchedule.schedule_id).all()

# Membership operations
class CRUDMembershipProfile(CRUDBase):
    def get_by_customer(self, db: Session, *, customer_id: int) -> Optional[models.CustomerMembershipProfile]:
        return db.query(models.CustomerMembershipProfile).filter(
            models.CustomerMembershipProfile.customer_id == customer_id
        ).first()

    def ensure_tier(self, db: Session, tier_name: str = STANDARD_TIER) -> models.MembershipTier:
        tier = db.query(models.MembershipTier).filter(models.MembershipTier.tier_name == tier_name).first()
        if tier is None:
            if tier_name != STANDARD_TIER:
                raise BusinessRuleError(f"Membership tier '{tier_name}' does not exist")
            tier = models.MembershipTier(tier_name=STANDARD_TIER, description="Default membership tier",
                                         monthly_fee=Decimal("0.00"), free_upgrades=0, bonus_point_rate=Decimal("1.00"))
            db.add(tier)
            db.flush()
        return tier

    def ensure_for_customer(self, db: Session, *, customer_id: int, commit: bool = True) -> models.CustomerMembershipProfile:
        """Every customer gets a membership profile (Standard tier) - created on demand if missing."""
        profile = self.get_by_customer(db, customer_id=customer_id)
        if profile is None:
            self.ensure_tier(db)
            profile = models.CustomerMembershipProfile(
                customer_id=customer_id, membership_tier=STANDARD_TIER, points_balance=0, tier_level="Bronze",
                lifetime_rentals=0, lifetime_spending=Decimal("0.00"))
            db.add(profile)
            db.flush()
        if commit:
            db.commit()
            db.refresh(profile)
        return profile

    def create_checked(self, db: Session, *, obj_in: schema.CustomerMembershipProfileCreate):
        require(db, models.Customer, obj_in.customer_id, "Customer", 404)
        if self.get_by_customer(db, customer_id=obj_in.customer_id) is not None:
            raise BusinessRuleError("Customer already has a membership profile")
        self.ensure_tier(db, obj_in.membership_tier or STANDARD_TIER)
        return self.create(db, obj_in=obj_in)

    def update_points(self, db: Session, *, customer_id: int, points_to_add: int) -> Optional[models.CustomerMembershipProfile]:
        profile = self.get_by_customer(db, customer_id=customer_id)
        if profile is None:
            if db.query(models.Customer).filter(models.Customer.customer_id == customer_id).first() is None:
                return None
            profile = self.ensure_for_customer(db, customer_id=customer_id, commit=False)
        new_balance = (profile.points_balance or 0) + points_to_add
        if new_balance < 0:
            raise BusinessRuleError("Points balance cannot become negative")
        profile.points_balance = new_balance
        profile.last_activity_date = date.today()
        db.commit()
        db.refresh(profile)
        return profile

    def record_completed_rental(self, db: Session, *, customer_id: int, amount: Decimal, commit: bool = True):
        """Add the rental to lifetime stats and award loyalty points (tier bonus rate applies)."""
        profile = self.ensure_for_customer(db, customer_id=customer_id, commit=False)
        tier = db.query(models.MembershipTier).filter(models.MembershipTier.tier_name == profile.membership_tier).first()
        bonus = Decimal(str(tier.bonus_point_rate)) if tier is not None and tier.bonus_point_rate is not None else Decimal("1")
        points = int((Decimal(str(amount)) * POINTS_PER_CURRENCY_UNIT * bonus).to_integral_value(rounding="ROUND_FLOOR"))
        profile.lifetime_spending = money(profile.lifetime_spending) + money(amount)
        profile.lifetime_rentals = (profile.lifetime_rentals or 0) + 1
        profile.points_balance = (profile.points_balance or 0) + points
        profile.last_activity_date = date.today()
        if commit:
            db.commit()
            db.refresh(profile)
        return profile

    def update_spending(self, db: Session, *, customer_id: int, amount: Decimal) -> Optional[models.CustomerMembershipProfile]:
        return self.record_completed_rental(db, customer_id=customer_id, amount=amount)

# Initialize CRUD instances
customer = CRUDCustomer(models.Customer)
vehicle = CRUDVehicle(models.Vehicle)
rental = CRUDRental(models.Rental)
reservation = CRUDReservation(models.Reservation)
employee = CRUDEmployee(models.Employee)
location = CRUDLocation(models.Location)
payment = CRUDPayment(models.Payment)
insurance_plan = CRUDInsurancePlan(models.InsurancePlan)
incident_report = CRUDIncidentReport(models.IncidentReport)
maintenance_schedule = CRUDMaintenanceSchedule(models.MaintenanceSchedule)
membership_profile = CRUDMembershipProfile(models.CustomerMembershipProfile)
vehicle_feature = CRUDBase(models.VehicleFeature)
membership_tier = CRUDBase(models.MembershipTier)