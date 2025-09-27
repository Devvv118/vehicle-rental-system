import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { customerApi } from '../services/api';
import type { Customer } from '../types';
import './Customers.css';

const Customers: React.FC = () => {
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [filteredCustomers, setFilteredCustomers] = useState<Customer[]>([]);
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage] = useState(10);

  useEffect(() => {
    fetchCustomers();
  }, []);

  useEffect(() => {
    if (searchTerm.trim() === '') {
      setFilteredCustomers(customers);
    } else {
      const filtered = customers.filter(
        (customer) =>
          customer.first_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
          customer.last_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
          customer.email.toLowerCase().includes(searchTerm.toLowerCase()) ||
          customer.phone.includes(searchTerm) ||
          customer.driver_license.toLowerCase().includes(searchTerm.toLowerCase())
      );
      setFilteredCustomers(filtered);
    }
    setCurrentPage(1);
  }, [searchTerm, customers]);

  const fetchCustomers = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await customerApi.getAll(0, 100);
      setCustomers(data);
      setFilteredCustomers(data);
    } catch (err) {
      setError('Failed to load customers');
      console.error('Error fetching customers:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (customerId: number) => {
    if (window.confirm('Are you sure you want to delete this customer?')) {
      try {
        await customerApi.delete(customerId);
        setCustomers(customers.filter(c => c.customer_id !== customerId));
      } catch (err) {
        alert('Failed to delete customer');
        console.error('Error deleting customer:', err);
      }
    }
  };

  const handleSearch = async () => {
    if (searchTerm.trim() === '') {
      fetchCustomers();
      return;
    }

    try {
      setLoading(true);
      const searchResults = await customerApi.search(searchTerm);
      setCustomers(searchResults);
      setFilteredCustomers(searchResults);
    } catch (err) {
      setError('Failed to search customers');
      console.error('Error searching customers:', err);
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString();
  };

  // Pagination
  const indexOfLastItem = currentPage * itemsPerPage;
  const indexOfFirstItem = indexOfLastItem - itemsPerPage;
  const currentCustomers = filteredCustomers.slice(indexOfFirstItem, indexOfLastItem);
  const totalPages = Math.ceil(filteredCustomers.length / itemsPerPage);

  const paginate = (pageNumber: number) => setCurrentPage(pageNumber);

  if (loading) {
    return (
      <div className="customers loading">
        <div className="loading-spinner">Loading customers...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="customers error">
        <div className="error-message">
          <p>{error}</p>
          <button onClick={fetchCustomers} className="retry-button">
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="customers">
      <div className="page-header">
        <div className="header-left">
          <h1>Customers</h1>
          <p>Manage your customer database</p>
        </div>
        <div className="header-right">
          <Link to="/customers/new" className="btn btn-primary">
            Add Customer
          </Link>
        </div>
      </div>

      <div className="search-section">
        <div className="search-bar">
          <input
            type="text"
            placeholder="Search customers by name, email, phone, or license..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
          />
          <button onClick={handleSearch} className="search-button">
            Search
          </button>
          {searchTerm && (
            <button
              onClick={() => {
                setSearchTerm('');
                fetchCustomers();
              }}
              className="clear-search"
            >
              Clear
            </button>
          )}
        </div>
        <div className="results-info">
          {filteredCustomers.length} customer{filteredCustomers.length !== 1 ? 's' : ''} found
        </div>
      </div>

      <div className="customers-table">
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>Name</th>
              <th>Email</th>
              <th>Phone</th>
              <th>Driver License</th>
              <th>Date of Birth</th>
              <th>Created</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {currentCustomers.map((customer) => (
              <tr key={customer.customer_id}>
                <td>{customer.customer_id}</td>
                <td>
                  <div className="customer-name">
                    <strong>{customer.first_name} {customer.last_name}</strong>
                  </div>
                </td>
                <td>{customer.email}</td>
                <td>{customer.phone}</td>
                <td>{customer.driver_license}</td>
                <td>
                  {customer.date_of_birth ? formatDate(customer.date_of_birth) : 'N/A'}
                </td>
                <td>{formatDate(customer.created_at)}</td>
                <td>
                  <div className="actions">
                    <Link
                      to={`/customers/${customer.customer_id}`}
                      className="btn btn-sm btn-outline"
                    >
                      View
                    </Link>
                    <Link
                      to={`/customers/${customer.customer_id}/edit`}
                      className="btn btn-sm btn-secondary"
                    >
                      Edit
                    </Link>
                    <button
                      onClick={() => handleDelete(customer.customer_id)}
                      className="btn btn-sm btn-danger"
                    >
                      Delete
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        {currentCustomers.length === 0 && (
          <div className="no-data">
            <p>No customers found.</p>
            <Link to="/customers/new" className="btn btn-primary">
              Add First Customer
            </Link>
          </div>
        )}
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="pagination">
          <button
            onClick={() => paginate(currentPage - 1)}
            disabled={currentPage === 1}
            className="pagination-btn"
          >
            Previous
          </button>

          {Array.from({ length: totalPages }, (_, i) => i + 1).map((number) => (
            <button
              key={number}
              onClick={() => paginate(number)}
              className={`pagination-btn ${currentPage === number ? 'active' : ''}`}
            >
              {number}
            </button>
          ))}

          <button
            onClick={() => paginate(currentPage + 1)}
            disabled={currentPage === totalPages}
            className="pagination-btn"
          >
            Next
          </button>
        </div>
      )}
    </div>
  );
};

export default Customers;