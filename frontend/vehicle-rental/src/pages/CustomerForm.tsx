import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { customerApi } from '../services/api';
import type { Customer, CustomerCreate } from '../types';

const CustomerForm: React.FC = () => {
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const isEdit = Boolean(id);

  const [formData, setFormData] = useState<CustomerCreate>({
    first_name: '',
    last_name: '',
    email: '',
    phone: '',
    address: '',
    driver_license: '',
    date_of_birth: '',
  });

  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [submitError, setSubmitError] = useState<string | null>(null);

  useEffect(() => {
    if (isEdit && id) {
      fetchCustomer(parseInt(id));
    }
  }, [isEdit, id]);

  const fetchCustomer = async (customerId: number) => {
    try {
      setLoading(true);
      const customer = await customerApi.getById(customerId);
      setFormData({
        first_name: customer.first_name,
        last_name: customer.last_name,
        email: customer.email,
        phone: customer.phone,
        address: customer.address || '',
        driver_license: customer.driver_license,
        date_of_birth: customer.date_of_birth || '',
      });
    } catch (err) {
      console.error('Error fetching customer:', err);
      setSubmitError('Failed to load customer data');
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
    // Clear error when user starts typing
    if (errors[name]) {
      setErrors(prev => ({
        ...prev,
        [name]: ''
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

    if (!formData.driver_license.trim()) {
      newErrors.driver_license = 'Driver license is required';
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
        await customerApi.update(parseInt(id), formData);
      } else {
        await customerApi.create(formData);
      }

      navigate('/customers');
    } catch (err: any) {
      console.error('Error saving customer:', err);
      
      if (err.status === 400) {
        if (err.message.includes('Email already registered')) {
          setErrors({ email: 'Email already registered' });
        } else if (err.message.includes('Driver license already registered')) {
          setErrors({ driver_license: 'Driver license already registered' });
        } else {
          setSubmitError('Validation error. Please check your input.');
        }
      } else {
        setSubmitError('Failed to save customer. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  if (loading && isEdit) {
    return (
      <div className="loading">
        <div className="loading-spinner">Loading customer data...</div>
      </div>
    );
  }

  return (
    <div>
      <div className="page-header">
        <div className="header-left">
          <h1>{isEdit ? 'Edit Customer' : 'Add New Customer'}</h1>
          <p>{isEdit ? 'Update customer information' : 'Create a new customer account'}</p>
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
            <label htmlFor="first_name" className="form-label">
              First Name *
            </label>
            <input
              type="text"
              id="first_name"
              name="first_name"
              value={formData.first_name}
              onChange={handleInputChange}
              className="form-input"
              required
            />
            {errors.first_name && (
              <div className="form-error">{errors.first_name}</div>
            )}
          </div>

          <div className="form-group">
            <label htmlFor="last_name" className="form-label">
              Last Name *
            </label>
            <input
              type="text"
              id="last_name"
              name="last_name"
              value={formData.last_name}
              onChange={handleInputChange}
              className="form-input"
              required
            />
            {errors.last_name && (
              <div className="form-error">{errors.last_name}</div>
            )}
          </div>
        </div>

        <div className="form-group">
          <label htmlFor="email" className="form-label">
            Email *
          </label>
          <input
            type="email"
            id="email"
            name="email"
            value={formData.email}
            onChange={handleInputChange}
            className="form-input"
            required
          />
          {errors.email && (
            <div className="form-error">{errors.email}</div>
          )}
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
          <div className="form-group">
            <label htmlFor="phone" className="form-label">
              Phone *
            </label>
            <input
              type="tel"
              id="phone"
              name="phone"
              value={formData.phone}
              onChange={handleInputChange}
              className="form-input"
              required
            />
            {errors.phone && (
              <div className="form-error">{errors.phone}</div>
            )}
          </div>

          <div className="form-group">
            <label htmlFor="driver_license" className="form-label">
              Driver License *
            </label>
            <input
              type="text"
              id="driver_license"
              name="driver_license"
              value={formData.driver_license}
              onChange={handleInputChange}
              className="form-input"
              required
            />
            {errors.driver_license && (
              <div className="form-error">{errors.driver_license}</div>
            )}
          </div>
        </div>

        <div className="form-group">
          <label htmlFor="date_of_birth" className="form-label">
            Date of Birth
          </label>
          <input
            type="date"
            id="date_of_birth"
            name="date_of_birth"
            value={formData.date_of_birth}
            onChange={handleInputChange}
            className="form-input"
          />
        </div>

        <div className="form-group">
          <label htmlFor="address" className="form-label">
            Address
          </label>
          <textarea
            id="address"
            name="address"
            value={formData.address}
            onChange={handleInputChange}
            className="form-textarea"
            rows={3}
            placeholder="Enter full address..."
          />
        </div>

        <div className="form-actions">
          <button
            type="button"
            onClick={() => navigate('/customers')}
            className="btn btn-secondary"
            disabled={loading}
          >
            Cancel
          </button>
          <button
            type="submit"
            className="btn btn-primary"
            disabled={loading}
          >
            {loading ? 'Saving...' : (isEdit ? 'Update Customer' : 'Create Customer')}
          </button>
        </div>
      </form>
    </div>
  );
};

export default CustomerForm;