-- =====================================================================================================
-- OPTIONAL demo data so a fresh install is not empty:  python database/init_db.py --sample-data
-- Only inserts when the database has no customers/vehicles/locations yet (so it never duplicates).
-- Requires seed.sql to have been applied first (init_db.py does that).
-- =====================================================================================================
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM customer) OR EXISTS (SELECT 1 FROM vehicle) OR EXISTS (SELECT 1 FROM location) THEN
        RAISE NOTICE 'Database already contains data - sample data skipped';
        RETURN;
    END IF;

    INSERT INTO location (name, address, city, state, zip_code, phone, operating_hours) VALUES
        ('Downtown Branch', '100 Main Street',      'Springfield', 'IL', '62701', '217-555-0100', 'Mon-Sat 8:00-18:00'),
        ('Airport Branch',  '1 Airport Road',       'Chicago',     'IL', '60666', '312-555-0199', 'Daily 5:00-23:00');

    INSERT INTO employee (first_name, last_name, email, phone, role, hire_date, salary, location_id) VALUES
        ('Maya',  'Robinson', 'maya.robinson@example.com', '217-555-0111', 'Manager',  '2022-03-01', 72000.00,
            (SELECT location_id FROM location WHERE name = 'Downtown Branch')),
        ('Andy',  'Cole',     'andy.cole@example.com',     '217-555-0112', 'Agent',    '2023-06-15', 41000.00,
            (SELECT location_id FROM location WHERE name = 'Downtown Branch')),
        ('Moe',   'Hamilton', 'moe.hamilton@example.com',  '312-555-0113', 'Mechanic', '2021-09-10', 52000.00,
            (SELECT location_id FROM location WHERE name = 'Airport Branch'));

    UPDATE employee SET manager_id = (SELECT employee_id FROM employee WHERE email = 'maya.robinson@example.com')
        WHERE email IN ('andy.cole@example.com');
    UPDATE location SET manager_id = (SELECT employee_id FROM employee WHERE email = 'maya.robinson@example.com')
        WHERE name = 'Downtown Branch';

    INSERT INTO vehicle (model, make, license_plate, year, daily_rate, mileage, fuel_type, transmission, seating_capacity, location_id) VALUES
        ('Corolla', 'Toyota', 'DEMO-001', 2022, 45.00, 12000, 'Gasoline', 'Automatic', 5, (SELECT location_id FROM location WHERE name = 'Downtown Branch')),
        ('Civic',   'Honda',  'DEMO-002', 2023, 50.00,  8000, 'Gasoline', 'Automatic', 5, (SELECT location_id FROM location WHERE name = 'Downtown Branch')),
        ('Model 3', 'Tesla',  'DEMO-003', 2023, 95.00,  4000, 'Electric', 'Automatic', 5, (SELECT location_id FROM location WHERE name = 'Airport Branch')),
        ('Sienna',  'Toyota', 'DEMO-004', 2021, 80.00, 30000, 'Hybrid',   'Automatic', 7, (SELECT location_id FROM location WHERE name = 'Airport Branch'));

    INSERT INTO vehicle_feature_mapping (vehicle_id, feature_id)
        SELECT v.vehicle_id, f.feature_id FROM vehicle v CROSS JOIN vehicle_feature f
        WHERE f.name IN ('Bluetooth', 'Backup Camera');

    INSERT INTO customer (first_name, last_name, email, phone, address, driver_license, date_of_birth) VALUES
        ('Alice', 'Anderson', 'alice.anderson@example.com', '555-0301', '12 Oak Avenue',   'DL-ALICE-01', '1990-04-12'),
        ('Bob',   'Brown',    'bob.brown@example.com',      '555-0302', '34 Pine Street',  'DL-BOB-02',   '1985-11-30'),
        ('Carol', 'Chen',     'carol.chen@example.com',     '555-0303', '56 Maple Drive',  'DL-CAROL-03', '1993-07-08');

    -- every customer has a membership profile (the API creates one automatically for new customers)
    INSERT INTO customer_membership_profile (customer_id) SELECT customer_id FROM customer;
END $$;
