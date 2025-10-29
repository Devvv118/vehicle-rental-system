// import React from 'react';

// const EmployeeForm: React.FC = () => {
//   return <div><h1>Employee Form</h1><p>Under construction</p></div>;
// };

// export default EmployeeForm;

// pages/EmployeeForm.tsx
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { employeeApi, locationApi } from '../services/api';
import type { EmployeeCreate, Location } from '../types';

const EmployeeForm: React.FC = () => {
  const navigate = useNavigate();

  const [formData, setFormData] = useState<EmployeeCreate>({
    first_name: '',
    last_name: '',
    email: '',
    phone: '',
    role: '',
    hire_date: '',
    salary: undefined,
    location_id: undefined,
    manager_id: undefined,
    is_active: true,
  });

  const [locations, setLocations] = useState<Location[]>([]);
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [submitError, setSubmitError] = useState<string | null>(null);

  useEffect(() => {
    fetchLocations();
  }, []);

  const fetchLocations = async () => {
    try {
      const data = await locationApi.getAll();
      setLocations(data);
    } catch (err) {
      console.error('Error fetching locations:', err);
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value, type } = e.target;
    
    let processedValue: any = value;
    
    if (type === 'number') {
      processedValue = value === '' ? undefined : parseFloat(value);
    } else if (type === 'checkbox') {
      processedValue = (e.target as HTMLInputElement).checked;
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

    if (!formData.first_name.trim()) {
      newErrors.first_name = 'First name is required';
    }

    if (!formData.last_name.trim()) {
      newErrors.last_name = 'Last name is required';
    }

    if (!formData.email.trim()) {
      newErrors.email = 'Email is required';
    } else if (!/\S+@\S+\.\S+/.test(formData.email)) {
      newErrors.email = 'Email is invalid';
    }

    if (!formData.phone.trim()) {
      newErrors.phone = 'Phone is required';
    }

    if (!formData.role.trim()) {
      newErrors.role = 'Role is required';
    }

    if (!formData.hire_date) {
      newErrors.hire_date = 'Hire date is required';
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

      await employeeApi.create(formData);
      navigate('/employees');
    } catch (err: any) {
      console.error('Error creating employee:', err);
      if (err.status === 400 && err.message.includes('Email already registered')) {
        setErrors({ email: 'Email already registered' });
      } else {
        setSubmitError('Failed to create employee. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <div className="page-header">
        <div className="header-left">
          <h1>Add New Employee</h1>
          <p>Create a new employee record</p>
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
            <label htmlFor="first_name" className="form-label">First Name *</label>
            <input
              type="text"
              id="first_name"
              name="first_name"
              value={formData.first_name}
              onChange={handleInputChange}
              className="form-input"
              required
            />
            {errors.first_name && <div className="form-error">{errors.first_name}</div>}
          </div>

          <div className="form-group">
            <label htmlFor="last_name" className="form-label">Last Name *</label>
            <input
              type="text"
              id="last_name"
              name="last_name"
              value={formData.last_name}
              onChange={handleInputChange}
              className="form-input"
              required
            />
            {errors.last_name && <div className="form-error">{errors.last_name}</div>}
          </div>
        </div>

        <div className="form-group">
          <label htmlFor="email" className="form-label">Email *</label>
          <input
            type="email"
            id="email"
            name="email"
            value={formData.email}
            onChange={handleInputChange}
            className="form-input"
            required
          />
          {errors.email && <div className="form-error">{errors.email}</div>}
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
          <div className="form-group">
            <label htmlFor="phone" className="form-label">Phone *</label>
            <input
              type="tel"
              id="phone"
              name="phone"
              value={formData.phone}
              onChange={handleInputChange}
              className="form-input"
              required
            />
            {errors.phone && <div className="form-error">{errors.phone}</div>}
          </div>

          <div className="form-group">
            <label htmlFor="role" className="form-label">Role *</label>
            <select
              id="role"
              name="role"
              value={formData.role}
              onChange={handleInputChange}
              className="form-select"
              required
            >
              <option value="">Select a role</option>
              <option value="Manager">Manager</option>
              <option value="Agent">Agent</option>
              <option value="Mechanic">Mechanic</option>
              <option value="Admin">Admin</option>
            </select>
            {errors.role && <div className="form-error">{errors.role}</div>}
          </div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
          <div className="form-group">
            <label htmlFor="hire_date" className="form-label">Hire Date *</label>
            <input
              type="date"
              id="hire_date"
              name="hire_date"
              value={formData.hire_date}
              onChange={handleInputChange}
              className="form-input"
              required
            />
            {errors.hire_date && <div className="form-error">{errors.hire_date}</div>}
          </div>

          <div className="form-group">
            <label htmlFor="salary" className="form-label">Salary (USD)</label>
            <input
              type="number"
              id="salary"
              name="salary"
              value={formData.salary || ''}
              onChange={handleInputChange}
              className="form-input"
              min="0"
              step="0.01"
            />
          </div>
        </div>

        <div className="form-group">
          <label htmlFor="location_id" className="form-label">Location</label>
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
          <div style={{ display: 'flex', alignItems: 'center', marginTop: '10px' }}>
            <input
              type="checkbox"
              id="is_active"
              name="is_active"
              checked={formData.is_active}
              onChange={handleInputChange}
              style={{ marginRight: '8px', width: '20px', height: '20px' }}
            />
            <label htmlFor="is_active" style={{ marginBottom: '0', fontWeight: 'normal' }}>
              Employee is active
            </label>
          </div>
        </div>

        <div className="form-actions">
          <button
            type="button"
            onClick={() => navigate('/employees')}
            className="btn btn-secondary"
            disabled={loading}
          >
            Cancel
          </button>
          <button type="submit" className="btn btn-primary" disabled={loading}>
            {loading ? 'Creating...' : 'Create Employee'}
          </button>
        </div>
      </form>
    </div>
  );
};

export default EmployeeForm;