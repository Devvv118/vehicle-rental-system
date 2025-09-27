import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import Customers from './pages/Customers';
import CustomerDetail from './pages/CustomerDetail';
import CustomerForm from './pages/CustomerForm';
import Vehicles from './pages/Vehicles';
import VehicleDetail from './pages/VehicleDetail';
import VehicleForm from './pages/VehicleForm';
import Rentals from './pages/Rentals';
import RentalDetail from './pages/RentalDetail';
import RentalForm from './pages/RentalForm';
import Reservations from './pages/Reservations';
import ReservationForm from './pages/ReservationForm';
import Employees from './pages/Employees';
import EmployeeForm from './pages/EmployeeForm';
import Locations from './pages/Locations';
import LocationForm from './pages/LocationForm';
import Maintenance from './pages/Maintenance';
import MaintenanceForm from './pages/MaintenanceForm';
import Incidents from './pages/Incidents';
import IncidentForm from './pages/IncidentForm';
import Reports from './pages/Reports';
import './App.css';

function App() {
  return (
    <Router>
      <Layout>
        <Routes>
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="/dashboard" element={<Dashboard />} />
          
          {/* Customer Routes */}
          <Route path="/customers" element={<Customers />} />
          <Route path="/customers/new" element={<CustomerForm />} />
          <Route path="/customers/:id" element={<CustomerDetail />} />
          <Route path="/customers/:id/edit" element={<CustomerForm />} />
          
          {/* Vehicle Routes */}
          <Route path="/vehicles" element={<Vehicles />} />
          <Route path="/vehicles/new" element={<VehicleForm />} />
          <Route path="/vehicles/:id" element={<VehicleDetail />} />
          <Route path="/vehicles/:id/edit" element={<VehicleForm />} />
          
          {/* Rental Routes */}
          <Route path="/rentals" element={<Rentals />} />
          <Route path="/rentals/new" element={<RentalForm />} />
          <Route path="/rentals/:id" element={<RentalDetail />} />
          
          {/* Reservation Routes */}
          <Route path="/reservations" element={<Reservations />} />
          <Route path="/reservations/new" element={<ReservationForm />} />
          
          {/* Employee Routes */}
          <Route path="/employees" element={<Employees />} />
          <Route path="/employees/new" element={<EmployeeForm />} />
          
          {/* Location Routes */}
          <Route path="/locations" element={<Locations />} />
          <Route path="/locations/new" element={<LocationForm />} />
          
          {/* Maintenance Routes */}
          <Route path="/maintenance" element={<Maintenance />} />
          <Route path="/maintenance/new" element={<MaintenanceForm />} />
          
          {/* Incident Routes */}
          <Route path="/incidents" element={<Incidents />} />
          <Route path="/incidents/new" element={<IncidentForm />} />
          
          {/* Reports */}
          <Route path="/reports" element={<Reports />} />
          
          {/* Catch all route */}
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </Layout>
    </Router>
  );
}

export default App;