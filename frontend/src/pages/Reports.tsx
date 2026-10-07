// import React from 'react';

// const Reports: React.FC = () => {
//   return <div><h1>Reports</h1><p>Under construction</p></div>;
// };

// export default Reports;

import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { rentalApi } from '../services/api';

const Reports: React.FC = () => {
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [revenue, setRevenue] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);

  const fetchRevenue = async () => {
    if (!startDate || !endDate) {
      alert('Please select both start and end dates');
      return;
    }

    try {
      setLoading(true);
      const report = await rentalApi.getRevenue(startDate, endDate);
      setRevenue(report.total_revenue);
    } catch (err) {
      console.error('Error fetching revenue:', err);
      alert('Failed to fetch revenue report');
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

  return (
    <div className="reports">
      <div className="page-header">
        <div className="header-left">
          <h1>Reports</h1>
          <p>Business analytics and reporting</p>
        </div>
      </div>

      <div style={{ background: 'white', padding: '24px', borderRadius: '8px', boxShadow: '0 2px 10px rgba(0, 0, 0, 0.1)', marginBottom: '24px' }}>
        <h2 style={{ marginBottom: '20px', fontSize: '18px', fontWeight: '600' }}>Revenue Report</h2>
        
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr auto', gap: '12px', marginBottom: '20px' }}>
          <div className="form-group">
            <label className="form-label">Start Date</label>
            <input
              type="date"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              className="form-input"
            />
          </div>

          <div className="form-group">
            <label className="form-label">End Date</label>
            <input
              type="date"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
              className="form-input"
            />
          </div>

          <button
            onClick={fetchRevenue}
            className="btn btn-primary"
            disabled={loading}
            style={{ alignSelf: 'end' }}
          >
            {loading ? 'Loading...' : 'Generate Report'}
          </button>
        </div>

        {revenue !== null && (
          <div style={{ padding: '24px', backgroundColor: '#e3f2fd', borderRadius: '8px', textAlign: 'center' }}>
            <div style={{ fontSize: '14px', color: '#6c757d', marginBottom: '8px' }}>
              Total Revenue ({startDate} to {endDate})
            </div>
            <div style={{ fontSize: '32px', fontWeight: '600', color: '#007bff' }}>
              {formatCurrency(revenue)}
            </div>
          </div>
        )}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '24px' }}>
        <div style={{ background: 'white', padding: '24px', borderRadius: '8px', boxShadow: '0 2px 10px rgba(0, 0, 0, 0.1)' }}>
          <h3 style={{ marginBottom: '16px', fontSize: '16px', fontWeight: '600' }}>Quick Links</h3>
          <div style={{ display: 'grid', gap: '12px' }}>
            <Link to="/customers" className="btn btn-outline" style={{ justifyContent: 'flex-start' }}>
              📊 Customer Analytics
            </Link>
            <Link to="/vehicles" className="btn btn-outline" style={{ justifyContent: 'flex-start' }}>
              🚗 Vehicle Utilization
            </Link>
            <Link to="/rentals" className="btn btn-outline" style={{ justifyContent: 'flex-start' }}>
              📋 Rental History
            </Link>
            <Link to="/maintenance" className="btn btn-outline" style={{ justifyContent: 'flex-start' }}>
              🔧 Maintenance Costs
            </Link>
          </div>
        </div>

        <div style={{ background: 'white', padding: '24px', borderRadius: '8px', boxShadow: '0 2px 10px rgba(0, 0, 0, 0.1)' }}>
          <h3 style={{ marginBottom: '16px', fontSize: '16px', fontWeight: '600' }}>Export Options</h3>
          <div style={{ display: 'grid', gap: '12px' }}>
            <button className="btn btn-outline" style={{ justifyContent: 'flex-start' }}>
              📄 Export to PDF
            </button>
            <button className="btn btn-outline" style={{ justifyContent: 'flex-start' }}>
              📊 Export to Excel
            </button>
            <button className="btn btn-outline" style={{ justifyContent: 'flex-start' }}>
              📧 Email Report
            </button>
          </div>
        </div>

        <div style={{ background: 'white', padding: '24px', borderRadius: '8px', boxShadow: '0 2px 10px rgba(0, 0, 0, 0.1)' }}>
          <h3 style={{ marginBottom: '16px', fontSize: '16px', fontWeight: '600' }}>Report Types</h3>
          <div style={{ display: 'grid', gap: '8px', fontSize: '14px', color: '#6c757d' }}>
            <div>• Revenue & Financial Reports</div>
            <div>• Customer Analytics</div>
            <div>• Vehicle Performance</div>
            <div>• Maintenance Tracking</div>
            <div>• Incident Statistics</div>
            <div>• Employee Performance</div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Reports;