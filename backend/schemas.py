from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional, List
from datetime import datetime, date
from decimal import Decimal

# Base schemas
class CustomerBase(BaseModel):
    first_name: str = Field(..., max_length=50)
    last_name: str = Field(..., max_length=50)
    email: EmailStr
    phone: str = Field(..., max_length=20)
    address: Optional[str] = None
    driver_license: str = Field(..., max_length=20)
    date_of_birth: Optional[date] = None

class CustomerCreate(CustomerBase):
    pass

class CustomerUpdate(BaseModel):
    first_name: Optional[str] = Field(None, max_length=50)
    last_name: Optional[str] = Field(None, max_length=50)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=20)
    address: Optional[str] = None
    driver_license: Optional[str] = Field(None, max_length=20)
    date_of_birth: Optional[date] = None

class Customer(CustomerBase):
    model_config = ConfigDict(from_attributes=True)
    
    customer_id: int
    created_at: datetime
    updated_at: datetime

# Membership Tier schemas
class MembershipTierBase(BaseModel):
    tier_name: str = Field(..., max_length=20)
    description: Optional[str] = None
    monthly_fee: Optional[Decimal] = None
    free_upgrades: Optional[int] = None
    bonus_point_rate: Optional[Decimal] = None

class MembershipTierCreate(MembershipTierBase):
    pass

class MembershipTier(MembershipTierBase):
    model_config = ConfigDict(from_attributes=True)

# Customer Membership Profile schemas
class CustomerMembershipProfileBase(BaseModel):
    membership_tier: str = "Standard"
    points_balance: int = 0
    tier_level: str = "Bronze"
    last_activity_date: Optional[date] = None
    lifetime_rentals: int = 0
    lifetime_spending: Decimal = Decimal('0.00')

class CustomerMembershipProfileCreate(CustomerMembershipProfileBase):
    customer_id: int

class CustomerMembershipProfileUpdate(BaseModel):
    membership_tier: Optional[str] = None
    points_balance: Optional[int] = None
    tier_level: Optional[str] = None
    last_activity_date: Optional[date] = None
    lifetime_rentals: Optional[int] = None
    lifetime_spending: Optional[Decimal] = None

class CustomerMembershipProfile(CustomerMembershipProfileBase):
    model_config = ConfigDict(from_attributes=True)
    
    profile_id: int
    customer_id: int
    join_date: date

# Customer Vehicle Preference schemas
class CustomerVehiclePreferenceBase(BaseModel):
    vehicle_type: str = Field(..., max_length=30)
    preference_score: Optional[int] = Field(None, ge=1, le=10)

class CustomerVehiclePreferenceCreate(CustomerVehiclePreferenceBase):
    customer_id: int

class CustomerVehiclePreference(CustomerVehiclePreferenceBase):
    model_config = ConfigDict(from_attributes=True)
    
    customer_id: int
    created_at: datetime

# Employee schemas
class EmployeeBase(BaseModel):
    first_name: str = Field(..., max_length=50)
    last_name: str = Field(..., max_length=50)
    email: EmailStr
    phone: str = Field(..., max_length=20)
    role: str = Field(..., max_length=30)
    hire_date: date
    salary: Optional[Decimal] = None
    location_id: Optional[int] = None
    manager_id: Optional[int] = None
    is_active: bool = True

class EmployeeCreate(EmployeeBase):
    pass

class EmployeeUpdate(BaseModel):
    first_name: Optional[str] = Field(None, max_length=50)
    last_name: Optional[str] = Field(None, max_length=50)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=20)
    role: Optional[str] = Field(None, max_length=30)
    salary: Optional[Decimal] = None
    location_id: Optional[int] = None
    manager_id: Optional[int] = None
    is_active: Optional[bool] = None

class Employee(EmployeeBase):
    model_config = ConfigDict(from_attributes=True)
    
    employee_id: int

