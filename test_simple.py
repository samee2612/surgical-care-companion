#!/usr/bin/env python3
"""
Simple Comprehensive Test Suite for Surgical Care Companion
==========================================================
Windows-compatible version without unicode emojis.
"""

import requests
import json
import time
import uuid
from datetime import datetime, timedelta
import logging

# Configure simple logging without unicode
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('test_results.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SimpleTestSuite:
    """Simple test suite for the Surgical Care Companion system."""
    
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.api_base = f"{base_url}/api/v1"
        self.test_results = {
            "passed": 0,
            "failed": 0,
            "errors": [],
            "details": []
        }
        self.test_data = {}
        
    def log_test(self, test_name, success, message=""):
        """Log test results."""
        status = "PASS" if success else "FAIL"
        logger.info(f"[{status}] {test_name}: {message}")
        
        if success:
            self.test_results["passed"] += 1
        else:
            self.test_results["failed"] += 1
            self.test_results["errors"].append(f"{test_name}: {message}")

    def test_system_health(self):
        """Test basic system health."""
        logger.info("Testing System Health & Service Availability")
        
        # Test main health endpoint
        try:
            response = requests.get(f"{self.base_url}/health", timeout=10)
            if response.status_code == 200:
                self.log_test("system_health", True, "Main health endpoint responding")
            else:
                self.log_test("system_health", False, f"Health endpoint returned {response.status_code}")
        except Exception as e:
            self.log_test("system_health", False, f"Health endpoint failed: {str(e)}")

    def test_api_endpoints(self):
        """Test API endpoints."""
        logger.info("Testing API Endpoints")
        
        endpoints = [
            ("/api/v1/patients/", "patients"),
            ("/api/v1/clinical/staff", "clinical_staff"),
            ("/docs", "api_docs")
        ]
        
        for endpoint, name in endpoints:
            try:
                response = requests.get(f"{self.base_url}{endpoint}", timeout=10)
                if response.status_code == 200:
                    self.log_test(f"api_{name}", True, f"Endpoint {endpoint} responding")
                else:
                    self.log_test(f"api_{name}", False, f"Endpoint {endpoint} returned {response.status_code}")
            except Exception as e:
                self.log_test(f"api_{name}", False, f"Endpoint {endpoint} failed: {str(e)}")

    def test_patient_workflow(self):
        """Test patient creation and management."""
        logger.info("Testing Patient Workflow")
        
        # First, get existing patients to verify system is working
        try:
            response = requests.get(f"{self.api_base}/patients/", timeout=10)
            if response.status_code == 200:
                patients = response.json()
                self.log_test("patient_list", True, f"Retrieved {len(patients)} patients")
                
                if patients:
                    # Test getting individual patient
                    patient_id = patients[0]["id"]
                    response = requests.get(f"{self.api_base}/patients/{patient_id}", timeout=10)
                    if response.status_code == 200:
                        self.log_test("patient_detail", True, "Individual patient retrieval successful")
                    else:
                        self.log_test("patient_detail", False, f"Patient detail failed: {response.status_code}")
                else:
                    self.log_test("patient_detail", False, "No patients available for testing")
            else:
                self.log_test("patient_list", False, f"Patient list failed: {response.status_code}")
        except Exception as e:
            self.log_test("patient_workflow", False, f"Patient workflow error: {str(e)}")

    def test_call_workflow(self):
        """Test call-related functionality."""
        logger.info("Testing Call Workflow")
        
        # Get existing patients
        try:
            response = requests.get(f"{self.api_base}/patients/", timeout=10)
            if response.status_code == 200:
                patients = response.json()
                if patients:
                    patient_id = patients[0]["id"]
                    
                    # Test getting call history
                    response = requests.get(f"{self.api_base}/calls/patient/{patient_id}/history", timeout=10)
                    if response.status_code == 200:
                        call_history = response.json()
                        self.log_test("call_history", True, f"Retrieved {len(call_history)} calls for patient")
                        
                        if call_history:
                            # Test individual call session
                            call_id = call_history[0]["id"]
                            response = requests.get(f"{self.api_base}/calls/{call_id}", timeout=10)
                            if response.status_code == 200:
                                self.log_test("call_detail", True, "Call session retrieval successful")
                            else:
                                self.log_test("call_detail", False, f"Call detail failed: {response.status_code}")
                        else:
                            self.log_test("call_detail", False, "No calls available for testing")
                    else:
                        self.log_test("call_history", False, f"Call history failed: {response.status_code}")
                else:
                    self.log_test("call_workflow", False, "No patients available for call testing")
            else:
                self.log_test("call_workflow", False, f"Cannot get patients for call testing: {response.status_code}")
        except Exception as e:
            self.log_test("call_workflow", False, f"Call workflow error: {str(e)}")

    def test_clinical_staff(self):
        """Test clinical staff management."""
        logger.info("Testing Clinical Staff Management")
        
        try:
            response = requests.get(f"{self.api_base}/clinical/staff", timeout=10)
            if response.status_code == 200:
                staff = response.json()
                self.log_test("clinical_staff_list", True, f"Retrieved {len(staff)} staff members")
                
                if staff:
                    # Test individual staff retrieval
                    staff_id = staff[0]["id"]
                    response = requests.get(f"{self.api_base}/clinical/staff/{staff_id}", timeout=10)
                    if response.status_code == 200:
                        self.log_test("clinical_staff_detail", True, "Individual staff retrieval successful")
                    else:
                        self.log_test("clinical_staff_detail", False, f"Staff detail failed: {response.status_code}")
                else:
                    self.log_test("clinical_staff_detail", False, "No staff available for testing")
            else:
                self.log_test("clinical_staff_list", False, f"Staff list failed: {response.status_code}")
        except Exception as e:
            self.log_test("clinical_staff", False, f"Clinical staff error: {str(e)}")

    def test_twilio_initiation(self):
        """Test Twilio call initiation with real patient."""
        logger.info("Testing Twilio Call Initiation")
        
        try:
            # Get existing patients
            response = requests.get(f"{self.api_base}/patients/", timeout=10)
            if response.status_code == 200:
                patients = response.json()
                if patients:
                    # Find Jane Doe or use first patient
                    test_patient = None
                    for patient in patients:
                        if "jane" in patient["name"].lower():
                            test_patient = patient
                            break
                    
                    if not test_patient:
                        test_patient = patients[0]
                    
                    # Test call initiation
                    call_data = {
                        "patient_id": test_patient["id"],
                        "call_type": "education"
                    }
                    
                    response = requests.post(
                        f"{self.api_base}/calls/initiate",
                        json=call_data,
                        timeout=15
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        self.log_test("twilio_call_initiation", True, 
                                    f"Call initiated successfully to {test_patient['name']}")
                        if "call_session_id" in result:
                            self.test_data["last_call_session"] = result["call_session_id"]
                    else:
                        self.log_test("twilio_call_initiation", False, 
                                    f"Call initiation failed: {response.status_code} - {response.text}")
                else:
                    self.log_test("twilio_call_initiation", False, "No patients available for call testing")
            else:
                self.log_test("twilio_call_initiation", False, f"Cannot get patients: {response.status_code}")
        except Exception as e:
            self.log_test("twilio_call_initiation", False, f"Twilio test error: {str(e)}")

    def test_webhook_endpoints(self):
        """Test webhook endpoints."""
        logger.info("Testing Webhook Endpoints")
        
        # Test Twilio voice webhook
        webhook_data = {
            "CallSid": "test_call_sid_123",
            "From": "+12132757114", 
            "To": "+18776589089",
            "CallStatus": "in-progress"
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/webhooks/twilio/voice",
                data=webhook_data,
                timeout=10
            )
            
            if response.status_code == 200:
                self.log_test("webhook_twilio_voice", True, "Twilio voice webhook responding")
            else:
                self.log_test("webhook_twilio_voice", False, f"Voice webhook failed: {response.status_code}")
        except Exception as e:
            self.log_test("webhook_twilio_voice", False, f"Voice webhook error: {str(e)}")

    def run_all_tests(self):
        """Run all tests."""
        logger.info("Running Complete Test Suite")
        logger.info("=" * 50)
        
        self.test_system_health()
        self.test_api_endpoints()
        self.test_patient_workflow()
        self.test_clinical_staff()
        self.test_call_workflow()
        self.test_twilio_initiation()
        self.test_webhook_endpoints()
        
        self.generate_report()

    def generate_report(self):
        """Generate test report."""
        total_tests = self.test_results["passed"] + self.test_results["failed"]
        success_rate = (self.test_results["passed"] / total_tests * 100) if total_tests > 0 else 0
        
        logger.info("=" * 50)
        logger.info("TEST REPORT SUMMARY")
        logger.info("=" * 50)
        logger.info(f"Total Tests: {total_tests}")
        logger.info(f"Passed: {self.test_results['passed']}")
        logger.info(f"Failed: {self.test_results['failed']}")
        logger.info(f"Success Rate: {success_rate:.1f}%")
        
        if self.test_results["failed"] > 0:
            logger.info("FAILED TESTS:")
            for error in self.test_results["errors"]:
                logger.info(f"  - {error}")
        
        logger.info("=" * 50)

if __name__ == "__main__":
    test_suite = SimpleTestSuite()
    test_suite.run_all_tests()
