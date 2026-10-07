-- =====================================================================================================
-- Reference data the application expects. Idempotent: safe to run repeatedly, never overwrites edits.
-- =====================================================================================================

-- Membership tiers. NOTE: every customer is created on the 'Standard' tier, so that row must exist.
INSERT INTO membership_tier (tier_name, description, monthly_fee, free_upgrades, bonus_point_rate) VALUES
    ('Standard', 'Default tier for every customer',       0.00, 0, 1.00),
    ('Premium',  'Monthly plan: 1 free upgrade, +25% points', 9.99, 1, 1.25),
    ('Elite',    'Monthly plan: 3 free upgrades, +50% points', 19.99, 3, 1.50)
ON CONFLICT (tier_name) DO NOTHING;

-- Insurance plans
INSERT INTO insurance_plan (name, description, daily_cost, coverage_amount, deductible, is_active)
SELECT v.* FROM (VALUES
    ('Basic Protection',    'Liability coverage only',                         9.99::numeric,  50000.00::numeric, 1000.00::numeric, true),
    ('Standard Protection', 'Liability + collision damage waiver',            19.99::numeric, 100000.00::numeric,  500.00::numeric, true),
    ('Premium Protection',  'Full coverage, zero deductible, roadside help',  34.99::numeric, 250000.00::numeric,    0.00::numeric, true)
) AS v(name, description, daily_cost, coverage_amount, deductible, is_active)
WHERE NOT EXISTS (SELECT 1 FROM insurance_plan p WHERE p.name = v.name);

-- Vehicle features
INSERT INTO vehicle_feature (name, description, category)
SELECT v.* FROM (VALUES
    ('GPS Navigation',   'Built-in navigation system',          'Convenience'),
    ('Bluetooth',        'Hands-free calling and audio',        'Entertainment'),
    ('Apple CarPlay',    'Phone projection (CarPlay/Android Auto)', 'Entertainment'),
    ('Backup Camera',    'Rear-view camera',                    'Safety'),
    ('Blind Spot Monitor','Warns about vehicles in blind spots','Safety'),
    ('Heated Seats',     'Front heated seats',                  'Comfort'),
    ('Sunroof',          'Power sunroof',                       'Comfort'),
    ('Child Seat',       'Child safety seat available',         'Safety')
) AS v(name, description, category)
WHERE NOT EXISTS (SELECT 1 FROM vehicle_feature f WHERE f.name = v.name);
