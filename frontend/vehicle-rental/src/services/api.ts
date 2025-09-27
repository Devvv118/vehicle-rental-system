import type { 
  Customer, 
  CustomerCreate, 
  CustomerWithProfile,
  Vehicle, 
  VehicleCreate, 
  VehicleWithFeatures,
  VehicleFilters,
  Rental, 
  RentalCreate, 
  RentalWithDetails,
  RentalFilters,
  Reservation, 
  ReservationCreate,
  Employee,
  EmployeeCreate,
  Location,
  LocationWithEmployees,
  Payment,
  PaymentCreate,
  InsurancePlan,
  IncidentReport,
  IncidentReportCreate,
  MaintenanceSchedule,
  MaintenanceScheduleCreate,
  MembershipTier,
  VehicleFeature,
  RevenueReport
} from '../types';

const API_BASE_URL = 'http://localhost:8000';

// class ApiError extends Error {
//   constructor(public status: number, message: string) {
//     super(message);
//     this.name = 'ApiError';
//   }
// }

class ApiError extends Error {
  public status: number; // declare the property

  constructor(status: number, message: string) {
    super(message);
    this.status = status; // assign in constructor
    this.name = 'ApiError';
  }
}


async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const errorText = await response.text();
    throw new ApiError(response.status, errorText || response.statusText);
  }
  return response.json();
}

async function apiRequest<T>(
  endpoint: string, 
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  const response = await fetch(url, {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  });
  return handleResponse<T>(response);
}

// Customer API
export const customerApi = {
  getAll: (skip = 0, limit = 100): Promise<Customer[]> =>
    apiRequest(`/customers/?skip=${skip}&limit=${limit}`),

  getById: (id: number): Promise<CustomerWithProfile> =>
    apiRequest(`/customers/${id}`),
  
  create: (customer: CustomerCreate): Promise<Customer> =>
    apiRequest('/customers/', {
      method: 'POST',
      body: JSON.stringify(customer),
    }),
  
  update: (id: number, customer: Partial<CustomerCreate>): Promise<Customer> =>
    apiRequest(`/customers/${id}`, {
      method: 'PUT',
      body: JSON.stringify(customer),
    }),
  
  delete: (id: number): Promise<{ message: string }> =>
    apiRequest(`/customers/${id}`, { method: 'DELETE' }),
  
  search: (query: string, skip = 0, limit = 100): Promise<Customer[]> =>
    apiRequest(`/customers/search/?q=${encodeURIComponent(query)}&skip=${skip}&limit=${limit}`),
  
  getTopCustomers: (limit = 10): Promise<Customer[]> =>
    apiRequest(`/customers/top/spending?limit=${limit}`),
};

// Vehicle API
export const vehicleApi = {
  getAll: (skip = 0, limit = 100): Promise<Vehicle[]> =>
    apiRequest(`/vehicles/?skip=${skip}&limit=${limit}`),
  
  getAvailable: (skip = 0, limit = 100): Promise<Vehicle[]> =>
    apiRequest(`/vehicles/available?skip=${skip}&limit=${limit}`),
  
  getById: (id: number): Promise<VehicleWithFeatures> =>
    apiRequest(`/vehicles/${id}`),
  
  create: (vehicle: VehicleCreate): Promise<Vehicle> =>
    apiRequest('/vehicles/', {
      method: 'POST',
      body: JSON.stringify(vehicle),
    }),
  
  update: (id: number, vehicle: Partial<VehicleCreate>): Promise<Vehicle> =>
    apiRequest(`/vehicles/${id}`, {
      method: 'PUT',
      body: JSON.stringify(vehicle),
    }),
  
  updateAvailability: (id: number, available: boolean): Promise<{ message: string }> =>
    apiRequest(`/vehicles/${id}/availability`, {
      method: 'PATCH',
      body: JSON.stringify({ available }),
    }),
  
  filter: (filters: VehicleFilters, skip = 0, limit = 100): Promise<Vehicle[]> => {
    const params = new URLSearchParams();
    Object.entries(filters).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        params.append(key, value.toString());
      }
    });
    params.append('skip', skip.toString());
    params.append('limit', limit.toString());
    return apiRequest(`/vehicles/filter/?${params}`);
  },
  
  getNeedingMaintenance: (): Promise<Vehicle[]> =>
    apiRequest('/vehicles/maintenance/needed'),
};

