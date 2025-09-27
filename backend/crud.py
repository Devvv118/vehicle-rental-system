from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func, desc, asc
from sqlalchemy.inspection import inspect
from typing import List, Optional, Dict, Any
from datetime import datetime, date
from decimal import Decimal

import models as models
import schemas as schema

# Base CRUD class
class CRUDBase:
    def __init__(self, model):
        self.model = model
        self.pk = inspect(model).primary_key[0].name
    
    def get(self, db: Session, id: Any) -> Optional[models.Base]:
        return db.query(self.model).filter(getattr(self.model, self.pk) == id).first()
    
    def get_multi(self, db: Session, *, skip: int = 0, limit: int = 100) -> List[models.Base]:
        return db.query(self.model).offset(skip).limit(limit).all()
    
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
        return db.query(models.Customer).filter(models.Customer.email == email).first()
    
    def get_by_driver_license(self, db: Session, *, driver_license: str) -> Optional[models.Customer]:
        return db.query(models.Customer).filter(models.Customer.driver_license == driver_license).first()
    
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
                models.Customer.phone.ilike(f"%{search_term}%")
            )
        ).offset(skip).limit(limit).all()
    
    def get_top_customers(self, db: Session, *, limit: int = 10) -> List[models.Customer]:
        return db.query(models.Customer).join(models.CustomerMembershipProfile).order_by(
            desc(models.CustomerMembershipProfile.lifetime_spending)
        ).limit(limit).all()

# Vehicle CRUD operations
class CRUDVehicle(CRUDBase):
    def get_available_vehicles(self, db: Session, *, skip: int = 0, limit: int = 100) -> List[models.Vehicle]:
        return db.query(models.Vehicle).filter(
            models.Vehicle.availability == True
        ).offset(skip).limit(limit).all()
    
    def get_by_license_plate(self, db: Session, *, license_plate: str) -> Optional[models.Vehicle]:
        return db.query(models.Vehicle).filter(
            models.Vehicle.license_plate == license_plate
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
        
        return query.offset(skip).limit(limit).all()
    
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
        ).all()

# Rental CRUD operations
class CRUDRental(CRUDBase):
    def get_active_rentals(self, db: Session, *, skip: int = 0, limit: int = 100) -> List[models.Rental]:
        return db.query(models.Rental).filter(
            models.Rental.status == "Active"
        ).offset(skip).limit(limit).all()
    
    def get_customer_rentals(self, db: Session, *, customer_id: int, skip: int = 0, limit: int = 100) -> List[models.Rental]:
        return db.query(models.Rental).filter(
            models.Rental.customer_id == customer_id
        ).order_by(desc(models.Rental.created_at)).offset(skip).limit(limit).all()
    
    def get_overdue_rentals(self, db: Session) -> List[models.Rental]:
        return db.query(models.Rental).filter(
            and_(
                models.Rental.status == "Active",
                models.Rental.end_date < datetime.now(),
                models.Rental.actual_return_date.is_(None)
            )
        ).all()
    
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
            query = query.filter(models.Rental.start_date <= filters.start_date_to)
        if filters.pickup_location_id:
            query = query.filter(models.Rental.pickup_location_id == filters.pickup_location_id)
        if filters.return_location_id:
            query = query.filter(models.Rental.return_location_id == filters.return_location_id)
        
        return query.order_by(desc(models.Rental.created_at)).offset(skip).limit(limit).all()
    
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
    
    def return_vehicle(self, db: Session, *, rental_id: int, return_data: Dict[str, Any]) -> Optional[models.Rental]:
        rental = db.query(models.Rental).filter(models.Rental.rental_id == rental_id).first()
        if rental:
            rental.actual_return_date = return_data.get('actual_return_date', datetime.now())
            rental.mileage_end = return_data.get('mileage_end')
            rental.fuel_level_end = return_data.get('fuel_level_end')
            rental.status = "Completed"
            rental.late_fees = return_data.get('late_fees', Decimal('0.00'))
            rental.damage_fees = return_data.get('damage_fees', Decimal('0.00'))
            
            # Update vehicle availability
            vehicle = db.query(models.Vehicle).filter(models.Vehicle.vehicle_id == rental.vehicle_id).first()
            if vehicle:
                vehicle.availability = True
                if rental.mileage_end:
                    vehicle.mileage = rental.mileage_end
            
            db.commit()
            db.refresh(rental)
        return rental
    
    def get_rental_revenue(self, db: Session, *, start_date: date, end_date: date) -> Decimal:
        result = db.query(func.sum(models.Rental.total_amount)).filter(
            and_(
                models.Rental.start_date >= start_date,
                models.Rental.start_date <= end_date,
                models.Rental.status == "Completed"
            )
        ).scalar()
        return result or Decimal('0.00')

