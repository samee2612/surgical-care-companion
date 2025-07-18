import requests
import json

def test_webhook():
    """Test the corrected webhook URL"""
    
    # Test both the old and new ngrok URLs
    urls_to_test = [
        "https://4cc552a3f261.ngrok-free.app/api/webhooks/twilio/voice",  # Old ngrok URL
        "https://bbd2b88f163a.ngrok-free.app/api/webhooks/twilio/voice"   # Current ngrok URL
    ]
    
    test_data = {
        'From': '+12132757114',
        'To': '+18776589089',
        'CallSid': 'CAtest123',
        'AccountSid': 'AC3123f54e85931d681c837b9b16f653a1',
        'CallStatus': 'ringing',
        'Direction': 'inbound'
    }
    
    for url in urls_to_test:
        print(f"\n🧪 Testing: {url}")
        try:
            response = requests.post(url, data=test_data, timeout=10)
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                print(f"✅ SUCCESS - Response: {response.text[:100]}...")
            else:
                print(f"❌ FAILED - Status: {response.status_code}")
        except Exception as e:
            print(f"❌ ERROR - {e}")

if __name__ == "__main__":
    test_webhook()
