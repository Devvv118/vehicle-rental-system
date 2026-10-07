-- =====================================================================================================
-- Car Rental Management System - PostgreSQL schema
-- GENERATED FILE - do not edit by hand. Edit backend/models.py and run:  python db/generate_schema.py
-- Safe to run repeatedly (everything is IF NOT EXISTS / guarded).
-- =====================================================================================================


-- ----- tables --------------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS customer (
	customer_id SERIAL NOT NULL, 
	first_name VARCHAR(50) NOT NULL, 
	last_name VARCHAR(50) NOT NULL, 
	email VARCHAR(255) NOT NULL, 
	phone VARCHAR(20) NOT NULL, 
	address TEXT, 
	driver_license VARCHAR(20) NOT NULL, 
	date_of_birth DATE, 
	created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP, 
	updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP, 
	PRIMARY KEY (customer_id), 
	UNIQUE (email), 
	UNIQUE (driver_license)
);

CREATE TABLE IF NOT EXISTS employee (
	employee_id SERIAL NOT NULL, 
	first_name VARCHAR(50) NOT NULL, 
	last_name VARCHAR(50) NOT NULL, 
	email VARCHAR(255) NOT NULL, 
	phone VARCHAR(20) NOT NULL, 
	role VARCHAR(30) NOT NULL, 
	hire_date DATE NOT NULL, 
	salary DECIMAL(10, 2), 
	location_id INTEGER, 
	manager_id INTEGER, 
	is_active BOOLEAN DEFAULT true, 
	PRIMARY KEY (employee_id), 
	UNIQUE (email)
);

CREATE TABLE IF NOT EXISTS insurance_plan (
	plan_id SERIAL NOT NULL, 
	name VARCHAR(100) NOT NULL, 
	description TEXT, 
	daily_cost DECIMAL(6, 2) NOT NULL, 
	coverage_amount DECIMAL(12, 2) NOT NULL, 
	deductible DECIMAL(8, 2) NOT NULL, 
	is_active BOOLEAN DEFAULT true, 
	PRIMARY KEY (plan_id)
);

CREATE TABLE IF NOT EXISTS location (
	location_id SERIAL NOT NULL, 
	name VARCHAR(100) NOT NULL, 
	address TEXT NOT NULL, 
	city VARCHAR(50) NOT NULL, 
	state VARCHAR(50) NOT NULL, 
	zip_code VARCHAR(10) NOT NULL, 
	phone VARCHAR(20), 
	operating_hours VARCHAR(100), 
	manager_id INTEGER, 
	PRIMARY KEY (location_id)
);

CREATE TABLE IF NOT EXISTS membership_tier (
	tier_name VARCHAR(20) NOT NULL, 
	description TEXT, 
	monthly_fee DECIMAL(8, 2), 
	free_upgrades INTEGER, 
	bonus_point_rate DECIMAL(4, 2), 
	PRIMARY KEY (tier_name)
);

CREATE TABLE IF NOT EXISTS vehicle_feature (
	feature_id SERIAL NOT NULL, 
	name VARCHAR(50) NOT NULL, 
	description TEXT, 
	category VARCHAR(30), 
	PRIMARY KEY (feature_id)
);

CREATE TABLE IF NOT EXISTS customer_membership_profile (
	profile_id SERIAL NOT NULL, 
	customer_id INTEGER NOT NULL, 
	membership_tier VARCHAR(20) DEFAULT 'Standard', 
	points_balance INTEGER DEFAULT 0, 
	tier_level VARCHAR(20) DEFAULT 'Bronze', 
	join_date DATE DEFAULT CURRENT_DATE, 
	last_activity_date DATE, 
	lifetime_rentals INTEGER DEFAULT 0, 
	lifetime_spending DECIMAL(10, 2) DEFAULT 0.0, 
	PRIMARY KEY (profile_id), 
	UNIQUE (customer_id), 
	FOREIGN KEY(customer_id) REFERENCES customer (customer_id) ON DELETE CASCADE, 
	FOREIGN KEY(membership_tier) REFERENCES membership_tier (tier_name) ON UPDATE CASCADE
);

