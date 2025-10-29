// import React from 'react';

// const Locations: React.FC = () => {
//   return <div><h1>Locations</h1><p>Under construction</p></div>;
// };

// export default Locations;

// pages/Locations.tsx
import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { locationApi } from '../services/api';
import type { Location } from '../types';

const Locations: React.FC = () => {
  const [locations, setLocations] = useState<Location[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchLocations();
  }, []);

  const fetchLocations = async () => {
    try {
      setLoading(true);
      const data = await locationApi.getAll();
      setLocations(data);
    } catch (err) {
      setError('Failed to load locations');
      console.error('Error fetching locations:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="loading"><div className="loading-spinner">Loading locations...</div></div>;
  }

  if (error) {
    return (
      <div className="error">
        <div className="error-message">
          <p>{error}</p>
          <button onClick={fetchLocations} className="retry-button">Retry</button>
        </div>
      </div>
    );
  }

  return (
    <div className="locations">
      <div className="page-header">
        <div className="header-left">
          <h1>Locations</h1>
          <p>Manage rental locations</p>
        </div>
        <div className="header-right">
          <Link to="/locations/new" className="btn btn-primary">Add Location</Link>
        </div>
      </div>

      <div className="locations-grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '24px' }}>
        {locations.map((location) => (
          <div
            key={location.location_id}
            style={{
              background: 'white',
              padding: '24px',
              borderRadius: '8px',
              boxShadow: '0 2px 10px rgba(0, 0, 0, 0.1)',
              border: '1px solid #dee2e6',
            }}
          >
            <h3 style={{ marginBottom: '16px', fontSize: '18px', fontWeight: '600' }}>
              {location.name}
            </h3>
            <div style={{ display: 'grid', gap: '8px', fontSize: '14px', color: '#6c757d' }}>
              <div>📍 {location.address}</div>
              <div>{location.city}, {location.state} {location.zip_code}</div>
              {location.phone && <div>📞 {location.phone}</div>}
              {location.operating_hours && (
                <div>🕒 {location.operating_hours}</div>
              )}
            </div>
            <div style={{ marginTop: '16px', paddingTop: '16px', borderTop: '1px solid #dee2e6' }}>
              <Link
                to={`/locations/${location.location_id}`}
                className="btn btn-sm btn-outline"
                style={{ width: '100%' }}
              >
                View Details
              </Link>
            </div>
          </div>
        ))}
      </div>

      {locations.length === 0 && (
        <div className="no-data">
          <p>No locations found.</p>
          <Link to="/locations/new" className="btn btn-primary">
            Add First Location
          </Link>
        </div>
      )}
    </div>
  );
};

export default Locations;
