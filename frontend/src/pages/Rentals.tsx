import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { rentalApi } from '../services/api';
import type { Rental } from '../types';

const Rentals: React.FC = () => {
  const [rentals, setRentals] = useState<Rental[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchRentals();
  }, []);

  const fetchRentals = async () => {
    try {
      setLoading(true);
      const data = await rentalApi.getAll();
      setRentals(data);
    } catch (err) {
      setError('Failed to load rentals');
      console.error('Error fetching rentals:', err);
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
    return <div className="loading"><div className="loading-spinner">Loading rentals...</div></div>;
  }

  if (error) {
    return (
      <div className="error">
        <div className="error-message">
          <p>{error}</p>
          <button onClick={fetchRentals} className="retry-button">Retry</button>
        </div>
      </div>
    );
  }

  return (
    <div className="rentals">
      <div className="page-header">
        <div className="header-left">
          <h1>Rentals</h1>
          <p>Manage vehicle rentals</p>
        </div>
        <div className="header-right">
          <Link to="/rentals/new" className="btn btn-primary">New Rental</Link>
        </div>
      </div>

      <div className="rentals-table">
        <table>
          <thead>
            <tr>
              <th>Rental ID</th>
              <th>Customer</th>
              <th>Vehicle</th>
              <th>Start Date</th>
              <th>End Date</th>
              <th>Status</th>
              <th>Total Amount</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {rentals.map((rental) => (
              <tr key={rental.rental_id}>
                <td>{rental.rental_id}</td>
                <td>Customer #{rental.customer_id}</td>
                <td>Vehicle #{rental.vehicle_id}</td>
                <td>{formatDate(rental.start_date)}</td>
                <td>{formatDate(rental.end_date)}</td>
                <td>
                  <span className={`status-badge ${rental.status.toLowerCase()}`}>
                    {rental.status}
                  </span>
                </td>
                <td>{formatCurrency(rental.total_amount)}</td>
                <td>
                  <div className="actions">
                    <Link to={`/rentals/${rental.rental_id}`} className="btn btn-sm btn-outline">View</Link>
                    {rental.status === 'Active' && (
                      <button className="btn btn-sm btn-secondary">Return</button>
                    )}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default Rentals;