"""
Twilio Service Example Usage

This script demonstrates how to use the enhanced Twilio service
to initiate calls, handle responses, and process patient interactions.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def example_call_workflow():
    """
    Example workflow demonstrating the complete call process
    """
    print("=== Twilio Voice Service Example ===\n")
    
    # Example 1: Initiate a patient call
    print("1. Initiating Patient Call")
    print("-" * 30)
    
    # Mock patient data
    patient_data = {
        'patient_id': 'patient_001',
        'call_session_id': 'session_' + datetime.now().strftime('%Y%m%d_%H%M%S'),
        'phone_number': '+1234567890',
        'name': 'John Doe',
        'call_type': 'followup'
    }
    
    print(f"Patient: {patient_data['name']}")
    print(f"Phone: {patient_data['phone_number']}")
    print(f"Call Type: {patient_data['call_type']}")
    print(f"Session ID: {patient_data['call_session_id']}")
    
    # Example API call to initiate call
    print("\nAPI Call:")
    print("POST /api/v1/calls/initiate")
    print({
        'patient_id': patient_data['patient_id'],
        'call_session_id': patient_data['call_session_id'],
        'call_type': patient_data['call_type']
    })
    
    print("\nExpected Response:")
    print({
        'call_session_id': patient_data['call_session_id'],
        'call_sid': 'CA1234567890abcdef',
        'status': 'initiated',
        'message': f"Call initiated successfully to patient {patient_data['patient_id']}",
        'webhook_url': f"https://your-ngrok-url.com/api/v1/twilio/voice-webhook/{patient_data['call_session_id']}"
    })
    
    # Example 2: Call Flow and Webhooks
    print("\n\n2. Call Flow and Webhook Handling")
    print("-" * 40)
    
    call_flow_steps = [
        {
            'step': 'Call Initiated',
            'twilio_event': 'Outbound call placed',
            'webhook': 'Status callback - initiated',
            'action': 'Wait for answer'
        },
        {
            'step': 'Call Answered',
            'twilio_event': 'Call answered',
            'webhook': 'Voice webhook called',
            'action': 'Generate greeting TwiML'
        },
        {
            'step': 'Initial Greeting',
            'twilio_event': 'Say greeting message',
            'webhook': 'Start audio streaming',
            'action': 'Begin conversation'
        },
        {
            'step': 'Patient Speaks',
            'twilio_event': 'Audio stream received',
            'webhook': 'Process speech input',
            'action': 'Transcribe and analyze'
        },
        {
            'step': 'AI Response',
            'twilio_event': 'Generate TwiML response',
            'webhook': 'Continue conversation',
            'action': 'Ask follow-up questions'
        },
        {
            'step': 'Call Completion',
            'twilio_event': 'Call ended',
            'webhook': 'Status callback - completed',
            'action': 'Generate summary and alerts'
        }
    ]
    
    for i, step in enumerate(call_flow_steps, 1):
        print(f"{i}. {step['step']}")
        print(f"   Twilio Event: {step['twilio_event']}")
        print(f"   Webhook: {step['webhook']}")
        print(f"   Action: {step['action']}")
        print()
    
    # Example 3: Speech Processing
    print("\n3. Speech Processing Example")
    print("-" * 35)
    
    speech_examples = [
        {
            'input': "My pain level is about 8 out of 10",
            'transcription_confidence': 0.95,
            'clinical_extraction': {
                'pain_level': 8,
                'concerns': ['high_pain']
            },
            'ai_response': "I understand you're experiencing significant pain. That's concerning. Can you tell me more about when this pain started?",
            'next_action': 'continue_conversation',
            'alerts_triggered': ['high_pain_level']
        },
        {
            'input': "I'm doing okay, walking a bit more each day",
            'transcription_confidence': 0.92,
            'clinical_extraction': {
                'mobility_status': 'improving',
                'activity_level': 'increasing'
            },
            'ai_response': "That's great to hear! Progressive mobility is exactly what we want to see. How many steps are you able to take now?",
            'next_action': 'continue_conversation',
            'alerts_triggered': []
        },
        {
            'input': "I have some concerns about my incision",
            'transcription_confidence': 0.88,
            'clinical_extraction': {
                'wound_concerns': True,
                'concerns_mentioned': True
            },
            'ai_response': "I'd like to hear more about your concerns with the incision. Can you describe what you're noticing?",
            'next_action': 'structured_questions',
            'alerts_triggered': ['patient_concerns']
        }
    ]
    
    for i, example in enumerate(speech_examples, 1):
        print(f"Example {i}:")
        print(f"Patient Input: \"{example['input']}\"")
        print(f"Confidence: {example['transcription_confidence']}")
        print(f"Clinical Data: {example['clinical_extraction']}")
        print(f"AI Response: \"{example['ai_response']}\"")
        print(f"Next Action: {example['next_action']}")
        if example['alerts_triggered']:
            print(f"Alerts: {example['alerts_triggered']}")
        print()
    
    # Example 4: Configuration and Setup
    print("\n4. Required Configuration")
    print("-" * 30)
    
    config_requirements = {
        'Twilio Configuration': [
            'TWILIO_ACCOUNT_SID=your_account_sid',
            'TWILIO_AUTH_TOKEN=your_auth_token',
            'TWILIO_PHONE_NUMBER=+1234567890',
            'TWILIO_WEBHOOK_URL=https://your-ngrok-url.com'
        ],
        'AI Services': [
            'GEMINI_API_KEY=your_gemini_key',
            'WHISPER_MODEL=base',
            'TTS_MODEL=tts_models/en/ljspeech/tacotron2-DDC'
        ],
        'Database': [
            'DATABASE_URL=postgresql://user:pass@localhost/db',
            'REDIS_URL=redis://localhost:6379'
        ],
        'Notifications': [
            'SMTP_HOST=smtp.gmail.com',
            'SMTP_PORT=587',
            'SMTP_USER=your_email@gmail.com',
            'SMTP_PASSWORD=your_app_password'
        ]
    }
    
    for category, settings in config_requirements.items():
        print(f"{category}:")
        for setting in settings:
            print(f"  {setting}")
        print()
    
    # Example 5: API Endpoints
    print("\n5. Available API Endpoints")
    print("-" * 30)
    
    endpoints = [
        {
            'method': 'POST',
            'path': '/api/v1/calls/initiate',
            'description': 'Initiate a new voice call',
            'payload': {
                'patient_id': 'string',
                'call_session_id': 'string',
                'call_type': 'followup|enrollment|education'
            }
        },
        {
            'method': 'GET',
            'path': '/api/v1/calls/status/{call_session_id}',
            'description': 'Get call status and progress',
            'payload': None
        },
        {
            'method': 'GET',
            'path': '/api/v1/calls/transcripts/{call_session_id}',
            'description': 'Get all transcripts and responses',
            'payload': None
        },
        {
            'method': 'POST',
            'path': '/api/v1/twilio/voice-webhook/{call_session_id}',
            'description': 'Twilio voice webhook (internal)',
            'payload': 'Twilio form data'
        },
        {
            'method': 'WebSocket',
            'path': '/api/v1/twilio/audio-stream/{call_session_id}',
            'description': 'Real-time audio streaming',
            'payload': 'Audio stream data'
        }
    ]
    
    for endpoint in endpoints:
        print(f"{endpoint['method']} {endpoint['path']}")
        print(f"  Description: {endpoint['description']}")
        if endpoint['payload']:
            print(f"  Payload: {endpoint['payload']}")
        print()
    
    # Example 6: Testing with cURL
    print("\n6. Testing with cURL")
    print("-" * 25)
    
    curl_examples = [
        {
            'description': 'Initiate a call',
            'command': '''curl -X POST "http://localhost:8000/api/v1/calls/initiate" \\
  -H "Content-Type: application/json" \\
  -d '{
    "patient_id": "patient_001",
    "call_session_id": "session_20240101_120000",
    "call_type": "followup"
  }' '''
        },
        {
            'description': 'Check call status',
            'command': 'curl "http://localhost:8000/api/v1/calls/status/session_20240101_120000"'
        },
        {
            'description': 'Get transcripts',
            'command': 'curl "http://localhost:8000/api/v1/calls/transcripts/session_20240101_120000"'
        },
        {
            'description': 'Check Twilio status',
            'command': 'curl "http://localhost:8000/api/v1/calls/twilio-status"'
        }
    ]
    
    for example in curl_examples:
        print(f"{example['description']}:")
        print(f"{example['command']}")
        print()
    
    print("=== End of Examples ===")


async def demonstrate_call_orchestration():
    """
    Demonstrate the call orchestration workflow
    """
    print("\n=== Call Orchestration Workflow ===\n")
    
    workflow_steps = [
        {
            'phase': 'Initialization',
            'actions': [
                'Load patient data and call context',
                'Generate AI conversation prompts',
                'Initialize Twilio call payload',
                'Set up webhook URLs and callbacks'
            ]
        },
        {
            'phase': 'Call Initiation',
            'actions': [
                'Validate patient phone number',
                'Create Twilio call through REST API',
                'Store call context and session data',
                'Wait for call status updates'
            ]
        },
        {
            'phase': 'Call Handling',
            'actions': [
                'Generate initial greeting TwiML',
                'Start real-time audio streaming',
                'Process speech input through STT',
                'Generate AI responses contextually'
            ]
        },
        {
            'phase': 'Conversation Management',
            'actions': [
                'Extract clinical information',
                'Maintain conversation history',
                'Check for alert conditions',
                'Adapt conversation flow dynamically'
            ]
        },
        {
            'phase': 'Call Completion',
            'actions': [
                'Generate conversation summary',
                'Process clinical alerts',
                'Schedule follow-up actions',
                'Notify care team members'
            ]
        }
    ]
    
    for step in workflow_steps:
        print(f"Phase: {step['phase']}")
        print("-" * (len(step['phase']) + 7))
        for action in step['actions']:
            print(f"• {action}")
        print()


if __name__ == "__main__":
    asyncio.run(example_call_workflow())
    asyncio.run(demonstrate_call_orchestration())
