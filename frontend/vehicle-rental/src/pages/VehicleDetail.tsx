// import React from 'react';
// import { useParams } from 'react-router-dom';

// const VehicleDetail: React.FC = () => {
//   const { id } = useParams<{ id: string }>();
  
//   return (
//     <div>
//       <h1>Vehicle Detail - ID: {id}</h1>
//       <p>Vehicle detail page is under construction.</p>
//     </div>
//   );
// };

// export default VehicleDetail;

import React, { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { vehicleApi, maintenanceApi, rentalApi } from '../services/api';
import type { VehicleWithFeatures, MaintenanceSchedule, Rental } from '../types';

const VehicleDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [vehicle, setVehicle] = useState<VehicleWithFeatures | null>(null);
  const [maintenance, setMaintenance] = useState<MaintenanceSchedule[]>([]);
  const [rentals, setRentals] = useState<Rental[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (id) {
      fetchVehicleData(parseInt(id));
    }
  }, [id]);

  const fetchVehicleData = async (vehicleId: number) => {
    try {
      setLoading(true);
      setError(null);

      const [vehicleData, maintenanceData, rentalData] = await Promise.all([
        vehicleApi.getById(vehicleId),
        maintenanceApi.getByVehicle(vehicleId),
        rentalApi.filter({ vehicle_id: vehicleId }, 0, 10),
      ]);

      setVehicle(vehicleData);
      setMaintenance(maintenanceData);
      setRentals(rentalData);
    } catch (err) {
      setError('Failed to load vehicle data');
      console.error('Error fetching vehicle data:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleToggleAvailability = async () => {
    if (!vehicle) return;

    try {
      await vehicleApi.updateAvailability(vehicle.vehicle_id, !vehicle.availability);
      setVehicle({
        ...vehicle,
        availability: !vehicle.availability,
      });
    } catch (err) {
      alert('Failed to update vehicle availability');
      console.error('Error updating availability:', err);
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
        <div className="loading-spinner">Loading vehicle details...</div>
      </div>
    );
  }

  if (error || !vehicle) {
    return (
      <div className="error">
        <div className="error-message">
          <p>{error || 'Vehicle not found'}</p>
          <Link to="/vehicles" className="btn btn-primary">
            Back to Vehicles
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
      <div className="page-header">
        <div className="header-left">
          <h1>{vehicle.year} {vehicle.make} {vehicle.model}</h1>
          <p>Vehicle details and maintenance history</p>
        </div>
        <div className="header-right" style={{ display: 'flex', gap: '12px' }}>
          <button
            onClick={handleToggleAvailability}
            className={`btn ${vehicle.availability ? 'btn-secondary' : 'btn-primary'}`}
          >
            {vehicle.availability ? 'Mark Unavailable' : 'Mark Available'}
          </button>
          <Link
            to={`/vehicles/${vehicle.vehicle_id}/edit`}
            className="btn btn-primary"
          >
            Edit Vehicle
          </Link>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px', marginBottom: '32px' }}>
        {/* Vehicle Information */}
        <div style={{ background: 'white', padding: '24px', borderRadius: '8px', boxShadow: '0 2px 10px rgba(0, 0, 0, 0.1)' }}>
          <h2 style={{ marginBottom: '20px', fontSize: '18px', fontWeight: '600' }}>Vehicle Information</h2>
          <div style={{ display: 'grid', gap: '12px' }}>
            <div>
              <strong>Vehicle ID:</strong> {vehicle.vehicle_id}
            </div>
            <div>
              <strong>Make & Model:</strong> {vehicle.make} {vehicle.model}
            </div>
            <div>
              <strong>Year:</strong> {vehicle.year}
            </div>
            <div>
              <strong>License Plate:</strong> {vehicle.license_plate}
            </div>
            <div>
              <strong>Fuel Type:</strong> {vehicle.fuel_type}
            </div>
            <div>
              <strong>Transmission:</strong> {vehicle.transmission}
            </div>
            <div>
              <strong>Seating Capacity:</strong> {vehicle.seating_capacity} passengers
            </div>
            <div>
              <strong>Daily Rate:</strong> {formatCurrency(vehicle.daily_rate)}
            </div>
            <div>
              <strong>Current Mileage:</strong> {vehicle.mileage.toLocaleString()} miles
            </div>
            <div>
              <strong>Status:</strong>{' '}
              <span className={`status-badge ${vehicle.availability ? 'active' : 'cancelled'}`}>
                {vehicle.availability ? 'Available' : 'Unavailable'}
              </span>
            </div>
            <div>
              <strong>Location ID:</strong> {vehicle.location_id || 'Not assigned'}
            </div>
            <div>
              <strong>Added:</strong> {formatDate(vehicle.created_at)}
            </div>
          </div>
        </div>

        {/* Maintenance Information */}
        <div style={{ background: 'white', padding: '24px', borderRadius: '8px', boxShadow: '0 2px 10px rgba(0, 0, 0, 0.1)' }}>
          <h2 style={{ marginBottom: '20px', fontSize: '18px', fontWeight: '600' }}>Maintenance Information</h2>
          {vehicle.maintenance_record ? (
            <div style={{ display: 'grid', gap: '12px' }}>
              <div>
                <strong>Current Condition:</strong>{' '}
                <span
                  style={{
                    padding: '4px 8px',
                    borderRadius: '12px',
                    fontSize: '12px',
                    fontWeight: '600',
                    backgroundColor:
                      vehicle.maintenance_record.current_condition === 'Excellent'
                        ? '#d4edda'
                        : vehicle.maintenance_record.current_condition === 'Good'
                        ? '#d1ecf1'
                        : vehicle.maintenance_record.current_condition === 'Fair'
                        ? '#fff3cd'
                        : '#f8d7da',
                    color:
                      vehicle.maintenance_record.current_condition === 'Excellent'
                        ? '#155724'
                        : vehicle.maintenance_record.current_condition === 'Good'
                        ? '#0c5460'
                        : vehicle.maintenance_record.current_condition === 'Fair'
                        ? '#856404'
                        : '#721c24',
                  }}
                >
                  {vehicle.maintenance_record.current_condition}
                </span>
              </div>
              <div>
                <strong>Last Service:</strong>{' '}
                {vehicle.maintenance_record.last_service_date
                  ? formatDate(vehicle.maintenance_record.last_service_date)
                  : 'Never'}
              </div>
              <div>
                <strong>Next Service Due:</strong>{' '}
                {vehicle.maintenance_record.next_service_due
                  ? formatDate(vehicle.maintenance_record.next_service_due)
                  : 'Not scheduled'}
              </div>
              <div>
                <strong>Total Maintenance Cost:</strong>{' '}
                {formatCurrency(vehicle.maintenance_record.total_maintenance_cost)}
              </div>
              {vehicle.maintenance_record.maintenance_alerts && (
                <div>
                  <strong>Alerts:</strong>
                  <div style={{ marginTop: '8px', padding: '12px', backgroundColor: '#fff3cd', borderRadius: '6px', fontSize: '14px' }}>
                    {vehicle.maintenance_record.maintenance_alerts}
                  </div>
                </div>
              )}
              {vehicle.maintenance_record.service_history && (
                <div>
                  <strong>Service History:</strong>
                  <div style={{ marginTop: '8px', padding: '12px', backgroundColor: '#f8f9fa', borderRadius: '6px', fontSize: '14px', whiteSpace: 'pre-wrap' }}>
                    {vehicle.maintenance_record.service_history}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <p style={{ color: '#6c757d' }}>No maintenance record found</p>
          )}
        </div>
      </div>

      {/* Vehicle Features */}
      {vehicle.features && vehicle.features.length > 0 && (
        <div style={{ background: 'white', padding: '24px', borderRadius: '8px', boxShadow: '0 2px 10px rgba(0, 0, 0, 0.1)', marginBottom: '24px' }}>
          <h2 style={{ marginBottom: '20px', fontSize: '18px', fontWeight: '600' }}>Vehicle Features</h2>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '16px' }}>
            {vehicle.features.map((feature) => (
              <div
                key={feature.feature_id}
                style={{
                  padding: '16px',
                  backgroundColor: '#f8f9fa',
                  borderRadius: '8px',
                  border: '1px solid #dee2e6',
                }}
              >
                <div style={{ fontWeight: '600', marginBottom: '4px' }}>{feature.name}</div>
                {feature.description && (
                  <div style={{ fontSize: '14px', color: '#6c757d', marginBottom: '4px' }}>
                    {feature.description}
                  </div>
                )}
                {feature.category && (
                  <div style={{ fontSize: '12px', color: '#6c757d' }}>
                    Category: {feature.category}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Maintenance Schedule */}
      <div style={{ background: 'white', borderRadius: '8px', boxShadow: '0 2px 10px rgba(0, 0, 0, 0.1)', marginBottom: '24px' }}>
        <div style={{ padding: '20px 24px', borderBottom: '1px solid #dee2e6', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h2 style={{ fontSize: '18px', fontWeight: '600', margin: '0' }}>
            Maintenance Schedule ({maintenance.length})
          </h2>
          <Link to={`/maintenance/new?vehicle_id=${vehicle.vehicle_id}`} className="btn btn-primary">
            Schedule Maintenance
          </Link>
        </div>
        <div style={{ padding: '24px' }}>
          {maintenance.length === 0 ? (
            <p style={{ color: '#6c757d', textAlign: 'center', padding: '20px' }}>
              No maintenance scheduled
            </p>
          ) : (
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', minWidth: '600px' }}>
                <thead>
                  <tr style={{ backgroundColor: '#f8f9fa' }}>
                    <th style={{ padding: '12px', textAlign: 'left', fontWeight: '600' }}>Type</th>
                    <th style={{ padding: '12px', textAlign: 'left', fontWeight: '600' }}>Scheduled Date</th>
                    <th style={{ padding: '12px', textAlign: 'left', fontWeight: '600' }}>Completed Date</th>
                    <th style={{ padding: '12px', textAlign: 'left', fontWeight: '600' }}>Cost</th>
                    <th style={{ padding: '12px', textAlign: 'left', fontWeight: '600' }}>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {maintenance.map((schedule) => (
                    <tr key={schedule.schedule_id}>
                      <td style={{ padding: '12px' }}>{schedule.maintenance_type}</td>
                      <td style={{ padding: '12px' }}>{formatDate(schedule.scheduled_date)}</td>
                      <td style={{ padding: '12px' }}>
                        {schedule.completed_date ? formatDate(schedule.completed_date) : 'N/A'}
                      </td>
                      <td style={{ padding: '12px' }}>
                        {schedule.cost ? formatCurrency(schedule.cost) : 'N/A'}
                      </td>
                      <td style={{ padding: '12px' }}>
                        <span className={`status-badge ${schedule.status.toLowerCase().replace(' ', '-')}`}>
                          {schedule.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

      {/* Rental History */}
      <div style={{ background: 'white', borderRadius: '8px', boxShadow: '0 2px 10px rgba(0, 0, 0, 0.1)' }}>
        <div style={{ padding: '20px 24px', borderBottom: '1px solid #dee2e6', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h2 style={{ fontSize: '18px', fontWeight: '600', margin: '0' }}>
            Recent Rentals ({rentals.length})
          </h2>
        </div>
        <div style={{ padding: '24px' }}>
          {rentals.length === 0 ? (
            <p style={{ color: '#6c757d', textAlign: 'center', padding: '20px' }}>
              No rental history
            </p>
          ) : (
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', minWidth: '600px' }}>
                <thead>
                  <tr style={{ backgroundColor: '#f8f9fa' }}>
                    <th style={{ padding: '12px', textAlign: 'left', fontWeight: '600' }}>Rental ID</th>
                    <th style={{ padding: '12px', textAlign: 'left', fontWeight: '600' }}>Customer ID</th>
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
                      <td style={{ padding: '12px' }}>#{rental.customer_id}</td>
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
    </div>
  );
};

export default VehicleDetail;