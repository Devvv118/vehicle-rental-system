import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { vehicleApi, rentalApi, customerApi } from '../services/api';
import type { Vehicle, Rental } from '../types';
import './Dashboard.css';

interface DashboardStats {
  totalCustomers: number;
  totalVehicles: number;
  activeRentals: number;
  availableVehicles: number;
  overdueRentals: number;
  revenue: number;
}

const Dashboard: React.FC = () => {
  const [stats, setStats] = useState<DashboardStats>({
    totalCustomers: 0,
    totalVehicles: 0,
    activeRentals: 0,
    availableVehicles: 0,
    overdueRentals: 0,
    revenue: 0,
  });
  const [recentRentals, setRecentRentals] = useState<Rental[]>([]);
  const [vehiclesNeedingMaintenance, setVehiclesNeedingMaintenance] = useState<Vehicle[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      setError(null);

      // Fetch all required data
      const [
        customers,
        vehicles,
        activeRentals,
        availableVehicles,
        overdueRentals,
        maintenanceVehicles,
        rentals,
      ] = await Promise.all([
        customerApi.getAll(0, 100),
        vehicleApi.getAll(0, 100),
        rentalApi.getActive(0, 100),
        vehicleApi.getAvailable(0, 100),
        rentalApi.getOverdue(),
        vehicleApi.getNeedingMaintenance(),
        rentalApi.getAll(0, 10),
      ]);

      // Calculate revenue from completed rentals
      const completedRentals = rentals.filter(r => r.status === 'Completed');
      const totalRevenue = completedRentals.reduce((sum, rental) => sum + rental.total_amount, 0);

      setStats({
        totalCustomers: customers.length,
        totalVehicles: vehicles.length,
        activeRentals: activeRentals.length,
        availableVehicles: availableVehicles.length,
        overdueRentals: overdueRentals.length,
        revenue: totalRevenue,
      });

      setRecentRentals(rentals.slice(0, 5));
      setVehiclesNeedingMaintenance(maintenanceVehicles.slice(0, 5));
    } catch (err) {
      setError('Failed to load dashboard data');
      console.error('Dashboard error:', err);
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

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString();
  };

  if (loading) {
    return (
      <div className="dashboard loading">
        <div className="loading-spinner">Loading dashboard...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="dashboard error">
        <div className="error-message">
          <p>{error}</p>
          <button onClick={fetchDashboardData} className="retry-button">
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <h1>Dashboard</h1>
        <p>Overview of your car rental business</p>
      </div>

      {/* Stats Cards */}
      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-icon">👥</div>
          <div className="stat-content">
            <h3>{stats.totalCustomers}</h3>
            <p>Total Customers</p>
          </div>
          <Link to="/customers" className="stat-link">View All</Link>
        </div>

        <div className="stat-card">
          <div className="stat-icon">🚗</div>
          <div className="stat-content">
            <h3>{stats.totalVehicles}</h3>
            <p>Total Vehicles</p>
          </div>
          <Link to="/vehicles" className="stat-link">View All</Link>
        </div>

        <div className="stat-card">
          <div className="stat-icon">📋</div>
          <div className="stat-content">
            <h3>{stats.activeRentals}</h3>
            <p>Active Rentals</p>
          </div>
          <Link to="/rentals?status=Active" className="stat-link">View All</Link>
        </div>

        <div className="stat-card">
          <div className="stat-icon">✅</div>
          <div className="stat-content">
            <h3>{stats.availableVehicles}</h3>
            <p>Available Vehicles</p>
          </div>
          <Link to="/vehicles?availability=true" className="stat-link">View All</Link>
        </div>

        <div className={`stat-card ${stats.overdueRentals > 0 ? 'warning' : ''}`}>
          <div className="stat-icon">⚠️</div>
          <div className="stat-content">
            <h3>{stats.overdueRentals}</h3>
            <p>Overdue Rentals</p>
          </div>
          <Link to="/rentals/overdue" className="stat-link">View All</Link>
        </div>

        <div className="stat-card revenue">
          <div className="stat-icon">💰</div>
          <div className="stat-content">
            <h3>{formatCurrency(stats.revenue)}</h3>
            <p>Total Revenue</p>
          </div>
          <Link to="/reports" className="stat-link">View Reports</Link>
        </div>
      </div>

      {/* Recent Activity */}
      <div className="dashboard-sections">
        <div className="dashboard-section">
          <div className="section-header">
            <h2>Recent Rentals</h2>
            <Link to="/rentals" className="view-all-link">View All</Link>
          </div>
          <div className="recent-rentals">
            {recentRentals.length === 0 ? (
              <p className="no-data">No recent rentals</p>
            ) : (
              <div className="rental-list">
                {recentRentals.map((rental) => (
                  <div key={rental.rental_id} className="rental-item">
                    <div className="rental-info">
                      <h4>Rental #{rental.rental_id}</h4>
                      <p>Customer ID: {rental.customer_id}</p>
                      <p>Vehicle ID: {rental.vehicle_id}</p>
                      <p>Start: {formatDate(rental.start_date)}</p>
                    </div>
                    <div className="rental-status">
                      <span className={`status-badge ${rental.status.toLowerCase()}`}>
                        {rental.status}
                      </span>
                      <span className="rental-amount">
                        {formatCurrency(rental.total_amount)}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        <div className="dashboard-section">
          <div className="section-header">
            <h2>Vehicles Needing Maintenance</h2>
            <Link to="/maintenance" className="view-all-link">View All</Link>
          </div>
          <div className="maintenance-vehicles">
            {vehiclesNeedingMaintenance.length === 0 ? (
              <p className="no-data">No vehicles need maintenance</p>
            ) : (
              <div className="vehicle-list">
                {vehiclesNeedingMaintenance.map((vehicle) => (
                  <div key={vehicle.vehicle_id} className="vehicle-item">
                    <div className="vehicle-info">
                      <h4>{vehicle.year} {vehicle.make} {vehicle.model}</h4>
                      <p>License: {vehicle.license_plate}</p>
                      <p>Mileage: {vehicle.mileage.toLocaleString()}</p>
                    </div>
                    <div className="vehicle-actions">
                      <Link
                        to={`/vehicles/${vehicle.vehicle_id}`}
                        className="btn btn-sm btn-outline"
                      >
                        View Details
                      </Link>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="quick-actions">
        <h2>Quick Actions</h2>
        <div className="action-buttons">
          <Link to="/customers/new" className="action-btn">
            <span className="btn-icon">👥</span>
            Add Customer
          </Link>
          <Link to="/vehicles/new" className="action-btn">
            <span className="btn-icon">🚗</span>
            Add Vehicle
          </Link>
          <Link to="/rentals/new" className="action-btn">
            <span className="btn-icon">📋</span>
            New Rental
          </Link>
          <Link to="/reservations/new" className="action-btn">
            <span className="btn-icon">📅</span>
            New Reservation
          </Link>
          <Link to="/maintenance/new" className="action-btn">
            <span className="btn-icon">🔧</span>
            Schedule Maintenance
          </Link>
          <Link to="/reports" className="action-btn">
            <span className="btn-icon">📈</span>
            View Reports
          </Link>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;