ALTER TABLE call_sessions
ADD COLUMN dialogue_state VARCHAR(50) NOT NULL DEFAULT 'STARTED',
ADD COLUMN extracted_data JSONB NOT NULL DEFAULT '{}'::jsonb; 