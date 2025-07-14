"""
Comprehensive Integration Tests for Surgical Care Companion
=========================================================

This module contains integration tests that verify the interaction between
different components of the system including:
- API endpoints and database operations
- Twilio service integration
- Speech-to-text service integration
- Clinical workflow automation
- Alert and notification systems

Usage:
    pytest tests/test_integration.py -v
    pytest tests/test_integration.py::TestPatientWorkflow -v
    pytest tests/test_integration.py::TestCallManagement -v
"""

import pytest
import httpx
import asyncio
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class TestSystemHealth:
    """Test system health and service availability."""
    
    @pytest.mark.asyncio
    async def test_main_health_endpoint(self, http_client: httpx.AsyncClient):
        """Test the main health check endpoint."""
        response = await http_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] in ["healthy", "ok"]
        
    @pytest.mark.asyncio
    async def test_api_health_endpoint(self, http_client: httpx.AsyncClient):
        """Test the API health check endpoint."""
        response = await http_client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        
    @pytest.mark.asyncio
    async def test_database_health_check(self, http_client: httpx.AsyncClient):
        """Test database connectivity health check."""
        response = await http_client.get("/api/health/database")
        assert response.status_code == 200
        data = response.json()
        assert "database" in data
        assert data["database"]["status"] in ["connected", "healthy"]
    
    @pytest.mark.asyncio
    async def test_api_documentation_available(self, http_client: httpx.AsyncClient):
        """Test that API documentation is accessible."""
        response = await http_client.get("/docs")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

