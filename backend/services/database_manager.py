# surgicalcompanian/backend/services/database_manager.py
import psycopg2
from psycopg2.errors import ConnectionFailure
import os
import datetime
import uuid
import json
import logging
from urllib.parse import urlparse # ADDED: for parsing DATABASE_URL
from typing import Optional # ADDED: for type hinting

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self):
        # Database connection parameters from environment variables
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            raise ValueError("DATABASE_URL environment variable is not set.")

        # Parse the DATABASE_URL (e.g., postgresql://user:password@host:port/dbname)
        result = urlparse(database_url)
        self.conn_params = {
            "database": result.path[1:], # Remove leading /
            "user": result.username,
            "password": result.password,
            "host": result.hostname,
            "port": result.port if result.port else 5432 # Default to 5432 if not specified
        }
        
        # Basic check for essential params
        if not all([self.conn_params["database"], self.conn_params["user"], self.conn_params["password"], self.conn_params["host"]]):
            raise ValueError("Incomplete DATABASE_URL provided. Check components.")
        
        print("DB_MANAGER_INIT: DatabaseManager instance initialized.")
        print(f"DB_MANAGER_INIT: Connecting to DB: {self.conn_params['host']}:{self.conn_params['port']}/{self.conn_params['database']} as {self.conn_params['user']}")
                            
    def _get_connection(self):
        """Establishes and returns a new database connection."""
        print("DB_MANAGER: Attempting to get DB connection...")
        try:
            conn = psycopg2.connect(**self.conn_params)
            print("DB_MANAGER: Successfully got DB connection.")
            return conn
        except psycopg2.Error as e:
            print(f"DB_MANAGER: ERROR - getting DB connection: {e}")
            raise ConnectionFailure(f"PostgreSQL connection failed: {e}")

    def get_patient_data(self, patient_id: str):
        conn = None
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute(
                "SELECT id, first_name, last_name, surgery_date, report FROM patients WHERE id = %s;",
                (patient_id,)
            )
            record = cur.fetchone()
            if record:
                return {
                    "id": str(record[0]),
                    "first_name": record[1],
                    "last_name": record[2],
                    "surgery_date": record[3],
                    "report": record[4]
                }
            return None
        except psycopg2.Error as e:
            print(f"Error fetching patient data for ID {patient_id}: {e}")
            raise
        finally:
            if conn: conn.close()

    def get_call_session_data(self, call_session_id: str):
        conn = None
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute(
                "SELECT id, patient_id, call_status, actual_call_start, conversation_history, call_type, call_duration_seconds FROM call_sessions WHERE id = %s;",
                (call_session_id,)
            )
            record = cur.fetchone()
            if record:
                # Parse conversation_history properly
                conversation_history = record[4]
                if isinstance(conversation_history, str):
                    try:
                        conversation_history = json.loads(conversation_history)
                    except (json.JSONDecodeError, TypeError):
                        conversation_history = []
                elif conversation_history is None:
                    conversation_history = []
                
                return {
                    "id": str(record[0]),
                    "patient_id": str(record[1]),
                    "call_status": record[2],
                    "call_type": record[5],
                    "actual_call_start": record[3],
                    "conversation_history": conversation_history,
                    "call_duration_seconds": record[6]
                }
            return None
        except psycopg2.Error as e:
            print(f"Error fetching call session data for ID {call_session_id}: {e}")
            raise
        finally:
            if conn: conn.close()

    def update_call_session(self, call_session_id: str, updates: dict):
        conn = None
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            
            set_clauses = []
            values = []
            for key, val in updates.items():
                set_clauses.append(f"{key} = %s")
                if isinstance(val, (dict, list)):
                    values.append(json.dumps(val))
                    set_clauses[-1] += "::jsonb"
                else:
                    values.append(val)
            
            values.append(call_session_id)
            
            sql = f"UPDATE call_sessions SET {', '.join(set_clauses)}, updated_at = NOW() WHERE id = %s;"
            cur.execute(sql, tuple(values))
            conn.commit()
        except psycopg2.Error as e:
            print(f"Error updating call session {call_session_id}: {e}")
            if conn: conn.rollback()
            raise
        finally:
            if conn: conn.close()

    def update_patient_report(self, patient_id: str, new_report_json: dict):
        """
        Updates a patient's report data in the database.
        """
        conn = None
        try:
            conn = self._get_connection()
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE patients SET report = %s::jsonb, updated_at = NOW() WHERE id = %s;",
                    (json.dumps(new_report_json), patient_id)
                )
            conn.commit()
            logger.info(f"Successfully updated report for patient {patient_id}")
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Error updating report for patient {patient_id}: {e}")
            raise
        finally:
            if conn:
                conn.close()
            
    # NOTE: create_dummy_patient_and_session is moved to backend/scripts/init_db.py
    # and backend/scripts/setup_education_test.py for cleaner setup via scripts.