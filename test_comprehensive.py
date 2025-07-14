#!/usr/bin/env python3
"""
Comprehensive Test Suite for Surgical Care Companion
====================================================

This file contains detailed test scenarios for validating the complete
surgical care companion system including API endpoints, database operations,
Twilio integration, AI conversation flows, and end-to-end workflows.

Usage:
    python test_comprehensive.py --help
    python test_comprehensive.py --run-all
    python test_comprehensive.py --run-unit
    python test_comprehensive.py --run-integration
    python test_comprehensive.py --run-workflow
    python test_comprehensive.py --test-patient-journey
    python test_comprehensive.py --test-twilio-integration
"""

import asyncio
import json
import logging
import requests
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import argparse
import sys
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('test_results.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class SurgicalCareTestSuite:
    """Comprehensive test suite for the Surgical Care Companion system."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.api_base = f"{base_url}/api"
        self.test_results = {
            "passed": 0,
            "failed": 0,
            "errors": [],
            "details": []
        }
        self.test_data = {}
        
    def log_test(self, test_name: str, success: bool, message: str = "", details: Dict = None):
        """Log test results with detailed information."""
        status = "PASS" if success else "FAIL"
        logger.info(f"[{status}] {test_name}: {message}")
        
        if success:
            self.test_results["passed"] += 1
        else:
            self.test_results["failed"] += 1
            self.test_results["errors"].append(f"{test_name}: {message}")
        
        self.test_results["details"].append({
            "test": test_name,
            "success": success,
            "message": message,
            "details": details or {},
            "timestamp": datetime.now().isoformat()
        })

    # =======================================================================
    # SYSTEM HEALTH TESTS
    # =======================================================================

    def test_system_health(self):
        """Test basic system health and service availability."""
        logger.info("🏥 Testing System Health & Service Availability")
        
        # Test main health endpoint
        try:
            response = requests.get(f"{self.base_url}/health", timeout=10)
            if response.status_code == 200:
                self.log_test("system_health", True, "Main health endpoint responding")
            else:
                self.log_test("system_health", False, f"Health endpoint returned {response.status_code}")
        except Exception as e:
            self.log_test("system_health", False, f"Health endpoint failed: {str(e)}")

        # Test API health
        try:
            response = requests.get(f"{self.api_base}/health", timeout=10)
            if response.status_code == 200:
                self.log_test("api_health", True, "API health endpoint responding")
            else:
                self.log_test("api_health", False, f"API health returned {response.status_code}")
        except Exception as e:
            self.log_test("api_health", False, f"API health failed: {str(e)}")

        # Test database connectivity
        try:
            response = requests.get(f"{self.api_base}/health/database", timeout=10)
            if response.status_code == 200:
                self.log_test("database_health", True, "Database connectivity verified")
            else:
                self.log_test("database_health", False, f"Database health check failed: {response.status_code}")
        except Exception as e:
            self.log_test("database_health", False, f"Database connection failed: {str(e)}")

    # =======================================================================
    # CLINICAL STAFF MANAGEMENT TESTS
    # =======================================================================

    def test_clinical_staff_management(self):
        """Test clinical staff creation, retrieval, and management."""
        logger.info("👨‍⚕️ Testing Clinical Staff Management")
        
        # Test staff creation
        staff_data = {
            "name": "Dr. Test Surgeon",
            "email": f"test.surgeon.{int(time.time())}@hospital.com",
            "role": "surgeon"
        }
        
        try:
            response = requests.post(
                f"{self.api_base}/clinical/staff",
                json=staff_data,
                timeout=10
            )
            
            if response.status_code == 201:
                staff_info = response.json()
                self.test_data["clinical_staff_id"] = staff_info["id"]
                self.log_test("staff_creation", True, f"Staff created with ID: {staff_info['id']}")
            else:
                self.log_test("staff_creation", False, f"Staff creation failed: {response.status_code} - {response.text}")
                return
        except Exception as e:
            self.log_test("staff_creation", False, f"Staff creation error: {str(e)}")
            return

        # Test staff retrieval
        try:
            response = requests.get(f"{self.api_base}/clinical/staff", timeout=10)
            if response.status_code == 200:
                staff_list = response.json()
                if len(staff_list) > 0:
                    self.log_test("staff_retrieval", True, f"Retrieved {len(staff_list)} staff members")
                else:
                    self.log_test("staff_retrieval", False, "No staff members found")
            else:
                self.log_test("staff_retrieval", False, f"Staff retrieval failed: {response.status_code}")
        except Exception as e:
            self.log_test("staff_retrieval", False, f"Staff retrieval error: {str(e)}")

        # Test individual staff retrieval
        if "clinical_staff_id" in self.test_data:
            try:
                response = requests.get(
                    f"{self.api_base}/clinical/staff/{self.test_data['clinical_staff_id']}",
                    timeout=10
                )
                if response.status_code == 200:
                    staff_info = response.json()
                    if staff_info["email"] == staff_data["email"]:
                        self.log_test("individual_staff_retrieval", True, "Individual staff retrieval successful")
                    else:
                        self.log_test("individual_staff_retrieval", False, "Staff data mismatch")
                else:
                    self.log_test("individual_staff_retrieval", False, f"Individual staff retrieval failed: {response.status_code}")
            except Exception as e:
                self.log_test("individual_staff_retrieval", False, f"Individual staff retrieval error: {str(e)}")

    # =======================================================================
    # PATIENT MANAGEMENT TESTS
    # =======================================================================

    def test_patient_management(self):
        """Test patient creation, retrieval, and management with call auto-scheduling."""
        logger.info("🏥 Testing Patient Management & Auto-Scheduling")
        
        if "clinical_staff_id" not in self.test_data:
            self.log_test("patient_prerequisites", False, "No clinical staff available for patient creation")
            return

        # Test patient creation with future surgery date
        surgery_date = (datetime.now() + timedelta(days=45)).isoformat()
        patient_data = {
            "name": "Jane Test Patient",
            "primary_phone_number": "+12132757114",
            "secondary_phone_number": "+12132757115",
            "emergency_contact": "John Doe - Husband - +12132757116",
            "surgery_date": surgery_date,
            "primary_physician_id": self.test_data["clinical_staff_id"]
        }
        
        try:
            response = requests.post(
                f"{self.api_base}/patients/",
                json=patient_data,
                timeout=10
            )
            
            if response.status_code == 201:
                patient_info = response.json()
                self.test_data["patient_id"] = patient_info["id"]
                self.log_test("patient_creation", True, f"Patient created with ID: {patient_info['id']}")
            else:
                self.log_test("patient_creation", False, f"Patient creation failed: {response.status_code} - {response.text}")
                return
        except Exception as e:
            self.log_test("patient_creation", False, f"Patient creation error: {str(e)}")
            return

        # Test patient retrieval
        try:
            response = requests.get(f"{self.api_base}/patients/", timeout=10)
            if response.status_code == 200:
                patients = response.json()
                patient_found = any(p["id"] == self.test_data["patient_id"] for p in patients)
                if patient_found:
                    self.log_test("patient_retrieval", True, f"Patient found in list of {len(patients)} patients")
                else:
                    self.log_test("patient_retrieval", False, "Created patient not found in patient list")
            else:
                self.log_test("patient_retrieval", False, f"Patient retrieval failed: {response.status_code}")
        except Exception as e:
            self.log_test("patient_retrieval", False, f"Patient retrieval error: {str(e)}")

        # Test individual patient retrieval
        try:
            response = requests.get(
                f"{self.api_base}/patients/{self.test_data['patient_id']}",
                timeout=10
            )
            if response.status_code == 200:
                patient_info = response.json()
                if patient_info["name"] == patient_data["name"]:
                    self.log_test("individual_patient_retrieval", True, "Individual patient retrieval successful")
                else:
                    self.log_test("individual_patient_retrieval", False, "Patient data mismatch")
            else:
                self.log_test("individual_patient_retrieval", False, f"Individual patient retrieval failed: {response.status_code}")
        except Exception as e:
            self.log_test("individual_patient_retrieval", False, f"Individual patient retrieval error: {str(e)}")

        # Verify auto-scheduled calls were created
        time.sleep(2)  # Allow time for trigger to execute
        try:
            response = requests.get(
                f"{self.api_base}/calls/patient/{self.test_data['patient_id']}/history",
                timeout=10
            )
            if response.status_code == 200:
                call_history = response.json()
                if len(call_history) >= 6:  # Should have 6 pre-op calls
                    self.log_test("auto_call_scheduling", True, f"Auto-scheduled {len(call_history)} calls")
                    self.test_data["scheduled_calls"] = call_history
                else:
                    self.log_test("auto_call_scheduling", False, f"Expected 6+ calls, got {len(call_history)}")
            else:
                self.log_test("auto_call_scheduling", False, f"Call history retrieval failed: {response.status_code}")
        except Exception as e:
            self.log_test("auto_call_scheduling", False, f"Auto-scheduling verification error: {str(e)}")

    # =======================================================================
    # CALL MANAGEMENT TESTS
    # =======================================================================

    def test_call_management(self):
        """Test call initiation, status tracking, and session management."""
        logger.info("📞 Testing Call Management & Twilio Integration")
        
        if "patient_id" not in self.test_data:
            self.log_test("call_prerequisites", False, "No patient available for call testing")
            return

        # Test call initiation
        call_data = {
            "patient_id": self.test_data["patient_id"],
            "call_type": "education"
        }
        
        try:
            response = requests.post(
                f"{self.api_base}/calls/initiate",
                json=call_data,
                timeout=15
            )
            
            if response.status_code == 200:
                call_info = response.json()
                if "call_session_id" in call_info:
                    self.test_data["call_session_id"] = call_info["call_session_id"]
                    self.log_test("call_initiation", True, f"Call initiated with session ID: {call_info['call_session_id']}")
                else:
                    self.log_test("call_initiation", False, "Call response missing session ID")
                    return
            else:
                self.log_test("call_initiation", False, f"Call initiation failed: {response.status_code} - {response.text}")
                return
        except Exception as e:
            self.log_test("call_initiation", False, f"Call initiation error: {str(e)}")
            return

        # Test call session retrieval
        try:
            response = requests.get(
                f"{self.api_base}/calls/{self.test_data['call_session_id']}",
                timeout=10
            )
            if response.status_code == 200:
                call_session = response.json()
                if call_session["call_type"] == "education":
                    self.log_test("call_session_retrieval", True, "Call session retrieved successfully")
                    self.test_data["call_session"] = call_session
                else:
                    self.log_test("call_session_retrieval", False, "Call session data mismatch")
            else:
                self.log_test("call_session_retrieval", False, f"Call session retrieval failed: {response.status_code}")
        except Exception as e:
            self.log_test("call_session_retrieval", False, f"Call session retrieval error: {str(e)}")

        # Test call session update
        update_data = {
            "call_status": "completed",
            "call_outcome": "successful",
            "agent_notes": "Test call completed successfully. Patient responsive and engaged.",
            "compliance_score": 85,
            "concerns_identified": [],
            "risk_level": "low"
        }
        
        try:
            response = requests.put(
                f"{self.api_base}/calls/{self.test_data['call_session_id']}",
                json=update_data,
                timeout=10
            )
            if response.status_code == 200:
                self.log_test("call_session_update", True, "Call session updated successfully")
            else:
                self.log_test("call_session_update", False, f"Call session update failed: {response.status_code}")
        except Exception as e:
            self.log_test("call_session_update", False, f"Call session update error: {str(e)}")

    # =======================================================================
    # SPEECH-TO-TEXT TESTS
    # =======================================================================

    def test_speech_to_text_service(self):
        """Test speech-to-text functionality with various audio formats."""
        logger.info("🎤 Testing Speech-to-Text Service")
        
        # Test health endpoint of speech service
        try:
            response = requests.get("http://localhost:8001/health", timeout=10)
            if response.status_code == 200:
                self.log_test("speech_service_health", True, "Speech-to-text service is healthy")
            else:
                self.log_test("speech_service_health", False, f"Speech service health check failed: {response.status_code}")
                return
        except Exception as e:
            self.log_test("speech_service_health", False, f"Speech service unavailable: {str(e)}")
            return

        # Test with sample audio file (if available)
        sample_audio_paths = [
            "test/sample.wav",
            "test/sample.ogg",
            "backend/test/sample.wav",
            "uploads/test_audio.wav"
        ]
        
        audio_file_found = False
        for audio_path in sample_audio_paths:
            if os.path.exists(audio_path):
                audio_file_found = True
                try:
                    with open(audio_path, 'rb') as audio_file:
                        files = {'audio_file': audio_file}
                        response = requests.post(
                            f"{self.api_base}/voice-chat/transcribe",
                            files=files,
                            timeout=30
                        )
                        
                        if response.status_code == 200:
                            result = response.json()
                            if "transcript" in result:
                                self.log_test("speech_transcription", True, 
                                            f"Audio transcribed: '{result['transcript'][:50]}...'")
                            else:
                                self.log_test("speech_transcription", False, "Transcription response missing transcript")
                        else:
                            self.log_test("speech_transcription", False, 
                                        f"Transcription failed: {response.status_code} - {response.text}")
                except Exception as e:
                    self.log_test("speech_transcription", False, f"Transcription error: {str(e)}")
                break
        
        if not audio_file_found:
            self.log_test("speech_transcription", False, "No sample audio file found for testing")

    # =======================================================================
    # CLINICAL ALERTS TESTS
    # =======================================================================

    def test_clinical_alerts_system(self):
        """Test clinical alert creation, routing, and management."""
        logger.info("🚨 Testing Clinical Alerts System")
        
        if "patient_id" not in self.test_data or "clinical_staff_id" not in self.test_data:
            self.log_test("alerts_prerequisites", False, "Missing patient or staff data for alert testing")
            return

        # Test alert creation
        alert_data = {
            "patient_id": self.test_data["patient_id"],
            "call_session_id": self.test_data.get("call_session_id"),
            "assigned_staff_id": self.test_data["clinical_staff_id"],
            "alert_type": "pain",
            "severity": "high",
            "title": "High Pain Level Reported",
            "description": "Patient reported pain level 8/10 during automated call. Requires immediate clinical review."
        }
        
        try:
            response = requests.post(
                f"{self.api_base}/clinical/alerts",
                json=alert_data,
                timeout=10
            )
            
            if response.status_code == 201:
                alert_info = response.json()
                self.test_data["alert_id"] = alert_info["id"]
                self.log_test("alert_creation", True, f"Alert created with ID: {alert_info['id']}")
            else:
                self.log_test("alert_creation", False, f"Alert creation failed: {response.status_code} - {response.text}")
                return
        except Exception as e:
            self.log_test("alert_creation", False, f"Alert creation error: {str(e)}")
            return

        # Test alert retrieval
        try:
            response = requests.get(f"{self.api_base}/clinical/alerts", timeout=10)
            if response.status_code == 200:
                alerts = response.json()
                alert_found = any(a["id"] == self.test_data["alert_id"] for a in alerts)
                if alert_found:
                    self.log_test("alert_retrieval", True, f"Alert found in list of {len(alerts)} alerts")
                else:
                    self.log_test("alert_retrieval", False, "Created alert not found in alerts list")
            else:
                self.log_test("alert_retrieval", False, f"Alert retrieval failed: {response.status_code}")
        except Exception as e:
            self.log_test("alert_retrieval", False, f"Alert retrieval error: {str(e)}")

        # Test alert acknowledgment
        try:
            response = requests.put(
                f"{self.api_base}/clinical/alerts/{self.test_data['alert_id']}/acknowledge",
                json={"acknowledged_by": self.test_data["clinical_staff_id"]},
                timeout=10
            )
            if response.status_code == 200:
                self.log_test("alert_acknowledgment", True, "Alert acknowledged successfully")
            else:
                self.log_test("alert_acknowledgment", False, f"Alert acknowledgment failed: {response.status_code}")
        except Exception as e:
            self.log_test("alert_acknowledgment", False, f"Alert acknowledgment error: {str(e)}")

    # =======================================================================
    # WEBHOOK TESTS
    # =======================================================================

    def test_twilio_webhooks(self):
        """Test Twilio webhook endpoints and response handling."""
        logger.info("🔗 Testing Twilio Webhook Integration")
        
        # Test voice webhook endpoint
        webhook_data = {
            "CallSid": "test_call_sid_123",
            "From": "+12132757114",
            "To": "+18776589089",
            "CallStatus": "in-progress",
            "Direction": "outbound-api"
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/webhooks/twilio/voice",
                data=webhook_data,  # Twilio sends form data, not JSON
                timeout=10
            )
            
            if response.status_code == 200:
                # Should return TwiML response
                if "xml" in response.headers.get("content-type", "").lower():
                    self.log_test("voice_webhook", True, "Voice webhook returned valid TwiML")
                else:
                    self.log_test("voice_webhook", True, "Voice webhook responded successfully")
            else:
                self.log_test("voice_webhook", False, f"Voice webhook failed: {response.status_code}")
        except Exception as e:
            self.log_test("voice_webhook", False, f"Voice webhook error: {str(e)}")

        # Test status callback webhook
        status_data = {
            "CallSid": "test_call_sid_123",
            "CallStatus": "completed",
            "CallDuration": "120",
            "From": "+12132757114",
            "To": "+18776589089"
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/webhooks/twilio/status",
                data=status_data,
                timeout=10
            )
            
            if response.status_code in [200, 204]:
                self.log_test("status_webhook", True, "Status webhook processed successfully")
            else:
                self.log_test("status_webhook", False, f"Status webhook failed: {response.status_code}")
        except Exception as e:
            self.log_test("status_webhook", False, f"Status webhook error: {str(e)}")

    # =======================================================================
    # END-TO-END WORKFLOW TESTS
    # =======================================================================

    def test_complete_patient_journey(self):
        """Test the complete patient journey from enrollment to follow-up."""
        logger.info("🏃‍♀️ Testing Complete Patient Journey Workflow")
        
        # This test uses data created in previous tests
        if not all(key in self.test_data for key in ["patient_id", "clinical_staff_id"]):
            self.log_test("journey_prerequisites", False, "Missing required test data for journey test")
            return

        # Test call schedule verification
        try:
            response = requests.get(
                f"{self.api_base}/calls/patient/{self.test_data['patient_id']}/history",
                timeout=10
            )
            
            if response.status_code == 200:
                calls = response.json()
                call_types = [call["call_type"] for call in calls]
                expected_types = ["enrollment", "education", "preparation", "final_prep"]
                
                # Check if we have the expected call types
                has_enrollment = "enrollment" in call_types
                has_education = "education" in call_types
                has_preparation = "preparation" in call_types
                
                if has_enrollment and has_education and has_preparation:
                    self.log_test("journey_call_schedule", True, 
                                f"Complete call schedule created: {len(calls)} calls with types: {set(call_types)}")
                else:
                    self.log_test("journey_call_schedule", False, 
                                f"Incomplete call schedule. Found types: {set(call_types)}")
            else:
                self.log_test("journey_call_schedule", False, 
                            f"Failed to retrieve call schedule: {response.status_code}")
        except Exception as e:
            self.log_test("journey_call_schedule", False, f"Call schedule verification error: {str(e)}")

        # Test patient readiness progression
        try:
            # Update patient readiness status
            response = requests.put(
                f"{self.api_base}/patients/{self.test_data['patient_id']}",
                json={"surgery_readiness_status": "ready"},
                timeout=10
            )
            
            if response.status_code == 200:
                self.log_test("journey_readiness_update", True, "Patient readiness status updated")
            else:
                self.log_test("journey_readiness_update", False, 
                            f"Readiness update failed: {response.status_code}")
        except Exception as e:
            self.log_test("journey_readiness_update", False, f"Readiness update error: {str(e)}")

        # Test compliance score calculation
        try:
            response = requests.get(
                f"{self.api_base}/patients/{self.test_data['patient_id']}/compliance",
                timeout=10
            )
            
            if response.status_code == 200:
                compliance_data = response.json()
                if "overall_score" in compliance_data:
                    score = compliance_data["overall_score"]
                    if 0 <= score <= 100:
                        self.log_test("journey_compliance_score", True, 
                                    f"Compliance score calculated: {score}")
                    else:
                        self.log_test("journey_compliance_score", False, 
                                    f"Invalid compliance score: {score}")
                else:
                    self.log_test("journey_compliance_score", False, 
                                "Compliance response missing score")
            else:
                self.log_test("journey_compliance_score", False, 
                            f"Compliance calculation failed: {response.status_code}")
        except Exception as e:
            self.log_test("journey_compliance_score", False, f"Compliance calculation error: {str(e)}")

    # =======================================================================
    # PERFORMANCE TESTS
    # =======================================================================

    def test_system_performance(self):
        """Test system performance under load."""
        logger.info("⚡ Testing System Performance")
        
        # Test response times for key endpoints
        endpoints_to_test = [
            ("/health", "GET"),
            ("/api/health", "GET"),
            ("/api/patients/", "GET"),
            ("/api/clinical/staff", "GET"),
            ("/api/clinical/alerts", "GET")
        ]
        
        for endpoint, method in endpoints_to_test:
            start_time = time.time()
            try:
                if method == "GET":
                    response = requests.get(f"{self.base_url}{endpoint}", timeout=5)
                else:
                    response = requests.post(f"{self.base_url}{endpoint}", timeout=5)
                
                end_time = time.time()
                response_time = end_time - start_time
                
                if response.status_code < 400 and response_time < 2.0:
                    self.log_test(f"performance_{endpoint.replace('/', '_')}", True, 
                                f"Response time: {response_time:.3f}s")
                else:
                    self.log_test(f"performance_{endpoint.replace('/', '_')}", False, 
                                f"Slow response or error: {response_time:.3f}s, status: {response.status_code}")
            except Exception as e:
                self.log_test(f"performance_{endpoint.replace('/', '_')}", False, 
                            f"Performance test error: {str(e)}")

    # =======================================================================
    # TEST ORCHESTRATION METHODS
    # =======================================================================

    def run_unit_tests(self):
        """Run all unit-level tests."""
        logger.info("🧪 Running Unit Tests")
        self.test_system_health()
        self.test_clinical_staff_management()
        self.test_speech_to_text_service()

    def run_integration_tests(self):
        """Run integration tests that require multiple components."""
        logger.info("🔗 Running Integration Tests")
        self.test_patient_management()
        self.test_call_management()
        self.test_clinical_alerts_system()
        self.test_twilio_webhooks()

    def run_workflow_tests(self):
        """Run end-to-end workflow tests."""
        logger.info("🏃‍♀️ Running Workflow Tests")
        self.test_complete_patient_journey()
        self.test_system_performance()

    def run_all_tests(self):
        """Run the complete test suite."""
        logger.info("🚀 Running Complete Test Suite")
        logger.info("=" * 60)
        
        self.run_unit_tests()
        logger.info("-" * 40)
        
        self.run_integration_tests()
        logger.info("-" * 40)
        
        self.run_workflow_tests()
        logger.info("-" * 40)

    def generate_test_report(self):
        """Generate a comprehensive test report."""
        total_tests = self.test_results["passed"] + self.test_results["failed"]
        success_rate = (self.test_results["passed"] / total_tests * 100) if total_tests > 0 else 0
        
        report = f"""
🏥 Surgical Care Companion - Test Report
========================================

📊 Test Summary:
- Total Tests: {total_tests}
- Passed: {self.test_results["passed"]}
- Failed: {self.test_results["failed"]}
- Success Rate: {success_rate:.1f}%

"""
        
        if self.test_results["failed"] > 0:
            report += "❌ Failed Tests:\n"
            for error in self.test_results["errors"]:
                report += f"  - {error}\n"
            report += "\n"
        
        report += "📋 Detailed Results:\n"
        for detail in self.test_results["details"]:
            status = "✅" if detail["success"] else "❌"
            report += f"{status} {detail['test']}: {detail['message']}\n"
        
        report += f"\n🕒 Test completed at: {datetime.now().isoformat()}\n"
        
        # Save report to file
        with open("test_report.txt", "w") as f:
            f.write(report)
        
        logger.info(report)
        return report

def main():
    """Main test execution function."""
    parser = argparse.ArgumentParser(description="Surgical Care Companion Test Suite")
    parser.add_argument("--base-url", default="http://localhost:8000", 
                       help="Base URL for the API (default: http://localhost:8000)")
    parser.add_argument("--run-all", action="store_true", 
                       help="Run all tests")
    parser.add_argument("--run-unit", action="store_true", 
                       help="Run unit tests only")
    parser.add_argument("--run-integration", action="store_true", 
                       help="Run integration tests only")
    parser.add_argument("--run-workflow", action="store_true", 
                       help="Run workflow tests only")
    parser.add_argument("--test-patient-journey", action="store_true", 
                       help="Run patient journey test only")
    parser.add_argument("--test-twilio-integration", action="store_true", 
                       help="Run Twilio integration test only")
    
    args = parser.parse_args()
    
    # Initialize test suite
    test_suite = SurgicalCareTestSuite(args.base_url)
    
    try:
        if args.run_all:
            test_suite.run_all_tests()
        elif args.run_unit:
            test_suite.run_unit_tests()
        elif args.run_integration:
            test_suite.run_integration_tests()
        elif args.run_workflow:
            test_suite.run_workflow_tests()
        elif args.test_patient_journey:
            test_suite.test_complete_patient_journey()
        elif args.test_twilio_integration:
            test_suite.test_call_management()
            test_suite.test_twilio_webhooks()
        else:
            # Default: run all tests
            test_suite.run_all_tests()
    
    except KeyboardInterrupt:
        logger.info("\n🛑 Test execution interrupted by user")
    except Exception as e:
        logger.error(f"🚨 Test execution failed: {str(e)}")
    finally:
        # Generate final report
        test_suite.generate_test_report()

if __name__ == "__main__":
    main()