# Location schemas
class LocationBase(BaseModel):
    name: str = Field(..., max_length=100)
    address: str
    city: str = Field(..., max_length=50)
    state: str = Field(..., max_length=50)
    zip_code: str = Field(..., max_length=10)
    phone: Optional[str] = Field(None, max_length=20)
    operating_hours: Optional[str] = Field(None, max_length=100)
    manager_id: Optional[int] = None

class LocationCreate(LocationBase):
    pass

class LocationUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    address: Optional[str] = None
    city: Optional[str] = Field(None, max_length=50)
    state: Optional[str] = Field(None, max_length=50)
    zip_code: Optional[str] = Field(None, max_length=10)
    phone: Optional[str] = Field(None, max_length=20)
    operating_hours: Optional[str] = Field(None, max_length=100)
    manager_id: Optional[int] = None

class Location(LocationBase):
    model_config = ConfigDict(from_attributes=True)
    
    location_id: int

# Vehicle schemas
class VehicleBase(BaseModel):
    model: str = Field(..., max_length=50)
    make: str = Field(..., max_length=50)
    license_plate: str = Field(..., max_length=10)
    year: int
    availability: bool = True
    daily_rate: Decimal
    mileage: int = 0
    fuel_type: str = Field(default="Gasoline", max_length=20)
    transmission: str = Field(default="Automatic", max_length=20)
    seating_capacity: int = 5
    location_id: Optional[int] = None

class VehicleCreate(VehicleBase):
    pass

class VehicleUpdate(BaseModel):
    model: Optional[str] = Field(None, max_length=50)
    make: Optional[str] = Field(None, max_length=50)
    license_plate: Optional[str] = Field(None, max_length=10)
    year: Optional[int] = None
    availability: Optional[bool] = None
    daily_rate: Optional[Decimal] = None
    mileage: Optional[int] = None
    fuel_type: Optional[str] = Field(None, max_length=20)
    transmission: Optional[str] = Field(None, max_length=20)
    seating_capacity: Optional[int] = None
    location_id: Optional[int] = None

class Vehicle(VehicleBase):
    model_config = ConfigDict(from_attributes=True)
    
    vehicle_id: int
    created_at: datetime

# Vehicle Feature schemas
class VehicleFeatureBase(BaseModel):
    name: str = Field(..., max_length=50)
    description: Optional[str] = None
    category: Optional[str] = Field(None, max_length=30)

class VehicleFeatureCreate(VehicleFeatureBase):
    pass

class VehicleFeature(VehicleFeatureBase):
    model_config = ConfigDict(from_attributes=True)
    
    feature_id: int

# Vehicle Feature Mapping schemas
class VehicleFeatureMappingCreate(BaseModel):
    vehicle_id: int
    feature_id: int