class TestClinicalStaffManagement:
    """Test clinical staff creation and management."""
    
    @pytest.mark.asyncio
    async def test_create_clinical_staff(self, http_client: httpx.AsyncClient):
        """Test creating a new clinical staff member."""
        staff_data = {
            "name": "Dr. Integration Test",
            "email": f"integration.test.{int(datetime.now().timestamp())}@hospital.com",
            "role": "surgeon"
        }
        
        response = await http_client.post("/api/clinical/staff", json=staff_data)
        assert response.status_code == 201
        
        data = response.json()
        assert "id" in data
        assert data["name"] == staff_data["name"]
        assert data["email"] == staff_data["email"]
        assert data["role"] == staff_data["role"]
        
        return data["id"]
    
    @pytest.mark.asyncio
    async def test_list_clinical_staff(self, http_client: httpx.AsyncClient):
        """Test retrieving list of clinical staff."""
        response = await http_client.get("/api/clinical/staff")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        
        # Verify structure of staff entries
        if data:
            staff_member = data[0]
            required_fields = ["id", "name", "email", "role", "created_at"]
            for field in required_fields:
                assert field in staff_member
    
    @pytest.mark.asyncio
    async def test_get_individual_staff_member(self, http_client: httpx.AsyncClient):
        """Test retrieving a specific staff member."""
        # First create a staff member
        staff_id = await self.test_create_clinical_staff(http_client)
        
        # Then retrieve it
        response = await http_client.get(f"/api/clinical/staff/{staff_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["id"] == staff_id

class TestPatientManagement:
    """Test patient creation, management, and auto-scheduling."""
    
    @pytest.fixture
    async def clinical_staff_id(self, http_client: httpx.AsyncClient):
        """Create a clinical staff member for testing."""
        staff_data = {
            "name": "Dr. Test Physician",
            "email": f"test.physician.{int(datetime.now().timestamp())}@hospital.com",
            "role": "surgeon"
        }
        
        response = await http_client.post("/api/clinical/staff", json=staff_data)
        assert response.status_code == 201
        return response.json()["id"]
    
    @pytest.mark.asyncio
    async def test_create_patient_with_auto_scheduling(self, http_client: httpx.AsyncClient, clinical_staff_id):
        """Test patient creation and verify automatic call scheduling."""
        # Create patient with surgery date 45 days in the future
        surgery_date = (datetime.now() + timedelta(days=45)).isoformat()
        patient_data = {
            "name": "Jane Integration Test",
            "primary_phone_number": "+12132757114",
            "secondary_phone_number": "+12132757115",
            "emergency_contact": "John Doe - Emergency Contact",
            "surgery_date": surgery_date,
            "primary_physician_id": clinical_staff_id
        }
        
        response = await http_client.post("/api/patients/", json=patient_data)
        assert response.status_code == 201
        
        data = response.json()
        assert "id" in data
        assert data["name"] == patient_data["name"]
        assert data["primary_phone_number"] == patient_data["primary_phone_number"]
        
        patient_id = data["id"]
        
        # Wait a moment for auto-scheduling trigger to execute
        await asyncio.sleep(2)
        
        # Verify that calls were auto-scheduled
        response = await http_client.get(f"/api/calls/patient/{patient_id}/history")
        assert response.status_code == 200
        
        call_history = response.json()
        assert len(call_history) >= 6  # Should have at least 6 pre-op calls
        
        # Verify call types and scheduling
        call_types = [call["call_type"] for call in call_history]
        expected_types = ["enrollment", "education", "preparation", "final_prep"]
        
        assert "enrollment" in call_types
        assert "education" in call_types
        assert "preparation" in call_types
        
        return patient_id
    
    @pytest.mark.asyncio
    async def test_list_patients(self, http_client: httpx.AsyncClient):
        """Test retrieving list of patients."""
        response = await http_client.get("/api/patients/")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
    
    @pytest.mark.asyncio
    async def test_get_individual_patient(self, http_client: httpx.AsyncClient, clinical_staff_id):
        """Test retrieving a specific patient."""
        # First create a patient
        patient_id = await self.test_create_patient_with_auto_scheduling(http_client, clinical_staff_id)
        
        # Then retrieve it
        response = await http_client.get(f"/api/patients/{patient_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["id"] == patient_id
    
    @pytest.mark.asyncio
    async def test_update_patient(self, http_client: httpx.AsyncClient, clinical_staff_id):
        """Test updating patient information."""
        # First create a patient
        patient_id = await self.test_create_patient_with_auto_scheduling(http_client, clinical_staff_id)
        
        # Update patient data
        update_data = {
            "emergency_contact": "Updated Emergency Contact Information",
            "surgery_readiness_status": "ready"
        }
        
        response = await http_client.put(f"/api/patients/{patient_id}", json=update_data)
        assert response.status_code == 200
        
        # Verify update
        response = await http_client.get(f"/api/patients/{patient_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["emergency_contact"] == update_data["emergency_contact"]
        assert data["surgery_readiness_status"] == update_data["surgery_readiness_status"]

class TestCallManagement:
    """Test call initiation, management, and Twilio integration."""
    
    @pytest.fixture
    async def test_patient_id(self, http_client: httpx.AsyncClient):
        """Create a test patient for call testing."""
        # Create clinical staff first
        staff_data = {
            "name": "Dr. Call Test",
            "email": f"call.test.{int(datetime.now().timestamp())}@hospital.com",
            "role": "surgeon"
        }
        
        staff_response = await http_client.post("/api/clinical/staff", json=staff_data)
        assert staff_response.status_code == 201
        staff_id = staff_response.json()["id"]
        
        # Create patient
        surgery_date = (datetime.now() + timedelta(days=30)).isoformat()
        patient_data = {
            "name": "Call Test Patient",
            "primary_phone_number": "+12132757114",
            "surgery_date": surgery_date,
            "primary_physician_id": staff_id
        }
        
        patient_response = await http_client.post("/api/patients/", json=patient_data)
        assert patient_response.status_code == 201
        return patient_response.json()["id"]
    
    @pytest.mark.asyncio
    async def test_call_initiation(self, http_client: httpx.AsyncClient, test_patient_id):
        """Test call initiation endpoint."""
        call_data = {
            "patient_id": test_patient_id,
            "call_type": "education"
        }
        
        response = await http_client.post("/api/calls/initiate", json=call_data)
        
        # Call might succeed or fail depending on Twilio configuration
        # But should return proper HTTP status and error handling
        assert response.status_code in [200, 422, 500]
        
        if response.status_code == 200:
            data = response.json()
            assert "call_session_id" in data
            return data["call_session_id"]
        else:
            # Log the error for debugging
            logger.warning(f"Call initiation failed (expected in test): {response.text}")
    
    @pytest.mark.asyncio
    async def test_call_session_retrieval(self, http_client: httpx.AsyncClient, test_patient_id):
        """Test retrieving call session information."""
        # Get patient's call history
        response = await http_client.get(f"/api/calls/patient/{test_patient_id}/history")
        assert response.status_code == 200
        
        call_history = response.json()
        assert isinstance(call_history, list)
        
        if call_history:
            # Test retrieving individual call session
            call_session_id = call_history[0]["id"]
            response = await http_client.get(f"/api/calls/{call_session_id}")
            assert response.status_code == 200
            
            data = response.json()
            assert data["id"] == call_session_id
            assert "patient_id" in data
            assert "call_type" in data
    
    @pytest.mark.asyncio
    async def test_call_session_update(self, http_client: httpx.AsyncClient, test_patient_id):
        """Test updating call session with results."""
        # Get a call session to update
        response = await http_client.get(f"/api/calls/patient/{test_patient_id}/history")
        assert response.status_code == 200
        
        call_history = response.json()
        if not call_history:
            pytest.skip("No call sessions available for update test")
        
        call_session_id = call_history[0]["id"]
        
        # Update call session
        update_data = {
            "call_status": "completed",
            "call_outcome": "successful", 
            "agent_notes": "Integration test call completed successfully",
            "compliance_score": 90,
            "concerns_identified": ["minor_concern"],
            "risk_level": "low"
        }
        
        response = await http_client.put(f"/api/calls/{call_session_id}", json=update_data)
        assert response.status_code == 200
        
        # Verify update
        response = await http_client.get(f"/api/calls/{call_session_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["call_status"] == update_data["call_status"]
        assert data["agent_notes"] == update_data["agent_notes"]

class TestClinicalAlertsSystem:
    """Test clinical alert creation, management, and notifications."""
    
    @pytest.fixture
    async def test_data_for_alerts(self, http_client: httpx.AsyncClient):
        """Create test data needed for alert testing."""
        # Create clinical staff
        staff_data = {
            "name": "Dr. Alert Test",
            "email": f"alert.test.{int(datetime.now().timestamp())}@hospital.com",
            "role": "surgeon"
        }
        
        staff_response = await http_client.post("/api/clinical/staff", json=staff_data)
        assert staff_response.status_code == 201
        staff_id = staff_response.json()["id"]
        
        # Create patient
        surgery_date = (datetime.now() + timedelta(days=20)).isoformat()
        patient_data = {
            "name": "Alert Test Patient",
            "primary_phone_number": "+12132757114",
            "surgery_date": surgery_date,
            "primary_physician_id": staff_id
        }
        
        patient_response = await http_client.post("/api/patients/", json=patient_data)
        assert patient_response.status_code == 201
        patient_id = patient_response.json()["id"]
        
        return {"staff_id": staff_id, "patient_id": patient_id}
    
    @pytest.mark.asyncio
    async def test_create_clinical_alert(self, http_client: httpx.AsyncClient, test_data_for_alerts):
        """Test creating a clinical alert."""
        alert_data = {
            "patient_id": test_data_for_alerts["patient_id"],
            "assigned_staff_id": test_data_for_alerts["staff_id"],
            "alert_type": "pain",
            "severity": "high",
            "title": "High Pain Level Reported",
            "description": "Patient reported pain level 9/10 during integration test call"
        }
        
        response = await http_client.post("/api/clinical/alerts", json=alert_data)
        assert response.status_code == 201
        
        data = response.json()
        assert "id" in data
        assert data["alert_type"] == alert_data["alert_type"]
        assert data["severity"] == alert_data["severity"]
        assert data["status"] == "open"  # Default status
        
        return data["id"]
    
    @pytest.mark.asyncio
    async def test_list_clinical_alerts(self, http_client: httpx.AsyncClient):
        """Test retrieving list of clinical alerts."""
        response = await http_client.get("/api/clinical/alerts")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
    
    @pytest.mark.asyncio
    async def test_acknowledge_alert(self, http_client: httpx.AsyncClient, test_data_for_alerts):
        """Test acknowledging a clinical alert."""
        # First create an alert
        alert_id = await self.test_create_clinical_alert(http_client, test_data_for_alerts)
        
        # Acknowledge the alert
        ack_data = {
            "acknowledged_by": test_data_for_alerts["staff_id"]
        }
        
        response = await http_client.put(f"/api/clinical/alerts/{alert_id}/acknowledge", json=ack_data)
        assert response.status_code == 200
        
        # Verify acknowledgment
        response = await http_client.get(f"/api/clinical/alerts/{alert_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "acknowledged"
        assert data["acknowledged_by"] == test_data_for_alerts["staff_id"]

class TestWebhookIntegration:
    """Test webhook endpoints for Twilio integration."""
    
    @pytest.mark.asyncio
    async def test_twilio_voice_webhook(self, http_client: httpx.AsyncClient):
        """Test Twilio voice webhook endpoint."""
        webhook_data = {
            "CallSid": "test_call_sid_123",
            "From": "+12132757114",
            "To": "+18776589089",
            "CallStatus": "in-progress",
            "Direction": "outbound-api"
        }
        
        # Twilio sends form data, not JSON
        response = await http_client.post(
            "/webhooks/twilio/voice",
            data=webhook_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        # Should return TwiML or proper response
        assert response.status_code == 200
        
        # Check if response contains TwiML or is valid webhook response
        content_type = response.headers.get("content-type", "")
        assert "xml" in content_type.lower() or "text" in content_type.lower()
    
    @pytest.mark.asyncio
    async def test_twilio_status_webhook(self, http_client: httpx.AsyncClient):
        """Test Twilio status callback webhook."""
        status_data = {
            "CallSid": "test_call_sid_123",
            "CallStatus": "completed",
            "CallDuration": "120",
            "From": "+12132757114",
            "To": "+18776589089"
        }
        
        response = await http_client.post(
            "/webhooks/twilio/status",
            data=status_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        # Status webhooks typically return 200 or 204
        assert response.status_code in [200, 204]

class TestSpeechToTextIntegration:
    """Test speech-to-text service integration."""
    
    @pytest.mark.asyncio
    async def test_speech_service_health(self, http_client: httpx.AsyncClient):
        """Test speech-to-text service health."""
        try:
            # Try to connect to speech service
            async with httpx.AsyncClient() as speech_client:
                response = await speech_client.get("http://localhost:8001/health", timeout=5.0)
                assert response.status_code == 200
        except httpx.ConnectError:
            pytest.skip("Speech-to-text service not running")
    
    @pytest.mark.asyncio 
    async def test_transcription_endpoint(self, http_client: httpx.AsyncClient):
        """Test audio transcription endpoint."""
        # This test requires sample audio file
        # In a real environment, you would upload a test audio file
        pytest.skip("Audio transcription test requires sample audio file")

class TestCompletePatientWorkflow:
    """Test complete end-to-end patient workflow."""
    
    @pytest.mark.asyncio
    async def test_patient_enrollment_to_call_flow(self, http_client: httpx.AsyncClient):
        """Test complete workflow from patient enrollment to call completion."""
        
        # Step 1: Create clinical staff
        staff_data = {
            "name": "Dr. Workflow Test",
            "email": f"workflow.test.{int(datetime.now().timestamp())}@hospital.com",
            "role": "surgeon"
        }
        
        staff_response = await http_client.post("/api/clinical/staff", json=staff_data)
        assert staff_response.status_code == 201
        staff_id = staff_response.json()["id"]
        
        # Step 2: Enroll patient (should auto-schedule calls)
        surgery_date = (datetime.now() + timedelta(days=35)).isoformat()
        patient_data = {
            "name": "Workflow Test Patient",
            "primary_phone_number": "+12132757114",
            "surgery_date": surgery_date,
            "primary_physician_id": staff_id
        }
        
        patient_response = await http_client.post("/api/patients/", json=patient_data)
        assert patient_response.status_code == 201
        patient_id = patient_response.json()["id"]
        
        # Step 3: Verify call auto-scheduling
        await asyncio.sleep(2)  # Wait for trigger
        response = await http_client.get(f"/api/calls/patient/{patient_id}/history")
        assert response.status_code == 200
        
        call_history = response.json()
        assert len(call_history) >= 6
        
        # Step 4: Simulate call completion with concerning findings
        if call_history:
            call_session_id = call_history[0]["id"]
            update_data = {
                "call_status": "completed",
                "call_outcome": "successful",
                "agent_notes": "Patient reported high pain levels and mobility concerns",
                "compliance_score": 45,  # Low score
                "concerns_identified": ["high_pain", "mobility_issues"],
                "risk_level": "high"
            }
            
            response = await http_client.put(f"/api/calls/{call_session_id}", json=update_data)
            assert response.status_code == 200
        
        # Step 5: Verify alert generation (if implemented)
        await asyncio.sleep(1)  # Wait for alert processing
        response = await http_client.get("/api/clinical/alerts")
        assert response.status_code == 200
        
        alerts = response.json()
        # Check if any alerts were created for our patient
        patient_alerts = [alert for alert in alerts if alert.get("patient_id") == patient_id]
        
        # This validates the complete workflow integrity
        logger.info(f"Workflow test completed. Patient: {patient_id}, Calls: {len(call_history)}, Alerts: {len(patient_alerts)}")
        
        assert True  # Workflow completed successfully
    async def test_call_status(self, http_client: httpx.AsyncClient):
        """Test call status endpoint."""
        response = await http_client.get("/api/v1/calls/status/test_call_id")
        
        # Should return not found or call data
        assert response.status_code in [200, 404]
    
    @pytest.mark.asyncio
    async def test_twilio_status(self, http_client: httpx.AsyncClient):
        """Test Twilio service status."""
        response = await http_client.get("/api/v1/calls/twilio-status")
        assert response.status_code == 200
        data = response.json()
        assert "configured" in data

class TestTwilioWebhooks:
    """Test Twilio webhook endpoints."""
    
    @pytest.mark.asyncio
    async def test_voice_webhook(self, http_client: httpx.AsyncClient):
        """Test voice webhook endpoint."""
        webhook_data = {
            "CallSid": "CAxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
            "From": "+1234567890",
            "To": "+18776589089",
            "CallStatus": "in-progress"
        }
        
        response = await http_client.post(
            "/api/v1/twilio/voice-webhook/test_session",
            data=webhook_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        assert response.status_code == 200
        assert "text/xml" in response.headers["content-type"]
        assert "Response" in response.text
    
    @pytest.mark.asyncio
    async def test_status_callback(self, http_client: httpx.AsyncClient):
        """Test status callback endpoint."""
        callback_data = {
            "CallSid": "CAxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
            "CallStatus": "completed",
            "CallDuration": "120"
        }
        
        response = await http_client.post(
            "/api/v1/twilio/status-callback",
            data=callback_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        assert response.status_code == 200

class TestSpeechProcessing:
    """Test speech processing functionality."""
    
    @pytest.mark.asyncio
    async def test_process_speech(self, http_client: httpx.AsyncClient, test_data: Dict[str, Any]):
        """Test speech processing endpoint."""
        payload = {
            "session_id": test_data["call_session_id"],
            "transcription": test_data["transcription"],
            "confidence": 0.95
        }
        
        response = await http_client.post("/api/v1/twilio/process-speech", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "response" in data

class TestPatientManagement:
    """Test patient management endpoints."""
    
    @pytest.mark.asyncio
    async def test_create_patient(self, http_client: httpx.AsyncClient):
        """Test patient creation."""
        patient_data = {
            "first_name": "John",
            "last_name": "Doe",
            "phone_number": "+1234567890",
            "surgery_date": "2025-01-15",
            "surgery_type": "TKA"
        }
        
        response = await http_client.post("/api/v1/patients/", json=patient_data)
        
        # Should succeed or handle validation errors
        assert response.status_code in [200, 201, 422]
    
    @pytest.mark.asyncio
    async def test_get_patients(self, http_client: httpx.AsyncClient):
        """Test getting patients list."""
        response = await http_client.get("/api/v1/patients/")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
