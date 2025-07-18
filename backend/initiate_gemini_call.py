#!/usr/bin/env python3
"""
Initiate a Twilio call to test the Gemini webhook flow
"""

import os
from twilio.rest import Client
import time

def make_gemini_test_call():
    """Make a call to test the Gemini-powered webhook"""
    
    # Get Twilio credentials from environment
    account_sid = os.getenv('TWILIO_ACCOUNT_SID')
    auth_token = os.getenv('TWILIO_AUTH_TOKEN')
    twilio_number = os.getenv('TWILIO_PHONE_NUMBER', '+18776589089')
    
    if not account_sid or not auth_token:
        print("❌ Missing Twilio credentials in environment variables")
        return
    
    print(f"🧠 GEMINI-POWERED CALL INITIATOR")
    print("=" * 40)
    print(f"🔑 Using Twilio Account: {account_sid[:10]}...")
    print(f"📞 From Number: {twilio_number}")
    print(f"📞 To Number: +12132757114")
    
    # Initialize Twilio client
    client = Client(account_sid, auth_token)
    
    # Webhook URL for the Gemini endpoint
    webhook_url = "https://0156ce1121f1.ngrok-free.app/api/webhooks/twilio/gemini-test"
    
    print(f"🔗 Webhook URL: {webhook_url}")
    print("\n🚀 Initiating AI-powered call...")
    
    try:
        # Make the call
        call = client.calls.create(
            to='+12132757114',
            from_=twilio_number,
            url=webhook_url,
            method='POST'
        )
        
        print(f"✅ Gemini call initiated successfully!")
        print(f"📋 Call SID: {call.sid}")
        print(f"📱 Status: {call.status}")
        
        print("\n⏳ Waiting for call to connect...")
        time.sleep(3)
        
        # Check call status
        call = client.calls(call.sid).fetch()
        print(f"📊 Updated Status: {call.status}")
        
        print("\n🧠 ANSWER THE PHONE AND TEST AI:")
        print("1. Tell it how you're feeling - should get AI response")
        print("2. Ask about pain levels - should get medical guidance") 
        print("3. Ask about recovery - should provide helpful info")
        print("4. Say 'I have a question' - should respond naturally")
        print("5. Say 'goodbye' - should end call warmly")
        print("6. Press 0 - for human transfer")
        print("7. Press 9 - to end call")
        
        print(f"\n📋 Monitor logs: docker-compose logs -f backend")
        print("🎯 This uses REAL Gemini AI responses!")
        return call.sid
        
    except Exception as e:
        print(f"❌ Call failed: {e}")
        return None

if __name__ == "__main__":
    call_sid = make_gemini_test_call()
    
    if call_sid:
        print(f"\n🔍 AI Call in progress: {call_sid}")
        print("💡 Check backend logs to see Gemini processing!")
    else:
        print("\n❌ Call initiation failed")
