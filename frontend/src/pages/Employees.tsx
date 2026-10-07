// import React from 'react';

// const Employees: React.FC = () => {
//   return <div><h1>Employees</h1><p>Under construction</p></div>;
// };

// export default Employees;

// pages/Employees.tsx
import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { employeeApi } from '../services/api';
import type { Employee } from '../types';

const Employees: React.FC = () => {
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<'all' | 'active'>('active');

  useEffect(() => {
    fetchEmployees();
  }, [filter]);

  const fetchEmployees = async () => {
    try {
      setLoading(true);
      const data = filter === 'active' 
        ? await employeeApi.getActive()
        : await employeeApi.getAll();
      setEmployees(data);
    } catch (err) {
      setError('Failed to load employees');
      console.error('Error fetching employees:', err);
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString();
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(amount);
  };

  if (loading) {
    return <div className="loading"><div className="loading-spinner">Loading employees...</div></div>;
  }

  if (error) {
    return (
      <div className="error">
        <div className="error-message">
          <p>{error}</p>
          <button onClick={fetchEmployees} className="retry-button">Retry</button>
        </div>
      </div>
    );
  }

  return (
    <div className="employees">
      <div className="page-header">
        <div className="header-left">
          <h1>Employees</h1>
          <p>Manage your workforce</p>
        </div>
        <div className="header-right">
          <Link to="/employees/new" className="btn btn-primary">Add Employee</Link>
        </div>
      </div>

      <div style={{ marginBottom: '24px', display: 'flex', gap: '12px' }}>
        <button
          className={`btn ${filter === 'active' ? 'btn-primary' : 'btn-outline'}`}
          onClick={() => setFilter('active')}
        >
          Active Employees
        </button>
        <button
          className={`btn ${filter === 'all' ? 'btn-primary' : 'btn-outline'}`}
          onClick={() => setFilter('all')}
        >
          All Employees
        </button>
      </div>

      <div className="employees-table">
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>Name</th>
              <th>Email</th>
              <th>Phone</th>
              <th>Role</th>
              <th>Hire Date</th>
              <th>Salary</th>
              <th>Location ID</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {employees.map((employee) => (
              <tr key={employee.employee_id}>
                <td>{employee.employee_id}</td>
                <td>
                  <strong>{employee.first_name} {employee.last_name}</strong>
                </td>
                <td>{employee.email}</td>
                <td>{employee.phone}</td>
                <td>
                  <span style={{ 
                    padding: '4px 8px', 
                    backgroundColor: '#e3f2fd', 
                    borderRadius: '12px',
                    fontSize: '12px',
                    fontWeight: '600'
                  }}>
                    {employee.role}
                  </span>
                </td>
                <td>{formatDate(employee.hire_date)}</td>
                <td>{employee.salary ? formatCurrency(employee.salary) : 'N/A'}</td>
                <td>#{employee.location_id || 'Unassigned'}</td>
                <td>
                  <span className={`status-badge ${employee.is_active ? 'active' : 'cancelled'}`}>
                    {employee.is_active ? 'Active' : 'Inactive'}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        {employees.length === 0 && (
          <div className="no-data">
            <p>No employees found.</p>
            <Link to="/employees/new" className="btn btn-primary">
              Add First Employee
            </Link>
          </div>
        )}
      </div>
    </div>
  );
};

export default Employees;