# Reservation CRUD operations
class CRUDReservation(CRUDBase):
    def get_active_reservations(self, db: Session, *, skip: int = 0, limit: int = 100) -> List[models.Reservation]:
        return db.query(models.Reservation).filter(
            models.Reservation.status == "Active"
        ).offset(skip).limit(limit).all()
    
    def get_customer_reservations(self, db: Session, *, customer_id: int) -> List[models.Reservation]:
        return db.query(models.Reservation).filter(
            models.Reservation.customer_id == customer_id
        ).order_by(desc(models.Reservation.reservation_date)).all()
    
    def check_vehicle_availability(self, db: Session, *, vehicle_id: int, start_date: datetime, end_date: datetime) -> bool:
        conflicting_reservations = db.query(models.Reservation).filter(
            and_(
                models.Reservation.vehicle_id == vehicle_id,
                models.Reservation.status.in_(["Active", "Confirmed"]),
                or_(
                    and_(models.Reservation.reserved_start_date <= start_date, models.Reservation.reserved_end_date > start_date),
                    and_(models.Reservation.reserved_start_date < end_date, models.Reservation.reserved_end_date >= end_date),
                    and_(models.Reservation.reserved_start_date >= start_date, models.Reservation.reserved_end_date <= end_date)
                )
            )
        ).first()
        return conflicting_reservations is None
    
    def convert_to_rental(self, db: Session, *, reservation_id: int, rental_data: schema.RentalCreate) -> Optional[models.Rental]:
        reservation = db.query(models.Reservation).filter(models.Reservation.reservation_id == reservation_id).first()
        if reservation and reservation.status == "Confirmed":
            # Create rental
            rental = models.Rental(**rental_data.model_dump())
            db.add(rental)
            
            # Update reservation status
            reservation.status = "Converted"
            
            # Update vehicle availability
            vehicle = db.query(models.Vehicle).filter(models.Vehicle.vehicle_id == reservation.vehicle_id).first()
            if vehicle:
                vehicle.availability = False
            
            db.commit()
            db.refresh(rental)
            return rental
        return None

# Employee CRUD operations
class CRUDEmployee(CRUDBase):
    def get_by_email(self, db: Session, *, email: str) -> Optional[models.Employee]:
        return db.query(models.Employee).filter(models.Employee.email == email).first()
    
    def get_active_employees(self, db: Session, *, skip: int = 0, limit: int = 100) -> List[models.Employee]:
        return db.query(models.Employee).filter(
            models.Employee.is_active == True
        ).offset(skip).limit(limit).all()
    
    def get_by_role(self, db: Session, *, role: str) -> List[models.Employee]:
        return db.query(models.Employee).filter(
            and_(models.Employee.role == role, models.Employee.is_active == True)
        ).all()
    
    def get_by_location(self, db: Session, *, location_id: int) -> List[models.Employee]:
        return db.query(models.Employee).filter(
            and_(models.Employee.location_id == location_id, models.Employee.is_active == True)
        ).all()

# Location CRUD operations
class CRUDLocation(CRUDBase):
    def get_with_details(self, db: Session, location_id: int) -> Optional[models.Location]:
        return db.query(models.Location).options(
            joinedload(models.Location.manager),
            joinedload(models.Location.employees),
            joinedload(models.Location.vehicles)
        ).filter(models.Location.location_id == location_id).first()
    
    def get_by_city(self, db: Session, *, city: str) -> List[models.Location]:
        return db.query(models.Location).filter(models.Location.city.ilike(f"%{city}%")).all()