// Rental API
export const rentalApi = {
  getAll: (skip = 0, limit = 100): Promise<Rental[]> =>
    apiRequest(`/rentals/?skip=${skip}&limit=${limit}`),
  
  getActive: (skip = 0, limit = 100): Promise<Rental[]> =>
    apiRequest(`/rentals/active?skip=${skip}&limit=${limit}`),
  
  getOverdue: (): Promise<Rental[]> =>
    apiRequest('/rentals/overdue'),
  
  getById: (id: number): Promise<RentalWithDetails> =>
    apiRequest(`/rentals/${id}`),
  
  getByCustomer: (customerId: number, skip = 0, limit = 100): Promise<Rental[]> =>
    apiRequest(`/rentals/customer/${customerId}?skip=${skip}&limit=${limit}`),
  
  create: (rental: RentalCreate): Promise<Rental> =>
    apiRequest('/rentals/', {
      method: 'POST',
      body: JSON.stringify(rental),
    }),
  
  filter: (filters: RentalFilters, skip = 0, limit = 100): Promise<Rental[]> => {
    const params = new URLSearchParams();
    Object.entries(filters).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        params.append(key, value.toString());
      }
    });
    params.append('skip', skip.toString());
    params.append('limit', limit.toString());
    return apiRequest(`/rentals/filter/?${params}`);
  },
  
  returnVehicle: (
    id: number, 
    returnData: {
      mileage_end?: number;
      fuel_level_end?: number;
      late_fees?: number;
      damage_fees?: number;
    }
  ): Promise<Rental> =>
    apiRequest(`/rentals/${id}/return`, {
      method: 'PATCH',
      body: JSON.stringify(returnData),
    }),
  
  getRevenue: (startDate: string, endDate: string): Promise<RevenueReport> =>
    apiRequest(`/rentals/revenue/report?start_date=${startDate}&end_date=${endDate}`),
};

// Reservation API
export const reservationApi = {
  getAll: (skip = 0, limit = 100): Promise<Reservation[]> =>
    apiRequest(`/reservations/?skip=${skip}&limit=${limit}`),
  
  getActive: (skip = 0, limit = 100): Promise<Reservation[]> =>
    apiRequest(`/reservations/active?skip=${skip}&limit=${limit}`),
  
  getById: (id: number): Promise<Reservation> =>
    apiRequest(`/reservations/${id}`),
  
  getByCustomer: (customerId: number): Promise<Reservation[]> =>
    apiRequest(`/reservations/customer/${customerId}`),
  
  create: (reservation: ReservationCreate): Promise<Reservation> =>
    apiRequest('/reservations/', {
      method: 'POST',
      body: JSON.stringify(reservation),
    }),
  
  update: (id: number, reservation: Partial<ReservationCreate>): Promise<Reservation> =>
    apiRequest(`/reservations/${id}`, {
      method: 'PUT',
      body: JSON.stringify(reservation),
    }),
  
  convertToRental: (id: number, rentalData: RentalCreate): Promise<Rental> =>
    apiRequest(`/reservations/${id}/convert`, {
      method: 'POST',
      body: JSON.stringify(rentalData),
    }),
};

// Employee API
export const employeeApi = {
  getAll: (skip = 0, limit = 100): Promise<Employee[]> =>
    apiRequest(`/employees/?skip=${skip}&limit=${limit}`),
  
  getActive: (skip = 0, limit = 100): Promise<Employee[]> =>
    apiRequest(`/employees/active?skip=${skip}&limit=${limit}`),
  
  getById: (id: number): Promise<Employee> =>
    apiRequest(`/employees/${id}`),
  
  getByRole: (role: string): Promise<Employee[]> =>
    apiRequest(`/employees/role/${role}`),
  
  getByLocation: (locationId: number): Promise<Employee[]> =>
    apiRequest(`/employees/location/${locationId}`),
  
  create: (employee: EmployeeCreate): Promise<Employee> =>
    apiRequest('/employees/', {
      method: 'POST',
      body: JSON.stringify(employee),
    }),
};

