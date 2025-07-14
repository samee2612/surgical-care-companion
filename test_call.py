#!/usr/bin/env python3
"""
Quick Call Test for Surgical Care Companion
"""

import requests
import json

def test_call_initiation():
    """Test Twilio call initiation with Jane Doe."""
    
    base_url = "http://localhost:8000/api/v1"
    
    # Test data
    patient_id = "2526be90-305f-42b7-b41c-9b4d3e562571"  # Jane Doe
    call_session_id = "9f2dde16-301a-4ee0-942e-87cbe623bf40"  # From her call history
    
    print("🔥 Testing Call Initiation to Jane Doe")
    print("=" * 50)
    
    # Prepare call data
    call_data = {
        "patient_id": patient_id,
        "call_session_id": call_session_id,
        "call_type": "education"
    }
    
    print(f"Patient ID: {patient_id}")
    print(f"Call Session ID: {call_session_id}")
    print(f"Call Type: {call_data['call_type']}")
    print()
    
    try:
        print("Initiating call...")
        response = requests.post(
            f"{base_url}/calls/initiate",
            json=call_data,
            timeout=15
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ CALL INITIATED SUCCESSFULLY!")
            print(f"Call ID: {result.get('call_id', 'N/A')}")
            print(f"Status: {result.get('status', 'N/A')}")
        else:
            print("❌ CALL INITIATION FAILED")
            try:
                error_detail = response.json()
                print(f"Error Details: {json.dumps(error_detail, indent=2)}")
            except:
                print(f"Raw Error: {response.text}")
    
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
    
    print("\n" + "=" * 50)

if __name__ == "__main__":
    test_call_initiation()