CREATE TABLE IF NOT EXISTS customer_vehicle_preference (
	customer_id INTEGER NOT NULL, 
	vehicle_type VARCHAR(30) NOT NULL, 
	preference_score INTEGER, 
	created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP, 
	PRIMARY KEY (customer_id, vehicle_type), 
	FOREIGN KEY(customer_id) REFERENCES customer (customer_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS vehicle (
	vehicle_id SERIAL NOT NULL, 
	model VARCHAR(50) NOT NULL, 
	make VARCHAR(50) NOT NULL, 
	license_plate VARCHAR(10) NOT NULL, 
	year INTEGER NOT NULL, 
	availability BOOLEAN DEFAULT true, 
	daily_rate DECIMAL(8, 2) NOT NULL, 
	mileage INTEGER DEFAULT 0, 
	fuel_type VARCHAR(20) DEFAULT 'Gasoline', 
	transmission VARCHAR(20) DEFAULT 'Automatic', 
	seating_capacity INTEGER DEFAULT 5, 
	location_id INTEGER, 
	created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP, 
	PRIMARY KEY (vehicle_id), 
	UNIQUE (license_plate), 
	FOREIGN KEY(location_id) REFERENCES location (location_id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS maintenance_schedule (
	schedule_id SERIAL NOT NULL, 
	vehicle_id INTEGER NOT NULL, 
	maintenance_type VARCHAR(50) NOT NULL, 
	scheduled_date DATE NOT NULL, 
	completed_date DATE, 
	assigned_mechanic INTEGER, 
	cost DECIMAL(8, 2), 
	notes TEXT, 
	status VARCHAR(20) DEFAULT 'Scheduled', 
	PRIMARY KEY (schedule_id), 
	FOREIGN KEY(vehicle_id) REFERENCES vehicle (vehicle_id) ON DELETE CASCADE, 
	FOREIGN KEY(assigned_mechanic) REFERENCES employee (employee_id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS rental (
	rental_id SERIAL NOT NULL, 
	customer_id INTEGER NOT NULL, 
	vehicle_id INTEGER NOT NULL, 
	employee_id INTEGER, 
	pickup_location_id INTEGER NOT NULL, 
	return_location_id INTEGER NOT NULL, 
	start_date TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	end_date TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	actual_return_date TIMESTAMP WITHOUT TIME ZONE, 
	daily_rate DECIMAL(8, 2) NOT NULL, 
	total_amount DECIMAL(10, 2) NOT NULL, 
	security_deposit DECIMAL(8, 2) DEFAULT 200.0, 
	mileage_start INTEGER, 
	mileage_end INTEGER, 
	fuel_level_start DECIMAL(3, 2), 
	fuel_level_end DECIMAL(3, 2), 
	status VARCHAR(20) DEFAULT 'Active', 
	discount_applied DECIMAL(8, 2) DEFAULT 0.0, 
	late_fees DECIMAL(8, 2) DEFAULT 0.0, 
	damage_fees DECIMAL(8, 2) DEFAULT 0.0, 
	created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP, 
	PRIMARY KEY (rental_id), 
	FOREIGN KEY(customer_id) REFERENCES customer (customer_id) ON DELETE CASCADE, 
	FOREIGN KEY(vehicle_id) REFERENCES vehicle (vehicle_id) ON DELETE CASCADE, 
	FOREIGN KEY(employee_id) REFERENCES employee (employee_id) ON DELETE SET NULL, 
	FOREIGN KEY(pickup_location_id) REFERENCES location (location_id), 
	FOREIGN KEY(return_location_id) REFERENCES location (location_id)
);

CREATE TABLE IF NOT EXISTS reservation (
	reservation_id SERIAL NOT NULL, 
	customer_id INTEGER NOT NULL, 
	vehicle_id INTEGER NOT NULL, 
	pickup_location_id INTEGER NOT NULL, 
	return_location_id INTEGER NOT NULL, 
	reserved_start_date TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	reserved_end_date TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	reservation_date TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP, 
	status VARCHAR(20) DEFAULT 'Active', 
	special_requests TEXT, 
	estimated_total DECIMAL(10, 2), 
	PRIMARY KEY (reservation_id), 
	FOREIGN KEY(customer_id) REFERENCES customer (customer_id) ON DELETE CASCADE, 
	FOREIGN KEY(vehicle_id) REFERENCES vehicle (vehicle_id) ON DELETE CASCADE, 
	FOREIGN KEY(pickup_location_id) REFERENCES location (location_id), 
	FOREIGN KEY(return_location_id) REFERENCES location (location_id)
);

CREATE TABLE IF NOT EXISTS vehicle_feature_mapping (
	vehicle_id INTEGER NOT NULL, 
	feature_id INTEGER NOT NULL, 
	PRIMARY KEY (vehicle_id, feature_id), 
	FOREIGN KEY(vehicle_id) REFERENCES vehicle (vehicle_id) ON DELETE CASCADE, 
	FOREIGN KEY(feature_id) REFERENCES vehicle_feature (feature_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS vehicle_maintenance_record (
	maintenance_id SERIAL NOT NULL, 
	vehicle_id INTEGER NOT NULL, 
	last_service_date DATE, 
	next_service_due DATE, 
	total_maintenance_cost DECIMAL(10, 2) DEFAULT 0.0, 
	service_history TEXT, 
	current_condition VARCHAR(20) DEFAULT 'Good', 
	maintenance_alerts TEXT, 
	PRIMARY KEY (maintenance_id), 
	UNIQUE (vehicle_id), 
	FOREIGN KEY(vehicle_id) REFERENCES vehicle (vehicle_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS incident_report (
	incident_id SERIAL NOT NULL, 
	rental_id INTEGER NOT NULL, 
	reported_by INTEGER, 
	incident_date TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	incident_type VARCHAR(30) NOT NULL, 
	description TEXT NOT NULL, 
	estimated_cost DECIMAL(10, 2), 
	status VARCHAR(20) DEFAULT 'Open', 
	photos TEXT, 
	police_report_number VARCHAR(50), 
	PRIMARY KEY (incident_id), 
	FOREIGN KEY(rental_id) REFERENCES rental (rental_id) ON DELETE CASCADE, 
	FOREIGN KEY(reported_by) REFERENCES employee (employee_id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS payment (
	payment_id SERIAL NOT NULL, 
	rental_id INTEGER NOT NULL, 
	payment_date TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP, 
	amount DECIMAL(10, 2) NOT NULL, 
	method VARCHAR(20) NOT NULL, 
	transaction_id VARCHAR(100), 
	status VARCHAR(20) DEFAULT 'Completed', 
	payment_type VARCHAR(20) NOT NULL, 
	PRIMARY KEY (payment_id), 
	FOREIGN KEY(rental_id) REFERENCES rental (rental_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS rental_insurance (
	rental_id INTEGER NOT NULL, 
	plan_id INTEGER NOT NULL, 
	start_date DATE NOT NULL, 
	end_date DATE NOT NULL, 
	premium_amount DECIMAL(8, 2) NOT NULL, 
	PRIMARY KEY (rental_id, plan_id), 
	FOREIGN KEY(rental_id) REFERENCES rental (rental_id) ON DELETE CASCADE, 
	FOREIGN KEY(plan_id) REFERENCES insurance_plan (plan_id) ON DELETE CASCADE
);

-- ----- circular foreign keys (employee <-> location) ----------------------------------------

DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'employee_location_id_fkey'
                   AND conrelid = 'employee'::regclass) THEN
        ALTER TABLE employee ADD CONSTRAINT employee_location_id_fkey FOREIGN KEY(location_id) REFERENCES location (location_id) ON DELETE SET NULL;
    END IF;
END $$;

DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'employee_manager_id_fkey'
                   AND conrelid = 'employee'::regclass) THEN
        ALTER TABLE employee ADD CONSTRAINT employee_manager_id_fkey FOREIGN KEY(manager_id) REFERENCES employee (employee_id) ON DELETE SET NULL;
    END IF;
END $$;

DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'location_manager_id_fkey'
                   AND conrelid = 'location'::regclass) THEN
        ALTER TABLE location ADD CONSTRAINT location_manager_id_fkey FOREIGN KEY(manager_id) REFERENCES employee (employee_id) ON DELETE SET NULL;
    END IF;
END $$;

-- ----- indexes -------------------------------------------------------------------------------

CREATE UNIQUE INDEX IF NOT EXISTS uq_customer_driver_license_lower ON customer (lower(driver_license));

CREATE UNIQUE INDEX IF NOT EXISTS uq_customer_email_lower ON customer (lower(email));

CREATE INDEX IF NOT EXISTS ix_employee_location_id ON employee (location_id);

CREATE UNIQUE INDEX IF NOT EXISTS uq_employee_email_lower ON employee (lower(email));

CREATE INDEX IF NOT EXISTS ix_vehicle_availability ON vehicle (availability);

CREATE INDEX IF NOT EXISTS ix_vehicle_location_id ON vehicle (location_id);

CREATE UNIQUE INDEX IF NOT EXISTS uq_vehicle_license_plate_lower ON vehicle (lower(license_plate));

CREATE INDEX IF NOT EXISTS ix_maintenance_schedule_status_date ON maintenance_schedule (status, scheduled_date);

CREATE INDEX IF NOT EXISTS ix_maintenance_schedule_vehicle_id ON maintenance_schedule (vehicle_id);

CREATE INDEX IF NOT EXISTS ix_rental_customer_id ON rental (customer_id);

CREATE INDEX IF NOT EXISTS ix_rental_status_start_date ON rental (status, start_date);

CREATE INDEX IF NOT EXISTS ix_rental_vehicle_status ON rental (vehicle_id, status);

CREATE INDEX IF NOT EXISTS ix_reservation_customer_id ON reservation (customer_id);

CREATE INDEX IF NOT EXISTS ix_reservation_vehicle_status ON reservation (vehicle_id, status);

CREATE INDEX IF NOT EXISTS ix_incident_report_rental_id ON incident_report (rental_id);

CREATE INDEX IF NOT EXISTS ix_payment_rental_id ON payment (rental_id);

-- ----- updated_at maintenance (MySQL had ON UPDATE CURRENT_TIMESTAMP; Postgres needs a trigger) ---------
CREATE OR REPLACE FUNCTION set_updated_at() RETURNS trigger AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_customer_updated_at ON customer;
CREATE TRIGGER trg_customer_updated_at BEFORE UPDATE ON customer
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();
