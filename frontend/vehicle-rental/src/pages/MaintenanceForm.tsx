// import React from 'react';

// const MaintenanceForm: React.FC = () => {
//   return <div><h1>Maintenance Form</h1><p>Under construction</p></div>;
// };

// export default MaintenanceForm;

import { useNavigate, useSearchParams } from 'react-router-dom';
import { maintenanceApi, vehicleApi, employeeApi } from '../services/api';
import type { MaintenanceScheduleCreate, Vehicle, Employee } from '../types';
import { useEffect, useState } from 'react';

const MaintenanceForm: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  const [formData, setFormData] = useState<MaintenanceScheduleCreate>({
    vehicle_id: parseInt(searchParams.get('vehicle_id') || '0') || 0,
    maintenance_type: '',
    scheduled_date: '',
    assigned_mechanic: undefined,
    cost: undefined,
    notes: '',
    status: 'Scheduled',
  });

  const [vehicles, setVehicles] = useState<Vehicle[]>([]);
  const [mechanics, setMechanics] = useState<Employee[]>([]);
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [submitError, setSubmitError] = useState<string | null>(null);

  useEffect(() => {
    fetchFormData();
  }, []);

  const fetchFormData = async () => {
    try {
      const [vehiclesData, mechanicsData] = await Promise.all([
        vehicleApi.getAll(0, 1000),
        employeeApi.getByRole('Mechanic'),
      ]);

      setVehicles(vehiclesData);
      setMechanics(mechanicsData);
    } catch (err) {
      console.error('Error fetching form data:', err);
      setSubmitError('Failed to load form data');
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value, type } = e.target;
    
    let processedValue: any = value;
    
    if (type === 'number') {
      processedValue = value === '' ? undefined : parseFloat(value);
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

    if (formData.vehicle_id === 0) {
      newErrors.vehicle_id = 'Please select a vehicle';
    }

    if (!formData.maintenance_type.trim()) {
      newErrors.maintenance_type = 'Maintenance type is required';
    }

    if (!formData.scheduled_date) {
      newErrors.scheduled_date = 'Scheduled date is required';
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

      await maintenanceApi.create(formData);
      navigate('/maintenance');
    } catch (err: any) {
      console.error('Error creating maintenance schedule:', err);
      setSubmitError('Failed to schedule maintenance. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <div className="page-header">
        <div className="header-left">
          <h1>Schedule Maintenance</h1>
          <p>Create a new maintenance schedule</p>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="form">
        {submitError && (
          <div className="form-error" style={{ marginBottom: '20px', padding: '12px', backgroundColor: '#f8d7da', borderRadius: '6px' }}>
            {submitError}
          </div>
        )}

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
                {vehicle.year} {vehicle.make} {vehicle.model} - {vehicle.license_plate}
              </option>
            ))}
          </select>
          {errors.vehicle_id && <div className="form-error">{errors.vehicle_id}</div>}
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
          <div className="form-group">
            <label htmlFor="maintenance_type" className="form-label">Maintenance Type *</label>
            <select
              id="maintenance_type"
              name="maintenance_type"
              value={formData.maintenance_type}
              onChange={handleInputChange}
              className="form-select"
              required
            >
              <option value="">Select maintenance type</option>
              <option value="Oil Change">Oil Change</option>
              <option value="Tire Rotation">Tire Rotation</option>
              <option value="Brake Inspection">Brake Inspection</option>
              <option value="Full Service">Full Service</option>
              <option value="Engine Inspection">Engine Inspection</option>
              <option value="Transmission Service">Transmission Service</option>
              <option value="Battery Replacement">Battery Replacement</option>
              <option value="Other">Other</option>
            </select>
            {errors.maintenance_type && <div className="form-error">{errors.maintenance_type}</div>}
          </div>

          <div className="form-group">
            <label htmlFor="scheduled_date" className="form-label">Scheduled Date *</label>
            <input
              type="date"
              id="scheduled_date"
              name="scheduled_date"
              value={formData.scheduled_date}
              onChange={handleInputChange}
              className="form-input"
              required
            />
            {errors.scheduled_date && <div className="form-error">{errors.scheduled_date}</div>}
          </div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
          <div className="form-group">
            <label htmlFor="assigned_mechanic" className="form-label">Assigned Mechanic</label>
            <select
              id="assigned_mechanic"
              name="assigned_mechanic"
              value={formData.assigned_mechanic || ''}
              onChange={handleInputChange}
              className="form-select"
            >
              <option value="">Select a mechanic</option>
              {mechanics.map((mechanic) => (
                <option key={mechanic.employee_id} value={mechanic.employee_id}>
                  {mechanic.first_name} {mechanic.last_name}
                </option>
              ))}
            </select>
          </div>

          <div className="form-group">
            <label htmlFor="cost" className="form-label">Estimated Cost (USD)</label>
            <input
              type="number"
              id="cost"
              name="cost"
              value={formData.cost || ''}
              onChange={handleInputChange}
              className="form-input"
              min="0"
              step="0.01"
            />
          </div>
        </div>

        <div className="form-group">
          <label htmlFor="notes" className="form-label">Notes</label>
          <textarea
            id="notes"
            name="notes"
            value={formData.notes}
            onChange={handleInputChange}
            className="form-textarea"
            rows={4}
            placeholder="Additional notes or details about the maintenance..."
          />
        </div>

        <div className="form-actions">
          <button
            type="button"
            onClick={() => navigate('/maintenance')}
            className="btn btn-secondary"
            disabled={loading}
          >
            Cancel
          </button>
          <button type="submit" className="btn btn-primary" disabled={loading}>
            {loading ? 'Scheduling...' : 'Schedule Maintenance'}
          </button>
        </div>
      </form>
    </div>
  );
};

export default MaintenanceForm;