CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_call_sessions_updated_at
BEFORE UPDATE ON call_sessions
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column(); 