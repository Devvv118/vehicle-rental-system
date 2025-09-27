import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { customerApi, rentalApi, reservationApi } from '../services/api';
import type { CustomerWithProfile, Rental, Reservation } from '../types';

const CustomerDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [customer, setCustomer] = useState<CustomerWithProfile | null>(null);
  const [rentals, setRentals] = useState<Rental[]>([]);
  const [reservations, setReservations] = useState<Reservation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (id) {
      fetchCustomerData(parseInt(id));
    }
  }, [id]);

  const fetchCustomerData = async (customerId: number) => {
    try {
      setLoading(true);
      setError(null);

      const [customerData, customerRentals, customerReservations] = await Promise.all([
        customerApi.getById(customerId),
        rentalApi.getByCustomer(customerId),
        reservationApi.getByCustomer(customerId),
      ]);

      setCustomer(customerData);
      setRentals(customerRentals);
      setReservations(customerReservations);
    } catch (err) {
      setError('Failed to load customer data');
      console.error('Error fetching customer data:', err);
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
    return (
      <div className="loading">
        <div className="loading-spinner">Loading customer details...</div>
      </div>
    );
  }

  if (error || !customer) {
    return (
      <div className="error">
        <div className="error-message">
          <p>{error || 'Customer not found'}</p>
          <Link to="/customers" className="btn btn-primary">
            Back to Customers
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
      <div className="page-header">
        <div className="header-left">
          <h1>{customer.first_name} {customer.last_name}</h1>
          <p>Customer details and rental history</p>
        </div>
        <div className="header-right">
          <Link
            to={`/customers/${customer.customer_id}/edit`}
            className="btn btn-primary"
          >
            Edit Customer
          </Link>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px', marginBottom: '32px' }}>
        {/* Customer Information */}
        <div style={{ background: 'white', padding: '24px', borderRadius: '8px', boxShadow: '0 2px 10px rgba(0, 0, 0, 0.1)' }}>
          <h2 style={{ marginBottom: '20px', fontSize: '18px', fontWeight: '600' }}>Customer Information</h2>
          <div style={{ display: 'grid', gap: '12px' }}>
            <div>
              <strong>Customer ID:</strong> {customer.customer_id}
            </div>
            <div>
              <strong>Name:</strong> {customer.first_name} {customer.last_name}
            </div>
            <div>
              <strong>Email:</strong> {customer.email}
            </div>
            <div>
              <strong>Phone:</strong> {customer.phone}
            </div>
            <div>
              <strong>Driver License:</strong> {customer.driver_license}
            </div>
            <div>
              <strong>Date of Birth:</strong> {customer.date_of_birth ? formatDate(customer.date_of_birth) : 'Not provided'}
            </div>
            <div>
              <strong>Address:</strong> {customer.address || 'Not provided'}
            </div>
            <div>
              <strong>Member Since:</strong> {formatDate(customer.created_at)}
            </div>
          </div>
        </div>

        {/* Membership Information */}
        <div style={{ background: 'white', padding: '24px', borderRadius: '8px', boxShadow: '0 2px 10px rgba(0, 0, 0, 0.1)' }}>
          <h2 style={{ marginBottom: '20px', fontSize: '18px', fontWeight: '600' }}>Membership Information</h2>
          {customer.membership_profile ? (
            <div style={{ display: 'grid', gap: '12px' }}>
              <div>
                <strong>Membership Tier:</strong> {customer.membership_profile.membership_tier}
              </div>
              <div>
                <strong>Tier Level:</strong> {customer.membership_profile.tier_level}
              </div>
              <div>
                <strong>Points Balance:</strong> {customer.membership_profile.points_balance.toLocaleString()}
              </div>
              <div>
                <strong>Lifetime Rentals:</strong> {customer.membership_profile.lifetime_rentals}
              </div>
              <div>
                <strong>Lifetime Spending:</strong> {formatCurrency(customer.membership_profile.lifetime_spending)}
              </div>
              <div>
                <strong>Join Date:</strong> {formatDate(customer.membership_profile.join_date)}
              </div>
              <div>
                <strong>Last Activity:</strong> {customer.membership_profile.last_activity_date ? formatDate(customer.membership_profile.last_activity_date) : 'Never'}
              </div>
            </div>
          ) : (
            <p style={{ color: '#6c757d' }}>No membership profile found</p>
          )}
        </div>
      </div>

      {/* Vehicle Preferences */}
      {customer.vehicle_preferences && customer.vehicle_preferences.length > 0 && (
        <div style={{ background: 'white', padding: '24px', borderRadius: '8px', boxShadow: '0 2px 10px rgba(0, 0, 0, 0.1)', marginBottom: '24px' }}>
          <h2 style={{ marginBottom: '20px', fontSize: '18px', fontWeight: '600' }}>Vehicle Preferences</h2>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px' }}>
            {customer.vehicle_preferences.map((pref, index) => (
              <div key={index} style={{ padding: '12px', backgroundColor: '#f8f9fa', borderRadius: '6px', border: '1px solid #dee2e6' }}>
                <div><strong>{pref.vehicle_type}</strong></div>
                <div style={{ color: '#6c757d', fontSize: '14px' }}>
                  Score: {pref.preference_score || 'Not rated'}/10
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Rental History */}
      <div style={{ background: 'white', borderRadius: '8px', boxShadow: '0 2px 10px rgba(0, 0, 0, 0.1)', marginBottom: '24px' }}>
        <div style={{ padding: '20px 24px', borderBottom: '1px solid #dee2e6', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h2 style={{ fontSize: '18px', fontWeight: '600', margin: '0' }}>Rental History ({rentals.length})</h2>
          <Link to={`/rentals/new?customer_id=${customer.customer_id}`} className="btn btn-primary">
            New Rental
          </Link>
        </div>
        <div style={{ padding: '24px' }}>
          {rentals.length === 0 ? (
            <p style={{ color: '#6c757d', textAlign: 'center', padding: '20px' }}>No rentals found</p>
          ) : (
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', minWidth: '600px' }}>
                <thead>
                  <tr style={{ backgroundColor: '#f8f9fa' }}>
                    <th style={{ padding: '12px', textAlign: 'left', fontWeight: '600' }}>Rental ID</th>
                    <th style={{ padding: '12px', textAlign: 'left', fontWeight: '600' }}>Vehicle</th>
                    <th style={{ padding: '12px', textAlign: 'left', fontWeight: '600' }}>Start Date</th>
                    <th style={{ padding: '12px', textAlign: 'left', fontWeight: '600' }}>End Date</th>
                    <th style={{ padding: '12px', textAlign: 'left', fontWeight: '600' }}>Status</th>
                    <th style={{ padding: '12px', textAlign: 'left', fontWeight: '600' }}>Total</th>
                    <th style={{ padding: '12px', textAlign: 'left', fontWeight: '600' }}>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {rentals.map((rental) => (
                    <tr key={rental.rental_id}>
                      <td style={{ padding: '12px' }}>{rental.rental_id}</td>
                      <td style={{ padding: '12px' }}>Vehicle #{rental.vehicle_id}</td>
                      <td style={{ padding: '12px' }}>{formatDate(rental.start_date)}</td>
                      <td style={{ padding: '12px' }}>{formatDate(rental.end_date)}</td>
                      <td style={{ padding: '12px' }}>
                        <span className={`status-badge ${rental.status.toLowerCase()}`}>
                          {rental.status}
                        </span>
                      </td>
                      <td style={{ padding: '12px', fontWeight: '600' }}>
                        {formatCurrency(rental.total_amount)}
                      </td>
                      <td style={{ padding: '12px' }}>
                        <Link
                          to={`/rentals/${rental.rental_id}`}
                          className="btn btn-sm btn-outline"
                        >
                          View
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

      {/* Current Reservations */}
      <div style={{ background: 'white', borderRadius: '8px', boxShadow: '0 2px 10px rgba(0, 0, 0, 0.1)' }}>
        <div style={{ padding: '20px 24px', borderBottom: '1px solid #dee2e6', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h2 style={{ fontSize: '18px', fontWeight: '600', margin: '0' }}>Reservations ({reservations.length})</h2>
          <Link to={`/reservations/new?customer_id=${customer.customer_id}`} className="btn btn-primary">
            New Reservation
          </Link>
        </div>
        <div style={{ padding: '24px' }}>
          {reservations.length === 0 ? (
            <p style={{ color: '#6c757d', textAlign: 'center', padding: '20px' }}>No reservations found</p>
          ) : (
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', minWidth: '600px' }}>
                <thead>
                  <tr style={{ backgroundColor: '#f8f9fa' }}>
                    <th style={{ padding: '12px', textAlign: 'left', fontWeight: '600' }}>Reservation ID</th>
                    <th style={{ padding: '12px', textAlign: 'left', fontWeight: '600' }}>Vehicle</th>
                    <th style={{ padding: '12px', textAlign: 'left', fontWeight: '600' }}>Start Date</th>
                    <th style={{ padding: '12px', textAlign: 'left', fontWeight: '600' }}>End Date</th>
                    <th style={{ padding: '12px', textAlign: 'left', fontWeight: '600' }}>Status</th>
                    <th style={{ padding: '12px', textAlign: 'left', fontWeight: '600' }}>Estimated Total</th>
                    <th style={{ padding: '12px', textAlign: 'left', fontWeight: '600' }}>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {reservations.map((reservation) => (
                    <tr key={reservation.reservation_id}>
                      <td style={{ padding: '12px' }}>{reservation.reservation_id}</td>
                      <td style={{ padding: '12px' }}>Vehicle #{reservation.vehicle_id}</td>
                      <td style={{ padding: '12px' }}>{formatDate(reservation.reserved_start_date)}</td>
                      <td style={{ padding: '12px' }}>{formatDate(reservation.reserved_end_date)}</td>
                      <td style={{ padding: '12px' }}>
                        <span className={`status-badge ${reservation.status.toLowerCase()}`}>
                          {reservation.status}
                        </span>
                      </td>
                      <td style={{ padding: '12px', fontWeight: '600' }}>
                        {reservation.estimated_total ? formatCurrency(reservation.estimated_total) : 'TBD'}
                      </td>
                      <td style={{ padding: '12px' }}>
                        <div style={{ display: 'flex', gap: '6px' }}>
                          <Link
                            to={`/reservations/${reservation.reservation_id}`}
                            className="btn btn-sm btn-outline"
                          >
                            View
                          </Link>
                          {reservation.status === 'Confirmed' && (
                            <button className="btn btn-sm btn-primary">
                              Convert to Rental
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default CustomerDetail;