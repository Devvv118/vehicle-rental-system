// import React from 'react';

// const Incidents: React.FC = () => {
//   return <div><h1>Incidents</h1><p>Under construction</p></div>;
// };

// export default Incidents;

// pages/Incidents.tsx
import { useEffect, useState } from 'react';
import { incidentApi } from '../services/api';
import type { IncidentReport } from '../types';
import { Link } from 'react-router-dom';

const Incidents: React.FC = () => {
  const [incidents, setIncidents] = useState<IncidentReport[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<'all' | 'open'>('open');

  useEffect(() => {
    fetchIncidents();
  }, [filter]);

  const fetchIncidents = async () => {
    try {
      setLoading(true);
      const data = filter === 'open'
        ? await incidentApi.getOpen()
        : await incidentApi.getAll();
      setIncidents(data);
    } catch (err) {
      setError('Failed to load incidents');
      console.error('Error fetching incidents:', err);
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

  if (loading) {
    return <div className="loading"><div className="loading-spinner">Loading incidents...</div></div>;
  }

  if (error) {
    return (
      <div className="error">
        <div className="error-message">
          <p>{error}</p>
          <button onClick={fetchIncidents} className="retry-button">Retry</button>
        </div>
      </div>
    );
  }

  return (
    <div className="incidents">
      <div className="page-header">
        <div className="header-left">
          <h1>Incident Reports</h1>
          <p>Track and manage rental incidents</p>
        </div>
        <div className="header-right">
          <Link to="/incidents/new" className="btn btn-primary">Report Incident</Link>
        </div>
      </div>

      <div style={{ marginBottom: '24px', display: 'flex', gap: '12px' }}>
        <button
          className={`btn ${filter === 'open' ? 'btn-primary' : 'btn-outline'}`}
          onClick={() => setFilter('open')}
        >
          Open Incidents
        </button>
        <button
          className={`btn ${filter === 'all' ? 'btn-primary' : 'btn-outline'}`}
          onClick={() => setFilter('all')}
        >
          All Incidents
        </button>
      </div>

      <div style={{ display: 'grid', gap: '24px' }}>
        {incidents.map((incident) => (
          <div
            key={incident.incident_id}
            style={{
              background: 'white',
              padding: '24px',
              borderRadius: '8px',
              boxShadow: '0 2px 10px rgba(0, 0, 0, 0.1)',
              border: '1px solid #dee2e6',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '16px' }}>
              <div>
                <h3 style={{ marginBottom: '8px', fontSize: '18px', fontWeight: '600' }}>
                  {incident.incident_type} - Rental #{incident.rental_id}
                </h3>
                <div style={{ fontSize: '14px', color: '#6c757d' }}>
                  {formatDate(incident.incident_date)}
                </div>
              </div>
              <span className={`status-badge ${incident.status.toLowerCase().replace(' ', '-')}`}>
                {incident.status}
              </span>
            </div>

            <div style={{ marginBottom: '16px', fontSize: '15px', lineHeight: '1.6' }}>
              {incident.description}
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '12px', marginBottom: '16px' }}>
              {incident.estimated_cost && (
                <div>
                  <strong>Estimated Cost:</strong>{' '}
                  <span style={{ color: '#dc3545', fontWeight: '600' }}>
                    {formatCurrency(incident.estimated_cost)}
                  </span>
                </div>
              )}
              {incident.reported_by && (
                <div>
                  <strong>Reported By:</strong> Employee #{incident.reported_by}
                </div>
              )}
              {incident.police_report_number && (
                <div>
                  <strong>Police Report:</strong> {incident.police_report_number}
                </div>
              )}
            </div>

            <div style={{ display: 'flex', gap: '12px' }}>
              <Link
                to={`/rentals/${incident.rental_id}`}
                className="btn btn-sm btn-outline"
              >
                View Rental
              </Link>
            </div>
          </div>
        ))}
      </div>

      {incidents.length === 0 && (
        <div className="no-data">
          <p>No incidents reported.</p>
        </div>
      )}
    </div>
  );
};

export default Incidents;