# Payment CRUD operations
class CRUDPayment(CRUDBase):
    def get_rental_payments(self, db: Session, *, rental_id: int) -> List[models.Payment]:
        return db.query(models.Payment).filter(
            models.Payment.rental_id == rental_id
        ).order_by(models.Payment.payment_date).all()
    
    def get_failed_payments(self, db: Session) -> List[models.Payment]:
        return db.query(models.Payment).filter(models.Payment.status == "Failed").all()
    
    def get_payments_by_date_range(self, db: Session, *, start_date: date, end_date: date) -> List[models.Payment]:
        return db.query(models.Payment).filter(
            and_(
                func.date(models.Payment.payment_date) >= start_date,
                func.date(models.Payment.payment_date) <= end_date,
                models.Payment.status == "Completed"
            )
        ).all()

# Insurance Plan CRUD operations
class CRUDInsurancePlan(CRUDBase):
    def get_active_plans(self, db: Session) -> List[models.InsurancePlan]:
        return db.query(models.InsurancePlan).filter(models.InsurancePlan.is_active == True).all()

# Incident Report CRUD operations
class CRUDIncidentReport(CRUDBase):
    def get_rental_incidents(self, db: Session, *, rental_id: int) -> List[models.IncidentReport]:
        return db.query(models.IncidentReport).filter(
            models.IncidentReport.rental_id == rental_id
        ).all()
    
    def get_open_incidents(self, db: Session) -> List[models.IncidentReport]:
        return db.query(models.IncidentReport).filter(
            models.IncidentReport.status.in_(["Open", "Under Review"])
        ).order_by(models.IncidentReport.incident_date).all()

# Maintenance Schedule CRUD operations
class CRUDMaintenanceSchedule(CRUDBase):
    def get_vehicle_maintenance(self, db: Session, *, vehicle_id: int) -> List[models.MaintenanceSchedule]:
        return db.query(models.MaintenanceSchedule).filter(
            models.MaintenanceSchedule.vehicle_id == vehicle_id
        ).order_by(desc(models.MaintenanceSchedule.scheduled_date)).all()
    
    def get_scheduled_maintenance(self, db: Session, *, target_date: date = None) -> List[models.MaintenanceSchedule]:
        if target_date is None:
            target_date = date.today()
        return db.query(models.MaintenanceSchedule).filter(
            and_(
                models.MaintenanceSchedule.scheduled_date <= target_date,
                models.MaintenanceSchedule.status == "Scheduled"
            )
        ).all()
    
    def get_mechanic_schedule(self, db: Session, *, mechanic_id: int, start_date: date, end_date: date) -> List[models.MaintenanceSchedule]:
        return db.query(models.MaintenanceSchedule).filter(
            and_(
                models.MaintenanceSchedule.assigned_mechanic == mechanic_id,
                models.MaintenanceSchedule.scheduled_date >= start_date,
                models.MaintenanceSchedule.scheduled_date <= end_date
            )
        ).order_by(models.MaintenanceSchedule.scheduled_date).all()

# Membership operations
class CRUDMembershipProfile(CRUDBase):
    def update_points(self, db: Session, *, customer_id: int, points_to_add: int) -> Optional[models.CustomerMembershipProfile]:
        profile = db.query(models.CustomerMembershipProfile).filter(
            models.CustomerMembershipProfile.customer_id == customer_id
        ).first()
        if profile:
            profile.points_balance += points_to_add
            profile.last_activity_date = date.today()
            db.commit()
            db.refresh(profile)
        return profile
    
    def update_spending(self, db: Session, *, customer_id: int, amount: Decimal) -> Optional[models.CustomerMembershipProfile]:
        profile = db.query(models.CustomerMembershipProfile).filter(
            models.CustomerMembershipProfile.customer_id == customer_id
        ).first()
        if profile:
            profile.lifetime_spending += amount
            profile.lifetime_rentals += 1
            profile.last_activity_date = date.today()
            db.commit()
            db.refresh(profile)
        return profile

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