// API Response Types
export interface ApiResponse<T> {
  success: boolean;
  message: string;
  data?: T;
}

export interface ListResponse<T> {
  success: boolean;
  message: string;
  data: T[];
  total: number;
  page: number;
  per_page: number;
}

// Customer Types
export interface Customer {
  customer_id: number;
  first_name: string;
  last_name: string;
  email: string;
  phone: string;
  address?: string;
  driver_license: string;
  date_of_birth?: string;
  created_at: string;
  updated_at: string;
}

export interface CustomerCreate {
  first_name: string;
  last_name: string;
  email: string;
  phone: string;
  address?: string;
  driver_license: string;
  date_of_birth?: string;
}

export interface CustomerWithProfile extends Customer {
  membership_profile?: CustomerMembershipProfile;
  vehicle_preferences: CustomerVehiclePreference[];
}

// Membership Types
export interface MembershipTier {
  tier_name: string;
  description?: string;
  monthly_fee?: number;
  free_upgrades?: number;
  bonus_point_rate?: number;
}

export interface CustomerMembershipProfile {
  profile_id: number;
  customer_id: number;
  membership_tier: string;
  points_balance: number;
  tier_level: string;
  join_date: string;
  last_activity_date?: string;
  lifetime_rentals: number;
  lifetime_spending: number;
}

export interface CustomerVehiclePreference {
  customer_id: number;
  vehicle_type: string;
  preference_score?: number;
  created_at: string;
}

// Vehicle Types
export interface Vehicle {
  vehicle_id: number;
  model: string;
  make: string;
  license_plate: string;
  year: number;
  availability: boolean;
  daily_rate: number;
  mileage: number;
  fuel_type: string;
  transmission: string;
  seating_capacity: number;
  location_id?: number;
  created_at: string;
}

export interface VehicleCreate {
  model: string;
  make: string;
  license_plate: string;
  year: number;
  availability?: boolean;
  daily_rate: number;
  mileage?: number;
  fuel_type?: string;
  transmission?: string;
  seating_capacity?: number;
  location_id?: number;
}

export interface VehicleWithFeatures extends Vehicle {
  features: VehicleFeature[];
  maintenance_record?: VehicleMaintenanceRecord;
}

export interface VehicleFeature {
  feature_id: number;
  name: string;
  description?: string;
  category?: string;
}

export interface VehicleMaintenanceRecord {
  maintenance_id: number;
  vehicle_id: number;
  last_service_date?: string;
  next_service_due?: string;
  total_maintenance_cost: number;
  service_history?: string;
  current_condition: string;
  maintenance_alerts?: string;
}

export interface VehicleFilters {
  make?: string;
  model?: string;
  fuel_type?: string;
  transmission?: string;
  min_year?: number;
  max_year?: number;
  availability?: boolean;
  location_id?: number;
  min_daily_rate?: number;
  max_daily_rate?: number;
}

// Location Types
export interface Location {
  location_id: number;
  name: string;
  address: string;
  city: string;
  state: string;
  zip_code: string;
  phone?: string;
  operating_hours?: string;
  manager_id?: number;
}

export interface LocationWithEmployees extends Location {
  manager?: Employee;
  employees: Employee[];
  vehicles: Vehicle[];
}

// Employee Types
export interface Employee {
  employee_id: number;
  first_name: string;
  last_name: string;
  email: string;
  phone: string;
  role: string;
  hire_date: string;
  salary?: number;
  location_id?: number;
  manager_id?: number;
  is_active: boolean;
}

export interface EmployeeCreate {
  first_name: string;
  last_name: string;
  email: string;
  phone: string;
  role: string;
  hire_date: string;
  salary?: number;
  location_id?: number;
  manager_id?: number;
  is_active?: boolean;
}

// Reservation Types
export interface Reservation {
  reservation_id: number;
  customer_id: number;
  vehicle_id: number;
  pickup_location_id: number;
  return_location_id: number;
  reserved_start_date: string;
  reserved_end_date: string;
  reservation_date: string;
  status: string;
  special_requests?: string;
  estimated_total?: number;
}

export interface ReservationCreate {
  customer_id: number;
  vehicle_id: number;
  pickup_location_id: number;
  return_location_id: number;
  reserved_start_date: string;
  reserved_end_date: string;
  status?: string;
  special_requests?: string;
  estimated_total?: number;
}

// Rental Types
export interface Rental {
  rental_id: number;
  customer_id: number;
  vehicle_id: number;
  employee_id?: number;
  pickup_location_id: number;
  return_location_id: number;
  start_date: string;
  end_date: string;
  actual_return_date?: string;
  daily_rate: number;
  total_amount: number;
  security_deposit: number;
  mileage_start?: number;
  mileage_end?: number;
  fuel_level_start?: number;
  fuel_level_end?: number;
  status: string;
  discount_applied: number;
  late_fees: number;
  damage_fees: number;
  created_at: string;
}

export interface RentalWithDetails extends Rental {
  customer?: Customer;
  vehicle?: Vehicle;
  employee?: Employee;
  pickup_location?: Location;
  return_location?: Location;
  payments: Payment[];
  incident_reports: IncidentReport[];
}

export interface RentalCreate {
  customer_id: number;
  vehicle_id: number;
  employee_id?: number;
  pickup_location_id: number;
  return_location_id: number;
  start_date: string;
  end_date: string;
  daily_rate: number;
  total_amount: number;
  security_deposit?: number;
  mileage_start?: number;
  fuel_level_start?: number;
  status?: string;
}

export interface RentalFilters {
  customer_id?: number;
  vehicle_id?: number;
  status?: string;
  start_date_from?: string;
  start_date_to?: string;
  pickup_location_id?: number;
  return_location_id?: number;
}

// Payment Types
export interface Payment {
  payment_id: number;
  rental_id: number;
  payment_date: string;
  amount: number;
  method: string;
  transaction_id?: string;
  status: string;
  payment_type: string;
}

export interface PaymentCreate {
  rental_id: number;
  amount: number;
  method: string;
  transaction_id?: string;
  status?: string;
  payment_type: string;
}

// Insurance Types
export interface InsurancePlan {
  plan_id: number;
  name: string;
  description?: string;
  daily_cost: number;
  coverage_amount: number;
  deductible: number;
  is_active: boolean;
}

// Incident Types
export interface IncidentReport {
  incident_id: number;
  rental_id: number;
  reported_by?: number;
  incident_date: string;
  incident_type: string;
  description: string;
  estimated_cost?: number;
  status: string;
  photos?: string;
  police_report_number?: string;
}

export interface IncidentReportCreate {
  rental_id: number;
  reported_by?: number;
  incident_date: string;
  incident_type: string;
  description: string;
  estimated_cost?: number;
  status?: string;
  photos?: string;
  police_report_number?: string;
}

// Maintenance Types
export interface MaintenanceSchedule {
  schedule_id: number;
  vehicle_id: number;
  maintenance_type: string;
  scheduled_date: string;
  completed_date?: string;
  assigned_mechanic?: number;
  cost?: number;
  notes?: string;
  status: string;
}

export interface MaintenanceScheduleCreate {
  vehicle_id: number;
  maintenance_type: string;
  scheduled_date: string;
  assigned_mechanic?: number;
  cost?: number;
  notes?: string;
  status?: string;
}

// Dashboard Types
export interface DashboardStats {
  total_customers: number;
  total_vehicles: number;
  active_rentals: number;
  total_revenue: number;
  available_vehicles: number;
  overdue_rentals: number;
}

export interface RevenueReport {
  start_date: string;
  end_date: string;
  total_revenue: number;
}