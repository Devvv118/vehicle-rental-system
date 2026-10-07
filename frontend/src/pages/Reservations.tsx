// import React from 'react';

// const Reservations: React.FC = () => {
//   return <div><h1>Reservations</h1><p>Under construction</p></div>;
// };

// export default Reservations;

// pages/Reservations.tsx - Complete Reservations Component
import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { reservationApi } from '../services/api';
import type { Reservation } from '../types';

const Reservations: React.FC = () => {
  const [reservations, setReservations] = useState<Reservation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<'all' | 'active'>('all');

  useEffect(() => {
    fetchReservations();
  }, [filter]);

  const fetchReservations = async () => {
    try {
      setLoading(true);
      const data = filter === 'active' 
        ? await reservationApi.getActive()
        : await reservationApi.getAll();
      setReservations(data);
    } catch (err) {
      setError('Failed to load reservations');
      console.error('Error fetching reservations:', err);
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
    return <div className="loading"><div className="loading-spinner">Loading reservations...</div></div>;
  }

  if (error) {
    return (
      <div className="error">
        <div className="error-message">
          <p>{error}</p>
          <button onClick={fetchReservations} className="retry-button">Retry</button>
        </div>
      </div>
    );
  }

  return (
    <div className="reservations">
      <div className="page-header">
        <div className="header-left">
          <h1>Reservations</h1>
          <p>Manage customer reservations</p>
        </div>
        <div className="header-right">
          <Link to="/reservations/new" className="btn btn-primary">New Reservation</Link>
        </div>
      </div>

      <div style={{ marginBottom: '24px', display: 'flex', gap: '12px' }}>
        <button
          className={`btn ${filter === 'all' ? 'btn-primary' : 'btn-outline'}`}
          onClick={() => setFilter('all')}
        >
          All Reservations
        </button>
        <button
          className={`btn ${filter === 'active' ? 'btn-primary' : 'btn-outline'}`}
          onClick={() => setFilter('active')}
        >
          Active Reservations
        </button>
      </div>

      <div className="reservations-table">
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>Customer ID</th>
              <th>Vehicle ID</th>
              <th>Pickup Date</th>
              <th>Return Date</th>
              <th>Pickup Location</th>
              <th>Status</th>
              <th>Estimated Total</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {reservations.map((reservation) => (
              <tr key={reservation.reservation_id}>
                <td>{reservation.reservation_id}</td>
                <td>#{reservation.customer_id}</td>
                <td>#{reservation.vehicle_id}</td>
                <td>{formatDate(reservation.reserved_start_date)}</td>
                <td>{formatDate(reservation.reserved_end_date)}</td>
                <td>#{reservation.pickup_location_id}</td>
                <td>
                  <span className={`status-badge ${reservation.status.toLowerCase()}`}>
                    {reservation.status}
                  </span>
                </td>
                <td>{reservation.estimated_total ? formatCurrency(reservation.estimated_total) : 'TBD'}</td>
                <td>
                  <div className="actions">
                    <button className="btn btn-sm btn-outline">View</button>
                    {reservation.status === 'Confirmed' && (
                      <button className="btn btn-sm btn-primary">Convert to Rental</button>
                    )}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        {reservations.length === 0 && (
          <div className="no-data">
            <p>No reservations found.</p>
            <Link to="/reservations/new" className="btn btn-primary">
              Create First Reservation
            </Link>
          </div>
        )}
      </div>
    </div>
  );
};

export default Reservations;