import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { vehicleApi } from '../services/api';
import type { Vehicle } from '../types';

const Vehicles: React.FC = () => {
  const [vehicles, setVehicles] = useState<Vehicle[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchVehicles();
  }, []);

  const fetchVehicles = async () => {
    try {
      setLoading(true);
      const data = await vehicleApi.getAll();
      setVehicles(data);
    } catch (err) {
      setError('Failed to load vehicles');
      console.error('Error fetching vehicles:', err);
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(amount);
  };

  if (loading) {
    return <div className="loading"><div className="loading-spinner">Loading vehicles...</div></div>;
  }

  if (error) {
    return (
      <div className="error">
        <div className="error-message">
          <p>{error}</p>
          <button onClick={fetchVehicles} className="retry-button">Retry</button>
        </div>
      </div>
    );
  }

  return (
    <div className="vehicles">
      <div className="page-header">
        <div className="header-left">
          <h1>Vehicles</h1>
          <p>Manage your vehicle fleet</p>
        </div>
        <div className="header-right">
          <Link to="/vehicles/new" className="btn btn-primary">Add Vehicle</Link>
        </div>
      </div>

      <div className="vehicles-table">
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>Vehicle</th>
              <th>License Plate</th>
              <th>Year</th>
              <th>Fuel Type</th>
              <th>Daily Rate</th>
              <th>Mileage</th>
              <th>Status</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {vehicles.map((vehicle) => (
              <tr key={vehicle.vehicle_id}>
                <td>{vehicle.vehicle_id}</td>
                <td>
                  <div>
                    <strong>{vehicle.make} {vehicle.model}</strong>
                    <div style={{ fontSize: '12px', color: '#6c757d' }}>
                      {vehicle.transmission} • {vehicle.seating_capacity} seats
                    </div>
                  </div>
                </td>
                <td>{vehicle.license_plate}</td>
                <td>{vehicle.year}</td>
                <td>{vehicle.fuel_type}</td>
                <td>{formatCurrency(vehicle.daily_rate)}</td>
                <td>{vehicle.mileage.toLocaleString()}</td>
                <td>
                  <span className={`status-badge ${vehicle.availability ? 'active' : 'cancelled'}`}>
                    {vehicle.availability ? 'Available' : 'Unavailable'}
                  </span>
                </td>
                <td>
                  <div className="actions">
                    <Link to={`/vehicles/${vehicle.vehicle_id}`} className="btn btn-sm btn-outline">View</Link>
                    <Link to={`/vehicles/${vehicle.vehicle_id}/edit`} className="btn btn-sm btn-secondary">Edit</Link>
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

export default Vehicles;