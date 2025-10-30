// import React from 'react';

// const Maintenance: React.FC = () => {
//   return <div><h1>Maintenance</h1><p>Under construction</p></div>;
// };

// export default Maintenance;

// pages/Maintenance.tsx
import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { maintenanceApi } from '../services/api';
import type { MaintenanceSchedule } from '../types';

const Maintenance: React.FC = () => {
  const [schedules, setSchedules] = useState<MaintenanceSchedule[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<'all' | 'scheduled'>('scheduled');

  useEffect(() => {
    fetchMaintenanceSchedules();
  }, [filter]);

  const fetchMaintenanceSchedules = async () => {
    try {
      setLoading(true);
      const data = filter === 'scheduled'
        ? await maintenanceApi.getScheduled()
        : await maintenanceApi.getScheduled(); // You can modify to fetch all
      setSchedules(data);
    } catch (err) {
      setError('Failed to load maintenance schedules');
      console.error('Error fetching maintenance:', err);
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
    return <div className="loading"><div className="loading-spinner">Loading maintenance schedules...</div></div>;
  }

  if (error) {
    return (
      <div className="error">
        <div className="error-message">
          <p>{error}</p>
          <button onClick={fetchMaintenanceSchedules} className="retry-button">Retry</button>
        </div>
      </div>
    );
  }

  return (
    <div className="maintenance">
      <div className="page-header">
        <div className="header-left">
          <h1>Maintenance Schedule</h1>
          <p>Manage vehicle maintenance and service</p>
        </div>
        <div className="header-right">
          <Link to="/maintenance/new" className="btn btn-primary">Schedule Maintenance</Link>
        </div>
      </div>

      <div style={{ marginBottom: '24px', display: 'flex', gap: '12px' }}>
        <button
          className={`btn ${filter === 'scheduled' ? 'btn-primary' : 'btn-outline'}`}
          onClick={() => setFilter('scheduled')}
        >
          Scheduled
        </button>
        <button
          className={`btn ${filter === 'all' ? 'btn-primary' : 'btn-outline'}`}
          onClick={() => setFilter('all')}
        >
          All Maintenance
        </button>
      </div>

      <div className="maintenance-table">
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>Vehicle ID</th>
              <th>Type</th>
              <th>Scheduled Date</th>
              <th>Completed Date</th>
              <th>Mechanic ID</th>
              <th>Cost</th>
              <th>Status</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {schedules.map((schedule) => (
              <tr key={schedule.schedule_id}>
                <td>{schedule.schedule_id}</td>
                <td>
                  <Link to={`/vehicles/${schedule.vehicle_id}`} style={{ color: '#007bff', textDecoration: 'none' }}>
                    #{schedule.vehicle_id}
                  </Link>
                </td>
                <td>{schedule.maintenance_type}</td>
                <td>{formatDate(schedule.scheduled_date)}</td>
                <td>{schedule.completed_date ? formatDate(schedule.completed_date) : 'N/A'}</td>
                <td>{schedule.assigned_mechanic ? `#${schedule.assigned_mechanic}` : 'Unassigned'}</td>
                <td>{schedule.cost ? formatCurrency(schedule.cost) : 'TBD'}</td>
                <td>
                  <span className={`status-badge ${schedule.status.toLowerCase().replace(' ', '-')}`}>
                    {schedule.status}
                  </span>
                </td>
                <td>
                  <button className="btn btn-sm btn-outline">View</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        {schedules.length === 0 && (
          <div className="no-data">
            <p>No maintenance scheduled.</p>
            <Link to="/maintenance/new" className="btn btn-primary">
              Schedule First Maintenance
            </Link>
          </div>
        )}
      </div>
    </div>
  );
};

export default Maintenance;