ALTER TABLE patients
    ADD COLUMN IF NOT EXISTS first_name VARCHAR NOT NULL,
    ADD COLUMN IF NOT EXISTS last_name VARCHAR NOT NULL,
    ADD COLUMN IF NOT EXISTS date_of_birth DATE NOT NULL,
    ADD COLUMN IF NOT EXISTS primary_phone VARCHAR NOT NULL,
    ADD COLUMN IF NOT EXISTS secondary_phone VARCHAR,
    ADD COLUMN IF NOT EXISTS surgery_readiness_status VARCHAR DEFAULT 'pending',
    ADD COLUMN IF NOT EXISTS surgery_date TIMESTAMP; 