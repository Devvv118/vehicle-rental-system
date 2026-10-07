// import React from 'react';

// const RentalForm: React.FC = () => {
//   return <div><h1>New Rental</h1><p>Under construction</p></div>;
// };

// export default RentalForm;

import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { rentalApi, customerApi, vehicleApi, locationApi, employeeApi } from '../services/api';
import type { RentalCreate, Customer, Vehicle, Location, Employee } from '../types';

const RentalForm: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  
  const [formData, setFormData] = useState<RentalCreate>({
    customer_id: parseInt(searchParams.get('customer_id') || '0') || 0,
    vehicle_id: parseInt(searchParams.get('vehicle_id') || '0') || 0,
    employee_id: undefined,
    pickup_location_id: 0,
    return_location_id: 0,
    start_date: '',
    end_date: '',
    daily_rate: 0,
    total_amount: 0,
    security_deposit: 200.00,
    mileage_start: undefined,
    fuel_level_start: undefined,
    status: 'Active',
  });

  const [customers, setCustomers] = useState<Customer[]>([]);
  const [vehicles, setVehicles] = useState<Vehicle[]>([]);
  const [locations, setLocations] = useState<Location[]>([]);
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [selectedVehicle, setSelectedVehicle] = useState<Vehicle | null>(null);
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [rentalDays, setRentalDays] = useState(0);

  useEffect(() => {
    fetchFormData();
  }, []);

  useEffect(() => {
    calculateTotalAmount();
  }, [formData.start_date, formData.end_date, formData.daily_rate, formData.vehicle_id]);

  const fetchFormData = async () => {
    try {
      const [customersData, vehiclesData, locationsData, employeesData] = await Promise.all([
        customerApi.getAll(0, 1000),
        vehicleApi.getAvailable(0, 1000),
        locationApi.getAll(0, 1000),
        employeeApi.getActive(0, 1000),
      ]);

      setCustomers(customersData);
      setVehicles(vehiclesData);
      setLocations(locationsData);
      setEmployees(employeesData);

      // Pre-select vehicle if passed in URL
      const vehicleId = parseInt(searchParams.get('vehicle_id') || '0');
      if (vehicleId) {
        const vehicle = vehiclesData.find(v => v.vehicle_id === vehicleId);
        if (vehicle) {
          setSelectedVehicle(vehicle);
          setFormData(prev => ({
            ...prev,
            vehicle_id: vehicle.vehicle_id,
            daily_rate: vehicle.daily_rate,
            mileage_start: vehicle.mileage,
          }));
        }
      }
    } catch (err) {
      console.error('Error fetching form data:', err);
      setSubmitError('Failed to load form data');
    }
  };

  const calculateTotalAmount = () => {
    if (formData.start_date && formData.end_date && formData.daily_rate > 0) {
      const start = new Date(formData.start_date);
      const end = new Date(formData.end_date);
      const days = Math.ceil((end.getTime() - start.getTime()) / (1000 * 60 * 60 * 24));
      
      if (days > 0) {
        setRentalDays(days);
        const total = days * formData.daily_rate;
        setFormData(prev => ({
          ...prev,
          total_amount: total,
        }));
      } else {
        setRentalDays(0);
      }
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value, type } = e.target;
    
    let processedValue: any = value;
    
    if (type === 'number') {
      processedValue = value === '' ? 0 : parseFloat(value);
    }

    setFormData(prev => ({
      ...prev,
      [name]: processedValue,
    }));

    // Handle vehicle selection
    if (name === 'vehicle_id') {
      const vehicleId = parseInt(value);
      const vehicle = vehicles.find(v => v.vehicle_id === vehicleId);
      if (vehicle) {
        setSelectedVehicle(vehicle);
        setFormData(prev => ({
          ...prev,
          vehicle_id: vehicle.vehicle_id,
          daily_rate: vehicle.daily_rate,
          mileage_start: vehicle.mileage,
          pickup_location_id: vehicle.location_id || prev.pickup_location_id,
        }));
      }
    }

    // Clear error when user starts typing
    if (errors[name]) {
      setErrors(prev => ({
        ...prev,
        [name]: '',
      }));
    }
  };

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (formData.customer_id === 0) {
      newErrors.customer_id = 'Please select a customer';
    }

    if (formData.vehicle_id === 0) {
      newErrors.vehicle_id = 'Please select a vehicle';
    }

    if (formData.pickup_location_id === 0) {
      newErrors.pickup_location_id = 'Please select a pickup location';
    }

    if (formData.return_location_id === 0) {
      newErrors.return_location_id = 'Please select a return location';
    }

    if (!formData.start_date) {
      newErrors.start_date = 'Start date is required';
    }

    if (!formData.end_date) {
      newErrors.end_date = 'End date is required';
    }

    if (formData.start_date && formData.end_date) {
      const start = new Date(formData.start_date);
      const end = new Date(formData.end_date);
      
      if (end <= start) {
        newErrors.end_date = 'End date must be after start date';
      }
    }

    if (formData.daily_rate <= 0) {
      newErrors.daily_rate = 'Daily rate must be greater than 0';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateForm()) {
      return;
    }

    try {
      setLoading(true);
      setSubmitError(null);

      await rentalApi.create(formData);
      navigate('/rentals');
    } catch (err: any) {
      console.error('Error creating rental:', err);
      setSubmitError('Failed to create rental. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(amount);
  };

  return (
    <div>
      <div className="page-header">
        <div className="header-left">
          <h1>Create New Rental</h1>
          <p>Start a new vehicle rental</p>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="form">
        {submitError && (
          <div
            className="form-error"
            style={{
              marginBottom: '20px',
              padding: '12px',
              backgroundColor: '#f8d7da',
              borderRadius: '6px',
            }}
          >
            {submitError}
          </div>
        )}

        {/* Customer and Vehicle Selection */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
          <div className="form-group">
            <label htmlFor="customer_id" className="form-label">
              Customer *
            </label>
            <select
              id="customer_id"
              name="customer_id"
              value={formData.customer_id}
              onChange={handleInputChange}
              className="form-select"
              required
            >
              <option value="0">Select a customer</option>
              {customers.map((customer) => (
                <option key={customer.customer_id} value={customer.customer_id}>
                  {customer.first_name} {customer.last_name} - {customer.email}
                </option>
              ))}
            </select>
            {errors.customer_id && <div className="form-error">{errors.customer_id}</div>}
          </div>

          <div className="form-group">
            <label htmlFor="vehicle_id" className="form-label">
              Vehicle *
            </label>
            <select
              id="vehicle_id"
              name="vehicle_id"
              value={formData.vehicle_id}
              onChange={handleInputChange}
              className="form-select"
              required
            >
              <option value="0">Select a vehicle</option>
              {vehicles.map((vehicle) => (
                <option key={vehicle.vehicle_id} value={vehicle.vehicle_id}>
                  {vehicle.year} {vehicle.make} {vehicle.model} - {formatCurrency(vehicle.daily_rate)}/day
                </option>
              ))}
            </select>
            {errors.vehicle_id && <div className="form-error">{errors.vehicle_id}</div>}
          </div>
        </div>

        {/* Selected Vehicle Info */}
        {selectedVehicle && (
          <div style={{ 
            padding: '16px', 
            backgroundColor: '#e3f2fd', 
            borderRadius: '8px', 
            marginBottom: '20px',
            border: '1px solid #90caf9'
          }}>
            <h3 style={{ marginBottom: '12px', fontSize: '16px', fontWeight: '600' }}>
              Selected Vehicle
            </h3>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '12px', fontSize: '14px' }}>
              <div><strong>Vehicle:</strong> {selectedVehicle.year} {selectedVehicle.make} {selectedVehicle.model}</div>
              <div><strong>License Plate:</strong> {selectedVehicle.license_plate}</div>
              <div><strong>Fuel Type:</strong> {selectedVehicle.fuel_type}</div>
              <div><strong>Transmission:</strong> {selectedVehicle.transmission}</div>
              <div><strong>Seating:</strong> {selectedVehicle.seating_capacity} passengers</div>
              <div><strong>Current Mileage:</strong> {selectedVehicle.mileage.toLocaleString()} miles</div>
            </div>
          </div>
        )}

        {/* Date Selection */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
          <div className="form-group">
            <label htmlFor="start_date" className="form-label">
              Start Date & Time *
            </label>
            <input
              type="datetime-local"
              id="start_date"
              name="start_date"
              value={formData.start_date}
              onChange={handleInputChange}
              className="form-input"
              required
            />
            {errors.start_date && <div className="form-error">{errors.start_date}</div>}
          </div>

          <div className="form-group">
            <label htmlFor="end_date" className="form-label">
              End Date & Time *
            </label>
            <input
              type="datetime-local"
              id="end_date"
              name="end_date"
              value={formData.end_date}
              onChange={handleInputChange}
              className="form-input"
              required
            />
            {errors.end_date && <div className="form-error">{errors.end_date}</div>}
          </div>
        </div>

        {/* Location Selection */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
          <div className="form-group">
            <label htmlFor="pickup_location_id" className="form-label">
              Pickup Location *
            </label>
            <select
              id="pickup_location_id"
              name="pickup_location_id"
              value={formData.pickup_location_id}
              onChange={handleInputChange}
              className="form-select"
              required
            >
              <option value="0">Select pickup location</option>
              {locations.map((location) => (
                <option key={location.location_id} value={location.location_id}>
                  {location.name} - {location.city}, {location.state}
                </option>
              ))}
            </select>
            {errors.pickup_location_id && (
              <div className="form-error">{errors.pickup_location_id}</div>
            )}
          </div>

          <div className="form-group">
            <label htmlFor="return_location_id" className="form-label">
              Return Location *
            </label>
            <select
              id="return_location_id"
              name="return_location_id"
              value={formData.return_location_id}
              onChange={handleInputChange}
              className="form-select"
              required
            >
              <option value="0">Select return location</option>
              {locations.map((location) => (
                <option key={location.location_id} value={location.location_id}>
                  {location.name} - {location.city}, {location.state}
                </option>
              ))}
            </select>
            {errors.return_location_id && (
              <div className="form-error">{errors.return_location_id}</div>
            )}
          </div>
        </div>

        {/* Rental Details */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '20px' }}>
          <div className="form-group">
            <label htmlFor="daily_rate" className="form-label">
              Daily Rate (USD) *
            </label>
            <input
              type="number"
              id="daily_rate"
              name="daily_rate"
              value={formData.daily_rate}
              onChange={handleInputChange}
              className="form-input"
              min="0"
              step="0.01"
              required
            />
            {errors.daily_rate && <div className="form-error">{errors.daily_rate}</div>}
          </div>

          <div className="form-group">
            <label htmlFor="security_deposit" className="form-label">
              Security Deposit (USD)
            </label>
            <input
              type="number"
              id="security_deposit"
              name="security_deposit"
              value={formData.security_deposit}
              onChange={handleInputChange}
              className="form-input"
              min="0"
              step="0.01"
            />
          </div>

          <div className="form-group">
            <label htmlFor="mileage_start" className="form-label">
              Starting Mileage
            </label>
            <input
              type="number"
              id="mileage_start"
              name="mileage_start"
              value={formData.mileage_start || ''}
              onChange={handleInputChange}
              className="form-input"
              min="0"
            />
          </div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
          <div className="form-group">
            <label htmlFor="fuel_level_start" className="form-label">
              Starting Fuel Level (0-1)
            </label>
            <input
              type="number"
              id="fuel_level_start"
              name="fuel_level_start"
              value={formData.fuel_level_start || ''}
              onChange={handleInputChange}
              className="form-input"
              min="0"
              max="1"
              step="0.01"
              placeholder="e.g., 1.00 for full tank"
            />
          </div>

          <div className="form-group">
            <label htmlFor="employee_id" className="form-label">
              Assigned Employee
            </label>
            <select
              id="employee_id"
              name="employee_id"
              value={formData.employee_id || ''}
              onChange={handleInputChange}
              className="form-select"
            >
              <option value="">No employee assigned</option>
              {employees.map((employee) => (
                <option key={employee.employee_id} value={employee.employee_id}>
                  {employee.first_name} {employee.last_name} - {employee.role}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Summary Section */}
        {rentalDays > 0 && (
          <div style={{ 
            padding: '20px', 
            backgroundColor: '#f8f9fa', 
            borderRadius: '8px', 
            marginTop: '20px',
            border: '2px solid #dee2e6'
          }}>
            <h3 style={{ marginBottom: '16px', fontSize: '18px', fontWeight: '600' }}>
              Rental Summary
            </h3>
            <div style={{ display: 'grid', gap: '12px', fontSize: '16px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span>Rental Duration:</span>
                <strong>{rentalDays} day{rentalDays !== 1 ? 's' : ''}</strong>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span>Daily Rate:</span>
                <strong>{formatCurrency(formData.daily_rate)}</strong>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span>Security Deposit:</span>
                <strong>{formatCurrency(formData.security_deposit || 0)}</strong>
              </div>
              <div style={{ 
                display: 'flex', 
                justifyContent: 'space-between', 
                paddingTop: '12px', 
                borderTop: '2px solid #dee2e6',
                fontSize: '18px'
              }}>
                <span>Total Rental Cost:</span>
                <strong style={{ color: '#28a745' }}>{formatCurrency(formData.total_amount)}</strong>
              </div>
              <div style={{ 
                display: 'flex', 
                justifyContent: 'space-between',
                fontSize: '18px',
                fontWeight: '600'
              }}>
                <span>Total Due Today:</span>
                <strong style={{ color: '#007bff' }}>
                  {formatCurrency(formData.total_amount + (formData.security_deposit || 0))}
                </strong>
              </div>
            </div>
          </div>
        )}

        <div className="form-actions">
          <button
            type="button"
            onClick={() => navigate('/rentals')}
            className="btn btn-secondary"
            disabled={loading}
          >
            Cancel
          </button>
          <button type="submit" className="btn btn-primary" disabled={loading || rentalDays === 0}>
            {loading ? 'Creating...' : 'Create Rental'}
          </button>
        </div>
      </form>
    </div>
  );
};

export default RentalForm;