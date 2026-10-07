// import React from 'react';

// const ReservationForm: React.FC = () => {
//   return <div><h1>New Reservation</h1><p>Under construction</p></div>;
// };

// export default ReservationForm;

// pages/ReservationForm.tsx - Complete Reservation Form Component
import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { reservationApi, customerApi, vehicleApi, locationApi } from '../services/api';
import type { ReservationCreate, Customer, Vehicle, Location } from '../types';

const ReservationForm: React.FC = () => {
  const navigate = useNavigate();

  const [formData, setFormData] = useState<ReservationCreate>({
    customer_id: 0,
    vehicle_id: 0,
    pickup_location_id: 0,
    return_location_id: 0,
    reserved_start_date: '',
    reserved_end_date: '',
    status: 'Active',
    special_requests: '',
    estimated_total: 0,
  });

  const [customers, setCustomers] = useState<Customer[]>([]);
  const [vehicles, setVehicles] = useState<Vehicle[]>([]);
  const [locations, setLocations] = useState<Location[]>([]);
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [submitError, setSubmitError] = useState<string | null>(null);

  useEffect(() => {
    fetchFormData();
  }, []);

  const fetchFormData = async () => {
    try {
      const [customersData, vehiclesData, locationsData] = await Promise.all([
        customerApi.getAll(0, 1000),
        vehicleApi.getAvailable(0, 1000),
        locationApi.getAll(0, 1000),
      ]);

      setCustomers(customersData);
      setVehicles(vehiclesData);
      setLocations(locationsData);
    } catch (err) {
      console.error('Error fetching form data:', err);
      setSubmitError('Failed to load form data');
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value, type } = e.target;
    
    let processedValue: any = value;
    
    if (type === 'number') {
      processedValue = value === '' ? 0 : parseFloat(value);
    }

    setFormData(prev => ({
      ...prev,
      [name]: processedValue,
    }));

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

    if (!formData.reserved_start_date) {
      newErrors.reserved_start_date = 'Start date is required';
    }

    if (!formData.reserved_end_date) {
      newErrors.reserved_end_date = 'End date is required';
    }

    if (formData.reserved_start_date && formData.reserved_end_date) {
      const start = new Date(formData.reserved_start_date);
      const end = new Date(formData.reserved_end_date);
      
      if (end <= start) {
        newErrors.reserved_end_date = 'End date must be after start date';
      }
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

      await reservationApi.create(formData);
      navigate('/reservations');
    } catch (err: any) {
      console.error('Error creating reservation:', err);
      if (err.message.includes('not available')) {
        setSubmitError('Vehicle is not available for the selected dates');
      } else {
        setSubmitError('Failed to create reservation. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <div className="page-header">
        <div className="header-left">
          <h1>Create New Reservation</h1>
          <p>Make a new vehicle reservation</p>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="form">
        {submitError && (
          <div className="form-error" style={{ marginBottom: '20px', padding: '12px', backgroundColor: '#f8d7da', borderRadius: '6px' }}>
            {submitError}
          </div>
        )}

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
          <div className="form-group">
            <label htmlFor="customer_id" className="form-label">Customer *</label>
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
            <label htmlFor="vehicle_id" className="form-label">Vehicle *</label>
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
                  {vehicle.year} {vehicle.make} {vehicle.model}
                </option>
              ))}
            </select>
            {errors.vehicle_id && <div className="form-error">{errors.vehicle_id}</div>}
          </div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
          <div className="form-group">
            <label htmlFor="reserved_start_date" className="form-label">Start Date & Time *</label>
            <input
              type="datetime-local"
              id="reserved_start_date"
              name="reserved_start_date"
              value={formData.reserved_start_date}
              onChange={handleInputChange}
              className="form-input"
              required
            />
            {errors.reserved_start_date && <div className="form-error">{errors.reserved_start_date}</div>}
          </div>

          <div className="form-group">
            <label htmlFor="reserved_end_date" className="form-label">End Date & Time *</label>
            <input
              type="datetime-local"
              id="reserved_end_date"
              name="reserved_end_date"
              value={formData.reserved_end_date}
              onChange={handleInputChange}
              className="form-input"
              required
            />
            {errors.reserved_end_date && <div className="form-error">{errors.reserved_end_date}</div>}
          </div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
          <div className="form-group">
            <label htmlFor="pickup_location_id" className="form-label">Pickup Location *</label>
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
            {errors.pickup_location_id && <div className="form-error">{errors.pickup_location_id}</div>}
          </div>

          <div className="form-group">
            <label htmlFor="return_location_id" className="form-label">Return Location *</label>
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
            {errors.return_location_id && <div className="form-error">{errors.return_location_id}</div>}
          </div>
        </div>

        <div className="form-group">
          <label htmlFor="special_requests" className="form-label">Special Requests</label>
          <textarea
            id="special_requests"
            name="special_requests"
            value={formData.special_requests}
            onChange={handleInputChange}
            className="form-textarea"
            rows={3}
            placeholder="Any special requests or notes..."
          />
        </div>

        <div className="form-group">
          <label htmlFor="estimated_total" className="form-label">Estimated Total (USD)</label>
          <input
            type="number"
            id="estimated_total"
            name="estimated_total"
            value={formData.estimated_total}
            onChange={handleInputChange}
            className="form-input"
            min="0"
            step="0.01"
          />
        </div>

        <div className="form-actions">
          <button
            type="button"
            onClick={() => navigate('/reservations')}
            className="btn btn-secondary"
            disabled={loading}
          >
            Cancel
          </button>
          <button type="submit" className="btn btn-primary" disabled={loading}>
            {loading ? 'Creating...' : 'Create Reservation'}
          </button>
        </div>
      </form>
    </div>
  );
};

export default ReservationForm;