// Location API
export const locationApi = {
  getAll: (skip = 0, limit = 100): Promise<Location[]> =>
    apiRequest(`/locations/?skip=${skip}&limit=${limit}`),
  
  getById: (id: number): Promise<LocationWithEmployees> =>
    apiRequest(`/locations/${id}`),
  
  getByCity: (city: string): Promise<Location[]> =>
    apiRequest(`/locations/city/${city}`),
  
  create: (location: Omit<Location, 'location_id'>): Promise<Location> =>
    apiRequest('/locations/', {
      method: 'POST',
      body: JSON.stringify(location),
    }),
};

// Payment API
export const paymentApi = {
  create: (payment: PaymentCreate): Promise<Payment> =>
    apiRequest('/payments/', {
      method: 'POST',
      body: JSON.stringify(payment),
    }),
  
  getByRental: (rentalId: number): Promise<Payment[]> =>
    apiRequest(`/payments/rental/${rentalId}`),
  
  getFailed: (): Promise<Payment[]> =>
    apiRequest('/payments/failed'),
  
  getReport: (startDate: string, endDate: string): Promise<{
    start_date: string;
    end_date: string;
    total_payments: number;
    total_amount: number;
    payments: Payment[];
  }> =>
    apiRequest(`/payments/report?start_date=${startDate}&end_date=${endDate}`),
};

// Insurance API
export const insuranceApi = {
  getAll: (): Promise<InsurancePlan[]> =>
    apiRequest('/insurance-plans/'),
  
  getActive: (): Promise<InsurancePlan[]> =>
    apiRequest('/insurance-plans/active'),
  
  create: (plan: Omit<InsurancePlan, 'plan_id'>): Promise<InsurancePlan> =>
    apiRequest('/insurance-plans/', {
      method: 'POST',
      body: JSON.stringify(plan),
    }),
};

// Incident API
export const incidentApi = {
  getAll: (skip = 0, limit = 100): Promise<IncidentReport[]> =>
    apiRequest(`/incidents/?skip=${skip}&limit=${limit}`),
  
  getByRental: (rentalId: number): Promise<IncidentReport[]> =>
    apiRequest(`/incidents/rental/${rentalId}`),
  
  getOpen: (): Promise<IncidentReport[]> =>
    apiRequest('/incidents/open'),
  
  create: (incident: IncidentReportCreate): Promise<IncidentReport> =>
    apiRequest('/incidents/', {
      method: 'POST',
      body: JSON.stringify(incident),
    }),
};

// Maintenance API
export const maintenanceApi = {
  create: (maintenance: MaintenanceScheduleCreate): Promise<MaintenanceSchedule> =>
    apiRequest('/maintenance/', {
      method: 'POST',
      body: JSON.stringify(maintenance),
    }),
  
  getByVehicle: (vehicleId: number): Promise<MaintenanceSchedule[]> =>
    apiRequest(`/maintenance/vehicle/${vehicleId}`),
  
  getScheduled: (targetDate?: string): Promise<MaintenanceSchedule[]> => {
    const params = targetDate ? `?target_date=${targetDate}` : '';
    return apiRequest(`/maintenance/scheduled${params}`);
  },
  
  getByMechanic: (
    mechanicId: number, 
    startDate: string, 
    endDate: string
  ): Promise<MaintenanceSchedule[]> =>
    apiRequest(`/maintenance/mechanic/${mechanicId}?start_date=${startDate}&end_date=${endDate}`),
};

// Membership API
export const membershipApi = {
  updatePoints: (customerId: number, pointsToAdd: number): Promise<{ message: string }> =>
    apiRequest(`/membership/${customerId}/points`, {
      method: 'PATCH',
      body: JSON.stringify({ points_to_add: pointsToAdd }),
    }),
  
  getTiers: (): Promise<MembershipTier[]> =>
    apiRequest('/membership-tiers/'),
};

// Vehicle Features API
export const vehicleFeaturesApi = {
  getAll: (): Promise<VehicleFeature[]> =>
    apiRequest('/vehicle-features/'),
  
  create: (feature: Omit<VehicleFeature, 'feature_id'>): Promise<VehicleFeature> =>
    apiRequest('/vehicle-features/', {
      method: 'POST',
      body: JSON.stringify(feature),
    }),
};

export { ApiError };