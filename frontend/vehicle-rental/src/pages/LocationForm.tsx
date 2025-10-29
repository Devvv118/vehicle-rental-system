// import React from 'react';

// const LocationForm: React.FC = () => {
//   return <div><h1>Location Form</h1><p>Under construction</p></div>;
// };

// export default LocationForm;

// pages/LocationForm.tsx - Similar pattern to other forms
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { locationApi } from '../services/api';

const LocationForm: React.FC = () => {
  const navigate = useNavigate();

  const [formData, setFormData] = useState({
    name: '',
    address: '',
    city: '',
    state: '',
    zip_code: '',
    phone: '',
    operating_hours: '',
  });

  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value,
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
    if (!formData.name.trim()) newErrors.name = 'Name is required';
    if (!formData.address.trim()) newErrors.address = 'Address is required';
    if (!formData.city.trim()) newErrors.city = 'City is required';
    if (!formData.state.trim()) newErrors.state = 'State is required';
    if (!formData.zip_code.trim()) newErrors.zip_code = 'ZIP code is required';

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validateForm()) return;

    try {
      setLoading(true);
      await locationApi.create(formData as any);
      navigate('/locations');
    } catch (err) {
      console.error('Error creating location:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <div className="page-header">
        <div className="header-left">
          <h1>Add New Location</h1>
          <p>Create a new rental location</p>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="form">
        <div className="form-group">
          <label htmlFor="name" className="form-label">Location Name *</label>
          <input
            type="text"
            id="name"
            name="name"
            value={formData.name}
            onChange={handleInputChange}
            className="form-input"
            placeholder="e.g., Downtown Branch"
            required
          />
          {errors.name && <div className="form-error">{errors.name}</div>}
        </div>

        <div className="form-group">
          <label htmlFor="address" className="form-label">Address *</label>
          <input
            type="text"
            id="address"
            name="address"
            value={formData.address}
            onChange={handleInputChange}
            className="form-input"
            required
          />
          {errors.address && <div className="form-error">{errors.address}</div>}
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '20px' }}>
          <div className="form-group">
            <label htmlFor="city" className="form-label">City *</label>
            <input
              type="text"
              id="city"
              name="city"
              value={formData.city}
              onChange={handleInputChange}
              className="form-input"
              required
            />
            {errors.city && <div className="form-error">{errors.city}</div>}
          </div>

          <div className="form-group">
            <label htmlFor="state" className="form-label">State *</label>
            <input
              type="text"
              id="state"
              name="state"
              value={formData.state}
              onChange={handleInputChange}
              className="form-input"
              required
            />
            {errors.state && <div className="form-error">{errors.state}</div>}
          </div>

          <div className="form-group">
            <label htmlFor="zip_code" className="form-label">ZIP Code *</label>
            <input
              type="text"
              id="zip_code"
              name="zip_code"
              value={formData.zip_code}
              onChange={handleInputChange}
              className="form-input"
              required
            />
            {errors.zip_code && <div className="form-error">{errors.zip_code}</div>}
          </div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
          <div className="form-group">
            <label htmlFor="phone" className="form-label">Phone</label>
            <input
              type="tel"
              id="phone"
              name="phone"
              value={formData.phone}
              onChange={handleInputChange}
              className="form-input"
            />
          </div>

          <div className="form-group">
            <label htmlFor="operating_hours" className="form-label">Operating Hours</label>
            <input
              type="text"
              id="operating_hours"
              name="operating_hours"
              value={formData.operating_hours}
              onChange={handleInputChange}
              className="form-input"
              placeholder="e.g., Mon-Fri 9AM-5PM"
            />
          </div>
        </div>

        <div className="form-actions">
          <button
            type="button"
            onClick={() => navigate('/locations')}
            className="btn btn-secondary"
            disabled={loading}
          >
            Cancel
          </button>
          <button type="submit" className="btn btn-primary" disabled={loading}>
            {loading ? 'Creating...' : 'Create Location'}
          </button>
        </div>
      </form>
    </div>
  );
};

export default LocationForm;