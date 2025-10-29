// import React from 'react';
// import { useParams } from 'react-router-dom';

// const RentalDetail: React.FC = () => {
//   const { id } = useParams<{ id: string }>();
//   return <div><h1>Rental Detail - ID: {id}</h1><p>Under construction</p></div>;
// };

// export default RentalDetail;

import React, { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { rentalApi, paymentApi, incidentApi } from '../services/api';
import type { RentalWithDetails, Payment, IncidentReport } from '../types';

const RentalDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [rental, setRental] = useState<RentalWithDetails | null>(null);
  const [payments, setPayments] = useState<Payment[]>([]);
  const [incidents, setIncidents] = useState<IncidentReport[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showReturnModal, setShowReturnModal] = useState(false);
  const [returnData, setReturnData] = useState({
    mileage_end: 0,
    fuel_level_end: 1.0,
    late_fees: 0,
    damage_fees: 0,
  });

  useEffect(() => {
    if (id) {
      fetchRentalData(parseInt(id));
    }
  }, [id]);

  const fetchRentalData = async (rentalId: number) => {
    try {
      setLoading(true);
      setError(null);

      const [rentalData, paymentsData, incidentsData] = await Promise.all([
        rentalApi.getById(rentalId),
        paymentApi.getByRental(rentalId),
        incidentApi.getByRental(rentalId),
      ]);

      setRental(rentalData);
      setPayments(paymentsData);
      setIncidents(incidentsData);

      // Initialize return mileage with vehicle's current mileage
      if (rentalData.vehicle?.mileage) {
        setReturnData(prev => ({
          ...prev,
          mileage_end: rentalData.vehicle!.mileage,
        }));
      }
    } catch (err) {
      setError('Failed to load rental data');
      console.error('Error fetching rental data:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleReturnVehicle = async () => {
    if (!rental) return;

    // Calculate late fees if applicable
    const endDate = new Date(rental.end_date);
    const now = new Date();
    if (now > endDate) {
      const daysLate = Math.ceil((now.getTime() - endDate.getTime()) / (1000 * 60 * 60 * 24));
      const lateFee = daysLate * rental.daily_rate * 0.5; // 50% of daily rate per late day
      setReturnData(prev => ({
        ...prev,
        late_fees: lateFee,
      }));
    }

    try {
      setLoading(true);
      await rentalApi.returnVehicle(rental.rental_id, returnData);
      setShowReturnModal(false);
      
      // Refresh rental data
      if (id) {
        await fetchRentalData(parseInt(id));
      }
    } catch (err) {
      alert('Failed to return vehicle. Please try again.');
      console.error('Error returning vehicle:', err);
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(amount);
  };

  const calculateRentalDuration = () => {
    if (!rental) return 0;
    const start = new Date(rental.start_date);
    const end = rental.actual_return_date 
      ? new Date(rental.actual_return_date)
      : new Date(rental.end_date);
    return Math.ceil((end.getTime() - start.getTime()) / (1000 * 60 * 60 * 24));
  };

  const calculateTotalPaid = () => {
    return payments
      .filter(p => p.status === 'Completed')
      .reduce((sum, payment) => sum + payment.amount, 0);
  };

  const isOverdue = () => {
    if (!rental || rental.status !== 'Active') return false;
    return new Date() > new Date(rental.end_date);
  };

  if (loading) {
    return (
      <div className="loading">
        <div className="loading-spinner">Loading rental details...</div>
      </div>
    );
  }

  if (error || !rental) {
    return (
      <div className="error">
        <div className="error-message">
          <p>{error || 'Rental not found'}</p>
          <Link to="/rentals" className="btn btn-primary">
            Back to Rentals
          </Link>
        </div>
      </div>
    );
  }

  const totalPaid = calculateTotalPaid();
  const balance = rental.total_amount + rental.late_fees + rental.damage_fees - totalPaid;

  return (
    <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
      <div className="page-header">
        <div className="header-left">
          <h1>Rental #{rental.rental_id}</h1>
          <p>Complete rental information and history</p>
        </div>
        <div className="header-right" style={{ display: 'flex', gap: '12px' }}>
          {rental.status === 'Active' && (
            <button
              onClick={() => setShowReturnModal(true)}
              className="btn btn-primary"
            >
              Return Vehicle
            </button>
          )}
          <Link to="/rentals" className="btn btn-secondary">
            Back to Rentals
          </Link>
        </div>
      </div>

      {/* Status Alert */}
      {isOverdue() && (
        <div style={{
          padding: '16px',
          backgroundColor: '#fff3cd',
          border: '1px solid #ffc107',
          borderRadius: '8px',
          marginBottom: '24px',
          color: '#856404'
        }}>
          <strong>⚠️ This rental is overdue!</strong> Expected return date was {formatDate(rental.end_date)}
        </div>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px', marginBottom: '32px' }}>
        {/* Rental Information */}
        <div style={{ background: 'white', padding: '24px', borderRadius: '8px', boxShadow: '0 2px 10px rgba(0, 0, 0, 0.1)' }}>
          <h2 style={{ marginBottom: '20px', fontSize: '18px', fontWeight: '600' }}>Rental Information</h2>
          <div style={{ display: 'grid', gap: '12px' }}>
            <div>
              <strong>Rental ID:</strong> {rental.rental_id}
            </div>
            <div>
              <strong>Status:</strong>{' '}
              <span className={`status-badge ${rental.status.toLowerCase()}`}>
                {rental.status}
              </span>
            </div>
            <div>
              <strong>Start Date:</strong> {formatDate(rental.start_date)}
            </div>
            <div>
              <strong>Expected End Date:</strong> {formatDate(rental.end_date)}
            </div>
            {rental.actual_return_date && (
              <div>
                <strong>Actual Return Date:</strong> {formatDate(rental.actual_return_date)}
              </div>
            )}
            <div>
              <strong>Duration:</strong> {calculateRentalDuration()} days
            </div>
            <div>
              <strong>Daily Rate:</strong> {formatCurrency(rental.daily_rate)}
            </div>
            <div>
              <strong>Pickup Location:</strong> {rental.pickup_location ? `${rental.pickup_location.name}` : `Location #${rental.pickup_location_id}`}
            </div>
            <div>
              <strong>Return Location:</strong> {rental.return_location ? `${rental.return_location.name}` : `Location #${rental.return_location_id}`}
            </div>
            {rental.employee && (
              <div>
                <strong>Assigned Employee:</strong> {rental.employee.first_name} {rental.employee.last_name}
              </div>
            )}
            <div>
              <strong>Created:</strong> {formatDate(rental.created_at)}
            </div>
          </div>
        </div>

        {/* Customer & Vehicle Information */}
        <div style={{ background: 'white', padding: '24px', borderRadius: '8px', boxShadow: '0 2px 10px rgba(0, 0, 0, 0.1)' }}>
          <h2 style={{ marginBottom: '20px', fontSize: '18px', fontWeight: '600' }}>Customer & Vehicle</h2>
          <div style={{ display: 'grid', gap: '16px' }}>
            <div>
              <h3 style={{ fontSize: '14px', fontWeight: '600', marginBottom: '8px', color: '#6c757d' }}>Customer</h3>
              {rental.customer ? (
                <div style={{ display: 'grid', gap: '6px' }}>
                  <div>
                    <Link to={`/customers/${rental.customer.customer_id}`} style={{ fontWeight: '600', color: '#007bff', textDecoration: 'none' }}>
                      {rental.customer.first_name} {rental.customer.last_name}
                    </Link>
                  </div>
                  <div style={{ fontSize: '14px' }}>{rental.customer.email}</div>
                  <div style={{ fontSize: '14px' }}>{rental.customer.phone}</div>
                  <div style={{ fontSize: '14px' }}>License: {rental.customer.driver_license}</div>
                </div>
              ) : (
                <div>Customer ID: {rental.customer_id}</div>
              )}
            </div>

            <div>
              <h3 style={{ fontSize: '14px', fontWeight: '600', marginBottom: '8px', color: '#6c757d' }}>Vehicle</h3>
              {rental.vehicle ? (
                <div style={{ display: 'grid', gap: '6px' }}>
                  <div>
                    <Link to={`/vehicles/${rental.vehicle.vehicle_id}`} style={{ fontWeight: '600', color: '#007bff', textDecoration: 'none' }}>
                      {rental.vehicle.year} {rental.vehicle.make} {rental.vehicle.model}
                    </Link>
                  </div>
                  <div style={{ fontSize: '14px' }}>License Plate: {rental.vehicle.license_plate}</div>
                  <div style={{ fontSize: '14px' }}>Fuel: {rental.vehicle.fuel_type} | {rental.vehicle.transmission}</div>
                  <div style={{ fontSize: '14px' }}>Capacity: {rental.vehicle.seating_capacity} passengers</div>
                </div>
              ) : (
                <div>Vehicle ID: {rental.vehicle_id}</div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Mileage & Fuel Information */}
      <div style={{ background: 'white', padding: '24px', borderRadius: '8px', boxShadow: '0 2px 10px rgba(0, 0, 0, 0.1)', marginBottom: '24px' }}>
        <h2 style={{ marginBottom: '20px', fontSize: '18px', fontWeight: '600' }}>Mileage & Fuel</h2>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px' }}>
          <div>
            <div style={{ fontSize: '14px', color: '#6c757d', marginBottom: '4px' }}>Starting Mileage</div>
            <div style={{ fontSize: '20px', fontWeight: '600' }}>
              {rental.mileage_start?.toLocaleString() || 'N/A'} miles
            </div>
          </div>
          <div>
            <div style={{ fontSize: '14px', color: '#6c757d', marginBottom: '4px' }}>Ending Mileage</div>
            <div style={{ fontSize: '20px', fontWeight: '600' }}>
              {rental.mileage_end?.toLocaleString() || 'N/A'} miles
            </div>
          </div>
          {rental.mileage_start && rental.mileage_end && (
            <div>
              <div style={{ fontSize: '14px', color: '#6c757d', marginBottom: '4px' }}>Distance Driven</div>
              <div style={{ fontSize: '20px', fontWeight: '600', color: '#28a745' }}>
                {(rental.mileage_end - rental.mileage_start).toLocaleString()} miles
              </div>
            </div>
          )}
          <div>
            <div style={{ fontSize: '14px', color: '#6c757d', marginBottom: '4px' }}>Starting Fuel Level</div>
            <div style={{ fontSize: '20px', fontWeight: '600' }}>
              {rental.fuel_level_start ? `${(rental.fuel_level_start * 100).toFixed(0)}%` : 'N/A'}
            </div>
          </div>
          <div>
            <div style={{ fontSize: '14px', color: '#6c757d', marginBottom: '4px' }}>Ending Fuel Level</div>
            <div style={{ fontSize: '20px', fontWeight: '600' }}>
              {rental.fuel_level_end ? `${(rental.fuel_level_end * 100).toFixed(0)}%` : 'N/A'}
            </div>
          </div>
        </div>
      </div>

      {/* Financial Summary */}
      <div style={{ background: 'white', padding: '24px', borderRadius: '8px', boxShadow: '0 2px 10px rgba(0, 0, 0, 0.1)', marginBottom: '24px' }}>
        <h2 style={{ marginBottom: '20px', fontSize: '18px', fontWeight: '600' }}>Financial Summary</h2>
        <div style={{ display: 'grid', gap: '12px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', padding: '12px', backgroundColor: '#f8f9fa', borderRadius: '6px' }}>
            <span>Base Rental Amount:</span>
            <strong>{formatCurrency(rental.total_amount)}</strong>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', padding: '12px', backgroundColor: '#f8f9fa', borderRadius: '6px' }}>
            <span>Security Deposit:</span>
            <strong>{formatCurrency(rental.security_deposit)}</strong>
          </div>
          {rental.discount_applied > 0 && (
            <div style={{ display: 'flex', justifyContent: 'space-between', padding: '12px', backgroundColor: '#d4edda', borderRadius: '6px' }}>
              <span>Discount Applied:</span>
              <strong style={{ color: '#28a745' }}>-{formatCurrency(rental.discount_applied)}</strong>
            </div>
          )}
          {rental.late_fees > 0 && (
            <div style={{ display: 'flex', justifyContent: 'space-between', padding: '12px', backgroundColor: '#fff3cd', borderRadius: '6px' }}>
              <span>Late Fees:</span>
              <strong style={{ color: '#856404' }}>+{formatCurrency(rental.late_fees)}</strong>
            </div>
          )}
          {rental.damage_fees > 0 && (
            <div style={{ display: 'flex', justifyContent: 'space-between', padding: '12px', backgroundColor: '#f8d7da', borderRadius: '6px' }}>
              <span>Damage Fees:</span>
              <strong style={{ color: '#721c24' }}>+{formatCurrency(rental.damage_fees)}</strong>
            </div>
          )}
          <div style={{ display: 'flex', justifyContent: 'space-between', padding: '12px', backgroundColor: '#e3f2fd', borderRadius: '6px' }}>
            <span>Total Paid:</span>
            <strong style={{ color: '#007bff' }}>{formatCurrency(totalPaid)}</strong>
          </div>
          <div style={{ 
            display: 'flex', 
            justifyContent: 'space-between', 
            padding: '16px', 
            backgroundColor: balance > 0 ? '#fff3cd' : '#d4edda', 
            borderRadius: '6px',
            fontSize: '18px',
            fontWeight: '600',
            borderTop: '2px solid #dee2e6'
          }}>
            <span>Balance:</span>
            <strong style={{ color: balance > 0 ? '#856404' : '#28a745' }}>
              {formatCurrency(Math.abs(balance))} {balance > 0 ? 'Due' : balance < 0 ? 'Overpaid' : 'Paid'}
            </strong>
          </div>
        </div>
      </div>

      {/* Payments */}
      <div style={{ background: 'white', borderRadius: '8px', boxShadow: '0 2px 10px rgba(0, 0, 0, 0.1)', marginBottom: '24px' }}>
        <div style={{ padding: '20px 24px', borderBottom: '1px solid #dee2e6', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h2 style={{ fontSize: '18px', fontWeight: '600', margin: '0' }}>
            Payments ({payments.length})
          </h2>
        </div>
        <div style={{ padding: '24px' }}>
          {payments.length === 0 ? (
            <p style={{ color: '#6c757d', textAlign: 'center', padding: '20px' }}>
              No payments recorded
            </p>
          ) : (
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', minWidth: '600px' }}>
                <thead>
                  <tr style={{ backgroundColor: '#f8f9fa' }}>
                    <th style={{ padding: '12px', textAlign: 'left', fontWeight: '600' }}>Date</th>
                    <th style={{ padding: '12px', textAlign: 'left', fontWeight: '600' }}>Amount</th>
                    <th style={{ padding: '12px', textAlign: 'left', fontWeight: '600' }}>Method</th>
                    <th style={{ padding: '12px', textAlign: 'left', fontWeight: '600' }}>Type</th>
                    <th style={{ padding: '12px', textAlign: 'left', fontWeight: '600' }}>Status</th>
                    <th style={{ padding: '12px', textAlign: 'left', fontWeight: '600' }}>Transaction ID</th>
                  </tr>
                </thead>
                <tbody>
                  {payments.map((payment) => (
                    <tr key={payment.payment_id}>
                      <td style={{ padding: '12px' }}>{formatDate(payment.payment_date)}</td>
                      <td style={{ padding: '12px', fontWeight: '600' }}>
                        {formatCurrency(payment.amount)}
                      </td>
                      <td style={{ padding: '12px' }}>{payment.method}</td>
                      <td style={{ padding: '12px' }}>{payment.payment_type}</td>
                      <td style={{ padding: '12px' }}>
                        <span className={`status-badge ${payment.status.toLowerCase()}`}>
                          {payment.status}
                        </span>
                      </td>
                      <td style={{ padding: '12px', fontSize: '12px', color: '#6c757d' }}>
                        {payment.transaction_id || 'N/A'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

      {/* Incidents */}
      <div style={{ background: 'white', borderRadius: '8px', boxShadow: '0 2px 10px rgba(0, 0, 0, 0.1)' }}>
        <div style={{ padding: '20px 24px', borderBottom: '1px solid #dee2e6', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h2 style={{ fontSize: '18px', fontWeight: '600', margin: '0' }}>
            Incident Reports ({incidents.length})
          </h2>
          <Link to={`/incidents/new?rental_id=${rental.rental_id}`} className="btn btn-primary">
            Report Incident
          </Link>
        </div>
        <div style={{ padding: '24px' }}>
          {incidents.length === 0 ? (
            <p style={{ color: '#6c757d', textAlign: 'center', padding: '20px' }}>
              No incidents reported
            </p>
          ) : (
            <div style={{ display: 'grid', gap: '16px' }}>
              {incidents.map((incident) => (
                <div
                  key={incident.incident_id}
                  style={{
                    padding: '16px',
                    backgroundColor: '#f8f9fa',
                    borderRadius: '8px',
                    border: '1px solid #dee2e6',
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '12px' }}>
                    <div>
                      <strong>{incident.incident_type}</strong>
                      <div style={{ fontSize: '14px', color: '#6c757d' }}>
                        {formatDate(incident.incident_date)}
                      </div>
                    </div>
                    <span className={`status-badge ${incident.status.toLowerCase().replace(' ', '-')}`}>
                      {incident.status}
                    </span>
                  </div>
                  <div style={{ marginBottom: '8px' }}>{incident.description}</div>
                  {incident.estimated_cost && (
                    <div style={{ fontSize: '14px', fontWeight: '600', color: '#dc3545' }}>
                      Estimated Cost: {formatCurrency(incident.estimated_cost)}
                    </div>
                  )}
                  {incident.police_report_number && (
                    <div style={{ fontSize: '14px', color: '#6c757d', marginTop: '8px' }}>
                      Police Report: {incident.police_report_number}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Return Vehicle Modal */}
      {showReturnModal && (
        <div
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: 'rgba(0, 0, 0, 0.5)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1000,
          }}
          onClick={() => setShowReturnModal(false)}
        >
          <div
            style={{
              backgroundColor: 'white',
              padding: '32px',
              borderRadius: '12px',
              maxWidth: '500px',
              width: '90%',
              maxHeight: '90vh',
              overflowY: 'auto',
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <h2 style={{ marginBottom: '24px' }}>Return Vehicle</h2>
            
            <div className="form-group">
              <label className="form-label">Ending Mileage *</label>
              <input
                type="number"
                className="form-input"
                value={returnData.mileage_end}
                onChange={(e) =>
                  setReturnData({ ...returnData, mileage_end: parseInt(e.target.value) })
                }
                min={rental.mileage_start || 0}
              />
            </div>

            <div className="form-group">
              <label className="form-label">Ending Fuel Level (0-1) *</label>
              <input
                type="number"
                className="form-input"
                value={returnData.fuel_level_end}
                onChange={(e) =>
                  setReturnData({ ...returnData, fuel_level_end: parseFloat(e.target.value) })
                }
                min="0"
                max="1"
                step="0.01"
              />
            </div>

            <div className="form-group">
              <label className="form-label">Late Fees (USD)</label>
              <input
                type="number"
                className="form-input"
                value={returnData.late_fees}
                onChange={(e) =>
                  setReturnData({ ...returnData, late_fees: parseFloat(e.target.value) })
                }
                min="0"
                step="0.01"
              />
            </div>

            <div className="form-group">
              <label className="form-label">Damage Fees (USD)</label>
              <input
                type="number"
                className="form-input"
                value={returnData.damage_fees}
                onChange={(e) =>
                  setReturnData({ ...returnData, damage_fees: parseFloat(e.target.value) })
                }
                min="0"
                step="0.01"
              />
            </div>

            <div style={{ display: 'flex', gap: '12px', marginTop: '24px' }}>
              <button
                onClick={() => setShowReturnModal(false)}
                className="btn btn-secondary"
                style={{ flex: 1 }}
              >
                Cancel
              </button>
              <button
                onClick={handleReturnVehicle}
                className="btn btn-primary"
                style={{ flex: 1 }}
                disabled={loading}
              >
                {loading ? 'Processing...' : 'Complete Return'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default RentalDetail;