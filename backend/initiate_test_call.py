#!/usr/bin/env python3
"""
Initiate a Twilio call to test the webhook flow
"""

import os
from twilio.rest import Client
import time

def make_test_call():
    """Make a call to the test number to verify webhook functionality"""
    
    # Get Twilio credentials from environment
    account_sid = os.getenv('TWILIO_ACCOUNT_SID')
    auth_token = os.getenv('TWILIO_AUTH_TOKEN')
    twilio_number = os.getenv('TWILIO_PHONE_NUMBER', '+18447418518')  # Default if not set
    
    if not account_sid or not auth_token:
        print("❌ Missing Twilio credentials in environment variables")
        return
    
    print(f"🔑 Using Twilio Account: {account_sid[:10]}...")
    print(f"📞 From Number: {twilio_number}")
    print(f"📞 To Number: +12132757114")
    
    # Initialize Twilio client
    client = Client(account_sid, auth_token)
    
    # Webhook URL for the simple test endpoint
    webhook_url = "https://0156ce1121f1.ngrok-free.app/api/webhooks/twilio/simple-test"
    
    print(f"🔗 Webhook URL: {webhook_url}")
    print("\n🚀 Initiating call...")
    
    try:
        # Make the call
        call = client.calls.create(
            to='+12132757114',
            from_=twilio_number,
            url=webhook_url,
            method='POST'
        )
        
        print(f"✅ Call initiated successfully!")
        print(f"📋 Call SID: {call.sid}")
        print(f"📱 Status: {call.status}")
        
        print("\n⏳ Waiting for call to connect...")
        time.sleep(3)
        
        # Check call status
        call = client.calls(call.sid).fetch()
        print(f"📊 Updated Status: {call.status}")
        
        print("\n🎯 ANSWER THE PHONE AND TEST:")
        print("1. Say 'hello' - should get greeting")
        print("2. Say 'help' - should list options") 
        print("3. Say 'status' - should give system status")
        print("4. Press '1' - should activate DTMF menu")
        print("5. Say 'goodbye' - should end call")
        
        print("\n📋 Monitoring backend logs...")
        return call.sid
        
    except Exception as e:
        print(f"❌ Call failed: {e}")
        return None

if __name__ == "__main__":
    print("📞 TWILIO CALL INITIATOR")
    print("=" * 40)
    
    call_sid = make_test_call()
    
    if call_sid:
        print(f"\n🔍 Call in progress: {call_sid}")
        print("💡 Check backend logs to see webhook data!")
    else:
        print("\n❌ Call initiation failed")
