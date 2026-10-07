// import React from 'react';

// const IncidentForm: React.FC = () => {
//   return <div><h1>Incident Form</h1><p>Under construction</p></div>;
// };

// export default IncidentForm;

// pages/IncidentForm.tsx
import { useNavigate, useSearchParams } from 'react-router-dom';
import { incidentApi, rentalApi, employeeApi } from '../services/api';
import type { IncidentReportCreate, Rental, Employee } from '../types';
import { useEffect, useState } from 'react';

const IncidentForm: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  const [formData, setFormData] = useState<IncidentReportCreate>({
    rental_id: parseInt(searchParams.get('rental_id') || '0') || 0,
    reported_by: undefined,
    incident_date: '',
    incident_type: '',
    description: '',
    estimated_cost: undefined,
    status: 'Open',
    photos: '',
    police_report_number: '',
  });

  const [rentals, setRentals] = useState<Rental[]>([]);
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});

  useEffect(() => {
    fetchFormData();
  }, []);

  const fetchFormData = async () => {
    try {
      const [rentalsData, employeesData] = await Promise.all([
        rentalApi.getActive(),
        employeeApi.getActive(),
      ]);

      setRentals(rentalsData);
      setEmployees(employeesData);
    } catch (err) {
      console.error('Error fetching form data:', err);
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

    if (formData.rental_id === 0) {
      newErrors.rental_id = 'Please select a rental';
    }

    if (!formData.incident_type.trim()) {
      newErrors.incident_type = 'Incident type is required';
    }

    if (!formData.description.trim()) {
      newErrors.description = 'Description is required';
    }

    if (!formData.incident_date) {
      newErrors.incident_date = 'Incident date is required';
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
      await incidentApi.create(formData);
      navigate('/incidents');
    } catch (err) {
      console.error('Error creating incident report:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <div className="page-header">
        <div className="header-left">
          <h1>Report New Incident</h1>
          <p>Document a rental incident</p>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="form">
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
          <div className="form-group">
            <label htmlFor="rental_id" className="form-label">Rental *</label>
            <select
              id="rental_id"
              name="rental_id"
              value={formData.rental_id}
              onChange={handleInputChange}
              className="form-select"
              required
            >
              <option value="0">Select a rental</option>
              {rentals.map((rental) => (
                <option key={rental.rental_id} value={rental.rental_id}>
                  Rental #{rental.rental_id} - Customer #{rental.customer_id}, Vehicle #{rental.vehicle_id}
                </option>
              ))}
            </select>
            {errors.rental_id && <div className="form-error">{errors.rental_id}</div>}
          </div>

          <div className="form-group">
            <label htmlFor="incident_type" className="form-label">Incident Type *</label>
            <select
              id="incident_type"
              name="incident_type"
              value={formData.incident_type}
              onChange={handleInputChange}
              className="form-select"
              required
            >
              <option value="">Select incident type</option>
              <option value="Accident">Accident</option>
              <option value="Damage">Damage</option>
              <option value="Theft">Theft</option>
              <option value="Breakdown">Breakdown</option>
              <option value="Traffic Violation">Traffic Violation</option>
              <option value="Other">Other</option>
            </select>
            {errors.incident_type && <div className="form-error">{errors.incident_type}</div>}
          </div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
          <div className="form-group">
            <label htmlFor="incident_date" className="form-label">Incident Date & Time *</label>
            <input
              type="datetime-local"
              id="incident_date"
              name="incident_date"
              value={formData.incident_date}
              onChange={handleInputChange}
              className="form-input"
              required
            />
            {errors.incident_date && <div className="form-error">{errors.incident_date}</div>}
          </div>

          <div className="form-group">
            <label htmlFor="reported_by" className="form-label">Reported By</label>
            <select
              id="reported_by"
              name="reported_by"
              value={formData.reported_by || ''}
              onChange={handleInputChange}
              className="form-select"
            >
              <option value="">Select employee</option>
              {employees.map((employee) => (
                <option key={employee.employee_id} value={employee.employee_id}>
                  {employee.first_name} {employee.last_name}
                </option>
              ))}
            </select>
          </div>
        </div>

        <div className="form-group">
          <label htmlFor="description" className="form-label">Description *</label>
          <textarea
            id="description"
            name="description"
            value={formData.description}
            onChange={handleInputChange}
            className="form-textarea"
            rows={5}
            placeholder="Detailed description of the incident..."
            required
          />
          {errors.description && <div className="form-error">{errors.description}</div>}
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
          <div className="form-group">
            <label htmlFor="estimated_cost" className="form-label">Estimated Cost (USD)</label>
            <input
              type="number"
              id="estimated_cost"
              name="estimated_cost"
              value={formData.estimated_cost || ''}
              onChange={handleInputChange}
              className="form-input"
              min="0"
              step="0.01"
            />
          </div>

          <div className="form-group">
            <label htmlFor="police_report_number" className="form-label">Police Report Number</label>
            <input
              type="text"
              id="police_report_number"
              name="police_report_number"
              value={formData.police_report_number}
              onChange={handleInputChange}
              className="form-input"
            />
          </div>
        </div>

        <div className="form-actions">
          <button
            type="button"
            onClick={() => navigate('/incidents')}
            className="btn btn-secondary"
            disabled={loading}
          >
            Cancel
          </button>
          <button type="submit" className="btn btn-primary" disabled={loading}>
            {loading ? 'Reporting...' : 'Submit Report'}
          </button>
        </div>
      </form>
    </div>
  );
};

export default IncidentForm;