class VehicleFeatureMapping(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    vehicle_id: int
    feature_id: int

# Vehicle Maintenance Record schemas
class VehicleMaintenanceRecordBase(BaseModel):
    last_service_date: Optional[date] = None
    next_service_due: Optional[date] = None
    total_maintenance_cost: Decimal = Decimal('0.00')
    service_history: Optional[str] = None
    current_condition: str = "Good"
    maintenance_alerts: Optional[str] = None

class VehicleMaintenanceRecordCreate(VehicleMaintenanceRecordBase):
    vehicle_id: int

class VehicleMaintenanceRecordUpdate(BaseModel):
    last_service_date: Optional[date] = None
    next_service_due: Optional[date] = None
    total_maintenance_cost: Optional[Decimal] = None
    service_history: Optional[str] = None
    current_condition: Optional[str] = None
    maintenance_alerts: Optional[str] = None

class VehicleMaintenanceRecord(VehicleMaintenanceRecordBase):
    model_config = ConfigDict(from_attributes=True)
    
    maintenance_id: int
    vehicle_id: int

# Reservation schemas
class ReservationBase(BaseModel):
    customer_id: int
    vehicle_id: int
    pickup_location_id: int
    return_location_id: int
    reserved_start_date: datetime
    reserved_end_date: datetime
    status: str = "Active"
    special_requests: Optional[str] = None
    estimated_total: Optional[Decimal] = None

class ReservationCreate(ReservationBase):
    pass

class ReservationUpdate(BaseModel):
    vehicle_id: Optional[int] = None
    pickup_location_id: Optional[int] = None
    return_location_id: Optional[int] = None
    reserved_start_date: Optional[datetime] = None
    reserved_end_date: Optional[datetime] = None
    status: Optional[str] = None
    special_requests: Optional[str] = None
    estimated_total: Optional[Decimal] = None

class Reservation(ReservationBase):
    model_config = ConfigDict(from_attributes=True)
    
    reservation_id: int
    reservation_date: datetime

# Rental schemas
class RentalBase(BaseModel):
    customer_id: int
    vehicle_id: int
    employee_id: Optional[int] = None
    pickup_location_id: int
    return_location_id: int
    start_date: datetime
    end_date: datetime
    actual_return_date: Optional[datetime] = None
    daily_rate: Decimal
    total_amount: Decimal
    security_deposit: Decimal = Decimal('200.00')
    mileage_start: Optional[int] = None
    mileage_end: Optional[int] = None
    fuel_level_start: Optional[Decimal] = None
    fuel_level_end: Optional[Decimal] = None
    status: str = "Active"
    discount_applied: Decimal = Decimal('0.00')
    late_fees: Decimal = Decimal('0.00')
    damage_fees: Decimal = Decimal('0.00')

class RentalCreate(RentalBase):
    pass

class RentalUpdate(BaseModel):
    employee_id: Optional[int] = None
    pickup_location_id: Optional[int] = None
    return_location_id: Optional[int] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    actual_return_date: Optional[datetime] = None
    daily_rate: Optional[Decimal] = None
    total_amount: Optional[Decimal] = None
    security_deposit: Optional[Decimal] = None
    mileage_start: Optional[int] = None
    mileage_end: Optional[int] = None
    fuel_level_start: Optional[Decimal] = None
    fuel_level_end: Optional[Decimal] = None
    status: Optional[str] = None
    discount_applied: Optional[Decimal] = None
    late_fees: Optional[Decimal] = None
    damage_fees: Optional[Decimal] = None

class Rental(RentalBase):
    model_config = ConfigDict(from_attributes=True)
    
    rental_id: int
    created_at: datetime

# Payment schemas
class PaymentBase(BaseModel):
    rental_id: int
    amount: Decimal
    method: str = Field(..., max_length=20)
    transaction_id: Optional[str] = Field(None, max_length=100)
    status: str = "Completed"
    payment_type: str = Field(..., max_length=20)

class PaymentCreate(PaymentBase):
    pass

class PaymentUpdate(BaseModel):
    amount: Optional[Decimal] = None
    method: Optional[str] = Field(None, max_length=20)
    transaction_id: Optional[str] = Field(None, max_length=100)
    status: Optional[str] = None
    payment_type: Optional[str] = Field(None, max_length=20)

class Payment(PaymentBase):
    model_config = ConfigDict(from_attributes=True)
    
    payment_id: int
    payment_date: datetime

# Insurance Plan schemas
class InsurancePlanBase(BaseModel):
    name: str = Field(..., max_length=100)
    description: Optional[str] = None
    daily_cost: Decimal
    coverage_amount: Decimal
    deductible: Decimal
    is_active: bool = True

class InsurancePlanCreate(InsurancePlanBase):
    pass

class InsurancePlanUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    daily_cost: Optional[Decimal] = None
    coverage_amount: Optional[Decimal] = None
    deductible: Optional[Decimal] = None
    is_active: Optional[bool] = None

class InsurancePlan(InsurancePlanBase):
    model_config = ConfigDict(from_attributes=True)
    
    plan_id: int

# Rental Insurance schemas
class RentalInsuranceBase(BaseModel):
    start_date: date
    end_date: date
    premium_amount: Decimal

class RentalInsuranceCreate(RentalInsuranceBase):
    rental_id: int
    plan_id: int

class RentalInsurance(RentalInsuranceBase):
    model_config = ConfigDict(from_attributes=True)
    
    rental_id: int
    plan_id: int

# Incident Report schemas
class IncidentReportBase(BaseModel):
    rental_id: int
    reported_by: Optional[int] = None
    incident_date: datetime
    incident_type: str = Field(..., max_length=30)
    description: str
    estimated_cost: Optional[Decimal] = None
    status: str = "Open"
    photos: Optional[str] = None
    police_report_number: Optional[str] = Field(None, max_length=50)

class IncidentReportCreate(IncidentReportBase):
    pass

class IncidentReportUpdate(BaseModel):
    reported_by: Optional[int] = None
    incident_date: Optional[datetime] = None
    incident_type: Optional[str] = Field(None, max_length=30)
    description: Optional[str] = None
    estimated_cost: Optional[Decimal] = None
    status: Optional[str] = None
    photos: Optional[str] = None
    police_report_number: Optional[str] = Field(None, max_length=50)

class IncidentReport(IncidentReportBase):
    model_config = ConfigDict(from_attributes=True)
    
    incident_id: int

# Maintenance Schedule schemas
class MaintenanceScheduleBase(BaseModel):
    vehicle_id: int
    maintenance_type: str = Field(..., max_length=50)
    scheduled_date: date
    completed_date: Optional[date] = None
    assigned_mechanic: Optional[int] = None
    cost: Optional[Decimal] = None
    notes: Optional[str] = None
    status: str = "Scheduled"

class MaintenanceScheduleCreate(MaintenanceScheduleBase):
    pass

class MaintenanceScheduleUpdate(BaseModel):
    maintenance_type: Optional[str] = Field(None, max_length=50)
    scheduled_date: Optional[date] = None
    completed_date: Optional[date] = None
    assigned_mechanic: Optional[int] = None
    cost: Optional[Decimal] = None
    notes: Optional[str] = None
    status: Optional[str] = None

class MaintenanceSchedule(MaintenanceScheduleBase):
    model_config = ConfigDict(from_attributes=True)
    
    schedule_id: int

# Enhanced schemas with relationships (for detailed responses)
class CustomerWithProfile(Customer):
    membership_profile: Optional[CustomerMembershipProfile] = None
    vehicle_preferences: List[CustomerVehiclePreference] = []

class VehicleWithFeatures(Vehicle):
    features: List[VehicleFeature] = []
    maintenance_record: Optional[VehicleMaintenanceRecord] = None

class RentalWithDetails(Rental):
    customer: Optional[Customer] = None
    vehicle: Optional[Vehicle] = None
    employee: Optional[Employee] = None
    pickup_location: Optional[Location] = None
    return_location: Optional[Location] = None
    payments: List[Payment] = []
    incident_reports: List[IncidentReport] = []

class LocationWithEmployees(Location):
    manager: Optional[Employee] = None
    employees: List[Employee] = []
    vehicles: List[Vehicle] = []

class EmployeeWithLocation(Employee):
    location: Optional[Location] = None
    manager: Optional[Employee] = None

# Response schemas for common operations
class CustomerResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Customer] = None

class VehicleResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Vehicle] = None

class RentalResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Rental] = None

class ListResponse(BaseModel):
    success: bool
    message: str
    data: List[dict] = []
    total: int = 0
    page: int = 1
    per_page: int = 10

# Query parameters for filtering and pagination
class PaginationParams(BaseModel):
    page: int = Field(1, ge=1)
    per_page: int = Field(10, ge=1, le=100)

class VehicleFilters(BaseModel):
    make: Optional[str] = None
    model: Optional[str] = None
    fuel_type: Optional[str] = None
    transmission: Optional[str] = None
    min_year: Optional[int] = None
    max_year: Optional[int] = None
    availability: Optional[bool] = None
    location_id: Optional[int] = None
    min_daily_rate: Optional[Decimal] = None
    max_daily_rate: Optional[Decimal] = None

class RentalFilters(BaseModel):
    customer_id: Optional[int] = None
    vehicle_id: Optional[int] = None
    status: Optional[str] = None
    start_date_from: Optional[date] = None
    start_date_to: Optional[date] = None
    pickup_location_id: Optional[int] = None
    return_location_id: Optional[int] = None