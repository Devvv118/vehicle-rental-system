// import React from 'react';
// import { useParams } from 'react-router-dom';

// const VehicleForm: React.FC = () => {
//   const { id } = useParams<{ id: string }>();
//   const isEdit = Boolean(id);
  
//   return (
//     <div>
//       <h1>{isEdit ? 'Edit Vehicle' : 'Add Vehicle'}</h1>
//       <p>Vehicle form is under construction.</p>
//     </div>
//   );
// };

// export default VehicleForm;

import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { vehicleApi, locationApi } from '../services/api';
import type { VehicleCreate, Location } from '../types';

const VehicleForm: React.FC = () => {
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const isEdit = Boolean(id);

  const [formData, setFormData] = useState<VehicleCreate>({
    make: '',
    model: '',
    license_plate: '',
    year: new Date().getFullYear(),
    availability: true,
    daily_rate: 0,
    mileage: 0,
    fuel_type: 'Gasoline',
    transmission: 'Automatic',
    seating_capacity: 5,
    location_id: undefined,
  });

  const [locations, setLocations] = useState<Location[]>([]);
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [submitError, setSubmitError] = useState<string | null>(null);

  useEffect(() => {
    fetchLocations();
    if (isEdit && id) {
      fetchVehicle(parseInt(id));
    }
  }, [isEdit, id]);

  const fetchLocations = async () => {
    try {
      const data = await locationApi.getAll();
      setLocations(data);
    } catch (err) {
      console.error('Error fetching locations:', err);
    }
  };

  const fetchVehicle = async (vehicleId: number) => {
    try {
      setLoading(true);
      const vehicle = await vehicleApi.getById(vehicleId);
      setFormData({
        make: vehicle.make,
        model: vehicle.model,
        license_plate: vehicle.license_plate,
        year: vehicle.year,
        availability: vehicle.availability,
        daily_rate: vehicle.daily_rate,
        mileage: vehicle.mileage,
        fuel_type: vehicle.fuel_type,
        transmission: vehicle.transmission,
        seating_capacity: vehicle.seating_capacity,
        location_id: vehicle.location_id || undefined,
      });
    } catch (err) {
      console.error('Error fetching vehicle:', err);
      setSubmitError('Failed to load vehicle data');
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>
  ) => {
    const { name, value, type } = e.target;
    
    let processedValue: any = value;
    
    if (type === 'number') {
      processedValue = value === '' ? 0 : parseFloat(value);
    } else if (type === 'checkbox') {
      processedValue = (e.target as HTMLInputElement).checked;
    }

    setFormData((prev) => ({
      ...prev,
      [name]: processedValue,
    }));

    // Clear error when user starts typing
    if (errors[name]) {
      setErrors((prev) => ({
        ...prev,
        [name]: '',
      }));
    }
  };

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!formData.make.trim()) {
      newErrors.make = 'Make is required';
    }

    if (!formData.model.trim()) {
      newErrors.model = 'Model is required';
    }

    if (!formData.license_plate.trim()) {
      newErrors.license_plate = 'License plate is required';
    }

    if (formData.year < 1900 || formData.year > new Date().getFullYear() + 1) {
      newErrors.year = 'Please enter a valid year';
    }

    if (formData.daily_rate <= 0) {
      newErrors.daily_rate = 'Daily rate must be greater than 0';
    }

    const capacity = formData.seating_capacity ?? 5;
    if (capacity < 1 || capacity > 20) {
      newErrors.seating_capacity = 'Seating capacity must be between 1 and 20';
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

      if (isEdit && id) {
        await vehicleApi.update(parseInt(id), formData);
      } else {
        await vehicleApi.create(formData);
      }

      navigate('/vehicles');
    } catch (err: any) {
      console.error('Error saving vehicle:', err);

      if (err.status === 400) {
        if (err.message.includes('License plate already exists')) {
          setErrors({ license_plate: 'License plate already exists' });
        } else {
          setSubmitError('Validation error. Please check your input.');
        }
      } else {
        setSubmitError('Failed to save vehicle. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  if (loading && isEdit) {
    return (
      <div className="loading">
        <div className="loading-spinner">Loading vehicle data...</div>
      </div>
    );
  }

  return (
    <div>
      <div className="page-header">
        <div className="header-left">
          <h1>{isEdit ? 'Edit Vehicle' : 'Add New Vehicle'}</h1>
          <p>{isEdit ? 'Update vehicle information' : 'Add a new vehicle to your fleet'}</p>
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

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
          <div className="form-group">
            <label htmlFor="make" className="form-label">
              Make *
            </label>
            <input
              type="text"
              id="make"
              name="make"
              value={formData.make}
              onChange={handleInputChange}
              className="form-input"
              placeholder="e.g., Toyota, Ford, BMW"
              required
            />
            {errors.make && <div className="form-error">{errors.make}</div>}
          </div>

          <div className="form-group">
            <label htmlFor="model" className="form-label">
              Model *
            </label>
            <input
              type="text"
              id="model"
              name="model"
              value={formData.model}
              onChange={handleInputChange}
              className="form-input"
              placeholder="e.g., Camry, F-150, X5"
              required
            />
            {errors.model && <div className="form-error">{errors.model}</div>}
          </div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
          <div className="form-group">
            <label htmlFor="license_plate" className="form-label">
              License Plate *
            </label>
            <input
              type="text"
              id="license_plate"
              name="license_plate"
              value={formData.license_plate}
              onChange={handleInputChange}
              className="form-input"
              placeholder="e.g., ABC-1234"
              required
            />
            {errors.license_plate && (
              <div className="form-error">{errors.license_plate}</div>
            )}
          </div>

          <div className="form-group">
            <label htmlFor="year" className="form-label">
              Year *
            </label>
            <input
              type="number"
              id="year"
              name="year"
              value={formData.year}
              onChange={handleInputChange}
              className="form-input"
              min="1900"
              max={new Date().getFullYear() + 1}
              required
            />
            {errors.year && <div className="form-error">{errors.year}</div>}
          </div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
          <div className="form-group">
            <label htmlFor="fuel_type" className="form-label">
              Fuel Type *
            </label>
            <select
              id="fuel_type"
              name="fuel_type"
              value={formData.fuel_type}
              onChange={handleInputChange}
              className="form-select"
              required
            >
              <option value="Gasoline">Gasoline</option>
              <option value="Diesel">Diesel</option>
              <option value="Electric">Electric</option>
              <option value="Hybrid">Hybrid</option>
            </select>
          </div>

          <div className="form-group">
            <label htmlFor="transmission" className="form-label">
              Transmission *
            </label>
            <select
              id="transmission"
              name="transmission"
              value={formData.transmission}
              onChange={handleInputChange}
              className="form-select"
              required
            >
              <option value="Automatic">Automatic</option>
              <option value="Manual">Manual</option>
            </select>
          </div>
        </div>

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
            {errors.daily_rate && (
              <div className="form-error">{errors.daily_rate}</div>
            )}
          </div>

          <div className="form-group">
            <label htmlFor="seating_capacity" className="form-label">
              Seating Capacity *
            </label>
            <input
              type="number"
              id="seating_capacity"
              name="seating_capacity"
              value={formData.seating_capacity}
              onChange={handleInputChange}
              className="form-input"
              min="1"
              max="20"
              required
            />
            {errors.seating_capacity && (
              <div className="form-error">{errors.seating_capacity}</div>
            )}
          </div>

          <div className="form-group">
            <label htmlFor="mileage" className="form-label">
              Current Mileage
            </label>
            <input
              type="number"
              id="mileage"
              name="mileage"
              value={formData.mileage}
              onChange={handleInputChange}
              className="form-input"
              min="0"
            />
          </div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
          <div className="form-group">
            <label htmlFor="location_id" className="form-label">
              Location
            </label>
            <select
              id="location_id"
              name="location_id"
              value={formData.location_id || ''}
              onChange={handleInputChange}
              className="form-select"
            >
              <option value="">Select a location</option>
              {locations.map((location) => (
                <option key={location.location_id} value={location.location_id}>
                  {location.name} - {location.city}, {location.state}
                </option>
              ))}
            </select>
          </div>

          <div className="form-group">
            <label htmlFor="availability" className="form-label">
              Availability
            </label>
            <div style={{ display: 'flex', alignItems: 'center', marginTop: '10px' }}>
              <input
                type="checkbox"
                id="availability"
                name="availability"
                checked={formData.availability}
                onChange={handleInputChange}
                style={{ marginRight: '8px', width: '20px', height: '20px' }}
              />
              <label htmlFor="availability" style={{ marginBottom: '0', fontWeight: 'normal' }}>
                Vehicle is available for rental
              </label>
            </div>
          </div>
        </div>

        <div className="form-actions">
          <button
            type="button"
            onClick={() => navigate('/vehicles')}
            className="btn btn-secondary"
            disabled={loading}
          >
            Cancel
          </button>
          <button type="submit" className="btn btn-primary" disabled={loading}>
            {loading ? 'Saving...' : isEdit ? 'Update Vehicle' : 'Create Vehicle'}
          </button>
        </div>
      </form>
    </div>
  );
};

export default VehicleForm;